import React from 'react';
import { Scale } from 'lucide-react';

interface PlanningBalanceProps {
  data: {
    benefits: Array<{ item: string; weight: string }>;
    harms: Array<{ item: string; weight: string }>;
    overall: string;
  };
}

const WEIGHT_COLORS: Record<string, string> = {
  substantial: '#22c55e',
  moderate: '#329c85',
  limited: '#f59e0b',
  neutral: '#6b7280',
};

export function PlanningBalance({ data }: PlanningBalanceProps) {
  const benefits = data?.benefits || [];
  const harms = data?.harms || [];
  const overall = data?.overall || 'No overall assessment available yet.';
  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <Scale className="w-5 h-5 text-[color:var(--accent)]" />
        <h3 className="text-lg font-semibold text-[color:var(--ink)]">Planning Balance</h3>
      </div>

      <div className="grid md:grid-cols-2 gap-4 mb-6">
        {/* Benefits */}
        <div>
          <h4 className="text-sm font-semibold text-[color:var(--ink)] mb-3 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            Benefits
          </h4>
          <div className="space-y-2">
            {benefits.map((benefit, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-green-50 border border-green-200"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[color:var(--ink)]">{benefit.item}</span>
                  <span
                    className="px-2 py-0.5 rounded text-xs font-medium"
                    style={{
                      backgroundColor: WEIGHT_COLORS[benefit.weight] + '20',
                      color: WEIGHT_COLORS[benefit.weight],
                    }}
                  >
                    {benefit.weight}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Harms */}
        <div>
          <h4 className="text-sm font-semibold text-[color:var(--ink)] mb-3 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            Harms
          </h4>
          <div className="space-y-2">
            {harms.map((harm, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-red-50 border border-red-200"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[color:var(--ink)]">{harm.item}</span>
                  <span
                    className="px-2 py-0.5 rounded text-xs font-medium"
                    style={{
                      backgroundColor: WEIGHT_COLORS[harm.weight] + '20',
                      color: WEIGHT_COLORS[harm.weight],
                    }}
                  >
                    {harm.weight}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Overall Assessment */}
      <div className="p-4 rounded-lg bg-[color:var(--surface)] border-2 border-[color:var(--accent)]">
        <p className="text-sm font-semibold text-[color:var(--ink)] mb-1">Overall Assessment</p>
        <p className="text-sm text-[color:var(--muted)]">{overall}</p>
      </div>
    </div>
  );
}
