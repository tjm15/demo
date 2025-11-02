import React from 'react';
import { Edit3 } from 'lucide-react';

interface PolicyEditorProps {
  data: {
    draft_text: string;
    suggestions: Array<{ type: string; text: string }>;
  };
}

export function PolicyEditor({ data }: PolicyEditorProps) {
  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <Edit3 className="w-5 h-5 text-[color:var(--accent)]" />
        <h3 className="text-lg font-semibold text-[color:var(--ink)]">Policy Editor</h3>
      </div>

      <textarea
        className="w-full p-4 rounded-lg border border-[color:var(--edge)] focus:outline-none focus:ring-2 focus:ring-[color:var(--accent)] font-mono text-sm resize-none mb-4"
        rows={10}
        defaultValue={data.draft_text}
      />

      {data.suggestions.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-[color:var(--ink)]">Suggestions</h4>
          {data.suggestions.map((suggestion, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg bg-blue-50 border border-blue-200"
            >
              <span className="text-xs font-semibold text-blue-700 uppercase">
                {suggestion.type}
              </span>
              <p className="text-sm text-[color:var(--muted)] mt-1">{suggestion.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
