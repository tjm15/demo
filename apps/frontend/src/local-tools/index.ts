let worker: Worker | null = null;

export async function initLocalTools(opts?: { embedModel?: string; rerankModel?: string }) {
  if ((import.meta as any)?.env?.VITE_LOCAL_TOOLS !== '1') return false;
  if (!worker) {
    worker = new Worker(new URL('./worker.ts', import.meta.url), { type: 'module' });
    await new Promise<void>((resolve, reject) => {
      const onMsg = (e: MessageEvent<any>) => {
        if (e.data?.kind === 'ready') { worker!.removeEventListener('message', onMsg); resolve(); }
      };
      worker!.addEventListener('message', onMsg);
      worker!.postMessage({ kind: 'init', ...opts });
      setTimeout(() => reject(new Error('LocalTools init timeout')), 15000);
    });
  }
  return true;
}

export async function localEmbed(texts: string[]) {
  if (!worker) return null;
  return new Promise<number[][]>((resolve, reject) => {
    const onMsg = (e: MessageEvent<any>) => {
      if (e.data?.kind === 'embeddings') { worker!.removeEventListener('message', onMsg); resolve(e.data.vectors); }
      if (e.data?.kind === 'error') { worker!.removeEventListener('message', onMsg); reject(new Error(e.data.message)); }
    };
    worker!.addEventListener('message', onMsg);
    worker!.postMessage({ kind: 'embed', texts });
  });
}

export async function localRerank(query: string, docs: { id: string; text: string }[], topK?: number) {
  if (!worker) return null;
  return new Promise<string[]>((resolve, reject) => {
    const onMsg = (e: MessageEvent<any>) => {
      if (e.data?.kind === 'reranked') { worker!.removeEventListener('message', onMsg); resolve(e.data.ids); }
      if (e.data?.kind === 'error') { worker!.removeEventListener('message', onMsg); reject(new Error(e.data.message)); }
    };
    worker!.addEventListener('message', onMsg);
    worker!.postMessage({ kind: 'rerank', query, docs, topK });
  });
}