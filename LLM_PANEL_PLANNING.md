# LLM-Driven Panel Planning

## Overview

The reasoning kernel now uses **conversational LLM reasoning** to decide which UI panels to show, replacing hardcoded module→panel mappings with adaptive planning.

## Architecture

```
User Query → LLM Planner → Panel Plan → Dispatcher → Data Retrieval → UI Intents
```

### Components

1. **Panel Planner** (`modules/panel_planner.py`)
   - Analyzes user query, module, and context
   - Prompts LLM to select 1-4 relevant panels
   - Validates panel names against registry
   - Falls back to sensible defaults if LLM fails

2. **Panel Dispatcher** (`modules/panel_dispatcher.py`)
   - Executes data retrieval for each planned panel
   - Calls DB search functions (policies, precedents, constraints)
   - Formats data payloads for frontend consumption
   - Handles errors gracefully per-panel

3. **Playbook Integration** (`modules/playbook.py`)
   - Phase 3: Call `plan_panels()` to get LLM-driven plan
   - Phase 3B: Loop through plan and `dispatch_panel()` for each
   - Phase 4: Stream reasoning text (unchanged)

## LLM Planning Prompt

The planner gives the LLM:
- Module name (dm, evidence, policy, strategy, vision, feedback)
- User query text
- Whether site coordinates are available
- Run mode (stable = 2-3 panels, deep = more flexible)
- List of available panels with descriptions

The LLM responds with a JSON array like:
```json
["applicable_policies", "precedents", "draft_decision"]
```

## Panel Registry (per module)

### DM (Development Management)
- `applicable_policies`: Relevant planning policies
- `key_issues_matrix`: Policy alignment matrix
- `precedents`: Appeal decisions and case law
- `planning_balance`: Benefits vs harms
- `draft_decision`: Recommendation with conditions
- `evidence_snapshot`: Site constraints overview
- `map`: Spatial context (requires lat/lng)
- `doc_viewer`: Policy document viewer

### Evidence
- `evidence_snapshot`: Site constraints and documents
- `map`: Spatial layers (requires lat/lng)
- `applicable_policies`: Relevant policies
- `doc_viewer`: Policy document viewer

### Policy
- `policy_editor`: Edit and validate policy text
- `conflict_heatmap`: Policy conflict visualization
- `applicable_policies`: Reference policies
- `precedents`: Appeal decisions
- `doc_viewer`: Policy document viewer

### Strategy
- `scenario_compare`: Side-by-side option comparison
- `planning_balance`: Benefits vs harms
- `applicable_policies`: Relevant policies

### Vision
- `visual_compliance`: Design code compliance check
- `applicable_policies`: Design policies

### Feedback
- `consultation_themes`: Thematic analysis of feedback
- `applicable_policies`: Related policies

## Fallback Behavior

If the LLM call fails (timeout, parsing error, hallucination), the system uses sensible defaults:

```python
FALLBACK_PANELS = {
    "dm": ["applicable_policies", "precedents", "planning_balance", "draft_decision"],
    "evidence": ["evidence_snapshot", "applicable_policies"],
    "policy": ["policy_editor"],
    "strategy": ["scenario_compare", "planning_balance"],
    "vision": ["visual_compliance"],
    "feedback": ["consultation_themes"],
}
```

## Validation Rules

1. **Panel name validation**: Only panels in module's registry are allowed
2. **Coordinate constraint**: `map` panel requires `lat` and `lng` in `site_data`
3. **Count limit**: Max 5 panels per run (prevents UI overload)
4. **Budget enforcement**: Panels still counted against circuit breaker budgets

## Example Flows

### DM: Short query
**Query**: "refusal"
**LLM Plan**: `["applicable_policies", "precedents"]`
**Rationale**: Focus on policies and precedents for appeal/refusal context

### DM: Full assessment
**Query**: "45 unit residential development, 6 storeys, near conservation area"
**LLM Plan**: `["applicable_policies", "precedents", "planning_balance", "draft_decision"]`
**Rationale**: Complete assessment workflow with recommendation

### Evidence: With coordinates
**Query**: "Site at 51.5074, -0.1278 for residential development"
**LLM Plan**: `["map", "evidence_snapshot", "applicable_policies"]`
**Rationale**: Show spatial context first, then constraints and policies

### Policy: Drafting
**Query**: "Review housing policy H1 for consistency"
**LLM Plan**: `["policy_editor", "applicable_policies", "conflict_heatmap"]`
**Rationale**: Editing tools plus reference and conflict detection

## Trace Logging

Each run logs:
- `plan_panels` step with user query
- `panel_plan` output with selected panels
- `emit_panel` for each successful panel
- `panel_error` for any dispatch failures

Traces stored in `LOG_DIR` (default: `./logs/traces/`).

## Testing

### Manual testing
```bash
# Start services
./start.sh

# Try varied queries in each module:
# - Short vs long queries
# - With/without coordinates
# - Keywords like "appeal", "refusal", "compliance"
```

### Checking LLM decisions
```bash
# Watch kernel logs
tail -f apps/kernel/logs/*.log

# Look for:
[PanelPlanner] LLM selected panels: ['applicable_policies', 'map']
[Playbook] Panel plan for evidence: ['map', 'evidence_snapshot']
```

### Fallback testing
```bash
# Temporarily break LLM to verify fallbacks work
export DISABLE_LLM=true
./start.sh
# Should see: [PanelPlanner] Planning failed: ..., using fallback
```

## Performance

- **Planning latency**: +500-1500ms per run (LLM call)
- **GPU usage**: Planning uses text generation (lighter than embedding)
- **Caching**: Not yet implemented; each run plans fresh

## Future Enhancements

1. **Plan caching**: Cache plans for similar queries
2. **User feedback loop**: Learn from user panel interactions
3. **Multi-turn refinement**: "Show me precedents too" → add panel
4. **Panel priority/scoring**: LLM assigns importance weights
5. **Conditional data loading**: Only fetch data for planned panels (currently all dm panels fetch policies)

## Configuration

No special config needed — uses same `LLM_PROVIDER` and `LLM_MODEL` as reasoning text.

To disable planning (use hardcoded fallbacks only):
```python
# In panel_planner.py, set:
ENABLE_LLM_PLANNING = False
```

## Debugging

If panels aren't appearing:
1. Check kernel logs for `[PanelPlanner]` messages
2. Verify LLM is responding (check `[LLM]` messages)
3. Look for `panel_error` in trace logs
4. Check frontend console for circuit breaker trips

If wrong panels appear:
1. Review LLM prompt in `panel_planner.py`
2. Check panel registry matches module expectations
3. Adjust fallback sequences
4. Consider adding more context to planning prompt (proposal details, etc.)
