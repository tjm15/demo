// Ambient declaration for the external '@xenova/transformers' package.
// Placed in a .d.ts file so TypeScript treats it as an external module
// declaration (not an augmentation).

declare module '@xenova/transformers' {
  // Minimal typings used by this worker
  export type PipelineFn = (task: string, model?: string, options?: any) => Promise<any>;

  export function pipeline(task: string, model?: string, options?: any): Promise<any>;

  const _default: { pipeline: PipelineFn };
  export default _default;
}