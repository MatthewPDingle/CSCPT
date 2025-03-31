"""History-related API endpoints for the poker application.
This module provides access to hand histories and player statistics."""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.domain_models import GameType, HandHistory, PlayerStats
from app.services.game_service import GameService

router = APIRouter(prefix="/history", tags=["history"])


# Dependency to get the game service
def get_game_service() -> GameService:
    """Get the game service singleton."""
    return GameService.get_instance()


@router.get("/game/{game_id}", response_model=List[Dict[str, Any]])
async def get_game_hand_histories(
    game_id: str, service: GameService = Depends(get_game_service)
) -> List[Dict[str, Any]]:
    """
    Get all hand histories for a game.

    Args:
        game_id: ID of the game

    Returns:
        List of hand histories
    """
    game = service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get hand histories from service
    hand_histories = service.get_game_hand_histories(game_id)

    # Convert to dictionaries for API response
    return [hand.dict() for hand in hand_histories]


@router.get("/hand/{game_id}/{hand_id}", response_model=Dict[str, Any])
async def get_hand_history(
    game_id: str, hand_id: str, service: GameService = Depends(get_game_service)
) -> Dict[str, Any]:
    """
    Get detailed history for a specific hand.

    Args:
        game_id: ID of the game
        hand_id: ID of the hand

    Returns:
        Detailed hand history
    """
    game = service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    hand_history = service.get_hand_history(hand_id)
    if not hand_history:
        raise HTTPException(status_code=404, detail="Hand history not found")

    if hand_history.game_id != game_id:
        raise HTTPException(status_code=403, detail="Hand does not belong to this game")

    return hand_history.dict()


@router.get("/player/{player_id}/stats", response_model=Dict[str, Any])
async def get_player_statistics(
    player_id: str,
    game_id: Optional[str] = None,
    service: GameService = Depends(get_game_service),
) -> Dict[str, Any]:
    """
    Get detailed statistics for a player.

    Args:
        player_id: ID of the player
        game_id: Optional ID of a specific game to limit stats to

    Returns:
        Player statistics
    """
    stats = service.get_player_stats(player_id, game_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Player or stats not found")

    return stats.dict()


@router.get("/player/{player_id}/hands", response_model=List[Dict[str, Any]])
async def get_player_hands(
    player_id: str,
    game_id: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    service: GameService = Depends(get_game_service),
) -> List[Dict[str, Any]]:
    """
    Get hands a player has participated in.

    Args:
        player_id: ID of the player
        game_id: Optional ID of a specific game to limit hands to
        limit: Maximum number of hands to return

    Returns:
        List of hand histories
    """
    # Get repository from service
    hand_history_repo = service.repo_factory.get_repository(
        service.hand_history_repo.__class__
    )

    # Get hands for player
    hands = hand_history_repo.get_by_player(player_id)

    # Filter by game_id if provided
    if game_id:
        hands = [h for h in hands if h.game_id == game_id]

    # Sort by timestamp (newest first) and limit
    hands = sorted(hands, key=lambda h: h.timestamp_start, reverse=True)[:limit]

    # Convert to dictionaries for API response
    return [hand.dict() for hand in hands]
