from dataclasses import dataclass
from typing import Dict, Any, List
import hashlib, json

@dataclass(frozen=True)
class AgentDecision:
    agent_id: str
    decision_type: str
    payload: Dict[str, Any]
    dependency_event_hashes: List[str]
    timestamp: str

    @property
    def payload_hash(self) -> str:
        canonical = json.dumps(self.payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
