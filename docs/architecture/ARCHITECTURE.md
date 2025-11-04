# Architecture Overview

## System Design

The Planner's Assistant is a streaming AI reasoning system with stable panel-based UI updates.

### Components

```
Frontend (React/Vite) ←→ Kernel (FastAPI) ←→ Database (PostgreSQL+PostGIS+pgvector)
                              ↓
                         Proxy (Web Retrieval)
```

### Key Patterns

**1. Dashboard Diffusion**
- LLM outputs intents (show_panel, update_panel)
- Frontend translates intents → validated patches
- Patches applied transactionally with rollback
- Budget limits: 5 panels (stable) / 15 (deep)
- Circuit breaker triggers safe mode on errors

**2. Streaming Reasoning**
- SSE events: `token` (text) | `intent` (UI update) | `final` (summary)
- Client batches intents over 50ms windows
- All panel data validated against Zod schemas
- Deterministic IDs for reproducible outputs

**3. Module System**
- 6 modules: Evidence, Policy, Strategy, Vision, Feedback, DM
- Each has its own playbook and panel permissions
- Independent state management
- Module-aware citations (domain restrictions)

**4. Security**
- Allow-listed web retrieval (GOV.UK, GLA, etc.)
- SQL injection protection (parameterized queries)
- Input sanitization and rate limiting
- Audit logging for all operations

**5. Data Layer**
- PostgreSQL with PostGIS (spatial) + pgvector (embeddings)
- Hybrid search: BM25 + vector similarity
- Evidence versioning with CAS hashing
- Policy graph with cross-references

## File Organization

```
apps/
  kernel/          # FastAPI reasoning engine
    modules/       # Playbooks, context, security
    services/      # Evidence, policy, spatial, precedent
  proxy/           # Web retrieval with allow-list
website/           # React frontend
  components/app/  # Workspace, panels, controls
  hooks/           # useReasoningStream, settings
contracts/         # Shared schemas (TS + Python)
scripts/           # Data ingestion & ETL
fixtures/          # Sample data
```

## Key Endpoints

**Kernel (8081):**
- `POST /reason` - Main reasoning endpoint (SSE)
- `POST /services/policy/search` - Policy search
- `POST /services/evidence/search` - Evidence search
- `POST /services/spatial/constraints` - Spatial analysis
- `POST /services/precedent/search` - Appeal decisions

**Proxy (8082):**
- Internal only, requires `PROXY_INTERNAL_TOKEN`
- `/search`, `/download`, `/extract`
- Domain allow-listed, robots.txt compliant

## Panel Registry

11 validated panel types in `contracts/registry.ts`:
- applicable_policies, key_issues_matrix, precedents
- planning_balance, draft_decision
- policy_editor, conflict_heatmap
- scenario_compare, visual_compliance
- consultation_themes, evidence_snapshot

Each panel has:
- Zod schema for data validation
- Module permissions
- Instance limits
- Update policies

## Development

See `README.md` for setup, `QUICKSTART.md` for fast start, `DASHBOARD_DIFFUSION.md` for patch pipeline details.
