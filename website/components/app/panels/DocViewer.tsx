import React from 'react';
import { ExternalLink, BookOpen } from 'lucide-react';

interface Paragraph {
  text: string;
  page?: number;
  ref?: string;
}

interface DocViewerProps {
  data: {
    title?: string;
    source_url?: string;
    domain?: string;
    paragraphs: Paragraph[];
    highlight?: string;
  };
}

export function DocViewer({ data }: DocViewerProps) {
  const title = data?.title || 'Document';
  const sourceUrl = data?.source_url;
  const highlight = (data?.highlight || '').toLowerCase();

  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <BookOpen className="w-5 h-5 text-[color:var(--accent)]" />
        <h3 className="text-lg font-semibold text-[color:var(--ink)]">{title}</h3>
        {sourceUrl && (
          <a
            href={sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="ml-auto inline-flex items-center gap-1 text-xs text-[color:var(--accent)] hover:underline"
          >
            Open source <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>

      <div className="space-y-3">
        {(data?.paragraphs || []).map((p, idx) => {
          const text = p.text || '';
          const showHl = highlight && text.toLowerCase().includes(highlight);
          return (
            <div key={idx} className={`p-3 rounded-lg border ${showHl ? 'border-[color:var(--accent)] bg-[color:var(--accent)]/5' : 'border-[color:var(--edge)] bg-[color:var(--surface)]'}`}>
              <div className="text-sm text-[color:var(--ink)] leading-relaxed">
                {text}
              </div>
              <div className="mt-1 text-[10px] text-[color:var(--muted)]">
                {p.ref ? <span className="mr-2">{p.ref}</span> : null}
                {typeof p.page === 'number' ? <span>p.{p.page}</span> : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
