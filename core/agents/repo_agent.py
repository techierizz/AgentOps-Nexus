import os
import networkx as nx
from core.agents.base import BaseAgent
from core.decision.agent_decision import AgentDecision
from core.utils.ast_parser import CodeASTParser

class RepositoryIntelligenceAgent(BaseAgent):
    def __init__(self):
        super().__init__("Repository Intel Agent")

    def execute(self, state: dict) -> dict:
        repo_path = state.get("repo_path", "")
        self.log(state, f"Scanning codebase and generating knowledge graph in: {repo_path}")
        
        if not os.path.exists(repo_path):
            self.log(state, f"Repository path {repo_path} does not exist. Initializing temporary mock repository.", "warning")
            os.makedirs(repo_path, exist_ok=True)
            
        parser = CodeASTParser(repo_path)
        ast_data = parser.parse_repo()
        
        # Build NetworkX Graph representation for graph calculations
        G = nx.DiGraph()
        
        for node in ast_data["nodes"]:
            G.add_node(node["id"], type=node["type"], label=node["label"], **node.get("properties", {}))
            
        for edge in ast_data["edges"]:
            G.add_edge(edge["source"], edge["target"], type=edge["type"])
            
        self.log(state, f"Discovered {G.number_of_nodes()} code entities and {G.number_of_edges()} relationships.")
        
        # Capture critical entrypoints (files and core modules)
        files = [n for n, d in G.nodes(data=True) if d.get("type") == "file"]
        state["files"] = list(set(state.get("files", []) + files))
        
        # Save graph in serialized format for frontend
        state["knowledge_graph"] = {
            "nodes": [{"id": n, "label": d.get("label", n), "type": d.get("type", "unknown"), "properties": {k: v for k, v in d.items() if k not in ["label", "type"]}} for n, d in G.nodes(data=True)],
            "edges": [{"source": u, "target": v, "type": d.get("type", "unknown")} for u, v, d in G.edges(data=True)]
        }
        
        self.log(state, "Codebase indexing and knowledge graph creation completed.", "success")
        return state


    def execute_pure(self, ledger) -> AgentDecision:
        import time
        import copy
        from core.agents.base import AgentDecision
        state_snapshot = ledger.get_projection("full_state")
        
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
