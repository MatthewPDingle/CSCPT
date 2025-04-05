"""
Main entry point for the FastAPI application.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.game import router as game_router
from app.api.history_api import router as history_router
from app.api.ai_connector import router as ai_router
from app.api.setup import router as setup_router
from app.repositories.persistence import RepositoryPersistence, PersistenceScheduler
from app.repositories.in_memory import (
    GameRepository, UserRepository, HandRepository, ActionHistoryRepository,
    HandHistoryRepository
)

# Import memory integration
try:
    from ai.memory_integration import MemoryIntegration
    MEMORY_SYSTEM_AVAILABLE = True
except ImportError:
    MEMORY_SYSTEM_AVAILABLE = False
    print("AI memory system not available, continuing without player memory features")

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
    if MEMORY_SYSTEM_AVAILABLE:
        try:
            # Enable memory by default, can be controlled through settings later
            memory_enabled = os.environ.get("ENABLE_PLAYER_MEMORY", "true").lower() == "true"
            MemoryIntegration.initialize(enable_memory=memory_enabled)
            print(f"Player memory system initialized (enabled={memory_enabled})")
        except Exception as e:
            print(f"Error initializing memory system: {str(e)}")
    
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
    allow_methods=["*"],
    allow_headers=["*"],
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