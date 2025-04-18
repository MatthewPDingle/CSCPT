# Backend Services

Contains the application's business logic.

## Directory Structure (`backend/app/services/`)

```
backend/app/services/
├── __init__.py
├── game_service.py
└── hand_history_service.py
```

*   `__init__.py`: Initializes the `services` directory as a Python package.
*   `game_service.py`: Implements the `GameService` singleton class, which acts as the central coordinator for all game-related operations (creating games, adding players, processing actions, managing game state, interacting with `PokerGame` instances and repositories).
*   `hand_history_service.py`: Implements the `HandHistoryRecorder` class, responsible for creating, updating, and saving detailed `HandHistory` records.
