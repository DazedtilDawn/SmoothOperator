import json
import os
from pathlib import Path
import requests

from external_ai_integration import LMStudioClient


def validate_lmstudio_integration():
    """Validate the LMStudio integration."""
    try:
        # Create test artifacts directory
        artifacts_dir = Path("transition_artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        log_file = artifacts_dir / "lmstudio_integration_tests.log"

        with open(log_file, "w", encoding="utf-8") as f:
            f.write("Starting LMStudio integration validation...\n")

            # Check if the client file exists
            if not Path("external_ai_integration.py").exists():
                raise FileNotFoundError("LMStudio client file not found")
            f.write("[OK] LMStudio client file exists\n")

            # Initialize client
            client = LMStudioClient()
            f.write("[OK] LMStudio client initialized\n")

            # Test API connection
            test_context = {
                "phase": "Test Phase",
                "task_description": "Test Task",
                "error_message": "Test Error",
                "implementation_data": "Test Data"
            }

            response = client.generate_prompt(test_context)
            if response.startswith("Error generating prompt:"):
                raise ConnectionError(response)

            # Check if response is a valid string
            if not isinstance(response, str) or not response.strip():
                raise ValueError("Invalid response from LMStudio API")

            f.write("[OK] Successfully connected to LMStudio API\n")
            f.write(f"[INFO] Response length: {len(response)} characters\n")

            # Test successful
            result = {
                "status": "success",
                "artifacts": ["lmstudio_integration_tests.log"]
            }

    except Exception as e:
        result = {
            "status": "failure",
            "error_message": str(e),
            "artifacts": ["lmstudio_integration_tests.log"]
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[ERROR] {str(e)}\n")

    print(json.dumps(result))


if __name__ == "__main__":
    validate_lmstudio_integration()
