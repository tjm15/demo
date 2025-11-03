/* WebWorker that provides optional local embeddings/rerank.
   Uses dynamic imports to keep main bundle lean. */

// Types for @xenova/transformers are provided in a separate ambient
// declaration file to avoid "module augmentation" errors in a .ts file.
// See: ./xenova-transformers.d.ts

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
      const [{ pipeline }] = await Promise.all([
        import('@xenova/transformers'), // transformers.js
      ]);
      embedPipe = await pipeline('feature-extraction', e.data.embedModel || 'Xenova/all-MiniLM-L6-v2', { dtype: 'fp32' });
      // Reranker optional: small cross-encoder
      try {
        rerankPipe = await pipeline('text-classification', e.data.rerankModel || 'Xenova/cross-encoder-ms-marco-MiniLM-L-6-v2');
      } catch { /* optional */ }
      postMessage({ kind: 'ready' } satisfies Reply);
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
      postMessage({ kind: 'embeddings', vectors: embs } satisfies Reply);
      return;
    }

    if (e.data.kind === 'rerank') {
      if (!rerankPipe) {
        // Fallback: cosine over query embedding
        if (!embedPipe) throw new Error('Not initialised');
        const q = (await embedPipe(e.data.query, { pooling: 'mean', normalize: true })).data as Float32Array;
        const sims = e.data.docs.map(d => {
          const v = (self as any)._cache?.[d.id] as Float32Array | undefined;
          // If no cached embedding, fallback to length heuristic
          const score = v ? cosine(q, v) : Math.min(d.text.length / 2000, 1);
          return { id: d.id, score };
        });
        sims.sort((a, b) => b.score - a.score);
        postMessage({ kind: 'reranked', ids: sims.slice(0, e.data.topK ?? 20).map(s => s.id) } satisfies Reply);
        return;
      }
      // Cross-encoder: score(query, doc) per doc
      const scored = [];
      for (const d of e.data.docs) {
        const res = await rerankPipe({ text: e.data.query, text_pair: d.text });
        const score = Array.isArray(res) ? res[0]?.score ?? 0 : (res as any)?.score ?? 0;
        scored.push({ id: d.id, score });
      }
      scored.sort((a, b) => b.score - a.score);
      postMessage({ kind: 'reranked', ids: scored.slice(0, e.data.topK ?? 20).map(s => s.id) } satisfies Reply);
      return;
    }
  } catch (err: any) {
    postMessage({ kind: 'error', message: err?.message || String(err) } satisfies Reply);
  }
};

function cosine(a: Float32Array, b: Float32Array) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) + 1e-8);
}