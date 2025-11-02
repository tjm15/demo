import React from 'react';
import { Eye, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface ComplianceItem {
  criterion: string;
  status: 'compliant' | 'partial' | 'non-compliant';
}

interface VisualComplianceProps {
  data: {
    compliance: ComplianceItem[];
  };
}

const STATUS_CONFIG = {
  compliant: { icon: CheckCircle, color: '#22c55e', label: 'Compliant' },
  partial: { icon: AlertCircle, color: '#f59e0b', label: 'Partial' },
  'non-compliant': { icon: XCircle, color: '#ef4444', label: 'Non-Compliant' },
};

export function VisualCompliance({ data }: VisualComplianceProps) {
  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <Eye className="w-5 h-5 text-[color:var(--accent)]" />
        <h3 className="text-lg font-semibold text-[color:var(--ink)]">Visual Compliance</h3>
      </div>

      <div className="space-y-3">
        {data.compliance.map((item, idx) => {
          const config = STATUS_CONFIG[item.status];
          const Icon = config.icon;

          return (
            <div
              key={idx}
              className="flex items-center justify-between p-3 rounded-lg bg-[color:var(--surface)] border border-[color:var(--edge)]"
            >
              <span className="text-sm font-medium text-[color:var(--ink)]">{item.criterion}</span>
              <div className="flex items-center gap-2">
                <span
                  className="px-2 py-1 rounded text-xs font-medium flex items-center gap-1"
                  style={{ backgroundColor: config.color + '20', color: config.color }}
                >
                  <Icon className="w-3 h-3" />
                  {config.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
