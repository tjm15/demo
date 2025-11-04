# Dashboard Diffusion - Quick Reference

## 🎯 What It Does

Converts LLM reasoning into validated, incremental UI updates through a patch pipeline.

## 🔑 Key Features

- **Validated Updates**: All panels pass schema validation before rendering
- **Budget Limits**: 5 panels (stable) / 15 panels (deep)
- **Circuit Breaker**: Auto safe-mode on repeated failures
- **Deterministic IDs**: Same content = same ID = stable diffs
- **Transactional**: All-or-nothing patch application

## 📦 Files Structure

```
contracts/
  schemas.ts          - Zod/Pydantic panel schemas
  schemas.py
  registry.ts         - Panel whitelist + permissions
  id-generator.ts     - Stable ID generation
  id_generator.py
  patch-reducer.ts    - Transactional patch application
  intent-translator.ts - Intent → Patch conversion
  circuit-breaker.ts  - Error tracking + safe mode
  
website/hooks/
  useReasoningStreamV2.ts  - New hook with patch pipeline
  
apps/kernel/modules/
  patch_emit.py       - Backend panel emission helpers
  
tests/
  golden_outputs.py   - Expected outputs per scenario
  snapshot_test.py    - Automated regression tests
```

## 🚀 Usage

### Frontend

```typescript
// Use the V2 hook
import { useReasoningStream } from '../hooks/useReasoningStreamV2';

const { panels, reasoning, safeMode, startReasoning } = useReasoningStream();

// safeMode flag indicates circuit breaker triggered
```

### Backend

```python
from modules.patch_emit import create_show_panel_intent, BudgetTracker

budget = BudgetTracker(run_mode)

# Check budget
can_add, reason = budget.can_add_panel("applicable_policies")
if not can_add:
    return  # Skip panel

# Emit with deterministic ID
yield {
    "type": "intent",
    "data": create_show_panel_intent(
        "applicable_policies",
        {"policies": [...]},
        module="dm"
    )
}

budget.add_panel("applicable_policies")
```

## 📋 Adding New Panels

### 1. Define Schema

```typescript
// contracts/schemas.ts
export const MyPanelDataSchema = z.object({
  title: z.string(),
  items: z.array(z.string()),
});

PANEL_DATA_SCHEMAS.my_panel = MyPanelDataSchema;
```

### 2. Register Panel

```typescript
// contracts/registry.ts
PANEL_REGISTRY.my_panel = {
  name: 'My Panel',
  description: 'What it does',
  allowedModules: ['dm'],
  maxInstances: 1,
  schemaKey: 'my_panel',
  weight: 2,
};
```

### 3. Create Component

```typescript
// components/app/panels/MyPanel.tsx
export function MyPanel({ data }) {
  return <div>{data.title}</div>;
}
```

### 4. Register Component

```typescript
// components/app/PanelHost.tsx
import { MyPanel } from './panels/MyPanel';

const PANEL_COMPONENTS = {
  // ...
  my_panel: MyPanel,
};
```

## 🧪 Testing

```bash
# Run snapshot tests
python tests/snapshot_test.py

# Add golden output
# Edit tests/golden_outputs.py
```

## ⚙️ Configuration

### Budget Limits

```typescript
stable: { maxPanels: 5, maxWeight: 12 }
deep:   { maxPanels: 15, maxWeight: 40 }
```

### Circuit Breaker Thresholds

```typescript
maxConsecutiveValidationFailures: 2
maxTotalFailures: 5
maxPermissionViolations: 2
maxOpsPerWindow: 20 (per 5s)
```

## 🐛 Debugging

### Frontend Console

```javascript
localStorage.setItem('debug_patches', 'true');
```

Shows: intents, translations, validations, budget state.

### Backend Traces

```bash
cat apps/kernel/logs/traces/<session_id>.jsonl | jq
```

### Safe Mode Panel

Automatically appears when circuit breaker triggers. Shows:
- Trigger reason
- Error count  
- Recovery steps

## 🔐 Security

- ✅ Panel whitelist (registry)
- ✅ Module permissions
- ✅ Budget enforcement
- ✅ Schema validation
- ✅ Prompt injection detection (permission violations)

## 📊 Performance

- Intent batching: 50ms windows
- Patch validation: ~2ms per batch
- Total latency: ~15ms (imperceptible)

## 🔄 Migration

```typescript
// Phase 1: Opt-in to V2
import { useReasoningStream } from '../hooks/useReasoningStreamV2';

// Phase 2: Backend uses patch_emit helpers
from modules.patch_emit import create_show_panel_intent

// Phase 3: Rename V2 → main (default for all)
```

## 🆘 Common Issues

**Panels not showing?**
- Check console for validation errors
- Verify panel type in PANEL_REGISTRY
- Confirm module permissions
- Check budget not exceeded

**Safe mode triggered?**
- Review validation errors in console
- Check backend traces
- Verify required fields present
- Look for permission violations

**Stale panel data?**
- Ensure IDs are deterministic
- Check content key extraction
- Verify updates target correct ID

## 📚 Full Documentation

See `DASHBOARD_DIFFUSION.md` for complete implementation guide.
