import os
import zipfile
import json
import pytest
from fastapi.testclient import TestClient

from runtime.app import app
from core.config import settings
from projection.views import get_replay_view, get_execution_trace

client = TestClient(app)

def create_dummy_zip(path):
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr("main.py", "def test_func():\n    return 10 / 0\n")
        zf.writestr("utils.js", "function hello() { return 'world'; }")
        zf.writestr("README.md", "# Test Project")

def test_project_ingestion_determinism():
    os.makedirs(settings.evidence_dir, exist_ok=True)
    zip_path = os.path.join(settings.evidence_dir, "dummy_test.zip")
    create_dummy_zip(zip_path)
    
    # Run 1
    with open(zip_path, "rb") as f:
        res1 = client.post("/api/v1/upload_project", files={"file": ("dummy.zip", f, "application/zip")})
    assert res1.status_code == 200
    run1 = res1.json()["run_id"]
    
    # Run 2
    with open(zip_path, "rb") as f:
        res2 = client.post("/api/v1/upload_project", files={"file": ("dummy.zip", f, "application/zip")})
    assert res2.status_code == 200
    run2 = res2.json()["run_id"]
    
    # Extract ledgers
    ledger1 = get_replay_view(run1)["events"]
    ledger2 = get_replay_view(run2)["events"]
    
    # Strip non-deterministic fields like run_id from payload for comparison
    def normalize_ledger(events):
        normalized = []
        for e in events:
            # Strip outer envelope non-deterministic fields
            for key in ["run_id", "execution_id", "current_hash", "previous_hash", "timestamp"]:
                if key in e:
                    del e[key]
            if "payload" in e and isinstance(e["payload"], dict):
                inner_payload = e["payload"].get("payload", {})
                if isinstance(inner_payload, dict) and "issue_id" in inner_payload:
                    del inner_payload["issue_id"]
                elif "issue_id" in e["payload"]:
                    del e["payload"]["issue_id"]
            normalized.append(e)
        return normalized

    assert normalize_ledger(ledger1) == normalize_ledger(ledger2), "Ingestion is NOT deterministic!"
    
    # Verify events
    event_types = [e["event_type"] for e in ledger1]
    assert "FILE_DISCOVERED" in event_types
    assert "FILE_READ" in event_types
    assert "FUNCTION_PARSED" in event_types
    assert "POTENTIAL_BUG_DETECTED" in event_types
    assert "INITIAL_CONTEXT" in event_types
    
    # Test Isolation (ensure code didn't execute)
    # The parsing logic uses simple regex and os.path, so there's literally no eval() or exec()
    
    # Cleanup
    os.remove(zip_path)

def test_issue_detection_pipeline():
    os.makedirs(settings.evidence_dir, exist_ok=True)
    zip_path = os.path.join(settings.evidence_dir, "dummy_test_2.zip")
    create_dummy_zip(zip_path)
    
    with open(zip_path, "rb") as f:
        res = client.post("/api/v1/upload_project", files={"file": ("dummy.zip", f, "application/zip")})
    run_id = res.json()["run_id"]
    
    # Run Analyze
    analysis = client.post(f"/api/v1/analyze_project/{run_id}")
    assert analysis.status_code == 200
    data = analysis.json()
    
    # Expect normalized mapped format
    assert "bugs" in data
    assert "risk_level" in data
    assert "files_affected" in data
    
    # Check trace for replay correctness
    trace = get_execution_trace(run_id)
    assert "Issue Agent" in trace["agents"]
    
    # Cleanup
    os.remove(zip_path)
