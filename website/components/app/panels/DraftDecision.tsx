import React from 'react';
import { Gavel, FileCheck } from 'lucide-react';

interface DraftDecisionProps {
  data: {
    recommendation: string;
    reasons: string[];
    conditions: string[];
  };
}

export function DraftDecision({ data }: DraftDecisionProps) {
  const recommendation = data?.recommendation || 'Pending';
  const reasons = data?.reasons || [];
  const conditions = data?.conditions || [];
  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <Gavel className="w-5 h-5 text-[color:var(--accent)]" />
        <h3 className="text-lg font-semibold text-[color:var(--ink)]">Draft Decision</h3>
      </div>

      {/* Recommendation Badge */}
      <div className="mb-6">
        <div
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg font-semibold ${
            recommendation === 'Approval'
              ? 'bg-green-100 text-green-700'
              : 'bg-red-100 text-red-700'
          }`}
        >
          <FileCheck className="w-5 h-5" />
          Recommendation: {recommendation}
        </div>
      </div>

      {/* Reasons */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-[color:var(--ink)] mb-3">Reasons</h4>
        <ol className="space-y-2 list-decimal list-inside">
          {reasons.map((reason, idx) => (
            <li key={idx} className="text-sm text-[color:var(--muted)] leading-relaxed">
              {reason}
            </li>
          ))}
        </ol>
      </div>

      {/* Conditions */}
      {conditions.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-[color:var(--ink)] mb-3">Conditions</h4>
          <ol className="space-y-2 list-decimal list-inside">
            {conditions.map((condition, idx) => (
              <li key={idx} className="text-sm text-[color:var(--muted)] leading-relaxed">
                {condition}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
