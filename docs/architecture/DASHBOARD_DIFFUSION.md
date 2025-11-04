# Dashboard Diffusion System - Implementation Guide

## Overview

This implementation provides a **stable, validated LLM-driven dashboard system** that incrementally builds UI panels through a rigorous patch pipeline. The system ensures:

- **Validated updates**: All UI changes pass schema validation before application
- **Deterministic behavior**: Stable IDs and reproducible outputs
- **Budget enforcement**: Hard limits on panel counts per run mode
- **Circuit breaker**: Automatic safe mode on repeated failures
- **Transactional patches**: Atomic updates with rollback on failure
- **Module-aware permissions**: Panels restricted to appropriate contexts

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
├─────────────────────────────────────────────────────────────┤
│  useReasoningStreamV2 Hook                                   │
│  ├─ SSE Event Stream Parser                                  │
│  ├─ Intent Batcher (50ms windows)                            │
│  ├─ Intent → Patch Translator                                │
│  ├─ Patch Reducer (validation + application)                 │
│  ├─ Circuit Breaker (error tracking)                         │
│  └─ Budget Tracker (panel limits)                            │
├─────────────────────────────────────────────────────────────┤
│  Dashboard State                                             │
│  ├─ panels: PanelData[]                                      │
│  ├─ module: 'dm' | 'policy' | ...                            │
│  ├─ safe_mode: boolean                                       │
│  └─ error_count: number                                      │
└─────────────────────────────────────────────────────────────┘
                            ↕ SSE
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
├─────────────────────────────────────────────────────────────┤
│  POST /reason (SSE endpoint)                                 │
│  ├─ Execute Playbook                                         │
│  ├─ Yield token events (reasoning text)                      │
│  ├─ Yield intent events (show_panel)                         │
│  ├─ Yield patch events (optional direct patches)             │
│  └─ Yield final event                                        │
├─────────────────────────────────────────────────────────────┤
│  Panel Emission Helpers                                      │
│  ├─ create_show_panel_intent()                               │
│  ├─ generate_panel_id_from_data()                            │
│  ├─ validate_panel_data()                                    │
│  └─ BudgetTracker                                            │
└─────────────────────────────────────────────────────────────┘
```

## Contracts Layer

All schemas and validation logic live in `/contracts/`:

### TypeScript (Frontend)

```typescript
// contracts/schemas.ts
- PanelData, PatchOp, PatchEnvelope, DashboardState
- Zod schemas for all panel types
- validatePanel(), validateDashboardState()

// contracts/registry.ts
- PANEL_REGISTRY: whitelist of allowed panels
- Budget limits per run mode
- Module permission checks

// contracts/id-generator.ts
- generatePanelId(): deterministic ID generation
- extractContentKey(): stable identifiers from panel data

// contracts/patch-reducer.ts
- applyPatch(): transactional patch application
- Validates pre/post state, rolls back on failure

// contracts/intent-translator.ts
- translateIntent(): converts show_panel → patch ops
- IntentBatcher: batches intents over 50ms windows

// contracts/circuit-breaker.ts
- Tracks errors, triggers safe mode
- Rate limiting, budget enforcement
```

### Python (Backend)

```python
# contracts/schemas.py
- Pydantic models for PanelData, PatchOperation, etc.
- validate_panel_data(), validate_panel()

# contracts/id_generator.py
- generate_panel_id_from_data()
- extract_content_key()

# apps/kernel/modules/patch_emit.py
- create_show_panel_intent()
- create_add_panel_op()
- emit_panel_as_intent()
- BudgetTracker
```

## Usage

### 1. Frontend Integration

Replace `useReasoningStream` with `useReasoningStreamV2`:

```typescript
// Before
import { useReasoningStream } from '../hooks/useReasoningStream';

// After
import { useReasoningStream } from '../hooks/useReasoningStreamV2';

// Usage (no API changes)
const { panels, reasoning, isRunning, startReasoning, safeMode } = useReasoningStream();
```

The new hook:
- Batches intents into patch operations
- Validates all patches before application
- Tracks budget (5 panels stable, 15 deep)
- Enters safe mode on repeated errors
- Provides `safeMode` flag for UI

### 2. Backend Integration

Update playbook to use patch emission helpers:

```python
from modules.patch_emit import (
    create_show_panel_intent,
    BudgetTracker,
)

async def execute_playbook(context: ContextPack, trace_path: Path):
    budget = BudgetTracker(context.run_mode)
    
    # Check budget before emitting panel
    can_add, reason = budget.can_add_panel("applicable_policies")
    if not can_add:
        # Skip or emit warning
        yield {"type": "error", "data": {"message": reason}}
        return
    
    # Emit panel with deterministic ID
    yield {
        "type": "intent",
        "data": create_show_panel_intent(
            panel_type="applicable_policies",
            data={"policies": policies},
            module=context.module
        )
    }
    
    budget.add_panel("applicable_policies")
```

### 3. Panel Registry

Add new panel types to registry:

```typescript
// contracts/registry.ts
export const PANEL_REGISTRY: Record<string, PanelRegistryEntry> = {
  my_new_panel: {
    name: 'My New Panel',
    description: 'Description of what this panel does',
    allowedModules: ['dm', 'policy'],
    maxInstances: 1,
    allowUpdates: true,
    schemaKey: 'my_new_panel',
    weight: 2,
  },
  // ...
};
```

Then define schema:

```typescript
// contracts/schemas.ts
export const MyNewPanelDataSchema = z.object({
  title: z.string(),
  items: z.array(z.string()),
});

export const PANEL_DATA_SCHEMAS: Record<string, z.ZodSchema> = {
  // ...
  my_new_panel: MyNewPanelDataSchema,
};
```

And create component:

```typescript
// components/app/panels/MyNewPanel.tsx
export function MyNewPanel({ data }: { data: z.infer<typeof MyNewPanelDataSchema> }) {
  return <div>{/* render panel */}</div>;
}
```

Register in PanelHost:

```typescript
// components/app/PanelHost.tsx
import { MyNewPanel } from './panels/MyNewPanel';

const PANEL_COMPONENTS: Record<string, React.FC<{ data: any }>> = {
  // ...
  my_new_panel: MyNewPanel,
};
```

## Budget System

### Limits

```typescript
// Stable mode (conservative)
maxPanels: 5
maxWeight: 12
maxUpdates: 3

// Deep mode (exploratory)
maxPanels: 15
maxWeight: 40
maxUpdates: 10
```

### Panel Weights

```typescript
draft_decision: 4        // Heaviest (most complex)
scenario_compare: 4
key_issues_matrix: 3
planning_balance: 3
policy_editor: 3
visual_compliance: 3
map: 3
applicable_policies: 2
precedents: 2
evidence_snapshot: 2
conflict_heatmap: 2
consultation_themes: 2
doc_viewer: 1            // Lightest (simplest)
```

Budget is tracked per session. Frontend enforces limits before applying patches.

## Circuit Breaker

Monitors patch application for errors and triggers safe mode:

### Thresholds

- **2** consecutive validation failures → break
- **5** total failures → break
- **1** unknown error → break
- **3** budget violations → break
- **2** permission violations → break (possible prompt injection)
- **20** operations per 5-second window → rate limit

### Safe Mode

When triggered:
1. Circuit breaker opens (rejects new patches)
2. `SafeModeNotice` panel added to dashboard
3. Existing panels remain visible
4. Reasoning text continues streaming
5. Batcher destroyed (no more intents processed)

User must start new run to reset.

## Testing

### Snapshot Tests

```bash
# Run golden output tests
cd /home/tjm/code/demo
python tests/snapshot_test.py
```

Tests validate:
- Correct panel types emitted for each module
- Required fields present in panel data
- Minimum counts (e.g., ≥3 policies)
- Reasoning contains expected keywords
- Panel structure hash (regression detection)

### Golden Outputs

Defined in `tests/golden_outputs.py`:

```python
DM_SCENARIO_1 = {
    "name": "Residential Intensification",
    "prompt": "45 unit residential development, 6 storeys...",
    "module": "dm",
    "expected_panels": [
        {"type": "evidence_snapshot", "required_fields": ["site", "constraints"]},
        {"type": "applicable_policies", "policies_min": 3},
        {"type": "key_issues_matrix", "issues_min": 2},
        {"type": "precedents", "cases_min": 1},
        {"type": "planning_balance"},
        {"type": "draft_decision"},
    ],
    "reasoning_must_contain": ["conservation", "height", "density"],
}
```

Add scenarios for new features to maintain regression coverage.

## Debugging

### Enable Detailed Logging

```typescript
// frontend
localStorage.setItem('debug_patches', 'true');
```

Console will show:
- Each intent received
- Patch translation results
- Validation errors
- Budget state
- Circuit breaker status

### Backend Traces

```bash
# View kernel traces
cat apps/kernel/logs/traces/<session_id>.jsonl | jq
```

### Safe Mode Panel

When safe mode activates, `SafeModeNotice` panel shows:
- Trigger reason
- Error count
- Technical details
- Recovery instructions

## Performance

- **Intent batching**: 50ms windows reduce React re-renders
- **Transactional patches**: Validation happens once per batch, not per operation
- **Lazy validation**: Panel data schemas only validated when panel type changes
- **Budget enforcement**: Hard stops prevent runaway LLM outputs

Typical timings:
- Intent → Patch translation: <1ms
- Patch validation: 1-2ms
- State update + React render: 5-10ms
- Total latency: ~15ms per batch (imperceptible to user)

## Migration Path

1. **Phase 1**: Deploy contracts + useReasoningStreamV2 (opt-in)
2. **Phase 2**: Update backend to use patch_emit helpers
3. **Phase 3**: Enable for all users (rename V2 → main)
4. **Phase 4**: Backend emits direct patch envelopes (skip intent layer)

Current implementation supports Phase 1-3 with backward compatibility.

## Security Considerations

- **Panel registry**: Only whitelisted panel types accepted
- **Module permissions**: Panel types restricted to appropriate modules
- **Budget limits**: Hard caps prevent resource exhaustion
- **Circuit breaker**: Protects against malformed LLM outputs
- **Schema validation**: Rejects malformed data before rendering
- **Prompt injection detection**: Permission violations trigger safe mode

## Troubleshooting

### Panels not appearing

1. Check browser console for validation errors
2. Verify panel type in PANEL_REGISTRY
3. Check module permission (allowedModules)
4. Confirm budget not exceeded

### Safe mode activating unexpectedly

1. Check panel data against schema
2. Verify all required fields present
3. Review backend traces for validation errors
4. Check for permission violations (wrong module)

### Stale panel data

1. Ensure panel IDs are deterministic
2. Check content key extraction in id-generator
3. Verify update operations target correct panel by ID

## Future Enhancements

- **Undo/redo**: Store patch history for rollback
- **Optimistic updates**: Apply patches before validation (with rollback)
- **Delta compression**: Only send changed fields in updates
- **Panel diffing**: Highlight what changed in updated panels
- **Multi-user sync**: Broadcast patches via WebSocket
- **A/B testing**: Compare patch pipeline vs direct rendering

---

**Implementation Status**: ✅ Complete

All components implemented:
- ✅ Schemas (TS + Python)
- ✅ Registry with permissions
- ✅ Deterministic IDs
- ✅ Patch reducer with validation
- ✅ Intent translator with batching
- ✅ Budget tracking
- ✅ Circuit breaker
- ✅ Safe mode UI
- ✅ Backend helpers
- ✅ Golden outputs
- ✅ Snapshot tests
