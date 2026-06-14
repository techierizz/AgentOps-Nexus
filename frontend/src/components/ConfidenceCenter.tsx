import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, HelpCircle, Check, AlertTriangle, AlertOctagon } from 'lucide-react';
import type { ConfidenceReport, SecurityReport, TestResults } from '../types';

interface ConfidenceCenterProps {
  confidence: ConfidenceReport;
  security: SecurityReport;
  tests: TestResults;
  status?: string;
  isUpload?: boolean;
}

export const ConfidenceCenter: React.FC<ConfidenceCenterProps> = ({
  confidence,
  security,
  tests,
  status,
  isUpload
}) => {
  const score = confidence?.score || 0;
  const risk = confidence?.risk || 'N/A';
  const safety = confidence?.safety || 'N/A';
  const modifiedCount = confidence?.files_modified || 0;

  const getScoreColor = (val: number) => {
    if (val >= 85) return 'text-accentGreen';
    if (val >= 60) return 'text-yellow-400';
    return 'text-accentRed';
  };

  const getScoreBorder = (val: number) => {
    if (val >= 85) return 'border-accentGreen/40';
    if (val >= 60) return 'border-yellow-500/40';
    return 'border-accentRed/40';
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'Low':
        return <ShieldCheck className="w-4.5 h-4.5 text-accentGreen" />;
      case 'Medium':
        return <AlertTriangle className="w-4.5 h-4.5 text-yellow-400" />;
      case 'High':
        return <AlertOctagon className="w-4.5 h-4.5 text-accentRed" />;
      default:
        return <HelpCircle className="w-4.5 h-4.5 text-gray-500" />;
    }
  };

  return (
    <div className="glass-panel p-5 flex flex-col h-full">
      <div className="flex items-center gap-2 mb-4 border-b border-borderDark pb-3">
        <ShieldCheck className="w-5 h-5 text-indigo-400" />
        <h2 className="text-sm font-semibold tracking-wider font-mono">CONFIDENCE & SAFETY</h2>
      </div>

      {score > 0 ? (
        <div className="flex-1 space-y-4">
          {/* Circular Score display */}
          <div className="flex items-center justify-around gap-4">
            <div className={`w-24 h-24 rounded-full border-4 flex flex-col items-center justify-center bg-black/20 ${getScoreBorder(score)}`}>
              <span className={`text-2xl font-bold font-mono tracking-tighter ${getScoreColor(score)}`}>
                {score}%
              </span>
              <span className="text-[8px] text-textMuted font-mono">CONFIDENCE</span>
            </div>

            <div className="space-y-2 font-mono text-xs">
              <div className="flex items-center gap-2">
                {getRiskIcon(risk)}
                <div>
                  <p className="text-[9px] text-textMuted leading-none">RISK ASSESSMENT</p>
                  <p className="font-bold text-gray-200 mt-0.5">{risk} Risk</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <ShieldCheck className={`w-4.5 h-4.5 ${safety === 'High' ? 'text-accentGreen' : 'text-yellow-400'}`} />
                <div>
                  <p className="text-[9px] text-textMuted leading-none">ESTIMATED SAFETY</p>
                  <p className="font-bold text-gray-200 mt-0.5">{safety} Merge</p>
                </div>
              </div>
            </div>
          </div>

          {/* Test Coverage & Security Badge */}
          <div className="grid grid-cols-2 gap-3 font-mono text-[10px]">
            <div className="p-2 bg-black/20 border border-borderDark rounded">
              <p className="text-textMuted">SECURITY STATUS</p>
              <p className={`font-semibold mt-1 ${security?.status === 'passed' ? 'text-accentGreen' : 'text-accentRed'}`}>
                {security?.status?.toUpperCase() || 'UNKNOWN'}
              </p>
            </div>
            <div className="p-2 bg-black/20 border border-borderDark rounded">
              <p className="text-textMuted">TEST COVERAGE</p>
              <p className="text-gray-200 font-semibold mt-1">
                {tests?.coverage ? `${tests.coverage}%` : 'N/A'}
              </p>
            </div>
          </div>

          {/* Weighted Factors Slider Preview */}
          {confidence.factors && (
            <div className="space-y-2 font-mono text-[9px] text-textMuted border-t border-borderDark pt-3">
              <p className="text-[10px] text-gray-300 font-semibold mb-1">DECISION MATRIX WEIGHTS</p>
              
              <div className="flex justify-between items-center">
                <span>Unit Tests ({confidence.factors.test_pass_weight}/40)</span>
                <div className="w-24 h-1.5 bg-black/40 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${(confidence.factors.test_pass_weight / 40) * 100}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full bg-emerald-500" 
                  />
                </div>
              </div>

              <div className="flex justify-between items-center">
                <span>Memory Match ({confidence.factors.memory_retrieval_weight}/20)</span>
                <div className="w-24 h-1.5 bg-black/40 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${(confidence.factors.memory_retrieval_weight / 20) * 100}%` }}
                    transition={{ duration: 1, ease: "easeOut", delay: 0.2 }}
                    className="h-full bg-purple-500" 
                  />
                </div>
              </div>

              <div className="flex justify-between items-center">
                <span>Security Check ({confidence.factors.security_scan_weight}/20)</span>
                <div className="w-24 h-1.5 bg-black/40 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${(confidence.factors.security_scan_weight / 20) * 100}%` }}
                    transition={{ duration: 1, ease: "easeOut", delay: 0.4 }}
                    className="h-full bg-blue-500" 
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-center text-textMuted/40">
          <ShieldCheck className="w-10 h-10 opacity-20 mb-2" />
          {status === 'completed' && isUpload ? (
            <>
              <p className="text-xs font-mono">Static Analysis Complete</p>
              <p className="text-[9px] mt-0.5">Confidence metrics are only available during full autonomous deployments.</p>
            </>
          ) : (
            <>
              <p className="text-xs font-mono">Awaiting metric calculations...</p>
              <p className="text-[9px] mt-0.5">Confidence engine calculates scores pre-PR.</p>
            </>
          )}
        </div>
      )}
    </div>
  );
};
