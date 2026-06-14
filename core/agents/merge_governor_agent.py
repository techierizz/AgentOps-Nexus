"""\nAgentOps Nexus — Merge Governor Agent\n\nOwnership: SOLE deployment decision authority.\nSecurity Agent → detects issues only\nPatch Validation Agent → structural safety only\nMerge Governor → final decision only\n"""
from core.agents.base import BaseAgent
from core.decision.agent_decision import AgentDecision

class MergeGovernorAgent(BaseAgent):
    def __init__(self):
        super().__init__("Merge Governor")

    def execute(self, state: dict) -> dict:
        self.log(state, "Evaluating deployment safety criteria and governance rules...")
        
        test_results = state.get("test_results", {})
        security_report = state.get("security_report", {})
        confidence_report = state.get("confidence_report", {})
        rca_score = state.get("rca_consistency_score", 100)
        status = state.get("status", "")
        patch_validation = state.get("patch_validation", {})
        patch_approval = patch_validation.get("approval", "SAFE_TO_TEST")
        patch_risk = patch_validation.get("risk_score", 0)
        
        # Extract variables
        tests_passed = test_results.get("passed", False)
        passed_count = test_results.get("passed_count", 0)
        total_count = test_results.get("total_count", 0)
        test_rate = (passed_count / total_count) if total_count > 0 else 0
        
        sec_passed = security_report.get("status", "passed") == "passed"
        conf_score = confidence_report.get("score", 0)
        rca_conflict = (status == "rca_conflict_detected") or (rca_score < 60)
        patch_unsafe = patch_approval == "UNSAFE_BLOCKED"

        # Decision Tree Logic
        decision = "BLOCKED"
        reason = ""
        failure_report = ""

        # Scenario A: Reject Deployment (BLOCKED)
        if not tests_passed or not sec_passed or conf_score < 60 or rca_conflict or patch_unsafe:
            decision = "BLOCKED"
            if patch_unsafe:
                reason = f"Patch validation BLOCKED: structural safety check failed (risk score: {patch_risk}/100)."
            elif not tests_passed:
                reason = "Critical unit test assertions failed."
            elif not sec_passed:
                reason = "Critical security vulnerability detected inside code patch."
            elif rca_conflict:
                reason = "Root cause analysis consistency validation conflict detected."
            else:
                reason = "Autonomous confidence safety score is below the 60% rejection threshold."
                
            # Compile structured Engineering Failure Report
            hyp_list = state.get("hypotheses", [])
            hyp_text = "\n".join([f"- {h['id']}: {h['description']}" for h in hyp_list])
            if not hyp_text:
                hyp_text = "- No hypotheses formulated successfully."
                
            failure_report = (
                "AGENTOPS NEXUS FAILURE REPORT\n\n"
                f"Issue:\n{state.get('issue_id', 'N/A')} - {state.get('issue_title', 'N/A')}\n\n"
                f"Attempted Hypotheses:\n{hyp_text}\n\n"
                f"Result:\nResolution unsuccessful.\n\n"
                f"Tests:\n{passed_count}/{total_count} Passed\n\n"
                f"Remaining Failure:\n{test_results.get('log', 'Unresolved static conflicts or compile errors.')}\n\n"
                f"Recommended Human Action:\n"
            )
            
            if not sec_passed:
                failure_report += "Review vulnerability warnings: remove credentials or refactor unsafe functions (eval/shell command execution)."
            elif rca_conflict:
                failure_report += "Examine repository paths and trace mismatch; check imports vs files on disk."
            else:
                failure_report += "Review payment logic, verify division guards, or modify discount mapping parameters."

            self.log(state, f"DECISION: PR BLOCKED!\nReason: {reason}", "error")
            
        # Scenario B: Auto Approve PR (APPROVED)
        elif test_rate == 1.0 and sec_passed and conf_score >= 85 and not rca_conflict and not patch_unsafe:
            decision = "APPROVED"
            reason = "100% tests passed, security check passed, and confidence score is >= 85%."
            self.log(state, f"DECISION: PR APPROVED!\nReason: {reason}", "success")
            
        # Scenario C: Human Review Required (DRAFT)
        else:
            decision = "DRAFT"
            reason = "Partial success or confidence score between 60-84%."
            self.log(state, f"DECISION: PR DRAFT!\nReason: {reason}", "warning")

        state["merge_decision"] = {
            "decision": decision,
            "reason": reason,
            "failure_report": failure_report
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
