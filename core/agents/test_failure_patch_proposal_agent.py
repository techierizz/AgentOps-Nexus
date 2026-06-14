import json
from datetime import datetime, timezone
from core.agents.base import BaseAgent
from core.decision.agent_decision import AgentDecision
from core.config import settings

PROMPT_VERSION = "patch_v1"

class TestFailurePatchProposalAgent(BaseAgent):
    def __init__(self):
        super().__init__("TestFailurePatchProposalAgent")

    def execute_pure(self, ledger) -> AgentDecision:
        # 1. Replay Determinism & Prompt Versioning Check
        patch_events = ledger.get_event_history("AI_PATCH_PROPOSED")
        fallback_events = ledger.get_event_history("AI_PATCH_PROPOSAL_UNAVAILABLE")
        
        all_patch_events = patch_events + fallback_events
        # Sort by timestamp to find the latest
        all_patch_events.sort(key=lambda x: x.get("timestamp", ""))
        
        if all_patch_events:
            latest_event = all_patch_events[-1]
            payload_envelope = latest_event.get("payload", {})
            actual_payload = payload_envelope.get("payload", payload_envelope)
            metadata = actual_payload.get("metadata", {})
            if metadata.get("prompt_version") == PROMPT_VERSION:
                # Return exact historical decision
                return AgentDecision(
                    agent_id=self.name,
                    decision_type=latest_event["event_type"] if "event_type" in latest_event else latest_event.get("decision_type", "AI_PATCH_PROPOSED"),
                    payload=actual_payload,
                    dependency_event_hashes=[],
                    timestamp=latest_event.get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
                )

        # 2. Context Retrieval
        testing_events = ledger.get_event_history("TESTING_AGENT_COMPLETED")
        analysis_events = ledger.get_event_history("AI_TEST_FAILURE_ANALYZED")
        file_events = ledger.get_event_history("FILE_READ")

        if not testing_events or not analysis_events:
            payload = {
                "reason": "Missing prerequisites (TESTING_AGENT_COMPLETED or AI_TEST_FAILURE_ANALYZED)",
                "fallback": "Cannot propose patch without analysis.",
                "metadata": {
                    "prompt_version": PROMPT_VERSION,
                    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            }
            return AgentDecision(
                agent_id=self.name,
                decision_type="AI_PATCH_PROPOSAL_UNAVAILABLE",
                payload=payload,
                dependency_event_hashes=[],
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )

        decision_envelope = testing_events[-1]["payload"]
        latest_test_payload = decision_envelope.get("payload", decision_envelope)
        test_log = latest_test_payload.get("test_results", {}).get("log", "")
        
        analysis_envelope = analysis_events[-1]["payload"]
        latest_analysis_payload = analysis_envelope.get("payload", analysis_envelope)
        ai_analysis = json.dumps(latest_analysis_payload.get("analysis", {}), indent=2)

        file_contents = ""
        for ev in file_events:
            f_payload = ev["payload"]
            path = f_payload.get("path", "")
            content = f_payload.get("content", "")
            file_contents += f"\n--- FILE: {path} ---\n{content}\n"

        model_name = getattr(settings, "LLM_PRIMARY_MODEL", "gemini-2.5-flash")
        model_version = model_name

        # 3. LLM Calling & Circuit Breaker
        prompt = f"""You are an expert AI software engineer.
A test has failed. You have the test failure log, the AI root cause analysis, and the codebase files.

Your task is to propose a code patch to fix the issue.
Respond ONLY with a strictly formatted JSON object. Do NOT use markdown formatting wrappers like ```json.
The JSON object MUST exactly match this schema:
{{
  "patch": {{
    "file": "<filename of the file to modify>",
    "diff": [
      "- <exact line to remove>",
      "+ <exact line to add>"
    ],
    "explanation": "<brief explanation of the patch>"
  }}
}}

--- TEST LOG ---
{test_log[:50000]}

--- AI ROOT CAUSE ANALYSIS ---
{ai_analysis}

--- CODEBASE ---
{file_contents[:50000]}
"""
        
        ai_patch = None
        error_reason = ""
        
        if settings.GEMINI_API_KEY and test_log:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                response_text = response.text
                
                print(f"[{self.name}] GEMINI RESPONSE:\n{response_text}")
                
                # Parse JSON safely
                text = response_text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                elif text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                    
                parsed = json.loads(text.strip())
                if isinstance(parsed, dict) and "patch" in parsed:
                    ai_patch = parsed["patch"]
            except Exception as e:
                error_reason = str(e)
                print(f"[{self.name}] Gemini API Patch Proposal failed: {error_reason}")
                
        if ai_patch:
            payload = {
                "patch": ai_patch,
                "metadata": {
                    "model": model_version,
                    "prompt_version": PROMPT_VERSION,
                    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            }
            return AgentDecision(
                agent_id=self.name,
                decision_type="AI_PATCH_PROPOSED",
                payload=payload,
                dependency_event_hashes=[],
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        else:
            payload = {
                "reason": error_reason if error_reason else "AI did not return valid JSON patch findings",
                "fallback": "Human review required",
                "metadata": {
                    "model": model_version,
                    "prompt_version": PROMPT_VERSION,
                    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            }
            return AgentDecision(
                agent_id=self.name,
                decision_type="AI_PATCH_PROPOSAL_UNAVAILABLE",
                payload=payload,
                dependency_event_hashes=[],
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
