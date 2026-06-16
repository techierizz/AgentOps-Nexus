import React from 'react';
import { motion } from 'framer-motion';
import { Bot, RefreshCw, ShieldCheck } from 'lucide-react';
import type { SystemCapabilities } from '../types';

interface HeaderProps {
  status: 'idle' | 'running' | 'completed' | 'failed' | 'rca_conflict_detected';
  iteration: number;
  maxIterations: number;
  onReset: () => void;
  resetting: boolean;
  systemHealth?: SystemCapabilities | null;
}

export const Header: React.FC<HeaderProps> = ({
  status,
  iteration,
  maxIterations,
  onReset,
  resetting,
  systemHealth
}) => {
  const getStatusBadge = () => {
    switch (status) {
      case 'running':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold bg-purple-950 text-accentPurpleLight border border-purple-800 rounded-full animate-pulse-slow">
            <span className="w-2 h-2 bg-accentPurple rounded-full animate-ping-slow" />
            RESOLVING (ITERATION {iteration}/{maxIterations})
          </span>
        );
      case 'completed':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold bg-emerald-950 text-accentGreenLight border border-emerald-800 rounded-full glow-green">
            <span className="w-2 h-2 bg-accentGreen rounded-full" />
            STABLE - PR OPENED
          </span>
        );
      case 'failed':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold bg-red-950 text-red-400 border border-red-900 rounded-full">
            <span className="w-2 h-2 bg-accentRed rounded-full" />
            FAILED
          </span>
        );
      case 'rca_conflict_detected':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold bg-orange-950 text-orange-400 border border-orange-900 rounded-full">
            <span className="w-2 h-2 bg-orange-500 rounded-full" />
            RCA CONFLICT
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold bg-gray-900 text-gray-400 border border-gray-800 rounded-full">
            <span className="w-2 h-2 bg-gray-500 rounded-full" />
            SYSTEM IDLE
          </span>
        );
    }
  };

  const isProduction = systemHealth?.runtime_mode === 'production';

  return (
    <div className="mb-6">
      {/* Mode Banner */}
      {systemHealth && (
        <div className={`w-full py-1.5 text-center text-[10px] font-mono tracking-widest font-bold uppercase ${
          isProduction 
            ? 'bg-emerald-950/80 text-emerald-400 border-b border-emerald-900/50' 
            : 'bg-amber-950/80 text-amber-400 border-b border-amber-900/50'
        }`}>
          {isProduction 
            ? 'PRODUCTION MODE — All systems verified.' 
            : 'DEMO MODE — Simulation and fallback systems enabled.'}
        </div>
      )}

      <motion.header 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring" as const, stiffness: 100 }}
        className="glass-panel px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4 glow-purple"
      >
      <div className="flex items-center gap-3">
        <motion.div 
          animate={{ scale: [1, 1.05, 1], rotate: [0, 5, -5, 0] }}
          transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
          className="p-2.5 bg-gradient-to-tr from-purple-600 to-emerald-500 rounded-lg"
        >
          <Bot className="w-7 h-7 text-white" />
        </motion.div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-white via-purple-300 to-emerald-300">
              AGENTOPS NEXUS
            </h1>
            <span className="text-[10px] bg-purple-900/40 text-purple-300 border border-purple-800/60 px-1.5 py-0.5 rounded font-mono">
              v1.0.0
            </span>
          </div>
          <p className="text-xs text-textMuted font-mono">
            Autonomous Self-Learning Multi-Agent Bug Resolution Platform
          </p>
        </div>
      </div>

      <div className="flex flex-col items-end gap-3">
        <div className="flex items-center gap-4 flex-wrap">
          {getStatusBadge()}
          
          <motion.button
            whileHover={!resetting && status !== 'running' ? { scale: 1.05 } : {}}
            whileTap={!resetting && status !== 'running' ? { scale: 0.95 } : {}}
            onClick={onReset}
            disabled={resetting || status === 'running'}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-mono rounded-lg border border-borderDark bg-bgCard text-gray-300 transition-colors ${
              status === 'running' 
                ? 'opacity-50 cursor-not-allowed' 
                : 'hover:bg-bgHover hover:text-white hover:border-purple-500'
            }`}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin text-purple-400' : ''}`} />
            {resetting ? 'RESETTING...' : 'RESET DEMO REPO'}
          </motion.button>
        </div>

        {/* Capabilities Indicator */}
        {systemHealth && (
          <div className="flex items-center gap-3 text-[10px] font-mono text-textMuted border border-borderDark/40 bg-bgCard/30 px-3 py-1 rounded-full">
            <span className="flex items-center gap-1">
              {systemHealth.github?.fully_configured ? <span className="text-emerald-400">✓</span> : <span className="text-red-400">✗</span>} GITHUB
            </span>
            <span className="flex items-center gap-1">
              {systemHealth.llm?.any_available ? <span className="text-emerald-400">✓</span> : <span className="text-red-400">✗</span>} LLM
            </span>
            <span className="flex items-center gap-1">
              {systemHealth.tools?.docker?.available ? <span className="text-emerald-400">✓</span> : <span className="text-red-400">✗</span>} DOCKER
            </span>
            <span className="flex items-center gap-1">
              {(systemHealth.tools?.semgrep?.available && systemHealth.tools?.bandit?.available) ? <span className="text-emerald-400">✓</span> : <span className="text-red-400">✗</span>} SECURITY
            </span>
          </div>
        )}
      </div>
    </motion.header>
    </div>
  );
};
