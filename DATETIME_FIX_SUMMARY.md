# DateTime Serialization Fix - Complete Resolution

## Problem
SSE streaming endpoint returned `Object of type datetime is not JSON serializable` error when querying Evidence module with "London".

## Root Cause
Evidence records from PostgreSQL contain `created_at`, `updated_at` timestamp columns that were being passed through SSE pipeline without serialization.

## Solution (Multi-Layer Defense)

### 1. **Main SSE Layer** (`apps/kernel/main.py`)
```python
def _json_default(obj):
    """Fallback serializer for non-JSON types."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (set, tuple)):
        return list(obj)
    return str(obj)

# Applied to ALL json.dumps in event_generator:
json.dumps(payload, default=_json_default)
```

### 2. **Playbook Layer** (`apps/kernel/modules/playbook.py`)
```python
def _sanitize_for_json(obj):
    """Recursively sanitize objects for JSON serialization."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(item) for item in obj]
    return obj

# Applied to ALL yields before emission:
items_raw = db_search_evidence(context.get("prompt", ""), 20)
items = _sanitize_for_json(items_raw)
yield {"action": "show_panel", "panel": "evidence_browser", "data": {"items": items}}
```

### 3. **LLM Prompt Building** (`apps/kernel/modules/llm.py`)
```python
def _fallback(o):
    return str(o)

# Applied to site/proposal JSON serialization:
json.dumps(site, indent=2, default=_fallback)
```

### 4. **Trace Logging** (`apps/kernel/modules/trace.py`)
Three-tier fallback:
1. `entry.model_dump_json()` (Pydantic native)
2. `json.dumps(entry.model_dump(), default=_json_default)` (with fallback)
3. Minimal dict with error flag

### 5. **Reasoning Executor** (`apps/kernel/modules/reasoning_executor.py`)
```python
json.dumps(context_traces, indent=2, default=str)
```

## Additional Fixes During Investigation

### Import Error Fix
**Problem:** `ImportError: cannot import name 'call_llm' from 'modules.llm'`

**Solution:**
```python
# reasoning_executor.py
from .llm import generate_text  # Changed from call_llm

# Function call updated:
result = await generate_text(action_prompt, model=None)
```

### Evidence Search Broadening
**Problem:** Search only matched `title` and `key_findings`, missing geographic scope.

**Solution:** Expanded to search across 6 fields:
- `title`
- `key_findings`
- `publisher`
- `author`
- `geographic_scope`
- `topic_tags` (with array unnest)

### Proactive Evidence Browser Emission
**Problem:** Evidence browser only appeared if LLM planner decided to emit it.

**Solution:** For Evidence module, proactively emit Evidence Browser at playbook start:
```python
if context.get("module") == "evidence":
    items_raw = db_search_evidence(context.get("prompt", ""), 20)
    items = _sanitize_for_json(items_raw)
    yield {
        "action": "show_panel",
        "panel": "evidence_browser",
        "data": {"items": items, "filters": {"topics": [], "scope": "db"}}
    }
```

## Verification
✅ `/reason` endpoint tested with `module=evidence`, `prompt=London`
✅ SSE stream returns valid JSON events
✅ Evidence Browser panel emitted with 3 items (including 2 London-related records)
✅ Applicable Policies panel emitted
✅ Streaming tokens started (reasoning text)
✅ No datetime serialization errors

## Test Results
**Matching Records for "London" Query:**
1. **London Plan Strategic Flood Risk Assessment** (id: 2)
   - Type: SFRA
   - Geographic Scope: Greater London Authority
   - Year: 2023
   - Status: adopted

2. **City of London Heritage and Tall Buildings Study** (id: 6)
   - Type: Heritage Assessment
   - Geographic Scope: City of London Corporation
   - Year: 2020
   - Status: adopted (stale flag)

3. **Camden Transport Strategy Evidence Base** (id: 3)
   - Type: Transport Assessment
   - Geographic Scope: Camden Council
   - Year: 2022
   - Status: adopted

## Architecture Pattern
**Defense in Depth:** Serialization guards at multiple layers ensure robustness:
- Database query results sanitized at source
- Playbook yields sanitized before emission
- SSE json.dumps has fallback serializer
- Trace logging has three-tier fallback
- LLM prompts have fallback serializer

## Status
✅ **RESOLVED** - All datetime serialization paths hardened
✅ Evidence module fully functional
✅ Evidence Browser renders with search results
✅ Kernel stable and healthy

## Files Modified
1. `apps/kernel/main.py` - SSE serialization
2. `apps/kernel/modules/playbook.py` - Recursive sanitization + proactive emission
3. `apps/kernel/modules/llm.py` - Prompt building fallback
4. `apps/kernel/modules/trace.py` - Trace logging fallback
5. `apps/kernel/modules/reasoning_executor.py` - Import fix + context serialization
