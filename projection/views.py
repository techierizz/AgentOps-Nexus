import os
import json
from typing import Dict, Any, List
from core.config import settings

def get_evidence_chain_path(run_id: str) -> str:
    """Resolve the path to the evidence_chain.jsonl for a given run."""
    # 1. Direct match check
    direct_path = os.path.join(settings.evidence_dir, run_id, "evidence_chain.jsonl")
    if os.path.exists(direct_path):
        return direct_path
        
    # 2. Dynamic timestamped run folder pattern search (e.g. run_*_{run_id}_*)
    if os.path.exists(settings.evidence_dir):
        matches = []
        for name in os.listdir(settings.evidence_dir):
            if os.path.isdir(os.path.join(settings.evidence_dir, name)):
                if f"_{run_id}_" in name or name.endswith(f"_{run_id}"):
                    matches.append(name)
        if matches:
            # Sort alphabetically to find the latest run timestamp
            matches.sort()
            latest_run = matches[-1]
            return os.path.join(settings.evidence_dir, latest_run, "evidence_chain.jsonl")
            
    return direct_path

def get_ledger_projection_view(run_id: str) -> Dict[str, Any]:
    """
    Reads evidence_chain.jsonl and projects it into a UI-ready state dict.
    Strictly read-only, NO mutation allowed.
    """
    chain_file = get_evidence_chain_path(run_id)
    state: Dict[str, Any] = {}
    
    if not os.path.exists(chain_file):
        return state
        
    with open(chain_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                env = json.loads(line)
                
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
                        
                    decision_type = payload_dict.get("decision_type", "COMPLETED")
                    
                    if decision_type == "AI_TEST_FAILURE_ANALYZED":
                        ai_payload = payload_dict.get("payload", {})
                        if "test_results" not in state:
                            state["test_results"] = {}
                        state["test_results"]["ai_analysis"] = ai_payload.get("analysis", {})
                    elif decision_type == "AI_PATCH_PROPOSED":
                        ai_payload = payload_dict.get("payload", {})
                        if "test_results" not in state:
                            state["test_results"] = {}
                        state["test_results"]["ai_patch_proposal"] = ai_payload.get("patch", {})
                    elif decision_type in ("AI_PATCH_VALIDATED", "AI_PATCH_REJECTED"):
                        ai_payload = payload_dict.get("payload", {})
                        if "test_results" not in state:
                            state["test_results"] = {}
                        state["test_results"]["ai_patch_validation"] = ai_payload
                    elif "payload" in payload_dict:
                        state.update(payload_dict["payload"])
                        
                    # Synthesize log
                    agent_id = payload_dict.get("agent_id", "Unknown Agent")
                    decision_type = payload_dict.get("decision_type", "COMPLETED")
                    state.setdefault("logs", [])
                    
                    evt_time = env.get("timestamp", "")
                    if "T" in evt_time:
                        time_str = evt_time.split("T")[1][:8]
                    else:
                        import datetime
                        time_str = datetime.datetime.now().strftime("%H:%M:%S")

                    state["logs"].append({
                        "timestamp": time_str,
                        "agent": agent_id,
                        "message": f"Concluded with decision: {decision_type}",
                        "type": "info"
                    })
            except Exception:
                pass
                
    # Default properties for UI rendering
    state.setdefault("logs", [])
    if "status" not in state:
        if any(k in state for k in ["pr_details", "merge_decision", "memory_status"]):
            state["status"] = "completed"
        else:
            state["status"] = "running"
            
    return state

def get_execution_trace(run_id: str) -> Dict[str, Any]:
    """
    Returns execution trace, agent order, and payload_hash chain.
    """
    chain_file = get_evidence_chain_path(run_id)
    trace = {
        "run_id": run_id,
        "agents": [],
        "hash_chain": []
    }
    
    if not os.path.exists(chain_file):
        return trace
        
    with open(chain_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                env = json.loads(line)
                ev_type = env.get("event_type")
                if ev_type == "AgentDecision":
                    payload_raw = env.get("payload", {})
                    if isinstance(payload_raw, str):
                        payload_dict = json.loads(payload_raw)
                    else:
                        payload_dict = payload_raw
                    
                    agent_id = payload_dict.get("agent_id", "UnknownAgent")
                    payload_hash = env.get("payload_hash", "")
                    
                    trace["agents"].append(agent_id)
                    trace["hash_chain"].append({
                        "agent": agent_id,
                        "hash": payload_hash
                    })
            except Exception:
                pass
                
    return trace

def get_replay_view(run_id: str) -> Dict[str, Any]:
    """
    Returns full ledger snapshot for deterministic replay.
    """
    chain_file = get_evidence_chain_path(run_id)
    events = []
    
    if not os.path.exists(chain_file):
        return {"events": []}
        
    with open(chain_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except Exception:
                pass
                
    return {
        "run_id": run_id,
        "events": events
    }
