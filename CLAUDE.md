# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands
- Backend: `cd backend && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm start`
- AI: `cd ai && pip install -r requirements.txt`
  - Examples: `python -m ai.examples.all_providers_example` (set API keys first)

## Lint & Format Commands
- Python: `cd backend && black . && mypy .` (line-length=88, py38+)
- Frontend: `cd frontend && npm run lint && npm run format`

## Test Commands
- Backend: `cd backend && pytest` (Single test: `pytest tests/path/to/test.py::test_name -v`)
- Frontend: `cd frontend && npm test` (Single test: `npm test -- -t "test name"`)
- AI: `python -m ai.tests.run_tests` or for specific: `python -m ai.tests.test_llm_service`

## Code Style
- Python: PEP 8, type annotations required, Google-style docstrings
- TypeScript: React components use PascalCase, interfaces for type safety
- Formatting: Black for Python (disallow_untyped_defs=true), ESLint/Prettier for JS/TS
- Imports: Group by standard library, third-party, local (alphabetized)
- Naming: snake_case (Python), camelCase (JS/TS), PascalCase (React components)
- Error Handling: Use specific exceptions, never silence errors, proper logging

## Repository Structure
- Backend: FastAPI (Python) in backend/ - poker engine, API, game mechanics
- Frontend: React/TypeScript in frontend/ - poker table UI, game controls
- AI: Python models in ai/ - agent implementations using OpenAI, Anthropic, Gemini