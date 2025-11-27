#!/usr/bin/env bash
# Stop all services for The Planner's Assistant

set -euo pipefail

echo "=== Stopping The Planner's Assistant ==="
echo ""

mkdir -p /tmp/tpa >/dev/null 2>&1 || true

# Stop Python services (started by start.sh via uvicorn with PID files)
echo "1. Stopping Python services..."

kill_pidfile() {
	local file="$1"; local name="$2"; local port="$3"
	if [ -f "$file" ]; then
		local pid
		pid=$(cat "$file" 2>/dev/null || true)
		if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
			kill "$pid" 2>/dev/null || true
			sleep 1
			if kill -0 "$pid" 2>/dev/null; then
				kill -9 "$pid" 2>/dev/null || true
			fi
			echo "   ✅ $name stopped (pid $pid)"
		else
			echo "   ⏭️  $name not running (no pid)"
		fi
		rm -f "$file" || true
	else
		# Fallback: try to kill uvicorn on port
		if command -v fuser >/dev/null 2>&1 && [ -n "$port" ]; then
			fuser -k "$port"/tcp >/dev/null 2>&1 && echo "   ✅ $name port $port freed" || echo "   ⏭️  $name not running"
		else
			echo "   ⏭️  $name not running"
		fi
	fi
}

kill_pidfile "/tmp/tpa/proxy.pid"  "Proxy"  "8082"
kill_pidfile "/tmp/tpa/kernel.pid" "Kernel" "8081"
echo ""

# Stop frontend
echo "2. Stopping frontend..."
if pkill -f "vite.*website" >/dev/null 2>&1 || pkill -f "pnpm.*run dev.*website" >/dev/null 2>&1; then
	echo "   ✅ Frontend stopped"
else
	echo "   ⏭️  Frontend not running"
fi
echo ""

# Stop Docker containers (optional) with fallback for restricted mounts
echo "3. Stopping Docker containers..."

COMPOSE_CMD=""
if command -v docker-compose >/dev/null 2>&1; then
	COMPOSE_CMD="docker-compose"
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
	COMPOSE_CMD="docker compose"
fi

if [ -n "$COMPOSE_CMD" ]; then
	set +e
	(cd docker && $COMPOSE_CMD down) > /tmp/tpa/compose_down.err 2>&1
	RC=$?
	set -e
	if [ $RC -ne 0 ]; then
		if [ -f "/tmp/tpa/compose/docker-compose.yml" ]; then
			echo "   ⚠️  Compose down failed in repo dir, trying fallback..."
			(cd /tmp/tpa/compose && $COMPOSE_CMD -f docker-compose.yml down) >/tmp/tpa/compose_down.err 2>&1 || true
			echo "   ✅ Docker stack stopped via fallback (if running)"
		else
			echo "   ⚠️  Compose down failed; see /tmp/tpa/compose_down.err"
		fi
	else
		echo "   ✅ Docker stack stopped"
	fi
else
	echo "   ⏭️  Docker not available"
fi
echo ""

echo "=== All Services Stopped ==="
echo ""
echo "To start again: ./start.sh"
