# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning where meaningful for a demo application.

## [Unreleased]
### Added
- Root `.env.example` with required environment variables for kernel, proxy, and website.
- `CONTRIBUTING.md` and `SECURITY.md` for publishing readiness.
- Root `.gitignore` covering Python, Node, env, logs, and caches.
- **LLM-driven panel planning system**: The kernel now uses conversational LLM reasoning to decide which UI panels to show, replacing hardcoded module→panel mappings. New modules: `panel_planner.py` (LLM prompt + validation) and `panel_dispatcher.py` (data retrieval executor).
- `LLM_PANEL_PLANNING.md`: Comprehensive documentation of the adaptive planning architecture, fallback behavior, and debugging guide.
- Frontend dev toggle: `VITE_DISABLE_CIRCUIT_BREAKER` env var to bypass circuit breaker in local dev for faster iteration.
- Hybrid search in playbook: `db_search_policies` and `db_search_precedents` now use GPU-accelerated embeddings (60% FTS + 40% vector similarity) for better semantic relevance.

### Changed
- Rewrote `start.sh` to a clean, robust starter (no duplicate frontend spawns; proper traps; optional Docker compose detection).
- Updated `stop.sh` to stop processes actually launched by `start.sh` and detect docker compose variants.
- Kernel DB utilities now defer `psycopg/pgvector` imports to runtime and raise a controlled error, enabling graceful fixture fallbacks without heavy DB deps during tests.
- Proxy internals tidied: removed duplicate/unused imports, added `PROXY_USER_AGENT` support, and centralized user-agent usage.
- Frontend: consolidated reasoning hooks — `hooks/useReasoningStream.ts` now re-exports the validated V2 pipeline to eliminate duplication; cleaned unused imports in `PanelHost`.
- **Playbook architecture**: Replaced hardcoded `if module == "dm"` conditionals with LLM-driven panel planning loop. The system now reasons about which panels are relevant before retrieving data.
- Frontend schemas: Extended to accept optional fields (citations in `applicable_policies`, simple forms in `policy_editor`, union types in `scenario_compare` and `visual_compliance`) to match diverse backend payloads.
- **Embedding model**: Switched from sentence-transformers to Ollama-based `qwen3-embedding:8b` for GPU-accelerated embeddings with graceful fallback chain (Ollama → sentence-transformers → hash-based).

### Fixed
- Minor script robustness and developer UX improvements.
- Ensured tests run in a minimal environment by avoiding hard import failures when DB libraries are missing.
- Frontend panels not appearing: relaxed and realigned TS Zod schemas to match actual backend panel payloads (precedents, planning balance, draft decision, evidence snapshot, map), unblocking the validated patch pipeline.