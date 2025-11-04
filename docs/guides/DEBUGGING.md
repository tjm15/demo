# Debugging Guide

## Quick Start

```bash
# Start all services (Docker + Python + Frontend)
./start.sh

# Or manually:
cd docker && docker compose up -d && cd ..
cd apps/proxy && ../../.venv/bin/uvicorn main:app --port 8082 --reload &
cd apps/kernel && ../../.venv/bin/uvicorn main:app --port 8081 --reload &
cd website && pnpm run dev
```

## Quick Status Check

### Check all services are running:
```bash
# Proxy (should show 200)
curl -s http://127.0.0.1:8082/status

# Kernel (should show 200)
curl -s http://127.0.0.1:8081/status

# Frontend (visit in browser)
http://localhost:5173
```

### Check Ollama:
```bash
# Check if Ollama is running
ps aux | grep ollama | grep -v grep

# Check Ollama API
curl http://127.0.0.1:11434/api/tags

# Start Ollama if not running
ollama serve

# Pull required models
ollama pull gpt-oss:20b
ollama pull qwen3-vl:30b
```

## Common Issues

### 1. Freezing during reasoning

**Symptom:** Frontend shows "Analyzing..." but nothing happens, even with Ollama running

**Causes:**
- Ollama process stuck/hung (high CPU, no response)
- Model too large/slow for hardware
- Previous generation didn't complete properly

**Diagnosis:**
```bash
# Check if Ollama is actually stuck
ps aux | grep ollama
# Look for high CPU% (>100%) or long runtime

# Test Ollama directly (should respond in <5 seconds)
time curl -X POST http://127.0.0.1:11434/api/generate \
  -d '{"model":"gpt-oss:20b","prompt":"test","stream":false}'
```

**Fix Option 1: Restart Ollama**
```bash
# Use the provided script
./fix-ollama.sh

# Or manually:
pkill -9 ollama
ollama serve &
sleep 3
ollama list  # Verify it's responding
```

**Fix Option 2: Use smaller model**
```bash
# Pull a faster model
ollama pull llama3.2:3b

# Use it
export LLM_MODEL=llama3.2:3b
# Restart kernel
```

**Fix Option 3: Bypass LLM for testing**
```bash
# Test the rest of the system without LLM
export DISABLE_LLM=true
cd apps/kernel && ../../.venv/bin/uvicorn main:app --port 8081 --reload

# App will show "🔧 LLM DISABLED" message but panels/citations will still work
```

**Expected behavior:**
- Without DISABLE_LLM: Falls back gracefully with message after 3-second timeout
- With DISABLE_LLM=true: Skips Ollama entirely, uses test template
- With working Ollama: Streams live tokens from model

### 2. Connection refused errors

**Symptom:** `Failed to fetch` or `ERR_CONNECTION_REFUSED`

**Causes:**
- Kernel/proxy not running
- Port conflicts

**Fix:**
```bash
# Check what's on each port
lsof -i :8081  # Kernel
lsof -i :8082  # Proxy
lsof -i :5173  # Frontend

# Kill conflicting processes
kill <PID>

# Restart services
cd apps/kernel && ../../.venv/bin/uvicorn main:app --port 8081 --reload &
cd apps/proxy && ../../.venv/bin/uvicorn main:app --port 8082 --reload &
cd website && pnpm run dev
```

### 3. Module import errors

**Symptom:** Python import errors in kernel logs

**Fix:**
```bash
cd /home/tjm/code/demo
source .venv/bin/activate
pip install -r apps/kernel/requirements.txt
pip install -r apps/proxy/requirements.txt
```

### 4. Database connection errors

**Symptom:** `psycopg` or connection errors in kernel

**Fix:**
```bash
# Check if PostgreSQL is running
systemctl status postgresql

# Start if needed
sudo systemctl start postgresql

# Check DATABASE_URL environment variable
echo $DATABASE_URL

# Set if missing (update credentials)
export DATABASE_URL="postgresql://user:pass@localhost:5432/tpa"
```

## Debugging Workflow

### Test reasoning flow:
```bash
# 1. Start all services
cd /home/tjm/code/demo

# Terminal 1: Proxy
cd apps/proxy && ../../.venv/bin/uvicorn main:app --port 8082 --reload

# Terminal 2: Kernel (shows LLM errors/logs)
cd apps/kernel && ../../.venv/bin/uvicorn main:app --port 8081 --reload

# Terminal 3: Frontend
cd website && pnpm run dev

# Terminal 4: Ollama (optional, for live reasoning)
ollama serve
```

### Monitor kernel logs:
Watch the kernel terminal for:
- `[LLM] Ollama streaming failed: ...` → Ollama issue
- `INFO: 127.0.0.1:xxxxx - "POST /reason HTTP/1.1" 200 OK` → Request succeeded
- Database errors → Check PostgreSQL

### Test endpoints directly:
```bash
# Test kernel reasoning (should return SSE stream)
curl -X POST http://127.0.0.1:8081/reason \
  -H "Content-Type: application/json" \
  -d '{"module":"dm","prompt":"test","site_data":null,"proposal_data":null}' \
  --no-buffer

# Test proxy search
curl -X POST http://127.0.0.1:8082/search \
  -H "Content-Type: application/json" \
  -d '{"q":"planning policy"}'
```

## Environment Variables

Create `.env` file in project root:
```bash
# LLM
OLLAMA_BASE_URL=http://127.0.0.1:11434
LLM_PROVIDER=ollama
LLM_MODEL=gpt-oss:20b
LLM_MODEL_VLM=qwen3-vl:30b

# Database
DATABASE_URL=postgresql://tpa:tpa@127.0.0.1:5432/tpa

# Proxy
PROXY_BASE_URL=http://127.0.0.1:8082
PROXY_INTERNAL_TOKEN=change-me-long-random
ALLOW_ON_DEMAND_FETCH=true

# Logs
LOG_DIR=./logs/traces
```

## Performance Tips

1. **Ollama GPU acceleration:**
   ```bash
   # Check if GPU is detected
   ollama list
   nvidia-smi  # For NVIDIA GPUs
   ```

2. **Reduce model size for faster testing:**
   ```bash
   # Use smaller model
   export LLM_MODEL=llama3.2:3b
   ollama pull llama3.2:3b
   ```

3. **Disable web fetch for faster iteration:**
   ```bash
   export ALLOW_ON_DEMAND_FETCH=false
   ```

## Next Steps

Once Ollama is running with models pulled:
1. Refresh frontend at http://localhost:5173/app
2. Select a module (e.g., "Development Management")
3. Enter a test prompt: "Analyse a residential extension proposal"
4. Click "Run" - should see streaming tokens and panels appearing
5. Check kernel terminal for `[LLM]` log messages

If still freezing, check browser DevTools console for specific errors.
