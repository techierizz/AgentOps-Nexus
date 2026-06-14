from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass
import threading
import time

# ── PHASE B.1: PURE EVENT-SOURCED ABSTRACTIONS ──────────────────────────

@dataclass(frozen=True)
class TypedLedgerMutationViolation(Exception):
    message: str

from core.decision.agent_decision import AgentDecision

class LedgerView:
    __slots__ = ("_artifacts", "_execution_id")

    def __init__(self, artifact_manager: Any, execution_id: str, state_snapshot: Optional[dict] = None):
        object.__setattr__(self, "_artifacts", artifact_manager)
        object.__setattr__(self, "_execution_id", execution_id)
        # _state_snapshot is explicitly ignored and eliminated to enforce pure event-sourcing

    def __setattr__(self, name: str, value: Any) -> None:
        raise TypedLedgerMutationViolation("LedgerView is strictly read-only. Mutation attempt blocked.")

    def read_event(self, event_type: str) -> Optional[dict]:
        return None

    def get_event_history(self, event_type: str = None) -> List[dict]:
        import os, json
        events = []
        if hasattr(self._artifacts, "_chain_file"):
            chain_file = self._artifacts._chain_file
            if os.path.exists(chain_file):
                with open(chain_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            env = json.loads(line)
                            ev_type = env.get("event_type")
                            payload_raw = env.get("payload", {})
                            
                            # Support both envelope event_type and nested DictEvent event_type
                            if ev_type == "DictEvent" and isinstance(payload_raw, dict):
                                ev_type = payload_raw.get("event_type", ev_type)
                            elif ev_type == "AgentDecision" and isinstance(payload_raw, dict):
                                ev_type = payload_raw.get("decision_type", ev_type)
                                
                            if event_type is None or ev_type == event_type:
                                events.append(env)
                        except Exception:
                            pass
        return events

    def get_projection(self, projection_type: str) -> dict:
        import os, json
        state = {}
        
        # Determine chain file path dynamically from the artifact manager
        if hasattr(self._artifacts, "_chain_file"):
            chain_file = self._artifacts._chain_file
            if os.path.exists(chain_file):
                with open(chain_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            env = json.loads(line)
                            
                            # Support both envelope event_type and nested DictEvent event_type
                            ev_type = env.get("event_type")
                            payload_raw = env.get("payload", {})
                            
                            if ev_type == "DictEvent" and isinstance(payload_raw, dict):
                                ev_type = payload_raw.get("event_type", ev_type)
                                
                            if ev_type == "INITIAL_CONTEXT":
                                state.update(payload_raw.get("payload", payload_raw))
                            elif ev_type == "AgentDecision":
                                if isinstance(payload_raw, str):
                                    payload_dict = json.loads(payload_raw)
                                else:
                                    payload_dict = payload_raw
                                    
                                if "payload" in payload_dict:
                                    state.update(payload_dict["payload"])
                                    
                        except Exception:
                            pass
                            
        if projection_type == "issue_context":
            return {
                "issue_description": state.get("issue_description", ""),
                "issue_title": state.get("issue_title", "")
            }
        elif projection_type == "full_state":
            return state
            
        return {}

class BaseAgent:
    """Base class for all pipeline agents."""
    def __init__(self, name: str):
        self.name = name

    def log(self, state: dict, message: str, log_type: str = "info"):
        """Append log message to the shared agent state logs."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        if "logs" not in state:
            state["logs"] = []
        state["logs"].append({
            "timestamp": timestamp,
            "agent": self.name,
            "message": message,
            "type": log_type
        })
        print(f"[{timestamp}] {self.name}: {message}")

    def execute_pure(self, ledger: LedgerView) -> AgentDecision:
        """
        Pure function: (LedgerView) -> AgentDecision
        Must be implemented by agents.
        """
        raise NotImplementedError("Agents must implement execute_pure")
