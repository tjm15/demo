# Contributing to The Planner's Assistant

Thanks for your interest in contributing! This repository is a demo-quality, production-style app. PRs that improve stability, documentation, tests, and security are welcome.

## Getting Started

- Read `README.md` and `QUICKSTART.md` for setup.
- Use `./start.sh` for a fast local run, or start services manually (proxy → kernel → website).
- Load sample data with the scripts in `scripts/` as needed.

## Development Guidelines

- Keep changes focused and small; one feature/fix per PR.
- Prefer type-safe and validated data flows:
  - Backend: Pydantic v2 models and FastAPI.
  - Frontend: TypeScript + Zod (where applicable).
- Follow existing code style and structure; avoid large refactors unless necessary.
- Include/update tests when changing behavior:
  - Backend: add unit tests in `tests/` or endpoint tests using FastAPI's TestClient.
  - Frontend: add/adjust Playwright tests under `website/tests/`.
- Update documentation when user-facing behavior or setup steps change.

## Running Tests

- Python tests (may require services or fixtures):
  - Ensure dependencies from `apps/kernel/requirements.txt` are installed.
  - Run with `pytest` from repo root.
- Frontend E2E tests:
  - `cd website && pnpm test:e2e`

## Commit Messages

- Use clear, descriptive messages:
  - feat: add new panel X
  - fix: correct proxy allow-list check for subdomains
  - docs: update Quickstart for Ubuntu 22.04
  - chore: bump FastAPI, add .env.example

## Security Considerations

- Do not include secrets in commits. Use `.env` (not versioned) and `.env.example` for placeholders.
- Changes to `apps/proxy/allowed_sources.yml` must be reviewed carefully.
- Keep the kernel’s module-aware citation policy intact.

## Pull Request Checklist

- [ ] Tests passing locally (or provide context if environment-dependent)
- [ ] Docs updated (`README.md`, `QUICKSTART.md`, or in-code docstrings)
- [ ] No stray logs/prints or debug code
- [ ] New files added to `.gitignore` as appropriate

## Reporting Issues

- Use GitHub Issues with a minimal reproduction, expected vs actual behavior, and environment details.

Thanks again for helping improve TPA! 🙏