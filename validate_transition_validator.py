import json
from pathlib import Path
import subprocess

from validation_system.core import TransitionValidator, ValidationStatus


def validate_transition_validator():
    """Validate the TransitionValidator implementation."""
    try:
        # Create test artifacts directory
        artifacts_dir = Path("transition_artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        log_file = artifacts_dir / "validator_tests.log"

        with open(log_file, "w", encoding="utf-8") as f:
            f.write("Starting TransitionValidator validation...\n")

            # Check if the validator file exists
            if not Path("validation_system/core.py").exists():
                raise FileNotFoundError("TransitionValidator file not found")
            f.write("[OK] TransitionValidator file exists\n")

            # Initialize validator
            validator = TransitionValidator("transition_artifacts")
            f.write("[OK] TransitionValidator initialized\n")

            # Create a test task
            test_task = {
                "description": "Test Task",
                "validation": {
                    "script": "test_lmstudio_connection.py",
                    "artifacts": ["lmstudio_tests.log"]
                }
            }

            # Test validation
            result = validator.validate_task(test_task, "Test Phase")
            if result.status != ValidationStatus.SUCCESS:
                raise ValueError(f"Validation failed: {result.error_message}")

            f.write("[OK] Successfully validated test task\n")
            f.write(f"[INFO] Found {len(result.artifacts)} artifacts\n")

            # Test successful
            result = {
                "status": "success",
                "artifacts": ["validator_tests.log"]
            }

    except Exception as e:
        result = {
            "status": "failure",
            "error_message": str(e),
            "artifacts": ["validator_tests.log"]
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[ERROR] {str(e)}\n")

    print(json.dumps(result))


if __name__ == "__main__":
    validate_transition_validator()
