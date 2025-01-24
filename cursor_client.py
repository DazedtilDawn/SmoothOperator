import os
import subprocess
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class OperationResult:
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None


class FileOperations:
    """Utility class for file operations and command execution."""

    def apply_patch(self, patch_file: str) -> OperationResult:
        """Apply a patch file using the git apply command."""
        try:
            if not os.path.exists(patch_file):
                return OperationResult(False, error=f"Patch file not found: {patch_file}")

            # Use git apply to handle the patch
            result = subprocess.run(
                ["git", "apply", patch_file],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return OperationResult(True, content=f"Patch applied successfully: {patch_file}")
            else:
                return OperationResult(False, error=f"Failed to apply patch: {result.stderr}")

        except Exception as e:
            return OperationResult(False, error=str(e))

    def insert_snippet(self, file_path: str, snippet: str, line: int) -> OperationResult:
        """Insert a code snippet at a specific line in a file."""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return OperationResult(False, error=f"Target file not found: {file_path}")

            with open(file_path, 'r') as f:
                lines = f.readlines()

            # Ensure line number is valid
            if line < 1 or line > len(lines) + 1:
                return OperationResult(False, error=f"Invalid line number: {line}")

            # Insert the snippet
            lines.insert(line - 1, snippet + '\n')

            with open(file_path, 'w') as f:
                f.writelines(lines)

            return OperationResult(True, content=f"Snippet inserted at line {line}")

        except Exception as e:
            return OperationResult(False, error=str(e))

    def run_command(self, command: str) -> OperationResult:
        """Run a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return OperationResult(True, content=result.stdout)
            else:
                return OperationResult(False, error=result.stderr)
        except Exception as e:
            return OperationResult(False, error=str(e))
