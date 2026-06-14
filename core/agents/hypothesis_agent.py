from core.agents.base import BaseAgent
from core.decision.agent_decision import AgentDecision

class HypothesisAgent(BaseAgent):
    def __init__(self):
        super().__init__("Hypothesis Agent")

    def execute(self, state: dict) -> dict:
        title = state.get("issue_title", "")
        desc = state.get("issue_description", "")
        rca_report = state.get("rca_report", {})
        error_type = rca_report.get("error_type", "Generic")
        
        self.log(state, "Running Hypothesis Generator...")
        
        hypotheses = []
        
        # Scenario 1: ZeroDivisionError
        if "division" in (title + " " + desc).lower() or "zerodivisionerror" in (title + " " + desc).lower():
            hypotheses.append({
                "id": "H1",
                "description": "ZeroDivisionError in payment_processor.py during fee calculation due to empty cart (total_items = 0)",
                "confidence": 95,
                "reasoning": "The stack trace and issue describe a ZeroDivisionError. Analyzing payment_processor.py shows a line where total_amount is divided by total_items. An empty cart or free product order with items=0 triggers this division by zero.",
                "target_file": "payment_processor.py",
                "validation_status": "pending"
            })
            hypotheses.append({
                "id": "H2",
                "description": "ZeroDivisionError in test cases mock framework due to uninitialized order weights",
                "confidence": 40,
                "reasoning": "A test setup might be injecting a 0 value when building mock orders for testing, but payment_processor.py should still guard against it.",
                "target_file": "test_payment.py",
                "validation_status": "pending"
            })
            hypotheses.append({
                "id": "H3",
                "description": "Decimal round-off precision error causing total_items count to cast to 0",
                "confidence": 25,
                "reasoning": "If total_items is loaded as a float discount percentage instead of integer item count, casting might drop the value to 0.",
                "target_file": "payment_processor.py",
                "validation_status": "pending"
            })
            
        # Scenario 2: ImportError
        elif "import" in (title + " " + desc).lower() or "importerror" in (title + " " + desc).lower():
            hypotheses.append({
                "id": "H1",
                "description": "Stripe module failed to import in payment_processor.py because the library name is misspelled or loaded incorrectly",
                "confidence": 90,
                "reasoning": "The issue reports 'ImportError: No module named stripe_gateway'. In payment_processor.py, there is a dynamic import for stripe_gateway which fails if the library or helper filename does not match exactly.",
                "target_file": "payment_processor.py",
                "validation_status": "pending"
            })
            hypotheses.append({
                "id": "H2",
                "description": "Missing system-level python dependencies inside environment",
                "confidence": 50,
                "reasoning": "The Stripe dependency is not installed in the environment pip manifest, causing standard imports to fail.",
                "target_file": "requirements.txt",
                "validation_status": "pending"
            })
            
        # Scenario 3: TypeError
        elif "typeerror" in (title + " " + desc).lower() or "null" in (title + " " + desc).lower() or "none" in (title + " " + desc).lower():
            hypotheses.append({
                "id": "H1",
                "description": "TypeError due to dictionary access with None / missing key when loading discounts",
                "confidence": 88,
                "reasoning": "The issue indicates a TypeError when applying discount codes. If code is invalid or missing, the value is returned as None, and attempting dictionary index lookups on None causes a TypeError.",
                "target_file": "payment_processor.py",
                "validation_status": "pending"
            })
            hypotheses.append({
                "id": "H2",
                "description": "TypeError in discount rate parsing due to string input from config database",
                "confidence": 35,
                "reasoning": "The discount code value is retrieved as a string (e.g. '10%') instead of float, causing math operation failures.",
                "target_file": "payment_processor.py",
                "validation_status": "pending"
            })
            
        else:
            # Generic Bug Scenario
            hypotheses.append({
                "id": "H1",
                "description": "Generic logic fault in payment_processor.py logic blocks",
                "confidence": 70,
                "reasoning": "Based on general codebase layout, logic handlers in payment_processor contain the core calculation code.",
                "target_file": "payment_processor.py",
                "validation_status": "pending"
            })

        # Run Hypothesis Ranking
        self.log(state, f"Generated {len(hypotheses)} bug hypotheses. Running Hypothesis Ranking...")
        
        # Sort by confidence descending
        hypotheses.sort(key=lambda x: x["confidence"], reverse=True)
        
        for idx, hyp in enumerate(hypotheses):
            self.log(state, f"Rank {idx+1}: {hyp['id']} - {hyp['description']} (Confidence: {hyp['confidence']}%)")
            
        state["hypotheses"] = hypotheses
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
