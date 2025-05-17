# AGENTS Quick Reference

This file summarizes key information for developers and AI assistants working in this repository.

## Directory Layout
- **ai/** – LLM integrations and agent logic.
- **backend/** – FastAPI service with poker engine and API.
- **frontend/** – React user interface.
- **docs/** – Project documentation.
- `codex.md` files exist in the root and each subdirectory with more detail.

## Build & Run
Commands from `CLAUDE.md`:
- Backend: `cd backend && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm start`
- AI setup: `cd ai && pip install -r requirements.txt`
  - Run examples: `python -m ai.examples.all_providers_example`

## Lint & Format
- Python: `cd backend && black . && mypy .`
- Frontend: `cd frontend && npm run lint && npm run format`

## Tests
- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm test`
- AI: `python -m ai.tests.run_tests`

## Contribution Guidelines
Extracted from `docs/CONTRIBUTING.md`:
- Create branches named `feature/`, `fix/`, `docs/`, `refactor/`, or `test/` followed by the issue number.
- Write commits in present, imperative mood and include the issue number.
- Reference the issue in the PR title and describe the implementation approach.
- Ensure all tests pass and update documentation when needed.
- Follow PEP 8 and Airbnb JavaScript style guides with type annotations.

## General Engineering Practices
- Adhere to common software engineering best practices such as version control, code reviews, and automated tests.
- Apply sound software architecture principles like separation of concerns and loose coupling when designing components.
- Research and fully understand new features or bugs before implementation. Create a detailed plan and follow it during development.
- Ensure fixes address the root cause of issues rather than masking symptoms.
- If the reason for a bug is unclear, add logging or other debugging steps to gather more information.

## Additional Documentation
Consult the codex files in each directory and the `docs/` folder for complete architecture, API design, and other project details.

