#!/usr/bin/env python3

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Set


def check_readme():
    """Check if README.md exists and has required sections."""
    readme_path = Path("README.md")
    if not readme_path.exists():
        return False, []

    required_sections = {
        "title": r"^#\s+.+",  # Title (level 1 heading)
        "description": r"^(?!#).+",  # Non-heading text after title
        "installation": r"^##\s+(?:Installation|Setup|Getting Started)",
        "usage": r"^##\s+(?:Usage|How to Use|Examples?)",
        "contributing": r"^##\s+Contributing",
        "license": r"^##\s+License"
    }

    found_sections = set()
    current_content = ""

    try:
        with open(readme_path, encoding='utf-8') as f:
            content = f.read()
            lines = content.split("\n")

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                current_content += line + "\n"

                for section, pattern in required_sections.items():
                    if re.match(pattern, line) and section not in found_sections:
                        found_sections.add(section)
    except UnicodeDecodeError as e:
        print(f"Warning: Could not read README.md: {e}", file=sys.stderr)
        return False, []

    missing_sections = set(required_sections.keys()) - found_sections
    return bool(found_sections), list(missing_sections)


def check_docs_structure():
    """Check if documentation structure exists and has required components."""
    docs_path = Path("docs")
    if not docs_path.exists() or not docs_path.is_dir():
        return False, []

    required_components = {
        "api": docs_path / "api",
        "tutorials": docs_path / "tutorials",
        "examples": docs_path / "examples"
    }

    existing_components = []
    for name, path in required_components.items():
        if path.exists() and path.is_dir():
            existing_components.append(name)

    return bool(existing_components), existing_components


def check_docstrings(directory: str = ".", pattern: str = "*.py") -> Dict[str, float]:
    """Check Python files for docstrings and return coverage metrics."""
    metrics = {
        "total_functions": 0,
        "documented_functions": 0,
        "total_classes": 0,
        "documented_classes": 0,
        "files": {}  # Track per-file metrics
    }

    # Define project directories to check
    project_dirs = [
        "validation_system",
        "tests",
        "docs/examples"
    ]

    for project_dir in project_dirs:
        dir_path = Path(project_dir)
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob(pattern):
            try:
                with open(py_file, encoding='utf-8') as f:
                    content = f.read()

                file_metrics = {
                    "total_functions": 0,
                    "documented_functions": 0,
                    "total_classes": 0,
                    "documented_classes": 0
                }

                # Find all function definitions
                function_matches = re.finditer(r"def\s+(\w+)\s*\(", content)
                class_matches = re.finditer(r"class\s+(\w+)\s*[:\(]", content)

                for match in function_matches:
                    file_metrics["total_functions"] += 1
                    metrics["total_functions"] += 1
                    # Check for docstring after function definition
                    pos = match.end()
                    next_lines = content[pos:pos+500]  # Look at next 500 chars
                    if re.search(r'\s*["\']""[\s\S]*?["\']""|\s*\'\'\'[\s\S]*?\'\'\'', next_lines):
                        file_metrics["documented_functions"] += 1
                        metrics["documented_functions"] += 1

                for match in class_matches:
                    file_metrics["total_classes"] += 1
                    metrics["total_classes"] += 1
                    pos = match.end()
                    next_lines = content[pos:pos+500]  # Look at next 500 chars
                    if re.search(r'\s*["\']""[\s\S]*?["\']""|\s*\'\'\'[\s\S]*?\'\'\'', next_lines):
                        file_metrics["documented_classes"] += 1
                        metrics["documented_classes"] += 1

                # Calculate file-level coverage
                file_metrics["function_coverage"] = (
                    (file_metrics["documented_functions"] /
                     file_metrics["total_functions"] * 100)
                    if file_metrics["total_functions"] > 0 else 100
                )
                file_metrics["class_coverage"] = (
                    (file_metrics["documented_classes"] /
                     file_metrics["total_classes"] * 100)
                    if file_metrics["total_classes"] > 0 else 100
                )
                file_metrics["overall_coverage"] = (
                    (file_metrics["function_coverage"] +
                     file_metrics["class_coverage"]) / 2
                    if file_metrics["total_functions"] + file_metrics["total_classes"] > 0
                    else 100
                )

                metrics["files"][str(py_file)] = file_metrics

            except (UnicodeDecodeError, IOError) as e:
                print(
                    f"Warning: Could not process file {py_file}: {e}", file=sys.stderr)
                continue

    # Calculate overall coverage percentages
    metrics["function_coverage"] = (
        (metrics["documented_functions"] / metrics["total_functions"] * 100)
        if metrics["total_functions"] > 0 else 100
    )
    metrics["class_coverage"] = (
        (metrics["documented_classes"] / metrics["total_classes"] * 100)
        if metrics["total_classes"] > 0 else 100
    )

    return metrics


def generate_docs_report(metrics: Dict[str, float], missing_sections: List[str], existing_components: List[str]) -> str:
    """Generate a documentation status report."""
    report = ["# Documentation Status Report", ""]

    # README.md status
    report.append("## README.md Status")
    if not missing_sections:
        report.append("✅ README.md is complete with all required sections")
    else:
        report.append("⚠️ README.md is missing the following sections:")
        for section in missing_sections:
            report.append(f"  - {section}")
    report.append("")

    # Documentation structure
    report.append("## Documentation Structure")
    if existing_components:
        report.append("✅ Found the following documentation components:")
        for component in existing_components:
            report.append(f"  - {component}")
    else:
        report.append("⚠️ No documentation structure found")
    report.append("")

    # Docstring Coverage
    report.append("## Docstring Coverage")
    report.append(
        f"- Functions: {metrics['function_coverage']:.1f}% ({metrics['documented_functions']}/{metrics['total_functions']})")
    report.append(
        f"- Classes: {metrics['class_coverage']:.1f}% ({metrics['documented_classes']}/{metrics['total_classes']})")
    report.append("")

    # Per-file Coverage
    report.append("## Per-file Coverage")
    report.append("| File | Functions | Classes | Overall |")
    report.append("|------|-----------|----------|----------|")
    for file_path, file_metrics in sorted(metrics["files"].items(), key=lambda x: x[1]["overall_coverage"]):
        report.append(
            f"| {file_path} | {file_metrics['function_coverage']:.1f}% | {file_metrics['class_coverage']:.1f}% | {file_metrics['overall_coverage']:.1f}% |"
        )

    return "\n".join(report)


def main():
    """Main validation function."""
    validation_results = {
        "success": True,
        "messages": [],
        "metrics": {
            "readme_score": 0.0,
            "docs_structure_score": 0.0,
            "docstring_coverage": 0.0
        }
    }

    # Check README.md
    readme_exists, missing_sections = check_readme()
    if not readme_exists:
        validation_results["success"] = False
        validation_results["messages"].append("README.md is missing")
    else:
        # Calculate score based on found sections (6 - missing)
        validation_results["metrics"]["readme_score"] = (
            (6 - len(missing_sections)) / 6 * 100  # 6 required sections
        )
        if missing_sections:
            validation_results["messages"].append(
                f"README.md is missing sections: {', '.join(missing_sections)}"
            )

    # Check documentation structure
    structure_exists, existing_components = check_docs_structure()
    if not structure_exists:
        validation_results["messages"].append(
            "Documentation structure is missing")
    else:
        validation_results["metrics"]["docs_structure_score"] = (
            len(existing_components) / 3 * 100  # 3 required components
        )

    # Check docstrings
    docstring_metrics = check_docstrings()
    validation_results["metrics"]["docstring_coverage"] = (
        (docstring_metrics["function_coverage"] +
         docstring_metrics["class_coverage"]) / 2
    )

    # Generate documentation report
    report = generate_docs_report(
        docstring_metrics,
        missing_sections if readme_exists else [],
        existing_components if structure_exists else []
    )

    # Save report artifact
    try:
        with open("docs_report.md", "w", encoding='utf-8') as f:
            f.write(report)
    except IOError as e:
        validation_results["messages"].append(
            f"Error writing docs report: {e}")

    # Overall success criteria
    if (validation_results["metrics"]["readme_score"] < 80 or
        validation_results["metrics"]["docs_structure_score"] < 66 or
            validation_results["metrics"]["docstring_coverage"] < 70):
        validation_results["success"] = False

    print(json.dumps(validation_results))
    return 0 if validation_results["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
