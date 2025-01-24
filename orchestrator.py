from cursor_client import FileOperations, OperationResult
from external_ai_integration import LMStudioClient
from validation_system.blockers.auto_blocker_resolver import BlockerResolver
from validation_system.core import TransitionValidator
from pathlib import Path
import json
import subprocess
import argparse


class TaskResult:
    def __init__(self, success: bool, error_message: str = ""):
        self.success = success
        self.error_message = error_message


class Orchestrator:
    def __init__(self, checklist_dir: str = ".checklists", patches_dir: str = ".patches"):
        self.checklist_dir = Path(checklist_dir)
        self.patches_dir = Path(patches_dir)
        self.patches_dir.mkdir(exist_ok=True)
        self.current_checklist = None
        self.status = {}
        self.results = {}
        self.validator = TransitionValidator("transition_artifacts")
        self.file_ops = FileOperations()
        self.lmstudio_client = LMStudioClient()
        self.blocker_resolver = BlockerResolver()

    def load_checklist(self, checklist_name: str) -> None:
        """Load a checklist from the checklist directory."""
        self.checklist_name = checklist_name  # Store the checklist name
        checklist_path = self.checklist_dir / f"{checklist_name}.json"
        if not checklist_path.exists():
            raise FileNotFoundError(f"Checklist {checklist_name} not found")

        with open(checklist_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if "checklist" not in data:
            raise ValueError("Invalid checklist format: missing 'checklist' key")
        
        checklist = data["checklist"]
        if "phases" not in checklist:
            raise ValueError("Invalid checklist format: missing 'phases' key")
        
        self.current_checklist = data
        
        # Try to load existing status
        status_path = Path(f"{checklist_name}_status.json")
        if status_path.exists():
            with open(status_path, 'r', encoding='utf-8') as f:
                self.status = json.load(f)
        else:
            # Initialize new status
            self.status = {
                phase["name"]: {
                    "status": "not_started",
                    "tasks": {
                        task["description"]: "not_started"
                        for task in phase.get("tasks", [])
                    }
                }
                for phase in checklist["phases"]
            }
            # Save initial status
            self._save_status()
        
        self.results = {}

    def _save_status(self) -> None:
        """Save the current status to a file."""
        if not self.current_checklist or not hasattr(self, 'checklist_name'):
            return

        status_path = Path(f"{self.checklist_name}_status.json")
        try:
            with open(status_path, 'w', encoding='utf-8') as f:
                json.dump(self.status, f, indent=4)
        except Exception as e:
            print(f"Warning: Failed to save status: {e}")

    def execute_checklist(self) -> int:
        """Execute all phases and tasks in the checklist."""
        if not self.current_checklist:
            print("No checklist loaded")
            return 1

        try:
            phases = self.current_checklist["checklist"]["phases"]
            for phase in phases:
                phase_name = phase["name"]
                print(f"\nExecuting phase: {phase_name}")

                # Update phase status
                if phase_name not in self.status:
                    self.status[phase_name] = {
                        "status": "not_started", "tasks": {}}
                self.status[phase_name]["status"] = "in_progress"
                self._save_status()

                for task in phase.get("tasks", []):
                    task_desc = task["description"]
                    print(f"\nTask: {task_desc}")

                    # Update task status
                    if "tasks" not in self.status[phase_name]:
                        self.status[phase_name]["tasks"] = {}
                    self.status[phase_name]["tasks"][task_desc] = "in_progress"
                    self._save_status()

                    # Check for blockers
                    blockers = task.get("blockers", [])
                    if blockers:
                        print("Checking blockers...")
                        unresolved = self.blocker_resolver.resolve_blockers(
                            blockers)
                        if unresolved:
                            print("Task blocked by:")
                            for blocker in unresolved:
                                print(f"- {blocker['type']}")
                                if "resolution" in blocker["resolution"]:
                                    if "required_experts" in blocker["resolution"]:
                                        experts = blocker["resolution"]["required_experts"]
                                        print(
                                            f"  Required experts: {', '.join(experts)}")
                                    if "diagnostics" in blocker["resolution"]:
                                        print(
                                            f"  Run diagnostics: {blocker['resolution']['diagnostics']}")
                            self.status[phase_name]["tasks"][task_desc] = "blocked"
                            self._save_status()
                            continue
                        print("All blockers resolved")

                    # Execute the task
                    if "command" in task:
                        print(f"Executing: {task['command']}")
                        try:
                            result = subprocess.run(
                                task["command"],
                                shell=True,
                                capture_output=True,
                                text=True
                            )
                            if result.returncode != 0:
                                print(
                                    f"Task failed with error:\n{result.stderr}")
                                self.status[phase_name]["tasks"][task_desc] = "failed"
                                self._save_status()
                                return 1
                            print(f"Output:\n{result.stdout}")
                        except Exception as e:
                            print(f"Error executing task: {str(e)}")
                            self.status[phase_name]["tasks"][task_desc] = "failed"
                            self._save_status()
                            return 1

                    # Run validation if present
                    if "validation" in task:
                        print("Running validation...")
                        try:
                            script = task["validation"]["script"]
                            validation_result = subprocess.run(
                                ["python", script],
                                capture_output=True,
                                text=True
                            )
                            if validation_result.returncode != 0:
                                print(
                                    f"Validation failed:\n{validation_result.stderr}")
                                self.status[phase_name]["tasks"][task_desc] = "failed"
                                self._save_status()
                                return 1
                            print("Validation passed")
                        except Exception as e:
                            print(f"Error during validation: {str(e)}")
                            self.status[phase_name]["tasks"][task_desc] = "failed"
                            self._save_status()
                            return 1

                    self.status[phase_name]["tasks"][task_desc] = "completed"
                    self._save_status()

                # Check phase success gate if present
                if "success_gate" in phase:
                    print(f"\nChecking success gate for phase {phase_name}...")
                    gate = phase["success_gate"]
                    if not self._check_success_gate(gate):
                        print("Phase failed to meet success gate criteria")
                        self.status[phase_name]["status"] = "failed"
                        self._save_status()
                        return 1
                    print("Success gate passed")

                self.status[phase_name]["status"] = "completed"
                self._save_status()

            print("\nChecklist execution completed successfully")
            return 0

        except Exception as e:
            print(f"Error executing checklist: {str(e)}")
            return 1

    def _check_success_gate(self, gate: dict) -> bool:
        """Check if a phase's success gate criteria are met."""
        try:
            if "metric" not in gate:
                return True

            metric = gate["metric"]
            min_value = gate.get("min_value", 0)

            if metric == "integration_test_coverage":
                # TODO: Implement coverage check
                return True

            if metric == "api_test_coverage":
                # TODO: Implement API coverage check
                return True

            if metric == "validation_coverage":
                # TODO: Implement validation coverage check
                return True

            return True

        except Exception as e:
            print(f"Error checking success gate: {str(e)}")
            return False

    def display_status(self) -> str:
        """Display the current status of all phases and tasks."""
        if not self.current_checklist:
            return "No checklist loaded"

        output = []
        output.append(
            f"📋 Checklist: {self.current_checklist['checklist']['name']}")
        output.append("=" * 50)
        output.append("")

        for phase in self.current_checklist["checklist"]["phases"]:
            phase_name = phase["name"]
            phase_status = self.status.get(
                phase_name, {}).get("status", "not_started")
            status_emoji = {
                "not_started": "⚪",
                "in_progress": "🔄",
                "completed": "✅",
                "failed": "❌",
                "blocked": "⛔"
            }.get(phase_status, "❓")

            output.append(
                f"{status_emoji} Phase: {phase_name} [{phase_status}]")

            if "success_gate" in phase:
                gate = phase["success_gate"]
                output.append(
                    f"   🎯 Success Gate: {gate['metric']} (min: {gate['min_value']})")

            for task in phase.get("tasks", []):
                task_desc = task["description"]
                task_status = self.status.get(phase_name, {}).get(
                    "tasks", {}).get(task_desc, "not_started")
                task_emoji = {
                    "not_started": "⚪",
                    "in_progress": "🔄",
                    "completed": "✅",
                    "failed": "❌",
                    "blocked": "⛔"
                }.get(task_status, "❓")
                output.append(f"   {task_emoji} {task_desc} [{task_status}]")

            output.append("")

        return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrate checklist execution")
    parser.add_argument("--checklist", required=True,
                        help="Name of the checklist to execute")
    parser.add_argument("--status", action="store_true",
                        help="Display checklist status")
    args = parser.parse_args()

    orchestrator = Orchestrator()
    try:
        orchestrator.load_checklist(args.checklist)
        if args.status:
            print(orchestrator.display_status())
        else:
            return orchestrator.execute_checklist()
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
