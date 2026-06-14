import json
import time
from datetime import datetime, timezone
from core.agents.base import BaseAgent, LedgerView, AgentDecision
from core.config import settings

PROMPT_VERSION = "test_failure_v1"

class TestFailureAnalysisAgent(BaseAgent):
    """
    Phase D.2: AI Test Failure Root Cause Advisor.
    Acts strictly as a Semantic Advisor for failing tests. Reads the ledger, queries Gemini once,
    and stores the structured advice as an AI_TEST_FAILURE_ANALYZED event.
    Replays strictly from the ledger to preserve determinism.
    """
    
    def __init__(self):
        super().__init__("TestFailureAnalysisAgent")

    def execute_pure(self, ledger: LedgerView) -> AgentDecision:
        # 1. Deterministic Replay Check
        # Check for successful analysis or fallback
        historical_success = ledger.get_event_history("AI_TEST_FAILURE_ANALYZED")
        if historical_success:
            return AgentDecision(
                agent_id=self.name,
                decision_type="AI_TEST_FAILURE_ANALYZED",
                payload=historical_success[0]["payload"],
                dependency_event_hashes=[],
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
            
        historical_failure = ledger.get_event_history("AI_TEST_FAILURE_UNAVAILABLE")
        if historical_failure:
            return AgentDecision(
                agent_id=self.name,
                decision_type="AI_TEST_FAILURE_UNAVAILABLE",
                payload=historical_failure[0]["payload"],
                dependency_event_hashes=[],
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )

        # 2. Gather Context from Ledger
        testing_events = ledger.get_event_history("TESTING_AGENT_COMPLETED")
        if not testing_events:
            return AgentDecision(
                agent_id=self.name,
                decision_type="AI_TEST_FAILURE_UNAVAILABLE",
                payload={"reason": "No test execution found", "fallback": "Raw pytest output not available"},
                dependency_event_hashes=[],
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
            
        decision_envelope = testing_events[-1]["payload"]
        latest_test_payload = decision_envelope.get("payload", decision_envelope)
        test_log = latest_test_payload.get("test_results", {}).get("log", "")
        
        file_events = ledger.get_event_history("FILE_READ")
        code_contents = []
        for evt in file_events:
            path = evt["payload"].get("path", "unknown")
            content = evt["payload"].get("content", "")
            if path.endswith(('.py', '.js', '.ts', '.tsx', '.jsx')):
                code_contents.append(f"--- FILE: {path} ---\n{content}\n")

        # 3. Request AI Advisory (if API key available)
        ai_findings = None
        model_version = "gemini-1.5-flash"
        
        if settings.GEMINI_API_KEY and test_log:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                
                model_name = getattr(settings, "LLM_PRIMARY_MODEL", "gemini-2.5-flash")
                model_version = model_name
                
                model = genai.GenerativeModel(model_name)
                
                prompt = "You are an expert AI software engineer. Analyze the following pytest failure log and the provided codebase to identify the root cause of the test failure.\n"
                prompt += "Respond ONLY with a valid JSON object. Do not use markdown formatting.\n"
                prompt += 'The JSON object must exactly have these string fields: "identified_error" (concise human-readable explanation), "root_cause" (logical error pinpointing), "severity" ("HIGH", "MEDIUM", "LOW"), and "recommended_fix" (how to fix it).\n\n'
                prompt += "--- PYTEST LOG ---\n" + test_log[:50000] + "\n\n"
                prompt += "--- CODEBASE ---\n" + "\n".join(code_contents)[:1000000]
                
                response = model.generate_content(prompt)
                response_text = response.text
                
                print(f"[DEBUG GEMINI RESPONSE]\n{response_text}\n[END DEBUG]")
                
                # Parse JSON safely
                text = response_text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                elif text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                    
                parsed = json.loads(text.strip())
                if isinstance(parsed, dict) and "identified_error" in parsed:
                    # Sanitize any floats
                    def clean_floats(obj):
                        if isinstance(obj, float):
                            return str(obj)
                        elif isinstance(obj, dict):
                            return {k: clean_floats(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [clean_floats(item) for item in obj]
                        return obj
                        
                    ai_findings = clean_floats(parsed)
            except Exception as e:
                print(f"[{self.name}] Gemini API Test Advisory failed: {e}")
                with open("debug_gemini.txt", "w") as f:
                    f.write(str(e))
                return AgentDecision(
                    agent_id=self.name,
                    decision_type="AI_TEST_FAILURE_UNAVAILABLE",
                    payload={"reason": str(e), "fallback": "Raw pytest output available"},
                    dependency_event_hashes=[],
                    timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                )

        if ai_findings:
            # 4. Construct Deterministic Output Envelope
            payload = {
                "analysis": ai_findings,
                "metadata": {
                    "model": model_version,
                    "prompt_version": PROMPT_VERSION,
                    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            }

            return AgentDecision(
                agent_id=self.name,
                decision_type="AI_TEST_FAILURE_ANALYZED",
                payload=payload,
                dependency_event_hashes=[],
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        else:
            with open("debug_gemini.txt", "w") as f:
                f.write(f"No AI Findings. Original Text:\n{response_text if 'response_text' in locals() else 'None'}")
            return AgentDecision(
                agent_id=self.name,
                decision_type="AI_TEST_FAILURE_UNAVAILABLE",
                payload={"reason": "AI did not return valid JSON findings", "fallback": "Raw pytest output available"},
                dependency_event_hashes=[],
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
