import React from 'react';
import { AlertTriangle, Clock, TrendingDown, FileQuestion } from 'lucide-react';

interface GapItem {
  policy_id: number;
  title: string;
  latest_year?: number;
  link_count?: number;
}

interface EvidenceGapsProps {
  data: {
    no_evidence: GapItem[];
    stale_evidence: GapItem[];
    weak_links_only: GapItem[];
  };
  onSelectPolicy?: (policyId: number) => void;
  onRequestUpdate?: (policyId: number) => void;
}

export function EvidenceGaps({ data, onSelectPolicy, onRequestUpdate }: EvidenceGapsProps) {
  const totalGaps = 
    (data?.no_evidence?.length || 0) +
    (data?.stale_evidence?.length || 0) +
    (data?.weak_links_only?.length || 0);

  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-orange-500" />
        <h3 className="text-lg font-semibold text-[color:var(--ink)]">Evidence Gaps & Alerts</h3>
        <span className="text-sm text-[color:var(--muted)]">({totalGaps} issues)</span>
      </div>

      {totalGaps === 0 ? (
        <div className="text-center py-12 text-[color:var(--muted)]">
          <AlertTriangle className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm font-medium">No evidence gaps detected</p>
          <p className="text-xs mt-1">All policies have adequate supporting evidence</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* No Evidence */}
          {data?.no_evidence && data.no_evidence.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <FileQuestion className="w-4 h-4 text-red-500" />
                <h4 className="text-sm font-semibold text-[color:var(--ink)]">No Evidence</h4>
                <span className="px-2 py-0.5 rounded-full bg-red-100 text-red-700 text-xs font-bold">
                  {data.no_evidence.length}
                </span>
              </div>
              <div className="space-y-2">
                {data.no_evidence.map((item) => (
                  <div
                    key={item.policy_id}
                    className="p-3 rounded-lg border border-red-200 bg-red-50 hover:border-red-400 transition-colors cursor-pointer"
                    onClick={() => onSelectPolicy?.(item.policy_id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-sm text-red-900">{item.title}</div>
                        <div className="text-xs text-red-700 mt-0.5">Policy #{item.policy_id}</div>
                      </div>
                      {onRequestUpdate && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onRequestUpdate(item.policy_id);
                          }}
                          className="px-3 py-1 rounded text-xs font-medium bg-red-600 text-white hover:bg-red-700 transition-colors"
                        >
                          Add Evidence
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Stale Evidence */}
          {data?.stale_evidence && data.stale_evidence.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Clock className="w-4 h-4 text-orange-500" />
                <h4 className="text-sm font-semibold text-[color:var(--ink)]">Stale Evidence (&gt;5 years)</h4>
                <span className="px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 text-xs font-bold">
                  {data.stale_evidence.length}
                </span>
              </div>
              <div className="space-y-2">
                {data.stale_evidence.map((item) => (
                  <div
                    key={item.policy_id}
                    className="p-3 rounded-lg border border-orange-200 bg-orange-50 hover:border-orange-400 transition-colors cursor-pointer"
                    onClick={() => onSelectPolicy?.(item.policy_id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-sm text-orange-900">{item.title}</div>
                        <div className="text-xs text-orange-700 mt-0.5">
                          Latest evidence: {item.latest_year || 'Unknown'}
                        </div>
                      </div>
                      {onRequestUpdate && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onRequestUpdate(item.policy_id);
                          }}
                          className="px-3 py-1 rounded text-xs font-medium bg-orange-600 text-white hover:bg-orange-700 transition-colors"
                        >
                          Update
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Weak Links Only */}
          {data?.weak_links_only && data.weak_links_only.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <TrendingDown className="w-4 h-4 text-amber-500" />
                <h4 className="text-sm font-semibold text-[color:var(--ink)]">Weak Evidence Links</h4>
                <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 text-xs font-bold">
                  {data.weak_links_only.length}
                </span>
              </div>
              <div className="space-y-2">
                {data.weak_links_only.map((item) => (
                  <div
                    key={item.policy_id}
                    className="p-3 rounded-lg border border-amber-200 bg-amber-50 hover:border-amber-400 transition-colors cursor-pointer"
                    onClick={() => onSelectPolicy?.(item.policy_id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-sm text-amber-900">{item.title}</div>
                        <div className="text-xs text-amber-700 mt-0.5">
                          {item.link_count || 0} tangential link(s) only
                        </div>
                      </div>
                      {onRequestUpdate && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onRequestUpdate(item.policy_id);
                          }}
                          className="px-3 py-1 rounded text-xs font-medium bg-amber-600 text-white hover:bg-amber-700 transition-colors"
                        >
                          Strengthen
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Summary Footer */}
      {totalGaps > 0 && (
        <div className="mt-6 pt-4 border-t border-[color:var(--edge)]">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[color:var(--muted)]">
              Review and address these gaps to strengthen the evidence base
            </span>
            <span className="font-semibold text-[color:var(--ink)]">
              {totalGaps} total issue{totalGaps !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
