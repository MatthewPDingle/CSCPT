"""
API routes for AI integration and memory system.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional, Any
import asyncio
import json
from datetime import datetime
import logging

# Try to import memory integration
try:
    from ai.memory_integration import MemoryIntegration
    MEMORY_SYSTEM_AVAILABLE = True
except ImportError:
    MEMORY_SYSTEM_AVAILABLE = False
    logging.warning("AI memory system not available. AI memory features will be disabled.")

router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/status")
async def get_ai_status():
    """
    Get the status of the AI and memory systems.
    
    Returns:
        Dict with system status information
    """
    if not MEMORY_SYSTEM_AVAILABLE:
        return {
            "memory_system_available": False,
            "message": "AI memory system not available"
        }
        
    try:
        return {
            "memory_system_available": True,
            "memory_system_enabled": MemoryIntegration.is_memory_enabled(),
            "profiles_count": len(MemoryIntegration.get_all_profiles())
        }
    except Exception as e:
        return {
            "memory_system_available": True,
            "memory_system_enabled": False,
            "error": str(e)
        }

@router.post("/decision")
async def get_ai_decision(request: Dict[str, Any]):
    """
    Get a decision from an AI agent.
    
    Parameters:
        - request: A dictionary containing:
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
        # Extract parameters
        archetype = request.get("archetype")
        game_state = request.get("game_state", {})
        context = request.get("context", {})
        player_id = request.get("player_id")
        use_memory = request.get("use_memory", True)
        intelligence_level = request.get("intelligence_level", "expert")
        
        # Validate required parameters
        if not archetype:
            raise HTTPException(status_code=400, detail="Missing required parameter: archetype")
        if not player_id:
            raise HTTPException(status_code=400, detail="Missing required parameter: player_id")
            
        # Get decision from agent
        decision = await MemoryIntegration.get_agent_decision(
            archetype=archetype,
            game_state=game_state,
            context=context,
            player_id=player_id,
            use_memory=use_memory,
            intelligence_level=intelligence_level
        )
        
        return decision
        
    except Exception as e:
        logging.error(f"Error getting AI decision: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting AI decision: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Error getting player profiles: {str(e)}")

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
            raise HTTPException(status_code=404, detail=f"Player profile not found: {player_id}")
        return profile
    except Exception as e:
        logging.error(f"Error getting player profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting player profile: {str(e)}")

@router.post("/memory/enable")
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
        return {"status": "success", "message": "Memory system enabled"}
    except Exception as e:
        logging.error(f"Error enabling memory system: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enabling memory system: {str(e)}")

@router.post("/memory/disable")
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
        return {"status": "success", "message": "Memory system disabled"}
    except Exception as e:
        logging.error(f"Error disabling memory system: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error disabling memory system: {str(e)}")

@router.delete("/memory/clear")
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
        return {"status": "success", "message": "Memory data cleared"}
    except Exception as e:
        logging.error(f"Error clearing memory data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing memory data: {str(e)}")