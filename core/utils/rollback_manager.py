"""
AgentOps Nexus — Repository Rollback Manager

Branch-per-run strategy for deterministic restore.
Guarantees no partial state corruption during iterative patching.

Flow per patch iteration:
  1. create_snapshot() → save current state
  2. apply patch
  3. run validation/tests
  4. If pass → commit_snapshot()
  5. If fail → rollback() → restore clean state
"""
import os
import shutil
import subprocess
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Snapshot:
    """Record of a repository snapshot."""
    snapshot_id: str
    iteration: int
    commit_hash: Optional[str] = None
    branch_name: Optional[str] = None
    backup_dir: Optional[str] = None
    status: str = "created"  # created, committed, rolled_back


class RollbackManager:
    """
    Manages repository state snapshots and rollbacks during patch iterations.

    Strategy:
    - If git is available: uses branch-per-run with stash/reset
    - If git is not available: uses filesystem copy (backup directory)

    Both strategies guarantee deterministic restore.
    """

    def __init__(self, work_dir: str, run_id: str, git_available: bool = True):
        self.work_dir = os.path.abspath(work_dir)
        self.run_id = run_id
        self.git_available = git_available and self._check_git()
        self._snapshots: List[Snapshot] = []
        self._backup_base = os.path.join(os.path.dirname(work_dir), f".nexus_backups", run_id)

    def _check_git(self) -> bool:
        """Check if git is available and work_dir is a git repo (or can be initialized)."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_git(self, args: list) -> tuple:
        """Run a git command in the working directory."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.work_dir,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace"
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return -1, "", str(e)

    def _ensure_git_repo(self) -> None:
        """Initialize git repo if needed."""
        git_dir = os.path.join(self.work_dir, ".git")
        if not os.path.exists(git_dir):
            self._run_git(["init"])
            self._run_git(["config", "user.name", "AgentOps Nexus"])
            self._run_git(["config", "user.email", "bot@agentops.nexus"])
            self._run_git(["add", "."])
            self._run_git(["commit", "-m", "Initial snapshot"])

    def create_snapshot(self, iteration: int) -> Snapshot:
        """
        Create a snapshot of the current repository state before patching.
        Returns a Snapshot that can be used for rollback.
        """
        snapshot_id = f"{self.run_id}_iter_{iteration}"

        if self.git_available:
            self._ensure_git_repo()
            # Commit any uncommitted changes first
            self._run_git(["add", "."])
            self._run_git(["commit", "-m", f"Pre-patch snapshot iter {iteration}", "--allow-empty"])

            # Get current commit hash
            _, commit_hash, _ = self._run_git(["rev-parse", "HEAD"])

            # Create a snapshot branch
            branch_name = f"nexus/{self.run_id}/iter-{iteration}"
            self._run_git(["branch", branch_name])

            snapshot = Snapshot(
                snapshot_id=snapshot_id,
                iteration=iteration,
                commit_hash=commit_hash,
                branch_name=branch_name,
            )
        else:
            # Filesystem backup
            backup_dir = os.path.join(self._backup_base, f"iter_{iteration}")
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            shutil.copytree(
                self.work_dir, backup_dir,
                ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache')
            )

            snapshot = Snapshot(
                snapshot_id=snapshot_id,
                iteration=iteration,
                backup_dir=backup_dir,
            )

        self._snapshots.append(snapshot)
        return snapshot

    def rollback(self, snapshot: Snapshot) -> bool:
        """
        Rollback to a previous snapshot state.
        Returns True if rollback succeeded.
        """
        if self.git_available and snapshot.commit_hash:
            # Hard reset to the snapshot commit
            code, _, err = self._run_git(["reset", "--hard", snapshot.commit_hash])
            # Clean untracked files
            self._run_git(["clean", "-fdx", "--exclude=.git"])
            snapshot.status = "rolled_back" if code == 0 else "rollback_failed"
            return code == 0
        elif snapshot.backup_dir and os.path.exists(snapshot.backup_dir):
            # Filesystem restore
            try:
                # Remove current contents (except .git)
                for item in os.listdir(self.work_dir):
                    if item == ".git":
                        continue
                    item_path = os.path.join(self.work_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)

                # Copy backup contents back
                for item in os.listdir(snapshot.backup_dir):
                    src = os.path.join(snapshot.backup_dir, item)
                    dst = os.path.join(self.work_dir, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)

                snapshot.status = "rolled_back"
                return True
            except Exception:
                snapshot.status = "rollback_failed"
                return False
        else:
            snapshot.status = "rollback_failed"
            return False

    def commit_snapshot(self, snapshot: Snapshot, message: str) -> Optional[str]:
        """
        Commit the current state after a successful patch iteration.
        Returns the new commit hash if git is available.
        """
        if self.git_available:
            self._run_git(["add", "."])
            self._run_git(["commit", "-m", message, "--allow-empty"])
            _, commit_hash, _ = self._run_git(["rev-parse", "HEAD"])
            snapshot.commit_hash = commit_hash
            snapshot.status = "committed"
            return commit_hash
        else:
            snapshot.status = "committed"
            return None

    def cleanup(self) -> None:
        """Remove backup directories (snapshot branches are kept for audit)."""
        if os.path.exists(self._backup_base):
            try:
                shutil.rmtree(self._backup_base)
            except Exception:
                pass

    def get_history(self) -> List[Dict[str, Any]]:
        """Returns snapshot history for evidence/audit."""
        return [
            {
                "snapshot_id": s.snapshot_id,
                "iteration": s.iteration,
                "commit_hash": s.commit_hash,
                "branch_name": s.branch_name,
                "status": s.status,
            }
            for s in self._snapshots
        ]
