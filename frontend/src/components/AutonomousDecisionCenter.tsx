import React from 'react';
import { Gavel, CheckCircle2, AlertTriangle, XOctagon, ClipboardList, ShieldAlert } from 'lucide-react';
import type { ConfidenceReport, SecurityReport, TestResults, PatchValidation } from '../types';

interface AutonomousDecisionCenterProps {
  decision: {
    decision?: 'auto_approve' | 'human_review' | 'reject';
    reason?: string;
    failure_report?: string;
  };
  confidence: ConfidenceReport;
  security: SecurityReport;
  tests: TestResults;
  rcaScore: number;
  patchValidation?: PatchValidation;
  status?: string;
  isUpload?: boolean;
}

export const AutonomousDecisionCenter: React.FC<AutonomousDecisionCenterProps> = ({
  decision,
  confidence,
  security,
  tests,
  rcaScore,
  patchValidation,
  status,
  isUpload
}) => {
  const currentDecision = decision?.decision || 'reject';
  const reason = decision?.reason || 'System is analyzing safety metrics.';
  const report = decision?.failure_report || '';

  // Extract variables safely
  const score = confidence?.score || 0;
  const passed = tests?.passed_count || 0;
  const total = tests?.total_count || 0;
  const testRate = total > 0 ? Math.round((passed / total) * 100) : 0;
  const secStatus = security?.status || 'passed';
  const pvApproval = patchValidation?.approval || 'SAFE_TO_TEST';
  const pvScore = patchValidation?.risk_score || 0;

  const getDecisionHeader = () => {
    switch (currentDecision) {
      case 'auto_approve':
        return (
          <div className="flex items-center gap-2 p-3 bg-emerald-950/50 border border-accentGreen text-accentGreenLight rounded-lg mb-4 glow-green">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
            <div>
              <p className="text-xs font-bold font-mono tracking-wider">AUTONOMOUS MERGE APPROVED</p>
              <p className="text-[10px] opacity-85 mt-0.5">Pipeline verified safe for production deployment</p>
            </div>
          </div>
        );
      case 'human_review':
        return (
          <div className="flex items-center gap-2 p-3 bg-yellow-950/50 border border-yellow-600 text-yellow-400 rounded-lg mb-4">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <div>
              <p className="text-xs font-bold font-mono tracking-wider">HUMAN REVIEW REQUIRED</p>
              <p className="text-[10px] opacity-85 mt-0.5">Autonomous confidence threshold not reached</p>
            </div>
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-2 p-3 bg-red-950/50 border border-accentRed text-red-400 rounded-lg mb-4">
            <XOctagon className="w-5 h-5 flex-shrink-0" />
            <div>
              <p className="text-xs font-bold font-mono tracking-wider">RESOLUTION FAILED / DEPLOY REJECTED</p>
              <p className="text-[10px] opacity-85 mt-0.5">Validation constraints violated or tests failed</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="glass-panel p-5 mb-6">
      <div className="flex items-center gap-2 mb-4 border-b border-borderDark pb-3">
        <Gavel className="w-5 h-5 text-purple-400" />
        <h2 className="text-sm font-semibold tracking-wider font-mono">AUTONOMOUS DECISION CENTER</h2>
      </div>

      {score > 0 || rcaScore > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left half: Decision and metrics */}
          <div className="lg:col-span-2 space-y-4">
            {getDecisionHeader()}

            <div className="p-3 bg-bgCard/60 border border-borderDark rounded-lg space-y-2.5 font-mono text-[10px]">
              <div>
                <p className="text-textMuted leading-none">GOVERNANCE EXPLANATION</p>
                <p className="text-gray-300 mt-1 leading-normal">{reason}</p>
              </div>

              <div className="border-t border-borderDark/60 pt-2.5 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-textMuted">RCA Consistency Score</span>
                  <span className={`font-semibold ${rcaScore >= 60 ? 'text-accentGreenLight' : 'text-accentRed'}`}>
                    {rcaScore}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-textMuted">Tests Pass Ratio</span>
                  <span className={`font-semibold ${testRate === 100 ? 'text-accentGreenLight' : 'text-yellow-400'}`}>
                    {testRate}% ({passed}/{total})
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-textMuted">Security Audit</span>
                  <span className={`font-semibold ${secStatus === 'passed' ? 'text-accentGreenLight' : 'text-accentRed'}`}>
                    {secStatus === 'passed' ? 'PASS' : 'FAIL'}
                  </span>
                </div>
                {patchValidation && (
                  <div className="flex justify-between items-center">
                    <span className="text-textMuted">Patch Validation</span>
                    <span className={`font-semibold ${pvApproval === 'SAFE_TO_TEST' ? 'text-accentGreenLight' : pvApproval === 'REVIEW_RECOMMENDED' ? 'text-yellow-400' : 'text-accentRed'}`}>
                      {pvApproval === 'SAFE_TO_TEST' ? 'SAFE' : pvApproval === 'REVIEW_RECOMMENDED' ? 'REVIEW' : 'BLOCKED'} ({pvScore}/100)
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right half: Engineering Failure Report if rejected, else PR summary */}
          <div className="lg:col-span-3 flex flex-col justify-between">
            {currentDecision === 'reject' && (tests?.ai_analysis || report) ? (
              <div className="flex-1 flex flex-col gap-3">
                {tests?.ai_analysis && (
                  <div className="flex-1 border border-indigo-900/50 bg-indigo-950/20 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-indigo-400 mb-3 border-b border-indigo-900/50 pb-2">
                      <ShieldAlert className="w-4 h-4" />
                      <h3 className="text-xs font-mono font-bold">🧠 AI Test Root Cause Analysis</h3>
                    </div>
                    <div className="space-y-3 text-[11px] font-mono">
                      <div>
                        <span className="text-textMuted block mb-0.5">Error:</span>
                        <span className="text-gray-200">{tests.ai_analysis.identified_error}</span>
                      </div>
                      <div>
                        <span className="text-textMuted block mb-0.5">Root Cause:</span>
                        <span className="text-red-300">{tests.ai_analysis.root_cause}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <div>
                          <span className="text-textMuted block mb-0.5">Severity:</span>
                          <span className={`font-bold ${tests.ai_analysis.severity === 'HIGH' ? 'text-accentRed' : tests.ai_analysis.severity === 'MEDIUM' ? 'text-yellow-400' : 'text-accentGreen'}`}>
                            {tests.ai_analysis.severity}
                          </span>
                        </div>
                      </div>
                      <div className="bg-black/40 p-2 rounded border border-borderDark mt-2">
                        <span className="text-emerald-400/80 block mb-0.5 text-[9px]">Recommended Fix:</span>
                        <span className="text-emerald-300">{tests.ai_analysis.recommended_fix}</span>
                      </div>
                    </div>
                  </div>
                )}

                {tests?.ai_patch_proposal && (
                  <div className="flex-1 border border-emerald-900/50 bg-emerald-950/20 rounded-lg p-4 mt-3">
                    <div className="flex items-center gap-2 text-emerald-400 mb-3 border-b border-emerald-900/50 pb-2">
                      <ShieldAlert className="w-4 h-4" />
                      <h3 className="text-xs font-mono font-bold">✨ AI Patch Proposal</h3>
                    </div>
                    <div className="space-y-3 text-[11px] font-mono">
                      <div>
                        <span className="text-textMuted block mb-0.5">Target File:</span>
                        <span className="text-emerald-300">{tests.ai_patch_proposal.file}</span>
                      </div>
                      <div className="bg-black/40 p-2 rounded border border-borderDark mt-2 overflow-x-auto">
                        <span className="text-textMuted block mb-2 text-[9px]">Proposed Diff:</span>
                        <pre className="text-[10px] leading-relaxed">
                          {tests.ai_patch_proposal.diff.map((line, idx) => {
                            let colorClass = "text-gray-300";
                            if (line.startsWith("+")) colorClass = "text-accentGreenLight bg-accentGreen/10";
                            else if (line.startsWith("-")) colorClass = "text-accentRed bg-accentRed/10";
                            return (
                              <div key={idx} className={`${colorClass} px-1 whitespace-pre-wrap`}>
                                {line}
                              </div>
                            );
                          })}
                        </pre>
                      </div>
                      <div>
                        <span className="text-textMuted block mb-0.5 mt-2">Explanation:</span>
                        <span className="text-gray-300 italic">{tests.ai_patch_proposal.explanation}</span>
                      </div>
                    </div>
                  </div>
                )}
                
                {tests?.ai_patch_validation && (
                  <div className={`flex-1 border rounded-lg p-4 mt-3 ${tests.ai_patch_validation.status === 'APPROVED' ? 'border-accentGreen/50 bg-accentGreen/10' : 'border-accentRed/50 bg-accentRed/10'}`}>
                    <div className={`flex items-center gap-2 mb-3 border-b pb-2 ${tests.ai_patch_validation.status === 'APPROVED' ? 'text-accentGreen' : 'text-accentRed border-accentRed/30'}`}>
                      {tests.ai_patch_validation.status === 'APPROVED' ? <CheckCircle2 className="w-4 h-4" /> : <XOctagon className="w-4 h-4" />}
                      <h3 className="text-xs font-mono font-bold">🛡️ AI Patch Validation Layer</h3>
                    </div>
                    <div className="space-y-3 text-[11px] font-mono">
                      <div className="flex justify-between items-center">
                        <span className="text-textMuted block">Status:</span>
                        <span className={`font-bold ${tests.ai_patch_validation.status === 'APPROVED' ? 'text-accentGreenLight' : 'text-accentRed'}`}>
                          {tests.ai_patch_validation.status}
                        </span>
                      </div>
                      {tests.ai_patch_validation.confidence !== undefined && (
                        <div>
                          <span className="text-textMuted block mb-1">Confidence Score:</span>
                          <div className="w-full bg-black/40 rounded-full h-1.5 border border-borderDark overflow-hidden">
                            <div 
                              className={`h-full ${tests.ai_patch_validation.status === 'APPROVED' ? 'bg-accentGreen' : 'bg-accentRed'}`} 
                              style={{ width: `${tests.ai_patch_validation.confidence * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                      {tests.ai_patch_validation.reason && (
                        <div className="bg-black/40 p-2 rounded border border-borderDark mt-2">
                          <span className="text-textMuted block mb-0.5 text-[9px]">Reason:</span>
                          <span className="text-gray-300">{tests.ai_patch_validation.reason}</span>
                        </div>
                      )}
                      {tests.ai_patch_validation.failed_checks && tests.ai_patch_validation.failed_checks.length > 0 && (
                        <div>
                          <span className="text-textMuted block mb-0.5 mt-2">Failed Checks:</span>
                          <ul className="list-disc pl-4 text-accentRed">
                            {tests.ai_patch_validation.failed_checks.map((check, idx) => (
                              <li key={idx}>{check}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {report && !tests?.ai_analysis && (
                  <div className="flex-1 flex flex-col">
                    <div className="flex items-center gap-1.5 text-xs font-mono font-semibold text-accentRed mb-2">
                      <ClipboardList className="w-4 h-4" />
                      <span>CRITICAL ENGINEERING FAILURE REPORT</span>
                    </div>
                    <pre className="flex-1 bg-black/60 border border-red-900/40 text-red-300 font-mono text-[10px] p-3 rounded-lg overflow-y-auto max-h-[160px] scrollbar-thin whitespace-pre-wrap leading-relaxed select-text">
                      {report}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex-1 flex flex-col justify-center items-center text-center p-6 border border-dashed border-borderDark rounded-lg">
                <CheckCircle2 className={`w-12 h-12 ${currentDecision === 'auto_approve' ? 'text-accentGreen' : 'text-yellow-400'} opacity-75 mb-2`} />
                <p className="text-xs font-mono font-semibold text-gray-200">
                  {currentDecision === 'auto_approve' ? 'Pipeline Deployable' : 'Draft Deployment Registered'}
                </p>
                <p className="text-[10px] text-textMuted font-mono mt-1 max-w-xs">
                  {currentDecision === 'auto_approve' 
                    ? 'All gates verified. Code commits pushed to git main.' 
                    : 'Awaiting engineer verification before final merging.'}
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-10 text-center text-textMuted/40">
          <Gavel className="w-10 h-10 mb-2 opacity-20" />
          {status === 'completed' && isUpload ? (
            <>
              <p className="text-xs font-mono">Static Analysis Complete</p>
              <p className="text-[9px] mt-0.5">Autonomous governance is skipped during static analysis mode.</p>
            </>
          ) : (
            <>
              <p className="text-xs font-mono">Awaiting safety governance review...</p>
              <p className="text-[9px] mt-0.5">Merge Governor verifies tests, security, and RCA consistency.</p>
            </>
          )}
        </div>
      )}
    </div>
  );
};
