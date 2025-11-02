import React from 'react';
import { BookOpen } from 'lucide-react';

interface Precedent {
  case_ref: string;
  decision: string;
  similarity: number;
  key_point: string;
  date?: string;
}

interface PrecedentsProps {
  data: {
    precedents: Precedent[];
  };
}

export function Precedents({ data }: PrecedentsProps) {
  const precedents = data?.precedents || [];
  
  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <BookOpen className="w-5 h-5 text-[color:var(--accent)]" />
        <h3 className="text-lg font-semibold text-[color:var(--ink)]">Relevant Precedents</h3>
        <span className="ml-auto text-sm text-[color:var(--muted)]">{precedents.length} found</span>
      </div>

      {precedents.length === 0 ? (
        <p className="text-[color:var(--muted)] text-sm">No precedents found</p>
      ) : (
        <div className="space-y-3">
          {precedents.map((precedent, idx) => (
          <div
            key={idx}
            className="p-4 rounded-lg bg-[color:var(--surface)] border border-[color:var(--edge)]"
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <span className="text-sm font-mono font-semibold text-[color:var(--accent)]">
                  {precedent.case_ref}
                </span>
                {precedent.date && (
                  <span className="text-xs text-[color:var(--muted)] ml-2">{precedent.date}</span>
                )}
              </div>
              <span
                className={`px-2 py-1 rounded text-xs font-medium ${
                  precedent.decision === 'Allowed'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-red-100 text-red-700'
                }`}
              >
                {precedent.decision}
              </span>
            </div>
            <p className="text-sm text-[color:var(--muted)] leading-relaxed mb-2">
              {precedent.key_point}
            </p>
            <div className="flex items-center gap-2">
              <span className="text-xs text-[color:var(--muted)]">Similarity:</span>
              <div className="flex-1 max-w-[100px] h-1.5 bg-[color:var(--edge)] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[color:var(--accent)]"
                  style={{ width: `${precedent.similarity * 100}%` }}
                />
              </div>
              <span className="text-xs text-[color:var(--muted)]">
                {Math.round(precedent.similarity * 100)}%
              </span>
            </div>
          </div>
        ))}
        </div>
      )}
    </div>
  );
}
