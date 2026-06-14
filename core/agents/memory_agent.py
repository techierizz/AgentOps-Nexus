import os
from core.agents.base import BaseAgent
from core.decision.agent_decision import AgentDecision
from core.utils.vector_store import LocalVectorStore

class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__("Memory Agent")

    def execute(self, state: dict) -> dict:
        title = state.get("issue_title", "")
        desc = state.get("issue_description", "")
        query = f"{title} {desc}"
        
        self.log(state, "Searching long-term bug memory database...")
        
        # Load local memory store
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory_store.json")
        store = LocalVectorStore(db_path)
        
        # In mock mode, if memory store is empty, we pre-seed it with some historical examples 
        # so the user can see beautiful matches and retrieval logic!
        if len(store.items) == 0:
            self.log(state, "Memory database is empty. Pre-seeding historical reference bug logs...")
            store.add_item(
                "HIST-101",
                "ZeroDivisionError in discount calculator: total items is zero, throws division by zero.",
                {
                    "issue_title": "ZeroDivisionError in discount calculator",
                    "root_cause": "Division by zero when item count is 0 in discount.py",
                    "patch_summary": "Add safe check if item_count == 0 return 0",
                    "files_changed": ["discount.py"],
                    "confidence_score": 95
                }
            )
            store.add_item(
                "HIST-102",
                "ImportError in dynamic stripe connector: Stripe module failed to load dynamically.",
                {
                    "issue_title": "ImportError in dynamic stripe connector",
                    "root_cause": "Stripe SDK name mismatch when importing dynamically in stripe_client.py",
                    "patch_summary": "Catch ImportError and fallback to stripe mock or correct string import name",
                    "files_changed": ["stripe_client.py"],
                    "confidence_score": 88
                }
            )
            store.add_item(
                "HIST-103",
                "TypeError in coupon handler: None value passed when loading discount dictionary.",
                {
                    "issue_title": "TypeError in coupon handler",
                    "root_cause": "Null value passed into dict lookup without default fallback in coupons.py",
                    "patch_summary": "Use .get() with default dictionary values",
                    "files_changed": ["coupons.py"],
                    "confidence_score": 92
                }
            )
        
        matches = store.search(query, top_k=2)
        
        similar_fixes = []
        for score, item in matches:
            if score > 0.15: # threshold
                self.log(state, f"Found similar historical bug {item['id']} (Similarity: {int(score*100)}%)")
                meta = item.get("metadata", {})
                similar_fixes.append({
                    "id": item["id"],
                    "similarity": int(score * 100),
                    "title": meta.get("issue_title", "Unresolved investigation"),
                    "root_cause": meta.get("root_cause", meta.get("reason_failed", "Failed resolution")),
                    "patch_summary": meta.get("patch_summary", "Unsuccessful attempt"),
                    "files_changed": meta.get("files_changed", ["payment_processor.py"]),
                    "status": meta.get("status", "VERIFIED")
                })
        
        if not similar_fixes:
            self.log(state, "No highly similar past bugs found in memory database. Proceeding with fresh analysis.")
        else:
            self.log(state, f"Retrieved {len(similar_fixes)} historical references to aid Root Cause Analysis.")
            
        state["similar_fixes"] = similar_fixes
        return state

    def record_event(self, state: dict):
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory_store.json")
        store = LocalVectorStore(db_path)
        
        tests_passed = state.get("test_results", {}).get("passed", False) is True
        security_passed = state.get("security_report", {}).get("status", "") == "passed"
        rca_valid = state.get("rca_report", {}).get("status", "") == "VALID"
        pr_approved = state.get("pr_details", {}).get("status", "") == "APPROVED"
        replay_consistent = state.get("replay_validation", "") == "CONSISTENT"

        if (tests_passed and security_passed and replay_consistent and rca_valid and pr_approved):
            classification = "RESOLVED_EXPERIENCE"
        else:
            classification = "FAILED_TRAJECTORY"
            
        state["memory_status"] = classification
            
        issue_id = state.get("issue_id", "UNKNOWN")
        issue_title = state.get("issue_title", "UNKNOWN")
        
        payload = {
            "event_type": "FINAL_OUTCOME",
            "classification": classification,
            "issue_id": issue_id,
            "issue_title": issue_title,
            "timestamp": "CURRENT_TIME",
            "hash": "DETERMINISTIC_HASH"
        }
        
        # Memory is purely a write-only event ledger at this stage
        store.add_item(
            f"MEM-{issue_id}-{classification}",
            f"{classification}: {issue_title}",
            payload
        )
        self.log(state, f"Memory Ledger Updated: Recorded as {classification}")


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
