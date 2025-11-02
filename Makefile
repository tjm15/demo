.PHONY: help install-deps db-init run-proxy run-kernel run-frontend dev clean

help:
	@echo "The Planner's Assistant - Make targets"
	@echo ""
	@echo "  install-deps    Install system dependencies (Ubuntu 22.04)"
	@echo "  db-init         Initialize PostgreSQL database"
	@echo "  run-proxy       Start proxy service"
	@echo "  run-kernel      Start kernel service"
	@echo "  run-frontend    Start frontend dev server"
	@echo "  dev             Start all services (tmux recommended)"
	@echo "  clean           Clean cache and temp files"

install-deps:
	@echo "Installing system dependencies..."
	sudo apt update
	sudo apt install -y build-essential python3.12 python3.12-venv nodejs npm
	sudo npm install -g pnpm

db-init:
	@echo "Initializing database..."
	@echo "Please ensure PostgreSQL 17 with PostGIS is running"
	@echo "Run: sudo -u postgres psql -f scripts/schema.sql"

run-proxy:
	@echo "Starting proxy service on port 8082..."
	cd apps/proxy && python3.12 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && python main.py

run-kernel:
	@echo "Starting kernel service on port 8081..."
	cd apps/kernel && python3.12 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && python main.py

run-frontend:
	@echo "Starting frontend on port 5173..."
	cd website && pnpm install && pnpm run dev

dev:
	@echo "Starting all services..."
	@echo "Recommended: Use tmux or run in separate terminals"
	@echo "  Terminal 1: make run-proxy"
	@echo "  Terminal 2: make run-kernel"
	@echo "  Terminal 3: make run-frontend"

clean:
	rm -rf apps/proxy/cache/*
	rm -rf apps/kernel/__pycache__
	rm -rf apps/proxy/__pycache__
	find . -type d -name ".venv" -exec rm -rf {} +
