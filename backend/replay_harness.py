import os
import json
import time
from dataclasses import dataclass

from core.orchestrator.orchestrator import AgentOrchestrator
from core.config import settings

@dataclass
class ReplayDeterminismReport:
    total_runs: int
    full_pipeline_stability_passed: bool
    orchestration_order_passed: bool
    ledger_growth_consistency_passed: bool
    shadow_consistency_passed: bool
    execution_timestamp: str

def run_harness():
    print("Starting Phase B.2.3 Replay Determinism Validation Harness...\n")
    
    N_RUNS = 50
    
    repo_path = os.path.join(settings.evidence_dir, "dummy_repo")
    os.makedirs(repo_path, exist_ok=True)
    with open(os.path.join(repo_path, "math.py"), "w") as f:
        f.write("def calc(): return 1 / total_items\n")
        
    issue_id = "ISSUE-123"
    issue_title = "Fix division by zero"
    issue_desc = "The math.py file crashes with a ```ZeroDivisionError: division by zero``` traceback."
    
    run_histories = []
    
    print(f"Executing {N_RUNS} full pipeline replays...")
    for i in range(N_RUNS):
        orchestrator = AgentOrchestrator()
        
        # Monkey patch RunContext.create locally to return a predictable run_id if needed,
        # but to test actual determinism, we let it generate organic UUIDs and check semantic equivalence
        
        final_state = orchestrator.run(issue_id, issue_title, issue_desc, repo_path)
        
        # Grab the latest run_id dynamically
        dirs = [d for d in os.listdir(settings.evidence_dir) if "run_" in d]
        # Sort by creation time to get the absolute latest directory created by the orchestrator run
        latest_dir = sorted(dirs, key=lambda d: os.path.getctime(os.path.join(settings.evidence_dir, d)))[-1]
            
        run_histories.append(latest_dir)
        if (i+1) % 10 == 0:
            print(f"Completed {i+1}/{N_RUNS} replays")

    print("\nValidating determinism across all runs...")
    
    reference_chain_types = None
    reference_shadow_hashes = None
    reference_event_count = None
    
    full_pipeline_stability_passed = True
    orchestration_order_passed = True
    ledger_growth_consistency_passed = True
    shadow_consistency_passed = True
    
    for run_id in run_histories:
        chain_path = os.path.join(settings.evidence_dir, run_id, "evidence_chain.jsonl")
        logs_path = os.path.join(settings.evidence_dir, run_id, "execution_logs.txt")
        
        chain_types = []
        agent_exec_order = []
        
        with open(chain_path, "r") as f:
            for line in f:
                event = json.loads(line)
                chain_types.append(event.get("event_type"))
                
                payload = event.get("payload", {})
                if isinstance(payload, dict) and "agent_id" in payload:
                    agent_exec_order.append(payload["agent_id"])
                elif isinstance(payload, str) and '"agent_id"' in payload:
                    try:
                        p = json.loads(payload)
                        if "agent_id" in p:
                            agent_exec_order.append(p["agent_id"])
                    except:
                        pass
                
        shadow_hashes = []
        if os.path.exists(logs_path):
            with open(logs_path, "r") as f:
                for line in f:
                    if "[Phase B Shadow]" in line and "pure decision hash:" in line:
                        shadow_hashes.append(line.split("pure decision hash: ")[1].strip())
                        
        if reference_chain_types is None:
            reference_chain_types = chain_types
            reference_shadow_hashes = shadow_hashes
            reference_event_count = len(chain_types)
            
            # Extract unique agents in order
            unique_agents = []
            for a in agent_exec_order:
                if a not in unique_agents:
                    unique_agents.append(a)
            
            try:
                issue_idx = unique_agents.index("Issue Agent")
                try:
                    reflection_idx = unique_agents.index("Reflection Agent")
                    if issue_idx >= reflection_idx:
                        orchestration_order_passed = False
                except ValueError:
                    pass
            except ValueError:
                pass 
                
        else:
            if len(chain_types) != reference_event_count:
                ledger_growth_consistency_passed = False
                full_pipeline_stability_passed = False
                
            if chain_types != reference_chain_types:
                full_pipeline_stability_passed = False
                
            if shadow_hashes != reference_shadow_hashes:
                shadow_consistency_passed = False
                
    report = ReplayDeterminismReport(
        total_runs=N_RUNS,
        full_pipeline_stability_passed=full_pipeline_stability_passed,
        orchestration_order_passed=orchestration_order_passed,
        ledger_growth_consistency_passed=ledger_growth_consistency_passed,
        shadow_consistency_passed=shadow_consistency_passed,
        execution_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )
    
    print("\n=== REPLAY VALIDATION REPORT ===")
    print(json.dumps(report.__dict__, indent=2))

if __name__ == "__main__":
    run_harness()
