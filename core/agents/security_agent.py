"""
AgentOps Nexus — Security Agent

Ownership: DETECTION only. Reports vulnerabilities.
Does NOT make deployment decisions (that is the Merge Governor's job).
Does NOT validate structural patch safety (that is the Patch Validation Agent's job).
"""
import re
from core.agents.base import BaseAgent
from core.decision.agent_decision import AgentDecision

class SecurityAgent(BaseAgent):
    def __init__(self):
        super().__init__("Security Agent")

    def execute(self, state: dict) -> dict:
        try:
            self.log(state, "Running static security scan on proposed patch...")
            
            patches = state.get("proposed_patch", [])
            
            if not patches:
                self.log(state, "No patch found to scan.", "warning")
                state["security_report"] = {
                    "vulnerabilities": [],
                    "status": "passed",
                    "message": "No patch to analyze."
                }
                return state

            vulnerabilities = []
            
            for patch in patches:
                diff_text = patch.get("diff", "")
                added_lines = [line[1:] for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++")]
                
                for line_no, line in enumerate(added_lines):
                    # Check 1: Hardcoded Secrets/API Keys
                    if re.search(r"(?:key|secret|password|token|auth)\s*=\s*['\"][a-zA-Z0-9_\-]{8,}['\"]", line, re.I):
                        vulnerabilities.append({
                            "file": patch["file"],
                            "issue": "Hardcoded Secret/API Key Detected",
                            "severity": "CRITICAL",
                            "line": line.strip()
                        })
                    
                    # Check 2: Unsafe Eval/Exec
                    if re.search(r"\b(eval|exec)\s*\(", line):
                        vulnerabilities.append({
                            "file": patch["file"],
                            "issue": "Use of unsafe eval() or exec() function",
                            "severity": "HIGH",
                            "line": line.strip()
                        })
                        
                    # Check 3: Shell command injection risk
                    if "shell=True" in line and "subprocess" in line:
                        vulnerabilities.append({
                            "file": patch["file"],
                            "issue": "Subprocess execution with shell=True represents command injection risk",
                            "severity": "HIGH",
                            "line": line.strip()
                        })

            if vulnerabilities:
                self.log(state, f"WARNING: Found {len(vulnerabilities)} potential security vulnerabilities!", "error")
                for vuln in vulnerabilities:
                    self.log(state, f"[{vuln['severity']}] {vuln['file']}: {vuln['issue']} (Line: '{vuln['line']}')", "warning")
                state["security_report"] = {
                    "vulnerabilities": vulnerabilities,
                    "status": "failed",
                    "message": f"Security scan failed with {len(vulnerabilities)} vulnerabilities."
                }
            else:
                self.log(state, "Static security scan completed. No vulnerabilities or secrets detected.", "success")
                state["security_report"] = {
                    "vulnerabilities": [],
                    "status": "passed",
                    "message": "All security tests passed."
                }
                
        except Exception as e:
            self.log(state, f"CRITICAL: Security scanner crashed or timed out: {e}", "error")
            state["security_report"] = {
                "vulnerabilities": [str(e)],
                "status": "UNKNOWN",
                "message": "Scanner crash detected"
            }
            
        return state


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
