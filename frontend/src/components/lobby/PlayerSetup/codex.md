# Frontend Player Setup Components

UI elements for setting up players in the lobby.

## Directory Structure (`frontend/src/components/lobby/PlayerSetup/`)

```
frontend/src/components/lobby/PlayerSetup/
├── CashGamePlayerSetup.tsx
├── index.tsx
└── TournamentPlayerSetup.tsx
```

*   `CashGamePlayerSetup.tsx`: UI component allowing the user to configure individual AI opponents (name, archetype) for a cash game based on the selected table size.
*   `index.tsx`: A wrapper component that conditionally renders either `CashGamePlayerSetup` or `TournamentPlayerSetup` based on the selected game mode.
*   `TournamentPlayerSetup.tsx`: UI component allowing the user to configure the distribution percentage of different AI archetypes for a tournament game.
