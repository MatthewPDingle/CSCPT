# Backend Application

Core logic and structure of the FastAPI application.

## Directory Structure (`backend/app/`)

```
backend/app/
├── __init__.py
├── main.py
├── api/
├── core/
├── models/
├── repositories/
└── services/
```

*   `__init__.py`: Initializes the `app` directory as a Python package.
*   `main.py`: The main entry point for the FastAPI application. Initializes the app, sets up middleware (CORS), includes routers, and manages application lifespan (startup/shutdown tasks like loading/saving data, initializing memory).

See subdirectory `codex.md` files for more detailed information about specific components.
