# Backend Model Tests

Tests for the Pydantic models defined in `backend/app/models/`.

## Directory Structure (`backend/tests/models/`)

```
backend/tests/models/
├── __init__.py
└── test_domain_models.py
```

*   `__init__.py`: Initializes the `models` tests directory as a Python package.
*   `test_domain_models.py`: Unit tests verifying the creation, validation, and default values of the core domain models (like `Game`, `Player`, `Hand`) defined in `backend/app/models/domain_models.py`.
