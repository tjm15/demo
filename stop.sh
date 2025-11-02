#!/usr/bin/env bash
# Stop all services for The Planner's Assistant

set -euo pipefail

echo "=== Stopping The Planner's Assistant ==="
echo ""

# Stop Python services (started by start.sh using python main.py)
echo "1. Stopping Python services..."
if pkill -f "apps/proxy/main.py" >/dev/null 2>&1; then
	echo "   ✅ Proxy stopped"
else
	echo "   ⏭️  Proxy not running"
fi
if pkill -f "apps/kernel/main.py" >/dev/null 2>&1; then
	echo "   ✅ Kernel stopped"
else
	echo "   ⏭️  Kernel not running"
fi
echo ""

# Stop frontend
echo "2. Stopping frontend..."
if pkill -f "vite.*website" >/dev/null 2>&1 || pkill -f "pnpm.*run dev.*website" >/dev/null 2>&1; then
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
