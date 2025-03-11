# Chip Swinger Championship Poker Trainer
## Architecture Documentation

This document provides a detailed overview of the architecture for the Chip Swinger Championship Poker Trainer application.

## System Architecture

The application follows a three-tier architecture:

1. **Frontend**: React-based web application
2. **Backend**: FastAPI-based REST and WebSocket API
3. **AI Layer**: LLM integration for opponent and coaching AI

### Architecture Diagram

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│    Frontend     │◄────►│     Backend     │◄────►│    AI Layer     │
│  (React + MUI)  │      │    (FastAPI)    │      │  (LLM Services) │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        ▲                        ▲                        ▲
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  Browser/Client │      │    Database     │      │   LLM Provider  │
│                 │      │  (PostgreSQL)   │      │      APIs       │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

## Component Architecture

### Frontend Architecture

The frontend is organized using a component-based architecture with React:

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── Table/        # Poker table components
│   │   ├── Cards/        # Card visualization
│   │   ├── Players/      # Player representation
│   │   ├── Actions/      # Player action controls
│   │   ├── Statistics/   # Stats display components
│   │   └── Coach/        # Coaching interface
│   ├── contexts/         # React contexts
│   │   ├── GameContext   # Game state management
│   │   ├── UserContext   # User authentication
│   │   └── SettingsContext # App settings
│   ├── hooks/            # Custom React hooks
│   ├── services/         # API interaction
│   │   ├── api.js        # Backend API calls
│   │   ├── websocket.js  # WebSocket connection
│   │   └── auth.js       # Authentication service
│   ├── utils/            # Helper functions
│   │   ├── cards.js      # Card utilities
│   │   ├── betting.js    # Betting calculations
│   │   └── statistics.js # Statistics calculations
│   └── pages/            # Application pages
│       ├── Home.js       # Landing page
│       ├── Game.js       # Main game page
│       ├── Settings.js   # Settings page
│       └── Profile.js    # User profile page
```

### Backend Architecture

The backend follows a service-oriented architecture with FastAPI:

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── routes/       # API route definitions
│   │   │   ├── game.py   # Game management endpoints
│   │   │   ├── users.py  # User management endpoints
│   │   │   └── stats.py  # Statistics endpoints
│   │   └── websockets/   # WebSocket handlers
│   │       └── game.py   # Game WebSocket handler
│   ├── core/             # Configuration
│   │   ├── config.py     # Application configuration
│   │   └── security.py   # Authentication security
│   ├── db/               # Database models
│   │   ├── models.py     # SQLAlchemy models
│   │   └── session.py    # Database session management
│   ├── models/           # Pydantic models
│   │   ├── game.py       # Game data models
│   │   ├── user.py       # User data models
│   │   └── stats.py      # Statistics models
│   ├── services/         # Business logic
│   │   ├── game.py       # Game service
│   │   ├── poker.py      # Poker logic
│   │   └── stats.py      # Statistics service
│   └── utils/            # Helper functions
│       ├── poker.py      # Poker utility functions
│       └── validation.py # Input validation
```

### AI Layer Architecture

The AI layer is structured to abstract various LLM providers:

```
ai/
├── agents/               # Player agent implementations
│   ├── base.py           # Base agent interface
│   ├── tag.py            # Tight-aggressive player
│   ├── lag.py            # Loose-aggressive player
│   └── passive.py        # Passive player types
├── coach/                # Coaching implementation
│   ├── analyzer.py       # Hand analysis
│   ├── feedback.py       # Feedback generation
│   └── strategy.py       # Strategic advice
├── prompts/              # LLM prompt templates
│   ├── agent_prompts.py  # Player agent prompts
│   └── coach_prompts.py  # Coaching prompts
├── services/             # API abstraction
│   ├── openai.py         # OpenAI API integration
│   ├── anthropic.py      # Anthropic API integration
│   └── base.py           # Base LLM service
└── utils/                # AI-specific utilities
    ├── context.py        # Context management
    ├── parsing.py        # Response parsing
    └── memory.py         # Conversation memory
```

## Data Flow

### Game Flow

1. User initiates a game session
2. Backend creates a new game instance
3. WebSocket connection established between frontend and backend
4. Backend deals cards and manages game state
5. AI layer generates decisions for AI players
6. Game state updates sent to frontend via WebSocket
7. User actions sent to backend via WebSocket
8. Game results and statistics stored in database

### Coaching Flow

1. User requests coaching advice
2. Backend sends game state and history to AI layer
3. AI layer generates coaching analysis and advice
4. Coaching feedback sent to frontend via WebSocket
5. User interacts with coach through chat interface
6. Conversation history maintained for context

## Technology Stack

### Frontend
- React (UI library)
- Material-UI (Component library)
- Redux (State management)
- Socket.IO Client (WebSocket communication)

### Backend
- FastAPI (API framework)
- SQLAlchemy (ORM)
- Pydantic (Data validation)
- WebSockets (Real-time communication)
- PostgreSQL (Database)

### AI Layer
- OpenAI API
- Anthropic API
- LangChain (Optional, for LLM orchestration)
- Prompt engineering toolkit

## Security Considerations

- JWT authentication for API security
- Rate limiting for API endpoints
- Secure handling of API keys for LLM services
- Input validation for all user inputs
- CORS configuration for frontend-backend communication

## Scalability Considerations

- Horizontal scaling of backend services
- Database connection pooling
- Caching strategies for frequently accessed data
- Efficient WebSocket connection management
- Batch processing for AI requests