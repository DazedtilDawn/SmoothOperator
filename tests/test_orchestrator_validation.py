import pytest
from pathlib import Path
import yaml
import json
import os
from orchestrator import Orchestrator, ChecklistStatus, TaskResult
from validation_system.core import ValidationStatus


@pytest.fixture
def test_checklist(tmp_path):
    """Create a test checklist with validation tasks."""
    checklist_dir = tmp_path / ".checklists"
    checklist_dir.mkdir()

    checklist = {
        "name": "Test Checklist",
        "phases": [
            {
                "name": "Test Phase",
                "success_gate": {
                    "metric": "test_coverage",
                    "min_value": 80
                },
                "tasks": [
                    {
                        "description": "Test Task",
                        "command": "echo 'test'",
                        "validation": {
                            "script": str(tmp_path / "validate_test.py"),
                            "artifacts": ["test.txt", "metrics.json"]
                        }
                    }
                ]
            }
        ]
    }

    checklist_path = checklist_dir / "test.yml"
    with open(checklist_path, "w") as f:
        yaml.dump(checklist, f)

    # Create a validation script
    validation_script = tmp_path / "validate_test.py"
    validation_script.write_text("""
import json
with open("test.txt", "w") as f:
    f.write("Test content")
with open("metrics.json", "w") as f:
    json.dump({"test_coverage": 85.0}, f)
""")

    return checklist_dir


def test_validation_integration(test_checklist, tmp_path):
    """Test that validation is properly integrated into task execution."""
    # Initialize orchestrator with test checklist
    orchestrator = Orchestrator(str(test_checklist))
    assert orchestrator.load_checklist("test")

    # Start the phase
    phase_name = "Test Phase"
    assert orchestrator.start_phase(phase_name)

    # Execute the task
    task_description = "Test Task"
    result = orchestrator.execute_task(phase_name, task_description)

    # Verify the result
    assert result.success
    assert len(result.artifacts) == 2
    assert "test.txt" in result.artifacts
    assert "metrics.json" in result.artifacts

    # Verify task status
    assert orchestrator.get_task_status(
        phase_name, task_description) == ChecklistStatus.COMPLETED


def test_validation_failure(test_checklist, tmp_path):
    """Test handling of validation failures."""
    # Create a failing validation script
    validation_script = tmp_path / "validate_test.py"
    validation_script.write_text("""
import json
with open("metrics.json", "w") as f:
    json.dump({"test_coverage": 75.0}, f)
exit(1)
""")

    # Initialize orchestrator
    orchestrator = Orchestrator(str(test_checklist))
    assert orchestrator.load_checklist("test")

    # Start the phase
    phase_name = "Test Phase"
    assert orchestrator.start_phase(phase_name)

    # Execute the task
    task_description = "Test Task"
    result = orchestrator.execute_task(phase_name, task_description)

    # Verify the failure
    assert not result.success
    assert result.error_message
    assert orchestrator.get_task_status(
        phase_name, task_description) == ChecklistStatus.FAILED


def test_blocker_handling(test_checklist, tmp_path):
    """Test handling of task blockers."""
    # Add a blocker to the checklist
    with open(test_checklist / "test.yml") as f:
        checklist = yaml.safe_load(f)

    checklist["phases"][0]["tasks"][0]["blockers"] = [
        {
            "type": "TestFailure",
            "resolution": {
                "required_experts": ["QA Engineer"],
                "diagnostics": "python -m pytest --verbose"
            }
        }
    ]

    with open(test_checklist / "test.yml", "w") as f:
        yaml.dump(checklist, f)

    # Initialize orchestrator
    orchestrator = Orchestrator(str(test_checklist))
    assert orchestrator.load_checklist("test")

    # Start the phase
    phase_name = "Test Phase"
    assert orchestrator.start_phase(phase_name)

    # Execute the task
    task_description = "Test Task"
    result = orchestrator.execute_task(phase_name, task_description)

    # Verify the task completed despite the blocker (since we haven't implemented blocker checking yet)
    assert result.success
    assert orchestrator.get_task_status(
        phase_name, task_description) == ChecklistStatus.COMPLETED
