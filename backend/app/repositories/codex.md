# Backend Repositories

Handles data persistence and retrieval.

## Directory Structure (`backend/app/repositories/`)

```
backend/app/repositories/
├── __init__.py
├── base.py
├── in_memory.py
└── persistence.py
```

*   `__init__.py`: Initializes the `repositories` directory as a Python package.
*   `base.py`: Defines the abstract `Repository` base class (interface) for CRUD operations.
*   `in_memory.py`: Provides concrete `InMemoryRepository` implementations for storing domain models (like `GameRepository`, `HandHistoryRepository`) in memory during runtime. Includes a `RepositoryFactory`.
*   `persistence.py`: Implements `RepositoryPersistence` and `PersistenceScheduler` to periodically save and load the in-memory repository data to/from JSON files on disk.
