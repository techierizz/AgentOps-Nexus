from datetime import datetime, timezone
import json
from core.agents.base import BaseAgent
from core.decision.agent_decision import AgentDecision

class AIPatchValidationAgent(BaseAgent):
    def __init__(self):
        super().__init__("AIPatchValidationAgent")

    def execute_pure(self, ledger) -> AgentDecision:
        # 1. Fetch latest AI_PATCH_PROPOSED
        patch_events = ledger.get_event_history("AI_PATCH_PROPOSED")
        if not patch_events:
            return AgentDecision(
                agent_id=self.name,
                decision_type="AI_PATCH_VALIDATION_SKIPPED",
                payload={"reason": "No AI_PATCH_PROPOSED event found."},
                dependency_event_hashes=[],
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        
        latest_patch_event = patch_events[-1]
        patch_payload = latest_patch_event.get("payload", {})
        actual_patch_payload = patch_payload.get("payload", patch_payload)
        patch = actual_patch_payload.get("patch", {})
        
        # 2. Check Replay: If we already validated this exact patch event
        validated_events = ledger.get_event_history("AI_PATCH_VALIDATED")
        rejected_events = ledger.get_event_history("AI_PATCH_REJECTED")
        simulation_requests = ledger.get_event_history("PATCH_SIMULATION_REQUEST")
        
        patch_event_hash = latest_patch_event.get("current_hash", "")
        
        # Find if any existing validation or simulation request was derived from this patch event
        for ev in validated_events + rejected_events + simulation_requests:
            if ev.get("payload", {}).get("payload", {}).get("derived_from_hash") == patch_event_hash:
                # Return historical decision exactly
                return AgentDecision(
                    agent_id=self.name,
                    decision_type=ev.get("payload", {}).get("decision_type", ev.get("event_type")),
                    payload=ev.get("payload", {}).get("payload", ev.get("payload")),
                    dependency_event_hashes=[],
                    timestamp=ev.get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
                )

        # 3. Static Validation Rules
        failed_checks = []
        
        file_name = patch.get("file", "")
        diff = patch.get("diff", [])
        
        if not diff:
            failed_checks.append("empty_diff")
            
        if not file_name:
            failed_checks.append("missing_file")
            
        # Dangerous modifications check
        dangerous_patterns = ["os.system", "subprocess", "eval(", "exec(", "rm -rf"]
        for line in diff:
            if line.startswith("+"):
                for pattern in dangerous_patterns:
                    if pattern in line:
                        failed_checks.append("unsafe_operation")
                        break
                        
        # Core logic modification check
        if "core/orchestrator" in file_name or "core/ledger" in file_name or "core\\orchestrator" in file_name or "core\\ledger" in file_name:
            failed_checks.append("modifies_core_system")
            
        if failed_checks:
            return AgentDecision(
                agent_id=self.name,
                decision_type="AI_PATCH_REJECTED",
                payload={
                    "reason": "Failed static validation rules.",
                    "failed_checks": failed_checks,
                    "derived_from_hash": patch_event_hash
                },
                dependency_event_hashes=[patch_event_hash],
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
            
        # 4. If all static rules pass, request simulation!
        return AgentDecision(
            agent_id=self.name,
            decision_type="PATCH_SIMULATION_REQUEST",
            payload={
                "patch": patch,
                "derived_from_hash": patch_event_hash
            },
            dependency_event_hashes=[patch_event_hash],
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )
