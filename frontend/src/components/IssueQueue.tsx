import React from 'react';
import { motion } from 'framer-motion';
import { Play, FileWarning, HelpCircle } from 'lucide-react';
import type { Issue } from '../types';

interface IssueQueueProps {
  issues: Issue[];
  selectedIssueId: string | null;
  onSelectIssue: (id: string) => void;
  onRunAgent: (id: string) => void;
  onUploadProject: (file: File) => void;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'rca_conflict_detected';
}

export const IssueQueue: React.FC<IssueQueueProps> = ({
  issues,
  selectedIssueId,
  onSelectIssue,
  onRunAgent,
  onUploadProject,
  status
}) => {
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUploadProject(e.target.files[0]);
    }
  };

  return (
    <div className="glass-panel p-5 flex flex-col h-full">
      <div className="flex items-center gap-2 mb-4">
        <FileWarning className="w-5 h-5 text-purple-400" />
        <h2 className="text-sm font-semibold tracking-wider font-mono">ISSUE QUEUE</h2>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-1 max-h-[350px] md:max-h-none">
        {issues.map((issue) => {
          const isSelected = selectedIssueId === issue.id;
          return (
            <motion.div
              key={issue.id}
              whileHover={status !== 'running' ? { scale: 1.02, y: -2 } : {}}
              whileTap={status !== 'running' ? { scale: 0.98 } : {}}
              onClick={() => status !== 'running' && onSelectIssue(issue.id)}
              className={`p-3 rounded-lg border transition-colors cursor-pointer ${
                isSelected
                  ? 'bg-purple-950/20 border-purple-500/80 shadow-md'
                  : 'bg-bgCard/60 border-borderDark hover:border-purple-900/60 hover:bg-bgHover'
              } ${status === 'running' ? 'opacity-60 cursor-not-allowed' : ''}`}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-[10px] font-mono bg-purple-900/30 text-purple-300 border border-purple-800/50 px-1.5 py-0.5 rounded">
                  {issue.id}
                </span>
                <span className="text-[10px] text-textMuted font-mono">Target: Repo</span>
              </div>
              <h3 className="text-xs font-semibold mt-2 text-gray-200 line-clamp-1">
                {issue.title}
              </h3>
              <p className="text-[11px] text-textMuted mt-1 line-clamp-2">
                {issue.description.replace(/```[\s\S]*?```/g, '')}
              </p>
            </motion.div>
          );
        })}

        {issues.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center text-textMuted">
            <HelpCircle className="w-8 h-8 opacity-40 mb-2" />
            <p className="text-xs font-mono">No issues loaded.</p>
          </div>
        )}
      </div>

      <div className="mt-4 flex flex-col gap-2">
        <input 
          type="file" 
          accept=".zip" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          className="hidden" 
        />
        <motion.button
          whileHover={status !== 'running' ? { scale: 1.02 } : {}}
          whileTap={status !== 'running' ? { scale: 0.98 } : {}}
          onClick={() => fileInputRef.current?.click()}
          disabled={status === 'running'}
          className={`w-full flex items-center justify-center gap-2 py-2 px-4 text-[10px] font-semibold tracking-wider font-mono rounded-lg transition-colors border border-borderDark ${
            status === 'running'
              ? 'opacity-50 cursor-not-allowed'
              : 'bg-bgCard hover:bg-bgHover hover:border-purple-500/50 text-gray-300'
          }`}
        >
          UPLOAD PROJECT (.ZIP)
        </motion.button>
      </div>

      {selectedIssueId && (
        <motion.button
          whileHover={status !== 'running' && !(status === 'completed' && selectedIssueId.startsWith("upload_")) ? { scale: 1.02 } : {}}
          whileTap={status !== 'running' && !(status === 'completed' && selectedIssueId.startsWith("upload_")) ? { scale: 0.98 } : {}}
          onClick={() => onRunAgent(selectedIssueId)}
          disabled={status === 'running' || (status === 'completed' && selectedIssueId.startsWith("upload_"))}
          className={`mt-4 w-full flex items-center justify-center gap-2 py-2.5 px-4 text-xs font-semibold tracking-wider font-mono rounded-lg transition-colors ${
            status === 'running' || (status === 'completed' && selectedIssueId.startsWith("upload_"))
              ? 'bg-purple-950/40 text-purple-400 border border-purple-900 cursor-not-allowed'
              : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-500/10'
          }`}
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          {selectedIssueId.startsWith("upload_") 
            ? (status === 'completed' ? "STATIC ANALYSIS COMPLETE" : "RUN STATIC ANALYSIS") 
            : "DEPLOY AGENTS"}
        </motion.button>
      )}
    </div>
  );
};
