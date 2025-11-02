/**
 * Workspace State Manager
 * Maintains independent states for each of the 6 modules with history/logging
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import type { WorkspaceState, ModuleState, DashboardState, Module } from 'contracts/schemas';

const MAX_HISTORY_PER_MODULE = 20;

interface WorkspaceStateManager {
  // Current active module state
  currentState: DashboardState | null;
  currentModule: Module | null;
  
  // Switch to a different module
  switchModule: (module: Module) => void;
  
  // Update current module's state
  updateState: (updates: Partial<DashboardState>) => void;
  
  // Get state for a specific module
  getModuleState: (module: Module) => ModuleState | null;
  
  // Get history for a specific module
  getModuleHistory: (module: Module) => DashboardState[];
  
  // Clear history for a module
  clearModuleHistory: (module: Module) => void;
  // Reset an entire module state (current + history)
  resetModuleState: (module: Module) => void;
  
  // Export all state for logging/debugging
  exportWorkspace: () => WorkspaceState;
  
  // Load workspace state
  loadWorkspace: (state: WorkspaceState) => void;
  
  // Reset all workspace state
  resetWorkspace: () => void;
}

export function useWorkspaceState(): WorkspaceStateManager {
  const [workspaceState, setWorkspaceState] = useState<WorkspaceState>({
    activeModule: undefined,
  });
  
  const [currentModule, setCurrentModule] = useState<Module | null>(null);
  
  // Log all state changes to localStorage for debugging (console logging disabled to reduce noise)
  const logStateChange = useCallback((module: Module, state: DashboardState, action: string) => {
    const logEntry = {
      timestamp: Date.now(),
      module,
      action,
      state: {
        panels: state.panels.length,
        session_id: state.session_id,
        prompt: state.prompt?.substring(0, 50) + '...',
        reasoning_length: state.reasoning?.length || 0,
      },
    };
    
    // Disabled console logging to reduce noise
    // console.log(`[WorkspaceState] ${action} for ${module}:`, logEntry);
    
    // Persist to localStorage for debugging
    try {
      const logs = JSON.parse(localStorage.getItem('tpa_state_logs') || '[]');
      logs.push(logEntry);
      // Keep last 100 logs
      if (logs.length > 100) logs.shift();
      localStorage.setItem('tpa_state_logs', JSON.stringify(logs));
    } catch (e) {
      // Silently fail
    }
  }, []);
  
  // Initialize module state if it doesn't exist
  const ensureModuleState = useCallback((module: Module): ModuleState => {
    const existing = workspaceState[module];
    if (existing) return existing;
    
    const initialState: ModuleState = {
      current: {
        panels: [],
        module,
        safe_mode: false,
        error_count: 0,
        timestamp: Date.now(),
      },
      history: [],
      lastUpdated: Date.now(),
    };
    
    return initialState;
  }, [workspaceState]);
  
  // Switch to a different module
  const switchModule = useCallback((module: Module) => {
    // Disabled logging to reduce noise
    // console.log(`[WorkspaceState] Switching to module: ${module}`);
    setCurrentModule(module);
    setWorkspaceState(prev => ({
      ...prev,
      activeModule: module,
      [module]: prev[module] || ensureModuleState(module),
    }));
  }, [ensureModuleState]);
  
  // Update current module's state
  const updateState = useCallback((updates: Partial<DashboardState>) => {
    if (!currentModule) {
      // Silently return if no active module
      return;
    }
    
    setWorkspaceState(prev => {
      const moduleState = prev[currentModule] || ensureModuleState(currentModule);
      
      // Check if anything actually changed (ignore timestamp in comparison)
      const hasChanges = Object.keys(updates).some(key => {
        if (key === 'timestamp') return false; // Ignore timestamp
        const currentValue = moduleState.current[key as keyof DashboardState];
        const newValue = updates[key as keyof Partial<DashboardState>];
        // Deep comparison using JSON stringify
        return JSON.stringify(currentValue) !== JSON.stringify(newValue);
      });
      
      // If nothing changed, return previous state to prevent re-render
      if (!hasChanges) {
        return prev;
      }
      
      const newState: DashboardState = {
        ...moduleState.current,
        ...updates,
        timestamp: Date.now(),
      };
      
      // Add current state to history before updating
      const newHistory = [...moduleState.history, moduleState.current].slice(-MAX_HISTORY_PER_MODULE);
      
      const updatedModuleState: ModuleState = {
        current: newState,
        history: newHistory,
        lastUpdated: Date.now(),
      };
      
      logStateChange(currentModule, newState, 'UPDATE');
      
      return {
        ...prev,
        [currentModule]: updatedModuleState,
      };
    });
  }, [currentModule, ensureModuleState, logStateChange]);
  
  // Get state for a specific module
  const getModuleState = useCallback((module: Module): ModuleState | null => {
    return workspaceState[module] || null;
  }, [workspaceState]);
  
  // Get history for a specific module
  const getModuleHistory = useCallback((module: Module): DashboardState[] => {
    return workspaceState[module]?.history || [];
  }, [workspaceState]);
  
  // Clear history for a module
  const clearModuleHistory = useCallback((module: Module) => {
    // Disabled logging to reduce noise
    setWorkspaceState(prev => {
      const moduleState = prev[module];
      if (!moduleState) return prev;
      
      return {
        ...prev,
        [module]: {
          ...moduleState,
          history: [],
          lastUpdated: Date.now(),
        },
      };
    });
  }, []);

  // Reset entire module state
  const resetModuleState = useCallback((module: Module) => {
    // Disabled logging to reduce noise
    setWorkspaceState(prev => {
      const initial: ModuleState = {
        current: {
          panels: [],
          module,
          safe_mode: false,
          error_count: 0,
          timestamp: Date.now(),
        },
        history: [],
        lastUpdated: Date.now(),
      };
      return {
        ...prev,
        [module]: initial,
        activeModule: prev.activeModule === module ? module : prev.activeModule,
      };
    });
  }, []);
  
  // Export all state
  const exportWorkspace = useCallback((): WorkspaceState => {
    return workspaceState;
  }, [workspaceState]);
  
  // Load workspace state
  const loadWorkspace = useCallback((state: WorkspaceState) => {
    // Disabled logging to reduce noise
    setWorkspaceState(state);
    if (state.activeModule) {
      setCurrentModule(state.activeModule);
    }
  }, []);

  // Reset entire workspace
  const resetWorkspace = useCallback(() => {
    // Disabled logging to reduce noise
    setWorkspaceState({ activeModule: currentModule || undefined });
  }, [currentModule]);
  
  // Get current state
  const currentState = currentModule ? workspaceState[currentModule]?.current || null : null;
  
  // Auto-persist to localStorage on changes
  useEffect(() => {
    try {
      localStorage.setItem('tpa_workspace_state', JSON.stringify(workspaceState));
    } catch (e) {
      // Silently fail
    }
  }, [workspaceState]);
  
  // Load from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem('tpa_workspace_state');
      if (saved) {
        const parsed = JSON.parse(saved);
        loadWorkspace(parsed);
        // Disabled logging to reduce noise
      }
    } catch (e) {
      // Silently fail
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  
  return {
    currentState,
    currentModule,
    switchModule,
    updateState,
    getModuleState,
    getModuleHistory,
    clearModuleHistory,
    resetModuleState,
    exportWorkspace,
    loadWorkspace,
    resetWorkspace,
  };
}
