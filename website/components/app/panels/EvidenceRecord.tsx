import React from 'react';
import { FileText, Calendar, User, ExternalLink, GitBranch, Link as LinkIcon, Map, Download, RefreshCw, AlertTriangle } from 'lucide-react';

interface EvidenceVersion {
  id: number;
  version_number: number;
  cas_hash: string;
  source_url?: string;
  etag?: string;
  file_size?: number;
  mime_type?: string;
  fetched_at: string;
  license?: string;
  robots_allowed: boolean;
}

interface PolicyLink {
  policy_id: number;
  policy_title?: string;
  rationale?: string;
  strength: 'core' | 'supporting' | 'tangential';
}

interface EvidenceRecordProps {
  item: {
    id: number;
    title: string;
    type: string;
    topic_tags: string[];
    geographic_scope?: string;
    author?: string;
    publisher?: string;
    year?: number;
    source_type: string;
    status: string;
    key_findings?: string;
    notes?: string;
    reliability_flags: any;
  };
  versions: EvidenceVersion[];
  policy_links: PolicyLink[];
  layer_ids: number[];
  onLinkPolicy?: (policyId: number) => void;
  onRefresh?: () => void;
  onDownload?: (versionId: number) => void;
}

const STRENGTH_CONFIG = {
  core: { color: 'bg-green-500', label: 'Core Evidence' },
  supporting: { color: 'bg-blue-500', label: 'Supporting' },
  tangential: { color: 'bg-gray-400', label: 'Tangential' },
};

export function EvidenceRecord({
  item,
  versions,
  policy_links,
  layer_ids,
  onLinkPolicy,
  onRefresh,
  onDownload,
}: EvidenceRecordProps) {
  const latestVersion = versions[0];
  const isStale = item.year && new Date().getFullYear() - item.year > 5;

  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="w-5 h-5 text-[color:var(--accent)]" />
            <h3 className="text-xl font-bold text-[color:var(--ink)]">{item.title}</h3>
          </div>
          <div className="flex items-center gap-3 text-sm text-[color:var(--muted)]">
            <span className="font-semibold text-[color:var(--accent)]">{item.type}</span>
            {item.status && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                item.status === 'adopted' ? 'bg-green-100 text-green-700' :
                item.status === 'superseded' ? 'bg-orange-100 text-orange-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {item.status}
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-2 rounded-lg border border-[color:var(--edge)] bg-[color:var(--surface)] text-[color:var(--ink)] hover:border-[color:var(--accent)] transition-colors"
              title="Refresh from source"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Alerts */}
      {(isStale || item.reliability_flags.method_issues) && (
        <div className="mb-4 p-3 rounded-lg bg-orange-50 border border-orange-200 flex items-start gap-2">
          <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <div className="font-semibold text-orange-900 mb-1">Currency Alert</div>
            <ul className="text-orange-700 space-y-0.5 text-xs">
              {isStale && <li>• Evidence is over 5 years old ({item.year})</li>}
              {item.reliability_flags.method_issues && <li>• Methodology concerns noted</li>}
            </ul>
          </div>
        </div>
      )}

      {/* Metadata Grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {item.author && (
          <div>
            <div className="text-xs font-semibold text-[color:var(--muted)] mb-1">Author</div>
            <div className="flex items-center gap-2 text-sm text-[color:var(--ink)]">
              <User className="w-4 h-4" />
              {item.author}
            </div>
          </div>
        )}
        {item.publisher && (
          <div>
            <div className="text-xs font-semibold text-[color:var(--muted)] mb-1">Publisher</div>
            <div className="text-sm text-[color:var(--ink)]">{item.publisher}</div>
          </div>
        )}
        {item.year && (
          <div>
            <div className="text-xs font-semibold text-[color:var(--muted)] mb-1">Year</div>
            <div className="flex items-center gap-2 text-sm text-[color:var(--ink)]">
              <Calendar className="w-4 h-4" />
              {item.year}
            </div>
          </div>
        )}
        {item.geographic_scope && (
          <div>
            <div className="text-xs font-semibold text-[color:var(--muted)] mb-1">Geographic Scope</div>
            <div className="flex items-center gap-2 text-sm text-[color:var(--ink)]">
              <Map className="w-4 h-4" />
              {item.geographic_scope}
            </div>
          </div>
        )}
      </div>

      {/* Topics */}
      {item.topic_tags.length > 0 && (
        <div className="mb-6">
          <div className="text-xs font-semibold text-[color:var(--muted)] mb-2">Topics</div>
          <div className="flex flex-wrap gap-2">
            {item.topic_tags.map((tag) => (
              <span
                key={tag}
                className="px-2.5 py-1 rounded-full bg-[color:var(--accent)]/10 text-[color:var(--accent)] text-xs font-medium"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Key Findings */}
      {item.key_findings && (
        <div className="mb-6">
          <div className="text-xs font-semibold text-[color:var(--muted)] mb-2">Key Findings</div>
          <div className="p-4 rounded-lg bg-[color:var(--surface)] border border-[color:var(--edge)] text-sm text-[color:var(--ink)] leading-relaxed">
            {item.key_findings}
          </div>
        </div>
      )}

      {/* Notes */}
      {item.notes && (
        <div className="mb-6">
          <div className="text-xs font-semibold text-[color:var(--muted)] mb-2">Notes</div>
          <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-sm text-amber-900">
            {item.notes}
          </div>
        </div>
      )}

      {/* Version Timeline */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-[color:var(--accent)]" />
            <h4 className="text-sm font-semibold text-[color:var(--ink)]">Version History</h4>
            <span className="text-xs text-[color:var(--muted)]">({versions.length})</span>
          </div>
        </div>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {versions.map((v, idx) => (
            <div
              key={v.id}
              className={`p-3 rounded-lg border ${
                idx === 0
                  ? 'border-[color:var(--accent)] bg-[color:var(--accent)]/5'
                  : 'border-[color:var(--edge)] bg-[color:var(--surface)]'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-[color:var(--accent)]">v{v.version_number}</span>
                  {idx === 0 && (
                    <span className="px-1.5 py-0.5 rounded bg-[color:var(--accent)] text-white text-[10px] font-bold">
                      LATEST
                    </span>
                  )}
                  <span className="text-xs text-[color:var(--muted)]">
                    {new Date(v.fetched_at).toLocaleDateString()}
                  </span>
                </div>
                {onDownload && (
                  <button
                    onClick={() => onDownload(v.id)}
                    className="p-1.5 rounded hover:bg-[color:var(--panel)] transition-colors"
                    title="Download this version"
                  >
                    <Download className="w-3.5 h-3.5 text-[color:var(--muted)]" />
                  </button>
                )}
              </div>
              <div className="space-y-1 text-xs text-[color:var(--muted)]">
                {v.source_url && (
                  <div className="flex items-center gap-1.5">
                    <ExternalLink className="w-3 h-3" />
                    <a
                      href={v.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-[color:var(--accent)] truncate max-w-[400px]"
                    >
                      {v.source_url}
                    </a>
                  </div>
                )}
                <div className="flex items-center gap-3">
                  {v.file_size && <span>{(v.file_size / 1024).toFixed(0)} KB</span>}
                  {v.mime_type && <span>{v.mime_type}</span>}
                  {v.license && <span>License: {v.license}</span>}
                </div>
                <div className="font-mono text-[10px] text-[color:var(--muted)] truncate">
                  {v.cas_hash.substring(0, 16)}...
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Policy Links */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <LinkIcon className="w-4 h-4 text-[color:var(--accent)]" />
            <h4 className="text-sm font-semibold text-[color:var(--ink)]">Linked Policies</h4>
            <span className="text-xs text-[color:var(--muted)]">({policy_links.length})</span>
          </div>
          {onLinkPolicy && (
            <button
              onClick={() => onLinkPolicy(0)}
              className="text-xs text-[color:var(--accent)] hover:underline font-medium"
            >
              + Link Policy
            </button>
          )}
        </div>
        {policy_links.length > 0 ? (
          <div className="space-y-2">
            {policy_links.map((link) => {
              const strengthCfg = STRENGTH_CONFIG[link.strength];
              return (
                <div
                  key={link.policy_id}
                  className="p-3 rounded-lg border border-[color:var(--edge)] bg-[color:var(--surface)]"
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="font-medium text-sm text-[color:var(--ink)]">
                      {link.policy_title || `Policy #${link.policy_id}`}
                    </div>
                    <span className={`px-2 py-0.5 rounded-full ${strengthCfg.color} text-white text-[10px] font-bold`}>
                      {strengthCfg.label}
                    </span>
                  </div>
                  {link.rationale && (
                    <p className="text-xs text-[color:var(--muted)] mt-1">{link.rationale}</p>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-6 text-[color:var(--muted)] text-sm">
            No policy links yet
          </div>
        )}
      </div>

      {/* Spatial Layers */}
      {layer_ids.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Map className="w-4 h-4 text-[color:var(--accent)]" />
            <h4 className="text-sm font-semibold text-[color:var(--ink)]">Spatial Layers</h4>
            <span className="text-xs text-[color:var(--muted)]">({layer_ids.length})</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {layer_ids.map((layerId) => (
              <div
                key={layerId}
                className="px-3 py-1.5 rounded-lg border border-[color:var(--edge)] bg-[color:var(--surface)] text-xs text-[color:var(--ink)] font-medium"
              >
                Layer #{layerId}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
