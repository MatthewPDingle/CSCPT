# Getting Started with Chip Swinger Championship Poker Trainer

This document provides instructions for setting up the development environment and contributing to the Chip Swinger Championship Poker Trainer application.

## Prerequisites

- Python 3.9+
- Node.js 16+
- Git

## Setting Up the Development Environment

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/cscp.git
cd cscp
```

### 2. Backend Setup

```bash
# Create and activate a virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn app.main:app --reload
```

The backend server will be available at http://localhost:8000.

### 3. Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Start the development server
npm start
```

The frontend application will be available at http://localhost:3000.

### 4. AI Layer Setup

```bash
# Switch to the AI directory
cd ai

# Install dependencies (if separate from backend)
pip install -r requirements.txt
```

## Project Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Backend
DATABASE_URL=postgresql://user:password@localhost:5432/cscp

# AI Services
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

## Code Guidelines

### General Guidelines

- Follow the established project structure
- Write unit tests for all new functionality
- Document your code using docstrings and comments
- Follow language-specific style guides (PEP 8 for Python, Airbnb style for JavaScript)

### Git Workflow

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes and commit them: `git commit -m "Description of changes"`
3. Push your branch: `git push origin feature/your-feature-name`
4. Create a pull request on GitHub

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Resources

- [Project Specification](./SPEC.md)
- [Project Implementation Plan](./PROJECT_PLAN.md)
- [API Documentation](./API.md) (to be created)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/getting-started.html)