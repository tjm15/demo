import React from 'react';
import { FileText, ExternalLink } from 'lucide-react';

interface Policy {
  id: string;
  title: string;
  relevance: number;
  text: string;
  source: string;
}

interface ApplicablePoliciesProps {
  data: {
    policies: Policy[];
  };
}

export function ApplicablePolicies({ data }: ApplicablePoliciesProps) {
  const policies = data?.policies || [];
  
  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-5 h-5 text-[color:var(--accent)]" />
        <h3 className="text-lg font-semibold text-[color:var(--ink)]">Applicable Policies</h3>
        <span className="ml-auto text-sm text-[color:var(--muted)]">{policies.length} found</span>
      </div>

      {policies.length === 0 ? (
        <p className="text-[color:var(--muted)] text-sm">No policies found</p>
      ) : (
        <div className="space-y-3">
          {policies.map((policy) => (
          <div
            key={policy.id}
            className="p-4 rounded-lg bg-[color:var(--surface)] border border-[color:var(--edge)] hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 rounded bg-[color:var(--accent)]/10 text-[color:var(--accent)] text-xs font-mono font-semibold">
                  {policy.id}
                </span>
                <h4 className="font-semibold text-[color:var(--ink)]">{policy.title}</h4>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-16 h-2 bg-[color:var(--edge)] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[color:var(--accent)]"
                    style={{ width: `${policy.relevance * 100}%` }}
                  />
                </div>
                <span className="text-xs text-[color:var(--muted)] ml-1">
                  {Math.round(policy.relevance * 100)}%
                </span>
              </div>
            </div>
            <p className="text-sm text-[color:var(--muted)] leading-relaxed">{policy.text}</p>
            <div className="flex items-center justify-between mt-3">
              <span className="text-xs text-[color:var(--muted)]">{policy.source}</span>
              <button className="text-xs text-[color:var(--accent)] hover:underline flex items-center gap-1">
                View full text
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>
          </div>
        ))}
        </div>
      )}
    </div>
  );
}
