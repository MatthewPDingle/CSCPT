# Frontend Poker Components

UI elements specifically for the poker game view.

## Directory Structure (`frontend/src/components/poker/`)

```
frontend/src/components/poker/
├── ActionControls.tsx
├── Card.tsx
├── CashGameControls.tsx
├── GameWebSocket.css
├── GameWebSocket.tsx
├── PlayerSeat.tsx
└── PokerTable.tsx
```

*   `ActionControls.tsx`: React component displaying the action buttons (Fold, Check, Call, Bet, Raise) available to the human player during their turn. Includes bet sizing controls.
*   `Card.tsx`: React component responsible for rendering a single playing card, showing its rank and suit, or a face-down representation.
*   `CashGameControls.tsx`: React component providing UI elements specific to cash games, such as buttons for Rebuy, Top Up, and Cash Out.
*   `GameWebSocket.css`: CSS file containing styles specifically for the `GameWebSocket` component, including animations like the pot flash.
*   `GameWebSocket.tsx`: React component that uses the `useGameWebSocket` hook to manage the WebSocket connection and display game state, actions, chat, and errors. *(Note: Primarily display logic, core WebSocket logic is in the hook)*.
*   `PlayerSeat.tsx`: React component representing a single player at the poker table, displaying their name, chip count, cards (hidden or shown), status, and position markers (Dealer, SB, BB).
*   `PokerTable.tsx`: The main component that renders the visual representation of the poker table, including the felt, community cards area, pot display, and arranges `PlayerSeat` components around the table.
