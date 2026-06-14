from core.orchestrator.orchestrator import AgentOrchestrator
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)

print("Forcing invalid API key to trigger circuit breaker...")
settings.GEMINI_API_KEY = "INVALID_KEY"

orchestrator = AgentOrchestrator()

run_id = "test_failure_run_001"
print(f"Running pipeline with run_id: {run_id}")

orchestrator.run(
    issue_id="NEXUS-103",
    issue_title="TypeError: 'NoneType' object is not subscriptable on coupon checkout",
    issue_description="...",
    repo_path=settings.demo_repo_path,
    run_id=run_id
)

print("Pipeline finished!")
