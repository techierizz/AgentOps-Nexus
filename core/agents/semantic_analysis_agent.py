import json
import time
from core.agents.base import BaseAgent, LedgerView, AgentDecision
from core.config import settings

class SemanticAnalysisAgent(BaseAgent):
    """
    Phase D.1: AI Semantic Analysis Engine.
    Acts strictly as a Semantic Advisor. Reads the ledger, queries Gemini once,
    and stores the structured advice as an AI_ANALYSIS_COMPLETED event.
    Replays strictly from the ledger to preserve determinism.
    """
    
    def __init__(self):
        super().__init__("SemanticAnalysisAgent")

    def execute_pure(self, ledger: LedgerView) -> AgentDecision:
        # 1. Deterministic Replay Check
        historical_decisions = ledger.get_event_history("AI_ANALYSIS_COMPLETED")
        if historical_decisions:
            # We are replaying. Return the historically recorded decision exactly as is.
            payload = historical_decisions[0]["payload"]
            return AgentDecision(
                agent_id=self.name,
                decision_type="AI_ANALYSIS_COMPLETED",
                payload=payload,
                dependency_event_hashes=[],
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            )

        # 2. Gather Context from Ledger
        file_events = ledger.get_event_history("FILE_READ")
        code_contents = []
        for evt in file_events:
            path = evt["payload"].get("path", "unknown")
            content = evt["payload"].get("content", "")
            if path.endswith(('.py', '.js', '.ts', '.tsx', '.jsx')):
                code_contents.append(f"--- FILE: {path} ---\n{content}\n")

        # 3. Request AI Advisory (if API key available)
        ai_findings = []
        model_version = "None"
        
        if settings.GEMINI_API_KEY and code_contents:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                
                model_name = getattr(settings, "LLM_PRIMARY_MODEL", "gemini-1.5-flash")
                if "2.5" in model_name:
                    model_name = "gemini-1.5-flash"
                model_version = model_name
                
                model = genai.GenerativeModel(model_name)
                
                prompt = "You are an expert AI code reviewer. Review the following codebase and identify bugs, vulnerabilities, logic errors, or bad practices.\n"
                prompt += "Respond ONLY with a valid JSON array of objects. Do not use markdown formatting.\n"
                prompt += 'Each object must exactly have these string fields: "severity" ("HIGH", "MEDIUM", "LOW"), "path" (the file path), "explanation" (what is wrong), and "suggested_fix" (how to fix it).\n\n'
                
                # Truncate context to stay within reasonable limits
                context_str = "\n".join(code_contents)[:1000000]
                prompt += context_str
                
                response = model.generate_content(prompt)
                response_text = response.text
                
                # Parse JSON
                if response_text.startswith("```json"):
                    response_text = response_text[7:-3]
                elif response_text.startswith("```"):
                    response_text = response_text[3:-3]
                    
                parsed = json.loads(response_text.strip())
                if isinstance(parsed, list):
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
                print(f"[{self.name}] Gemini API Advisory failed: {e}")

        # 4. Construct Deterministic Output Envelope
        payload = {
            "ai_findings": ai_findings,
            "model": model_version,
            "prompt_version": "v1",
            "generated_at": int(time.time())
        }

        return AgentDecision(
            agent_id=self.name,
            decision_type="AI_ANALYSIS_COMPLETED",
            payload=payload,
            dependency_event_hashes=[],
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
