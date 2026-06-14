import re
from core.agents.base import BaseAgent
from core.decision.agent_decision import AgentDecision

class IssueAgent(BaseAgent):
    def __init__(self):
        super().__init__("Issue Agent")

    def execute(self, state: dict) -> dict:
        self.log(state, "Starting issue parsing and context extraction...")
        
        desc = state.get("issue_description", "")
        title = state.get("issue_title", "")
        
        # Look for stack traces
        stack_trace_match = re.search(r"```(?:python|tb|text)?\n(Traceback.*?\n\w+Error:.*?)\n```", desc, re.DOTALL | re.IGNORECASE)
        stack_trace = stack_trace_match.group(1) if stack_trace_match else ""
        
        # Look for file paths mentioned in stack trace or issue
        suspected_files = []
        for word in re.findall(r"[\w\./\-]+\.py", desc + " " + title):
            if word not in suspected_files and not word.startswith("test_"):
                suspected_files.append(word)

        # Detect error types (e.g. ZeroDivisionError, ImportError, TypeError)
        error_type = "Generic Bug"
        for err in ["ZeroDivisionError", "ImportError", "TypeError", "NullPointerException", "KeyError"]:
            if err.lower() in (desc + " " + title).lower():
                error_type = err
                break

        self.log(state, f"Parsed issue title: '{title}'")
        self.log(state, f"Identified error type: {error_type}")
        if suspected_files:
            self.log(state, f"Suspected files mentioned: {', '.join(suspected_files)}")
            state["files"] = suspected_files
        else:
            self.log(state, "No files explicitly mentioned. Repository Intel Agent will do a complete scan.")

        # Save structured issue metadata
        state["rca_report"] = {
            "error_type": error_type,
            "stack_trace": stack_trace,
            "suspected_files": suspected_files
        }
        
        self.log(state, "Issue parsing complete.", "success")
        return state

    def execute_pure(self, ledger) -> AgentDecision:
        import time
        issue_context = ledger.get_projection("issue_context")
        desc = issue_context.get("issue_description", "")
        title = issue_context.get("issue_title", "")
        
        stack_trace_match = re.search(r"```(?:python|tb|text)?\n(Traceback.*?\n\w+Error:.*?)\n```", desc, re.DOTALL | re.IGNORECASE)
        stack_trace = stack_trace_match.group(1) if stack_trace_match else ""
        
        suspected_files = []
        for word in re.findall(r"[\w\./\-]+\.py", desc + " " + title):
            if word not in suspected_files and not word.startswith("test_"):
                suspected_files.append(word)

        error_type = "Generic Bug"
        for err in ["ZeroDivisionError", "ImportError", "TypeError", "NullPointerException", "KeyError"]:
            if err.lower() in (desc + " " + title).lower():
                error_type = err
                break

        payload = {
            "files": suspected_files,
            "rca_report": {
                "error_type": error_type,
                "stack_trace": stack_trace,
                "suspected_files": suspected_files
            }
        }
        
        return AgentDecision(
            agent_id=self.name,
            decision_type="ISSUE_ANALYSIS_COMPLETED",
            payload=payload,
            dependency_event_hashes=[],
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
