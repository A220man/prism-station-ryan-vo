# Changelog

## 1.8.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.7.1 — work-in-progress checkpoint

### Fixed
- Added `MockProvider` class to `backend/app/services/llm_service.py` to support `LLM_PROVIDER=mock` configuration
- Provider-agnostic LLM adapter now supports: OpenAI-compatible, Anthropic, Gemini, Ollama, and mock providers
- Prevents `NameError` when configuring `LLM_PROVIDER=mock` in environment

## 1.7.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.6.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.5.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.4.0 — work-in-progress checkpoint

### Added
- LLM integration foundation with provider-agnostic adapters (OpenAI-compatible, Anthropic, Gemini, Ollama)
- LLM service module: `backend/app/services/llm_service.py` with base provider abstraction and three concrete implementations
- LLM API endpoints: `backend/app/api/llm.py` with `/status`, `/analyze`, `/cross-platform`, `/deprecated-apis`
- 5 backend tests for LLM endpoints (all pass when provider not configured)

### Changed
- Updated `backend/app/main.py` to include LLM router
- Updated `backend/tests/test_main.py` with LLM endpoint tests

Partial code published for continued development. Known issues: STATUS.md.
## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

### Added
- Skill search and discovery UI: platform dropdown filter (iOS, macOS, visionOS, watchOS, tvOS, linux, windows) and tag text filter
- Frontend SkillsList page updated with filter controls that work with existing backend filtering API

### Changed
- SkillsList page: search form now includes platform and tag filters alongside text search

Partial code published for continued development. Known issues: STATUS.md.
