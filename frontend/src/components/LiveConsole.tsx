import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, CheckCircle, BrainCircuit } from 'lucide-react';
import type { LogMessage } from '../types';

interface LiveConsoleProps {
  logs: LogMessage[];
  status: 'idle' | 'running' | 'completed' | 'failed';
}

const ALL_AGENTS = [
  { id: 'Issue Agent', label: 'Issue parsing' },
  { id: 'Repository Intel Agent', label: 'AST knowledge graph' },
  { id: 'Memory Agent', label: 'Vector retrieval' },
  { id: 'Hypothesis Agent', label: 'Rank hypotheses' },
  { id: 'Root Cause Agent', label: 'RCA validation' },
  { id: 'Patch Agent', label: 'Generate patch' },
  { id: 'Security Agent', label: 'Vulnerability scan' },
  { id: 'Testing Agent', label: 'Execute tests' },
  { id: 'Reflection Agent', label: 'Failure loop' },
  { id: 'Confidence Agent', label: 'Metric assessment' },
  { id: 'PR Agent', label: 'Git branch & PR' }
];

export const LiveConsole: React.FC<LiveConsoleProps> = ({ logs, status }) => {
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Find active agent name based on logs
  const activeAgent = logs.length > 0 && status === 'running'
    ? logs[logs.length - 1].agent
    : null;

  // Set of completed agents
  const completedAgents = new Set(
    logs.map(log => log.agent).filter(agent => agent !== activeAgent)
  );

  const getLogTypeStyles = (type: string) => {
    switch (type) {
      case 'success':
        return 'text-accentGreen';
      case 'warning':
        return 'text-yellow-400';
      case 'error':
        return 'text-accentRed font-semibold';
      default:
        return 'text-gray-300';
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      {/* 1. Interactive Agent Flow Column */}
      <div className="glass-panel p-5 lg:col-span-1 flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-2 mb-4 border-b border-borderDark pb-3">
            <BrainCircuit className="w-5 h-5 text-accentPurple" />
            <h2 className="text-sm font-semibold tracking-wider font-mono">AGENT PIPELINE</h2>
          </div>
          <div className="space-y-2.5">
            {ALL_AGENTS.map((agent) => {
              const isActive = activeAgent === agent.id;
              const isCompleted = completedAgents.has(agent.id) || (status === 'completed');
              
              let cardStyle = 'border-borderDark bg-bgCard/30 text-gray-400';
              if (isActive) {
                cardStyle = 'border-accentPurple bg-purple-950/20 text-purple-200 active-agent-card';
              } else if (isCompleted) {
                cardStyle = 'border-emerald-900/60 bg-emerald-950/5 text-accentGreenLight';
              }

              return (
                <div
                  key={agent.id}
                  className={`flex items-center justify-between p-2 px-3 border rounded-lg text-xs font-mono transition-all ${cardStyle}`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] opacity-65">{agent.id}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] font-sans">
                    {isActive && (
                      <span className="flex items-center gap-1 text-purple-400 animate-pulse font-mono">
                        THINKING...
                      </span>
                    )}
                    {isCompleted && (
                      <CheckCircle className="w-3.5 h-3.5 text-accentGreen" />
                    )}
                    {!isActive && !isCompleted && (
                      <span className="text-gray-600 font-mono">PENDING</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 2. Streaming Thought Console Log Column */}
      <div className="glass-panel p-5 lg:col-span-2 flex flex-col h-[400px]">
        <div className="flex items-center justify-between mb-4 border-b border-borderDark pb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-emerald-400" />
            <h2 className="text-sm font-semibold tracking-wider font-mono">LIVE THINKING ENGINE</h2>
          </div>
          <span className="text-[10px] text-textMuted font-mono">Stream: Active</span>
        </div>

        <div className="flex-1 bg-black/40 border border-borderDark rounded-lg p-3 overflow-y-auto font-mono text-xs space-y-2 scrollbar-thin">
          <AnimatePresence initial={false}>
            {logs.map((log, index) => (
              <motion.div 
                key={index} 
                initial={{ opacity: 0, x: -10, scale: 0.98 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                transition={{ duration: 0.2 }}
                className="flex items-start gap-2 leading-relaxed"
              >
                <span className="text-[10px] text-purple-400 opacity-60 flex-shrink-0 select-none">
                  [{log.timestamp}]
                </span>
                <span className="text-[10px] text-emerald-500 font-semibold flex-shrink-0 select-none">
                  {log.agent}:
                </span>
                <span className={`${getLogTypeStyles(log.type)} whitespace-pre-wrap`}>
                  {log.message}
                </span>
              </motion.div>
            ))}
          </AnimatePresence>

          {logs.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-textMuted/40 font-mono text-center">
              <Terminal className="w-10 h-10 mb-2 opacity-25" />
              <p>Deployment Console Awaiting Action...</p>
              <p className="text-[10px] mt-1">Select an issue from queue and click Deploy.</p>
            </div>
          )}
          <div ref={terminalEndRef} />
        </div>
      </div>
    </div>
  );
};
