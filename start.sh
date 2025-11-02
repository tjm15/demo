#!/bin/bash
# Quick start script for The Planner's Assistant demo

set -e

echo "🚀 Starting The Planner's Assistant..."
echo ""

# Check if docker is available
if command -v docker &> /dev/null; then
    # Prefer 'docker compose' if available; fallback to 'docker-compose'
    #!/usr/bin/env bash
    # Quick start script for The Planner's Assistant demo (robust)

    set -euo pipefail

    # Resolve repo root
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"

    echo "� Starting The Planner's Assistant..."
    echo ""

    # Helper: print warning
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
        warn "If you're on WSL, enable Docker Desktop WSL integration or install docker-compose plugin."
        warn "You can also run Postgres manually and apply scripts/schema.sql."
        echo ""
    fi

    # Select Python interpreter
    select_python_with_venv() {
        for CAND in python3.12 python3.11 python3.10 python3; do
            if command -v "$CAND" >/dev/null 2>&1; then
                # ensure venv and ensurepip are available for this interpreter
                if "$CAND" -c 'import venv, ensurepip' >/dev/null 2>&1; then
                    echo "$CAND"
                    return 0
                fi
            fi
        done
        return 1
    }

    PYTHON_BIN=$(select_python_with_venv || true)
    if [ -z "${PYTHON_BIN:-}" ]; then
        err "❌ No suitable Python with venv/ensurepip found."
        if command -v apt >/dev/null 2>&1; then
            warn "Install the venv package for your Python version, e.g.:"
            warn "  sudo apt install python3.12-venv    # or python3.11-venv / python3.10-venv"
        fi
        exit 1
    fi
    info "🐍 Using Python: $PYTHON_BIN (venv available)"

    # Ensure pnpm is available
    ensure_pnpm() {
        if command -v pnpm >/dev/null 2>&1; then
            return 0
        fi
        warn "pnpm not found. Trying to activate via corepack..."
        if command -v corepack >/dev/null 2>&1; then
            if corepack enable >/dev/null 2>&1 && corepack prepare pnpm@latest --activate >/dev/null 2>&1; then
                ok "✓ pnpm activated via corepack"
                return 0
            fi
        fi
        if command -v npm >/dev/null 2>&1; then
            warn "Falling back to npm -g install (may require privileges)"
            if npm install -g pnpm >/dev/null 2>&1; then
                ok "✓ pnpm installed globally"
                return 0
            else
                warn "Couldn't install pnpm automatically. Install manually: npm i -g pnpm"
            fi
        else
            warn "npm not found. Please install Node.js and pnpm."
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
    if [ -d "website" ]; then
        (cd website && if [ ! -d node_modules ]; then if command -v pnpm >/dev/null 2>&1; then pnpm install --silent; else warn "pnpm missing; skipping install (run manually)"; fi; fi)
    fi
    ok "✓ Frontend dependencies ready"
    echo ""

    # Create .env if missing
    if [ ! -f ".env" ]; then
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
    echo ""
    echo "  Proxy:    http://127.0.0.1:8082"
    echo "  Kernel:   http://127.0.0.1:8081"
    echo "  Frontend: http://127.0.0.1:5173"
    echo ""
    echo "Press Ctrl+C to stop all services"
    echo ""

    # Kill background on exit
    trap 'kill $(jobs -p) 2>/dev/null || true' EXIT

    # Start proxy
    (cd apps/proxy && .venv/bin/python main.py > /tmp/tpa/proxy.log 2>&1 &)
    sleep 1

    # Start kernel
    (cd apps/kernel && .venv/bin/python main.py > /tmp/tpa/kernel.log 2>&1 &)
    sleep 1

    # Start frontend
    if command -v pnpm >/dev/null 2>&1; then
        (cd website && pnpm run dev &)
    else
        warn "pnpm not available; start frontend manually: cd website && pnpm run dev"
    fi

    echo ""
    ok "✨ All services started (logs in /tmp/tpa/*.log)"
    echo ""
    echo "Logs:"
    echo "  Proxy:  tail -f /tmp/tpa/proxy.log"
    echo "  Kernel: tail -f /tmp/tpa/kernel.log"
    echo ""
    echo "Open your browser to: http://localhost:5173"
    echo ""

    # Wait for any process to exit
    wait || true
    cd website
    pnpm run dev &
    FRONTEND_PID=$!
    cd ..
else
    echo "💡 Frontend not started (pnpm missing). UI will be unavailable until pnpm is installed."
fi

echo ""
echo "✨ All services running!"
echo ""
echo "Logs:"
echo "  Proxy:  tail -f /tmp/tpa/proxy.log"
echo "  Kernel: tail -f /tmp/tpa/kernel.log"
echo ""
echo "Open your browser to: http://localhost:5173"
echo ""

# Wait for any process to exit
wait
