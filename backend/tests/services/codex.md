# Backend Service Tests

Tests for the business logic layer defined in `backend/app/services/`.

## Directory Structure (`backend/tests/services/`)

```
backend/tests/services/
├── __init__.py
├── test_cash_game_service.py
└── test_game_service.py
```

*   `__init__.py`: Initializes the `services` tests directory as a Python package.
*   `test_cash_game_service.py`: Tests specifically for the cash game related methods within the `GameService`.
*   `test_game_service.py`: Unit tests for the `GameService` class defined in `backend/app/services/game_service.py`, testing its methods for game creation, player management, action processing, etc. (likely mocking repository interactions).
