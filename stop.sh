#!/usr/bin/env bash
# Stop all services for The Planner's Assistant

set -euo pipefail

echo "=== Stopping The Planner's Assistant ==="
echo ""

# Stop Python services (started by start.sh using python main.py)
echo "1. Stopping Python services..."

# Try graceful kill first, then force kill if needed
PROXY_STOPPED=false
KERNEL_STOPPED=false

# Kill proxy using PID file if available
if [ -f "/tmp/tpa/proxy.pid" ]; then
	PROXY_PID=$(cat /tmp/tpa/proxy.pid 2>/dev/null || echo "")
	if [ -n "$PROXY_PID" ] && kill -0 "$PROXY_PID" 2>/dev/null; then
		kill "$PROXY_PID" 2>/dev/null && sleep 1
		# Force kill if still running
		if kill -0 "$PROXY_PID" 2>/dev/null; then
			kill -9 "$PROXY_PID" 2>/dev/null
		fi
		PROXY_STOPPED=true
		rm -f /tmp/tpa/proxy.pid
	fi
fi

# Fallback: kill by port pattern
if [ "$PROXY_STOPPED" = false ] && pgrep -f "uvicorn.*main:app.*--port 8082" >/dev/null 2>&1; then
	pkill -f "uvicorn.*main:app.*--port 8082" && sleep 1
	# Force kill if still running
	if pgrep -f "uvicorn.*main:app.*--port 8082" >/dev/null 2>&1; then
		pkill -9 -f "uvicorn.*main:app.*--port 8082"
	fi
	PROXY_STOPPED=true
	rm -f /tmp/tpa/proxy.pid
fi

# Kill kernel using PID file if available
if [ -f "/tmp/tpa/kernel.pid" ]; then
	KERNEL_PID=$(cat /tmp/tpa/kernel.pid 2>/dev/null || echo "")
	if [ -n "$KERNEL_PID" ] && kill -0 "$KERNEL_PID" 2>/dev/null; then
		kill "$KERNEL_PID" 2>/dev/null && sleep 1
		# Force kill if still running
		if kill -0 "$KERNEL_PID" 2>/dev/null; then
			kill -9 "$KERNEL_PID" 2>/dev/null
		fi
		KERNEL_STOPPED=true
		rm -f /tmp/tpa/kernel.pid
	fi
fi

# Fallback: kill by port pattern
if [ "$KERNEL_STOPPED" = false ] && pgrep -f "uvicorn.*main:app.*--port 8081" >/dev/null 2>&1; then
	pkill -f "uvicorn.*main:app.*--port 8081" && sleep 1
	# Force kill if still running
	if pgrep -f "uvicorn.*main:app.*--port 8081" >/dev/null 2>&1; then
		pkill -9 -f "uvicorn.*main:app.*--port 8081"
	fi
	KERNEL_STOPPED=true
	rm -f /tmp/tpa/kernel.pid
fi

if [ "$PROXY_STOPPED" = true ]; then
	echo "   ✅ Proxy stopped"
else
	echo "   ⏭️  Proxy not running"
fi

if [ "$KERNEL_STOPPED" = true ]; then
	echo "   ✅ Kernel stopped"
else
	echo "   ⏭️  Kernel not running"
fi
echo ""

# Stop frontend
echo "2. Stopping frontend..."
FRONTEND_STOPPED=false

# Kill all vite processes in website directory
if pgrep -f "vite.*website" >/dev/null 2>&1; then
	pkill -f "vite.*website" && sleep 1
	# Force kill if still running
	if pgrep -f "vite.*website" >/dev/null 2>&1; then
		pkill -9 -f "vite.*website"
	fi
	FRONTEND_STOPPED=true
fi

# Kill pnpm dev processes
if pgrep -f "pnpm.*dev" >/dev/null 2>&1; then
	pkill -f "pnpm.*dev" && sleep 1
	if pgrep -f "pnpm.*dev" >/dev/null 2>&1; then
		pkill -9 -f "pnpm.*dev"
	fi
	FRONTEND_STOPPED=true
fi

if [ "$FRONTEND_STOPPED" = true ]; then
	echo "   ✅ Frontend stopped"
else
	echo "   ⏭️  Frontend not running"
fi
echo ""

# Stop Docker containers (optional)
echo "3. Stopping Docker containers..."
if command -v docker-compose >/dev/null 2>&1; then
	(cd docker && docker-compose down) || true
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
	(cd docker && docker compose down) || true
else
	echo "   ⏭️  Docker not available"
fi
echo ""

echo "=== All Services Stopped ==="
echo ""
echo "To start again: ./start.sh"
