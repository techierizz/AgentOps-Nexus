import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Header } from './components/Header';
import { IssueQueue } from './components/IssueQueue';
import { LiveConsole } from './components/LiveConsole';
import { GraphView } from './components/GraphView';
import { MemoryCenter } from './components/MemoryCenter';
import { ConfidenceCenter } from './components/ConfidenceCenter';
import { AutonomousDecisionCenter } from './components/AutonomousDecisionCenter';
import { PRCenter } from './components/PRCenter';
import type { AgentState, Issue, SystemCapabilities } from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const App: React.FC = () => {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [selectedIssueId, setSelectedIssueId] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);
  
  // Shared state mapping current runner execution
  const [state, setState] = useState<AgentState>({
    issue_id: '',
    issue_title: '',
    issue_description: '',
    repo_path: '',
    files: [],
    knowledge_graph: { nodes: [], edges: [] },
    similar_fixes: [],
    hypotheses: [],
    rca_report: {},
    proposed_patch: [],
    patch_validation: {},
    security_report: { vulnerabilities: [], status: 'passed', message: '' },
    test_results: {},
    reflection: '',
    confidence_report: {},
    pr_details: {},
    status: 'idle',
    logs: [],
    iteration: 1,
    max_iterations: 3
  });

  const [systemHealth, setSystemHealth] = useState<SystemCapabilities | null>(null);

  // Fetch demo issues and system health on mount
  useEffect(() => {
    fetchHealth();
    fetchIssues();
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/system/health`);
      if (res.ok) {
        const data = await res.json();
        setSystemHealth(data);
      }
    } catch (e) {
      console.error("Failed to load system health:", e);
    }
  };

  const fetchIssues = async () => {
    try {
      const res = await fetch(`${API_BASE}/issues`);
      const data = await res.json();
      setIssues(data);
      if (data.length > 0) {
        setSelectedIssueId(data[0].id);
      }
    } catch (e) {
      console.error("Failed to load issues:", e);
    }
  };

  const handleResetRepo = async () => {
    setResetting(true);
    try {
      // In v1, reset-demo might still be at /api/reset-demo if we kept it out of v1,
      // but let's assume we use the compat router or we can call it on v1.
      // Wait, in main.py, router = APIRouter(prefix="/api/v1"). I didn't put reset-demo there.
      // Wait, I didn't put reset-demo in /api/v1 ? Let me check.
      // Ah, I need to call /api/reset-demo because I put it in the compat_router.
      // Let's use the v1 if it's there or keep it as API_BASE/../api/reset-demo.
      // Let's fix main.py so reset-demo is in v1 too. Actually, I will just call /api/reset-demo for now.
      const baseUrl = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL.replace('/v1', '') : 'http://localhost:8000/api';
      const res = await fetch(`${baseUrl}/reset-demo`, { method: 'POST' });
      if (res.ok) {
        // Reset local runner states
        setState({
          issue_id: '',
          issue_title: '',
          issue_description: '',
          repo_path: '',
          files: [],
          knowledge_graph: { nodes: [], edges: [] },
          similar_fixes: [],
          hypotheses: [],
          rca_report: {},
          proposed_patch: [],
          patch_validation: {},
          security_report: { vulnerabilities: [], status: 'passed', message: '' },
          test_results: {},
          reflection: '',
          confidence_report: {},
          pr_details: {},
          status: 'idle',
          logs: [],
          iteration: 1,
          max_iterations: 3
        });
        alert("Demo target repository successfully reset to its buggy state.");
      }
    } catch (e) {
      console.error("Failed to reset repo:", e);
    } finally {
      setResetting(false);
    }
  };

  const handleRunAgent = async (issueId: string) => {
    if (issueId.startsWith("upload_")) {
      try {
        setState(prev => ({ ...prev, status: 'running' }));
        const analyzeRes = await fetch(`${API_BASE}/analyze_project/${issueId}`, {
          method: "POST",
        });

        if (!analyzeRes.ok) {
          alert("Failed to analyze project.");
          setState(prev => ({ ...prev, status: 'failed' }));
          return;
        }

        const analyzeData = await analyzeRes.json();
        setState(prev => ({
          ...prev,
          status: 'completed',
          rca_report: { 
            error_type: analyzeData.risk_level, 
            stack_trace: "", 
            suspected_files: analyzeData.files_affected 
          },
          logs: [
            ...prev.logs,
            { timestamp: new Date().toISOString(), level: 'info', agent: 'System', message: `Re-analysis complete. Found ${analyzeData.bugs.length} potential issues.` }
          ]
        }));
      } catch (e) {
        console.error("Re-analysis error:", e);
        setState(prev => ({ ...prev, status: 'failed' }));
      }
      return;
    }

    // 1. Trigger agent runner in backend
    try {
      const res = await fetch(`${API_BASE}/run-agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ issue_id: issueId })
      });
      
      if (!res.ok) {
        alert("Failed to trigger agent pipeline.");
        return;
      }
      
      const runData = await res.json();
      
      // 2. Open Server-Sent Events (SSE) Stream to fetch real-time updates
      const eventSource = new EventSource(`${API_BASE}/stream/${runData.run_id}`);
      
      eventSource.onmessage = (event) => {
        const updatedState = JSON.parse(event.data) as AgentState;
        setState(prev => ({ ...prev, ...updatedState }));
        
        if (updatedState.status === 'completed' || updatedState.status === 'failed') {
          eventSource.close();
        }
      };

      eventSource.onerror = (err) => {
        console.error("SSE stream error:", err);
        eventSource.close();
      };
      
    } catch (e) {
      console.error("Error running agent:", e);
    }
  };

  const handleUploadProject = async (file: File) => {
    try {
      setResetting(true);
      const formData = new FormData();
      formData.append("file", file);

      // 1. Upload ZIP to ingestion engine
      const uploadRes = await fetch(`${API_BASE}/upload_project`, {
        method: "POST",
        body: formData,
      });

      if (!uploadRes.ok) {
        alert("Failed to upload project ZIP.");
        return;
      }
      
      const uploadData = await uploadRes.json();
      const newRunId = uploadData.run_id;
      
      // Select the new uploaded project pseudo-issue ID visually
      setSelectedIssueId(newRunId);
      setState({ ...state, status: 'running', issue_title: file.name, issue_description: "Uploaded Project Scanned." });

      // 2. Trigger IssueAgent normalization pipeline
      const analyzeRes = await fetch(`${API_BASE}/analyze_project/${newRunId}`, {
        method: "POST",
      });

      if (!analyzeRes.ok) {
        alert("Failed to analyze project.");
        setState({ ...state, status: 'failed' });
        return;
      }

      const analyzeData = await analyzeRes.json();
      
      // Update UI with newly structured data
      setState({
        ...state,
        status: 'completed',
        rca_report: { 
          error_type: analyzeData.risk_level, 
          stack_trace: "", 
          suspected_files: analyzeData.files_affected 
        },
        logs: [{ timestamp: new Date().toISOString(), level: 'info', agent: 'System', message: `Analysis complete. Found ${analyzeData.bugs.length} potential issues.` }]
      });

    } catch (e) {
      console.error("Upload error:", e);
      setState({ ...state, status: 'failed' });
    } finally {
      setResetting(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.15, delayChildren: 0.2 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 40, scale: 0.95 },
    show: { opacity: 1, y: 0, scale: 1, transition: { type: "spring", stiffness: 60, damping: 12 } }
  };

  return (
    <div className="min-h-screen p-4 md:p-6 max-w-7xl mx-auto flex flex-col justify-between">
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        {/* Header Control Panel */}
        <motion.div variants={itemVariants}>
          <Header
            status={state.status}
            iteration={state.iteration}
            maxIterations={state.max_iterations}
            onReset={handleResetRepo}
            resetting={resetting}
            systemHealth={systemHealth}
          />
        </motion.div>

        {/* Console Log + Agent Flow Chart */}
        <motion.div variants={itemVariants}>
          <LiveConsole logs={state.logs} status={state.status} />
        </motion.div>

        {/* Dashboard Grid Details */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {/* Column 1: Selector */}
          <motion.div variants={itemVariants} className="md:col-span-1">
            <IssueQueue
              issues={issues}
              selectedIssueId={selectedIssueId}
              onSelectIssue={setSelectedIssueId}
              onRunAgent={handleRunAgent}
              onUploadProject={handleUploadProject}
              status={state.status}
            />
          </motion.div>

          {/* Column 2: Vector Memory retrieved cases */}
          <motion.div variants={itemVariants} className="md:col-span-1">
            <MemoryCenter 
              similarFixes={state.similar_fixes} 
              status={state.status}
              isUpload={selectedIssueId?.startsWith('upload_')}
            />
          </motion.div>

          {/* Column 3: Safety and Risk assessment gauges */}
          <motion.div variants={itemVariants} className="md:col-span-1">
            <ConfidenceCenter
              confidence={state.confidence_report}
              security={state.security_report}
              tests={state.test_results}
              status={state.status}
              isUpload={selectedIssueId?.startsWith('upload_')}
            />
          </motion.div>
        </div>

        {/* Autonomous Decision Center Panel */}
        <motion.div variants={itemVariants}>
          <AutonomousDecisionCenter
            decision={state.merge_decision}
            confidence={state.confidence_report}
            security={state.security_report}
            tests={state.test_results}
            rcaScore={state.rca_consistency_score}
            patchValidation={state.patch_validation}
            status={state.status}
            isUpload={selectedIssueId?.startsWith('upload_')}
          />
        </motion.div>

        {/* Graph representation */}
        <motion.div variants={itemVariants}>
          <GraphView graph={state.knowledge_graph} rca={state.rca_report} status={state.status} />
        </motion.div>

        {/* Branch PR Details and Diffs */}
        <motion.div variants={itemVariants}>
          <PRCenter 
            pr={state.pr_details} 
            patch={state.proposed_patch?.[0] || null} 
            status={state.status}
            isUpload={selectedIssueId?.startsWith('upload_')}
          />
        </motion.div>
      </motion.div>

      <motion.footer 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="text-center font-mono text-[10px] text-textMuted/60 mt-8 border-t border-borderDark/40 pt-4"
      >
        © 2026 AgentOps Nexus. Developed for International AI Software Engineering Hackathon.
      </motion.footer>
    </div>
  );
};

export default App;
