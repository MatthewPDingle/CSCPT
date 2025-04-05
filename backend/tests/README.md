# Testing Guide for CSCPT Backend

This document provides guidance on setting up and running tests for the Chip Swinger Championship Poker Trainer backend.

## Test Environment Setup

The CSCPT application uses a modular architecture with separate components (AI, Backend, Frontend).
Tests that integrate these components require special setup.

### Prerequisites

1. **Python Environment**
   - Use the virtual environment: `source venv/bin/activate`
   - Install test dependencies: `pip install -r requirements.txt pytest pytest-asyncio`

2. **PYTHONPATH Configuration**
   - Tests that use the AI module require access to the parent directory
   - Set before running tests: `export PYTHONPATH=/path/to/cscpt:$PYTHONPATH`

3. **Mock Configuration**
   - Most tests mock external components
   - Pay attention to the import paths being mocked
   - Use the exact same import paths as in the source code

### Test Database

Some tests require a database. The tests use:
- In-memory repositories for unit tests
- File-based repositories for integration tests

## Types of Tests

### Unit Tests

Test individual components in isolation:
- Repository tests
- Service method tests 
- Utility function tests

Example: `pytest tests/repositories/test_in_memory.py`

### API Tests

Test API endpoints with FastAPI TestClient:
- Route validation
- Response formats
- Error handling

Example: `pytest tests/api/test_game_api.py`

### Integration Tests

Test complete workflows across multiple components:
- Game flow
- WebSocket interactions
- AI integration

Example: `pytest tests/api/test_integration.py`

## AI Integration Tests

Tests for AI integration require special handling:

1. **Environment Variables**
   ```
   export PYTHONPATH=/path/to/cscpt
   export AI_TESTING=1  # Enables test mode for AI components
   ```

2. **Running AI Integration Tests**
   ```
   cd /path/to/cscpt
   python -m pytest backend/tests/api/test_ai_integration.py -v
   ```

3. **Common Issues**
   - `ModuleNotFoundError: No module named 'ai'`: PYTHONPATH not set correctly
   - `AttributeError: module has no attribute 'MemoryIntegration'`: Import path mismatch
   - Missing mock responses: AI components expected specific responses

## WebSocket Tests

Testing WebSocket endpoints requires both client and server components:

1. Use `TestClient` for connection setup
2. Use mocked connections for message exchange
3. Test asyncio behavior with `pytest.mark.asyncio`

Example: `python -m pytest backend/tests/test_game_ws_api.py -v`

## Test in Isolation

To test specific files or functions:

```bash
# Test a single file
pytest tests/test_cards.py

# Test a specific function
pytest tests/test_cards.py::test_card_comparison

# Verbose output
pytest -v tests/test_cards.py
```

## Continuous Integration

The test suite runs automatically on:
- Pull request creation
- Push to main branch
- Daily scheduled builds

Make sure all tests pass locally before pushing changes.