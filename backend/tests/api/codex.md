# Backend API Tests

Tests specifically for the RESTful API endpoints defined in `backend/app/api/`.

## Directory Structure (`backend/tests/api/`)

```
backend/tests/api/
├── __init__.py
├── test_ai_connector.py
├── test_ai_integration.py
├── test_cash_game_api.py
├── test_game_api.py
├── test_game_ws_api.py
├── test_history_api.py
├── test_integration.py
├── test_setup_api.py
└── __pycache__/
```

*   `__init__.py`: Initializes the `api` tests directory as a Python package.
*   `test_ai_connector.py`: Tests for the API endpoints defined in `backend/app/api/ai_connector.py` that handle AI interactions.
*   `test_ai_integration.py`: Integration tests verifying the interaction between the backend API/services and the AI layer.
*   `test_cash_game_api.py`: Tests for the cash game specific API endpoints defined in `backend/app/api/cash_game.py`.
*   `test_game_api.py`: Tests for the general game management API endpoints defined in `backend/app/api/game.py`.
*   `test_game_ws_api.py`: Tests specifically for the WebSocket communication logic, focusing on message processing and broadcasting aspects managed via `backend/app/api/game_ws.py`.
*   `test_history_api.py`: Tests for the game/hand history API endpoints defined in `backend/app/api/history_api.py`.
*   `test_integration.py`: Broader integration tests covering flows across multiple API endpoints and backend components.
*   `test_setup_api.py`: Tests for the game setup endpoint defined in `backend/app/api/setup.py`.
*   `__pycache__/`: Python cache directory (automatically generated, not part of source code).
