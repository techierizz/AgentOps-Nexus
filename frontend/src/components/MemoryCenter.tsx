import React from 'react';
import { motion } from 'framer-motion';
import { Database, ShieldCheck, AlertTriangle, AlertOctagon } from 'lucide-react';

interface MemoryCenterProps {
  similarFixes: Array<{
    id: string;
    similarity: number;
    title: string;
    root_cause: string;
    patch_summary: string;
    files_changed: string[];
    status?: string;
  }>;
  status?: string;
  isUpload?: boolean;
}

export const MemoryCenter: React.FC<MemoryCenterProps> = ({ similarFixes = [], status, isUpload }) => {
  const getMemoryBadge = (status: string = 'VERIFIED') => {
    switch (status) {
      case 'FAILED':
        return (
          <span className="flex items-center gap-1 text-[8px] bg-red-950/40 text-accentRed border border-red-900/60 px-1.5 py-0.5 rounded font-mono font-bold">
            <AlertOctagon className="w-2.5 h-2.5" />
            FAILED ATTEMPT
          </span>
        );
      case 'PARTIAL':
        return (
          <span className="flex items-center gap-1 text-[8px] bg-yellow-950/40 text-yellow-400 border border-yellow-800/60 px-1.5 py-0.5 rounded font-mono font-bold">
            <AlertTriangle className="w-2.5 h-2.5" />
            PARTIAL INVESTIGATION
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 text-[8px] bg-emerald-950/40 text-accentGreenLight border border-emerald-900/60 px-1.5 py-0.5 rounded font-mono font-bold glow-green">
            <ShieldCheck className="w-2.5 h-2.5" />
            VERIFIED ENGINEERING EXPERIENCE
          </span>
        );
    }
  };

  return (
    <div className="glass-panel p-5 flex flex-col h-full">
      <div className="flex items-center gap-2 mb-4 border-b border-borderDark pb-3">
        <Database className="w-5 h-5 text-emerald-400" />
        <h2 className="text-sm font-semibold tracking-wider font-mono">MEMORY ENGINE</h2>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 max-h-[300px] md:max-h-none scrollbar-thin">
        {similarFixes.map((fix, index) => (
          <motion.div
            key={fix.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: 1.01 }}
            className="p-3 bg-bgCard/60 border border-borderDark rounded-lg text-xs space-y-2 hover:border-emerald-800/40 transition-colors"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-[10px] bg-emerald-950/40 text-emerald-300 border border-emerald-900/60 px-1.5 py-0.5 rounded font-mono">
                {fix.id}
              </span>
              {getMemoryBadge(fix.status)}
            </div>
            
            <div className="flex justify-between items-center text-[10px] text-textMuted font-mono">
              <span className="font-semibold text-gray-200 line-clamp-1">{fix.title}</span>
              <span className="text-accentGreen text-[9px] font-bold">
                Sim: {(fix.similarity * 100).toFixed(0)}%
              </span>
            </div>

            <div className="space-y-1 font-mono text-[10px] text-textMuted bg-black/20 p-2 rounded">
              <p>
                <span className="text-emerald-500">ROOT CAUSE:</span> {fix.root_cause}
              </p>
              <p className="mt-1">
                <span className="text-indigo-400">RESOLVED BY:</span> {fix.patch_summary}
              </p>
            </div>

            <div className="flex items-center gap-1.5 text-[9px] text-textMuted font-mono">
              <span>Files:</span>
              {fix.files_changed.map(f => (
                <span key={f} className="bg-borderDark/40 px-1 py-0.2 rounded border border-borderDark text-gray-300">
                  {f}
                </span>
              ))}
            </div>
          </motion.div>
        ))}

        {similarFixes.length === 0 && (
          <div className="flex flex-col items-center justify-center py-10 text-center text-textMuted/40">
            <Database className="w-8 h-8 opacity-20 mb-2" />
            {status === 'completed' && isUpload ? (
              <>
                <p className="text-xs font-mono">Static Analysis Complete</p>
                <p className="text-[9px] mt-0.5">Vector memory matching is disabled during offline static analysis.</p>
              </>
            ) : (
              <>
                <p className="text-xs font-mono">Awaiting memory query results...</p>
                <p className="text-[9px] mt-0.5">Vector matching triggers during Memory Phase.</p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
