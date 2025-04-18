# Backend Tests

Contains all tests for the backend application.

## Directory Structure (`backend/tests/`)

```
backend/tests/
├── README.md
├── __init__.py
├── test_cards.py
├── test_cash_game_integration.py
├── test_cash_game_mechanics.py
├── test_game_ws_api.py
├── test_hand_evaluator.py
├── test_hand_history.py
├── test_poker_game.py
├── test_side_pots.py
├── test_websocket.py
├── api/
├── models/
├── repositories/
└── services/
```

*   `README.md`: Provides guidance on setting up and running backend tests.
*   `__init__.py`: Initializes the `tests` package.
*   `test_cards.py`: Unit tests for `cards.py`.
*   `test_cash_game_integration.py`: Integration tests focusing on the full cash game flow.
*   `test_cash_game_mechanics.py`: Unit tests for specific cash game logic within `poker_game.py`.
*   `test_game_ws_api.py`: Tests for the logic within the game WebSocket endpoint (`game_ws.py`).
*   `test_hand_evaluator.py`: Unit tests for `hand_evaluator.py`.
*   `test_hand_history.py`: Tests for the hand history recording functionality (`hand_history_service.py`).
*   `test_poker_game.py`: Unit tests for the core `PokerGame` logic.
*   `test_side_pots.py`: Specific unit tests for side pot calculation logic in `poker_game.py`.
*   `test_websocket.py`: Unit tests for the `ConnectionManager` and `GameStateNotifier` in `websocket.py`.
*   `api/`: Contains tests specifically for the API endpoints.
*   `models/`: Contains tests for the Pydantic domain models.
*   `repositories/`: Contains tests for the repository implementations.
*   `services/`: Contains tests for the service layer classes.
