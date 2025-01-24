#!/usr/bin/env python3

import sys
import json
import subprocess
from pathlib import Path


def check_git_installation():
    """Check if git is installed and accessible."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_git_repository():
    """Check if current directory is a git repository."""
    try:
        subprocess.run(["git", "rev-parse", "--git-dir"],
                       capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def check_git_config():
    """Check if git configuration is set up properly."""
    required_configs = {
        "user.name": "Git username is not set",
        "user.email": "Git email is not set"
    }

    missing_configs = []
    for config, message in required_configs.items():
        try:
            result = subprocess.run(
                ["git", "config", "--get", config],
                capture_output=True,
                text=True,
                check=True
            )
            if not result.stdout.strip():
                missing_configs.append(message)
        except subprocess.CalledProcessError:
            missing_configs.append(message)

    return missing_configs


def check_gitignore():
    """Check if .gitignore exists and has basic entries."""
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        return False

    basic_entries = {
        "*.pyc",
        "__pycache__/",
        "*.pyo",
        "*.pyd",
        ".Python",
        "env/",
        "venv/",
        ".env",
        ".venv",
        "pip-log.txt",
        "pip-delete-this-directory.txt",
        ".tox/",
        ".coverage",
        ".coverage.*",
        ".cache",
        "nosetests.xml",
        "coverage.xml",
        "*.cover",
        "*.log",
        ".pytest_cache/",
        ".mypy_cache/",
        ".hypothesis/"
    }

    current_entries = set()
    with open(gitignore_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                current_entries.add(line)

    # Check for any common entries
    return bool(basic_entries & current_entries)


def main():
    """Main validation function."""
    validation_results = {
        "success": True,
        "messages": [],
        "metrics": {
            "git_configured": False,
            "gitignore_score": 0.0
        }
    }

    # Check git installation
    if not check_git_installation():
        validation_results["success"] = False
        validation_results["messages"].append(
            "Git is not installed or not accessible")
        print(json.dumps(validation_results))
        return 1

    # Check if directory is a git repository
    if not check_git_repository():
        validation_results["success"] = False
        validation_results["messages"].append("Not a git repository")
        print(json.dumps(validation_results))
        return 1

    # Check git configuration
    missing_configs = check_git_config()
    if missing_configs:
        validation_results["success"] = False
        validation_results["messages"].extend(missing_configs)
    else:
        validation_results["metrics"]["git_configured"] = True

    # Check .gitignore
    if not check_gitignore():
        validation_results["messages"].append(
            "Missing or incomplete .gitignore file")
        validation_results["metrics"]["gitignore_score"] = 0.0
    else:
        validation_results["metrics"]["gitignore_score"] = 1.0

    # Generate git status artifact
    try:
        status_output = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        with open("git_status.txt", "w") as f:
            f.write(status_output.stdout)
    except subprocess.CalledProcessError as e:
        validation_results["messages"].append(f"Error getting git status: {e}")

    # Generate git config artifact
    try:
        config_output = subprocess.run(
            ["git", "config", "--list"],
            capture_output=True,
            text=True,
            check=True
        )
        with open("git_config.txt", "w") as f:
            f.write(config_output.stdout)
    except subprocess.CalledProcessError as e:
        validation_results["messages"].append(f"Error getting git config: {e}")

    print(json.dumps(validation_results))
    return 0 if validation_results["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
