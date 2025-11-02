import React from 'react';
import { GitCompare } from 'lucide-react';

interface Scenario {
  name: string;
  housing?: number | string | null;
  density: string;
  score?: number | string | null;
}

interface ScenarioCompareProps {
  data: {
    scenarios: Scenario[];
  };
}

export function ScenarioCompare({ data }: ScenarioCompareProps) {
  const scenarios = Array.isArray(data?.scenarios) ? data!.scenarios : [];
  const num = (v: unknown): number | null => {
    if (typeof v === 'number' && isFinite(v)) return v;
    if (typeof v === 'string') {
      const n = Number(v);
      return Number.isFinite(n) ? n : null;
    }
    return null;
  };
  const fmtInt = (v: unknown): string => {
    const n = num(v);
    return (n === null || n === undefined) ? '—' : Math.round(n).toLocaleString();
  };
  const scoreOf = (s: Scenario): number => num(s?.score) ?? 0;
  const maxScore = Math.max(...(scenarios.map(scoreOf) as number[]), 0);

  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <GitCompare className="w-5 h-5 text-[color:var(--accent)]" />
        <h3 className="text-lg font-semibold text-[color:var(--ink)]">Scenario Comparison</h3>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {scenarios.map((scenario, idx) => {
          const isTop = scoreOf(scenario) === maxScore;

          return (
            <div
              key={idx}
              className={`p-4 rounded-lg border-2 ${
                isTop
                  ? 'border-[color:var(--accent)] bg-[color:var(--accent)]/5'
                  : 'border-[color:var(--edge)] bg-[color:var(--surface)]'
              }`}
            >
              <h4 className="font-semibold text-[color:var(--ink)] mb-3">
                {scenario.name}
                {isTop && (
                  <span className="ml-2 px-2 py-0.5 rounded bg-[color:var(--accent)] text-white text-xs">
                    Recommended
                  </span>
                )}
              </h4>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-[color:var(--muted)]">Housing Units</span>
                  <span className="text-sm font-semibold text-[color:var(--ink)]">{fmtInt(scenario.housing)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-[color:var(--muted)]">Density</span>
                  <span className="text-sm font-semibold text-[color:var(--ink)] capitalize">
                    {scenario.density}
                  </span>
                </div>
                <div className="pt-2 border-t border-[color:var(--edge)]">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-[color:var(--muted)]">Overall Score</span>
                    <span className="text-lg font-bold text-[color:var(--accent)]">{scoreOf(scenario)}/100</span>
                  </div>
                  <div className="mt-2 h-2 bg-[color:var(--edge)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[color:var(--accent)]"
                      style={{ width: `${scoreOf(scenario)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
