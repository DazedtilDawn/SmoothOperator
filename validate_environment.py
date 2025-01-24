import sys
import pkg_resources
import subprocess
from pathlib import Path


def validate_environment():
    """Validate the Python environment setup."""
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print(f"Error: Python version must be >= 3.8 (current: {sys.version})")
        return 1

    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Error: Not running in a virtual environment")
        return 1

    # Read requirements.txt
    try:
        with open('requirements.txt') as f:
            required = {line.strip().split(
                '==')[0] for line in f if line.strip() and not line.startswith('#')}
    except FileNotFoundError:
        print("Error: requirements.txt not found")
        return 1

    # Check installed packages
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = required - installed

    if missing:
        print(f"Error: Missing required packages: {', '.join(missing)}")
        return 1

    # Generate pip freeze artifact
    subprocess.run([sys.executable, "-m", "pip", "freeze"],
                   stdout=open("pip_freeze.txt", "w"))

    print("Python environment validation successful")
    return 0


if __name__ == "__main__":
    sys.exit(validate_environment())
