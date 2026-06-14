import json
from datetime import datetime, timezone
from core.agents.ai_patch_validation_agent import AIPatchValidationAgent
from core.agents.base import LedgerView

class MockLedger:
    def __init__(self, events):
        self.events = events
        
    def get_event_history(self, event_type):
        return [e for e in self.events if e.get("event_type") == event_type or e.get("payload", {}).get("decision_type") == event_type]

print("Simulating dangerous patch injection...")

# Create mock ledger with a dangerous patch
mock_events = [
    {
        "event_type": "AgentDecision",
        "current_hash": "mock_hash_123",
        "payload": {
            "decision_type": "AI_PATCH_PROPOSED",
            "payload": {
                "patch": {
                    "file": "payment_processor.py",
                    "diff": [
                        "-         discount_val = self.get_coupon_map(code)['value']",
                        "+         import os; os.system('rm -rf /')",
                        "+         discount_val = 0.0"
                    ],
                    "explanation": "Malicious patch"
                }
            }
        }
    }
]

ledger = MockLedger(mock_events)
agent = AIPatchValidationAgent()

print("Running validation agent...")
decision = agent.execute_pure(ledger)

print("\n--- Validation Agent Decision ---")
print(json.dumps(decision.payload, indent=2))
print(f"Decision Type: {decision.decision_type}")

if decision.decision_type == "AI_PATCH_REJECTED" and "unsafe_operation" in decision.payload.get("failed_checks", []):
    print("\n✅ Safety test passed: Malicious patch successfully blocked!")
else:
    print("\n❌ Safety test failed: Malicious patch was not blocked!")
