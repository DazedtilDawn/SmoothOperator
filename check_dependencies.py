import os
import sys
import importlib
from pathlib import Path
import subprocess
import json


def check_dependencies():
    """Check if all required dependencies are installed and configured."""
    try:
        # Create test artifacts directory
        artifacts_dir = Path("transition_artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        log_file = artifacts_dir / "dependency_check.log"

        with open(log_file, "w", encoding="utf-8") as f:
            f.write("🔄 Running Dependency Checks...\n\n")

            f.write("🔍 Checking Environment Variables:\n")

            # Check required modules
            f.write("\n🔍 Checking Required Modules:\n")
            required_modules = ["requests", "pytest", "dotenv"]
            for module in required_modules:
                try:
                    importlib.import_module(module)
                    f.write(f"✅ {module} is installed\n")
                except ImportError:
                    raise ImportError(f"{module} is not installed")

            # Check required files and directories
            f.write("\n🔍 Checking Required Files and Directories:\n")
            required_paths = [
                ".checklists",
                ".patches",
                "orchestrator.py",
                "cursor_client.py"
            ]

            for path_str in required_paths:
                path = Path(path_str)
                if path.exists():
                    f.write(
                        f"✅ {path_str} {'directory' if path.is_dir() else 'file'} exists\n")
                else:
                    raise FileNotFoundError(f"{path_str} not found")

            # Check Git setup
            f.write("\n🔍 Checking Git Setup:\n")
            try:
                result = subprocess.run(
                    ["git", "--version"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                f.write(f"✅ Git is available: {result.stdout.strip()}\n")
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise EnvironmentError("Git is not installed or not in PATH")

            # Test successful
            result = {
                "status": "success",
                "artifacts": ["dependency_check.log"]
            }

    except Exception as e:
        result = {
            "status": "failure",
            "error_message": str(e),
            "artifacts": ["dependency_check.log"]
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n❌ Error: {str(e)}\n")

    print(json.dumps(result))


if __name__ == "__main__":
    check_dependencies()
