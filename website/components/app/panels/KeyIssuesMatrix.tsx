import React from 'react';
import { AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react';

interface Issue {
  category: string;
  status: 'concern' | 'acceptable' | 'positive';
  description: string;
  policies: string[];
}

interface KeyIssuesMatrixProps {
  data: {
    issues: Issue[];
  };
}

const STATUS_CONFIG = {
  concern: { icon: AlertCircle, color: '#ef4444', bg: '#fef2f2', label: 'Concern' },
  acceptable: { icon: CheckCircle, color: '#329c85', bg: '#f0fdf4', label: 'Acceptable' },
  positive: { icon: CheckCircle, color: '#22c55e', bg: '#f0fdf4', label: 'Positive' },
};

export function KeyIssuesMatrix({ data }: KeyIssuesMatrixProps) {
  const issues = data?.issues || [];
  
  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-[color:var(--ink)]">Key Issues Matrix</h3>
        <span className="text-sm text-[color:var(--muted)]">{issues.length} issues</span>
      </div>

      {issues.length === 0 ? (
        <p className="text-[color:var(--muted)] text-sm">No issues identified</p>
      ) : (
        <div className="space-y-3">
          {issues.map((issue, idx) => {
          const config = STATUS_CONFIG[issue.status];
          const Icon = config.icon;

          return (
            <div
              key={idx}
              className="p-4 rounded-lg border"
              style={{ borderColor: config.color + '40', backgroundColor: config.bg }}
            >
              <div className="flex items-start gap-3">
                <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: config.color }} />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-[color:var(--ink)]">{issue.category}</h4>
                    <span
                      className="px-2 py-1 rounded text-xs font-medium"
                      style={{ backgroundColor: config.color + '20', color: config.color }}
                    >
                      {config.label}
                    </span>
                  </div>
                  <p className="text-sm text-[color:var(--muted)] mb-2">{issue.description}</p>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs text-[color:var(--muted)]">Related policies:</span>
                    {issue.policies.map((policy) => (
                      <span
                        key={policy}
                        className="px-2 py-0.5 rounded bg-[color:var(--surface)] text-[color:var(--accent)] text-xs font-mono font-semibold"
                      >
                        {policy}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
        </div>
      )}
    </div>
  );
}
