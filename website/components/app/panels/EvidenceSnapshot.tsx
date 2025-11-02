import React from 'react';
import { MapPin, Layers } from 'lucide-react';

interface Constraint {
  type: string;
  name: string;
  impact: 'high' | 'moderate' | 'low';
}

interface EvidenceSnapshotProps {
  data: {
    constraints: Constraint[];
    policy_count: number;
  };
}

const IMPACT_CONFIG = {
  high: { color: '#ef4444', label: 'High' },
  moderate: { color: '#f59e0b', label: 'Moderate' },
  low: { color: '#22c55e', label: 'Low' },
};

export function EvidenceSnapshot({ data }: EvidenceSnapshotProps) {
  const constraints = data?.constraints || [];
  const policyCount = typeof data?.policy_count === 'number' ? data.policy_count : 0;
  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <MapPin className="w-5 h-5 text-[color:var(--accent)]" />
        <h3 className="text-lg font-semibold text-[color:var(--ink)]">Evidence Snapshot</h3>
      </div>

      <div className="mb-4 p-3 rounded-lg bg-[color:var(--surface)] border border-[color:var(--edge)]">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-[color:var(--accent)]" />
          <span className="text-sm text-[color:var(--muted)]">Applicable policies:</span>
          <span className="text-sm font-bold text-[color:var(--accent)]">{policyCount}</span>
        </div>
      </div>

      <h4 className="text-sm font-semibold text-[color:var(--ink)] mb-3">Site Constraints</h4>
      <div className="space-y-2">
        {constraints.map((constraint, idx) => {
          const config = IMPACT_CONFIG[constraint.impact];

          return (
            <div
              key={idx}
              className="p-3 rounded-lg bg-[color:var(--surface)] border border-[color:var(--edge)] flex items-center justify-between"
            >
              <div>
                <div className="text-sm font-medium text-[color:var(--ink)]">
                  {constraint.type}
                </div>
                <div className="text-xs text-[color:var(--muted)]">{constraint.name}</div>
              </div>
              <span
                className="px-2 py-1 rounded text-xs font-medium"
                style={{ backgroundColor: config.color + '20', color: config.color }}
              >
                {config.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
