#!/bin/bash
# Stop all services for The Planner's Assistant

echo "=== Stopping The Planner's Assistant ==="
echo ""

# Stop Python services
echo "1. Stopping Python services..."
pkill -f "uvicorn.*apps/proxy" && echo "   ✅ Proxy stopped" || echo "   ⏭️  Proxy not running"
pkill -f "uvicorn.*apps/kernel" && echo "   ✅ Kernel stopped" || echo "   ⏭️  Kernel not running"
echo ""

# Stop frontend
echo "2. Stopping frontend..."
pkill -f "vite.*website" && echo "   ✅ Frontend stopped" || echo "   ⏭️  Frontend not running"
echo ""

# Stop Docker containers
echo "3. Stopping Docker containers..."
cd docker
docker compose down
cd ..
echo ""

echo "=== All Services Stopped ==="
echo ""
echo "To start again: ./start.sh"
