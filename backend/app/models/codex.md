# Backend Models

Pydantic models defining data structures.

## Directory Structure (`backend/app/models/`)

```
backend/app/models/
├── __init__.py
├── domain_models.py
└── game_models.py
```

*   `__init__.py`: Initializes the `models` directory as a Python package.
*   `domain_models.py`: Defines core business entities using Pydantic models (e.g., `Game`, `Player`, `Hand`, `ActionHistory`, Enums like `GameStatus`, `PlayerAction`). These represent the application's internal data structure.
*   `game_models.py`: Defines Pydantic models specifically for API request/response structures related to the game state (e.g., `GameStateModel`, `PlayerModel`, `CardModel`, `ActionRequest`).
