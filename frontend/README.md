# Chip Swinger Championship Poker Trainer - Frontend

This is the frontend for the Chip Swinger Championship Poker Trainer application. It provides a visual interface for playing poker against AI opponents with different play styles.

## Project Structure

```
frontend/
├── public/              # Static assets
└── src/
    ├── components/      # UI components
    │   ├── common/      # Shared UI components
    │   └── poker/       # Poker-specific components
    ├── contexts/        # React contexts for state management
    ├── hooks/           # Custom React hooks
    ├── pages/           # Application pages
    ├── services/        # API interaction
    └── utils/           # Helper functions
```

## Key Components

### Poker Components

1. **PokerTable**: Renders the poker table with player positions and community cards
2. **Card**: Visualizes playing cards with proper suits and ranks
3. **PlayerSeat**: Displays player information and cards at the table
4. **ActionControls**: Provides UI for player actions (fold, check, call, bet, raise)

### Pages

1. **HomePage**: Landing page with game introduction and start button
2. **GamePage**: Main game interface with poker table and controls
3. **NotFoundPage**: 404 page for invalid routes

## Getting Started

### Prerequisites

- Node.js (version 14 or higher)
- npm (version 6 or higher)

### Installation

1. Clone the repository
2. Navigate to the frontend directory:
   ```
   cd cscpt/frontend
   ```
3. Install dependencies:
   ```
   npm install
   ```

### Development

Run the development server:

```
npm start
```

This will start the application in development mode at http://localhost:3000.

### Building for Production

Create a production build:

```
npm run build
```

This will generate optimized production files in the `build/` directory.

## API Integration

The frontend communicates with the backend API using Axios. API service functions are defined in `src/services/api.ts`.

To configure the API URL, set the `REACT_APP_API_URL` environment variable or modify the default URL in the api.ts file.

## Game State Management

Game state is managed using React Context API through the `GameContext`. This provides a centralized way to manage and access the game state throughout the application.

## Styling

The application uses a combination of:
- CSS for global styles
- Styled Components for component-specific styling with dynamic properties

## Testing

Run tests:

```
npm test
```

This project uses Jest and React Testing Library for unit and integration tests.

---

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).