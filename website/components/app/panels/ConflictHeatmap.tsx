import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface Conflict {
  policy_a: string;
  policy_b: string;
  severity: 'low' | 'moderate' | 'high';
  description: string;
}

interface ConflictHeatmapProps {
  data: {
    conflicts: Conflict[];
  };
}

const SEVERITY_CONFIG = {
  low: { color: '#f59e0b', label: 'Low' },
  moderate: { color: '#f97316', label: 'Moderate' },
  high: { color: '#ef4444', label: 'High' },
};

export function ConflictHeatmap({ data }: ConflictHeatmapProps) {
  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-[color:var(--accent)]" />
        <h3 className="text-lg font-semibold text-[color:var(--ink)]">Policy Conflicts</h3>
      </div>

      <div className="space-y-3">
        {data.conflicts.map((conflict, idx) => {
          const config = SEVERITY_CONFIG[conflict.severity];

          return (
            <div
              key={idx}
              className="p-4 rounded-lg border"
              style={{ borderColor: config.color + '40', backgroundColor: config.color + '10' }}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 rounded bg-[color:var(--surface)] text-[color:var(--accent)] text-xs font-mono font-semibold">
                    {conflict.policy_a}
                  </span>
                  <span className="text-[color:var(--muted)]">↔</span>
                  <span className="px-2 py-1 rounded bg-[color:var(--surface)] text-[color:var(--accent)] text-xs font-mono font-semibold">
                    {conflict.policy_b}
                  </span>
                </div>
                <span
                  className="px-2 py-1 rounded text-xs font-medium"
                  style={{ backgroundColor: config.color + '20', color: config.color }}
                >
                  {config.label}
                </span>
              </div>
              <p className="text-sm text-[color:var(--muted)]">{conflict.description}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
