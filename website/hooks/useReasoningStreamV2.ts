/**
 * Enhanced Reasoning Stream Hook with Patch Pipeline
 * Implements stable dashboard diffusion with validation and circuit breaker
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { PanelData } from '../components/app/PanelHost';
import {
  DashboardState,
  PatchEnvelope,
  Intent,
  validatePatchEnvelope,
} from 'contracts/schemas';
import {
  applyPatch,
  PatchResult,
} from 'contracts/patch-reducer';
import {
  translateIntent,
  createTranslationContext,
  IntentBatcher,
  TranslationContext,
} from 'contracts/intent-translator';
import {
  createBudgetTracker,
  BudgetTracker,
  Module,
} from 'contracts/registry';
import {
  createCircuitBreaker,
  recordPatchResult,
  shouldAllowOperation,
  getSafeModeState,
  CircuitBreakerState,
  resetCircuitBreaker,
} from 'contracts/circuit-breaker';

interface ReasonRequest {
  module: string;
  prompt: string;
  run_mode: 'stable' | 'deep';
  allow_web_fetch: boolean;
  site_data?: any;
  proposal_data?: any;
  interactive_actions?: boolean;
}

const KERNEL_URL = (import.meta as any).env?.VITE_KERNEL_URL ?? 'http://127.0.0.1:8081';
// Hardcode to true for testing - bypass env var issues
const DISABLE_CIRCUIT_BREAKER = true; // String((import.meta as any).env?.VITE_DISABLE_CIRCUIT_BREAKER || '').toLowerCase() === 'true';

// Debug logging
console.log('[useReasoningStreamV2] DISABLE_CIRCUIT_BREAKER:', DISABLE_CIRCUIT_BREAKER);

type StreamOptions = {
  onStateChange?: (state: DashboardState) => void;
  initialState?: DashboardState;
};

export function useReasoningStream(opts?: StreamOptions) {
  const [state, setState] = useState<DashboardState>({
    panels: [],
    module: 'evidence' as Module,
    safe_mode: false,
    error_count: 0,
  });
  
  const [isRunning, setIsRunning] = useState(false);
  const [reasoning, setReasoning] = useState<string>('');
  
  // Internal state refs
  const budgetRef = useRef<BudgetTracker>(createBudgetTracker());
  const circuitBreakerRef = useRef<CircuitBreakerState>(createCircuitBreaker());
  const batcherRef = useRef<IntentBatcher | null>(null);
  const sessionIdRef = useRef<string>('');
  const runModeRef = useRef<'stable' | 'deep'>('stable');
  const lastRequestRef = useRef<ReasonRequest | null>(null);
  const [suggestions, setSuggestions] = useState<Array<{ type: string; query?: string }>>([]);
  
  // Track if we should persist (disable during hydration to prevent spam)
  const shouldPersistRef = useRef(false);

  // Hydrate from initial state if provided
  useEffect(() => {
    if (opts?.initialState) {
      shouldPersistRef.current = false; // Disable persistence during hydration
      setState(opts.initialState);
      setReasoning(opts.initialState.reasoning || '');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Notify parent on state change (skip during hydration)
  useEffect(() => {
      const handler = opts?.onStateChange;
      if (handler && shouldPersistRef.current) {
        // Use a microtask to prevent infinite loops
        queueMicrotask(() => handler(state));
    }
      // Only re-run when state actually changes, not when opts changes
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [state]);
  
  // Cleanup batcher on unmount
  useEffect(() => {
    return () => {
      if (batcherRef.current) {
        batcherRef.current.destroy();
        batcherRef.current = null;
      }
    };
  }, []);
  
  /**
   * Apply a patch envelope to the dashboard state
   */
  const applyPatchEnvelope = useCallback((envelope: PatchEnvelope) => {
    // Check circuit breaker
    if (!shouldAllowOperation(circuitBreakerRef.current)) {
      console.warn('Circuit breaker is open, rejecting patch');
      return;
    }
    // Optional guard: allow bypassing CB in local dev
    if (!DISABLE_CIRCUIT_BREAKER) {
      if (!shouldAllowOperation(circuitBreakerRef.current)) {
        console.warn('Circuit breaker is open, rejecting patch');
        return;
      }
    }
    
    // Validate envelope
    const validation = validatePatchEnvelope(envelope);
    if (!validation.valid) {
      console.error('Invalid patch envelope:', validation.error);
      
      if (!DISABLE_CIRCUIT_BREAKER) {
        const result: PatchResult = {
          success: false,
          error: validation.error,
        };
        
        const shouldBreak = recordPatchResult(circuitBreakerRef.current, result);
        if (shouldBreak) {
          enterSafeMode();
        }
      }
      
      return;
    }
    
    // Apply patch
    setState(currentState => {
      console.log('[useReasoningStreamV2] About to apply patch. Envelope:', JSON.stringify(envelope, null, 2));
      console.log('[useReasoningStreamV2] Current state panels:', Object.keys(currentState.panels || {}));
      const result = applyPatch(
        currentState,
        envelope,
        budgetRef.current,
        runModeRef.current
      );
      
      // Record result in circuit breaker
      if (!DISABLE_CIRCUIT_BREAKER) {
        const shouldBreak = recordPatchResult(
          circuitBreakerRef.current,
          result,
          envelope.ops.length
        );
        
        if (shouldBreak) {
          // Enter safe mode asynchronously
          setTimeout(() => enterSafeMode(), 0);
          return currentState; // Don't apply this patch
        }
      }
      
      if (result.success && result.newState) {
        // Success - return new state
        return result.newState;
      } else {
        // Failure - log but keep current state (rollback)
        console.error('[useReasoningStreamV2] Patch application failed:', result.error);
        console.error('[useReasoningStreamV2] Full result object:', result);
        if (result.errors) {
          console.error('[useReasoningStreamV2] Individual errors:', result.errors);
        }
        return currentState;
      }
    });
  }, []);
  
  /**
   * Enter safe mode
   */
  const enterSafeMode = useCallback(() => {
    setState(currentState => {
      if (currentState.safe_mode) {
          // In disabled CB mode, we keep streaming and do not enter safe mode
        return currentState; // Already in safe mode
      }
      
      return getSafeModeState(currentState, circuitBreakerRef.current);
    });
    
    // Destroy batcher to stop accepting new patches
    if (batcherRef.current) {
      batcherRef.current.destroy();
      batcherRef.current = null;
    }
  }, []);
  
  /**
   * Start reasoning with patch pipeline
   */
  const startReasoning = useCallback(async (request: ReasonRequest) => {
    setIsRunning(true);
    setReasoning('');
    setSuggestions([]);
    
    // Reset state
    sessionIdRef.current = `session_${Date.now()}`;
    runModeRef.current = request.run_mode;
    budgetRef.current = createBudgetTracker();
    resetCircuitBreaker(circuitBreakerRef.current);
    
    const initial: DashboardState = {
      panels: [],
      module: request.module as Module,
      safe_mode: false,
      error_count: 0,
    };
    shouldPersistRef.current = false; // Disable during reset
    setState(initial);
    lastRequestRef.current = { ...request };
    
    // Enable persistence after initial state is set
    setTimeout(() => { shouldPersistRef.current = true; }, 0);
    
    // Create translation context
    const translationContext: TranslationContext = createTranslationContext(
      request.module as Module,
      sessionIdRef.current,
      []
    );
    
    // Create intent batcher
    batcherRef.current = new IntentBatcher(
      translationContext,
      50, // 50ms batch window
      applyPatchEnvelope
    );
    
    try {
      const response = await fetch(`${KERNEL_URL}/reason`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ ...request, interactive_actions: true }),
      });

      if (!response.ok) {
        throw new Error('Failed to start reasoning');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';
      let lastEventType: string | null = null;

      while (true) {
        // Check circuit breaker before reading more
        if (!DISABLE_CIRCUIT_BREAKER && circuitBreakerRef.current.isBroken) {
          console.warn('Circuit breaker open, stopping stream processing');
          break;
        }
        
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim() || line.startsWith(':')) continue;

          if (line.startsWith('event:')) {
            lastEventType = line.substring(6).trim();
            continue;
          }

          if (line.startsWith('data:')) {
            const data = line.substring(5).trim();
            
            try {
              const parsed = JSON.parse(data);
              
              if (lastEventType === 'token') {
                setReasoning((prev) => prev + (parsed.token || parsed.data?.token || ''));
              } else if (lastEventType === 'intent') {
                const intent: Intent = parsed;
                // Capture suggestions from status event
                if (intent.action === 'status' && intent.data?.suggestions) {
                  setSuggestions(intent.data.suggestions);
                }
                
                // Route through batcher for patch translation
                if (batcherRef.current && !circuitBreakerRef.current.isBroken) {
                  batcherRef.current.addIntent(intent);
                  
                  // Update batcher context with current panel IDs
                  setState(currentState => {
                    batcherRef.current?.updateContext(
                      currentState.panels.map(p => p.id),
                      currentState.module
                    );
                    return currentState;
                  });
                }
              } else if (lastEventType === 'patch') {
                // Direct patch envelope from backend
                const envelope: PatchEnvelope = parsed;
                
                if (!circuitBreakerRef.current.isBroken) {
                  applyPatchEnvelope(envelope);
                }
              } else if (lastEventType === 'final') {
                // Flush any pending batched intents
                if (batcherRef.current) {
                  batcherRef.current.flush();
                }
                
                // Analysis complete
                setIsRunning(false);
              } else if (lastEventType === 'error') {
                // Backend error
                console.error('Backend error:', parsed);
                
                if (!DISABLE_CIRCUIT_BREAKER) {
                  // Trigger safe mode on backend errors
                  const result: PatchResult = {
                    success: false,
                    error: parsed.message || 'Backend error',
                  };
                  
                  const shouldBreak = recordPatchResult(circuitBreakerRef.current, result);
                  if (shouldBreak) {
                    enterSafeMode();
                  }
                }
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
      
      // Ensure final flush
      if (batcherRef.current) {
        batcherRef.current.flush();
      }
      
    } catch (error) {
      console.error('Reasoning error:', error);
      if (!DISABLE_CIRCUIT_BREAKER) {
        enterSafeMode();
      }
    } finally {
      setIsRunning(false);
      
      // Cleanup batcher
      if (batcherRef.current) {
        batcherRef.current.destroy();
        batcherRef.current = null;
      }
    }
  }, [applyPatchEnvelope, enterSafeMode]);

  // Allow external hydration from a saved dashboard state
  const hydrateDashboardState = useCallback((dashboard: DashboardState) => {
    shouldPersistRef.current = false; // Disable persistence during hydration
    console.log('[useReasoningStream] Hydrating dashboard state:', {
      panels: dashboard.panels.length,
      reasoning: dashboard.reasoning?.substring(0, 50) + '...',
      hasReasoning: !!dashboard.reasoning
    });
    setState(dashboard);
    setReasoning(dashboard.reasoning || '');
    // Clear suggestions on hydrate; they're tied to a specific run
    setSuggestions([]);
    // Re-enable persistence after hydration completes
    setTimeout(() => { shouldPersistRef.current = true; }, 0);
  }, []);

  // Execute a suggested action on demand
  const executeAction = useCallback(async (actionType: string, query?: string) => {
    const req = lastRequestRef.current;
    if (!req) return;
    const payload = {
      module: req.module,
      action: actionType,
      prompt: req.prompt,
      site_data: req.site_data,
      proposal_data: req.proposal_data,
      query,
    };
    try {
      const res = await fetch(`${KERNEL_URL}/services/actions/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Action execution failed');
      const data = await res.json();
      const intents = (data?.intents || []) as Intent[];
      if (batcherRef.current) {
        intents.forEach((i) => batcherRef.current!.addIntent(i));
        // Flush quickly to show results
        batcherRef.current.flush();
      }
    } catch (e) {
      console.error('Failed to execute action', actionType, e);
    }
  }, []);

  return {
    panels: state.panels,
    isRunning,
    reasoning,
    suggestions,
    executeAction,
    startReasoning,
    hydrateDashboardState,
    safeMode: state.safe_mode,
    errorCount: state.error_count,
  };
}
