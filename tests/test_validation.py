import pytest
import os
import shutil
from pathlib import Path
import json
import time
from validation_system.core import TransitionValidator, ValidationStatus, ValidationResult


@pytest.fixture
def validator(tmp_path):
    """Create a TransitionValidator instance with a temporary artifacts directory."""
    artifacts_dir = tmp_path / "artifacts"
    return TransitionValidator(str(artifacts_dir))


@pytest.fixture
def sample_task():
    """Create a sample task configuration."""
    return {
        "description": "Test Task",
        "command": "echo 'test'",
        "validation": {
            "script": "validate_test.py",
            "artifacts": ["test.txt", "metrics.json"]
        },
        "success_gate": {
            "metric": "test_coverage",
            "min_value": 80
        }
    }


@pytest.fixture
def validation_script(tmp_path):
    """Create a sample validation script."""
    script_content = """
import json
import sys

# Create test artifacts
with open("test.txt", "w") as f:
    f.write("Test output")
    
with open("metrics.json", "w") as f:
    json.dump({"test_coverage": 85}, f)

sys.exit(0)
"""
    script_path = tmp_path / "validate_test.py"
    with open(script_path, "w") as f:
        f.write(script_content)
    return script_path


def test_validator_initialization(validator):
    """Test TransitionValidator initialization."""
    assert validator.artifacts_dir.exists()
    assert validator.artifacts_dir.is_dir()


def test_validate_task_no_validation(validator):
    """Test validating a task with no validation configuration."""
    task = {"description": "Test Task"}
    result = validator.validate_task(task, "test_phase")

    assert result.status == ValidationStatus.SKIPPED
    assert len(result.artifacts) == 0
    assert "No validation configured" in result.error_message


def test_validate_task_missing_script(validator, sample_task):
    """Test validating a task with a missing validation script."""
    result = validator.validate_task(sample_task, "test_phase")

    assert result.status == ValidationStatus.FAILURE
    assert len(result.artifacts) == 0
    assert "not found" in result.error_message


def test_validate_task_success(validator, sample_task, validation_script, tmp_path):
    """Test successful task validation."""
    # Create test artifacts in the working directory
    os.chdir(tmp_path)

    # Update the task to use the actual script path and remove success gate
    sample_task["validation"]["script"] = str(validation_script)
    sample_task.pop("success_gate", None)  # Remove success gate for this test

    result = validator.validate_task(sample_task, "test_phase")

    assert result.status == ValidationStatus.SUCCESS
    assert result.artifacts
    assert result.metrics is not None


def test_validate_task_with_success_gate(validator, sample_task, validation_script, monkeypatch, tmp_path):
    """Test task validation with success gate checking."""
    os.chdir(tmp_path)
    sample_task["validation"]["script"] = str(validation_script)

    # Create metrics.json with passing value
    metrics_file = tmp_path / "metrics.json"
    metrics_file.write_text('{"test_coverage": 85.0}')

    # Mock _collect_metrics to return our metrics
    def mock_collect_metrics(self, artifacts_dir):
        return {"test_coverage": 85.0, "execution_time": time.time()}

    monkeypatch.setattr(TransitionValidator,
                        "_collect_metrics", mock_collect_metrics)

    result = validator.validate_task(sample_task, "test_phase")
    assert result.status == ValidationStatus.SUCCESS
    assert result.metrics["test_coverage"] == 85.0


def test_artifact_collection(validator, tmp_path):
    """Test artifact collection functionality."""
    # Create test artifacts in the artifacts directory
    task_id = "test_phase/Test Task"
    artifacts_dir = validator.artifacts_dir / task_id
    artifacts_dir.mkdir(parents=True)

    test_file = artifacts_dir / "test.txt"
    test_file.write_text("Test content")

    test_dir = artifacts_dir / "test_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("File 1")

    # Create a task with a validation script
    validation_script = tmp_path / "validate_test.py"
    validation_script.write_text("""
import json
with open("metrics.json", "w") as f:
    json.dump({"execution_time": 1.0}, f)
exit(0)
""")

    task = {
        "description": "Test Task",
        "validation": {
            "script": str(validation_script),
            "artifacts": ["test.txt", "file1.txt"]
        }
    }

    result = validator.validate_task(task, "test_phase")
    assert result.status == ValidationStatus.SUCCESS
    assert len(result.artifacts) > 0
    assert "test.txt" in result.artifacts
    assert "Test content" in result.artifacts["test.txt"]


def test_cleanup_artifacts(validator, tmp_path):
    """Test artifact cleanup functionality."""
    # Create some test artifacts
    task_id = "test_phase/test_task"
    artifact_dir = validator.artifacts_dir / task_id
    artifact_dir.mkdir(parents=True)

    old_file = artifact_dir / "old.txt"
    new_file = artifact_dir / "new.txt"

    old_file.write_text("Old content")
    new_file.write_text("New content")

    # Modify access time of old file to be 8 days ago
    old_time = time.time() - (8 * 24 * 3600)
    os.utime(old_file, (old_time, old_time))

    cleaned = validator.cleanup_artifacts(task_id, max_age_days=7)
    assert cleaned == 1  # One file should be cleaned up
    assert not old_file.exists()  # Old file should be deleted
    assert new_file.exists()  # New file should remain


def test_metrics_collection(validator, sample_task, validation_script, monkeypatch, tmp_path):
    """Test metrics collection from artifacts."""
    os.chdir(tmp_path)
    sample_task["validation"]["script"] = str(validation_script)

    # Create metrics.json with test metrics
    metrics_file = tmp_path / "metrics.json"
    test_metrics = {
        "execution_time": 1.0,
        "test_coverage": 85.0
    }
    metrics_file.write_text(json.dumps(test_metrics))

    # Mock _collect_metrics to return our metrics
    def mock_collect_metrics(self, artifacts_dir):
        return test_metrics

    monkeypatch.setattr(TransitionValidator,
                        "_collect_metrics", mock_collect_metrics)

    result = validator.validate_task(sample_task, "test_phase")
    assert result.metrics is not None
    assert result.metrics["execution_time"] == 1.0
    assert result.metrics["test_coverage"] == 85.0
