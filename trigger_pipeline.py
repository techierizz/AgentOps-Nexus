from core.orchestrator.orchestrator import AgentOrchestrator
from core.config import settings

orchestrator = AgentOrchestrator()
run_id = "test_run_validation_001"
result = orchestrator.run(
    issue_id="NEXUS-103",
    issue_title="TypeError: NoneType object is not subscriptable",
    issue_description="Coupon processing",
    repo_path=settings.demo_repo_path,
    run_id=run_id
)
print("Pipeline finished.")
