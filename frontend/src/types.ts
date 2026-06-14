// ── AgentOps Nexus — Frontend Type Schema ────────────────────
// API Version: v1
// Schema version must match backend AgentState exactly.

export interface LogMessage {
  timestamp: string;
  agent: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'file' | 'class' | 'function' | 'unknown';
  properties?: any;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

export interface KnowledgeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Hypothesis {
  id: string;
  description: string;
  confidence: number;
  reasoning: string;
  target_file: string;
  validation_status: 'pending' | 'validated' | 'disproved';
}

export interface RCAReport {
  affected_component?: string;
  trigger?: string;
  cause?: string;
  evidence?: string;
  impact?: string;
  recommended_fix?: string;
}

export interface ProposedPatch {
  file: string;
  original: string;
  modified: string;
  diff: string;
}

export interface SecurityReport {
  vulnerabilities: Array<{
    file: string;
    issue: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    line: string;
  }>;
  status: 'passed' | 'failed';
  message: string;
}

export interface TestFailureAIAnalysis {
  identified_error: string;
  root_cause: string;
  severity: string;
  recommended_fix: string;
}

export interface TestFailureAIPatchProposal {
  file: string;
  diff: string[];
  explanation: string;
}

export interface AIPatchValidation {
  status: "APPROVED" | "REJECTED";
  confidence: number;
  reason?: string;
  failed_checks?: string[];
}

export interface TestResults {
  passed?: boolean;
  passed_count?: number;
  failed_count?: number;
  total_count?: number;
  log?: string;
  coverage?: number;
  ai_analysis?: TestFailureAIAnalysis;
  ai_patch_proposal?: TestFailureAIPatchProposal;
  ai_patch_validation?: AIPatchValidation;
}

export interface ConfidenceReport {
  score?: number;
  risk?: 'Low' | 'Medium' | 'High';
  safety?: 'Low' | 'Medium' | 'High';
  files_modified?: number;
  tests_passed?: string;
  factors?: {
    test_pass_weight: number;
    memory_retrieval_weight: number;
    security_scan_weight: number;
    modification_scope_weight: number;
    system_certainty_weight: number;
  };
}

export interface PRDetails {
  title?: string;
  body?: string;
  branch?: string;
  commit?: string;
  github_url?: string;
}

export interface Issue {
  id: string;
  title: string;
  description: string;
}

// ── New Phase A Types ────────────────────────────────────────

export interface PatchValidation {
  syntax_valid?: boolean;
  structural_valid?: boolean;
  unexpected_changes?: boolean;
  files_changed?: number;
  lines_added?: number;
  lines_deleted?: number;
  high_risk_files?: string[];
  complexity_delta?: number;
  risk_score?: number;
  approval?: 'SAFE_TO_TEST' | 'REVIEW_RECOMMENDED' | 'UNSAFE_BLOCKED';
  details?: string;
}

export interface ResourceUsage {
  tokens?: { used: number; limit: number };
  cost_usd?: { used: number; limit: number };
  elapsed_seconds?: { used: number; limit: number };
  files_modified?: { used: number; limit: number };
  lines_changed?: { used: number; limit: number };
  patch_iterations?: { used: number; limit: number };
  circuit_breaker_tripped?: boolean;
  trip_report?: any;
}

export interface ExecutionTimings {
  [agentName: string]: number; // agent name → duration in ms
}

export type RuntimeMode = 'demo' | 'production';

export interface SystemCapabilities {
  runtime_mode: RuntimeMode;
  production_ready: boolean;
  tools: Record<string, {
    available: boolean;
    version?: string;
    path?: string;
    error?: string;
  }>;
  llm: {
    gemini: boolean;
    openai: boolean;
    anthropic: boolean;
    any_available: boolean;
  };
  github: {
    token_present: boolean;
    repo_configured: boolean;
    fully_configured: boolean;
  };
}

// ── Main Agent State ─────────────────────────────────────────

export interface AgentState {
  // Issue Context
  issue_id: string;
  issue_title: string;
  issue_description: string;
  repo_path: string;
  work_dir: string;

  // Analysis Outputs
  files: string[];
  knowledge_graph: KnowledgeGraph;
  similar_fixes: any[];
  hypotheses: Hypothesis[];
  rca_report: RCAReport;
  rca_consistency_score: number;

  // Patch & Validation
  proposed_patch: ProposedPatch[];
  patch_validation: PatchValidation;

  // Security & Testing
  security_report: SecurityReport;
  test_results: TestResults;
  reflection: string;

  // Confidence & Governance
  confidence_report: ConfidenceReport;
  merge_decision: {
    decision?: 'auto_approve' | 'human_review' | 'reject';
    reason?: string;
    failure_report?: string;
  };
  pr_details: PRDetails;
  memory_status: string;

  // Execution Control
  run_id: string;
  runtime_mode: RuntimeMode;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'rca_conflict_detected';
  current_state: string;
  logs: LogMessage[];
  iteration: number;
  max_iterations: number;

  // Resource Tracking
  execution_timings: ExecutionTimings;
  resource_usage: ResourceUsage;
  llm_usage: any[];
}
