# The Planner’s Assistant – Maximal Demo (Ubuntu 22.04, 2025)

## 1. Vision

This is a **fully functioning application**, not a scripted demo. It must:

* Run on Ubuntu 22.04 with current (2025) toolchain.
* Handle real data via **pre‑loaded fixtures** and **on‑demand retrieval (Light Proxy)**.
* Provide planner‑grade reasoning with live streaming, citations, and module‑aware security.
* Present an **attractive, production‑style UI** (no internal traces exposed; traces persisted server‑side).
* Maintain **feature parity** with your existing artefacts (zip) as listed in the **Feature Parity Checklist** below.

---

## 2. Stack Overview

| Layer              | Stack                                                      | Notes                              |
| ------------------ | ---------------------------------------------------------- | ---------------------------------- |
| **OS / Base**      | Ubuntu 22.04 LTS                                           | Target baseline                    |
| **Database**       | PostgreSQL 17 + PostGIS 3.6 + pgvector                     | Spatial + vector search            |
| **Backend**        | Python 3.12, FastAPI, Uvicorn, Pydantic v2                 | Async microservices                |
| **Frontend**       | React 18 + Vite + TypeScript, TailwindCSS 4, Framer Motion | UI-first, reactive                 |
| **Spatial Tools**  | GDAL 3.6+, Shapely 2, PyProj                               | For layer ingestion + geometry ops |
| **LLM / AI**       | Provider-agnostic (OpenAI, Anthropic, Ollama, Gemini)      | Streamed reasoning                 |
| **Data Ingestion** | ogr2ogr, pdfminer, surya-ocr, embedding scripts            | Plan parsing + indexing            |
| **Proxy**          | FastAPI + aiohttp + BeautifulSoup                          | Light web fetch/download service   |

---

## 3. Environment Setup

### 3.1 System dependencies

```bash
sudo apt update && sudo apt install -y \
  build-essential cmake pkg-config curl wget git \
  postgresql-17 postgresql-17-postgis-3 postgresql-17-pgvector \
  gdal-bin libgdal-dev python3.12 python3.12-venv python3.12-dev \
  nodejs npm redis-server libssl-dev
```

### 3.2 Python environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel uvicorn fastapi pydantic sse-starlette psycopg[binary] pgvector shapely pyproj tenacity
```

### 3.3 Node environment

```bash
sudo npm install -g pnpm@latest
cd apps/frontend && pnpm i
```

---

## 4. Repository Layout

```
tpa/
├─ apps/
│  ├─ frontend/           # React (Vite + Tailwind + Framer Motion)
│  ├─ kernel/             # FastAPI reasoning kernel
│  └─ proxy/              # Light proxy for web fetch/download/extract
├─ contracts/             # Shared TS + Pydantic schemas
├─ fixtures/lpa_demo/     # Local plan, spatial, precedent data
├─ scripts/               # ETL: parse PDFs, embed, load PostGIS
├─ docker/                # optional compose for PG stack
└─ Makefile
```

---

## 5. Database Schema

Postgres 17 with PostGIS + pgvector. Enable:

```sql
CREATE EXTENSION postgis;
CREATE EXTENSION vector;
```

Tables: `policy`, `policy_para`, `policy_rel`, `policy_test`, `layer`, `layer_geom`, `precedent`.
Each policy paragraph gets a `vector(1024)` embedding.

---

## 6. Data Ingestion Pipeline

### Scripts

* `extract_paras.py` → parse PDFs to JSONL (refs, text, page).
* `embed_paras.py` → compute embeddings + store in pgvector.
* `import_layers.sh` → use ogr2ogr to load GeoPackages into PostGIS.
* `ingest_policy_graph.py`, `ingest_precedents.py`.

### Make targets

```bash
make db-init ingest-paras ingest-embeddings ingest-layers ingest-graph ingest-precedents
```

---

## 7. Light Proxy (apps/proxy)

**Purpose:** fetch policy docs or spatial data on the fly.

**Endpoints:**

* `/search { q }` → search government/LPA domains.
* `/download { url }` → download file, store cache_key.
* `/extract { cache_key }` → parse PDF/HTML, extract paragraphs.
* `/ingest { paras }` → push into DB via kernel.

**Cache:**

* Filesystem (`cache/GET_<hash>.bin`) + SQLite manifest.
* gzip-compressed JSON extracts.

**Security (allow‑listed retrieval only):**

* All outbound requests are gated by `allowed_sources.yml` (HTTPS schemes, domain allow‑list, path regex, content‑type allow‑list, max bytes).
* Proxy enforces robots.txt where present; follows redirects only if the final URL still matches the allow‑list.
* Content scanning: MIME magic check matches declared type; PDFs are text‑extracted only (no JS/attachments).
* Provenance recorded on ingest: `source_url`, `fetched_at`, `sha256`, `domain`, `robots_allowed` → table `source_provenance`.
* Rate‑limits per domain (token bucket) and per‑run fetch cap (kernel) to prevent abuse.

---

## 8. Kernel Architecture

**Modules:** Evidence, Policy, Strategy, Vision, Feedback, DM.
All share the same ContextPack + playbook framework.

**Phases:** plan → retrieve → ground → answer → reflect → emit.

**Endpoints:**

* `/reason` (SSE stream): emits `{event: token|intent|final}`.
* `/status` → simple health check.

**Trace storage:** server-side JSONL at `/var/log/tpa/traces/{session_id}.jsonl`.

**Citation source policy (module‑aware):**

* Kernel admits citations only from domains allowed **for the active module** (e.g., GOV.UK/GLA/LPA/PINS for DM & Policy). Any paragraph from a non‑permitted domain is dropped, response continues, and an audit entry is written to the trace log.

---

## 9. Services (kernel/services)

* `policy_search.py`: hybrid BM25 + vector search.
* `policy_graph.py`: policy cross-refs + exceptions.
* `docs.py`: retrieve paragraphs.
* `spatial.py`: PostGIS constraint overlay.
* `precedent.py`: curated precedent retrieval.
* `standards.py`: design/height/parking tests.
* `feedback.py`: NLP clustering for representations.

Each tool logs start/end/time and writes structured TraceEntry.

---

## 10. Reasoning Kernel (FastAPI)

Each run:

1. Build `ContextPack` from prompt + metadata.
2. Execute `Playbook` to choose tools + panels.
3. Stream reasoning tokens & intents.
4. Save TraceEntries to JSONL.

Example snippet:

```python
@app.post("/reason")
async def reason(req: ReasonRequest):
    async def eventgen():
        session_id = str(uuid4())
        trace_path = f"/var/log/tpa/traces/{session_id}.jsonl"
        async for event in agent_run(req.context, trace_path):
            yield {"event": event.type, "data": json.dumps(event.data)}
    return EventSourceResponse(eventgen())
```

---

## 11. Frontend (React)

### Goals

* Clean, planner-friendly interface.
* Dynamic panels reveal reasoning stages.
* No visible trace/log UI.

### Key libs

* TailwindCSS 4, Framer Motion, shadcn/ui.

### Panels

* EvidenceSnapshot
* ApplicablePolicies
* KeyIssuesMatrix
* Precedents
* PlanningBalance
* DraftDecision
* PolicyEditor / ConflictHeatmap
* ScenarioCompare
* VisualCompliance
* ConsultationThemes

### Controller

`translateIntent(intent) -> jsonPatch[]`, batch updates every 50ms.

**Framer Motion:** animate new panels sliding in with opacity + spring transitions.

---

## 12. Environment Variables

```
DATABASE_URL=postgresql://tpa:tpa@127.0.0.1:5432/tpa
LLM_PROVIDER=openai
LLM_MODEL=gpt-5-turbo
EMBED_MODEL=text-embedding-3-large
PROXY_BASE_URL=http://127.0.0.1:8082
PROXY_INTERNAL_TOKEN=change-me-long-random
ALLOW_ON_DEMAND_FETCH=true
ALLOWED_SOURCES_PATH=apps/proxy/allowed_sources.yml
TIMEOUT_SECONDS=60
LOG_DIR=/var/log/tpa/traces
```

---

## 13. Running the System

**Start services:**

```bash
# Proxy (no CORS, internal token required)
uvicorn apps.proxy.main:app --port 8082 --reload
# Kernel (talks to proxy with PROXY_INTERNAL_TOKEN)
uvicorn apps.kernel.main:app --port 8081 --reload
# Frontend
cd apps/frontend && pnpm run dev
```

**Reverse proxy (optional):**

```
NGINX
→ /api → :8081
→ /proxy → :8082 (internal; do not expose publicly)
→ / (frontend)
```

**Network egress hardening (recommended):**

* Container/network policy or `ufw/nftables` to restrict proxy egress to resolved IPs of allow‑listed domains only.

---

## 14. Logging & Audit

**Trace file (server):**

```
/var/log/tpa/traces/<session>.jsonl
```

Each entry:

```json
{"t":"2025-11-02T22:10Z","step":"retrieve","tool":"policy.search","input":"height near hub","out":["SP1","DM3"],"ms":91}
```

No UI visibility; accessible for post-run audits.

---

## 15. Acceptance Criteria

* All five flows work (Evidence, Policy, Strategy, Vision, Feedback, DM) **as navigable app features** (no scripted sequence).
* Live reasoning + streamed panel updates with citations.
* On‑demand fetch from proxy works; security allow‑list enforced; provenance recorded.
* Attractive, consistent UI with smooth panel choreography and responsive layout.
* Logs persisted server‑side for every run; no trace UI exposed.
* **Feature parity with zip artefacts** satisfied (see §20): routes, panels, kernels, and data paths wired.

## 16. App Navigation (no script; real app)

* Single‑page app with **top‑level module switcher**: Evidence | Policy | Strategy | Vision | Feedback | DM.
* Each module exposes: prompt input, optional site/proposal inputs, **Run** button, and a canvas where panels dynamically appear.
* A compact **Run Controls** bar (top‑right): Room‑stable/Deep‑dive toggle, budgets (steps, tokens, tools), allow web‑fetch toggle.
* Left sidebar (optional): dataset selector (fixtures bundle), site selector (saved features), recent runs.

## 17. Reliability & Safeguards

* Timeouts on each tool call; retries with jitter.
* Graceful degradation if proxy fails; continue with local corpus.
* Async caching (Redis optional).

## 18. Roadmap Extensions

* GPU/NPU inference integration.
* Multi-authority data packs.
* Live VLM (ONNXRuntime‑web) for design code analysis.
* Post‑demo: optional trace summaries for research mode.
* **Security ops:** domain/IP resolver job for egress ACLs; Prometheus counters for ALLOW/DENY; Slack/email alert on high DENY rate.

## 19. Retrieval Security (Allow‑Listed Sources)

### 19.1 Allow‑list registry

* `apps/proxy/allowed_sources.yml` defines: `schemes`, `domains`, `paths_regex`, `content_types`, `max_bytes`, `disallowed_query_keys`.
* Version‑controlled; changes via PR only.

### 19.2 Proxy guard

* All `/download` requests pass `guarded_head` + `guarded_get` checks (scheme/domain/path/content‑type/size, robots.txt, MIME magic).
* Cache stores raw bytes (`GET_<sha>.bin`) and extracted JSON (`EXTRACT_<sha>.json.gz`).

### 19.3 Provenance & audit

* Table `source_provenance(url, fetched_at, sha256, domain, robots_allowed)` populated on ingest.
* Trace JSONL notes ALLOW/DENY decisions and suppressed citations (module policy).

### 19.4 Module‑aware citation policy

* `ALLOWED_BY_MODULE` restricts which domains can appear in citations for each module (DM/Policy/Strategy/Vision/Feedback).

### 19.5 Egress controls

* Container/network ACLs or `nftables` limit proxy egress to allow‑listed IPs only; daily resolver job updates sets.

### 19.6 Quotas & abuse prevention

* Per‑domain token‑bucket rate limiting at proxy; kernel caps per‑run web fetches (default 1; deep‑dive 3).

### 19.7 Hardening

* Disable CORS on proxy; require `PROXY_INTERNAL_TOKEN` from kernel.
* Strip scripts/styles from HTML; PDF text only; UTF‑8 normalisation; limit page count.

## 20. Feature Parity Checklist (must match your zip)

* **Dashboard Diffusion UI**: intent→patch controller; panel registry; animation presets.
* **Evidence Base**: policy/doc search panel, constraint snapshot, doc viewer with paragraph focus.
* **Policy Drafter**: editable clause panel, cross‑ref inspector, conflict heatmap.
* **Strategy/Scenario**: scenario parameters, option compare cards, planning balance panel.
* **Vision & Concepts**: visual descriptors, code checklist, compliance matrix (VLM optional).
* **Feedback & Consultation**: theme clusters, counts, policy links, summary card.
* **Development Management**: applicable policies, key issues matrix, planning balance, draft decision with reasons/conditions.
* **Security**: light proxy allow‑list; module‑aware citation restrictions; provenance table; egress ACL guidance.
* **Data**: fixtures bundle path compatibility; paragraph refs and policy graph import; layer SRID = EPSG:27700.
* **App chrome**: header/footer components per your design, color scheme, typography, icons.

## 21. Frontend Route & Component Map

* **`/`** → Module switcher + workspace.
* **Shared components**: `RunControls`, `IntentStream`, `PanelHost`, `PanelCard`, `DocViewer`, `GeoChipList`.
* **Panels** (registry): `EvidenceSnapshot`, `ApplicablePolicies`, `KeyIssuesMatrix`, `Precedents`, `StandardsChecks`, `PlanningBalance`, `DraftDecision`, `PolicyEditor`, `ConflictHeatmap`, `ScenarioCompare`, `VisualCompliance`, `ConsultationThemes`.

## 22. Kernel Endpoints & Contracts (must exist)

* `POST /reason` (SSE) — streams `token|intent|final`.
* `POST /services/policy/search` → PolicyHit[]
* `GET  /services/policy/{id}/graph` → refs/exceptions/tests
* `POST /services/docs/get` → DocPara[]
* `POST /services/spatial/constraints` → Constraint[]
* `POST /services/precedent/search` → Precedent[]
* `POST /services/standards/check` → checks[]
* `POST /services/feedback/cluster` → themes[]

## 23. Zip Artefact Integration Hooks

* Place your uploaded assets under `fixtures/` and `apps/frontend/src/assets/` as needed.
* Ensure panel components read mock/sample data **and** live kernel outputs (feature‑flagged via `.env` or URL param).
* Preserve existing IDs/refs from your zip where possible to avoid breaking links in copy or screenshots.
  Demo Script

1. DM: prompt about intensification → panels build → DraftDecision.
2. Policy: check consistency → rewrite suggestion.
3. Strategy: compare two options → PlanningBalance updates.
4. Vision: image upload → VisualCompliance check.
5. Feedback: paste consultation text → ConsultationThemes appear.
6. Proxy test: ask for conservation area guidance → new citations appear.

---

## 17. Reliability & Safeguards

* Timeouts on each tool call.
* Retry logic with backoff.
* Graceful degradation if proxy fails.
* Async caching (Redis optional).

---

## 18. Roadmap Extensions

* GPU/NPU inference integration.
* Multi-authority data packs.
* Live VLM (ONNXRuntime-web) for design code analysis.
* Post-demo: explainable panel toggle (optional visibility of trace summaries).
* **Security ops:** domain/IP resolver job for egress ACLs; Prometheus counters for ALLOW/DENY; Slack/email alert on high DENY rate.

---

## 19. Retrieval Security (Allow‑Listed Sources)

### 19.1 Allow‑list registry

* `apps/proxy/allowed_sources.yml` defines: `schemes`, `domains`, `paths_regex`, `content_types`, `max_bytes`, `disallowed_query_keys`.
* Version‑controlled; changes via PR only.

### 19.2 Proxy guard

* All `/download` requests pass `guarded_head` + `guarded_get` checks (scheme/domain/path/content‑type/size, robots.txt, MIME magic).
* Cache stores raw bytes (`GET_<sha>.bin`) and extracted JSON (`EXTRACT_<sha>.json.gz`).

### 19.3 Provenance & audit

* Table `source_provenance(url, fetched_at, sha256, domain, robots_allowed)` populated on ingest.
* Trace JSONL notes ALLOW/DENY decisions and suppressed citations (module policy).

### 19.4 Module‑aware citation policy

* `ALLOWED_BY_MODULE` restricts which domains can appear in citations for each module (DM/Policy/Strategy/Vision/Feedback).

### 19.5 Egress controls

* Container/network ACLs or `nftables` limit proxy egress to allow‑listed IPs only; daily resolver job updates sets.

### 19.6 Quotas & abuse prevention

* Per‑domain token‑bucket rate limiting at proxy; kernel caps per‑run web fetches (default 1; deep‑dive 3).

### 19.7 Hardening

* Disable CORS on proxy; require `PROXY_INTERNAL_TOKEN` from kernel.
* Strip scripts/styles from HTML; PDF text only; UTF‑8 normalisation; limit page count.

---

**End of Full Developer Runbook**
