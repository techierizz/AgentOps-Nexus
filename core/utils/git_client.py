import os
import subprocess
import shutil
from typing import Dict, Any, Optional

class LocalGitClient:
    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        self.git_available = self._check_git()

    def _check_git(self) -> bool:
        try:
            # Check if git is installed
            res = subprocess.run(["git", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return res.returncode == 0
        except Exception:
            return False

    def run_cmd(self, args: list[str]) -> tuple[int, str, str]:
        """Runs a git command inside the repository path."""
        if not self.git_available:
            return 1, "", "Git is not installed"
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except Exception as e:
            return -1, "", str(e)

    def init_repo_if_needed(self):
        """Initializes a local git repository if one doesn't exist."""
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)
            
        git_dir = os.path.join(self.repo_path, ".git")
        if not os.path.exists(git_dir):
            if self.git_available:
                self.run_cmd(["init"])
                # Configure dummy local user for commit safety
                self.run_cmd(["config", "user.name", "AgentOps Nexus Bot"])
                self.run_cmd(["config", "user.email", "bot@agentops.nexus"])
                
                # Create a dummy initial file to commit
                readme_path = os.path.join(self.repo_path, "README.md")
                if not os.path.exists(readme_path):
                    with open(readme_path, "w") as f:
                        f.write("# Target Demo Repository\n")
                self.run_cmd(["add", "."])
                self.run_cmd(["commit", "-m", "Initial commit"])
            else:
                print("Git not available, proceeding in filesystem-only mode")

    def create_branch(self, branch_name: str) -> bool:
        """Creates and checks out a new branch."""
        if self.git_available:
            code, _, _ = self.run_cmd(["checkout", "-b", branch_name])
            if code != 0:
                # If branch already exists, checkout
                code, _, _ = self.run_cmd(["checkout", branch_name])
            return code == 0
        return True

    def commit_changes(self, message: str) -> bool:
        """Adds all changes and commits them."""
        if self.git_available:
            self.run_cmd(["add", "."])
            code, _, _ = self.run_cmd(["commit", "-m", message])
            return code == 0
        return True

    def get_diff(self, base: str = "main") -> str:
        """Returns the diff of current branch against main."""
        if self.git_available:
            code, out, _ = self.run_cmd(["diff", base])
            if code == 0:
                return out
        return ""

    def get_file_content(self, relative_path: str) -> Optional[str]:
        """Helper to get file content safely."""
        full_path = os.path.join(self.repo_path, relative_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                return None
        return None

    def write_file_content(self, relative_path: str, content: str) -> bool:
        """Helper to write file content safely."""
        full_path = os.path.join(self.repo_path, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

if __name__ == "__main__":
    # Test script
    client = LocalGitClient("./test_git_repo")
    client.init_repo_if_needed()
    client.create_branch("fix-bug-123")
    client.write_file_content("hello.py", "print('hello world')")
    client.commit_changes("added hello.py")
    print("Diff:")
    print(client.get_diff("master" if client.run_cmd(["show-ref", "--verify", "refs/heads/master"])[0] == 0 else "main"))
    
    # clean up test dir
    if os.path.exists("./test_git_repo"):
        shutil.rmtree("./test_git_repo")
