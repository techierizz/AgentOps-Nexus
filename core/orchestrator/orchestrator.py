"""
AgentOps Nexus — Pure Event-Sourced Orchestrator
PHASE B COMPLETE → PRODUCTION READY EVENT-SOURCED ENGINE
"""
import time
from enum import Enum
from core.ledger.execution_artifact_manager import ExecutionArtifactManager
from runtime.budget_controller import RunBudgetController, BudgetLimits
from runtime.run_context import RunContext
from core.config import settings

from core.agents.issue_agent import IssueAgent
from core.agents.repo_agent import RepositoryIntelligenceAgent
from core.agents.memory_agent import MemoryAgent
from core.agents.hypothesis_agent import HypothesisAgent
from core.agents.rca_agent import RootCauseAgent
from core.agents.patch_agent import PatchAgent
from core.agents.patch_validation_agent import PatchValidationAgent
from core.agents.security_agent import SecurityAgent
from core.agents.testing_agent import TestingAgent
from core.agents.reflection_agent import ReflectionAgent
from core.agents.confidence_agent import ConfidenceAgent
from core.agents.merge_governor_agent import MergeGovernorAgent
from core.agents.pr_agent import PullRequestAgent
from core.agents.semantic_analysis_agent import SemanticAnalysisAgent
from core.agents.test_failure_analysis_agent import TestFailureAnalysisAgent
from core.agents.test_failure_patch_proposal_agent import TestFailurePatchProposalAgent
from core.agents.ai_patch_validation_agent import AIPatchValidationAgent
from core.runners.test_simulation_runner import TestSimulationRunner

class DecisionIntegrityViolation(Exception):
    pass

class AgentOrchestrator:
    def __init__(self):
        self.issue_agent = IssueAgent()
        self.semantic_agent = SemanticAnalysisAgent()
        self.repo_agent = RepositoryIntelligenceAgent()
        self.memory_agent = MemoryAgent()
        self.hypothesis_agent = HypothesisAgent()
        self.rca_agent = RootCauseAgent()
        self.patch_agent = PatchAgent()
        self.patch_validation_agent = PatchValidationAgent()
        self.security_agent = SecurityAgent()
        self.testing_agent = TestingAgent()
        self.reflection_agent = ReflectionAgent()
        self.confidence_agent = ConfidenceAgent()
        self.merge_governor_agent = MergeGovernorAgent()
        self.pr_agent = PullRequestAgent()
        self.test_failure_analysis_agent = TestFailureAnalysisAgent()
        self.test_failure_patch_proposal_agent = TestFailurePatchProposalAgent()
        self.ai_patch_validation_agent = AIPatchValidationAgent()

    def run(self, issue_id: str, issue_title: str, issue_description: str, repo_path: str, run_id: str = None) -> dict:
        """Pure Event-Sourced Pipeline Execution."""
        ctx = RunContext.create(
            issue_id=issue_id, issue_title=issue_title, issue_description=issue_description,
            repo_path=repo_path, base_evidence_dir=settings.evidence_dir, runtime_mode=settings.RUNTIME_MODE,
            run_id=run_id,
        )
        ctx.setup()
        artifacts = ExecutionArtifactManager(settings.evidence_dir, ctx.run_id)

        from core.agents.base import LedgerView
        import hashlib, json

        def run_pure_agent(agent_obj):
            ledger_view = LedgerView(artifacts, ctx.run_id)
            decision = agent_obj.execute_pure(ledger_view)
            
            # ── Integrity Verification ──
            canonical = json.dumps(decision.payload, sort_keys=True, separators=(",", ":"))
            recomputed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if decision.payload_hash != recomputed:
                raise DecisionIntegrityViolation(f"Mismatch: {decision.payload_hash} != {recomputed}")
                
            # Write Decision to Ledger
            artifacts.write(decision)
            artifacts.append_structured_log("PHASE_B_SHADOW", f"{agent_obj.name} | {decision.payload_hash}")
            artifacts.append_structured_log("SHADOW_VERIFY", "PASS")
            return decision

        # ── Execution Pipeline ──
        
        # 1. INITIAL_CONTEXT
        artifacts.write({
            "event_type": "INITIAL_CONTEXT", 
            "payload": {
                "issue_id": issue_id, "issue_title": issue_title, 
                "issue_description": issue_description, "repo_path": repo_path
            }
        })
        run_pure_agent(self.issue_agent)

        # 2. INDEX_REPO
        run_pure_agent(self.repo_agent)

        # 3. SEARCH_MEMORY
        run_pure_agent(self.memory_agent)

        # 4. HYPOTHESIZE
        run_pure_agent(self.hypothesis_agent)

        # 5. VALIDATE_RCA
        run_pure_agent(self.rca_agent)

        ledger_state = LedgerView(artifacts, ctx.run_id).get_projection("full_state")
        
        if ledger_state.get("status") == "rca_conflict_detected":
            # 6. EVALUATE_CONFIDENCE directly
            run_pure_agent(self.confidence_agent)
        else:
            # Enter Patch Loop
            for iteration in range(settings.MAX_PATCH_ITERATIONS):
                run_pure_agent(self.patch_agent)
                run_pure_agent(self.patch_validation_agent)
                
                ledger_state = LedgerView(artifacts, ctx.run_id).get_projection("full_state")
                approval = ledger_state.get("approval", "SAFE_TO_TEST")
                
                if approval == "UNSAFE_BLOCKED":
                    continue
                    
                run_pure_agent(self.security_agent)
                run_pure_agent(self.testing_agent)
                
                ledger_state = LedgerView(artifacts, ctx.run_id).get_projection("full_state")
                
                # Run AI test failure analysis if tests failed
                test_results = ledger_state.get("test_results", {})
                if test_results.get("failed_count", 0) > 0:
                    run_pure_agent(self.test_failure_analysis_agent)
                    run_pure_agent(self.test_failure_patch_proposal_agent)
                    
                    # Phase D.4 - Validation & Simulation Gate
                    decision = run_pure_agent(self.ai_patch_validation_agent)
                    if decision.decision_type == "PATCH_SIMULATION_REQUEST":
                        runner = TestSimulationRunner(artifacts, ctx.run_id, repo_path, ctx.issue_id)
                        runner.run_simulation(decision.payload)
                    
                if ledger_state.get("passed", False) or test_results.get("passed", False):
                    break
                    
            run_pure_agent(self.confidence_agent)
            
        run_pure_agent(self.merge_governor_agent)
        run_pure_agent(self.pr_agent)
        
        artifacts.finalize()
        return LedgerView(artifacts, ctx.run_id).get_projection("full_state")

    def run_issue_agent_only(self, run_id: str, evidence_dir: str) -> dict:
        """Runs IssueAgent and SemanticAnalysisAgent for ingested projects and normalizes output."""
        from core.agents.base import LedgerView
        import hashlib, json
        
        artifacts = ExecutionArtifactManager(evidence_dir, run_id)
        
        def run_pure_agent(agent_obj):
            ledger_view = LedgerView(artifacts, run_id)
            decision = agent_obj.execute_pure(ledger_view)
            
            canonical = json.dumps(decision.payload, sort_keys=True, separators=(",", ":"))
            recomputed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if decision.payload_hash != recomputed:
                raise DecisionIntegrityViolation(f"Mismatch: {decision.payload_hash} != {recomputed}")
                
            artifacts.write(decision)
            return decision

        # 1. Execute IssueAgent (Deterministic basic extraction)
        issue_decision = run_pure_agent(self.issue_agent)
        
        # 2. Execute SemanticAnalysisAgent (LLM Advisor encapsulated as Ledger Event)
        semantic_decision = run_pure_agent(self.semantic_agent)
        
        artifacts.finalize()
        
        # ── Orchestrator Normalization Layer (Module 4) ──
        legacy_payload = issue_decision.payload
        files = legacy_payload.get("files", [])
        
        # Merge basic errors and AI findings
        bugs = []
        basic_error_type = legacy_payload.get("rca_report", {}).get("error_type", "Unknown")
        if basic_error_type != "Unknown":
            bugs.append({"type": basic_error_type, "description": "Deterministic parser finding", "severity": "MEDIUM"})
            
        ai_findings = semantic_decision.payload.get("ai_findings", [])
        for f in ai_findings:
            bugs.append({
                "type": f.get("severity", "MEDIUM") + " Risk",
                "description": f.get("explanation", "AI detected issue"),
                "suggested_fix": f.get("suggested_fix", ""),
                "path": f.get("path", "")
            })
            if f.get("path") and f.get("path") not in files:
                files.append(f.get("path"))
        
        normalized_result = {
            "bugs": bugs,
            "risk_level": "High" if any(b.get("type", "").startswith("HIGH") for b in bugs) else "Medium",
            "files_affected": files
        }
        
        return normalized_result
