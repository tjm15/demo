import React, { useCallback } from 'react';
import { EvidenceBrowser } from './EvidenceBrowser';
import type { Intent } from 'contracts/schemas';
import { useReasoningStream } from '../../../hooks/useReasoningStream';

type EvidenceItem = {
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
  reliability_flags: Record<string, unknown>;
};

interface EvidenceBrowserPanelProps {
  data: {
    items: EvidenceItem[];
    filters?: Record<string, unknown>;
  };
}

const KERNEL_URL = (import.meta as any).env?.VITE_KERNEL_URL ?? 'http://127.0.0.1:8081';

export function EvidenceBrowserPanel({ data }: EvidenceBrowserPanelProps) {
  const { ingestIntent, executeAction } = useReasoningStream();

  const openRecord = useCallback(async (item: EvidenceItem) => {
    try {
      const res = await fetch(`${KERNEL_URL}/evidence/${item.id}`);
      if (!res.ok) throw new Error('Failed to fetch evidence detail');
      const detail = await res.json();
      const intent: Intent = {
        action: 'show_panel',
        panel: 'evidence_record',
        id: `evidence_record_${item.id}`,
        data: detail,
      };
      ingestIntent(intent);
    } catch (e) {
      console.error('Failed to open evidence record', e);
    }
  }, [ingestIntent]);

  const onSearch = useCallback((query: string, filters: any) => {
    // Trigger kernel action to search evidence and stream back a new panel
    // This uses the existing /services/actions/execute endpoint
    executeAction('search_evidence', query);
  }, [executeAction]);

  return (
    <EvidenceBrowser
      items={data?.items || []}
      onSelectItem={openRecord}
      onSearch={onSearch}
    />
  );
}
