import os
from pydantic_settings import BaseSettings
from typing import Optional

def _resolve_base_dir() -> str:
    """Resolve project root from environment or by walking up from this file."""
    env_val = os.environ.get("BASE_DIR")
    if env_val and os.path.isdir(env_val):
        return os.path.abspath(env_val)
    # Default: two levels up from backend/config.py → project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    PROJECT_NAME: str = "AgentOps Nexus API"
    API_VERSION: str = "v1"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # ── Runtime Mode ──────────────────────────────────────────
    # "demo" = fallbacks allowed | "production" = zero fallbacks
    RUNTIME_MODE: str = "demo"

    # ── Agent Mode ────────────────────────────────────────────
    # "simulator" = deterministic | "llm" = live LLM reasoning
    AGENT_MODE: str = "simulator"

    # ── Path Settings (platform-portable) ─────────────────────
    BASE_DIR: str = _resolve_base_dir()

    @property
    def demo_repo_path(self) -> str:
        return os.path.join(self.BASE_DIR, "demo_target_repo")

    @property
    def evidence_dir(self) -> str:
        return os.path.join(self.BASE_DIR, "artifacts")

    @property
    def db_path(self) -> str:
        return os.path.join(self.BASE_DIR, "backend", "nexus.db")

    @property
    def memory_store_path(self) -> str:
        return os.path.join(self.BASE_DIR, "backend", "memory_store.json")

    # ── GitHub Integration ────────────────────────────────────
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    GITHUB_REPO_OWNER: Optional[str] = None
    GITHUB_REPO_NAME: Optional[str] = None

    # ── LLM Providers ────────────────────────────────────────
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_PRIMARY_MODEL: str = "gemini-2.5-flash"

    # ── Budget Limits (per run) ───────────────────────────────
    MAX_TOKENS_PER_RUN: int = 500000
    MAX_COST_PER_RUN: float = 5.00
    MAX_EXECUTION_SECONDS: int = 600
    MAX_FILES_MODIFIED: int = 10
    MAX_LINES_CHANGED: int = 500
    MAX_PATCH_ITERATIONS: int = 3

    # ── Capability Flags (auto-detected at startup) ───────────
    # These are set by the ToolRegistry, not by the user.
    # Kept here for reference only.

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
