import React from 'react';
import { MessageSquare, TrendingUp, TrendingDown } from 'lucide-react';

interface Theme {
  theme: string;
  count: number;
  sentiment: 'positive' | 'negative' | 'neutral';
  policy_links?: string[];
}

interface ConsultationThemesProps {
  data: {
    themes: Theme[];
  };
}

const SENTIMENT_CONFIG = {
  positive: { icon: TrendingUp, color: '#22c55e', bg: '#f0fdf4' },
  negative: { icon: TrendingDown, color: '#ef4444', bg: '#fef2f2' },
  neutral: { icon: MessageSquare, color: '#6b7280', bg: '#f9fafb' },
};

export function ConsultationThemes({ data }: ConsultationThemesProps) {
  const themes = data?.themes || [];
  const totalCount = themes.reduce((sum, t) => sum + t.count, 0);

  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <MessageSquare className="w-5 h-5 text-[color:var(--accent)]" />
        <h3 className="text-lg font-semibold text-[color:var(--ink)]">Consultation Themes</h3>
        <span className="ml-auto text-sm text-[color:var(--muted)]">
          {totalCount} total responses
        </span>
      </div>

      {themes.length === 0 ? (
        <p className="text-[color:var(--muted)] text-sm">No themes identified</p>
      ) : (
        <div className="space-y-3">
          {themes.map((theme, idx) => {
          const config = SENTIMENT_CONFIG[theme.sentiment];
          const Icon = config.icon;
          const percentage = ((theme.count / totalCount) * 100).toFixed(1);

          return (
            <div
              key={idx}
              className="p-4 rounded-lg border"
              style={{ borderColor: config.color + '40', backgroundColor: config.bg }}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Icon className="w-5 h-5 flex-shrink-0" style={{ color: config.color }} />
                  <h4 className="font-semibold text-[color:var(--ink)]">{theme.theme}</h4>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-[color:var(--ink)]">{theme.count}</div>
                  <div className="text-xs text-[color:var(--muted)]">{percentage}%</div>
                </div>
              </div>

              {theme.policy_links && theme.policy_links.length > 0 && (
                <div className="flex items-center gap-2 flex-wrap mt-2">
                  <span className="text-xs text-[color:var(--muted)]">Related:</span>
                  {theme.policy_links.map((policy) => (
                    <span
                      key={policy}
                      className="px-2 py-0.5 rounded bg-white/60 text-[color:var(--accent)] text-xs font-mono font-semibold"
                    >
                      {policy}
                    </span>
                  ))}
                </div>
              )}

              <div className="mt-2 h-1.5 bg-white/60 rounded-full overflow-hidden">
                <div
                  className="h-full"
                  style={{ width: `${percentage}%`, backgroundColor: config.color }}
                />
              </div>
            </div>
          );
        })}
        </div>
      )}
    </div>
  );
}
