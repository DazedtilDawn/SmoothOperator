import json
import sys
from pathlib import Path
import inspect
import subprocess

from orchestrator import Orchestrator, TaskResult
from validation_system.core import TransitionValidator
from cursor_client import FileOperations
from external_ai_integration import LMStudioClient


def validate_orchestrator():
    """Validate the Orchestrator implementation."""
    try:
        # Create test artifacts directory
        artifacts_dir = Path("transition_artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        log_file = artifacts_dir / "orchestrator_tests.log"

        with open(log_file, "w", encoding="utf-8") as f:
            f.write("Starting Orchestrator validation...\n")

            # Initialize orchestrator
            orchestrator = Orchestrator()
            f.write("[OK] Orchestrator instance created successfully\n")

            # Test checklist loading
            orchestrator.load_checklist("smooth_operator_impl")
            f.write("[OK] Checklist loaded successfully\n")

            # Check if status is initialized
            if not orchestrator.status:
                raise ValueError("Status not initialized")
            f.write("[OK] Status initialized\n")

            # Check if phases are tracked
            phases = orchestrator.current_checklist["checklist"]["phases"]
            for phase in phases:
                phase_name = phase["name"]
                if phase_name not in orchestrator.status:
                    raise ValueError(
                        f"Phase {phase_name} not tracked in status")
                f.write(f"[OK] Phase {phase_name} tracked in status\n")

                # Check if tasks are tracked
                for task in phase["tasks"]:
                    task_desc = task["description"]
                    if task_desc not in orchestrator.status[phase_name]["tasks"]:
                        raise ValueError(
                            f"Task {task_desc} not tracked in status")
                    f.write(f"[OK] Task {task_desc} tracked in status\n")

            # Test successful
            result = {
                "status": "success",
                "artifacts": ["orchestrator_tests.log"]
            }

    except Exception as e:
        result = {
            "status": "failure",
            "error_message": str(e),
            "artifacts": ["orchestrator_tests.log"]
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[ERROR] {str(e)}\n")

    print(json.dumps(result))
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    validate_orchestrator()
