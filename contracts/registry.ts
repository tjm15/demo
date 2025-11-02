/**
 * Panel Registry - Central whitelist of approved UI components
 * Defines which panels can be created, their constraints, and module permissions
 */

import { z } from 'zod';

export type Module = 'evidence' | 'policy' | 'strategy' | 'vision' | 'feedback' | 'dm';

/**
 * Panel metadata definition
 */
export interface PanelRegistryEntry {
  /** Human-readable name */
  name: string;
  
  /** Description of panel purpose */
  description: string;
  
  /** Which modules can emit this panel */
  allowedModules: Module[];
  
  /** Maximum instances per session (undefined = unlimited) */
  maxInstances?: number;
  
  /** Whether this panel requires site data */
  requiresSiteData?: boolean;
  
  /** Whether this panel can be updated after creation */
  allowUpdates?: boolean;
  
  /** Schema validator key (references PANEL_DATA_SCHEMAS) */
  schemaKey: string;
  
  /** Estimated complexity weight (for budget calculations) */
  weight?: number;
}

/**
 * Complete panel registry - the single source of truth
 */
export const PANEL_REGISTRY: Record<string, PanelRegistryEntry> = {
  applicable_policies: {
    name: 'Applicable Policies',
    description: 'List of relevant planning policies for the proposal',
    allowedModules: ['dm', 'policy', 'evidence'],
    maxInstances: 1,
    allowUpdates: true,
    schemaKey: 'applicable_policies',
    weight: 2,
  },
  
  key_issues_matrix: {
    name: 'Key Issues Matrix',
    description: 'Matrix of planning issues and their policy alignment',
    allowedModules: ['dm'],
    maxInstances: 1,
    allowUpdates: true,
    schemaKey: 'key_issues_matrix',
    weight: 3,
  },
  
  precedents: {
    name: 'Precedents',
    description: 'Relevant appeal decisions and case law',
    allowedModules: ['dm', 'policy'],
    maxInstances: 1,
    allowUpdates: true,
    schemaKey: 'precedents',
    weight: 2,
  },
  
  planning_balance: {
    name: 'Planning Balance',
    description: 'Weighing of benefits and harms for decision',
    allowedModules: ['dm'],
    maxInstances: 1,
    allowUpdates: true,
    schemaKey: 'planning_balance',
    weight: 3,
  },
  
  draft_decision: {
    name: 'Draft Decision',
    description: 'Recommended decision with reasons and conditions',
    allowedModules: ['dm'],
    maxInstances: 1,
    allowUpdates: true,
    schemaKey: 'draft_decision',
    weight: 4,
  },
  
  evidence_snapshot: {
    name: 'Evidence Snapshot',
    description: 'Overview of site constraints and available documents',
    allowedModules: ['evidence', 'dm'],
    maxInstances: 1,
    requiresSiteData: false,
    allowUpdates: true,
    schemaKey: 'evidence_snapshot',
    weight: 2,
  },
  
  policy_editor: {
    name: 'Policy Editor',
    description: 'Edit and validate policy wording',
    allowedModules: ['policy'],
    maxInstances: 3, // Allow comparing multiple drafts
    allowUpdates: true,
    schemaKey: 'policy_editor',
    weight: 3,
  },
  
  conflict_heatmap: {
    name: 'Conflict Heatmap',
    description: 'Visualization of policy conflicts and tensions',
    allowedModules: ['policy'],
    maxInstances: 1,
    allowUpdates: true,
    schemaKey: 'conflict_heatmap',
    weight: 2,
  },
  
  scenario_compare: {
    name: 'Scenario Compare',
    description: 'Side-by-side comparison of strategy options',
    allowedModules: ['strategy'],
    maxInstances: 1,
    allowUpdates: true,
    schemaKey: 'scenario_compare',
    weight: 4,
  },
  
  visual_compliance: {
    name: 'Visual Compliance',
    description: 'Design code compliance check with visual analysis',
    allowedModules: ['vision'],
    maxInstances: 1,
    requiresSiteData: false,
    allowUpdates: true,
    schemaKey: 'visual_compliance',
    weight: 3,
  },
  
  consultation_themes: {
    name: 'Consultation Themes',
    description: 'Thematic analysis of consultation feedback',
    allowedModules: ['feedback'],
    maxInstances: 1,
    allowUpdates: true,
    schemaKey: 'consultation_themes',
    weight: 2,
  },
  
  map: {
    name: 'Map Panel',
    description: 'Interactive map with spatial layers and features',
    allowedModules: ['evidence', 'dm'],
    maxInstances: 2,
    requiresSiteData: false,
    allowUpdates: true,
    schemaKey: 'map',
    weight: 3,
  },
  
  doc_viewer: {
    name: 'Document Viewer',
    description: 'View policy documents with paragraph highlighting',
    allowedModules: ['evidence', 'policy', 'dm'],
    maxInstances: 2,
    allowUpdates: true,
    schemaKey: 'doc_viewer',
    weight: 1,
  },
  
  evidence_browser: {
    name: 'Evidence Browser',
    description: 'Search and filter evidence base items',
    allowedModules: ['evidence'],
    maxInstances: 1,
    allowUpdates: true,
    schemaKey: 'evidence_browser',
    weight: 3,
  },
  
  evidence_record: {
    name: 'Evidence Record',
    description: 'Detailed view of evidence item with versions and links',
    allowedModules: ['evidence'],
    maxInstances: 1,
    allowUpdates: true,
    schemaKey: 'evidence_record',
    weight: 2,
  },
  
  evidence_gaps: {
    name: 'Evidence Gaps & Alerts',
    description: 'Analysis of evidence gaps and currency issues',
    allowedModules: ['evidence'],
    maxInstances: 1,
    allowUpdates: true,
    schemaKey: 'evidence_gaps',
    weight: 2,
  },
  
  dependency_graph: {
    name: 'Dependency Graph',
    description: 'Visual graph of evidence-policy relationships',
    allowedModules: ['evidence'],
    maxInstances: 1,
    allowUpdates: true,
    schemaKey: 'dependency_graph',
    weight: 3,
  },
};

/**
 * Budget limits per run mode
 */
export const BUDGET_LIMITS = {
  stable: {
    maxPanels: 5,
    maxWeight: 12,
    maxUpdates: 3,
  },
  deep: {
    maxPanels: 15,
    maxWeight: 40,
    maxUpdates: 10,
  },
};

/**
 * Validation helpers
 */

export function isPanelTypeAllowed(type: string): boolean {
  return type in PANEL_REGISTRY;
}

export function isPanelAllowedForModule(type: string, module: Module): boolean {
  const entry = PANEL_REGISTRY[type];
  if (!entry) return false;
  return entry.allowedModules.includes(module);
}

export function canCreateMoreInstances(type: string, currentCount: number): boolean {
  const entry = PANEL_REGISTRY[type];
  if (!entry) return false;
  if (entry.maxInstances === undefined) return true;
  return currentCount < entry.maxInstances;
}

export function getPanelWeight(type: string): number {
  const entry = PANEL_REGISTRY[type];
  return entry?.weight ?? 1;
}

export function canUpdatePanel(type: string): boolean {
  const entry = PANEL_REGISTRY[type];
  return entry?.allowUpdates ?? false;
}

/**
 * Budget tracking
 */
export interface BudgetTracker {
  panelCount: number;
  totalWeight: number;
  updateCount: number;
  panelCounts: Record<string, number>;
}

export function createBudgetTracker(): BudgetTracker {
  return {
    panelCount: 0,
    totalWeight: 0,
    updateCount: 0,
    panelCounts: {},
  };
}

export function checkBudget(
  tracker: BudgetTracker,
  runMode: 'stable' | 'deep'
): { allowed: boolean; reason?: string } {
  const limits = BUDGET_LIMITS[runMode];
  
  if (tracker.panelCount >= limits.maxPanels) {
    return { allowed: false, reason: `Panel limit reached (${limits.maxPanels})` };
  }
  
  if (tracker.totalWeight >= limits.maxWeight) {
    return { allowed: false, reason: `Weight budget exceeded (${limits.maxWeight})` };
  }
  
  if (tracker.updateCount >= limits.maxUpdates) {
    return { allowed: false, reason: `Update limit reached (${limits.maxUpdates})` };
  }
  
  return { allowed: true };
}

export function addPanelToBudget(
  tracker: BudgetTracker,
  type: string
): void {
  tracker.panelCount++;
  tracker.totalWeight += getPanelWeight(type);
  tracker.panelCounts[type] = (tracker.panelCounts[type] ?? 0) + 1;
}

export function addUpdateToBudget(tracker: BudgetTracker): void {
  tracker.updateCount++;
}

/**
 * Get all panel types allowed for a module
 */
export function getAllowedPanelTypes(module: Module): string[] {
  return Object.entries(PANEL_REGISTRY)
    .filter(([_, entry]) => entry.allowedModules.includes(module))
    .map(([type, _]) => type);
}
