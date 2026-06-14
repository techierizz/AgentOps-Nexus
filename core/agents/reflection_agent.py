from core.agents.base import BaseAgent
from core.decision.agent_decision import AgentDecision

class ReflectionAgent(BaseAgent):
    def __init__(self):
        super().__init__("Reflection Agent")

    def execute(self, state: dict) -> dict:
        test_results = state.get("test_results", {})
        
        # This agent only operates on test failures
        if test_results.get("passed", True):
            self.log(state, "Tests passed. Skipping reflection feedback loop.")
            state["reflection"] = ""
            return state

        self.log(state, "Analyzing test failures to construct self-correction instructions...", "warning")
        
        failure_log = test_results.get("log", "")
        
        # Analyze failure trace
        reason = "Unknown crash"
        suggestion = "Double check method signatures and syntax."
        
        if "ZeroDivisionError" in failure_log:
            reason = "Division by zero still occurred during execution"
            suggestion = "Ensure division divisor (total_items) is explicitly checked for zero before doing standard float division."
        elif "ImportError" in failure_log:
            reason = "Import failed inside target script"
            suggestion = "Verify local files in repository. If Stripe mock module is named stripe_client, import stripe_client instead of stripe_gateway."
        elif "TypeError" in failure_log:
            reason = "TypeError during dictionary access"
            suggestion = "Check if returned coupon object is None. Wrap dict lookup in verification block or use coupon.get('value', 0) if coupon else 0"

        feedback = f"CRASH REASON: {reason}.\nREMEDIAL SUGGESTION: {suggestion}"
        
        self.log(state, f"Reflection Feedback Compiled:\n{feedback}", "info")
        state["reflection"] = feedback
        return state

    def execute_pure(self, ledger) -> AgentDecision:
        import time
        state_snapshot = getattr(ledger, "_state_snapshot")
        test_results = state_snapshot.get("test_results", {})
        
        if test_results.get("passed", True):
            feedback = ""
        else:
            failure_log = test_results.get("log", "")
            reason = "Unknown crash"
            suggestion = "Double check method signatures and syntax."
            
            if "ZeroDivisionError" in failure_log:
                reason = "Division by zero still occurred during execution"
                suggestion = "Ensure division divisor (total_items) is explicitly checked for zero before doing standard float division."
            elif "ImportError" in failure_log:
                reason = "Import failed inside target script"
                suggestion = "Verify local files in repository. If Stripe mock module is named stripe_client, import stripe_client instead of stripe_gateway."
            elif "TypeError" in failure_log:
                reason = "TypeError during dictionary access"
                suggestion = "Check if returned coupon object is None. Wrap dict lookup in verification block or use coupon.get('value', 0) if coupon else 0"

            feedback = f"CRASH REASON: {reason}.\nREMEDIAL SUGGESTION: {suggestion}"

        return AgentDecision(
            agent_id=self.name,
            decision_type="REFLECTION_GENERATED",
            payload={"reflection": feedback},
            dependency_event_hashes=[],
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
