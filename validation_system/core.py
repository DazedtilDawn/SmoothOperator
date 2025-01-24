import json
import subprocess
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


class ValidationStatus(Enum):
    """Enumeration of possible validation statuses."""
    SUCCESS = "success"
    FAILURE = "failure"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    status: ValidationStatus
    artifacts: Dict[str, Any]
    error_message: Optional[str] = None


class TransitionValidator:
    """Validator for checking task transitions and success criteria."""

    def __init__(self, artifacts_dir: str = "transition_artifacts"):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(exist_ok=True)

    def validate_task(self, task: Dict[str, Any], phase_name: str) -> ValidationResult:
        """Validate a task using its validation script and collect artifacts."""
        try:
            if "validation" not in task:
                return ValidationResult(ValidationStatus.SUCCESS, {})

            validation = task["validation"]
            script = validation["script"]
            expected_artifacts = validation.get("artifacts", [])

            # Run the validation script
            result = subprocess.run(
                ["python", script],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return ValidationResult(
                    ValidationStatus.FAILURE,
                    {},
                    f"Validation script failed: {result.stderr}"
                )

            try:
                output = json.loads(result.stdout)
                status = output.get("status", "failure")
                artifacts = {}

                # Check for expected artifacts
                for artifact in expected_artifacts:
                    artifact_path = self.artifacts_dir / artifact
                    if artifact_path.exists():
                        with open(artifact_path, 'r') as f:
                            artifacts[artifact] = f.read()
                    else:
                        return ValidationResult(
                            ValidationStatus.FAILURE,
                            artifacts,
                            f"Missing artifact: {artifact}"
                        )

                if status == "success":
                    return ValidationResult(ValidationStatus.SUCCESS, artifacts)
                else:
                    return ValidationResult(
                        ValidationStatus.FAILURE,
                        artifacts,
                        output.get("error_message", "Validation failed")
                    )

            except json.JSONDecodeError:
                return ValidationResult(
                    ValidationStatus.FAILURE,
                    {},
                    "Invalid validation script output format"
                )

        except Exception as e:
            return ValidationResult(
                ValidationStatus.FAILURE,
                {},
                f"Validation error: {str(e)}"
            )
