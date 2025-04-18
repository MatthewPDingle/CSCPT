# Frontend Hooks

Custom React hooks for encapsulating stateful logic.

## Directory Structure (`frontend/src/hooks/`)

```
frontend/src/hooks/
├── useGameWebSocket.test.ts
├── useGameWebSocket.ts
├── useWebSocket.test.ts
└── useWebSocket.ts
```

*   `useGameWebSocket.test.ts`: Unit tests for the `useGameWebSocket` hook.
*   `useGameWebSocket.ts`: Custom hook specifically designed to handle the WebSocket communication for the poker game, parsing incoming messages (game state, actions, requests) and providing functions to send actions/chat. Manages game-specific state derived from WebSocket messages.
*   `useWebSocket.test.ts`: Unit tests for the generic `useWebSocket` hook.
*   `useWebSocket.ts`: A generic custom hook for managing a WebSocket connection, handling connection status, sending/receiving messages, and automatic reconnection logic.
