import React from 'react';
import { GitPullRequest, GitBranch, Key, ExternalLink } from 'lucide-react';
import type { PRDetails, ProposedPatch } from '../types';

interface PRCenterProps {
  pr: PRDetails;
  patch: ProposedPatch | null;
  status?: string;
  isUpload?: boolean;
}

export const PRCenter: React.FC<PRCenterProps> = ({ pr = {}, patch, status, isUpload }) => {
  const renderDiff = (diffText: string) => {
    return diffText.split('\n').map((line, idx) => {
      let lineClass = 'text-gray-300';
      if (line.startsWith('+') && !line.startsWith('+++')) {
        lineClass = 'bg-emerald-950/40 text-emerald-300 border-l-2 border-emerald-500 pl-1';
      } else if (line.startsWith('-') && !line.startsWith('---')) {
        lineClass = 'bg-red-950/40 text-red-300 border-l-2 border-red-500 pl-1';
      } else if (line.startsWith('@@')) {
        lineClass = 'text-indigo-400 text-[10px] opacity-70';
      }

      return (
        <div key={idx} className={`font-mono text-xs whitespace-pre-wrap leading-relaxed ${lineClass}`}>
          {line}
        </div>
      );
    });
  };

  return (
    <div className="glass-panel p-5 mb-6">
      <div className="flex items-center gap-2 mb-4 border-b border-borderDark pb-3">
        <GitPullRequest className="w-5 h-5 text-purple-400" />
        <h2 className="text-sm font-semibold tracking-wider font-mono">PULL REQUEST CENTER</h2>
      </div>

      {pr.title ? (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Metadata details */}
          <div className="lg:col-span-2 space-y-4">
            <div className="p-3 bg-bgCard/60 border border-borderDark rounded-lg space-y-3 font-mono text-xs">
              <div>
                <p className="text-[10px] text-textMuted leading-none">PR TITLE</p>
                <p className="font-semibold text-gray-200 mt-1">{pr.title}</p>
              </div>

              <div className="flex justify-between items-center gap-2 border-t border-borderDark/60 pt-2">
                <div className="flex items-center gap-1.5 text-[10px]">
                  <GitBranch className="w-3.5 h-3.5 text-purple-400" />
                  <div>
                    <p className="text-[8px] text-textMuted leading-none">TARGET BRANCH</p>
                    <p className="text-gray-300 font-semibold mt-0.5">{pr.branch}</p>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 text-[10px]">
                  <Key className="w-3.5 h-3.5 text-indigo-400" />
                  <div>
                    <p className="text-[8px] text-textMuted leading-none">COMMIT HASH</p>
                    <p className="text-gray-300 font-semibold mt-0.5">{pr.commit}</p>
                  </div>
                </div>
              </div>
            </div>

            <a
              href={pr.github_url}
              target="_blank"
              rel="noreferrer"
              className="w-full flex items-center justify-center gap-2 py-2 bg-purple-900/30 hover:bg-purple-900/50 border border-purple-800 text-purple-200 rounded-lg text-xs font-semibold tracking-wider font-mono transition-all"
            >
              <ExternalLink className="w-4 h-4" />
              VIEW ON GITHUB
            </a>
          </div>

          {/* Interactive Code Diff */}
          <div className="lg:col-span-3 flex flex-col">
            <h3 className="text-xs font-mono font-semibold text-textMuted mb-2">PROPOSED PATCH DIFF ({patch?.file})</h3>
            <div className="flex-1 bg-black/50 border border-borderDark rounded-lg p-3 max-h-[250px] overflow-y-auto overflow-x-auto scrollbar-thin">
              {patch?.diff ? (
                renderDiff(patch.diff)
              ) : (
                <div className="text-textMuted/40 text-xs font-mono text-center py-10">
                  No diff records computed.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 text-center text-textMuted/40">
          <GitPullRequest className="w-10 h-10 mb-2 opacity-20" />
          {status === 'completed' && isUpload ? (
            <>
              <p className="text-xs font-mono">Static Analysis Complete</p>
              <p className="text-[9px] mt-0.5">Automated patch creation is not executed for static analysis runs.</p>
            </>
          ) : (
            <>
              <p className="text-xs font-mono">Awaiting patch commit execution...</p>
              <p className="text-[9px] mt-0.5">PR details are registered when all verification tests pass.</p>
            </>
          )}
        </div>
      )}
    </div>
  );
};
