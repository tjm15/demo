import React, { useCallback } from 'react';
import { EvidenceRecord } from './EvidenceRecord';
import type { Intent } from 'contracts/schemas';
import { useReasoningStream } from '../../../hooks/useReasoningStream';

interface EvidenceRecordPanelProps {
  data: {
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
      reliability_flags: Record<string, unknown>;
    };
    versions: any[];
    policy_links: any[];
    layer_ids: number[];
  };
}

const KERNEL_URL = (import.meta as any).env?.VITE_KERNEL_URL ?? 'http://127.0.0.1:8081';

export function EvidenceRecordPanel({ data }: EvidenceRecordPanelProps) {
  const { ingestIntent } = useReasoningStream();

  const refresh = useCallback(async () => {
    try {
      const id = data?.item?.id;
      if (!id) return;
      const res = await fetch(`${KERNEL_URL}/evidence/${id}`);
      if (!res.ok) throw new Error('Failed to refresh evidence');
      const detail = await res.json();
      const intent: Intent = {
        action: 'show_panel',
        panel: 'evidence_record',
        id: `evidence_record_${id}`,
        data: detail,
      };
      ingestIntent(intent);
    } catch (e) {
      console.error('Failed to refresh evidence record', e);
    }
  }, [ingestIntent, data?.item?.id]);

  const download = useCallback(async (versionId: number) => {
    try {
      // Placeholder: trigger a direct file download if an endpoint exists
      // For now, just re-fetch detail to ensure UI stays fresh after download
      await refresh();
    } catch (e) {
      console.error('Download failed', e);
    }
  }, [refresh]);

  return (
    <EvidenceRecord
      item={data.item}
      versions={data.versions}
      policy_links={data.policy_links}
      layer_ids={data.layer_ids}
      onRefresh={refresh}
      onDownload={download}
    />
  );
}
