from typing import List, Dict, Any
from external_ai_integration import LMStudioClient


class BlockerResolver:
    """Resolver for automatically checking and resolving task blockers."""

    def __init__(self):
        """Initialize the BlockerResolver with an LMStudio client."""
        self.ai_client = LMStudioClient()

    def resolve_blockers(self, blockers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Attempt to resolve a list of blockers.
        Returns a list of blockers that could not be resolved.
        """
        unresolved = []
        for blocker in blockers:
            if not self._check_if_resolved(blocker):
                unresolved.append(blocker)
        return unresolved

    def _check_if_resolved(self, blocker: Dict[str, Any]) -> bool:
        """
        Check if a blocker is resolved by running its diagnostics
        and analyzing the resolution requirements.
        """
        resolution = blocker.get("resolution", {})

        # Run diagnostics if available
        if "diagnostics" in resolution:
            import subprocess
            try:
                result = subprocess.run(
                    resolution["diagnostics"],
                    shell=True,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    return False

                # Parse JSON output if present
                try:
                    import json
                    output = json.loads(result.stdout)
                    if output.get("status") != "success":
                        return False
                except json.JSONDecodeError:
                    pass
            except Exception:
                return False

        # Check if LMStudio prompt is available and use it
        prompt = resolution.get("lmstudio_prompt")
        if prompt:
            response = self.ai_client.generate_prompt({
                "phase": "Blocker Resolution",
                "task_description": f"Checking blocker: {blocker['type']}",
                "implementation_data": prompt
            })
            return "resolved" in response.lower()

        # If no diagnostics or prompt, check if required experts are available
        required_experts = resolution.get("required_experts", [])
        if not required_experts:
            # If no experts are required and no diagnostics failed, consider it resolved
            return True

        return False
