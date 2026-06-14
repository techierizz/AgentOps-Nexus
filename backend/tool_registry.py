"""
AgentOps Nexus — Tool Abstraction Layer & Capability Registry

Centralized detection and registration of external tool capabilities.
The system uses this registry to determine what's available at runtime
and degrade gracefully in demo mode (or abort in production mode).
"""
import subprocess
import shutil
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ToolCapability:
    """Status of a single external tool."""
    name: str
    available: bool
    version: Optional[str] = None
    path: Optional[str] = None
    error: Optional[str] = None


class ToolRegistry:
    """
    Detects and registers available external tools at startup.

    Checked tools:
    - git
    - docker
    - pytest
    - semgrep
    - bandit
    - trivy
    - gitleaks

    Usage:
        registry = ToolRegistry()
        registry.detect_all()
        if registry.has("docker"):
            # use docker
        else:
            # fallback or abort
    """

    def __init__(self):
        self._capabilities: Dict[str, ToolCapability] = {}

    def detect_all(self) -> None:
        """Run detection for all known tools."""
        self._detect_tool("git", ["git", "--version"])
        self._detect_tool("docker", ["docker", "--version"])
        self._detect_tool("pytest", ["pytest", "--version"])
        self._detect_tool("semgrep", ["semgrep", "--version"])
        self._detect_tool("bandit", ["bandit", "--version"])
        self._detect_tool("trivy", ["trivy", "--version"])
        self._detect_tool("gitleaks", ["gitleaks", "version"])

    def _detect_tool(self, name: str, version_cmd: list) -> None:
        """Attempt to detect a tool by running its version command."""
        try:
            binary_path = shutil.which(version_cmd[0])
            if not binary_path:
                self._capabilities[name] = ToolCapability(
                    name=name, available=False, error="Binary not found in PATH"
                )
                return

            result = subprocess.run(
                version_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                version = (result.stdout.strip() or result.stderr.strip()).split("\n")[0]
                self._capabilities[name] = ToolCapability(
                    name=name, available=True, version=version, path=binary_path
                )
            else:
                self._capabilities[name] = ToolCapability(
                    name=name, available=False,
                    error=f"Exit code {result.returncode}: {result.stderr.strip()[:200]}"
                )
        except subprocess.TimeoutExpired:
            self._capabilities[name] = ToolCapability(
                name=name, available=False, error="Detection timed out"
            )
        except Exception as e:
            self._capabilities[name] = ToolCapability(
                name=name, available=False, error=str(e)[:200]
            )

    def has(self, tool_name: str) -> bool:
        """Check if a tool is available."""
        cap = self._capabilities.get(tool_name)
        return cap.available if cap else False

    def get(self, tool_name: str) -> Optional[ToolCapability]:
        """Get full capability details for a tool."""
        return self._capabilities.get(tool_name)

    def get_all(self) -> Dict[str, ToolCapability]:
        """Get all detected capabilities."""
        return dict(self._capabilities)

    def get_summary(self) -> Dict[str, Dict]:
        """Get a serializable summary of all capabilities."""
        return {
            name: {
                "available": cap.available,
                "version": cap.version,
                "path": cap.path,
                "error": cap.error,
            }
            for name, cap in self._capabilities.items()
        }

    def get_missing_for_production(self) -> list:
        """Returns list of tools required for production that are missing."""
        required_production = ["git", "docker", "pytest", "semgrep", "bandit", "trivy", "gitleaks"]
        missing = []
        for tool in required_production:
            if not self.has(tool):
                cap = self._capabilities.get(tool)
                missing.append({
                    "tool": tool,
                    "error": cap.error if cap else "Not detected",
                })
        return missing


# ── LLM Provider Detection ──────────────────────────────────

def detect_llm_providers(gemini_key: Optional[str], openai_key: Optional[str], anthropic_key: Optional[str]) -> Dict[str, bool]:
    """Check which LLM providers have API keys configured."""
    return {
        "gemini": bool(gemini_key),
        "openai": bool(openai_key),
        "anthropic": bool(anthropic_key),
        "any_available": bool(gemini_key or openai_key or anthropic_key),
    }


# ── GitHub Detection ─────────────────────────────────────────

def detect_github(token: Optional[str], owner: Optional[str], repo: Optional[str]) -> Dict[str, bool]:
    """Check if GitHub integration is configured."""
    return {
        "token_present": bool(token),
        "repo_configured": bool(owner and repo),
        "fully_configured": bool(token and owner and repo),
    }
