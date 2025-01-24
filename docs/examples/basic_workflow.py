#!/usr/bin/env python3
"""
Basic workflow example using the Smooth Operator system.
This example demonstrates how to:
1. Load and execute a checklist
2. Handle validation results
3. Generate and collect artifacts
"""

import sys
from pathlib import Path
from orchestrator import Orchestrator
from validation_system.core import TaskResult


def main():
    """Execute a basic workflow using the Smooth Operator system.

    This function demonstrates:
    1. Loading a checklist from a YAML file
    2. Starting and executing phases
    3. Running validation tasks
    4. Handling validation results and artifacts

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    # Initialize the orchestrator
    orchestrator = Orchestrator()

    # Load the example checklist
    checklist_path = Path(".checklists") / "example_workflow.yaml"
    if not orchestrator.load_checklist(str(checklist_path)):
        print("Error: Failed to load checklist")
        return 1

    # Start the workflow
    if not orchestrator.start_phase("Setup"):
        print("Error: Failed to start Setup phase")
        return 1

    # Execute setup tasks
    tasks = [
        ("Git Configuration", "Validating Git setup..."),
        ("Documentation", "Checking documentation standards..."),
    ]

    for task_name, message in tasks:
        print(message)
        result = orchestrator.execute_task("Setup", task_name)
        if not result.success:
            print(f"Error in {task_name}: {result.error_message}")
            return 1

        print(f"✓ {task_name} completed successfully")
        if result.artifacts:
            print("Generated artifacts:")
            for artifact in result.artifacts:
                print(f"  - {artifact}")
        print()

    # Move to the next phase
    if not orchestrator.start_phase("Development"):
        print("Error: Failed to start Development phase")
        return 1

    print("Workflow completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
