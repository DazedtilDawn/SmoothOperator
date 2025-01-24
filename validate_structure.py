import sys
import os
import argparse
import yaml
import subprocess
import logging

# Import your existing validation system
from transition_checklist.validation_system import TransitionValidator, ChecklistStatus

# OPTIONAL: If you have a local Python interface for Cursor AI or external AI
# from your_ai_integration import CursorAI  # (Placeholder for actual AI invocation)

# OPTIONAL: If you want to call collect_diagnostics.sh
COLLECT_SCRIPT = "transition_checklist/collect_diagnostics.sh"

# Example: Where to store overall orchestrator logs
ORCHESTRATOR_LOG = "transition_artifacts/orchestrator.log"

# Setup module-level logger
logging.basicConfig(
    filename=ORCHESTRATOR_LOG,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AIChecklistOrchestrator:
    """
    Orchestrator class that reads tasks from a YAML checklist,
    executes them, and calls validation methods from transition_checklist/validation_system.py.
    """

    def __init__(self, checklist_path, collect_diagnostics=False, use_cursor_ai=False):
        self.checklist_path = checklist_path
        self.collect_diagnostics = collect_diagnostics
        self.use_cursor_ai = use_cursor_ai

        # Create a TransitionValidator instance from your existing system
        self.validator = TransitionValidator(
            artifacts_dir="transition_artifacts")

        # In-memory store for phase/task statuses
        # e.g. { phase_name: [ (task_desc, success_bool, message), ... ] }
        self.results = {}

        # Attempt to load the YAML checklist
        self.checklist_data = self._load_checklist()

        # If you have an AI interface, you could instantiate it here
        # self.ai_client = CursorAI() if self.use_cursor_ai else None

    def _load_checklist(self):
        if not os.path.exists(self.checklist_path):
            logger.error(f"Checklist file not found: {self.checklist_path}")
            sys.exit(1)

        with open(self.checklist_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not data or "phases" not in data:
                logger.error(
                    "Invalid checklist file format. 'phases' key missing.")
                sys.exit(1)
            return data

    def run(self):
        """
        Main entry point to iterate over phases and tasks in the checklist,
        execute them, and run validations.
        """
        phases = self.checklist_data.get("phases", [])
        for phase in phases:
            phase_name = phase.get("name", "Unnamed Phase")
            tasks = phase.get("tasks", [])
            logger.info(f"--- Starting Phase: {phase_name} ---")
            self.results[phase_name] = []

            for task in tasks:
                success, message = self._execute_task(phase_name, task)
                # Store the result
                self.results[phase_name].append(
                    (task.get("description", "Task"), success, message))

            # Possibly skip next phases if a critical failure
            # (You can add logic here if you want to abort on failure)

        # After all phases, generate a final orchestrator report
        self._generate_orchestrator_report()

        # If requested, optionally run diagnostics script
        if self.collect_diagnostics:
            self._run_diagnostics()

        logger.info("All phases completed. Orchestrator exiting.")

    def _execute_task(self, phase_name, task):
        """
        Execute a single task from the checklist.
        This can include applying patches, running a command, or using AI prompts.
        After the task, we run the associated validation from transition_checklist.validation_system.
        """

        description = task.get("description", "No description")
        logger.info(f"[{phase_name}] Executing Task: {description}")

        # 1) Possibly apply a patch
        if "patch_file" in task:
            patch_file = task["patch_file"]
            success, message = self._apply_patch(patch_file)
            if not success:
                return (False, f"Patch application failed: {message}")

        # 2) Possibly run a command
        if "cmd" in task:
            cmd = task["cmd"]
            success, message = self._run_shell_command(cmd)
            if not success:
                return (False, f"Command failed: {message}")

        # 3) Possibly do an AI-based code modification
        if self.use_cursor_ai and "ai_prompt" in task:
            ai_prompt = task["ai_prompt"]
            success, message = self._run_ai_modification(ai_prompt)
            if not success:
                return (False, f"AI code modification failed: {message}")

        # 4) Artifacts: If the checklist says an artifact is expected, we can check existence
        artifacts = task.get("artifacts", [])
        for artifact in artifacts:
            if not os.path.exists(artifact):
                logger.warning(f"Expected artifact not found: {artifact}")

        # 5) Validation
        validation_method_name = task.get("validation")
        if validation_method_name:
            success, message = self._call_validation_method(
                validation_method_name, artifacts)
            return (success, message)

        # If no validation or patch or command, assume success
        return (True, "Task completed successfully (no validation)")

    def _apply_patch(self, patch_file):
        """Apply a unified diff patch to the codebase using git apply."""
        if not os.path.exists(patch_file):
            return (False, f"Patch file not found: {patch_file}")
        cmd = ["git", "apply", patch_file]
        logger.info(f"Applying patch: {patch_file}")
        try:
            subprocess.run(cmd, check=True)
            return (True, "Patch applied successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error applying patch: {str(e)}")
            return (False, str(e))

    def _run_shell_command(self, cmd):
        """Run a shell command and return success/fail plus any output or error."""
        logger.info(f"Running command: {cmd}")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, check=True)
            if result.stdout:
                logger.info(result.stdout.strip())
            if result.stderr:
                logger.info(result.stderr.strip())
            return (True, "Command succeeded")
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Command failed with return code {e.returncode}: {e.stderr}")
            return (False, e.stderr.strip())

    def _run_ai_modification(self, prompt):
        """
        Example of how you might call Cursor AI or another AI to modify code automatically.
        This is a placeholder method: adapt to your actual AI interface.
        """
        logger.info(f"Using AI to address prompt: {prompt}")
        # Here you'd do something like:
        #   response = self.ai_client.modify_code(prompt=prompt)
        #   if response.succeeded:
        #       return (True, "AI modification succeeded")
        #   else:
        #       return (False, response.error_message)

        # For demonstration, we pretend success
        return (True, "AI code modification succeeded (placeholder)")

    def _call_validation_method(self, method_name, artifacts=None):
        """
        Call a specific method on the TransitionValidator instance, returning (bool, message).
        We match the method_name with the ones in validation_system.py
        """
        if not hasattr(self.validator, method_name):
            logger.warning(
                f"Validation method {method_name} not found in TransitionValidator.")
            return (False, f"Validation method {method_name} not found")

        # Some validations require file paths, see your existing system
        # e.g. validate_no_wizard_dependencies(self, dependency_map, wizard_refs)
        # We'll guess based on known signatures or pass nothing:
        method = getattr(self.validator, method_name)

        try:
            # Example: if method_name == "validate_no_wizard_dependencies", we guess we have
            # 'dependency_map.dot' and 'wizard_references.txt' as artifacts.
            # In reality, you'd parse or pass from the checklist or artifacts array:
            if method_name == "validate_no_wizard_dependencies":
                # Possibly find relevant artifacts from the list
                # This is 100% example logic—adapt to your real usage
                dependency_map = next(
                    (a for a in artifacts if "dependency_map" in a), None)
                wizard_refs = next(
                    (a for a in artifacts if "wizard_references" in a), None)
                if not dependency_map or not wizard_refs:
                    return (False, "Missing required artifacts for validate_no_wizard_dependencies")
                ok, msg = method(dependency_map, wizard_refs)

            elif method_name == "validate_code_changes":
                # Similarly
                patch_file = next(
                    (a for a in artifacts if "code_diff" in a or "patch" in a), None)
                if not patch_file:
                    return (False, "Missing patch artifact for validate_code_changes")
                ok, msg = method(patch_file)

            elif method_name == "validate_advanced_view_functionality":
                # e.g. we expect the test_results.xml among the artifacts
                test_xml = next(
                    (a for a in artifacts if "test_results" in a and a.endswith(".xml")), None)
                if not test_xml:
                    return (False, "Missing test XML for advanced view validation")
                ok, msg = method(test_xml)

            else:
                # For other methods, you might need to pass arguments differently or read them from the checklist
                # If it's a no-argument method, just call it:
                ok, msg = method()

            # Update deliverable status if you want
            # For demonstration, let's say each validation is tied to one deliverable
            # (Your system is more flexible: you might have to figure out which deliverable to update)
            # e.g. self.validator.update_deliverable_status("dependency_map", ...)

            return (ok, msg)
        except Exception as e:
            logger.error(
                f"Exception calling validation {method_name}: {str(e)}")
            return (False, str(e))

    def _generate_orchestrator_report(self):
        """
        Summarize phase/task results to a markdown file, e.g. transition_artifacts/orchestrator_report.md
        """
        lines = ["# Orchestrator Report", ""]
        for phase_name, tasks in self.results.items():
            lines.append(f"## Phase: {phase_name}")
            for (task_desc, success, message) in tasks:
                status_str = "PASS" if success else "FAIL"
                lines.append(f"- **Task**: {task_desc}")
                lines.append(f"  - **Result**: {status_str}")
                lines.append(f"  - **Message**: {message}")
            lines.append("")  # blank line

        report_path = os.path.join(
            "transition_artifacts", "orchestrator_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Orchestrator report generated at {report_path}")

    def _run_diagnostics(self):
        """
        Optionally invoke the collect_diagnostics.sh script
        """
        if not os.path.exists(COLLECT_SCRIPT):
            logger.warning(f"Diagnostic script not found: {COLLECT_SCRIPT}")
            return
        logger.info("Running diagnostics script...")
        try:
            subprocess.run([COLLECT_SCRIPT, "--include-logs",
                           "--include-traces"], check=True)
            logger.info("Diagnostics script completed.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Diagnostics script failed: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="AI Orchestrator for wizard removal or other transitions.")
    parser.add_argument("--checklist", required=True,
                        help="Path to the YAML checklist.")
    parser.add_argument("--collect-diagnostics", action="store_true",
                        help="Run collect_diagnostics.sh on completion.")
    parser.add_argument("--use-cursor-ai", action="store_true",
                        help="Use Cursor AI to automatically modify code.")

    args = parser.parse_args()

    orchestrator = AIChecklistOrchestrator(
        checklist_path=args.checklist,
        collect_diagnostics=args.collect_diagnostics,
        use_cursor_ai=args.use_cursor_ai
    )
    orchestrator.run()


if __name__ == "__main__":
    main()
