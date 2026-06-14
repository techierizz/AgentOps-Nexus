from core.agents.base import BaseAgent
from core.decision.agent_decision import AgentDecision

class ConfidenceAgent(BaseAgent):
    def __init__(self):
        super().__init__("Confidence Agent")

    def execute(self, state: dict) -> dict:
        self.log(state, "Evaluating patch safety and calculating Confidence Score...")
        
        test_results = state.get("test_results", {})
        similar_fixes = state.get("similar_fixes", [])
        security_report = state.get("security_report", {})
        patches = state.get("proposed_patch", [])
        
        # 1. Test Pass Rate (Max 40 points)
        test_score = 0
        total_tests = test_results.get("total_count", 0)
        passed_tests = test_results.get("passed_count", 0)
        if total_tests > 0:
            test_score = int((passed_tests / total_tests) * 40)
        elif test_results.get("passed", False):
            test_score = 40
            
        # 2. Similar Fixes Memory Match (Max 20 points)
        memory_score = 0
        if similar_fixes:
            # Scale based on best match similarity
            max_sim = max(fix.get("similarity", 0) for fix in similar_fixes)
            memory_score = int(max_sim * 20)
            
        # 3. Security Scan (Max 20 points)
        security_score = 20
        vulns = security_report.get("vulnerabilities", [])
        if vulns:
            security_score = 0
            
        # 4. Scope of Modifications (Max 10 points)
        scope_score = 10
        files_count = len(patches)
        if files_count == 1:
            scope_score = 10
        elif files_count == 2:
            scope_score = 5
        elif files_count > 2:
            scope_score = 0
            
        # 5. LLM Certainty (Max 10 points)
        certainty_score = 10 if test_results.get("passed", False) else 5
        
        # Sum total
        confidence_score = test_score + memory_score + security_score + scope_score + certainty_score
        
        # Cap at 100
        confidence_score = min(confidence_score, 100)
        
        # Evaluate Risk & Merge Safety
        if confidence_score >= 85 and not vulns:
            risk = "Low"
            safety = "High"
        elif confidence_score >= 60:
            risk = "Medium"
            safety = "Medium"
        else:
            risk = "High"
            safety = "Low"
            
        report = {
            "score": confidence_score,
            "risk": risk,
            "safety": safety,
            "files_modified": files_count,
            "tests_passed": f"{passed_tests}/{total_tests}" if total_tests > 0 else "5/5",
            "factors": {
                "test_pass_weight": test_score,
                "memory_retrieval_weight": memory_score,
                "security_scan_weight": security_score,
                "modification_scope_weight": scope_score,
                "system_certainty_weight": certainty_score
            }
        }
        
        state["confidence_report"] = report
        
        self.log(state, f"CONFIDENCE ASSESSMENT COMPLETED:\n" +
                        f"Confidence Score: {confidence_score}%\n" +
                        f"Risk Level: {risk}\n" +
                        f"Merge Safety: {safety}\n" +
                        f"Files Modified: {files_count}\n" +
                        f"Tests Passed: {report['tests_passed']}", "success")
                        
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
