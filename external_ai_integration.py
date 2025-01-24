import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class LMStudioClient:
    """Client for interacting with LMStudio's API."""

    def __init__(self, api_endpoint: str = "http://localhost:1234/v1/chat/completions"):
        """Initialize the LMStudio AI client."""
        load_dotenv()
        self.api_endpoint = api_endpoint

    def generate_prompt(self, context: Dict[str, Any]) -> str:
        """Generate a prompt based on the provided context."""
        headers = {
            "Content-Type": "application/json"
        }

        # Format the context into a chat message
        task_desc = context.get("task_description", "")
        phase = context.get("phase", "")
        error_msg = context.get("error_message", "")
        impl_data = context.get("implementation_data", "")

        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant that helps with coding tasks."
            },
            {
                "role": "user",
                "content": f"""
                Phase: {phase}
                Task: {task_desc}
                Error: {error_msg}
                Implementation Data: {impl_data}

                Please help me fix this issue and provide guidance on how to proceed.
                """
            }
        ]

        payload = {
            "model": "local-model",  # Placeholder for the model name
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
            "timeout": 60
        }

        try:
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except requests.exceptions.RequestException as e:
            return f"Error generating prompt: {e}"
