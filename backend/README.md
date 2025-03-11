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
  - `api/` - API endpoints
  - `models/` - Pydantic models for API
- `tests/` - Test suite