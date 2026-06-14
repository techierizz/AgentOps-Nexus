from core.orchestrator.orchestrator import AgentOrchestrator
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)

run_id = "run_20260614_230239_NEXUS-103_cc88263a"

print(f"Testing deterministic replay for run_id: {run_id}")
orchestrator = AgentOrchestrator()

orchestrator.run(
    issue_id="NEXUS-103",
    issue_title="TypeError: 'NoneType' object is not subscriptable on coupon checkout",
    issue_description="...",
    repo_path=settings.demo_repo_path,
    run_id=run_id
)

print("Replay completed successfully!")
