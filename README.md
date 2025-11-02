# The Planner's Assistant - Full Demo

A fully functioning AI-powered planning assistant for urban development and policy analysis.

## 🎯 Overview

The Planner's Assistant (TPA) is a production-ready application that provides AI-powered reasoning for:

- **Development Management (DM)**: Assess planning applications with policy analysis, precedents, and draft decisions
- **Policy Drafting**: Create and review planning policies with consistency checks
- **Strategic Planning**: Compare development scenarios and spatial strategies  
- **Vision & Concepts**: Analyze design compliance with local codes
- **Consultation Feedback**: Cluster and analyze public consultation responses
- **Evidence Base**: Site analysis with spatial constraints and policy mapping

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │  React + Vite + TailwindCSS + Framer Motion
│  (Port 5173)│  Real-time streaming UI with animated panels
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Kernel    │  FastAPI reasoning engine
│  (Port 8081)│  Module-aware playbooks, SSE streaming
└──────┬──────┘
       │
       ├─────────────┐
       ▼             ▼
┌──────────┐  ┌───────────┐
│  Proxy   │  │ PostgreSQL│  PostGIS + pgvector
│(Port 8082)│  │  + Redis  │  Spatial + vector search
└──────────┘  └───────────┘
```

## 🚀 Quick Start

### Prerequisites (Ubuntu 22.04)

```bash
# System dependencies
sudo apt update && sudo apt install -y \
  build-essential python3.12 python3.12-venv \
  postgresql-17 postgresql-17-postgis-3 postgresql-17-pgvector \
  nodejs npm redis-server

# Node package manager
sudo npm install -g pnpm
```

### Database Setup

```bash
# Start PostgreSQL with Docker (recommended - includes PostGIS + pgvector)
cd docker && docker-compose up -d

# Verify extensions loaded
docker exec tpa-postgres psql -U tpa -d tpa -c "SELECT * FROM pg_extension;"
# Should show: postgis, vector

# OR initialize manually (requires custom Dockerfile)
sudo -u postgres psql -f scripts/schema.sql
```

### Load Sample Data

```bash
# From project root
cd scripts

# Load 3 sample policies with 6 paragraphs (includes embeddings)
python3.12 ingest_policy_graph.py ../fixtures/lpa_demo/policy_graph.json

# Load 3 sample precedents (includes embeddings)
python3.12 ingest_precedents.py ../fixtures/lpa_demo/precedents.jsonl

# Verify data
docker exec tpa-postgres psql -U tpa -d tpa -c "SELECT COUNT(*) FROM policy_para;"
# Should return 6
```

### Backend Services

```bash
# Terminal 1: Proxy Service
cd apps/proxy
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8082 --reload

# Terminal 2: Kernel Service  
cd apps/kernel
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8081 --reload
```

### Frontend

```bash
# Terminal 3: Frontend
cd website
pnpm install
pnpm run dev
# Open http://localhost:5173
```

### Quick Test

```bash
# Test E2E flow
curl -X POST http://127.0.0.1:8081/reason \
  -H "Content-Type: application/json" \
  -d '{
    "module":"dm",
    "prompt":"residential development",
    "run_mode":"stable",
    "allow_web_fetch":false
  }'
# Should return SSE stream with policy hits (H1.1, H1.2) and precedents
```

## 📋 Features

### ✅ Implemented

- **6 Reasoning Modules**: Evidence, Policy, Strategy, Vision, Feedback, DM
- **11 Dynamic Panels**: Animated UI components that appear based on reasoning flow
- **Dynamic Module Switching**: Tool selection grid hides when tool is active; "Back to Tools" button returns to grid
- **Streaming Reasoning**: Real-time SSE with token-by-token output
- **Security-First Proxy**: Allow-listed retrieval with provenance tracking
- **Module-Aware Citations**: Domain restrictions per reasoning context
- **PostGIS Integration**: Spatial constraint analysis with EPSG:27700
- **Vector Search**: pgvector embeddings for policy/precedent retrieval (all-MiniLM-L6-v2, 1024-d)
- **Hybrid Search**: Combined text (BM25) + vector similarity for policy/precedent ranking
- **Production UI**: Local Tailwind CSS build (no CDN) + Framer Motion animations
- **E2E Testing**: Playwright tests for UI flows
- **Optimized Development**: VS Code settings to prevent freezing (file watcher limits, editor limits)

### 🎨 UI Panels

| Panel | Module | Description |
|-------|--------|-------------|
| Evidence Snapshot | Evidence | Site constraints + applicable policies |
| Applicable Policies | DM, Evidence | Relevant policies with relevance scores |
| Key Issues Matrix | DM | Material considerations with status |
| Precedents | DM | Similar planning appeals |
| Planning Balance | DM, Strategy | Benefits vs harms assessment |
| Draft Decision | DM | Recommendation with reasons/conditions |
| Policy Editor | Policy | Editable policy text with suggestions |
| Conflict Heatmap | Policy | Inter-policy conflicts |
| Scenario Compare | Strategy | Strategic option comparison |
| Visual Compliance | Vision | Design code checklist |
| Consultation Themes | Feedback | Clustered public responses |

## 🔒 Security

### Allow-Listed Retrieval

All web fetches are gated by `apps/proxy/allowed_sources.yml`:

- HTTPS-only scheme enforcement
- Domain allow-list (GOV.UK, GLA, PINS, etc.)
- Path regex matching
- Content-type validation
- Max file size limits
- robots.txt compliance

### Module-Aware Citations

Citations are filtered by module context:

- **DM/Policy**: GOV.UK, GLA, LPA, PINS only
- **Strategy/Vision**: GOV.UK, GLA only  
- **Feedback**: GOV.UK, GLA, Planning Portal

Violations are logged to trace files for audit.

### Provenance Tracking

Every fetched document is recorded in `source_provenance` table:

- Source URL + fetch timestamp
- SHA-256 hash for integrity
- Domain + robots.txt status
- Ingest count

## 📊 Data Ingestion

```bash
# Extract paragraphs from PDFs
python scripts/extract_paras.py fixtures/lpa_demo/policies/*.pdf

# Compute embeddings
python scripts/embed_paras.py --model text-embedding-3-large

# Load spatial layers (GeoPackage → PostGIS)
bash scripts/import_layers.sh fixtures/lpa_demo/layers/*.gpkg

# Ingest policy graph
python scripts/ingest_policy_graph.py fixtures/lpa_demo/graph.json

# Load precedents
python scripts/ingest_precedents.py fixtures/lpa_demo/precedents.jsonl
```

## 🎮 Usage Examples

### Development Management

```
1. Open http://localhost:5173/#/app
2. Click "Site Assessment" card
3. Enter prompt: "Residential development of 45 units on brownfield site, 
   6 storeys, located 200m from conservation area"
4. Click "Run Analysis"

Expected Output:
→ Applicable Policies panel (H1.1, H1.2 from sample data)
→ Key Issues Matrix (height, density, parking)
→ Precedents (APP/2023/1234, APP/2024/0123 from sample data)
→ Planning Balance (benefits vs harms)
→ Draft Decision (approval with conditions)
→ AI Reasoning stream (token-by-token explanation)
```

### Policy Drafting

```
1. Click "Policy Drafter" card
2. Enter prompt: "Review housing policy H1 for consistency with London Plan density ranges"
3. Click "Run Analysis"

Expected Output:
→ Policy Editor (editable text)
→ Conflict Heatmap (H1 ↔ ENV3 moderate conflict)
```

### Strategic Planning

```
1. Click "Strategy Modeler" card
2. Enter prompt: "Compare urban extension vs brownfield intensification 
   for 2,500 homes"
3. Click "Run Analysis"

Expected Output:
→ Scenario Compare (Option A vs B with scores)
→ Planning Balance (sustainability metrics)
```

### Returning to Module Grid

- Click "Back to Tools" button in sticky header
- Module grid fades in with smooth animation
- All tool state (prompt, coordinates) is reset

## 🛠️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://tpa:tpa@127.0.0.1:5432/tpa

# LLM (optional - uses mock data by default)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo
OPENAI_API_KEY=your-key-here

# Proxy
PROXY_INTERNAL_TOKEN=your-random-token-here
ALLOW_ON_DEMAND_FETCH=true

# Logs
LOG_DIR=/tmp/tpa/traces
```

## 📁 Project Structure

```
tpa/
├── apps/
│   ├── kernel/          # FastAPI reasoning engine
│   │   ├── modules/     # Context, playbook, trace
│   │   └── services/    # Policy, spatial, precedent, etc.
│   └── proxy/           # Secure web retrieval service
├── website/             # React frontend
│   ├── components/
│   │   └── app/         # Workspace, panels, controls
│   ├── hooks/           # useReasoningStream
│   └── pages/           # AppPage with workspace
├── contracts/           # Shared TS/Pydantic schemas
├── fixtures/lpa_demo/   # Sample data
├── scripts/             # ETL scripts
├── docker/              # PostgreSQL + Redis compose
└── Makefile             # Build targets
```

## 🧪 Testing

### Backend Health Checks

```bash
# Test proxy health
curl http://127.0.0.1:8082/status

# Test kernel health  
curl http://127.0.0.1:8081/status

# Test reasoning stream (should return policies H1.1, H1.2 and precedents)
curl -X POST http://127.0.0.1:8081/reason \
  -H "Content-Type: application/json" \
  -d '{
    "module":"dm",
    "prompt":"residential development",
    "run_mode":"stable",
    "allow_web_fetch":false
  }'
```

### Frontend E2E Tests

```bash
cd website

# Run all Playwright tests
pnpm test:e2e

# Run in UI mode (interactive)
pnpm test:e2e -- --ui

# Run specific test
pnpm test:e2e tests/e2e/app.spec.ts

# Expected: 7/7 tests passing
# - Module grid renders
# - Tool selection works
# - Example prompts populate textarea
# - Back button navigation
# - Empty panel state displays correctly
```

### Manual UI Testing

1. **Module Switching**:
   - Grid should show 6 tool cards
   - Clicking a card should hide grid and show tool interface
   - "Back to Tools" button should return to grid

2. **Example Prompts**:
   - Each tool should show 2 example prompts
   - Clicking an example should populate the textarea

3. **Site Coordinates** (Evidence Base & Site Assessment only):
   - "Add Site Coordinates" button should appear
   - Clicking should reveal lat/lng inputs with smooth animation
   - "Hide Site Coordinates" should collapse inputs

4. **Settings Panel**:
   - "Settings" button should toggle settings panel
   - Fast/Deep mode toggle should work
   - Web fetch toggle should work

5. **Streaming**:
   - "Run Analysis" should trigger SSE connection
   - "AI Reasoning" panel should appear with streaming text
   - Result panels should appear dynamically
   - Button should show "Analyzing..." during run

## 📈 Roadmap

- [ ] GPU/NPU inference (ONNX Runtime)
- [ ] Multi-authority data packs
- [ ] Live VLM for design analysis
- [ ] Advanced spatial analysis (viewsheds, shadows)
- [ ] User authentication + sessions
- [ ] Export to Word/PDF reports
- [ ] API documentation (OpenAPI)

## 📝 License

**GNU Affero General Public License v3.0 (AGPL-3.0)**

This project is licensed under AGPLv3 to ensure transparency and community benefit in AI-assisted planning:

### Why AGPL-3.0?

- **Network Copyleft**: Modified versions deployed as web services must make source code available to users
- **Public Accountability**: Planning decisions affect communities and must be auditable
- **Prevents SaaS Loophole**: Unlike GPL, AGPL requires source disclosure even for network-only deployments
- **Collaborative Development**: Forces improvements to be contributed back to the commons
- **Data Sovereignty**: Local authorities retain control over planning logic and data

### What This Means

✅ **You CAN:**
- Use commercially (charge for hosting, support, training)
- Modify and deploy internally
- Offer as a web service (with source disclosure)
- Integrate with proprietary systems via APIs

❌ **You MUST:**
- Provide source code to all network users of modified versions
- License modifications under AGPLv3
- Preserve copyright notices

See [LICENSE](LICENSE) for full terms and detailed explanation.

For alternative licensing (e.g., Open Government License), contact the maintainers.

## 🤝 Contributing

This is a demonstration project. For production deployment:

1. Configure LLM provider (OpenAI, Anthropic, etc.)
2. Load real policy/spatial data for your authority
3. Harden network egress (firewall rules)
4. Enable authentication + HTTPS
5. Set up monitoring (Prometheus + Grafana)

## 🐛 Troubleshooting

**Frontend can't connect to kernel**
- Check CORS settings in `apps/kernel/main.py` (should allow `http://localhost:5173`)
- Verify kernel is running: `curl http://127.0.0.1:8081/status`
- Check `VITE_KERNEL_URL` in `website/.env.local`

**Proxy download fails**
- Check `allowed_sources.yml` for domain
- Verify HTTPS and valid SSL certificate
- Check proxy logs for security violations
- Ensure `PROXY_INTERNAL_TOKEN` matches between kernel and proxy

**Database connection error**
- Ensure PostgreSQL is running: `docker-compose ps`
- Check `DATABASE_URL` in `.env`
- Verify PostGIS + pgvector extensions: `docker exec tpa-postgres psql -U tpa -d tpa -c "SELECT * FROM pg_extension;"`
- Check logs: `docker logs tpa-postgres`

**Panels not appearing**
- Open browser console (F12) for errors
- Check kernel trace logs in `LOG_DIR` (default: `/tmp/tpa/traces/`)
- Verify SSE connection in Network tab (should see `/reason` with `text/event-stream`)
- Ensure sample data is loaded: `docker exec tpa-postgres psql -U tpa -d tpa -c "SELECT COUNT(*) FROM policy_para;"`

**No policies/precedents returned**
- Verify embeddings are loaded: `docker exec tpa-postgres psql -U tpa -d tpa -c "SELECT COUNT(*) FROM policy_para WHERE embedding IS NOT NULL;"`
- Check kernel imports pgvector correctly: look for "register_vector" in startup logs
- Try simpler query: "residential" should match H1.1 and H1.2

**VS Code freezing**
- Settings already configured in `.vscode/settings.json`
- If still freezing, disable extensions: `code --disable-extensions`
- Clear workspace storage: `rm -rf ~/.config/Code/User/workspaceStorage/*`
- Restart VS Code

**Frontend not hot-reloading**
- Clear Vite cache: `rm -rf website/node_modules/.vite`
- Restart dev server: `pnpm dev`
- Check for TypeScript errors: `pnpm run build`

**Tailwind styles not applying**
- Ensure local build is configured (not CDN): check `website/postcss.config.js` exists
- Rebuild: `cd website && pnpm build`
- Check browser console for CSS loading errors

---

**Built with ❤️ for urban planners everywhere**
