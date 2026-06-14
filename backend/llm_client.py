import hashlib
import json
import datetime
from typing import Dict, Any

class LlmEvidenceMissingError(Exception):
    pass

class LlmClient:
    """
    Cryptographic wrapper for LLM invocations.
    Ensures that every LLM call generates immutable input/output evidence.
    """
    
    @staticmethod
    def execute(artifacts, execution_id: str, provider: str, model: str, config: Dict[str, Any], system_prompt: str, user_prompt: str, retrieved_context: str, repo_commit: str, mock_response: str) -> str:
        if not all([execution_id, provider, model, config is not None, system_prompt, user_prompt, retrieved_context is not None, repo_commit]):
            raise LlmEvidenceMissingError("LLM_EVIDENCE_INCOMPLETE")

        # Canonical hashing of inputs
        config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode("utf-8")).hexdigest()
        system_hash = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()
        user_hash = hashlib.sha256(user_prompt.encode("utf-8")).hexdigest()
        context_hash = hashlib.sha256(retrieved_context.encode("utf-8")).hexdigest()
        
        request_payload = {
            "system": system_prompt,
            "user": user_prompt,
            "context": retrieved_context
        }
        request_hash = hashlib.sha256(json.dumps(request_payload, sort_keys=True).encode("utf-8")).hexdigest()
        
        # Simulated LLM invocation (mock_response is passed in for now)
        response_text = mock_response
        response_hash = hashlib.sha256(response_text.encode("utf-8")).hexdigest()
        
        event = {
            "event_type": "LLM_EXECUTION",
            "execution_id": execution_id,
            "provider": provider,
            "model": model,
            "config_hash": config_hash,
            "system_prompt_hash": system_hash,
            "user_prompt_hash": user_hash,
            "retrieved_context_hash": context_hash,
            "repository_commit_hash": repo_commit,
            "request_hash": request_hash,
            "response_hash": response_hash,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        try:
            artifacts.record("llm_execution", event)
        except Exception as e:
            raise LlmEvidenceMissingError(f"LLM_EVIDENCE_INCOMPLETE: {e}")
            
        return response_text
