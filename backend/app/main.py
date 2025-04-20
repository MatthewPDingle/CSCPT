"""
Main entry point for the FastAPI application.
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from AI .env file first, before any other imports
from dotenv import load_dotenv

# Determine the project root based on the current file's location
project_root = Path(__file__).parent.parent.parent
ai_env_path = project_root / 'ai' / '.env'

# Explicitly load the .env file from the ai directory
if ai_env_path.is_file():
    print(f"Loading environment variables from: {ai_env_path}")
    load_dotenv(dotenv_path=ai_env_path, override=True)
else:
    print(f"Warning: .env file not found at {ai_env_path}")

# Log relevant env vars AFTER loading to confirm
print(f"OPENAI_API_KEY loaded: {'Yes' if os.environ.get('OPENAI_API_KEY') else 'No'}")
print(f"OPENAI_MODEL loaded: {os.environ.get('OPENAI_MODEL', 'Not Set')}")

from app.api.game import router as game_router
from app.api.history_api import router as history_router
from app.api.ai_connector import router as ai_router
from app.api.setup import router as setup_router
from app.repositories.persistence import RepositoryPersistence, PersistenceScheduler
from app.repositories.in_memory import (
    GameRepository, UserRepository, HandRepository, ActionHistoryRepository,
    HandHistoryRepository
)

# Import and update system configuration
from app.core.config import MEMORY_SYSTEM_AVAILABLE
import app.core.config as app_config

print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
print(f"sys.path: {sys.path}")

# Add parent directory to path if running from backend directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    print(f"Adding parent directory to sys.path: {parent_dir}")
    sys.path.insert(0, parent_dir)

try:
    from ai.memory_integration import MemoryIntegration
    print("Successfully imported MemoryIntegration")
    # Update global flag for memory system availability in config
    app_config.MEMORY_SYSTEM_AVAILABLE = True
except ImportError as e:
    app_config.MEMORY_SYSTEM_AVAILABLE = False
    print(f"AI memory system not available: {e}")
    print("Continuing without player memory features")
    import traceback
    print(traceback.format_exc())

# Repository persistence setup
data_dir = os.environ.get("DATA_DIR", "./data")
persistence = RepositoryPersistence(data_dir=data_dir)
scheduler = PersistenceScheduler(
    persistence=persistence,
    interval_seconds=60,  # Save every minute
    repositories=[
        GameRepository,
        UserRepository,
        HandRepository,
        ActionHistoryRepository,
        HandHistoryRepository
    ]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for the FastAPI application.
    Handles startup and shutdown tasks.
    """
    # Startup: Load repositories and start persistence scheduler
    print("Starting Chip Swinger Championship Poker Trainer API...")
    
    # Initialize memory system if available
    if app_config.MEMORY_SYSTEM_AVAILABLE:
        try:
            # Enable memory by default, can be controlled through settings later
            memory_enabled = os.environ.get("ENABLE_PLAYER_MEMORY", "true").lower() == "true"
            MemoryIntegration.initialize(enable_memory=memory_enabled)
            print(f"Player memory system initialized (enabled={memory_enabled})")
        except Exception as e:
            print(f"Error initializing memory system: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    # Create data directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created data directory: {data_dir}")
    
    # Try to load existing data
    scheduler.load_all()
    print("Repository data loaded")
    
    # Start persistence scheduler
    scheduler.start()
    print("Persistence scheduler started")
    
    yield
    
    # Shutdown: Save all repositories and stop scheduler
    print("Shutting down Chip Swinger Championship Poker Trainer API...")
    scheduler.stop()
    print("Final data save completed")


app = FastAPI(
    title="Chip Swinger Championship Poker Trainer",
    description="Interactive Texas Hold'em poker training application with AI opponents",
    version="0.1.0",
    lifespan=lifespan
)

# CORS settings for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific origin in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400  # Cache preflight requests for 24 hours
)

@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "status": "ok",
        "message": "Chip Swinger Championship Poker Trainer API is running"
    }


# Include API routers
app.include_router(game_router)
app.include_router(history_router)
app.include_router(ai_router)
app.include_router(setup_router)

# Include Cash Game API router
from app.api.cash_game import router as cash_game_router
app.include_router(cash_game_router)

# Include WebSocket routers
from app.api.game_ws import router as game_ws_router
app.include_router(game_ws_router)