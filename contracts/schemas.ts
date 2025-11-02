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
  data: z.record(z.string(), z.unknown()),
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
  citations: z.array(z.object({
    title: z.string(),
    url: z.string(),
    domain: z.string(),
    snippet: z.string().optional(),
  })).optional(),
});

// Frontend expects { precedents: [{ case_ref, decision, similarity, key_point, date? }] }
export const PrecedentsDataSchema = z.object({
  precedents: z.array(z.object({
    case_ref: z.string(),
    decision: z.string(),
    similarity: z.number().min(0).max(1),
    key_point: z.string(),
    date: z.string().optional(),
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

// Frontend uses { benefits: [{ item, weight }], harms: [{ item, weight }], overall: string }
export const PlanningBalanceDataSchema = z.object({
  benefits: z.array(z.object({
    item: z.string(),
    weight: z.string(),
  })),
  harms: z.array(z.object({
    item: z.string(),
    weight: z.string(),
  })),
  overall: z.string().optional(),
});

// Frontend displays free-text recommendation (e.g., "Approval" or "Further information required")
export const DraftDecisionDataSchema = z.object({
  recommendation: z.string(),
  reasons: z.array(z.string()),
  conditions: z.array(z.string()).optional(),
  informatives: z.array(z.string()).optional(),
});

// Frontend uses constraints [{ type, name, impact }], plus policy_count and optional citations
export const EvidenceSnapshotDataSchema = z.object({
  site: z.object({
    lat: z.number().optional(),
    lng: z.number().optional(),
    address: z.string().optional(),
  }).optional(),
  constraints: z.array(z.object({
    type: z.string(),
    name: z.string(),
    impact: z.enum(['high', 'moderate', 'low']).optional(),
  })).optional().default([]),
  policy_count: z.number().int().optional(),
  citations: z.array(z.object({
    title: z.string(),
    url: z.string(),
    domain: z.string(),
    snippet: z.string().optional(),
  })).optional(),
});

// Accept both a rich policy editor payload and a simple draft form
const RichPolicyEditorSchema = z.object({
  policy_id: z.string(),
  original_text: z.string(),
  suggested_text: z.string().optional(),
  issues: z.array(z.object({
    type: z.string(),
    description: z.string(),
    line: z.number().optional(),
  })).optional(),
});

const SimplePolicyEditorSchema = z.object({
  draft_text: z.string().optional(),
  suggestions: z.array(z.string()).optional(),
});

export const PolicyEditorDataSchema = z.union([
  RichPolicyEditorSchema,
  SimplePolicyEditorSchema,
]);

export const ConflictHeatmapDataSchema = z.object({
  conflicts: z.array(z.object({
    policy_a: z.string(),
    policy_b: z.string(),
    severity: z.enum(['high', 'medium', 'low']),
    description: z.string(),
  })),
});

// Strategy panel currently emits simple scenarios with { name, score }.
// Accept both the simple and rich forms for forward compatibility.
const SimpleScenarioSchema = z.object({
  name: z.string(),
  score: z.number().optional(),
});

const RichScenarioSchema = z.object({
  id: z.string().optional(),
  name: z.string(),
  parameters: z.record(z.string(), z.unknown()).optional(),
  outcomes: z.record(z.string(), z.unknown()).optional(),
  score: z.number().optional(),
});

export const ScenarioCompareDataSchema = z.object({
  scenarios: z.array(z.union([SimpleScenarioSchema, RichScenarioSchema])).min(2),
});

// Frontend component expects { compliance: [{ criterion, status: 'compliant'|'partial'|'non-compliant' }] }
// but we also allow an alternate { checks: [{ criterion, status: 'pass'|'fail'|'partial'|'unknown' }] } shape.
const VisualComplianceChecksSchema = z.object({
  image_url: z.string().url().optional(),
  checks: z.array(z.object({
    criterion: z.string(),
    status: z.enum(['pass', 'fail', 'partial', 'unknown']),
    notes: z.string().optional(),
  })),
});

const VisualComplianceComplianceSchema = z.object({
  image_url: z.string().url().optional(),
  compliance: z.array(z.object({
    criterion: z.string(),
    status: z.enum(['compliant', 'partial', 'non-compliant']),
  })),
});

export const VisualComplianceDataSchema = z.union([
  VisualComplianceComplianceSchema,
  VisualComplianceChecksSchema,
]);

export const ConsultationThemesDataSchema = z.object({
  themes: z.array(z.object({
    theme: z.string(),
    count: z.number().int().positive(),
    sentiment: z.enum(['positive', 'negative', 'neutral', 'mixed']).optional(),
    examples: z.array(z.string()).optional(),
  })),
});

// Frontend MapPanel expects { center?, constraints?[] } (not GeoJSON)
export const MapPanelDataSchema = z.object({
  center: z.object({
    lat: z.number(),
    lng: z.number(),
  }).optional(),
  constraints: z.array(z.object({
    type: z.string(),
    name: z.string(),
    impact: z.string(),
    geometry: z.unknown().optional(),
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

// Evidence Base Schemas
export const EvidenceBrowserDataSchema = z.object({
  items: z.array(z.object({
    id: z.number(),
    title: z.string(),
    type: z.string(),
    topic_tags: z.array(z.string()),
    geographic_scope: z.string().optional(),
    author: z.string().optional(),
    publisher: z.string().optional(),
    year: z.number().optional(),
    source_type: z.enum(['upload', 'cached_url', 'live_url']),
    status: z.enum(['draft', 'adopted', 'superseded']),
    spatial_layer_ref: z.number().optional(),
    key_findings: z.string().optional(),
    version_count: z.number(),
    reliability_flags: z.record(z.string(), z.unknown()),
  })),
  filters: z.record(z.string(), z.unknown()).optional(),
});

export const EvidenceRecordDataSchema = z.object({
  item: z.object({
    id: z.number(),
    title: z.string(),
    type: z.string(),
    topic_tags: z.array(z.string()),
    geographic_scope: z.string().optional(),
    author: z.string().optional(),
    publisher: z.string().optional(),
    year: z.number().optional(),
    source_type: z.string(),
    status: z.string(),
    key_findings: z.string().optional(),
    notes: z.string().optional(),
    reliability_flags: z.record(z.string(), z.unknown()),
  }),
  versions: z.array(z.object({
    id: z.number(),
    version_number: z.number(),
    cas_hash: z.string(),
    source_url: z.string().optional(),
    etag: z.string().optional(),
    file_size: z.number().optional(),
    mime_type: z.string().optional(),
    fetched_at: z.string(),
    license: z.string().optional(),
    robots_allowed: z.boolean(),
  })),
  policy_links: z.array(z.object({
    policy_id: z.number(),
    policy_title: z.string().optional(),
    rationale: z.string().optional(),
    strength: z.enum(['core', 'supporting', 'tangential']),
  })),
  layer_ids: z.array(z.number()),
});

export const EvidenceGapsDataSchema = z.object({
  no_evidence: z.array(z.object({
    policy_id: z.number(),
    title: z.string(),
  })),
  stale_evidence: z.array(z.object({
    policy_id: z.number(),
    title: z.string(),
    latest_year: z.number().optional(),
  })),
  weak_links_only: z.array(z.object({
    policy_id: z.number(),
    title: z.string(),
    link_count: z.number().optional(),
  })),
});

export const DependencyGraphDataSchema = z.object({
  nodes: z.array(z.object({
    id: z.string(),
    label: z.string(),
    type: z.enum(['evidence', 'policy']),
    subtype: z.string().optional(),
  })),
  edges: z.array(z.object({
    from: z.string(),
    to: z.string(),
    strength: z.enum(['core', 'supporting', 'tangential']),
    rationale: z.string().optional(),
  })),
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
  evidence_browser: EvidenceBrowserDataSchema,
  evidence_record: EvidenceRecordDataSchema,
  evidence_gaps: EvidenceGapsDataSchema,
  dependency_graph: DependencyGraphDataSchema,
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
  value: z.unknown().optional(),
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
  data: z.unknown().optional(),
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
  prompt: z.string().optional(),
  reasoning: z.string().optional(),
  timestamp: z.number().optional(),
});

export type DashboardState = z.infer<typeof DashboardStateSchema>;
export type Module = DashboardState['module'];

// Per-module state container with history
export const ModuleStateSchema = z.object({
  current: DashboardStateSchema,
  history: z.array(DashboardStateSchema).default([]),
  lastUpdated: z.number(),
});

export type ModuleState = z.infer<typeof ModuleStateSchema>;

// Workspace state with all 6 module states
export const WorkspaceStateSchema = z.object({
  evidence: ModuleStateSchema.optional(),
  policy: ModuleStateSchema.optional(),
  strategy: ModuleStateSchema.optional(),
  vision: ModuleStateSchema.optional(),
  feedback: ModuleStateSchema.optional(),
  dm: ModuleStateSchema.optional(),
  activeModule: z.enum(['evidence', 'policy', 'strategy', 'vision', 'feedback', 'dm']).optional(),
});

export type WorkspaceState = z.infer<typeof WorkspaceStateSchema>;

// ============================================================================
// Validation Helpers
// ============================================================================

/**
 * Validate panel data against its schema
 */
export function validatePanelData(type: string, data: any): { valid: boolean; error?: string } {
  console.log('[validatePanelData] Called with type:', type);
  const schema = PANEL_DATA_SCHEMAS[type];
  console.log('[validatePanelData] Schema for type exists:', !!schema);
  console.log('[validatePanelData] Schema._zod exists:', !!(schema as any)?._zod);
  
  if (!schema) {
    console.error(`[validatePanelData] Unknown panel type: ${type}`);
    console.error(`[validatePanelData] Available schemas:`, Object.keys(PANEL_DATA_SCHEMAS));
    return { valid: false, error: `Unknown panel type: ${type}` };
  }
  
  try {
    console.log('[validatePanelData] About to call safeParse on schema');
    console.log('[validatePanelData] Data to validate:', JSON.stringify(data, null, 2));
    const result = schema.safeParse(data);
    console.log('[validatePanelData] safeParse completed, success:', result.success);
    if (!result.success) {
      console.error('[validatePanelData] Validation failed:', result.error.issues);
      return { valid: false, error: result.error.message };
    }
    return { valid: true };
  } catch (e: any) {
    console.error(`[validatePanelData] EXCEPTION during safeParse for ${type}:`, e);
    console.error(`[validatePanelData] Exception stack:`, e?.stack);
    return { valid: false, error: `Schema validation failed: ${e?.message || e}` };
  }
}

/**
 * Validate a complete panel object
 */
export function validatePanel(panel: any): { valid: boolean; error?: string } {
  console.log('[validatePanel] Called with panel:', { id: panel?.id, type: panel?.type, hasData: !!panel?.data });
  console.log('[validatePanel] PanelDataSchema exists:', !!PanelDataSchema);
  console.log('[validatePanel] PanelDataSchema._zod exists:', !!(PanelDataSchema as any)?._zod);
  
  try {
    const baseResult = PanelDataSchema.safeParse(panel);
    console.log('[validatePanel] safeParse completed, success:', baseResult.success);
    if (!baseResult.success) {
      console.error('[validatePanel] Base validation failed:', baseResult.error.message);
      return { valid: false, error: baseResult.error.message };
    }
    
    console.log('[validatePanel] Base validation passed, checking panel data for type:', panel.type);
    return validatePanelData(panel.type, panel.data);
  } catch (err) {
    console.error('[validatePanel] EXCEPTION during validation:', err);
    return { valid: false, error: `Validation exception: ${err}` };
  }
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
