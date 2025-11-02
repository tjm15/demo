#!/usr/bin/env bash
# Quick start script for The Planner's Assistant demo (robust)

set -euo pipefail

# Resolve repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting The Planner's Assistant..."
echo ""

# Helper output
warn() { echo -e "\033[33m⚠️  $*\033[0m"; }
info() { echo -e "\033[36m$*\033[0m"; }
ok()   { echo -e "\033[32m$*\033[0m"; }
err()  { echo -e "\033[31m$*\033[0m"; }

# Detect docker compose command
COMPOSE_CMD=""
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
fi

# Start database stack if possible
if [ -n "$COMPOSE_CMD" ]; then
    info "📦 Starting PostgreSQL + Redis (using $COMPOSE_CMD)..."
    (cd docker && $COMPOSE_CMD up -d)
    ok "✓ Database services started"
    echo ""
    sleep 2
else
    warn "Docker Compose not found. Skipping DB startup."
    warn "Run DB manually or apply scripts/schema.sql."
    echo ""
fi

# Select Python interpreter with venv support
select_python_with_venv() {
    for CAND in python3.12 python3.11 python3.10 python3; do
        if command -v "$CAND" >/dev/null 2>&1; then
            if "$CAND" -c 'import venv, ensurepip' >/dev/null 2>&1; then
                echo "$CAND"; return 0
            fi
        fi
    done
    return 1
}

PYTHON_BIN=$(select_python_with_venv || true)
if [ -z "${PYTHON_BIN:-}" ]; then
    err "❌ No suitable Python with venv/ensurepip found."
    if command -v apt >/dev/null 2>&1; then
        warn "Install: sudo apt install python3.12-venv"
    fi
    exit 1
fi
info "🐍 Using Python: $PYTHON_BIN"

# Ensure pnpm is available (best-effort)
ensure_pnpm() {
    if command -v pnpm >/dev/null 2>&1; then return 0; fi
    warn "pnpm not found. Trying corepack..."
    if command -v corepack >/dev/null 2>&1; then
        if corepack enable >/dev/null 2>&1 && corepack prepare pnpm@latest --activate >/dev/null 2>&1; then
            ok "✓ pnpm activated via corepack"; return 0
        fi
    fi
    if command -v npm >/dev/null 2>&1; then
        warn "Installing pnpm globally (may require sudo)"
        npm install -g pnpm >/dev/null 2>&1 || return 1
        ok "✓ pnpm installed globally"; return 0
    fi
    return 1
}
ensure_pnpm || true

echo "🔧 Setting up Python environments..."

# Proxy venv
if [ ! -d "apps/proxy/.venv" ]; then
    info "  Creating proxy venv..."
    (cd apps/proxy && "$PYTHON_BIN" -m venv .venv && .venv/bin/pip install -q --upgrade pip && .venv/bin/pip install -q -r requirements.txt)
fi

# Kernel venv
if [ ! -d "apps/kernel/.venv" ]; then
    info "  Creating kernel venv..."
    (cd apps/kernel && "$PYTHON_BIN" -m venv .venv && .venv/bin/pip install -q --upgrade pip && .venv/bin/pip install -q -r requirements.txt)
fi

ok "✓ Python environments ready"
echo ""

# Frontend deps
info "📦 Installing frontend dependencies..."
if [ -d "website" ] && command -v pnpm >/dev/null 2>&1; then
    (cd website && [ -d node_modules ] || pnpm install --silent)
fi
ok "✓ Frontend dependencies ready"
echo ""

# Create .env if missing
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    info "📝 Creating .env from template..."
    cp .env.example .env || true
    ok "✓ Edit .env to configure API keys"
    echo ""
fi

# Create log dir
mkdir -p /tmp/tpa/traces

ok "✅ Setup complete!"
echo ""
info "🎬 Starting services..."
echo "  Proxy:    http://127.0.0.1:8082"
echo "  Kernel:   http://127.0.0.1:8081"
echo "  Frontend: http://127.0.0.1:5173"
echo ""

# Kill background on exit
trap 'kill $(jobs -p) 2>/dev/null || true' EXIT

# Start proxy
bash -lc "cd apps/proxy && . .venv/bin/activate && nohup uvicorn main:app --port 8082 --reload > /tmp/tpa/proxy.log 2>&1 & echo \$!" > /tmp/tpa/proxy.pid
sleep 1

# Start kernel
bash -lc "cd apps/kernel && . .venv/bin/activate && nohup uvicorn main:app --port 8081 --reload > /tmp/tpa/kernel.log 2>&1 & echo \$!" > /tmp/tpa/kernel.pid
sleep 1

# Start frontend
if command -v pnpm >/dev/null 2>&1; then
    (cd website && pnpm run dev &)
else
    warn "pnpm not available; start frontend manually: cd website && pnpm run dev"
fi

echo ""
ok "✨ All services started (logs in /tmp/tpa/*.log)"
echo "Open your browser to: http://localhost:5173"
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for background jobs
wait || true
