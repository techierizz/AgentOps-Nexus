import os
import sys
import glob
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.orchestrator.orchestrator import AgentOrchestrator

def run_determinism_test(iterations=100):
    print(f"Starting Determinism CI Gate: {iterations} Iterations")
    hash_sets = []
    
    for i in range(iterations):
        run_id = f"CI-DET-RUN-{i}"
        try:
            state = AgentOrchestrator().run('ISSUE-999', 'CI Determinism Test', 'Determinism verification', 'test_repo')
        except Exception as e:
            print(f"Run {i} failed: {e}")
            sys.exit(1)
            
        # Collect the hashes from the observability cache
        dirs = sorted(glob.glob('d:/Japan/artifacts/*ISSUE-999*'))
        if not dirs:
            print(f"No artifacts found for run {i}")
            sys.exit(1)
            
        latest = dirs[-1]
        cache_path = os.path.join(latest, 'execution_logs.txt')
        
        if not os.path.exists(cache_path):
            print(f"Logs missing for run {i}")
            sys.exit(1)
            
        with open(cache_path, 'r', encoding='utf-8') as f:
            logs = f.readlines()
            
        # Extract AgentDecision payload hashes from SHADOW log
        payload_hashes = []
        for line in logs:
            if "[PHASE_B_SHADOW]" in line:
                parts = line.split("|")
                if len(parts) >= 2:
                    payload_hashes.append(parts[1].strip())
                    
        hash_sets.append(tuple(payload_hashes))
        print(f"Run {i} completed. Generated {len(payload_hashes)} decision hashes.")
        
    # Validation
    reference = hash_sets[0]
    variance = 0
    for i, h_set in enumerate(hash_sets):
        if h_set != reference:
            print(f"VARIANCE DETECTED in run {i}!")
            variance += 1
            
    if variance > 0:
        print(f"Determinism CI Gate FAILED. Variance: {variance}")
        sys.exit(1)
    else:
        print(f"Determinism CI Gate PASSED. 100% Identical Execution across {iterations} runs.")
        print("[CI_GATE] hash consistency verified")
        sys.exit(0)

if __name__ == "__main__":
    run_determinism_test(100)
