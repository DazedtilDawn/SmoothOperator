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

    with open(readme_path) as f:
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
        "documented_classes": 0
    }

    for py_file in Path(directory).rglob(pattern):
        with open(py_file) as f:
            content = f.read()

        # Find all function definitions
        function_matches = re.finditer(r"def\s+(\w+)\s*\(", content)
        class_matches = re.finditer(r"class\s+(\w+)\s*[:\(]", content)

        for match in function_matches:
            metrics["total_functions"] += 1
            # Check for docstring after function definition
            pos = match.end()
            next_lines = content[pos:pos+200]  # Look at next 200 chars
            if re.search(r'"""[\s\S]*?"""|\'\'\'.[\s\S]*?\'\'\'', next_lines):
                metrics["documented_functions"] += 1

        for match in class_matches:
            metrics["total_classes"] += 1
            pos = match.end()
            next_lines = content[pos:pos+200]
            if re.search(r'"""[\s\S]*?"""|\'\'\'.[\s\S]*?\'\'\'', next_lines):
                metrics["documented_classes"] += 1

    # Calculate coverage percentages
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

    # Docstring coverage
    report.append("## Docstring Coverage")
    report.append(
        f"- Functions: {metrics['function_coverage']:.1f}% ({metrics['documented_functions']}/{metrics['total_functions']})")
    report.append(
        f"- Classes: {metrics['class_coverage']:.1f}% ({metrics['documented_classes']}/{metrics['total_classes']})")

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
        validation_results["metrics"]["readme_score"] = (
            (len(missing_sections) / 6) * 100  # 6 required sections
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
    with open("docs_report.md", "w") as f:
        f.write(report)

    # Overall success criteria
    if (validation_results["metrics"]["readme_score"] < 80 or
        validation_results["metrics"]["docs_structure_score"] < 66 or
            validation_results["metrics"]["docstring_coverage"] < 70):
        validation_results["success"] = False

    print(json.dumps(validation_results))
    return 0 if validation_results["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
