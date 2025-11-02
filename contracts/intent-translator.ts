/**
 * Intent-to-Patch Translator
 * Converts high-level LLM intents into validated JSON patch operations
 */

import { Intent, PatchOp, PatchEnvelope, PanelData } from './schemas';
import { generatePanelIdFromData } from './id-generator';
import { Module } from './registry';

/**
 * Translation context for maintaining state during batch conversion
 */
export interface TranslationContext {
  module: Module;
  session_id: string;
  batch_id?: string;
  existingPanelIds: Set<string>;
  panelIndices: Map<string, number>;
}

/**
 * Translation result
 */
export interface TranslationResult {
  success: boolean;
  ops: PatchOp[];
  errors?: string[];
}

/**
 * Translate a single intent to patch operations
 * 
 * @param intent - High-level intent from LLM/kernel
 * @param context - Translation context
 * @returns Array of patch operations
 */
export function translateIntent(
  intent: Intent,
  context: TranslationContext
): TranslationResult {
  const errors: string[] = [];
  const ops: PatchOp[] = [];
  
  try {
    switch (intent.action) {
      case 'show_panel':
        ops.push(...translateShowPanel(intent, context, errors));
        break;
        
      case 'update_panel':
        ops.push(...translateUpdatePanel(intent, context, errors));
        break;
        
      case 'remove_panel':
        ops.push(...translateRemovePanel(intent, context, errors));
        break;
        
      case 'patch':
        // Already a patch operation, validate and pass through
        if (intent.data?.ops && Array.isArray(intent.data.ops)) {
          ops.push(...intent.data.ops);
        } else {
          errors.push('Invalid patch intent: missing ops array');
        }
        break;
        
      case 'init_workspace':
      case 'status':
        // Non-panel intents, no ops generated
        break;
        
      default:
        errors.push(`Unknown intent action: ${intent.action}`);
    }
    
    return {
      success: errors.length === 0,
      ops,
      errors: errors.length > 0 ? errors : undefined,
    };
    
  } catch (err) {
    return {
      success: false,
      ops: [],
      errors: [`Translation error: ${err}`],
    };
  }
}

/**
 * Translate show_panel intent to add operation
 */
function translateShowPanel(
  intent: Intent,
  context: TranslationContext,
  errors: string[]
): PatchOp[] {
  if (!intent.panel) {
    errors.push('show_panel intent missing panel type');
    return [];
  }
  
  // Generate deterministic ID
  const panelId = intent.id || generatePanelIdFromData(
    intent.panel,
    intent.data || {}
  );
  
  // Check for duplicate
  if (context.existingPanelIds.has(panelId)) {
    // Panel already exists, convert to update instead
    return translateUpdatePanel(
      { ...intent, action: 'update_panel', id: panelId },
      context,
      errors
    );
  }
  
  // Build panel data
  const panel: PanelData = {
    id: panelId,
    type: intent.panel,
    data: intent.data || {},
    timestamp: Date.now(),
    module: context.module,
  };
  
  // Create add operation (append to end)
  const op: PatchOp = {
    op: 'add',
    path: '/panels/-',
    value: panel,
  };
  
  // Update context
  context.existingPanelIds.add(panelId);
  context.panelIndices.set(panelId, -1); // Will be resolved when applied
  
  return [op];
}

/**
 * Translate update_panel intent to replace operation
 */
function translateUpdatePanel(
  intent: Intent,
  context: TranslationContext,
  errors: string[]
): PatchOp[] {
  if (!intent.id && !intent.panel) {
    errors.push('update_panel intent missing id or panel type');
    return [];
  }
  
  // Resolve panel ID
  const panelId = intent.id || (intent.panel ? generatePanelIdFromData(
    intent.panel,
    intent.data || {}
  ) : '');
  
  if (!panelId) {
    errors.push('Could not resolve panel ID for update');
    return [];
  }
  
  // Get panel index (will be resolved at application time if -1)
  let index = context.panelIndices.get(panelId);
  if (index === undefined) {
    // Panel doesn't exist in context, might be an error or race condition
    errors.push(`Panel ${panelId} not found for update`);
    return [];
  }
  
  // For now, we'll use a placeholder and the reducer will resolve by ID
  // In a real implementation, we'd track indices more carefully
  const path = index >= 0 ? `/panels/${index}/data` : `/panels/*/data`;
  
  const op: PatchOp = {
    op: 'replace',
    path,
    value: intent.data || {},
  };
  
  return [op];
}

/**
 * Translate remove_panel intent to remove operation
 */
function translateRemovePanel(
  intent: Intent,
  context: TranslationContext,
  errors: string[]
): PatchOp[] {
  if (!intent.id && !intent.panel) {
    errors.push('remove_panel intent missing id or panel type');
    return [];
  }
  
  const panelId = intent.id || (intent.panel || '');
  let index = context.panelIndices.get(panelId);
  
  if (index === undefined) {
    errors.push(`Panel ${panelId} not found for removal`);
    return [];
  }
  
  const path = index >= 0 ? `/panels/${index}` : `/panels/*`;
  
  const op: PatchOp = {
    op: 'remove',
    path,
  };
  
  // Update context
  context.existingPanelIds.delete(panelId);
  context.panelIndices.delete(panelId);
  
  return [op];
}

/**
 * Batch translation with temporal grouping
 * Collects intents over a time window and translates them as a batch
 */
export class IntentBatcher {
  private intents: Intent[] = [];
  private timer: ReturnType<typeof setTimeout> | null = null;
  private readonly batchWindow: number;
  private readonly onBatch: (envelope: PatchEnvelope) => void;
  private context: TranslationContext;
  
  constructor(
    context: TranslationContext,
    batchWindow: number = 50,
    onBatch: (envelope: PatchEnvelope) => void
  ) {
    this.context = context;
    this.batchWindow = batchWindow;
    this.onBatch = onBatch;
  }
  
  /**
   * Add intent to batch queue
   */
  addIntent(intent: Intent): void {
    this.intents.push(intent);
    
    // Reset timer
    if (this.timer !== null) {
      clearTimeout(this.timer);
    }
    
    this.timer = setTimeout(() => this.flush(), this.batchWindow);
  }
  
  /**
   * Force flush current batch
   */
  flush(): void {
    if (this.timer !== null) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    
    if (this.intents.length === 0) {
      return;
    }
    
    // Translate all intents
    const allOps: PatchOp[] = [];
    const allErrors: string[] = [];
    
    for (const intent of this.intents) {
      const result = translateIntent(intent, this.context);
      if (result.success) {
        allOps.push(...result.ops);
      }
      if (result.errors) {
        allErrors.push(...result.errors);
      }
    }
    
    // Create envelope
    if (allOps.length > 0) {
      const envelope: PatchEnvelope = {
        action: 'patch',
        ops: allOps,
        session_id: this.context.session_id,
        batch_id: `batch_${Date.now()}`,
      };
      
      this.onBatch(envelope);
    }
    
    if (allErrors.length > 0) {
      console.warn('Translation errors in batch:', allErrors);
    }
    
    // Clear batch
    this.intents = [];
  }
  
  /**
   * Update context with current panel state
   */
  updateContext(panelIds: string[], module?: Module): void {
    this.context.existingPanelIds = new Set(panelIds);
    if (module) {
      this.context.module = module;
    }
    
    // Rebuild indices
    this.context.panelIndices.clear();
    panelIds.forEach((id, index) => {
      this.context.panelIndices.set(id, index);
    });
  }
  
  /**
   * Clean up resources
   */
  destroy(): void {
    if (this.timer !== null) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    this.intents = [];
  }
}

/**
 * Create a translation context from current state
 */
export function createTranslationContext(
  module: Module,
  session_id: string,
  existingPanels: PanelData[] = []
): TranslationContext {
  const context: TranslationContext = {
    module,
    session_id,
    existingPanelIds: new Set(existingPanels.map(p => p.id)),
    panelIndices: new Map(),
  };
  
  existingPanels.forEach((panel, index) => {
    context.panelIndices.set(panel.id, index);
  });
  
  return context;
}
