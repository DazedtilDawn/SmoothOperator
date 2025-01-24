import pytest
from pathlib import Path
import yaml
from orchestrator import Orchestrator, ChecklistStatus, TaskResult


@pytest.fixture
def sample_checklist(tmp_path):
    """Create a sample checklist for testing."""
    checklist_dir = tmp_path / ".checklists"
    checklist_dir.mkdir()

    checklist_content = {
        "name": "Test Checklist",
        "phases": [
            {
                "name": "Phase 1",
                "success_gate": {
                    "metric": "test_coverage",
                    "min_value": 80
                },
                "tasks": [
                    {
                        "description": "Task 1",
                        "command": "echo 'test'",
                        "validation": {
                            "script": "validate.py",
                            "artifacts": ["test.txt"]
                        }
                    },
                    {
                        "description": "Task 2",
                        "command": "echo 'test2'",
                        "validation": {
                            "script": "validate2.py",
                            "artifacts": ["test2.txt"]
                        }
                    }
                ]
            }
        ]
    }

    checklist_path = checklist_dir / "test_checklist.yml"
    with open(checklist_path, "w") as f:
        yaml.dump(checklist_content, f)

    return tmp_path


def test_orchestrator_initialization():
    """Test Orchestrator initialization."""
    orchestrator = Orchestrator()
    assert orchestrator.current_checklist is None
    assert orchestrator.status == {}
    assert orchestrator.results == {}


def test_load_checklist(sample_checklist):
    """Test loading a checklist."""
    orchestrator = Orchestrator(str(sample_checklist / ".checklists"))
    assert orchestrator.load_checklist("test_checklist")
    assert orchestrator.current_checklist is not None
    assert orchestrator.current_checklist["name"] == "Test Checklist"


def test_load_nonexistent_checklist():
    """Test loading a nonexistent checklist."""
    orchestrator = Orchestrator()
    assert not orchestrator.load_checklist("nonexistent")
    assert orchestrator.current_checklist is None


def test_initialize_status(sample_checklist):
    """Test status initialization after loading checklist."""
    orchestrator = Orchestrator(str(sample_checklist / ".checklists"))
    orchestrator.load_checklist("test_checklist")

    assert orchestrator.get_phase_status(
        "Phase 1") == ChecklistStatus.NOT_STARTED
    assert orchestrator.get_task_status(
        "Phase 1", "Task 1") == ChecklistStatus.NOT_STARTED
    assert orchestrator.get_task_status(
        "Phase 1", "Task 2") == ChecklistStatus.NOT_STARTED


def test_start_phase(sample_checklist):
    """Test starting a phase."""
    orchestrator = Orchestrator(str(sample_checklist / ".checklists"))
    orchestrator.load_checklist("test_checklist")

    assert orchestrator.start_phase("Phase 1")
    assert orchestrator.get_phase_status(
        "Phase 1") == ChecklistStatus.IN_PROGRESS

    # Test starting an already started phase
    assert not orchestrator.start_phase("Phase 1")


def test_execute_task(sample_checklist):
    """Test executing a task."""
    orchestrator = Orchestrator(str(sample_checklist / ".checklists"))
    orchestrator.load_checklist("test_checklist")
    orchestrator.start_phase("Phase 1")

    result = orchestrator.execute_task("Phase 1", "Task 1")
    assert isinstance(result, TaskResult)
    assert result.success
    assert orchestrator.get_task_status(
        "Phase 1", "Task 1") == ChecklistStatus.COMPLETED


def test_execute_task_invalid_phase(sample_checklist):
    """Test executing a task in an invalid phase."""
    orchestrator = Orchestrator(str(sample_checklist / ".checklists"))
    orchestrator.load_checklist("test_checklist")

    result = orchestrator.execute_task("Invalid Phase", "Task 1")
    assert not result.success
    assert "not found" in result.error_message


def test_complete_phase(sample_checklist):
    """Test completing a phase."""
    orchestrator = Orchestrator(str(sample_checklist / ".checklists"))
    orchestrator.load_checklist("test_checklist")
    orchestrator.start_phase("Phase 1")

    # Execute all tasks
    orchestrator.execute_task("Phase 1", "Task 1")
    orchestrator.execute_task("Phase 1", "Task 2")

    assert orchestrator.complete_phase("Phase 1")
    assert orchestrator.get_phase_status(
        "Phase 1") == ChecklistStatus.COMPLETED


def test_get_task_result(sample_checklist):
    """Test getting task results."""
    orchestrator = Orchestrator(str(sample_checklist / ".checklists"))
    orchestrator.load_checklist("test_checklist")
    orchestrator.start_phase("Phase 1")

    orchestrator.execute_task("Phase 1", "Task 1")
    result = orchestrator.get_task_result("Phase 1", "Task 1")

    assert isinstance(result, TaskResult)
    assert result.success
    assert result.execution_time > 0
