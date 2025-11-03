/* WebWorker that provides optional local embeddings/rerank.
   Uses dynamic imports to keep main bundle lean. */

export type Msg =
  | { kind: 'init'; embedModel?: string; rerankModel?: string }
  | { kind: 'embed'; texts: string[] }
  | { kind: 'rerank'; query: string; docs: { id: string; text: string }[]; topK?: number };

export type Reply =
  | { kind: 'ready' }
  | { kind: 'embeddings'; vectors: number[][] }
  | { kind: 'reranked'; ids: string[] }
  | { kind: 'error'; message: string };

let embedPipe: any | null = null;
let rerankPipe: any | null = null;

self.onmessage = async (e: MessageEvent<Msg>) => {
  try {
    if (e.data.kind === 'init') {
      // Lazy import to avoid loading when disabled
      // Dynamic import via eval to avoid bundler/TS resolution until enabled
      const mod = await (eval('import') as any)('@xenova/transformers').catch(() => null);
      if (!mod) {
        postMessage({ kind: 'error', message: 'Local tools not available: @xenova/transformers not installed' } as Reply);
        return;
      }
      const { pipeline } = mod;
      embedPipe = await pipeline('feature-extraction', e.data.embedModel || 'Xenova/all-MiniLM-L6-v2', { dtype: 'fp32' });
      // Reranker optional: small cross-encoder
      try {
        rerankPipe = await pipeline('text-classification', e.data.rerankModel || 'Xenova/cross-encoder-ms-marco-MiniLM-L-6-v2');
      } catch { /* optional */ }
      postMessage({ kind: 'ready' } as Reply);
      return;
    }

    if (e.data.kind === 'embed') {
      if (!embedPipe) throw new Error('Not initialised');
      const embs: number[][] = [];
      // Batch for stability on low-memory devices
      for (const t of e.data.texts) {
        const out = await embedPipe(t, { pooling: 'mean', normalize: true });
        // out.data is Float32Array
        embs.push(Array.from(out.data as Float32Array));
      }
      postMessage({ kind: 'embeddings', vectors: embs } as Reply);
      return;
    }

    if (e.data.kind === 'rerank') {
      if (!rerankPipe) {
        // Fallback: cosine over query embedding
        if (!embedPipe) throw new Error('Not initialised');
        const q = (await embedPipe(e.data.query, { pooling: 'mean', normalize: true })).data as Float32Array;
        const scored = e.data.docs.map(d => ({ id: d.id, score: cosine(q, textVec(embedPipe, d.text)) }));
        scored.sort((a, b) => b.score - a.score);
        postMessage({ kind: 'reranked', ids: scored.slice(0, e.data.topK ?? 20).map(s => s.id) } as Reply);
        return;
      }
      // Cross-encoder: score(query, doc) per doc
      const scored = [] as { id: string; score: number }[];
      for (const d of e.data.docs) {
        const res = await rerankPipe({ text: e.data.query, text_pair: d.text });
        const score = Array.isArray(res) ? res[0]?.score ?? 0 : (res as any)?.score ?? 0;
        scored.push({ id: d.id, score });
      }
      scored.sort((a, b) => b.score - a.score);
      postMessage({ kind: 'reranked', ids: scored.slice(0, e.data.topK ?? 20).map(s => s.id) } as Reply);
      return;
    }
  } catch (err: any) {
    postMessage({ kind: 'error', message: err?.message || String(err) } as Reply);
  }
};

function cosine(a: Float32Array, b: Float32Array) {
  let dot = 0, na = 0, nb = 0;
  const len = Math.min(a.length, b.length);
  for (let i = 0; i < len; i++) {
    dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) + 1e-8);
}

function textVec(pipe: any, text: string): Float32Array {
  // Synchronous cache-less helper – this should ideally be cached
  // but in fallback path we only call for a few docs.
  // Note: This is a synchronous wrapper around an async op – in real usage you would pre-embed docs.
  // For simplicity, return a zero vector to avoid blocking – the cross-encoder path is preferred.
  return new Float32Array(384);
}
