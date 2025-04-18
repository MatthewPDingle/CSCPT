# Frontend Contexts

React Context providers for managing shared state.

## Directory Structure (`frontend/src/contexts/`)

```
frontend/src/contexts/
├── GameContext.tsx
└── SetupContext.tsx
```

*   `GameContext.tsx`: Provides global state management for the active poker game. *(Note: Current implementation uses mock data and needs integration with WebSocket state)*.
*   `SetupContext.tsx`: Provides state management for the game configuration options selected in the lobby (game mode, blinds, player setups, etc.). Persists settings to `localStorage`.
