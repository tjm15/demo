/**
 * Shared TypeScript schemas for dashboard diffusion system
 * These define the contract between kernel and frontend for patch-based UI updates
 */

import { z } from 'zod';

// ============================================================================
// Panel Data Schemas
// ============================================================================

/**
 * Base panel data structure - all panels must conform to this
 */
export const PanelDataSchema = z.object({
  id: z.string().min(1, "Panel ID required"),
  type: z.string().min(1, "Panel type required"),
  data: z.record(z.any()),
  timestamp: z.number().int().positive(),
  module: z.enum(['evidence', 'policy', 'strategy', 'vision', 'feedback', 'dm']).optional(),
});

export type PanelData = z.infer<typeof PanelDataSchema>;

/**
 * Panel-specific data schemas for validation
 */
export const ApplicablePoliciesDataSchema = z.object({
  policies: z.array(z.object({
    id: z.string(),
    title: z.string(),
    text: z.string().optional(),
    relevance: z.number().min(0).max(1).optional(),
    source: z.string().optional(),
  })),
});

export const PrecedentsDataSchema = z.object({
  cases: z.array(z.object({
    ref: z.string(),
    title: z.string(),
    decision: z.string().optional(),
    relevance: z.number().min(0).max(1).optional(),
    url: z.string().url().optional(),
  })),
});

export const KeyIssuesMatrixDataSchema = z.object({
  issues: z.array(z.object({
    id: z.string(),
    topic: z.string(),
    concern: z.string(),
    policies: z.array(z.string()),
    weight: z.enum(['major', 'moderate', 'minor']).optional(),
  })),
});

export const PlanningBalanceDataSchema = z.object({
  benefits: z.array(z.object({
    factor: z.string(),
    weight: z.enum(['substantial', 'moderate', 'limited']),
    description: z.string().optional(),
  })),
  harms: z.array(z.object({
    factor: z.string(),
    weight: z.enum(['substantial', 'moderate', 'limited']),
    description: z.string().optional(),
  })),
  overall: z.enum(['approve', 'refuse', 'marginal']).optional(),
});

export const DraftDecisionDataSchema = z.object({
  recommendation: z.enum(['approve', 'refuse', 'defer']),
  reasons: z.array(z.string()),
  conditions: z.array(z.string()).optional(),
  informatives: z.array(z.string()).optional(),
});

export const EvidenceSnapshotDataSchema = z.object({
  site: z.object({
    lat: z.number().optional(),
    lng: z.number().optional(),
    address: z.string().optional(),
  }).optional(),
  constraints: z.array(z.object({
    type: z.string(),
    description: z.string(),
    severity: z.enum(['high', 'medium', 'low']).optional(),
  })),
  docs: z.array(z.object({
    title: z.string(),
    url: z.string().optional(),
    snippet: z.string().optional(),
  })).optional(),
});

export const PolicyEditorDataSchema = z.object({
  policy_id: z.string(),
  original_text: z.string(),
  suggested_text: z.string().optional(),
  issues: z.array(z.object({
    type: z.string(),
    description: z.string(),
    line: z.number().optional(),
  })).optional(),
});

export const ConflictHeatmapDataSchema = z.object({
  conflicts: z.array(z.object({
    policy_a: z.string(),
    policy_b: z.string(),
    severity: z.enum(['high', 'medium', 'low']),
    description: z.string(),
  })),
});

export const ScenarioCompareDataSchema = z.object({
  scenarios: z.array(z.object({
    id: z.string(),
    name: z.string(),
    parameters: z.record(z.any()),
    outcomes: z.record(z.any()),
  })).min(2),
});

export const VisualComplianceDataSchema = z.object({
  image_url: z.string().url().optional(),
  checks: z.array(z.object({
    criterion: z.string(),
    status: z.enum(['pass', 'fail', 'partial', 'unknown']),
    notes: z.string().optional(),
  })),
});

export const ConsultationThemesDataSchema = z.object({
  themes: z.array(z.object({
    theme: z.string(),
    count: z.number().int().positive(),
    sentiment: z.enum(['positive', 'negative', 'neutral', 'mixed']).optional(),
    examples: z.array(z.string()).optional(),
  })),
});

export const MapPanelDataSchema = z.object({
  center: z.object({
    lat: z.number(),
    lng: z.number(),
  }),
  zoom: z.number().min(1).max(20).optional(),
  layers: z.array(z.string()).optional(),
  features: z.array(z.object({
    type: z.string(),
    geometry: z.any(),
    properties: z.record(z.any()).optional(),
  })).optional(),
});

export const DocViewerDataSchema = z.object({
  doc_id: z.string(),
  title: z.string(),
  paragraphs: z.array(z.object({
    id: z.string(),
    text: z.string(),
    page: z.number().optional(),
  })),
  highlight_ids: z.array(z.string()).optional(),
});

/**
 * Map panel types to their data schemas
 */
export const PANEL_DATA_SCHEMAS: Record<string, z.ZodSchema> = {
  applicable_policies: ApplicablePoliciesDataSchema,
  precedents: PrecedentsDataSchema,
  key_issues_matrix: KeyIssuesMatrixDataSchema,
  planning_balance: PlanningBalanceDataSchema,
  draft_decision: DraftDecisionDataSchema,
  evidence_snapshot: EvidenceSnapshotDataSchema,
  policy_editor: PolicyEditorDataSchema,
  conflict_heatmap: ConflictHeatmapDataSchema,
  scenario_compare: ScenarioCompareDataSchema,
  visual_compliance: VisualComplianceDataSchema,
  consultation_themes: ConsultationThemesDataSchema,
  map: MapPanelDataSchema,
  doc_viewer: DocViewerDataSchema,
};

// ============================================================================
// JSON Patch Schemas
// ============================================================================

/**
 * JSON Patch operation
 */
export const PatchOpSchema = z.object({
  op: z.enum(['add', 'replace', 'remove', 'test']),
  path: z.string().min(1, "Path required"),
  value: z.any().optional(),
  from: z.string().optional(), // for move/copy ops
});

export type PatchOp = z.infer<typeof PatchOpSchema>;

/**
 * Patch envelope - a batch of operations with metadata
 */
export const PatchEnvelopeSchema = z.object({
  action: z.literal('patch'),
  ops: z.array(PatchOpSchema).max(20, "Too many operations in single patch"),
  session_id: z.string().optional(),
  batch_id: z.string().optional(),
});

export type PatchEnvelope = z.infer<typeof PatchEnvelopeSchema>;

/**
 * Legacy intent format (for backward compatibility)
 */
export const IntentSchema = z.object({
  action: z.string(),
  panel: z.string().optional(),
  id: z.string().optional(),
  data: z.any().optional(),
  message: z.string().optional(),
});

export type Intent = z.infer<typeof IntentSchema>;

// ============================================================================
// Dashboard State Schema
// ============================================================================

/**
 * Complete dashboard state
 */
export const DashboardStateSchema = z.object({
  panels: z.array(PanelDataSchema),
  module: z.enum(['evidence', 'policy', 'strategy', 'vision', 'feedback', 'dm']),
  session_id: z.string().optional(),
  safe_mode: z.boolean().default(false),
  error_count: z.number().int().min(0).default(0),
});

export type DashboardState = z.infer<typeof DashboardStateSchema>;

// ============================================================================
// Validation Helpers
// ============================================================================

/**
 * Validate panel data against its schema
 */
export function validatePanelData(type: string, data: any): { valid: boolean; error?: string } {
  const schema = PANEL_DATA_SCHEMAS[type];
  if (!schema) {
    return { valid: false, error: `Unknown panel type: ${type}` };
  }
  
  const result = schema.safeParse(data);
  if (!result.success) {
    return { valid: false, error: result.error.message };
  }
  
  return { valid: true };
}

/**
 * Validate a complete panel object
 */
export function validatePanel(panel: any): { valid: boolean; error?: string } {
  const baseResult = PanelDataSchema.safeParse(panel);
  if (!baseResult.success) {
    return { valid: false, error: baseResult.error.message };
  }
  
  return validatePanelData(panel.type, panel.data);
}

/**
 * Validate patch envelope
 */
export function validatePatchEnvelope(envelope: any): { valid: boolean; error?: string } {
  const result = PatchEnvelopeSchema.safeParse(envelope);
  if (!result.success) {
    return { valid: false, error: result.error.message };
  }
  
  return { valid: true };
}

/**
 * Validate dashboard state
 */
export function validateDashboardState(state: any): { valid: boolean; error?: string } {
  const result = DashboardStateSchema.safeParse(state);
  if (!result.success) {
    return { valid: false, error: result.error.message };
  }
  
  // Validate each panel
  for (const panel of state.panels) {
    const panelResult = validatePanel(panel);
    if (!panelResult.valid) {
      return { valid: false, error: `Panel ${panel.id}: ${panelResult.error}` };
    }
  }
  
  return { valid: true };
}
