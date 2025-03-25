"""
Game API endpoints using the repository pattern and service layer.
This is an improved version that uses the new storage system.
"""
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Path, Query, Depends

from app.models.domain_models import (
    Game, Player, Hand, ActionHistory, GameType, 
    GameStatus, PlayerAction, PlayerStatus
)
from app.services.game_service import GameService

router = APIRouter(prefix="/v2/game", tags=["game"])

# Dependency to get the game service
def get_game_service():
    """Get the game service instance."""
    return GameService()


@router.post("/create", response_model=Game)
async def create_game(
    game_type: GameType,
    name: Optional[str] = None,
    buy_in: Optional[int] = None,
    small_blind: Optional[int] = None,
    big_blind: Optional[int] = None,
    ante: Optional[int] = None,
    tier: Optional[str] = None,
    stage: Optional[str] = None,
    starting_chips: Optional[int] = None,
    game_service: GameService = Depends(get_game_service)
) -> Game:
    """
    Create a new poker game.
    
    Args:
        game_type: Type of game (cash or tournament)
        name: Optional name for the game
        buy_in: Buy-in amount for cash games
        small_blind: Small blind amount
        big_blind: Big blind amount
        ante: Ante amount
        tier: Tournament tier
        stage: Tournament stage
        starting_chips: Starting chips for tournament
        
    Returns:
        The created game
    """
    options = {}
    
    # Set options based on game type
    if game_type == GameType.CASH:
        if buy_in is not None:
            options["buy_in"] = buy_in
        if small_blind is not None:
            options["min_bet"] = small_blind * 2
        if ante is not None:
            options["ante"] = ante
    else:  # Tournament
        if tier is not None:
            options["tier"] = tier
        if stage is not None:
            options["stage"] = stage
        if starting_chips is not None:
            options["starting_chips"] = starting_chips
            
    # Create the game
    game = game_service.create_game(game_type, name, **options)
    return game


@router.get("/{game_id}", response_model=Game)
async def get_game(
    game_id: str = Path(..., title="The ID of the game to get"),
    game_service: GameService = Depends(get_game_service)
) -> Game:
    """
    Get a game by ID.
    
    Args:
        game_id: ID of the game to get
        
    Returns:
        The game
        
    Raises:
        HTTPException: If the game doesn't exist
    """
    game = game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
    return game


@router.post("/{game_id}/join", response_model=Game)
async def join_game(
    game_id: str = Path(..., title="The ID of the game to join"),
    name: str = Query(..., title="The player's name"),
    is_human: bool = Query(True, title="Whether the player is human"),
    archetype: Optional[str] = Query(None, title="The AI archetype for AI players"),
    position: Optional[int] = Query(None, title="The position at the table"),
    game_service: GameService = Depends(get_game_service)
) -> Game:
    """
    Join a game as a player.
    
    Args:
        game_id: ID of the game to join
        name: Player name
        is_human: Whether the player is human
        archetype: AI archetype for AI players
        position: Optional position at the table
        
    Returns:
        The updated game
        
    Raises:
        HTTPException: If there's an error joining the game
    """
    try:
        game, player = game_service.add_player(
            game_id=game_id,
            name=name,
            is_human=is_human,
            archetype=archetype,
            position=position
        )
        return game
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/start", response_model=Game)
async def start_game(
    game_id: str = Path(..., title="The ID of the game to start"),
    game_service: GameService = Depends(get_game_service)
) -> Game:
    """
    Start a poker game.
    
    Args:
        game_id: ID of the game to start
        
    Returns:
        The updated game
        
    Raises:
        HTTPException: If there's an error starting the game
    """
    try:
        game = game_service.start_game(game_id)
        return game
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/action", response_model=Game)
async def player_action(
    game_id: str = Path(..., title="The ID of the game"),
    player_id: str = Query(..., title="The ID of the player taking the action"),
    action: PlayerAction = Query(..., title="The action to take"),
    amount: Optional[int] = Query(None, title="The amount for bet/raise actions"),
    game_service: GameService = Depends(get_game_service)
) -> Game:
    """
    Take an action in a poker game.
    
    Args:
        game_id: ID of the game
        player_id: ID of the player taking the action
        action: The action to take
        amount: The amount for bet/raise actions
        
    Returns:
        The updated game
        
    Raises:
        HTTPException: If there's an error processing the action
    """
    try:
        game = game_service.process_action(
            game_id=game_id,
            player_id=player_id,
            action=action,
            amount=amount
        )
        return game
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list/active", response_model=List[Game])
async def list_active_games(
    game_service: GameService = Depends(get_game_service)
) -> List[Game]:
    """
    List all active games.
    
    Returns:
        List of active games
    """
    return game_service.game_repo.get_active_games()


@router.get("/{game_id}/history", response_model=List[ActionHistory])
async def get_game_history(
    game_id: str = Path(..., title="The ID of the game"),
    game_service: GameService = Depends(get_game_service)
) -> List[ActionHistory]:
    """
    Get the action history for a game.
    
    Args:
        game_id: ID of the game
        
    Returns:
        List of action history records
        
    Raises:
        HTTPException: If the game doesn't exist
    """
    game = game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
        
    return game_service.action_repo.get_by_game(game_id)