"""
AgentOps Nexus — Runtime Mode Controller

Enforces strict separation between DEMO and PRODUCTION modes.

DEMO_MODE:
  - Fallbacks allowed (subprocess, regex security, simulator agents)
  - Dashboard shows "DEMO MODE" banner
  - Local repositories only

PRODUCTION_MODE:
  - All dependencies mandatory (GitHub, LLM, Docker, security tools)
  - Zero automatic fallback
  - Aborts with structured ProductionReadinessReport on missing dependency
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from core.config import settings
from backend.tool_registry import ToolRegistry, detect_llm_providers, detect_github


@dataclass
class ReadinessCheck:
    """Single readiness check result."""
    name: str
    required: bool
    available: bool
    detail: str


class ProductionNotReadyError(Exception):
    """Raised when production mode requirements are not met."""
    def __init__(self, report: Dict[str, Any]):
        self.report = report
        failures = [c["name"] for c in report["checks"] if not c["available"]]
        super().__init__(f"Production readiness failed: {', '.join(failures)}")


class RuntimeManager:
    """
    Singleton-like runtime manager that validates system capabilities
    and enforces mode-specific rules.
    """

    def __init__(self):
        self.tool_registry = ToolRegistry()
        self._mode = settings.RUNTIME_MODE.lower()
        self._initialized = False
        self._readiness_report: Optional[Dict[str, Any]] = None

    def initialize(self) -> Dict[str, Any]:
        """
        Run at application startup. Detects all tools and validates mode.
        Returns the health/capabilities report.
        """
        self.tool_registry.detect_all()

        llm_status = detect_llm_providers(
            settings.GEMINI_API_KEY,
            settings.OPENAI_API_KEY,
            settings.ANTHROPIC_API_KEY,
        )

        github_status = detect_github(
            settings.GITHUB_TOKEN,
            settings.GITHUB_REPO_OWNER,
            settings.GITHUB_REPO_NAME,
        )

        checks: List[ReadinessCheck] = [
            ReadinessCheck("git", True, self.tool_registry.has("git"), self._detail("git")),
            ReadinessCheck("docker", self.is_production, self.tool_registry.has("docker"), self._detail("docker")),
            ReadinessCheck("pytest", True, self.tool_registry.has("pytest"), self._detail("pytest")),
            ReadinessCheck("semgrep", self.is_production, self.tool_registry.has("semgrep"), self._detail("semgrep")),
            ReadinessCheck("bandit", self.is_production, self.tool_registry.has("bandit"), self._detail("bandit")),
            ReadinessCheck("trivy", self.is_production, self.tool_registry.has("trivy"), self._detail("trivy")),
            ReadinessCheck("gitleaks", self.is_production, self.tool_registry.has("gitleaks"), self._detail("gitleaks")),
            ReadinessCheck("llm_provider", self.is_production, llm_status["any_available"], "At least one LLM API key configured"),
            ReadinessCheck("github", self.is_production, github_status["fully_configured"], "GitHub token + repo configured"),
        ]

        self._readiness_report = {
            "runtime_mode": self._mode,
            "checks": [{"name": c.name, "required": c.required, "available": c.available, "detail": c.detail} for c in checks],
            "tools": self.tool_registry.get_summary(),
            "llm": llm_status,
            "github": github_status,
            "production_ready": all(c.available for c in checks if c.required),
        }

        self._initialized = True
        return self._readiness_report

    def _detail(self, tool_name: str) -> str:
        cap = self.tool_registry.get(tool_name)
        if cap and cap.available:
            return cap.version or "Available"
        elif cap:
            return cap.error or "Not available"
        return "Not detected"

    @property
    def is_production(self) -> bool:
        return self._mode == "production"

    @property
    def is_demo(self) -> bool:
        return self._mode == "demo"

    @property
    def mode(self) -> str:
        return self._mode

    def assert_production_ready(self) -> None:
        """
        Call before starting a production run.
        Raises ProductionNotReadyError if any required dependency is missing.
        """
        if not self._initialized:
            self.initialize()

        if self.is_production and not self._readiness_report["production_ready"]:
            raise ProductionNotReadyError(self._readiness_report)

    def get_health_report(self) -> Dict[str, Any]:
        """Returns the full health/capabilities report for the API."""
        if not self._initialized:
            self.initialize()
        return self._readiness_report

    def can_use(self, tool_name: str) -> bool:
        """
        Check if a tool can be used in the current mode.
        In production mode, required tools MUST be available (or we would have aborted).
        In demo mode, returns True if available, False otherwise (fallback allowed).
        """
        return self.tool_registry.has(tool_name)
