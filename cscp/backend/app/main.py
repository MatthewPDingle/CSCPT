"""
Main entry point for the FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.game import router as game_router

app = FastAPI(
    title="Chip Swinger Championship Poker Trainer",
    description="Interactive Texas Hold'em poker training application with AI opponents",
    version="0.1.0"
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