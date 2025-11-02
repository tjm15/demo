/**
 * Safe Mode and Circuit Breaker System
 * Detects errors and gracefully degrades functionality when LLM behavior is unstable
 */

import { DashboardState, PanelData } from './schemas';
import { PatchResult, PatchErrorType } from './patch-reducer';

/**
 * Error thresholds for triggering safe mode
 */
export const CIRCUIT_BREAKER_CONFIG = {
  // Max consecutive validation failures before breaking
  maxConsecutiveValidationFailures: 2,
  
  // Max total failures in a session
  maxTotalFailures: 5,
  
  // Max unknown/unexpected errors
  maxUnknownErrors: 1,
  
  // Max budget violations (should be enforced but this is backup)
  maxBudgetViolations: 3,
  
  // Max permission violations (could indicate prompt injection)
  maxPermissionViolations: 2,
  
  // Time window for rate limiting (ms)
  rateLimitWindow: 5000,
  
  // Max patch operations per time window
  maxOpsPerWindow: 20,
};

/**
 * Circuit breaker state
 */
export interface CircuitBreakerState {
  // Counters
  consecutiveValidationFailures: number;
  totalFailures: number;
  unknownErrors: number;
  budgetViolations: number;
  permissionViolations: number;
  
  // Rate limiting
  recentOpTimestamps: number[];
  
  // Status
  isBroken: boolean;
  breakReason?: string;
  breakTimestamp?: number;
  
  // History
  errorHistory: CircuitBreakerError[];
}

export interface CircuitBreakerError {
  timestamp: number;
  type: PatchErrorType;
  message: string;
  opIndex?: number;
}

/**
 * Create initial circuit breaker state
 */
export function createCircuitBreaker(): CircuitBreakerState {
  return {
    consecutiveValidationFailures: 0,
    totalFailures: 0,
    unknownErrors: 0,
    budgetViolations: 0,
    permissionViolations: 0,
    recentOpTimestamps: [],
    isBroken: false,
    errorHistory: [],
  };
}

/**
 * Record a patch result and update circuit breaker state
 * Returns true if circuit should break
 */
export function recordPatchResult(
  breaker: CircuitBreakerState,
  result: PatchResult,
  opCount: number = 0
): boolean {
  const config = CIRCUIT_BREAKER_CONFIG;
  
  if (result.success) {
    // Reset consecutive failure counter on success
    breaker.consecutiveValidationFailures = 0;
    
    // Record operation timestamps for rate limiting
    const now = Date.now();
    breaker.recentOpTimestamps.push(now);
    
    // Clean old timestamps outside window
    breaker.recentOpTimestamps = breaker.recentOpTimestamps.filter(
      ts => now - ts < config.rateLimitWindow
    );
    
    // Check rate limit
    if (breaker.recentOpTimestamps.length > config.maxOpsPerWindow) {
      breaker.isBroken = true;
      breaker.breakReason = `Rate limit exceeded: ${breaker.recentOpTimestamps.length} ops in ${config.rateLimitWindow}ms`;
      breaker.breakTimestamp = now;
      return true;
    }
    
    return false;
  }
  
  // Failure case - analyze errors
  breaker.totalFailures++;
  
  const now = Date.now();
  const errorTypes = new Set<PatchErrorType>();
  
  // Parse error message to determine type
  if (result.error) {
    const error: CircuitBreakerError = {
      timestamp: now,
      type: classifyError(result.error),
      message: result.error,
    };
    
    breaker.errorHistory.push(error);
    errorTypes.add(error.type);
    
    // Update type-specific counters
    updateErrorCounters(breaker, error.type);
  }
  
  // Process multiple errors if present
  if (result.errors) {
    for (let i = 0; i < result.errors.length; i++) {
      const errorMsg = result.errors[i];
      const type = classifyError(errorMsg);
      errorTypes.add(type);
      
      const error: CircuitBreakerError = {
        timestamp: now,
        type,
        message: errorMsg,
        opIndex: result.rejectedOps?.[i],
      };
      
      breaker.errorHistory.push(error);
      updateErrorCounters(breaker, type);
    }
  }
  
  // Limit error history size
  if (breaker.errorHistory.length > 50) {
    breaker.errorHistory = breaker.errorHistory.slice(-50);
  }
  
  // Check thresholds
  if (breaker.consecutiveValidationFailures >= config.maxConsecutiveValidationFailures) {
    breaker.isBroken = true;
    breaker.breakReason = `Too many consecutive validation failures (${breaker.consecutiveValidationFailures})`;
    breaker.breakTimestamp = now;
    return true;
  }
  
  if (breaker.totalFailures >= config.maxTotalFailures) {
    breaker.isBroken = true;
    breaker.breakReason = `Too many total failures (${breaker.totalFailures})`;
    breaker.breakTimestamp = now;
    return true;
  }
  
  if (breaker.unknownErrors >= config.maxUnknownErrors) {
    breaker.isBroken = true;
    breaker.breakReason = `Too many unknown errors (${breaker.unknownErrors})`;
    breaker.breakTimestamp = now;
    return true;
  }
  
  if (breaker.permissionViolations >= config.maxPermissionViolations) {
    breaker.isBroken = true;
    breaker.breakReason = `Too many permission violations (${breaker.permissionViolations}) - possible prompt injection`;
    breaker.breakTimestamp = now;
    return true;
  }
  
  if (breaker.budgetViolations >= config.maxBudgetViolations) {
    breaker.isBroken = true;
    breaker.breakReason = `Too many budget violations (${breaker.budgetViolations})`;
    breaker.breakTimestamp = now;
    return true;
  }
  
  return false;
}

/**
 * Classify error message to error type
 */
function classifyError(errorMsg: string): PatchErrorType {
  const msg = errorMsg.toLowerCase();
  
  if (msg.includes('permission') || msg.includes('not allowed') || msg.includes('unauthorized')) {
    return PatchErrorType.PERMISSION;
  }
  
  if (msg.includes('budget') || msg.includes('limit') || msg.includes('maximum')) {
    return PatchErrorType.BUDGET;
  }
  
  if (msg.includes('validation') || msg.includes('invalid') || msg.includes('schema')) {
    return PatchErrorType.VALIDATION;
  }
  
  if (msg.includes('not found') || msg.includes('does not exist')) {
    return PatchErrorType.NOT_FOUND;
  }
  
  return PatchErrorType.UNKNOWN;
}

/**
 * Update error counters based on type
 */
function updateErrorCounters(breaker: CircuitBreakerState, type: PatchErrorType): void {
  switch (type) {
    case PatchErrorType.VALIDATION:
      breaker.consecutiveValidationFailures++;
      break;
    case PatchErrorType.BUDGET:
      breaker.budgetViolations++;
      break;
    case PatchErrorType.PERMISSION:
      breaker.permissionViolations++;
      break;
    case PatchErrorType.UNKNOWN:
      breaker.unknownErrors++;
      break;
  }
}

/**
 * Check if circuit breaker should allow operation
 */
export function shouldAllowOperation(breaker: CircuitBreakerState): boolean {
  return !breaker.isBroken;
}

/**
 * Get safe mode dashboard state with warning panel
 */
export function getSafeModeState(
  currentState: DashboardState,
  breaker: CircuitBreakerState
): DashboardState {
  // Create a safe mode notice panel
  const safeModePanel: PanelData = {
    id: 'safe_mode_notice',
    type: 'safe_mode_notice',
    data: {
      reason: breaker.breakReason || 'System entered safe mode',
      timestamp: breaker.breakTimestamp || Date.now(),
      errorCount: breaker.totalFailures,
      message: getSafeModeMessage(breaker),
    },
    timestamp: Date.now(),
    module: currentState.module,
  };
  
  return {
    ...currentState,
    panels: [safeModePanel, ...currentState.panels],
    safe_mode: true,
    error_count: breaker.totalFailures,
  };
}

/**
 * Generate user-friendly safe mode message
 */
function getSafeModeMessage(breaker: CircuitBreakerState): string {
  if (breaker.permissionViolations >= CIRCUIT_BREAKER_CONFIG.maxPermissionViolations) {
    return 'The assistant attempted to create unauthorized interface elements. ' +
           'This may indicate an issue with the query. ' +
           'Any valid results generated before this point are displayed below.';
  }
  
  if (breaker.budgetViolations >= CIRCUIT_BREAKER_CONFIG.maxBudgetViolations) {
    return 'The assistant generated more interface elements than allowed. ' +
           'The most important results are displayed below in simplified form.';
  }
  
  if (breaker.unknownErrors >= CIRCUIT_BREAKER_CONFIG.maxUnknownErrors) {
    return 'The assistant encountered an unexpected error while generating the interface. ' +
           'Results are displayed in simplified mode.';
  }
  
  if (breaker.consecutiveValidationFailures >= CIRCUIT_BREAKER_CONFIG.maxConsecutiveValidationFailures) {
    return 'The assistant generated malformed interface elements. ' +
           'Displaying results in simplified mode for stability.';
  }
  
  return 'The assistant encountered issues generating the full interactive interface. ' +
         'Results are displayed in simplified mode.';
}

/**
 * Reset circuit breaker for new session
 */
export function resetCircuitBreaker(breaker: CircuitBreakerState): void {
  breaker.consecutiveValidationFailures = 0;
  breaker.totalFailures = 0;
  breaker.unknownErrors = 0;
  breaker.budgetViolations = 0;
  breaker.permissionViolations = 0;
  breaker.recentOpTimestamps = [];
  breaker.isBroken = false;
  breaker.breakReason = undefined;
  breaker.breakTimestamp = undefined;
  breaker.errorHistory = [];
}

/**
 * Get circuit breaker status summary
 */
export function getCircuitBreakerStatus(breaker: CircuitBreakerState): {
  healthy: boolean;
  status: 'healthy' | 'degraded' | 'broken';
  message?: string;
  stats: {
    totalFailures: number;
    validationFailures: number;
    budgetViolations: number;
    permissionViolations: number;
    unknownErrors: number;
  };
} {
  const stats = {
    totalFailures: breaker.totalFailures,
    validationFailures: breaker.consecutiveValidationFailures,
    budgetViolations: breaker.budgetViolations,
    permissionViolations: breaker.permissionViolations,
    unknownErrors: breaker.unknownErrors,
  };
  
  if (breaker.isBroken) {
    return {
      healthy: false,
      status: 'broken',
      message: breaker.breakReason,
      stats,
    };
  }
  
  const config = CIRCUIT_BREAKER_CONFIG;
  const isDegraded = 
    breaker.consecutiveValidationFailures > 0 ||
    breaker.totalFailures >= config.maxTotalFailures * 0.6 ||
    breaker.budgetViolations > 0 ||
    breaker.permissionViolations > 0;
  
  if (isDegraded) {
    return {
      healthy: false,
      status: 'degraded',
      message: 'System is experiencing minor issues but continuing to operate',
      stats,
    };
  }
  
  return {
    healthy: true,
    status: 'healthy',
    stats,
  };
}
