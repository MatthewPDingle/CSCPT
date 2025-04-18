# Frontend Pages

Top-level route components for the application.

## Directory Structure (`frontend/src/pages/`)

```
frontend/src/pages/
├── GamePage.tsx
├── HomePage.tsx
├── LobbyPage.tsx
└── NotFoundPage.tsx
```

*   `GamePage.tsx`: The main page where the poker game is played. Renders the `PokerTable`, `ActionControls`, and uses `useGameWebSocket` to manage the game state and interaction.
*   `HomePage.tsx`: The landing page of the application, providing an introduction and a link to start setting up a game.
*   `LobbyPage.tsx`: The page where users configure game settings (mode, blinds, players, archetypes) before starting a game. Uses `SetupContext`.
*   `NotFoundPage.tsx`: A standard 404 page displayed when a user navigates to an invalid URL.
