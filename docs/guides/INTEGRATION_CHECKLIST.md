# Integration Checklist - Dashboard Diffusion System

## Pre-Integration Verification

### ✅ Phase 0: Dependencies

- [x] Install zod: `cd website && pnpm add zod`
- [x] Verify TypeScript configuration
- [x] Check Python dependencies (pydantic already installed)

### ✅ Phase 1: Contracts Layer

#### TypeScript Files
- [x] `/contracts/schemas.ts` - Panel schemas with Zod
- [x] `/contracts/registry.ts` - Panel whitelist and permissions
- [x] `/contracts/id-generator.ts` - Deterministic IDs
- [x] `/contracts/patch-reducer.ts` - Transactional patches
- [x] `/contracts/intent-translator.ts` - Intent batching
- [x] `/contracts/circuit-breaker.ts` - Error tracking
- [x] `/contracts/index.ts` - Barrel exports

#### Python Files
- [x] `/contracts/schemas.py` - Pydantic models
- [x] `/contracts/id_generator.py` - ID generation

#### Backend Modules
- [x] `/apps/kernel/modules/patch_emit.py` - Emission helpers

### ✅ Phase 2: Frontend Components

- [x] `/website/hooks/useReasoningStreamV2.ts` - Enhanced hook
- [x] `/website/components/app/panels/SafeModeNotice.tsx` - Safe mode UI
- [x] `/website/components/app/PanelHost.tsx` - Updated registry

### ✅ Phase 3: Testing Infrastructure

- [x] `/tests/golden_outputs.py` - Expected outputs
- [x] `/tests/snapshot_test.py` - Test runner

### ✅ Phase 4: Documentation

- [x] `/DASHBOARD_DIFFUSION.md` - Full guide
- [x] `/PATCH_PIPELINE_QUICK_REF.md` - Quick reference
- [x] `/IMPLEMENTATION_SUMMARY.md` - Summary

---

## Integration Steps

### Step 1: Enable V2 Hook (Opt-In)

**File**: `website/components/app/AppWorkspace.tsx`

```typescript
// Add import for V2 hook
import { useReasoningStream } from '../../hooks/useReasoningStreamV2';

// Component will now use patch pipeline
// API is identical, plus new safeMode flag
```

**Testing**:
```bash
cd website && pnpm run dev
# Navigate to http://localhost:5173
# Test each module with sample prompts
# Verify panels appear and safe mode works
```

### Step 2: Update Backend Playbook

**File**: `apps/kernel/modules/playbook.py`

Add at top:
```python
from modules.patch_emit import (
    create_show_panel_intent,
    BudgetTracker,
)
```

Replace direct intent construction with helper:
```python
# Before
yield {
    "type": "intent",
    "data": {
        "action": "show_panel",
        "panel": "applicable_policies",
        "data": {"policies": policies}
    }
}

# After
yield {
    "type": "intent",
    "data": create_show_panel_intent(
        panel_type="applicable_policies",
        data={"policies": policies},
        module=context.module
    )
}
```

Add budget tracking:
```python
budget = BudgetTracker(context.run_mode)

# Before yielding panel
can_add, reason = budget.can_add_panel(panel_type)
if not can_add:
    await write_trace(trace_path, TraceEntry(
        t=datetime.utcnow().isoformat(),
        step="budget_exceeded",
        output={"reason": reason}
    ))
    # Skip panel or emit warning
else:
    yield {...}
    budget.add_panel(panel_type)
```

### Step 3: Run Integration Tests

```bash
# 1. Start kernel
cd apps/kernel
source ../../.venv/bin/activate
uvicorn main:app --port 8081

# 2. In another terminal, run snapshot tests
cd /home/tjm/code/demo
source .venv/bin/activate
python tests/snapshot_test.py

# Expected output:
# - All scenarios should pass
# - Panel counts should match golden outputs
# - Structure hashes should be consistent
```

### Step 4: Manual Testing Checklist

For each module, test with golden scenario:

#### DM Module
- [ ] Prompt: "45 unit residential development, 6 storeys, near conservation area"
- [ ] Expected: 6 panels (evidence_snapshot, applicable_policies, key_issues_matrix, precedents, planning_balance, draft_decision)
- [ ] Verify: IDs are deterministic (same prompt = same IDs)
- [ ] Test safe mode: Send 10 rapid requests (should trigger rate limit)

#### Evidence Module
- [ ] Prompt: "Site at 51.5074, -0.1278 for residential development"
- [ ] Expected: evidence_snapshot with lat/lng, map panel
- [ ] Verify: Map center matches coordinates

#### Policy Module
- [ ] Prompt: "Review housing policy H1 for consistency with London Plan"
- [ ] Expected: policy_editor, applicable_policies
- [ ] Verify: policy_id field present

#### Strategy Module
- [ ] Prompt: "Compare urban extension vs brownfield intensification for 5000 homes"
- [ ] Expected: scenario_compare with 2+ scenarios, planning_balance
- [ ] Verify: scenarios array has min 2 items

#### Vision Module
- [ ] Prompt: "Check design compliance for 8-storey mixed-use scheme"
- [ ] Expected: visual_compliance panel
- [ ] Verify: checks array present

#### Feedback Module
- [ ] Prompt: "Analyze consultation responses on proposed local plan"
- [ ] Expected: consultation_themes panel
- [ ] Verify: themes array with counts

### Step 5: Budget Testing

#### Stable Mode (5 panel limit)
```bash
# Prompt that would generate 6+ panels
# System should stop at 5 panels
# No safe mode (budget is enforced gracefully)
```

#### Deep Mode (15 panel limit)
```bash
# Prompt that would generate 16+ panels
# System should stop at 15 panels
```

### Step 6: Circuit Breaker Testing

#### Validation Failures
```bash
# Modify backend to emit invalid panel data
# After 2 consecutive failures, safe mode should trigger
```

#### Permission Violations
```bash
# Try to emit policy_editor panel from dm module
# After 2 violations, safe mode should trigger
```

#### Rate Limiting
```bash
# Send 20+ rapid panel updates within 5 seconds
# Circuit breaker should trigger
```

### Step 7: Safe Mode UI Verification

When safe mode triggers:
- [ ] SafeModeNotice panel appears at top
- [ ] Shows trigger reason
- [ ] Shows error count
- [ ] Shows timestamp
- [ ] Existing panels remain visible
- [ ] Reasoning text continues streaming
- [ ] "Start new run to reset" message present
- [ ] Details expandable section works

### Step 8: Performance Testing

```bash
# Measure latency with browser DevTools
# Expected: ~15ms per batch
# Network tab should show SSE stream
# No React warnings in console
```

### Step 9: Rollback Verification

#### Test Transactional Patches
```bash
# Create patch with 3 ops: 2 valid, 1 invalid
# Entire batch should be rejected
# State should remain unchanged
```

---

## Post-Integration Verification

### Automated Checks

```bash
# Run snapshot tests
python tests/snapshot_test.py

# Expected: 100% pass rate
# If failures, check tests/snapshot_results.json for details
```

### Manual Smoke Tests

- [ ] All 6 modules accessible from module switcher
- [ ] Each module produces expected panels
- [ ] Safe mode UI appears when triggered
- [ ] Panel IDs are stable (same prompt = same IDs)
- [ ] Budget limits enforced (5 stable / 15 deep)
- [ ] Reasoning text streams smoothly
- [ ] No console errors
- [ ] No TypeScript errors
- [ ] Backend traces written to logs/traces/

### Regression Tests

Compare with baseline:
- [ ] Panel structure hashes match golden outputs
- [ ] Panel counts match golden outputs
- [ ] Required fields present in all panels
- [ ] Reasoning contains expected keywords

---

## Rollback Plan

If issues arise:

### Quick Rollback (Frontend Only)
```typescript
// In AppWorkspace.tsx, revert to original hook
import { useReasoningStream } from '../../hooks/useReasoningStream';
// V2 hook not imported, system uses legacy behavior
```

### Full Rollback (Frontend + Backend)
```bash
# Remove V2 hook import
git checkout apps/kernel/modules/playbook.py
git checkout website/components/app/AppWorkspace.tsx

# Restart services
./stop.sh && ./start.sh
```

---

## Success Criteria

System is ready for production when:

- [x] All snapshot tests pass (100%)
- [ ] All manual tests pass
- [ ] Safe mode triggers correctly on errors
- [ ] Budget limits enforced
- [ ] Panel IDs deterministic
- [ ] No console errors
- [ ] Performance <20ms latency
- [ ] Circuit breaker functional
- [ ] Documentation complete

---

## Contact & Support

For issues during integration:

1. Check `/DASHBOARD_DIFFUSION.md` troubleshooting section
2. Review `/PATCH_PIPELINE_QUICK_REF.md` for common issues
3. Inspect browser console for validation errors
4. Check backend traces: `apps/kernel/logs/traces/*.jsonl`
5. Review snapshot test results: `tests/snapshot_results.json`

---

**Integration Date**: ___________  
**Integrated By**: ___________  
**Sign-Off**: ___________
