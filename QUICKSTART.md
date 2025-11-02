# Quick Start Guide - The Planner's Assistant

Get TPA running in under 5 minutes!

## 🚀 Prerequisites

```bash
# Ubuntu 22.04
sudo apt update && sudo apt install -y \
  python3.12 python3.12-venv \
  docker.io docker-compose \
  nodejs npm

# Install pnpm
sudo npm install -g pnpm
```

## ⚡ Fast Track (Automated)

```bash
# Clone and start everything
git clone <repo-url> tpa
cd tpa
chmod +x start.sh
./start.sh
```

This will:
1. Start PostgreSQL + Redis (Docker)
2. Load sample data (3 policies, 6 paragraphs, 3 precedents)
3. Set up Python virtual environments
4. Install dependencies
5. Start proxy (8082), kernel (8081), frontend (5173)
6. Open http://localhost:5173 in your browser

## 🎯 Manual Start (Step-by-Step)

### 1. Start Database

```bash
cd docker
docker-compose up -d

# Wait 10 seconds for PostgreSQL to initialize
sleep 10

# Verify it's running
docker ps | grep tpa-postgres
# Should show container running on port 5432
```

### 2. Load Sample Data

```bash
cd ../scripts

# Create Python environment and install dependencies
python3.12 -m venv .venv
source .venv/bin/activate
pip install psycopg sentence-transformers torch

# Load 3 sample policies with embeddings (6 paragraphs total)
python3.12 ingest_policy_graph.py ../fixtures/lpa_demo/policy_graph.json

# Load 3 sample precedents with embeddings
python3.12 ingest_precedents.py ../fixtures/lpa_demo/precedents.jsonl

# Verify data loaded
docker exec tpa-postgres psql -U tpa -d tpa -c "SELECT title FROM policy;"
# Should show: Local Plan 2024, London Plan 2021, NPPF 2023

docker exec tpa-postgres psql -U tpa -d tpa -c "SELECT COUNT(*) FROM policy_para WHERE embedding IS NOT NULL;"
# Should show: 6
```

### 3. Start Proxy Service

```bash
# Terminal 1
cd ../apps/proxy
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8082 --reload

# Should see: "Application startup complete"
# Test: curl http://127.0.0.1:8082/status
```

### 4. Start Kernel Service

```bash
# Terminal 2
cd ../apps/kernel
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8081 --reload

# Should see: "Application startup complete"
# Test: curl http://127.0.0.1:8081/status
```

### 5. Start Frontend

```bash
# Terminal 3
cd ../website
pnpm install
pnpm run dev

## 📖 Using the Demo

### 1. Open the App

Navigate to http://localhost:5173/#/app

You'll see the **Welcome Screen** with 6 tool cards:
- 🗺️ Evidence Base
- 🎨 Vision & Concepts
- 📋 Policy Drafter
- 📊 Strategy Modeler
- 📍 Site Assessment
- 💬 Feedback Analysis

### 2. Select a Tool

Click any tool card. The grid will fade out and the tool interface will appear with:
- Sticky header with "Back to Tools" button
- Prompt textarea on the left
- Example prompts (click to auto-fill)
- Results panel on the right

### 3. Try Example Queries

**Site Assessment (DM)**
```
45 unit residential development, 6 storeys, near conservation area
```
Expected panels: Applicable Policies (H1.1, H1.2), Key Issues Matrix, Precedents, Planning Balance, Draft Decision

**Policy Drafter**
```
Review housing policy H1 for consistency with London Plan
```
Expected panels: Policy Editor, Conflict Heatmap

### 4. Navigate Back

Click "Back to Tools" in the header to return to the module grid. All state (prompt, coordinates) is reset.

## 🧪 Testing Endpoints

### Health Checks
```bash
curl http://127.0.0.1:8082/status  # Proxy
curl http://127.0.0.1:8081/status  # Kernel
```

### Reasoning Stream
```bash
curl -X POST http://127.0.0.1:8081/reason \
  -H "Content-Type: application/json" \
  -d '{
    "module": "dm",
    "prompt": "Test development",
    "run_mode": "stable",
    "allow_web_fetch": false
  }'
```

### Policy Search
```bash
curl -X POST http://127.0.0.1:8081/services/policy/search \
  -H "Content-Type: application/json" \
  -d '{"query": "housing", "limit": 5}'
```

## 📊 Expected Panel Flow

### DM Module
1. Applicable Policies (SP1, DM3, H1)
2. Key Issues Matrix (design, transport, heritage)
3. Precedents (similar appeals)
4. Planning Balance (benefits vs harms)
5. Draft Decision (recommendation + reasons)

### Policy Module
1. Policy Editor (editable text)
2. Conflict Heatmap (policy conflicts)

### Strategy Module
1. Scenario Compare (options with scores)
2. Planning Balance (sustainability metrics)

### Vision Module
1. Visual Compliance (design checklist)

### Feedback Module
1. Consultation Themes (clustered responses)

### Evidence Module
1. Evidence Snapshot (constraints + policy count)
2. Applicable Policies

## 🛠️ Troubleshooting

### "Docker compose not found" (WSL / Desktop)
- If you see an error about `docker-compose` not found, the script now tries `docker compose` automatically.
- On WSL, enable Docker Desktop → Settings → Resources → WSL integration for your distro.
- Alternatively, run the DB stack manually:
```bash
cd docker
docker compose up -d   # or: docker-compose up -d
```

### "Python venv/ensurepip missing"
- If the script reports: "No suitable Python with venv/ensurepip found" or "ensurepip is not available",
install the venv package for your Python version (Ubuntu):
```bash
sudo apt update
sudo apt install -y python3.12-venv  # or python3.11-venv / python3.10-venv
```
- Then re-run:
```bash
./start.sh
```

### "Cannot connect to kernel"
- Check kernel is running: `curl http://127.0.0.1:8081/status`
- Check logs: `tail -f /tmp/tpa/kernel.log`
- Verify CORS allows localhost:5173

### "Database connection failed"
- Start PostgreSQL: `cd docker && docker-compose up -d`
- Check connection: `psql postgresql://tpa:tpa@127.0.0.1:5432/tpa`
- Initialize schema: `psql -f scripts/schema.sql`

### "Panels not appearing"
- Open browser console (F12)
- Check Network tab for SSE connection
- Verify kernel logs show reasoning events

### "pnpm not found"
- The script will try Corepack to activate pnpm; if that fails, install manually:
```bash
npm install -g pnpm
```
- Or install Node.js with Corepack (Node 18+ recommended) and re-run `./start.sh`.

### "Module not responding"
- Check playbook is defined for module in `apps/kernel/modules/playbook.py`
- Verify mock data generation for panel types
- Check trace logs in `/tmp/tpa/traces/`

## 🔧 Configuration

### Enable Real LLM (OpenAI)
```bash
# Edit .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4-turbo
```

### Load Real Data
```bash
# Extract policy docs
python scripts/extract_paras.py path/to/policies/*.pdf

# Compute embeddings (requires OpenAI API)
python scripts/embed_paras.py

# Load spatial layers
bash scripts/import_layers.sh path/to/layers/*.gpkg

# Ingest policy graph
python scripts/ingest_policy_graph.py

# Load precedents
python scripts/ingest_precedents.py
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `apps/kernel/main.py` | FastAPI reasoning engine |
| `apps/proxy/main.py` | Secure retrieval service |
| `website/components/app/AppWorkspace.tsx` | Main UI |
| `website/hooks/useReasoningStream.ts` | SSE client |
| `apps/kernel/modules/playbook.py` | Reasoning flows |
| `scripts/schema.sql` | Database schema |

## 🎨 Customization

### Add New Panel
1. Create `website/components/app/panels/MyPanel.tsx`
2. Add to `PANEL_COMPONENTS` in `PanelHost.tsx`
3. Emit from playbook: `yield {"type": "intent", "data": {"action": "show_panel", "panel": "my_panel"}}`

### Add New Module
1. Add to `MODULES` array in `AppWorkspace.tsx`
2. Add reasoning flow in `execute_playbook()` in `playbook.py`
3. Add mock data generator in `generate_mock_data()`

### Modify Styling
- Theme colors: `website/constants.ts`
- TailwindCSS classes throughout components
- Framer Motion animations in panel transitions

## 📞 Support

See full documentation in:
- `README.md` - Complete setup guide
- `PROJECT_SUMMARY.md` - Implementation overview
- `AGENTS.md` - Original specification
