import React from 'react';
import { Edit3, FileText, Plus, ExternalLink } from 'lucide-react';

interface EvidenceLink {
  evidence_id: number;
  title: string;
  type: string;
  year?: number;
  strength: 'core' | 'supporting' | 'tangential';
}

interface PolicyEditorProps {
  data: {
    draft_text: string;
    suggestions: Array<{ type: string; text: string }>;
    evidence_links?: EvidenceLink[];
    policy_id?: number;
  };
}

const STRENGTH_CONFIG = {
  core: { color: 'bg-green-500', label: 'Core' },
  supporting: { color: 'bg-blue-500', label: 'Supporting' },
  tangential: { color: 'bg-gray-400', label: 'Background' },
};

export function PolicyEditor({ data }: PolicyEditorProps) {
  const evidenceLinks = data.evidence_links || [];
  
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

      {/* Evidence Base Section */}
      <div className="mb-4 border-t border-[color:var(--edge)] pt-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-[color:var(--accent)]" />
            <h4 className="text-sm font-semibold text-[color:var(--ink)]">Evidence Base</h4>
            <span className="text-xs text-[color:var(--muted)]">({evidenceLinks.length})</span>
          </div>
          <button
            className="flex items-center gap-1 text-xs text-[color:var(--accent)] hover:underline font-medium"
            onClick={() => {
              // TODO: Implement evidence linking dialog
              console.log('Open evidence linking dialog for policy', data.policy_id);
            }}
          >
            <Plus className="w-3 h-3" />
            Link Evidence
          </button>
        </div>
        
        {evidenceLinks.length > 0 ? (
          <div className="space-y-2">
            {evidenceLinks.map((link) => {
              const strengthCfg = STRENGTH_CONFIG[link.strength];
              return (
                <div
                  key={link.evidence_id}
                  className="p-3 rounded-lg border border-[color:var(--edge)] bg-[color:var(--surface)] hover:border-[color:var(--accent)] transition-colors cursor-pointer"
                  onClick={() => {
                    // TODO: Navigate to evidence detail
                    console.log('View evidence', link.evidence_id);
                  }}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-[color:var(--ink)] truncate">
                          {link.title}
                        </span>
                        <ExternalLink className="w-3 h-3 text-[color:var(--muted)] flex-shrink-0" />
                      </div>
                      <div className="flex items-center gap-2 text-xs text-[color:var(--muted)]">
                        <span className="font-semibold text-[color:var(--accent)]">{link.type}</span>
                        {link.year && <span>•</span>}
                        {link.year && <span>{link.year}</span>}
                      </div>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full ${strengthCfg.color} text-white text-[10px] font-bold whitespace-nowrap`}>
                      {strengthCfg.label}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-6 text-[color:var(--muted)] text-sm border border-dashed border-[color:var(--edge)] rounded-lg">
            <FileText className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p>No evidence linked to this policy yet</p>
            <p className="text-xs mt-1">Click "Link Evidence" to add supporting documents</p>
          </div>
        )}
      </div>

      {data.suggestions.length > 0 && (
        <div className="space-y-2 border-t border-[color:var(--edge)] pt-4">
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
