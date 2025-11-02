import React from 'react';
import { MapPin, Layers } from 'lucide-react';
import { GeoChipList } from '../GeoChipList';

interface Constraint {
  type: string;
  name: string;
  impact: 'high' | 'moderate' | 'low';
}

interface Citation {
  title: string;
  url: string;
  domain: string;
  snippet?: string;
}

interface EvidenceSnapshotProps {
  data: {
    constraints: Constraint[];
    policy_count: number;
    citations?: Citation[];
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
  const citations = data?.citations || [];
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

      {citations.length > 0 && (
        <div className="mb-4">
          <div className="text-xs font-semibold text-[color:var(--ink)] mb-2">Citations</div>
          <div className="flex flex-wrap gap-2">
            {citations.map((c, i) => (
              <a
                key={i}
                href={c.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 px-2.5 py-1.5 rounded-full border border-[color:var(--edge)] bg-[color:var(--surface)] text-[color:var(--ink)] hover:border-[color:var(--accent)] hover:text-[color:var(--accent)] text-xs"
                title={c.snippet || c.title}
              >
                <span className="px-1 py-0.5 rounded bg-[color:var(--accent)]/10 text-[color:var(--accent)] font-mono text-[10px]">{c.domain}</span>
                <span className="truncate max-w-[200px]">{c.title}</span>
              </a>
            ))}
          </div>
        </div>
      )}

      <h4 className="text-sm font-semibold text-[color:var(--ink)] mb-3">Site Constraints</h4>
      <GeoChipList
        items={constraints.map((c) => ({
          label: `${c.type}: ${c.name}`,
          impact: c.impact,
        }))}
      />
    </div>
  );
}
