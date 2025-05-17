# mypy: ignore-errors
"""
API routes for AI integration and memory system.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional, Any, Union
import asyncio
import json
import os
import sys
from datetime import datetime
import logging
from pydantic import BaseModel, Field

# Ensure the parent directory (containing ai module) is in the path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    logging.info(f"Added parent directory to sys.path in ai_connector.py: {parent_dir}")

# Import memory integration using the global flag from config
from app.core.config import MEMORY_SYSTEM_AVAILABLE

if MEMORY_SYSTEM_AVAILABLE:
    try:
        from ai.memory_integration import MemoryIntegration
        from ai.agents.response_parser import AgentResponseParser

        logging.info("Successfully imported AI modules in ai_connector.py")
    except ImportError as e:
        logging.error(f"Failed to import AI modules in ai_connector.py: {e}")
        import traceback

        logging.error(traceback.format_exc())
else:
    logging.warning(
        "AI memory system not available. AI memory features will be disabled."
    )

router = APIRouter(prefix="/ai", tags=["ai"])

# === Models ===


class AIDecisionRequest(BaseModel):
    """Request model for AI decision."""

    archetype: str
    game_state: Dict[str, Any]
    context: Dict[str, Any] = Field(default_factory=dict)
    player_id: str
    use_memory: bool = True
    intelligence_level: str = "expert"


class AIStatusResponse(BaseModel):
    """Response model for AI status."""

    memory_system_available: bool
    memory_system_enabled: Optional[bool] = None
    profiles_count: Optional[int] = None
    error: Optional[str] = None
    message: Optional[str] = None


class StatusResponse(BaseModel):
    """Generic status response."""

    status: str
    message: str


# === Routes ===


@router.get("/status", response_model=AIStatusResponse)
async def get_ai_status():
    """
    Get the status of the AI and memory systems.

    Returns:
        Dict with system status information
    """
    if not MEMORY_SYSTEM_AVAILABLE:
        return AIStatusResponse(
            memory_system_available=False, message="AI memory system not available"
        )

    try:
        return AIStatusResponse(
            memory_system_available=True,
            memory_system_enabled=MemoryIntegration.is_memory_enabled(),
            profiles_count=len(MemoryIntegration.get_all_profiles()),
        )
    except Exception as e:
        return AIStatusResponse(
            memory_system_available=True, memory_system_enabled=False, error=str(e)
        )


@router.post("/decision")
async def get_ai_decision(request: AIDecisionRequest):
    """
    Get a decision from an AI agent.

    Parameters:
        - request: A model containing:
            - archetype: The agent archetype (TAG, LAG, etc.)
            - game_state: Current game state
            - context: Additional context
            - player_id: ID of the player
            - use_memory: Whether to use memory (default: True)
            - intelligence_level: Agent intelligence level (default: expert)

    Returns:
        Dict with AI decision (action, amount, reasoning)
    """
    if not MEMORY_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI system not available")

    try:
        # Get decision from agent
        decision = await MemoryIntegration.get_agent_decision(
            archetype=request.archetype,
            game_state=request.game_state,
            context=request.context,
            player_id=request.player_id,
            use_memory=request.use_memory,
            intelligence_level=request.intelligence_level,
        )

        # Parse and validate response
        try:
            action, amount, metadata = AgentResponseParser.parse_response(decision)

            # Apply game rules
            action, amount = AgentResponseParser.apply_game_rules(
                action, amount, request.game_state
            )

            # Ensure all-in actions are consistently formatted
            if action and "all" in action.lower() and "in" in action.lower():
                action = "all-in"
                # For all-in, we'll set the amount on the game side based on the player's stack
                logging.info(
                    f"AI Connector: Normalized all-in action to 'all-in' format"
                )

            # Return validated decision
            return {
                "action": action,
                "amount": amount,
                "reasoning": metadata.get("reasoning", {}),
                "validated": True,
            }
        except ValueError:
            # Return the original decision but mark as not validated
            return {**decision, "validated": False}

    except Exception as e:
        logging.error(f"Error getting AI decision: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting AI decision: {str(e)}"
        )


@router.get("/profiles")
async def get_player_profiles():
    """
    Get all available player profiles.

    Returns:
        List of player profile dictionaries
    """
    if not MEMORY_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI memory system not available")

    try:
        return MemoryIntegration.get_all_profiles()
    except Exception as e:
        logging.error(f"Error getting player profiles: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting player profiles: {str(e)}"
        )


@router.get("/profiles/{player_id}")
async def get_player_profile(player_id: str):
    """
    Get a player's profile.

    Parameters:
        - player_id: ID of the player

    Returns:
        Dict with player profile data
    """
    if not MEMORY_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI memory system not available")

    try:
        profile = MemoryIntegration.get_player_profile(player_id)
        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Player profile not found: {player_id}"
            )
        return profile
    except Exception as e:
        logging.error(f"Error getting player profile: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting player profile: {str(e)}"
        )


@router.post("/memory/enable", response_model=StatusResponse)
async def enable_memory():
    """
    Enable the memory system.

    Returns:
        Dict with status message
    """
    if not MEMORY_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI memory system not available")

    try:
        MemoryIntegration.enable_memory()
        return StatusResponse(status="success", message="Memory system enabled")
    except Exception as e:
        logging.error(f"Error enabling memory system: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error enabling memory system: {str(e)}"
        )


@router.post("/memory/disable", response_model=StatusResponse)
async def disable_memory():
    """
    Disable the memory system.

    Returns:
        Dict with status message
    """
    if not MEMORY_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI memory system not available")

    try:
        MemoryIntegration.disable_memory()
        return StatusResponse(status="success", message="Memory system disabled")
    except Exception as e:
        logging.error(f"Error disabling memory system: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error disabling memory system: {str(e)}"
        )


@router.delete("/memory/clear", response_model=StatusResponse)
async def clear_memory():
    """
    Clear all memory data.

    Returns:
        Dict with status message
    """
    if not MEMORY_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI memory system not available")

    try:
        connector = MemoryIntegration._memory_service
        if connector:
            connector.clear_all_memory()
        return StatusResponse(status="success", message="Memory data cleared")
    except Exception as e:
        logging.error(f"Error clearing memory data: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error clearing memory data: {str(e)}"
        )


@router.post("/process-hand-history", response_model=StatusResponse)
async def process_hand_history(hand_data: Dict[str, Any]):
    """
    Process a hand history to update player profiles.

    Parameters:
        - hand_data: Hand history data

    Returns:
        Status response
    """
    if not MEMORY_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI memory system not available")

    try:
        MemoryIntegration.process_hand_history(hand_data)
        return StatusResponse(
            status="success",
            message=f"Processed hand #{hand_data.get('hand_number', 'Unknown')}",
        )
    except Exception as e:
        logging.error(f"Error processing hand history: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing hand history: {str(e)}"
        )


@router.get("/archetypes")
async def get_available_archetypes():
    """
    Get a list of available AI archetypes.

    Returns:
        List of available archetypes
    """
    try:
        # Get list of available archetypes
        from app.models.domain_models import ArchetypeEnum

        return [archetype.value for archetype in ArchetypeEnum]
    except Exception as e:
        logging.error(f"Error getting archetypes: {str(e)}")
        # Return basic archetypes if enum not available
        return ["TAG", "LAG", "TightPassive", "CallingStation", "Maniac", "Beginner"]
