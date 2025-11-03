.PHONY: help install-deps db-init run-proxy run-kernel run-frontend dev clean \
	ingest-paras ingest-embeddings ingest-evidence-embeddings ingest-layers ingest-graph ingest-precedents

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
	@echo ""
	@echo "  ingest-paras        Extract policy paragraphs to fixtures JSONL (see scripts/extract_paras.py)"
	@echo "  ingest-embeddings   Embed paragraphs and load to DB (scripts/embed_paras.py)"
	@echo "  ingest-evidence-embeddings Embed evidence key findings to evidence_chunk (scripts/embed_evidence_chunks.py)"
	@echo "  ingest-layers       Import GeoPackages into PostGIS (scripts/import_layers.sh)"
	@echo "  ingest-graph        Import policy graph/tests (scripts/ingest_policy_graph.py)"
	@echo "  ingest-precedents   Import precedents with embeddings (scripts/ingest_precedents.py)"

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

# --- Ingestion helpers ---

ingest-paras:
	@if [ -f fixtures/lpa_demo/policy_paras.jsonl ]; then \
		echo "fixtures/lpa_demo/policy_paras.jsonl already exists"; \
	else \
		echo "Run: python scripts/extract_paras.py <pdf_files...> (writes fixtures/lpa_demo/policy_paras.jsonl)"; \
	fi

ingest-embeddings:
	@echo "Embedding policy paragraphs into Postgres..."
	python3.12 scripts/embed_paras.py

ingest-evidence-embeddings:
	@echo "Embedding evidence key findings into evidence_chunk..."
	# Use kernel venv if available for sentence-transformers
	@if [ -d apps/kernel/.venv ]; then \
		cd apps/kernel && . .venv/bin/activate && python ../../scripts/embed_evidence_chunks.py; \
	else \
		python3.12 scripts/embed_evidence_chunks.py; \
	fi

ingest-graph:
	@echo "Importing policy graph relationships and tests..."
	python3.12 scripts/ingest_policy_graph.py

ingest-precedents:
	@echo "Importing precedents with embeddings..."
	python3.12 scripts/ingest_precedents.py

ingest-layers:
	@echo "Importing GeoPackages in fixtures/lpa_demo (if any) ..."
	@if ls fixtures/lpa_demo/*.gpkg >/dev/null 2>&1; then \
		bash scripts/import_layers.sh fixtures/lpa_demo/*.gpkg; \
	else \
		echo "No .gpkg files found under fixtures/lpa_demo. Run scripts/import_layers.sh <your.gpkg> ..."; \
	fi
