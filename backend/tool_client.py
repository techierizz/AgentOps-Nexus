import subprocess
import hashlib
import json
import datetime
from typing import List, Dict, Any, Tuple

class ToolEvidenceMissingError(Exception):
    pass

class ToolClient:
    """
    Cryptographic wrapper for external tool executions.
    Ensures that every tool invocation generates immutable evidence.
    """
    
    @staticmethod
    def run(artifacts, tool_name: str, cmd: List[str], cwd: str = None, execution_id: str = "unknown", env_hash: str = "unknown", container_digest: str = "unknown") -> Tuple[int, str, str]:
        if not all([tool_name, cmd, execution_id, env_hash, container_digest]):
            raise ToolEvidenceMissingError("TOOL_EVIDENCE_INVALID")

        # Hash the command
        cmd_str = " ".join(cmd)
        command_hash = hashlib.sha256(cmd_str.encode("utf-8")).hexdigest()
        
        try:
            res = subprocess.run(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            stdout_text = res.stdout
            stderr_text = res.stderr
            exit_code = res.returncode
        except Exception as e:
            # If the tool completely fails to launch, record the failure
            stdout_text = ""
            stderr_text = str(e)
            exit_code = -1

        stdout_hash = hashlib.sha256(stdout_text.encode("utf-8")).hexdigest()
        stderr_hash = hashlib.sha256(stderr_text.encode("utf-8")).hexdigest()

        event = {
            "event_type": "TOOL_EXECUTION",
            "tool_name": tool_name,
            "tool_version": "unknown",  # Could be resolved if needed
            "command_hash": command_hash,
            "full_command_string": cmd_str,
            "stdout_hash": stdout_hash,
            "stderr_hash": stderr_hash,
            "exit_code": exit_code,
            "environment_hash": env_hash,
            "container_image_digest": container_digest,
            "execution_id": execution_id,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        try:
            artifacts.record("tool_execution", event)
        except Exception as e:
            raise ToolEvidenceMissingError(f"TOOL_EVIDENCE_INVALID: {e}")
            
        return exit_code, stdout_text, stderr_text
