# CLAUDE.md - Project Guidelines

## Build & Run Commands
- Backend: `cd cscp/backend && uvicorn app.main:app --reload`
- Frontend: `cd cscp/frontend && npm start`

## Test Commands
- Backend: `cd cscp/backend && pytest` (Single test: `pytest path/to/test.py::test_name`)
- Frontend: `cd cscp/frontend && npm test` (Single test: `npm test -- -t "test name"`)

## Code Style
- Python: PEP 8, type annotations, docstrings
- JavaScript: Airbnb JavaScript Style Guide, TypeScript preferred
- Formatting: Black for Python, Prettier for JS/TS
- Imports: Group standard library, third-party, and local imports
- Naming: snake_case for Python, camelCase for JS/TS
- Error handling: Use try/except with specific exceptions, never silent fails

## Repository Structure
- Backend: FastAPI in Python
- Frontend: React/TypeScript 
- AI: Python models in cscp/ai directory
- Documentation: Markdown files in docs/