# Chip Swinger Championship Poker Trainer - Backend

The backend component of the Chip Swinger Championship Poker Trainer, built with FastAPI.

## Overview

This backend provides:
- Core poker game engine 
- RESTful and WebSocket APIs for game interaction
- AI opponent integration

## Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Clone the repository (if not already done)
git clone https://github.com/your-username/cscpt.git
cd cscpt/backend

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"
```

## Running the Server

```bash
# Start the development server
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

When the server is running, you can access the auto-generated API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
pytest

# Run a specific test
pytest tests/test_cards.py::test_deck_creation
```

## Project Structure

- `app/` - Main application code
  - `core/` - Core poker engine
    - `cards.py` - Card representation and deck management
    - `hand_evaluator.py` - Poker hand evaluation
    - `poker_game.py` - Game flow and betting logic
    - `utils.py` - Shared utility functions
  - `api/` - API endpoints
    - `game.py` - Game management endpoints
    - `game_ws.py` - WebSocket endpoints for real-time game interaction
    - `history_api.py` - Endpoints for accessing game history and statistics
  - `models/` - Data models
    - `domain_models.py` - Core domain entities
    - `game_models.py` - API-specific models
  - `services/` - Business logic
    - `game_service.py` - Centralized game management service (singleton)
    - `hand_history_service.py` - Historical data recording service
  - `repositories/` - Data access layer
- `tests/` - Test suite
  - `api/` - API-specific tests
  - `models/` - Model tests
  - `repositories/` - Repository tests
  - `services/` - Service tests

## Architecture

The backend follows a service-oriented architecture pattern:

1. **API Layer** (`app/api/`) - Handles HTTP/WebSocket requests and responses
2. **Service Layer** (`app/services/`) - Contains business logic and coordinates operations
3. **Repository Layer** (`app/repositories/`) - Handles data persistence
4. **Domain Model Layer** (`app/models/`) - Defines core entities and data structures
5. **Core Engine** (`app/core/`) - Implements poker game mechanics and rules

All API endpoints interact with the game state through the `GameService` singleton, which provides a consistent interface for game operations and ensures proper state management.