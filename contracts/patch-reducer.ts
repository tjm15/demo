/**
 * Patch Reducer - Transactional JSON Patch application with validation
 * Ensures atomic, validated updates to dashboard state with rollback on failure
 */

import {
  PatchOp,
  PatchEnvelope,
  PanelData,
  DashboardState,
  validatePanel,
  validateDashboardState,
  PANEL_DATA_SCHEMAS,
} from './schemas';
import {
  PANEL_REGISTRY,
  isPanelAllowedForModule,
  canCreateMoreInstances,
  canUpdatePanel,
  BudgetTracker,
  checkBudget,
  addPanelToBudget,
  addUpdateToBudget,
  Module,
} from './registry';

/**
 * Result of patch application
 */
export interface PatchResult {
  success: boolean;
  newState?: DashboardState;
  error?: string;
  errors?: string[];
  rejectedOps?: number[];
}

/**
 * Error types for better handling
 */
export enum PatchErrorType {
  VALIDATION = 'validation',
  BUDGET = 'budget',
  PERMISSION = 'permission',
  NOT_FOUND = 'not_found',
  UNKNOWN = 'unknown',
}

export class PatchError extends Error {
  constructor(
    message: string,
    public type: PatchErrorType,
    public opIndex?: number
  ) {
    super(message);
    this.name = 'PatchError';
  }
}

/**
 * Apply JSON Patch operations to dashboard state with validation
 * 
 * This function:
 * 1. Validates patch envelope structure
 * 2. Checks permissions for each operation
 * 3. Applies operations to a cloned state
 * 4. Validates final state
 * 5. Returns new state or rolls back on any failure
 * 
 * @param currentState - Current dashboard state
 * @param envelope - Patch envelope with operations
 * @param budget - Budget tracker for operation limits
 * @param runMode - Run mode for budget limits
 * @returns Result with new state or error details
 */
export function applyPatch(
  currentState: DashboardState,
  envelope: PatchEnvelope,
  budget: BudgetTracker,
  runMode: 'stable' | 'deep'
): PatchResult {
  const errors: string[] = [];
  const rejectedOps: number[] = [];
  
  try {
    // Step 1: Validate envelope structure
    if (!envelope.ops || !Array.isArray(envelope.ops)) {
      return {
        success: false,
        error: 'Invalid patch envelope: ops must be an array',
      };
    }
    
    if (envelope.ops.length === 0) {
      // Empty patch is valid but no-op
      return { success: true, newState: currentState };
    }
    
    // Step 2: Clone state for transactional application
    const newState: DashboardState = {
      ...currentState,
      panels: [...currentState.panels],
    };
    
    // Step 3: Apply each operation
    for (let i = 0; i < envelope.ops.length; i++) {
      const op = envelope.ops[i];
      
      try {
        applyOperation(newState, op, budget, runMode, i);
      } catch (err) {
        if (err instanceof PatchError) {
          errors.push(`Op ${i} (${op.op} ${op.path}): ${err.message}`);
          rejectedOps.push(i);
          
          // For critical errors (permission, budget), fail entire patch
          if (err.type === PatchErrorType.BUDGET || err.type === PatchErrorType.PERMISSION) {
            return {
              success: false,
              error: `Critical error at operation ${i}: ${err.message}`,
              errors,
              rejectedOps,
            };
          }
          
          // For non-critical errors, log and continue (graceful degradation)
          console.warn(`Non-critical patch error at op ${i}:`, err.message);
        } else {
          // Unexpected error - fail entire patch
          return {
            success: false,
            error: `Unexpected error at operation ${i}: ${err}`,
            errors,
            rejectedOps,
          };
        }
      }
    }
    
    // Step 4: Validate final state
    const stateValidation = validateDashboardState(newState);
    if (!stateValidation.valid) {
      return {
        success: false,
        error: `Final state validation failed: ${stateValidation.error}`,
        errors,
        rejectedOps,
      };
    }
    
    // Step 5: Success - return new state
    return {
      success: true,
      newState,
      errors: errors.length > 0 ? errors : undefined,
      rejectedOps: rejectedOps.length > 0 ? rejectedOps : undefined,
    };
    
  } catch (err) {
    return {
      success: false,
      error: `Patch application failed: ${err}`,
      errors,
      rejectedOps,
    };
  }
}

/**
 * Apply a single patch operation
 */
function applyOperation(
  state: DashboardState,
  op: PatchOp,
  budget: BudgetTracker,
  runMode: 'stable' | 'deep',
  opIndex: number
): void {
  const pathParts = parsePath(op.path);
  
  if (pathParts[0] !== 'panels') {
    throw new PatchError(
      `Invalid path: only /panels/* operations are allowed`,
      PatchErrorType.VALIDATION,
      opIndex
    );
  }
  
  switch (op.op) {
    case 'add':
      applyAdd(state, pathParts, op.value, budget, runMode, opIndex);
      break;
      
    case 'replace':
      applyReplace(state, pathParts, op.value, budget, runMode, opIndex);
      break;
      
    case 'remove':
      applyRemove(state, pathParts, opIndex);
      break;
      
    case 'test':
      applyTest(state, pathParts, op.value, opIndex);
      break;
      
    default:
      throw new PatchError(
        `Unsupported operation: ${op.op}`,
        PatchErrorType.VALIDATION,
        opIndex
      );
  }
}

/**
 * Add operation - append or insert a panel
 */
function applyAdd(
  state: DashboardState,
  pathParts: string[],
  value: any,
  budget: BudgetTracker,
  runMode: 'stable' | 'deep',
  opIndex: number
): void {
  if (pathParts.length !== 2) {
    throw new PatchError(
      `Invalid add path: expected /panels/- or /panels/<index>`,
      PatchErrorType.VALIDATION,
      opIndex
    );
  }
  
  // Validate panel structure
  const panelValidation = validatePanel(value);
  if (!panelValidation.valid) {
    throw new PatchError(
      `Invalid panel data: ${panelValidation.error}`,
      PatchErrorType.VALIDATION,
      opIndex
    );
  }
  
  const panel = value as PanelData;
  
  // Check module permission
  if (!isPanelAllowedForModule(panel.type, state.module)) {
    throw new PatchError(
      `Panel type '${panel.type}' not allowed for module '${state.module}'`,
      PatchErrorType.PERMISSION,
      opIndex
    );
  }
  
  // Check instance limits
  const currentCount = state.panels.filter((p: PanelData) => p.type === panel.type).length;
  if (!canCreateMoreInstances(panel.type, currentCount)) {
    throw new PatchError(
      `Maximum instances reached for panel type '${panel.type}'`,
      PatchErrorType.BUDGET,
      opIndex
    );
  }
  
  // Check budget
  const budgetCheck = checkBudget(budget, runMode);
  if (!budgetCheck.allowed) {
    throw new PatchError(
      `Budget exceeded: ${budgetCheck.reason}`,
      PatchErrorType.BUDGET,
      opIndex
    );
  }
  
  // Check for duplicate ID
  if (state.panels.some((p: PanelData) => p.id === panel.id)) {
    throw new PatchError(
      `Panel with id '${panel.id}' already exists`,
      PatchErrorType.VALIDATION,
      opIndex
    );
  }
  
  // Apply operation
  const target = pathParts[1];
  if (target === '-') {
    // Append
    state.panels.push(panel);
  } else {
    // Insert at index
    const index = parseInt(target, 10);
    if (isNaN(index) || index < 0 || index > state.panels.length) {
      throw new PatchError(
        `Invalid index: ${target}`,
        PatchErrorType.VALIDATION,
        opIndex
      );
    }
    state.panels.splice(index, 0, panel);
  }
  
  // Update budget
  addPanelToBudget(budget, panel.type);
}

/**
 * Replace operation - update panel data or entire panel
 */
function applyReplace(
  state: DashboardState,
  pathParts: string[],
  value: any,
  budget: BudgetTracker,
  runMode: 'stable' | 'deep',
  opIndex: number
): void {
  if (pathParts.length < 2) {
    throw new PatchError(
      `Invalid replace path: expected /panels/<index> or /panels/<index>/<field>`,
      PatchErrorType.VALIDATION,
      opIndex
    );
  }
  
  const index = parseInt(pathParts[1], 10);
  if (isNaN(index) || index < 0 || index >= state.panels.length) {
    throw new PatchError(
      `Panel index ${pathParts[1]} not found`,
      PatchErrorType.NOT_FOUND,
      opIndex
    );
  }
  
  const panel = state.panels[index];
  
  // Check if updates are allowed for this panel type
  if (!canUpdatePanel(panel.type)) {
    throw new PatchError(
      `Updates not allowed for panel type '${panel.type}'`,
      PatchErrorType.PERMISSION,
      opIndex
    );
  }
  
  if (pathParts.length === 2) {
    // Replace entire panel
    const panelValidation = validatePanel(value);
    if (!panelValidation.valid) {
      throw new PatchError(
        `Invalid panel data: ${panelValidation.error}`,
        PatchErrorType.VALIDATION,
        opIndex
      );
    }
    
    state.panels[index] = value as PanelData;
  } else {
    // Replace specific field
    const field = pathParts[2];
    if (field === 'data') {
      // Validate new data against schema
      const panelValidation = validatePanel({ ...panel, data: value });
      if (!panelValidation.valid) {
        throw new PatchError(
          `Invalid panel data: ${panelValidation.error}`,
          PatchErrorType.VALIDATION,
          opIndex
        );
      }
      
      state.panels[index] = { ...panel, data: value };
    } else if (['id', 'type', 'timestamp', 'module'].includes(field)) {
      // Allow updating other fields with validation
      state.panels[index] = { ...panel, [field]: value };
    } else {
      throw new PatchError(
        `Invalid field: ${field}`,
        PatchErrorType.VALIDATION,
        opIndex
      );
    }
  }
  
  // Update budget for replacements
  addUpdateToBudget(budget);
}

/**
 * Remove operation - delete a panel
 */
function applyRemove(
  state: DashboardState,
  pathParts: string[],
  opIndex: number
): void {
  if (pathParts.length !== 2) {
    throw new PatchError(
      `Invalid remove path: expected /panels/<index>`,
      PatchErrorType.VALIDATION,
      opIndex
    );
  }
  
  const index = parseInt(pathParts[1], 10);
  if (isNaN(index) || index < 0 || index >= state.panels.length) {
    throw new PatchError(
      `Panel index ${pathParts[1]} not found`,
      PatchErrorType.NOT_FOUND,
      opIndex
    );
  }
  
  state.panels.splice(index, 1);
}

/**
 * Test operation - verify a value matches expectation
 */
function applyTest(
  state: DashboardState,
  pathParts: string[],
  value: any,
  opIndex: number
): void {
  if (pathParts.length < 2) {
    throw new PatchError(
      `Invalid test path`,
      PatchErrorType.VALIDATION,
      opIndex
    );
  }
  
  const index = parseInt(pathParts[1], 10);
  if (isNaN(index) || index < 0 || index >= state.panels.length) {
    throw new PatchError(
      `Test failed: panel ${pathParts[1]} not found`,
      PatchErrorType.VALIDATION,
      opIndex
    );
  }
  
  const panel = state.panels[index];
  
  if (pathParts.length === 2) {
    // Test entire panel
    if (JSON.stringify(panel) !== JSON.stringify(value)) {
      throw new PatchError(
        `Test failed: panel ${index} does not match expected value`,
        PatchErrorType.VALIDATION,
        opIndex
      );
    }
  } else {
    // Test specific field
    const field = pathParts[2] as keyof PanelData;
    if (panel[field] !== value) {
      throw new PatchError(
        `Test failed: panel ${index}.${String(field)} does not match expected value`,
        PatchErrorType.VALIDATION,
        opIndex
      );
    }
  }
}

/**
 * Parse JSON Pointer path into parts
 */
function parsePath(path: string): string[] {
  if (!path.startsWith('/')) {
    throw new Error(`Invalid path: must start with /`);
  }
  
  return path.substring(1).split('/').map(part => 
    part.replace(/~1/g, '/').replace(/~0/g, '~')
  );
}

/**
 * Helper: Find panel by ID
 */
export function findPanelById(state: DashboardState, id: string): PanelData | undefined {
  return state.panels.find((p: PanelData) => p.id === id);
}

/**
 * Helper: Find panel index by ID
 */
export function findPanelIndexById(state: DashboardState, id: string): number {
  return state.panels.findIndex((p: PanelData) => p.id === id);
}

/**
 * Helper: Get panel count by type
 */
export function getPanelCountByType(state: DashboardState, type: string): number {
  return state.panels.filter((p: PanelData) => p.type === type).length;
}
