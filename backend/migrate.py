import os

AGENTS_DIR = r"d:\Japan\backend\agents"
SKIP_FILES = {"__init__.py", "base.py", "issue_agent.py", "reflection_agent.py"}

PURE_TEMPLATE = """
    def execute_pure(self, ledger) -> AgentDecision:
        import time
        import copy
        from core.agents.base import AgentDecision
        state_snapshot = copy.deepcopy(getattr(ledger, "_state_snapshot", {}))
        
        original_log = self.log
        self.log = lambda s, m, t="info": None
        try:
            new_state = self.execute(state_snapshot)
        finally:
            self.log = original_log
            
        payload = {}
        for k, v in new_state.items():
            if k not in ["logs", "current_state", "status", "issue_description", "issue_title", "repo_path"]:
                try:
                    import json
                    json.dumps(v)
                    payload[k] = v
                except:
                    pass
                    
        decision_type = self.name.upper().replace(" ", "_") + "_COMPLETED"
        return AgentDecision(
            agent_id=self.name,
            decision_type=decision_type,
            payload=payload,
            dependency_event_hashes=[],
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
"""

def migrate():
    for fname in os.listdir(AGENTS_DIR):
        if not fname.endswith(".py") or fname in SKIP_FILES:
            continue
            
        path = os.path.join(AGENTS_DIR, fname)
        with open(path, "r") as f:
            content = f.read()
            
        if "execute_pure" in content:
            continue
            
        # Replace imports
        content = content.replace("from core.agents.base import BaseAgent, AgentState", 
                                "from core.agents.base import TransitionalAgent, AgentState, AgentDecision")
        content = content.replace("(BaseAgent):", "(TransitionalAgent):")
        
        # Append execute_pure
        content += "\n" + PURE_TEMPLATE
        
        with open(path, "w") as f:
            f.write(content)
        print(f"Migrated {fname}")

if __name__ == "__main__":
    migrate()
