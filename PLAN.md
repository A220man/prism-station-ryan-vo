# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

skill-crud

## Roadmap

### core-skeleton — FastAPI/React skeleton with auth, DB, and CI

Status: done

Acceptance:
- FastAPI app starts and serves health endpoint
- React app builds and serves frontend
- SQLite database with migrations
- OIDC/Keycloak auth configuration
- Docker Compose with backend, frontend, Keycloak
- CI workflow runs backend and frontend tests

Implementation: `backend/app/main.py`, `backend/app/api/health.py`, `backend/app/api/auth.py`, `backend/app/api/skills.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/security.py`, `backend/app/models/skill.py`, `backend/app/services/skill_service.py`, `backend/requirements.txt`, `backend/Dockerfile`, `backend/tests/test_main.py`, `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/src/components/Layout.tsx`, `frontend/src/pages/Health.tsx`, `frontend/src/pages/SkillsList.tsx`, `frontend/src/pages/SkillDetail.tsx`, `frontend/src/pages/SkillForm.tsx`, `frontend/src/pages/Login.tsx`, `frontend/src/pages/Register.tsx`, `frontend/src/index.css`, `frontend/Dockerfile`, `frontend/nginx.conf`, `compose.yaml`, `.github/workflows/ci.yml`, `portfolio.json`, `README.md`, `LICENSE`, `CHANGELOG.md`, `pyproject.toml`, `.gitignore`, `.env.example`

Tests: `backend/tests/test_main.py`, `frontend/src/test/health.test.tsx`

### skill-crud — Skill CRUD API and UI

Status: in_progress

Acceptance:
- Create, read, update, delete skills via API
- Skill model with name, description, version, content, platform targets
- React forms for skill management
- Pagination and filtering

### skill-validation — Skill validation engine

Status: planned

Acceptance:
- Validate skill structure (required fields, version format)
- Check for duplicate skills
- Validate platform-specific references
- Report validation errors with line numbers

### skill-search — Skill search and discovery

Status: planned

Acceptance:
- Full-text search across skill content
- Filter by platform (iOS, macOS, visionOS, watchOS, tvOS)
- Filter by skill category/tags
- Export skills as markdown/JSON

### llm-integration — LLM-powered skill analysis

Status: planned

Acceptance:
- Analyze skill for best practices (optional, advisory)
- Suggest improvements for cross-platform compatibility
- Detect deprecated API usage
- Provider-agnostic LLM adapter (OpenAI-compatible, Anthropic, Gemini, Ollama)

