# Chip Swinger Championship Poker Trainer
## API Design Documentation

This document outlines the API design for the Chip Swinger Championship Poker Trainer, detailing the RESTful endpoints and WebSocket interfaces that enable communication between the frontend and backend components.

## REST API Endpoints

### Game Management

#### Create Game Session

```
POST /api/games
```

Request Body:
```json
{
  "gameType": "cash_game", // or "tournament"
  "tableSize": 6, // Number of players (2-9)
  "buyIn": 1000, // Starting chips
  "blinds": {
    "small": 5,
    "big": 10
  },
  "playerArchetypes": [
    {
      "seat": 1,
      "archetype": "TAG" // TAG, LAG, TP, CS, Maniac, Noob, or Random
    },
    // ... additional players
  ]
}
```

Response:
```json
{
  "gameId": "12345abc",
  "tableState": {
    // Initial table state
  },
  "wsEndpoint": "ws://hostname/ws/game/12345abc"
}
```

#### Game Setup from Lobby

```
POST /setup/game
```

Request Body:
```json
{
  "game_mode": "cash", // or "tournament"
  "small_blind": 5,
  "big_blind": 10,
  "ante": 0,
  "min_buy_in": 400,
  "max_buy_in": 2000,
  "table_size": 6,
  "betting_structure": "no_limit",
  "rake_percentage": 0.05,
  "rake_cap": 5,
  "players": [
    {
      "name": "You",
      "is_human": true,
      "buy_in": 1000,
      "position": 0
    },
    {
      "name": "Player 1",
      "is_human": false,
      "archetype": "TAG",
      "buy_in": 1000,
      "position": 1
    },
    // Additional players
  ]
}
```

Response:
```json
{
  "game_id": "12345abc",
  "human_player_id": "player123"
}
```

### User Management

#### Create User

```
POST /api/users
```

Request Body:
```json
{
  "username": "player1",
  "email": "player1@example.com",
  "password": "securepassword"
}
```

Response:
```json
{
  "userId": "user123",
  "username": "player1",
  "created": "2025-03-11T12:00:00Z"
}
```

#### User Authentication

```
POST /api/auth/login
```

Request Body:
```json
{
  "username": "player1",
  "password": "securepassword"
}
```

Response:
```json
{
  "userId": "user123",
  "token": "jwt-token-here",
  "expires": "2025-03-12T12:00:00Z"
}
```

### Statistics

#### Get Player Statistics

```
GET /api/stats/player/{userId}
```

Response:
```json
{
  "userId": "user123",
  "handsPlayed": 150,
  "winRate": 0.55,
  "vpip": 0.23,
  "pfr": 0.18,
  "aggFactor": 2.4,
  "lastUpdated": "2025-03-11T12:00:00Z"
}
```

#### Get Game Statistics

```
GET /api/stats/game/{gameId}
```

Response:
```json
{
  "gameId": "12345abc",
  "handsPlayed": 42,
  "potSizes": {
    "average": 120.5,
    "largest": 350
  },
  "playerStats": [
    {
      "seat": 1,
      "vpip": 0.25,
      "pfr": 0.15,
      // Additional stats
    },
    // ... other players
  ]
}
```

## WebSocket Protocol

The Chip Swinger application uses WebSockets for real-time game communication.

WebSocket endpoint: `/ws/game/{game_id}?player_id={player_id}`

### Client to Server Messages

1. Player Actions
```json
{
  "type": "action",
  "data": {
    "action": "CALL",
    "amount": 20
  }
}
```

Valid action types:
- `FOLD` - Fold the hand
- `CHECK` - Check (when no bet is required)
- `CALL` - Call the current bet
- `BET` - Make a bet (when no previous bet exists)
- `RAISE` - Raise a previous bet
- `ALL_IN` - Go all-in with remaining chips

2. Chat Messages
```json
{
  "type": "chat",
  "data": {
    "text": "Good luck!",
    "target": "table"
  }
}
```

3. Heartbeat
```json
{
  "type": "ping",
  "timestamp": 1648657890123
}
```

### Server to Client Messages

1. Game State Updates
```json
{
  "type": "game_state",
  "data": {
    "game_id": "game123",
    "players": [
      {
        "player_id": "player1",
        "name": "Alice",
        "chips": 980,
        "position": 0,
        "status": "ACTIVE",
        "current_bet": 20,
        "total_bet": 20,
        "cards": [
          {"rank": "A", "suit": "H"},
          {"rank": "K", "suit": "H"}
        ]
      },
      {
        "player_id": "player2",
        "name": "Bob",
        "chips": 1000,
        "position": 1,
        "status": "ACTIVE",
        "current_bet": 0,
        "total_bet": 0,
        "cards": null
      }
    ],
    "community_cards": [
      {"rank": "10", "suit": "H"},
      {"rank": "J", "suit": "H"},
      {"rank": "Q", "suit": "H"}
    ],
    "pots": [
      {
        "name": "Main Pot",
        "amount": 40,
        "eligible_player_ids": ["player1", "player2"]
      }
    ],
    "total_pot": 40,
    "current_round": "FLOP",
    "button_position": 0,
    "current_player_idx": 1,
    "current_bet": 20,
    "small_blind": 10,
    "big_blind": 20,
    "min_buy_in": 400,
    "max_buy_in": 2000
  }
}
```

Note: Each connected client receives a personalized game state where only their own cards are visible.

2. Player Action Notifications
```json
{
  "type": "player_action",
  "data": {
    "player_id": "player1",
    "action": "RAISE",
    "amount": 60,
    "timestamp": "2023-04-01T12:34:56.789Z"
  }
}
```

3. Action Requests
```json
{
  "type": "action_request",
  "data": {
    "handId": "hand123",
    "player_id": "player2",
    "options": ["FOLD", "CALL", "RAISE"],
    "callAmount": 20,
    "minRaise": 40,
    "maxRaise": 1000,
    "timeLimit": 30,
    "timestamp": "2023-04-01T12:34:56.789Z"
  }
}
```

4. Hand Results
```json
{
  "type": "hand_result",
  "data": {
    "handId": "hand123",
    "winners": [
      {
        "player_id": "player1",
        "name": "Alice",
        "amount": 500,
        "cards": ["AH", "KH"],
        "hand_rank": "Flush, Ace High"
      }
    ],
    "players": [
      {
        "player_id": "player1",
        "name": "Alice",
        "folded": false,
        "cards": ["AH", "KH"]
      },
      {
        "player_id": "player2",
        "name": "Bob",
        "folded": true
      }
    ],
    "board": ["10H", "JH", "QH", "2S", "7D"],
    "timestamp": "2023-04-01T12:35:30.123Z"
  }
}
```

5. Chat Messages
```json
{
  "type": "chat",
  "data": {
    "from": "Alice",
    "text": "Good game!",
    "timestamp": "2023-04-01T12:36:00.123Z"
  }
}
```

6. Error Messages
```json
{
  "type": "error",
  "data": {
    "code": "not_your_turn",
    "message": "Not your turn to act"
  }
}
```

7. Heartbeat Response
```json
{
  "type": "pong",
  "timestamp": 1648657890123
}
```

## Game Setup

Before establishing the WebSocket connection, the frontend should:

1. Create a game using the `/setup/game` endpoint
2. Receive the `game_id` and `human_player_id`
3. Connect to the WebSocket using these IDs

The setup endpoint handles creating the game, adding players (human and AI), and starting the game.

## Data Models

### Game State Model

```json
{
  "gameId": "game123",
  "gameType": "cash", 
  "status": "active",
  "players": [
    {
      "player_id": "player1",
      "name": "Alice",
      "chips": 980,
      "position": 0,
      "status": "ACTIVE",
      "cards": ["AH", "KH"] 
    }
  ],
  "community_cards": [
    {"rank": "10", "suit": "H"},
    {"rank": "J", "suit": "H"},
    {"rank": "Q", "suit": "H"}
  ],
  "pots": [
    {
      "name": "Main Pot",
      "amount": 40,
      "eligible_player_ids": ["player1", "player2"]
    }
  ],
  "total_pot": 40,
  "current_round": "FLOP",
  "button_position": 0,
  "current_player_idx": 1,
  "current_bet": 20,
  "small_blind": 10,
  "big_blind": 20,
  "min_buy_in": 400,
  "max_buy_in": 2000
}
```

### Player Model

```json
{
  "player_id": "player1",
  "name": "Alice",
  "chips": 980,
  "position": 0,
  "status": "ACTIVE",
  "current_bet": 20,
  "total_bet": 20,
  "cards": [
    {"rank": "A", "suit": "H"},
    {"rank": "K", "suit": "H"}
  ]
}
```

## API Authentication

All API endpoints and WebSocket connections require authentication, which can be achieved using:

1. **JWT Authentication**
   - Issue token via `/api/auth/login`
   - Include token in Authorization header: `Authorization: Bearer <token>`
   - For WebSocket, pass token as query parameter: `?token=<token>`

2. **Rate Limiting**
   - API requests limited to 100 requests per minute per user
   - WebSocket messages limited to 60 messages per minute per connection

3. **Security Measures**
   - HTTPS required for all API endpoints
   - WebSocket connections secured with WSS protocol
   - API keys for third-party services stored securely
   - Input validation for all API endpoints