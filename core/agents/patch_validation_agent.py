"""
AgentOps Nexus — Patch Validation Agent

Inserted between Patch Agent and Security Agent.
Validates that a generated patch is structurally safe before expensive testing.

Responsibilities:
  - Syntax validation (compile check)
  - Structural validation (AST diff)
  - Change scope analysis (files/lines/risk)
  - Patch Safety Score → SAFE_TO_TEST / REVIEW_RECOMMENDED / UNSAFE_BLOCKED

Ownership boundary:
  - Patch Validation Agent → structural safety ONLY
  - Security Agent → vulnerability detection ONLY
  - Merge Governor → final deployment decision ONLY
"""
import ast
import os
from core.agents.base import BaseAgent
from core.decision.agent_decision import AgentDecision


# High-risk filename patterns
HIGH_RISK_PATTERNS = [
    "auth", "login", "session", "token", "password", "credential",
    "payment", "billing", "charge", "invoice", "stripe",
    "security", "middleware", "csrf", "cors", "firewall",
    "config", "settings", "env", "secret",
    "migration", "schema", "deploy", "docker",
]

# Dangerous imports that increase risk score
DANGEROUS_IMPORTS = {"eval", "exec", "subprocess", "os.system", "pickle", "marshal"}


class PatchValidationAgent(BaseAgent):
    def __init__(self):
        super().__init__("Patch Validation Agent")

    def execute(self, state: dict) -> dict:
        self.log(state, "Starting patch structural validation...")

        patches = state.get("proposed_patch", [])

        if not patches:
            self.log(state, "No patches to validate.", "warning")
            state["patch_validation"] = {
                "syntax_valid": True,
                "structural_valid": True,
                "unexpected_changes": False,
                "files_changed": 0,
                "lines_added": 0,
                "lines_deleted": 0,
                "high_risk_files": [],
                "complexity_delta": 0,
                "risk_score": 0,
                "approval": "SAFE_TO_TEST",
                "details": "No patches to validate.",
            }
            return state

        total_risk = 0
        files_changed = 0
        total_lines_added = 0
        total_lines_deleted = 0
        high_risk_files = []
        syntax_valid = True
        structural_valid = True
        unexpected_changes = False
        complexity_delta = 0
        details = []

        for patch in patches:
            file_name = patch.get("file", "unknown")
            original = patch.get("original", "")
            modified = patch.get("modified", "")

            files_changed += 1

            # ── 1. Syntax Validation ──────────────────────────
            if file_name.endswith(".py"):
                try:
                    compile(modified, file_name, "exec")
                    self.log(state, f"Syntax check PASSED for {file_name}")
                except SyntaxError as e:
                    syntax_valid = False
                    total_risk += 40
                    details.append(f"Syntax error in {file_name}: {e}")
                    self.log(state, f"Syntax check FAILED for {file_name}: {e}", "error")

            # ── 2. Change Scope Analysis ──────────────────────
            orig_lines = original.splitlines()
            mod_lines = modified.splitlines()

            added = len(mod_lines) - len(orig_lines) if len(mod_lines) > len(orig_lines) else 0
            deleted = len(orig_lines) - len(mod_lines) if len(orig_lines) > len(mod_lines) else 0

            # Count actual changed lines
            lines_added = sum(1 for line in mod_lines if line not in orig_lines)
            lines_deleted = sum(1 for line in orig_lines if line not in mod_lines)
            total_lines_added += lines_added
            total_lines_deleted += lines_deleted

            # High-risk file detection
            basename_lower = os.path.basename(file_name).lower()
            for pattern in HIGH_RISK_PATTERNS:
                if pattern in basename_lower:
                    high_risk_files.append(file_name)
                    total_risk += 10
                    details.append(f"High-risk file modified: {file_name} (pattern: {pattern})")
                    break

            # ── 3. Structural Validation (AST diff) ──────────
            if file_name.endswith(".py") and syntax_valid:
                try:
                    orig_tree = ast.parse(original, filename=f"original/{file_name}")
                    mod_tree = ast.parse(modified, filename=f"modified/{file_name}")

                    # Check for deleted functions/classes
                    orig_defs = self._extract_definitions(orig_tree)
                    mod_defs = self._extract_definitions(mod_tree)

                    deleted_defs = orig_defs - mod_defs
                    if deleted_defs:
                        structural_valid = False
                        total_risk += 20
                        details.append(f"Deleted definitions in {file_name}: {deleted_defs}")
                        self.log(state, f"Structural warning: deleted definitions {deleted_defs}", "warning")

                    # Check for new dangerous imports
                    orig_imports = self._extract_imports(orig_tree)
                    mod_imports = self._extract_imports(mod_tree)
                    new_imports = mod_imports - orig_imports
                    dangerous_new = new_imports & DANGEROUS_IMPORTS
                    if dangerous_new:
                        total_risk += 15
                        details.append(f"New dangerous imports in {file_name}: {dangerous_new}")
                        self.log(state, f"Structural warning: dangerous imports {dangerous_new}", "warning")

                    # Complexity delta (function count as proxy)
                    orig_func_count = len([n for n in ast.walk(orig_tree) if isinstance(n, ast.FunctionDef)])
                    mod_func_count = len([n for n in ast.walk(mod_tree) if isinstance(n, ast.FunctionDef)])
                    complexity_delta += (mod_func_count - orig_func_count)

                except Exception as e:
                    details.append(f"AST analysis error for {file_name}: {e}")

            # ── 4. Scope-based risk ──────────────────────────
            if lines_added > 50:
                total_risk += 10
            if lines_deleted > 20:
                total_risk += 5
            if files_changed > 3:
                total_risk += 15

        # ── Final Risk Score & Decision ───────────────────────
        total_risk = min(total_risk, 100)  # Cap at 100

        if total_risk <= 30 and syntax_valid:
            approval = "SAFE_TO_TEST"
        elif total_risk <= 60 and syntax_valid:
            approval = "REVIEW_RECOMMENDED"
        else:
            approval = "UNSAFE_BLOCKED"

        validation_result = {
            "syntax_valid": syntax_valid,
            "structural_valid": structural_valid,
            "unexpected_changes": unexpected_changes,
            "files_changed": files_changed,
            "lines_added": total_lines_added,
            "lines_deleted": total_lines_deleted,
            "high_risk_files": high_risk_files,
            "complexity_delta": complexity_delta,
            "risk_score": total_risk,
            "approval": approval,
            "details": "; ".join(details) if details else "All checks passed.",
        }

        state["patch_validation"] = validation_result

        self.log(state, f"Patch Validation Result: {approval} (Risk Score: {total_risk}/100)", 
                 "success" if approval == "SAFE_TO_TEST" else "warning" if approval == "REVIEW_RECOMMENDED" else "error")

        return state

    @staticmethod
    def _extract_definitions(tree: ast.AST) -> set:
        """Extract all function and class names from an AST."""
        defs = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defs.add(node.name)
        return defs

    @staticmethod
    def _extract_imports(tree: ast.AST) -> set:
        """Extract all import names from an AST."""
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
        return imports


    def execute_pure(self, ledger) -> AgentDecision:
        import time
        import copy
        from core.agents.base import AgentDecision
        state_snapshot = ledger.get_projection("full_state")
        
        original_log = self.log
        self.log = lambda s, m, t="info": None
        try:
            new_state = self.execute(state_snapshot)
        finally:
            self.log = original_log
            
        payload = {}
        for k, v in new_state.items():
            if k not in ["logs", "current_state", "status", "issue_description", "issue_title", "repo_path"]:
                try:
                    import json
                    json.dumps(v)
                    payload[k] = v
                except:
                    pass
                    
        decision_type = self.name.upper().replace(" ", "_") + "_COMPLETED"
        return AgentDecision(
            agent_id=self.name,
            decision_type=decision_type,
            payload=payload,
            dependency_event_hashes=[],
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
