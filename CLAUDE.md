# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands
- Backend: `cd backend && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm start`
- AI: `pip install -r ai/requirements.txt`
  - Examples: `python -m ai.examples.all_providers_example` (set API keys first)

## Lint & Format Commands
- Python: `cd backend && black . && mypy .` 
- Frontend: `cd frontend && npm run lint && npm run format`

## Test Commands
- Backend: `cd backend && pytest` (Single test: `pytest path/to/test.py::test_name -v`)
- Frontend: `cd frontend && npm test` (Single test: `npm test -- -t "test name"`)
- AI: `python -m ai.tests.run_integration_tests` or `python -m ai.tests.test_llm_service`

## Code Style
- Python: PEP 8, type annotations, docstrings (Google style)
- JavaScript: Airbnb Style Guide, TypeScript interfaces for type safety
- Formatting: Black for Python, ESLint/Prettier for JS/TS
- Imports: Group standard library, third-party, local imports (alphabetized)
- Naming: snake_case (Python), camelCase (JS/TS), PascalCase (React components)
- Error Handling: Use specific exceptions, never silent fails, proper logging

## Repository Structure
- Backend: FastAPI (Python) in backend/
- Frontend: React/TypeScript in frontend/
- AI: Python models in ai/ (OpenAI, Anthropic, Gemini providers)