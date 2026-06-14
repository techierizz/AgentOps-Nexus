import asyncio
import json
import threading
import os
import time
import uuid
import shutil
from fastapi import FastAPI, HTTPException, APIRouter, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.config import settings
from runtime.database import DEMO_ISSUES, reset_target_repository
from core.orchestrator.orchestrator import AgentOrchestrator
from projection.views import get_ledger_projection_view, get_execution_trace, get_replay_view, get_evidence_chain_path
from ingestion.project_loader import load_project
from ingestion.code_to_ledger import convert_project_to_ledger

# ── Application Setup ─────────────────────────────────────────
app = FastAPI(title=settings.PROJECT_NAME, version=settings.API_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api/v1")

class IssueRunRequest(BaseModel):
    issue_id: str

# ── Endpoints ─────────────────────────────────────────────────

@router.get("/system/health")
def system_health():
    return {
        "status": "ok",
        "architecture": "phase_b_event_sourced",
        "runtime_mode": settings.RUNTIME_MODE,
        "production_ready": True
    }

@router.get("/issues")
def get_issues():
    return DEMO_ISSUES

@router.post("/upload_project")
async def upload_project(file: UploadFile = File(...)):
    run_id = f"upload_{uuid.uuid4().hex[:8]}"
    
    # Save the uploaded ZIP securely
    os.makedirs(settings.evidence_dir, exist_ok=True)
    zip_path = os.path.join(settings.evidence_dir, f"{run_id}.zip")
    
    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Step 1: Load Project (extract and collect metadata)
        artifact = load_project(run_id, zip_path)
        
        # Step 2: Convert to Ledger Events
        convert_project_to_ledger(artifact, settings.evidence_dir)
        
        return {
            "run_id": run_id,
            "status": "INGESTED",
            "message": "Project successfully converted to ledger events"
        }
    finally:
        # Cleanup the uploaded zip
        if os.path.exists(zip_path):
            os.remove(zip_path)

@router.post("/analyze_project/{run_id}")
def analyze_project(run_id: str):
    orchestrator = AgentOrchestrator()
    try:
        normalized_result = orchestrator.run_issue_agent_only(run_id, settings.evidence_dir)
        return normalized_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-demo")
def reset_demo():
    reset_target_repository(settings.demo_repo_path)
    return {"status": "success"}

def run_orchestrator_background(issue_id: str, issue_title: str, issue_description: str, run_id: str = None):
    """Pure background orchestrator trigger. No state tracking."""
    orchestrator = AgentOrchestrator()
    try:
        orchestrator.run(
            issue_id=issue_id,
            issue_title=issue_title,
            issue_description=issue_description,
            repo_path=settings.demo_repo_path,
            run_id=run_id
        )
    except Exception as e:
        print(f"Orchestrator background failure: {e}")

@router.post("/run-agent")
def trigger_run(req: IssueRunRequest):
    if req.issue_id.startswith("upload_"):
        return {"status": "started", "run_id": req.issue_id}

    issue = next((iss for iss in DEMO_ISSUES if iss["id"] == req.issue_id), None)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")

    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_hash = uuid.uuid4().hex[:8]
    actual_run_id = f"run_{timestamp}_{req.issue_id}_{unique_hash}"

    # Reset repo to ensure clean run
    reset_target_repository(settings.demo_repo_path)

    # Fire and forget orchestrator
    threading.Thread(
        target=run_orchestrator_background,
        args=(issue["id"], issue["title"], issue["description"], actual_run_id),
        daemon=True
    ).start()

    return {"status": "started", "run_id": actual_run_id}

@router.get("/trace/{run_id}")
def trace_run(run_id: str):
    return get_execution_trace(run_id)

@router.get("/replay/{run_id}")
def replay_run(run_id: str):
    return get_replay_view(run_id)

@router.get("/stream/{run_id}")
async def stream_run_updates(run_id: str):
    """
    Streams derived projection state by tailing the ledger file.
    No in-memory state tracking.
    """
    chain_file = get_evidence_chain_path(run_id)

    async def event_generator():
        # Wait up to 5 seconds for file creation
        for _ in range(10):
            # Re-evaluate in case the orchestrator just created it
            chain_file = get_evidence_chain_path(run_id)
            if os.path.exists(chain_file):
                break
            await asyncio.sleep(0.5)
            
        if not os.path.exists(chain_file):
            yield f"data: {json.dumps({'status': 'failed', 'logs': [{'message': 'Ledger file not found'}]})}\n\n"
            return
            
        # File exists. Poll the projection layer
        last_event_count = 0
        last_state = {}
        
        while True:
            # Check file length (lines) to avoid expensive projection if no new data
            try:
                with open(chain_file, "r", encoding="utf-8") as f:
                    current_count = sum(1 for _ in f)
            except Exception:
                current_count = last_event_count
                
            if current_count > last_event_count:
                last_event_count = current_count
                state = get_ledger_projection_view(run_id)
                # Ensure status transitions exist
                # Calculate status heuristically if not explicitly "completed" or "failed"
                if "status" not in state or state["status"] == "idle":
                    state["status"] = "running"
                    
                # If we see PR Agent or Merge Governor decision, consider it completed
                if any(k in state for k in ["pr_details", "merge_decision", "memory_status"]):
                    state["status"] = "completed"
                    
                yield f"data: {json.dumps(state)}\n\n"
                last_state = state
                
                if state.get("status") in ["completed", "failed"]:
                    break
                    
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

app.include_router(router)

# Compatibility Router for older frontend endpoints
compat_router = APIRouter(prefix="/api")

@compat_router.get("/issues")
def compat_issues():
    return DEMO_ISSUES

@compat_router.post("/run-agent")
def compat_run(req: IssueRunRequest):
    return trigger_run(req)

@compat_router.get("/stream/{run_id}")
async def compat_stream(run_id: str):
    return await stream_run_updates(run_id)

@compat_router.post("/reset-demo")
def compat_reset():
    return reset_demo()

app.include_router(compat_router)
