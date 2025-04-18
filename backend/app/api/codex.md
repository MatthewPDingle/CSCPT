# Backend API

Defines the RESTful and WebSocket endpoints.

## Directory Structure (`backend/app/api/`)

```
backend/app/api/
├── __init__.py
├── ai_connector.py
├── cash_game.py
├── game.py
├── game_ws.py
├── history_api.py
└── setup.py
```

*   `__init__.py`: Initializes the `api` directory as a Python package.
*   `ai_connector.py`: API endpoints specifically for interacting with the AI layer (requesting decisions, managing memory).
*   `cash_game.py`: API endpoints for managing cash game specific features (creating cash games, rebuys, cashouts).
*   `game.py`: Core API endpoints for general game management (creating, joining, starting games, processing actions via REST - potentially deprecated in favor of WebSocket).
*   `game_ws.py`: Defines the WebSocket endpoint (`/ws/game/{game_id}`) for real-time game communication (state updates, action requests, player actions).
*   `history_api.py`: API endpoints for retrieving game and hand history data, and player statistics.
*   `setup.py`: API endpoint (`/setup/game`) for initializing a new game based on configuration received from the frontend lobby.
