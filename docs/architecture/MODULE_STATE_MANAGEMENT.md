# Independent Module State Management

## Overview

The Planner's Assistant now maintains **independent, logged states** for each of the 6 modules (Evidence, Policy, Strategy, Vision, Feedback, DM). This allows users to:

- Switch between modules without losing their work
- Maintain separate conversation histories per module
- Review and restore previous states
- Export/import workspace configurations

## Architecture

### Data Structures

```typescript
// Per-module state with history
interface ModuleState {
  current: DashboardState;    // Current active state
  history: DashboardState[];  // Up to 20 previous states
  lastUpdated: number;        // Timestamp
}

// Workspace containing all 6 modules
interface WorkspaceState {
  evidence?: ModuleState;
  policy?: ModuleState;
  strategy?: ModuleState;
  vision?: ModuleState;
  feedback?: ModuleState;
  dm?: ModuleState;
  activeModule?: Module;
}

// Enhanced dashboard state
interface DashboardState {
  panels: PanelData[];
  module: Module;
  session_id?: string;
  safe_mode: boolean;
  error_count: number;
  prompt?: string;          // NEW: Store the query
  reasoning?: string;       // NEW: Store AI reasoning
  timestamp?: number;       // NEW: When this state was created
}
```

### State Manager Hook

```typescript
const {
  currentState,           // Current module's state
  currentModule,          // Active module
  switchModule,           // Switch to different module
  updateState,            // Update current module
  getModuleState,         // Get any module's state
  getModuleHistory,       // Get history for a module
  clearModuleHistory,     // Clear history
  exportWorkspace,        // Export entire workspace
  loadWorkspace,          // Load workspace
} = useWorkspaceState();
```

## Usage

### Basic Module Switching

```typescript
// Switch to Evidence module
switchModule('evidence');

// Update state for current module
updateState({
  panels: [...newPanels],
  reasoning: 'AI analysis complete...',
  prompt: 'User query here',
});

// Switch to Policy module (Evidence state is preserved)
switchModule('policy');
```

### History Management

```typescript
// Get history for a specific module
const evidenceHistory = getModuleHistory('evidence');

// Review previous states
evidenceHistory.forEach((state, i) => {
  console.log(`State ${i}:`, state.panels.length, 'panels');
});

// Clear history for cleanup
clearModuleHistory('evidence');
```

### Workspace Persistence

```typescript
// Export entire workspace (all 6 modules)
const workspaceBackup = exportWorkspace();
localStorage.setItem('workspace_backup', JSON.stringify(workspaceBackup));

// Load workspace (restore all states)
const saved = JSON.parse(localStorage.getItem('workspace_backup'));
loadWorkspace(saved);
```

## Logging

### Automatic Logging

All state changes are automatically logged:

```javascript
// Console logs
[WorkspaceState] Switching to module: evidence
[WorkspaceState] UPDATE for evidence: {
  timestamp: 1699012345678,
  module: 'evidence',
  action: 'UPDATE',
  state: {
    panels: 3,
    session_id: 'session_1699012345678',
    prompt: 'Site at 51.5074, -0.1278 for residential...',
    reasoning_length: 1247
  }
}

// LocalStorage logs (last 100)
localStorage.getItem('tpa_state_logs')
// Returns array of log entries
```

### Accessing Logs

```typescript
// Get all logs
const logs = JSON.parse(localStorage.getItem('tpa_state_logs') || '[]');

// Filter by module
const evidenceLogs = logs.filter(log => log.module === 'evidence');

// Filter by action
const updateLogs = logs.filter(log => log.action === 'UPDATE');
```

## Integration with Existing Code

### AppWorkspace Integration

```typescript
export function AppWorkspace() {
  const workspaceState = useWorkspaceState();
  const { panels, isRunning, startReasoning, reasoning } = useReasoningStream();
  
  const handleModuleSelect = (moduleId: Module) => {
    // Switch module and restore its state
    workspaceState.switchModule(moduleId);
    const savedState = workspaceState.currentState;
    
    if (savedState) {
      // Restore panels, prompt, etc.
      console.log('Restored state:', savedState);
    }
  };
  
  const handleRun = () => {
    startReasoning({...});
    
    // Update workspace state after reasoning
    workspaceState.updateState({
      panels: panels,
      reasoning: reasoning,
      prompt: prompt,
    });
  };
}
```

### useReasoningStream Integration

The reasoning stream can be enhanced to update workspace state:

```typescript
const startReasoning = useCallback(async (request: ReasonRequest) => {
  // ... existing code ...
  
  // After reasoning completes, update workspace
  workspaceState.updateState({
    panels: state.panels,
    reasoning: reasoningText,
    prompt: request.prompt,
    session_id: sessionIdRef.current,
  });
}, [workspaceState]);
```

## Benefits

### For Users

1. **Context Preservation**: Switch between modules without losing work
2. **History Review**: See what queries and results were generated
3. **Session Management**: Save and load entire workspaces
4. **Debugging**: Access logs to understand what happened

### For Developers

1. **State Isolation**: Each module's state is independent
2. **Audit Trail**: Complete log of all state changes
3. **Testing**: Export/import states for testing scenarios
4. **Debugging**: Console logs + localStorage persistence

## Storage

### LocalStorage Keys

- `tpa_workspace_state`: Current workspace state (all modules)
- `tpa_state_logs`: Last 100 state change logs

### Storage Limits

- Max 20 history states per module
- Max 100 state change logs
- Automatic cleanup of old entries

## Future Enhancements

1. **Cloud Sync**: Save workspaces to server
2. **Shared Workspaces**: Collaborate with others
3. **State Diff**: Show what changed between states
4. **Undo/Redo**: Navigate state history
5. **State Analytics**: Visualize usage patterns
6. **Export to File**: Download workspace as JSON/CSV

## Example Workflow

```typescript
// 1. User starts with Evidence module
workspaceState.switchModule('evidence');
workspaceState.updateState({
  prompt: 'Site at 51.5074, -0.1278',
  panels: [evidenceSnapshot, constraints],
});

// 2. Switches to Policy module
workspaceState.switchModule('policy');
workspaceState.updateState({
  prompt: 'Review housing policy H1',
  panels: [applicablePolicies, crossRefs],
});

// 3. Back to Evidence (state preserved!)
workspaceState.switchModule('evidence');
console.log(workspaceState.currentState.prompt);
// Output: 'Site at 51.5074, -0.1278'

// 4. Review what was done in Policy
const policyHistory = workspaceState.getModuleHistory('policy');
console.log('Policy queries:', policyHistory.map(s => s.prompt));

// 5. Export for later
const backup = workspaceState.exportWorkspace();
localStorage.setItem('friday_session', JSON.stringify(backup));
```

## Implementation Status

- ✅ Core state management hook (`useWorkspaceState`)
- ✅ Schemas for ModuleState and WorkspaceState
- ✅ Automatic logging to console + localStorage
- ✅ History tracking (20 states per module)
- ✅ Export/import functionality
- ⏳ Integration with AppWorkspace (next step)
- ⏳ Integration with useReasoningStream (next step)
- ⏳ UI for viewing history (future)
- ⏳ UI for exporting/importing (future)
