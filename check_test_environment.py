import json
import sys
from pathlib import Path
import subprocess


def check_test_environment():
    """Check if the test environment is properly set up."""
    try:
        # Create test artifacts directory
        artifacts_dir = Path("transition_artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        log_file = artifacts_dir / "test_env_check.log"

        with open(log_file, "w", encoding="utf-8") as f:
            f.write("Starting test environment check...\n")

            # Check Python version
            python_version = sys.version_info
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
                raise ValueError("Python 3.7 or higher is required")
            f.write(
                f"[OK] Python version {sys.version.split()[0]} is compatible\n")

            # Check pytest installation
            try:
                import pytest
                f.write(f"[OK] pytest {pytest.__version__} is installed\n")
            except ImportError:
                raise ImportError("pytest is not installed")

            # Check test directories
            test_dirs = ["tests", "transition_artifacts"]
            for dir_name in test_dirs:
                path = Path(dir_name)
                if not path.exists():
                    path.mkdir(exist_ok=True)
                f.write(f"[OK] {dir_name} directory exists\n")

            # Check test file permissions
            for dir_name in test_dirs:
                path = Path(dir_name)
                try:
                    test_file = path / "test_write.tmp"
                    test_file.write_text("test")
                    test_file.unlink()
                    f.write(f"[OK] {dir_name} directory is writable\n")
                except Exception as e:
                    raise PermissionError(f"Cannot write to {dir_name}: {e}")

            # Test successful
            result = {
                "status": "success",
                "artifacts": ["test_env_check.log"]
            }

    except Exception as e:
        result = {
            "status": "failure",
            "error_message": str(e),
            "artifacts": ["test_env_check.log"]
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[ERROR] {str(e)}\n")

    print(json.dumps(result))


if __name__ == "__main__":
    check_test_environment()
