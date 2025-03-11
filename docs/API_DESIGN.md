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

#### Get Game Session

```
GET /api/games/{gameId}
```

Response:
```json
{
  "gameId": "12345abc",
  "gameType": "cash_game",
  "tableSize": 6,
  "blinds": {
    "small": 5,
    "big": 10
  },
  "players": [
    // Player information
  ],
  "status": "active" // or "completed", "paused"
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

### AI Coaching

#### Request Coaching Analysis

```
POST /api/coach/analyze
```

Request Body:
```json
{
  "gameId": "12345abc",
  "handId": "hand789",
  "userId": "user123"
}
```

Response:
```json
{
  "analysisId": "analysis456",
  "status": "processing" // or "completed", "failed"
}
```

#### Get Coaching Analysis

```
GET /api/coach/analyze/{analysisId}
```

Response:
```json
{
  "analysisId": "analysis456",
  "gameId": "12345abc",
  "handId": "hand789",
  "userId": "user123",
  "analysis": {
    "overview": "You played this hand well overall, but missed value on the river.",
    "preflop": {
      "action": "raise",
      "evaluation": "Good raise with premium holding.",
      "alternative": "A slightly larger raise would be better to isolate."
    },
    "flop": {
      // Analysis of flop play
    },
    "turn": {
      // Analysis of turn play
    },
    "river": {
      // Analysis of river play
    },
    "summary": "Consider betting larger on the river to maximize value from weaker hands."
  },
  "status": "completed"
}
```

## WebSocket API

### Game WebSocket Interface

WebSocket Endpoint: `ws://hostname/ws/game/{gameId}`

#### Connection Parameters

Query Parameters:
```
token=<jwt-token>
userId=<user-id>
```

#### Server Messages

1. **Game State Update**
```json
{
  "type": "game_state",
  "data": {
    "gameId": "12345abc",
    "hand": {
      "handId": "hand789",
      "board": ["As", "Kh", "2d", "Ts", "3c"],
      "pot": 120,
      "sidePots": [],
      "currentBet": 10,
      "minRaise": 20
    },
    "players": [
      {
        "seat": 1,
        "userId": "user123",
        "name": "Player 1",
        "stack": 950,
        "bet": 10,
        "folded": false,
        "cards": ["Ah", "Ac"], // Only visible for the logged-in user
        "status": "active"
      },
      // ... other players with hidden cards
    ],
    "action": {
      "seat": 2,
      "remainingTime": 30
    },
    "lastAction": {
      "seat": 1,
      "action": "bet",
      "amount": 10
    }
  }
}
```

2. **Action Request**
```json
{
  "type": "action_request",
  "data": {
    "handId": "hand789",
    "seat": 1,
    "options": ["fold", "call", "raise"],
    "callAmount": 10,
    "minRaise": 20,
    "maxRaise": 950,
    "timeLimit": 30
  }
}
```

3. **Hand Result**
```json
{
  "type": "hand_result",
  "data": {
    "handId": "hand789",
    "winners": [
      {
        "seat": 3,
        "amount": 120,
        "hand": ["Qs", "Qc"],
        "handRank": "Three of a Kind",
        "bestCards": ["Qs", "Qc", "Qd", "As", "Kh"]
      }
    ],
    "players": [
      {
        "seat": 1,
        "cards": ["Ah", "Ac"],
        "folded": false
      },
      // ... other players
    ],
    "board": ["Qs", "Kh", "2d", "Qd", "3c"]
  }
}
```

4. **Chat Message**
```json
{
  "type": "chat",
  "data": {
    "from": "system", // or "player", "coach"
    "text": "Player 3 wins with Three of a Kind",
    "timestamp": "2025-03-11T12:05:30Z"
  }
}
```

5. **Error Message**
```json
{
  "type": "error",
  "data": {
    "code": "invalid_action",
    "message": "Invalid action: raise amount below minimum",
    "handId": "hand789"
  }
}
```

#### Client Messages

1. **Player Action**
```json
{
  "type": "action",
  "data": {
    "handId": "hand789",
    "action": "raise", // fold, call, check, bet, raise, all-in
    "amount": 30 // required for bet and raise
  }
}
```

2. **Chat Message**
```json
{
  "type": "chat",
  "data": {
    "text": "Nice hand!",
    "target": "table" // or "coach" for private coaching chat
  }
}
```

3. **Coach Query**
```json
{
  "type": "coach_query",
  "data": {
    "query": "What range should I put player 3 on?",
    "handId": "hand789"
  }
}
```

4. **Heartbeat**
```json
{
  "type": "ping",
  "timestamp": 1628765432
}
```

### Coaching WebSocket Interface

WebSocket Endpoint: `ws://hostname/ws/coach/{userId}`

This interface provides a dedicated channel for real-time coaching interactions, independent of the game flow.

#### Server Messages

1. **Coach Response**
```json
{
  "type": "coach_response",
  "data": {
    "text": "Based on their play style, player 3 likely has a range of...",
    "relatedHand": "hand789",
    "timestamp": "2025-03-11T12:06:00Z"
  }
}
```

2. **Coach Insight**
```json
{
  "type": "coach_insight",
  "data": {
    "category": "pattern_recognition",
    "text": "I've noticed player 2 has been 3-betting light from position...",
    "confidence": 0.85,
    "timestamp": "2025-03-11T12:10:00Z"
  }
}
```

#### Client Messages

1. **General Query**
```json
{
  "type": "coach_query",
  "data": {
    "query": "How should I adjust to tight players?",
    "context": {
      "gameId": "12345abc"
    }
  }
}
```

2. **Strategy Question**
```json
{
  "type": "strategy_question",
  "data": {
    "topic": "3-betting",
    "question": "When should I 3-bet with middle pairs?",
    "skill_level": "intermediate"
  }
}
```

## Event Types

1. **Game Events**
   - `game_created`: New game session created
   - `game_started`: Game play has begun
   - `hand_started`: New hand being dealt
   - `player_action`: Player performed an action
   - `hand_completed`: Hand results determined
   - `game_completed`: Game session ended

2. **Player Events**
   - `player_joined`: Player joined the table
   - `player_left`: Player left the table
   - `player_timeout`: Player failed to act in time

3. **Coaching Events**
   - `coach_analysis_started`: Hand analysis has begun
   - `coach_analysis_completed`: Hand analysis is ready
   - `coach_tip`: Real-time coaching advice provided

## Data Models

### Game State Model

```json
{
  "gameId": "12345abc",
  "gameType": "cash_game",
  "status": "active",
  "currentHand": {
    "handId": "hand789",
    "dealerPosition": 0,
    "sbPosition": 1,
    "bbPosition": 2,
    "board": ["As", "Kh", "2d", null, null],
    "pot": 120,
    "mainPot": 120,
    "sidePots": [],
    "round": "flop", // preflop, flop, turn, river, showdown
    "currentPosition": 3,
    "lastRaisePosition": 5,
    "lastAction": {
      "position": 5,
      "action": "raise",
      "amount": 40
    }
  },
  "players": [
    {
      "userId": "user123",
      "seat": 0,
      "name": "Player 1",
      "stack": 950,
      "bet": 0,
      "totalBet": 10,
      "cards": ["Ah", "Ac"], // Visible only to the player
      "status": "active", // active, folded, all-in, sitting-out
      "isDealer": true,
      "timebank": 60
    },
    // ... other players
  ],
  "blinds": {
    "small": 5,
    "big": 10
  },
  "ante": 0,
  "minBuyIn": 500,
  "maxBuyIn": 5000
}
```

### Player Profile Model

```json
{
  "userId": "user123",
  "username": "pokerplayer1",
  "stats": {
    "handsPlayed": 1240,
    "winRate": 2.3, // bb/100 hands
    "vpip": 0.22,
    "pfr": 0.17,
    "threebet": 0.05,
    "aggFactor": 2.1,
    "wtsd": 0.24,
    "cbet": {
      "flop": 0.67,
      "turn": 0.55,
      "river": 0.40
    }
  },
  "preferences": {
    "autoMuck": true,
    "showTimebank": true,
    "sounds": true
  }
}
```

### Hand History Model

```json
{
  "handId": "hand789",
  "gameId": "12345abc",
  "timestamp": "2025-03-11T12:00:00Z",
  "blinds": {
    "small": 5,
    "big": 10
  },
  "ante": 0,
  "players": [
    {
      "seat": 0,
      "name": "Player 1",
      "stack": 1000,
      "cards": ["Ah", "Ac"],
      "position": "BTN" // BTN, SB, BB, UTG, etc.
    },
    // ... other players
  ],
  "actions": [
    {
      "street": "preflop",
      "seat": 1,
      "action": "post",
      "amount": 5,
      "type": "sb"
    },
    {
      "street": "preflop",
      "seat": 2,
      "action": "post",
      "amount": 10,
      "type": "bb"
    },
    {
      "street": "preflop",
      "seat": 3,
      "action": "fold",
      "amount": 0
    },
    // ... other actions
  ],
  "board": ["As", "Kh", "2d", "Ts", "3c"],
  "results": [
    {
      "seat": 0,
      "amount": 120,
      "handRank": "Three of a Kind",
      "bestHand": ["Ah", "Ac", "As", "Kh", "Ts"]
    }
  ],
  "pot": {
    "main": 120,
    "side": []
  }
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

## API Versioning

The API uses URI versioning:

```
/api/v1/games
```

Future versions will be specified with incremented version numbers:

```
/api/v2/games
```