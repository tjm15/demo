import React, { useState } from 'react';
import { Search, Filter, Database, Globe, HardDrive, Calendar, Tag, AlertCircle, Link as LinkIcon, MapPin, TrendingUp } from 'lucide-react';

interface EvidenceItem {
  id: number;
  title: string;
  type: string;
  topic_tags: string[];
  geographic_scope?: string;
  author?: string;
  publisher?: string;
  year?: number;
  source_type: 'upload' | 'cached_url' | 'live_url';
  status: 'draft' | 'adopted' | 'superseded';
  spatial_layer_ref?: number;
  key_findings?: string;
  version_count: number;
  reliability_flags: {
    stale?: boolean;
    method_issues?: boolean;
  };
}

interface EvidenceBrowserProps {
  items?: EvidenceItem[];
  onSelectItem?: (item: EvidenceItem) => void;
  onSearch?: (query: string, filters: any) => void;
}

const SOURCE_BADGES = {
  upload: { icon: HardDrive, label: 'LOCAL', color: 'bg-blue-500' },
  cached_url: { icon: Database, label: 'CACHED', color: 'bg-purple-500' },
  live_url: { icon: Globe, label: 'LIVE', color: 'bg-green-500' },
};

const STATUS_COLORS = {
  draft: 'text-gray-500',
  adopted: 'text-green-600',
  superseded: 'text-orange-500',
};

export function EvidenceBrowser({ items = [], onSelectItem, onSearch }: EvidenceBrowserProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [scope, setScope] = useState<'db' | 'cache' | 'live'>('db');
  const [showFilters, setShowFilters] = useState(false);

  const allTopics = Array.from(new Set(items.flatMap(i => i.topic_tags || [])));
  const allTypes = Array.from(new Set(items.map(i => i.type)));

  const handleSearch = () => {
    if (onSearch) {
      onSearch(searchQuery, {
        topics: selectedTopics,
        types: selectedTypes,
        scope,
      });
    }
  };

  const filteredItems = items.filter(item => {
    if (searchQuery && !item.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !item.key_findings?.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    if (selectedTopics.length > 0 && !selectedTopics.some(t => item.topic_tags.includes(t))) {
      return false;
    }
    if (selectedTypes.length > 0 && !selectedTypes.includes(item.type)) {
      return false;
    }
    return true;
  });

  const isStale = (year?: number) => {
    if (!year) return false;
    return new Date().getFullYear() - year > 5;
  };

  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-[color:var(--accent)]" />
          <h3 className="text-lg font-semibold text-[color:var(--ink)]">Evidence Browser</h3>
          <span className="text-sm text-[color:var(--muted)]">({filteredItems.length} items)</span>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[color:var(--edge)] bg-[color:var(--surface)] text-[color:var(--ink)] hover:border-[color:var(--accent)] transition-colors text-sm"
        >
          <Filter className="w-4 h-4" />
          Filters
        </button>
      </div>

      {/* Search Bar */}
      <div className="mb-4 flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[color:var(--muted)]" />
          <input
            type="text"
            placeholder="Search evidence by title, type, or findings..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-[color:var(--edge)] bg-[color:var(--surface)] text-[color:var(--ink)] placeholder:text-[color:var(--muted)] focus:outline-none focus:border-[color:var(--accent)]"
          />
        </div>
        <button
          onClick={handleSearch}
          className="px-4 py-2 rounded-lg bg-[color:var(--accent)] text-white hover:opacity-90 transition-opacity font-medium"
        >
          Search
        </button>
      </div>

      {/* Scope Toggle */}
      <div className="mb-4 flex items-center gap-2">
        <span className="text-sm text-[color:var(--muted)]">Scope:</span>
        <div className="flex gap-1 p-1 rounded-lg bg-[color:var(--surface)] border border-[color:var(--edge)]">
          {(['db', 'cache', 'live'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setScope(s)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                scope === s
                  ? 'bg-[color:var(--accent)] text-white'
                  : 'text-[color:var(--muted)] hover:text-[color:var(--ink)]'
              }`}
            >
              {s === 'db' ? 'DB' : s === 'cache' ? 'DB+Cache' : 'DB+Cache+Live'}
            </button>
          ))}
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="mb-4 p-4 rounded-lg bg-[color:var(--surface)] border border-[color:var(--edge)] space-y-3">
          {/* Topics */}
          <div>
            <div className="text-xs font-semibold text-[color:var(--ink)] mb-2">Topics</div>
            <div className="flex flex-wrap gap-2">
              {allTopics.map((topic) => (
                <button
                  key={topic}
                  onClick={() =>
                    setSelectedTopics((prev) =>
                      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
                    )
                  }
                  className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                    selectedTopics.includes(topic)
                      ? 'bg-[color:var(--accent)] text-white'
                      : 'bg-[color:var(--panel)] border border-[color:var(--edge)] text-[color:var(--ink)] hover:border-[color:var(--accent)]'
                  }`}
                >
                  {topic}
                </button>
              ))}
            </div>
          </div>

          {/* Types */}
          <div>
            <div className="text-xs font-semibold text-[color:var(--ink)] mb-2">Evidence Type</div>
            <div className="flex flex-wrap gap-2">
              {allTypes.map((type) => (
                <button
                  key={type}
                  onClick={() =>
                    setSelectedTypes((prev) =>
                      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
                    )
                  }
                  className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                    selectedTypes.includes(type)
                      ? 'bg-[color:var(--accent)] text-white'
                      : 'bg-[color:var(--panel)] border border-[color:var(--edge)] text-[color:var(--ink)] hover:border-[color:var(--accent)]'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Evidence List */}
      <div className="space-y-3 max-h-[600px] overflow-y-auto">
        {filteredItems.map((item) => {
          const SourceBadge = SOURCE_BADGES[item.source_type];
          const stale = isStale(item.year);

          return (
            <div
              key={item.id}
              onClick={() => onSelectItem?.(item)}
              className="p-4 rounded-lg border border-[color:var(--edge)] bg-[color:var(--surface)] hover:border-[color:var(--accent)] transition-colors cursor-pointer"
            >
              {/* Header Row */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold text-[color:var(--ink)]">{item.title}</h4>
                    <span className={`text-xs font-medium ${STATUS_COLORS[item.status]}`}>
                      {item.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-[color:var(--muted)]">
                    <span className="font-medium">{item.type}</span>
                    {item.author && <span>• {item.author}</span>}
                    {item.year && (
                      <span className="flex items-center gap-1">
                        • <Calendar className="w-3 h-3" /> {item.year}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div
                    className={`flex items-center gap-1 px-2 py-1 rounded-full ${SourceBadge.color} text-white text-[10px] font-bold`}
                  >
                    <SourceBadge.icon className="w-3 h-3" />
                    {SourceBadge.label}
                  </div>
                  {item.spatial_layer_ref && (
                    <div title="Has spatial layer">
                      <MapPin className="w-4 h-4 text-[color:var(--accent)]" />
                    </div>
                  )}
                </div>
              </div>

              {/* Topics */}
              {item.topic_tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {item.topic_tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[color:var(--accent)]/10 text-[color:var(--accent)] text-[10px] font-medium"
                    >
                      <Tag className="w-2.5 h-2.5" />
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Key Findings */}
              {item.key_findings && (
                <p className="text-xs text-[color:var(--muted)] line-clamp-2 mb-2">{item.key_findings}</p>
              )}

              {/* Alerts */}
              {(stale || item.reliability_flags.stale || item.reliability_flags.method_issues) && (
                <div className="flex items-center gap-2 pt-2 border-t border-[color:var(--edge)]">
                  <AlertCircle className="w-3.5 h-3.5 text-orange-500" />
                  <span className="text-xs text-orange-600 font-medium">
                    {stale && 'Evidence is >5 years old'}
                    {item.reliability_flags.method_issues && ' • Method concerns'}
                  </span>
                </div>
              )}

              {/* Footer */}
              <div className="flex items-center justify-between pt-2 border-t border-[color:var(--edge)] mt-2">
                <div className="flex items-center gap-3 text-xs text-[color:var(--muted)]">
                  <span>{item.version_count} version{item.version_count !== 1 ? 's' : ''}</span>
                  {item.geographic_scope && (
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {item.geographic_scope}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {filteredItems.length === 0 && (
          <div className="text-center py-12 text-[color:var(--muted)]">
            <Database className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No evidence items found</p>
            <p className="text-xs mt-1">Try adjusting your search or filters</p>
          </div>
        )}
      </div>
    </div>
  );
}
