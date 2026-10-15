# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-15

### Added
- Initial release of Prism Station
- FastAPI backend with SQLite persistence
- React + TypeScript + Vite frontend
- Skill CRUD API with full metadata (name, slug, version, content, platform targets, tags)
- Skill validation engine (required sections, version format, platform targets)
- Skill search and filtering (full-text, platform, tags)
- Skill export (Markdown and JSON)
- JWT-based authentication with registration/login
- OIDC/Keycloak integration with SAML broker support
- Audit logging for all skill mutations
- Role-based access control (user, admin)
- Docker Compose with backend, frontend, Keycloak
- CI/CD pipeline (backend tests, frontend typecheck/build/test, Docker builds)
- Provider-agnostic LLM adapter framework (OpenAI-compatible, Anthropic, Gemini, Ollama)

### Security
- HttpOnly SameSite cookies for session management
- CSRF protection on state-changing operations
- PKCE for OIDC authorization code flow
- Token validation (signature, issuer, audience)
- No hardcoded secrets or credentials
- Demo mode restricted to localhost

### Infrastructure
- Non-root Docker users
- Health checks on all services
- Persistent volumes for database and Keycloak
- Development ports bound to 127.0.0.1