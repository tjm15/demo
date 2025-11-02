import React from 'react';

export interface ChipItem {
  label: string;
  impact?: 'high' | 'moderate' | 'low' | 'unknown';
}

const COLORS: Record<string, string> = {
  high: '#ef4444',
  moderate: '#f59e0b',
  low: '#22c55e',
  unknown: '#64748b',
};

export function GeoChipList({ items }: { items: ChipItem[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((it, i) => {
        const color = COLORS[it.impact || 'unknown'];
        return (
          <span
            key={i}
            className="inline-flex items-center gap-2 px-2.5 py-1.5 rounded-full border text-xs"
            style={{ borderColor: 'var(--edge)', backgroundColor: 'var(--surface)', color: 'var(--ink)' }}
            title={`${it.label}${it.impact ? ` • ${it.impact}` : ''}`}
          >
            {it.impact && (
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: color }}
              />
            )}
            <span className="truncate max-w-[200px]">{it.label}</span>
          </span>
        );
      })}
    </div>
  );
}
