import pytest
import json
import os
from validation_system.blockers.auto_blocker_resolver import BlockerResolver
from orchestrator import Orchestrator


@pytest.fixture
def test_checklist():
    return {
        "name": "Test Checklist",
        "checklist": {
            "phases": [
                {
                    "name": "Test Phase",
                    "tasks": [
                        {
                            "name": "Test Task",
                            "description": "A test task with blockers",
                            "command": "echo 'test'",
                            "blockers": [
                                {
                                    "type": "TestBlocker",
                                    "resolution": {
                                        "diagnostics": "echo '{\"status\": \"success\"}'"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }


@pytest.fixture
def test_checklist_file(test_checklist, tmp_path):
    checklist_path = tmp_path / "test_checklist.json"
    with open(checklist_path, "w") as f:
        json.dump(test_checklist, f)
    return checklist_path


def test_orchestrator_with_blocker_resolution(test_checklist_file):
    """Test that the Orchestrator can handle blocker resolution."""
    orchestrator = Orchestrator()
    resolver = BlockerResolver()

    # Load the test checklist
    orchestrator.load_checklist(str(test_checklist_file))

    # Get the blockers from the first task
    task = orchestrator.current_checklist["checklist"]["phases"][0]["tasks"][0]
    blockers = task.get("blockers", [])

    # Resolve the blockers
    unresolved = resolver.resolve_blockers(blockers)

    # Assert that all blockers were resolved
    assert len(unresolved) == 0

    # Execute the task
    result = orchestrator.execute_checklist()
    assert result == 0  # Success


def test_orchestrator_with_unresolvable_blocker(test_checklist_file):
    """Test that the Orchestrator handles unresolvable blockers correctly."""
    orchestrator = Orchestrator()
    resolver = BlockerResolver()

    # Modify the checklist to include an unresolvable blocker
    with open(test_checklist_file) as f:
        checklist = json.load(f)

    checklist["checklist"]["phases"][0]["tasks"][0]["blockers"][0]["resolution"] = {
        "required_experts": ["Unavailable Expert"]
    }

    modified_checklist = str(test_checklist_file).replace(
        ".json", "_modified.json")
    with open(modified_checklist, "w") as f:
        json.dump(checklist, f)

    # Load the modified checklist
    orchestrator.load_checklist(modified_checklist)

    # Get the blockers from the first task
    task = orchestrator.current_checklist["checklist"]["phases"][0]["tasks"][0]
    blockers = task.get("blockers", [])

    # Try to resolve the blockers
    unresolved = resolver.resolve_blockers(blockers)

    # Assert that the blocker was not resolved
    assert len(unresolved) == 1
    assert unresolved[0]["type"] == "TestBlocker"

    # Execute the task (should fail due to unresolved blocker)
    result = orchestrator.execute_checklist()
    assert result == 1  # Failure
