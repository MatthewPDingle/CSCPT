# Backend Core

Fundamental building blocks of the poker game.

## Directory Structure (`backend/app/core/`)

```
backend/app/core/
├── __init__.py
├── cards.py
├── config.py
├── hand_evaluator.py
├── poker_game.py
├── utils.py
└── websocket.py
```

*   `__init__.py`: Initializes the `core` directory as a Python package.
*   `cards.py`: Defines classes for `Card`, `Suit`, `Rank`, `Deck`, and `Hand`. Handles card representation and deck operations.
*   `config.py`: Contains global application configuration flags and settings (e.g., `MEMORY_SYSTEM_AVAILABLE`).
*   `hand_evaluator.py`: Implements the logic (`HandEvaluator`) for determining the rank (Pair, Flush, etc.) and value of poker hands.
*   `poker_game.py`: Contains the core `PokerGame` class, managing game flow, betting rounds, player states, pot calculation, and rule enforcement.
*   `utils.py`: Contains utility functions used across the backend, such as `game_to_model` for converting game state to API models.
*   `websocket.py`: Defines the `ConnectionManager` for handling WebSocket connections and the `GameStateNotifier` for broadcasting updates.
