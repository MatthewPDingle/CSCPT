# Backend Repository Tests

Tests for the data access layer implementations in `backend/app/repositories/`.

## Directory Structure (`backend/tests/repositories/`)

```
backend/tests/repositories/
├── __init__.py
├── test_in_memory.py
└── test_persistence.py
```

*   `__init__.py`: Initializes the `repositories` tests directory as a Python package.
*   `test_in_memory.py`: Unit tests for the `InMemoryRepository` implementations (e.g., `GameRepository`) defined in `backend/app/repositories/in_memory.py`, testing CRUD operations and thread safety.
*   `test_persistence.py`: Tests for the data persistence utilities (`RepositoryPersistence`, `PersistenceScheduler`) defined in `backend/app/repositories/persistence.py`, verifying saving and loading from disk.
