"""
AgentOps Nexus — Run Context & Concurrency Isolation

Every execution run gets a fully isolated context that prevents:
- Race conditions between concurrent runs
- Shared artifact collisions
- Cross-run state leakage

All shared resources are scoped by run_id.
"""
import os
import uuid
import shutil
import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


import hashlib

@dataclass
class RunContext:
    """
    Immutable execution context for a single pipeline run.
    Created once at run start, never modified.
    All paths and identifiers are scoped to this run.
    """
    run_id: str
    issue_id: str
    issue_title: str
    issue_description: str
    repo_path: str                    # Original repo path
    work_dir: str                     # Isolated working directory for this run
    evidence_dir: str                 # Immutable evidence output directory
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    # ── Immutable Properties ──
    _runtime_mode: str = "demo"
    _llm_execution_config: Dict[str, Any] = field(default_factory=dict)
    _llm_configuration_locked: bool = False

    # ── Environment Hashes ──
    container_image_digest: str = "unknown"
    dependency_lock_hash: str = "unknown"
    environment_variable_hash: str = "unknown"

    @property
    def runtime_mode(self) -> str:
        return self._runtime_mode

    @runtime_mode.setter
    def runtime_mode(self, value: str):
        if self._llm_configuration_locked:
            raise RuntimeError("IMMUTABLE_RUNTIME_MODE_VIOLATION")
        self._runtime_mode = value

    @property
    def llm_execution_config(self) -> Dict[str, Any]:
        return self._llm_execution_config

    @llm_execution_config.setter
    def llm_execution_config(self, value: Dict[str, Any]):
        if self._llm_configuration_locked:
            raise RuntimeError("IMMUTABLE_CONFIGURATION_VIOLATION")
        self._llm_execution_config = value

    @property
    def llm_configuration_locked(self) -> bool:
        return self._llm_configuration_locked

    def lock_configuration(self):
        self._llm_configuration_locked = True

    @staticmethod
    def create(
        issue_id: str,
        issue_title: str,
        issue_description: str,
        repo_path: str,
        base_evidence_dir: str,
        runtime_mode: str = "demo",
        run_id: Optional[str] = None,
    ) -> "RunContext":
        """Factory method to create an isolated run context."""
        if not run_id:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            run_id = f"run_{timestamp}_{issue_id}_{uuid.uuid4().hex[:8]}"

        # Each run gets its own working directory (copy of repo)
        work_dir = os.path.join(os.path.dirname(repo_path), f".nexus_runs", run_id)

        # Each run gets its own evidence output directory
        evidence_dir = os.path.join(base_evidence_dir, run_id)

        return RunContext(
            run_id=run_id,
            issue_id=issue_id,
            issue_title=issue_title,
            issue_description=issue_description,
            repo_path=repo_path,
            work_dir=work_dir,
            evidence_dir=evidence_dir,
            _runtime_mode=runtime_mode,
            container_image_digest=hashlib.sha256(b"image_v1").hexdigest(),
            dependency_lock_hash=hashlib.sha256(b"deps_v1").hexdigest(),
            environment_variable_hash=hashlib.sha256(os.environ.get("PATH", "").encode()).hexdigest()
        )

    def setup(self) -> None:
        """Create the isolated working directory by copying the source repo."""
        # Create work directory
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)

        if os.path.exists(self.repo_path):
            shutil.copytree(
                self.repo_path,
                self.work_dir,
                ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache', '*.pyc')
            )
        else:
            os.makedirs(self.work_dir, exist_ok=True)

        # Create evidence directory
        os.makedirs(self.evidence_dir, exist_ok=True)

    def cleanup(self) -> None:
        """Remove the isolated working directory (evidence is preserved)."""
        if os.path.exists(self.work_dir):
            try:
                shutil.rmtree(self.work_dir)
            except Exception:
                pass  # Best-effort cleanup

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "issue_id": self.issue_id,
            "issue_title": self.issue_title,
            "repo_path": self.repo_path,
            "work_dir": self.work_dir,
            "evidence_dir": self.evidence_dir,
            "created_at": self.created_at,
            "runtime_mode": self.runtime_mode,
        }
