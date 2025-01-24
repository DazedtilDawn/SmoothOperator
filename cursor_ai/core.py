from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv


class AIServiceType(Enum):
    CURSOR = "cursor"
    OPENAI = "openai"
    CUSTOM = "custom"


class AIRequestType(Enum):
    CODE_REVIEW = "code_review"
    VALIDATION = "validation"
    SUGGESTION = "suggestion"
    DOCUMENTATION = "documentation"


@dataclass
class AIRequest:
    service: AIServiceType
    request_type: AIRequestType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    context_files: Optional[List[str]] = None


@dataclass
class AIResponse:
    success: bool
    content: str
    suggestions: Optional[List[str]] = None
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class CursorAIClient:
    def __init__(self, config_dir: str = ".cursor_ai"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        # Load environment variables
        load_dotenv()

        self.api_key = os.getenv("CURSOR_AI_API_KEY")
        self.api_base_url = os.getenv(
            "CURSOR_AI_BASE_URL", "https://api.cursor.sh/v1")
        self.default_service = AIServiceType(
            os.getenv("CURSOR_AI_SERVICE", "cursor"))

        # Load service configurations
        self.service_configs = self._load_service_configs()

    def _load_service_configs(self) -> Dict[str, Any]:
        """Load service configurations from the config directory."""
        config_file = self.config_dir / "services.json"
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        return {}

    def save_service_config(self, service: AIServiceType, config: Dict[str, Any]) -> bool:
        """Save a service configuration."""
        try:
            self.service_configs[service.value] = config
            config_file = self.config_dir / "services.json"
            with open(config_file, "w") as f:
                json.dump(self.service_configs, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving service config: {e}")
            return False

    def validate_code(self, code: str, context_files: Optional[List[str]] = None) -> AIResponse:
        """Validate code using AI service."""
        request = AIRequest(
            service=self.default_service,
            request_type=AIRequestType.VALIDATION,
            content=code,
            context_files=context_files
        )
        return self._make_request(request)

    def review_code(self, code: str, context_files: Optional[List[str]] = None) -> AIResponse:
        """Get code review feedback using AI service."""
        request = AIRequest(
            service=self.default_service,
            request_type=AIRequestType.CODE_REVIEW,
            content=code,
            context_files=context_files
        )
        return self._make_request(request)

    def get_suggestions(self, context: str, context_files: Optional[List[str]] = None) -> AIResponse:
        """Get suggestions for improvements or next steps."""
        request = AIRequest(
            service=self.default_service,
            request_type=AIRequestType.SUGGESTION,
            content=context,
            context_files=context_files
        )
        return self._make_request(request)

    def generate_documentation(self, code: str, context_files: Optional[List[str]] = None) -> AIResponse:
        """Generate documentation for code."""
        request = AIRequest(
            service=self.default_service,
            request_type=AIRequestType.DOCUMENTATION,
            content=code,
            context_files=context_files
        )
        return self._make_request(request)

    def _make_request(self, request: AIRequest) -> AIResponse:
        """Make a request to the AI service."""
        if not self.api_key:
            return AIResponse(False, "API key not configured", confidence=0.0)

        service_config = self.service_configs.get(request.service.value, {})

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "type": request.request_type.value,
                "content": request.content,
                "metadata": request.metadata or {},
                "context_files": request.context_files or []
            }

            # Add service-specific configuration
            payload.update(service_config)

            response = requests.post(
                f"{self.api_base_url}/{request.request_type.value}",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                return AIResponse(
                    success=True,
                    content=data["content"],
                    suggestions=data.get("suggestions"),
                    confidence=data.get("confidence", 1.0),
                    metadata=data.get("metadata")
                )
            else:
                return AIResponse(
                    success=False,
                    content=f"Request failed: {response.text}",
                    confidence=0.0
                )

        except Exception as e:
            return AIResponse(
                success=False,
                content=f"Error making request: {str(e)}",
                confidence=0.0
            )

    def cache_context(self, files: List[str]) -> str:
        """Cache context files for future requests."""
        cache_dir = self.config_dir / "context_cache"
        cache_dir.mkdir(exist_ok=True)

        cache_id = str(hash(tuple(sorted(files))))
        cache_path = cache_dir / f"{cache_id}.json"

        try:
            context_data = {}
            for file_path in files:
                if Path(file_path).exists():
                    with open(file_path) as f:
                        context_data[file_path] = f.read()

            with open(cache_path, "w") as f:
                json.dump(context_data, f)

            return cache_id

        except Exception as e:
            print(f"Error caching context: {e}")
            return ""

    def get_cached_context(self, cache_id: str) -> Dict[str, str]:
        """Retrieve cached context files."""
        cache_path = self.config_dir / "context_cache" / f"{cache_id}.json"

        if cache_path.exists():
            try:
                with open(cache_path) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cached context: {e}")

        return {}

    def apply_patch(self, patch_path: str) -> AIResponse:
        """
        Apply a patch file using Cursor AI.
        :param patch_path: Path to the patch file.
        :return: AIResponse indicating success or failure.
        """
        try:
            with open(patch_path, 'r', encoding='utf-8') as f:
                patch_content = f.read()

            request = AIRequest(
                service=self.default_service,
                request_type=AIRequestType.CODE_REVIEW,
                content=patch_content,
                metadata={"action": "apply_patch", "path": patch_path}
            )
            return self._make_request(request)
        except Exception as e:
            return AIResponse(False, f"Error applying patch: {str(e)}", confidence=0.0)

    def insert_snippet(self, file_path: str, snippet: str, line: int) -> AIResponse:
        """
        Insert a snippet into a file at a specific line using Cursor AI.
        :param file_path: Path to the target file.
        :param snippet: Snippet to insert.
        :param line: Line number to insert the snippet at.
        :return: AIResponse indicating success or failure.
        """
        try:
            request = AIRequest(
                service=self.default_service,
                request_type=AIRequestType.CODE_REVIEW,
                content=snippet,
                metadata={
                    "action": "insert_snippet",
                    "file_path": file_path,
                    "line": line
                }
            )
            return self._make_request(request)
        except Exception as e:
            return AIResponse(False, f"Error inserting snippet: {str(e)}", confidence=0.0)

    def receive_prompt(self, prompt: str) -> AIResponse:
        """
        Send a detailed prompt to Cursor AI and receive a response.
        :param prompt: The prompt to send.
        :return: AIResponse indicating success or failure.
        """
        request = AIRequest(
            service=self.default_service,
            request_type=AIRequestType.SUGGESTION,
            content=prompt,
            metadata={"action": "process_prompt"}
        )
        return self._make_request(request)
