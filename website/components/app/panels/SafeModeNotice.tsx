import React from 'react';
import { AlertTriangle, ShieldAlert, XCircle } from 'lucide-react';

interface SafeModeNoticeProps {
  data: {
    reason?: string;
    timestamp?: number;
    errorCount?: number;
    message?: string;
  };
}

export function SafeModeNotice({ data }: SafeModeNoticeProps) {
  const { reason, timestamp, errorCount = 0, message } = data;
  
  return (
    <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-400 rounded-xl p-6 shadow-lg">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center">
            <ShieldAlert className="w-6 h-6 text-amber-600" />
          </div>
        </div>
        
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-lg font-bold text-amber-900">
              Safe Mode Activated
            </h3>
            <span className="px-2 py-1 bg-amber-200 text-amber-800 text-xs font-mono rounded">
              DEGRADED
            </span>
          </div>
          
          <p className="text-sm text-amber-800 mb-4 leading-relaxed">
            {message || 'The system encountered issues while generating the interactive interface and has switched to simplified output mode for stability.'}
          </p>
          
          <div className="bg-white/60 rounded-lg p-4 mb-4">
            <div className="flex items-start gap-2 text-xs text-amber-700">
              <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium mb-1">Technical Details:</p>
                {reason && (
                  <p className="mb-1">
                    <span className="font-mono">{reason}</span>
                  </p>
                )}
                {errorCount > 0 && (
                  <p>
                    Error count: <span className="font-mono font-semibold">{errorCount}</span>
                  </p>
                )}
                {timestamp && (
                  <p className="text-amber-600 mt-1">
                    {new Date(timestamp).toLocaleTimeString()}
                  </p>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2 text-sm text-amber-700">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Results below may be simplified</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-amber-700">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Reasoning text continues normally</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-amber-700">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Start new run to reset</span>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-amber-300">
            <details className="text-xs text-amber-700">
              <summary className="cursor-pointer font-medium hover:text-amber-900 select-none">
                What does this mean?
              </summary>
              <div className="mt-2 pl-4 space-y-2 text-amber-600">
                <p>
                  <strong>Safe Mode</strong> is automatically activated when the AI assistant generates
                  interface elements that don't pass validation checks. This protects the system from
                  unstable or malformed outputs.
                </p>
                <p>
                  Your query may have been ambiguous, or the system may have attempted to create
                  interface elements it doesn't have permission to generate. The reasoning and any
                  successfully generated panels are still available below.
                </p>
                <p>
                  <strong>To recover:</strong> Start a new analysis with a different query or more specific parameters.
                </p>
              </div>
            </details>
          </div>
        </div>
      </div>
    </div>
  );
}
