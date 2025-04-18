# Frontend Services

Modules for handling external interactions.

## Directory Structure (`frontend/src/services/`)

```
frontend/src/services/
└── api.ts
```

*   `api.ts`: Configures an Axios instance for making REST API calls to the backend. Defines functions for specific API endpoints (e.g., `setupGame`, `createCashGame`). Includes a helper to generate WebSocket URLs.
