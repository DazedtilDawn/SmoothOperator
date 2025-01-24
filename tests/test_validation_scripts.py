import pytest
import json
import os
import subprocess
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the validation scripts
import validate_git
import validate_docs


@pytest.fixture
def setup_validation_scripts(tmp_path):
    """Copy validation scripts to the test directory."""
    # Get the absolute paths of the validation scripts
    base_dir = Path(__file__).parent.parent
    git_script = base_dir / "validation_system" / "validate_git.py"
    docs_script = base_dir / "validation_system" / "validate_docs.py"

    # Create validation_system directory in tmp_path
    validation_dir = tmp_path / "validation_system"
    validation_dir.mkdir(exist_ok=True)

    # Copy validation scripts to temp directory
    shutil.copy2(str(git_script), str(validation_dir / "validate_git.py"))
    shutil.copy2(str(docs_script), str(validation_dir / "validate_docs.py"))

    return validation_dir


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository."""
    os.chdir(tmp_path)
    subprocess.run(["git", "init"], capture_output=True)
    subprocess.run(["git", "config", "user.name",
                   "Test User"], capture_output=True)
    subprocess.run(["git", "config", "user.email",
                   "test@example.com"], capture_output=True)
    return tmp_path


@pytest.fixture
def sample_gitignore(tmp_path):
    """Create a sample .gitignore file."""
    content = """
# Python
*.pyc
__pycache__/
*.pyo
*.pyd
.Python
venv/
.env

# Testing
.pytest_cache/
.coverage
coverage.xml
"""
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text(content)
    return gitignore_path


@pytest.fixture
def sample_readme(tmp_path):
    """Create a sample README.md file."""
    content = """# Project Title

Project description goes here.

## Installation

Installation instructions...

## Usage

Usage examples...

## Contributing

Contribution guidelines...

## License

MIT License
"""
    readme_path = tmp_path / "README.md"
    readme_path.write_text(content)
    return readme_path


@pytest.fixture
def docs_structure(tmp_path):
    """Create a sample documentation structure."""
    docs_path = tmp_path / "docs"
    (docs_path / "api").mkdir(parents=True)
    (docs_path / "tutorials").mkdir()
    (docs_path / "examples").mkdir()
    return docs_path


@pytest.fixture
def sample_python_files(tmp_path):
    """Create sample Python files with and without docstrings."""
    src_path = tmp_path / "src"
    src_path.mkdir()

    # File with docstrings
    file1 = src_path / "documented.py"
    file1.write_text('''
"""Module docstring."""

def function_with_docstring():
    """This function has a docstring."""
    pass

class ClassWithDocstring:
    """This class has a docstring."""
    pass
''')

    # File without docstrings
    file2 = src_path / "undocumented.py"
    file2.write_text('''
def function_without_docstring():
    pass

class ClassWithoutDocstring:
    pass
''')

    return src_path


def test_git_installation():
    """Test git installation check."""
    assert validate_git.check_git_installation()


def test_git_repository(git_repo):
    """Test git repository check."""
    assert validate_git.check_git_repository()

    # Test non-git directory
    os.chdir(git_repo.parent)
    assert not validate_git.check_git_repository()


def test_git_config(git_repo):
    """Test git configuration check."""
    missing_configs = validate_git.check_git_config()
    assert not missing_configs


def test_git_ignore(git_repo, sample_gitignore):
    """Test .gitignore check."""
    assert validate_git.check_gitignore()

    # Test without .gitignore
    sample_gitignore.unlink()
    assert not validate_git.check_gitignore()


def test_git_validation_script(git_repo, sample_gitignore, setup_validation_scripts):
    """Test the complete git validation script."""
    # Change to the git repo directory
    os.chdir(git_repo)
    script_path = setup_validation_scripts / "validate_git.py"

    # Ensure the script exists and is executable
    assert script_path.exists(), f"Script not found at {script_path}"

    result = subprocess.run(
        ["python", str(script_path)],
        capture_output=True,
        text=True,
        cwd=git_repo  # Explicitly set working directory
    )

    assert result.returncode == 0, f"Script failed with output: {result.stdout}\nError: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["success"]
    assert data["metrics"]["git_configured"]
    assert data["metrics"]["gitignore_score"] > 0

    # Verify artifacts were created
    assert (git_repo / "git_status.txt").exists()
    assert (git_repo / "git_config.txt").exists()


def test_readme_check(tmp_path, sample_readme):
    """Test README.md validation."""
    os.chdir(tmp_path)
    exists, missing = validate_docs.check_readme()
    assert exists
    assert not missing


def test_docs_structure_check(tmp_path, docs_structure):
    """Test documentation structure validation."""
    os.chdir(tmp_path)
    exists, components = validate_docs.check_docs_structure()
    assert exists
    assert len(components) == 3
    assert "api" in components
    assert "tutorials" in components
    assert "examples" in components


def test_docstring_check(tmp_path, sample_python_files):
    """Test docstring coverage check."""
    os.chdir(tmp_path)
    metrics = validate_docs.check_docstrings("src")

    assert metrics["total_functions"] == 2
    assert metrics["documented_functions"] == 1
    assert metrics["total_classes"] == 2
    assert metrics["documented_classes"] == 1
    assert metrics["function_coverage"] == 50.0
    assert metrics["class_coverage"] == 50.0


def test_docs_report_generation(tmp_path, sample_readme, docs_structure, sample_python_files):
    """Test documentation report generation."""
    os.chdir(tmp_path)

    metrics = validate_docs.check_docstrings("src")
    exists, missing = validate_docs.check_readme()
    structure_exists, components = validate_docs.check_docs_structure()

    report = validate_docs.generate_docs_report(metrics, missing, components)

    assert "Documentation Status Report" in report
    assert "README.md Status" in report
    assert "Documentation Structure" in report
    assert "Docstring Coverage" in report


def test_docs_validation_script(tmp_path, sample_readme, docs_structure, sample_python_files, setup_validation_scripts):
    """Test the complete documentation validation script."""
    # Change to the temporary directory
    os.chdir(tmp_path)
    script_path = setup_validation_scripts / "validate_docs.py"

    # Ensure the script exists
    assert script_path.exists(), f"Script not found at {script_path}"

    result = subprocess.run(
        ["python", str(script_path)],
        capture_output=True,
        text=True,
        cwd=tmp_path  # Explicitly set working directory
    )

    # The script may return non-zero if validation fails, but it should still output valid JSON
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        pytest.fail(
            f"Failed to parse JSON output: {e}\nOutput was: {result.stdout}")

    assert "metrics" in data
    assert "readme_score" in data["metrics"]
    assert "docs_structure_score" in data["metrics"]
    assert "docstring_coverage" in data["metrics"]

    # Check if report was generated
    assert (tmp_path / "docs_report.md").exists()
