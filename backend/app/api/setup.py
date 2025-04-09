"""
Setup API endpoints for game configuration from the frontend.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.models.domain_models import GameType
from app.services.game_service import GameService

router = APIRouter(prefix="/setup", tags=["setup"])


class PlayerSetup(BaseModel):
    """Model for player setup in a game."""
    name: str
    is_human: bool = False
    archetype: Optional[str] = None
    position: Optional[int] = None
    buy_in: int = 1000


class GameSetup(BaseModel):
    """Model for game setup from frontend."""
    game_mode: str  # 'cash' or 'tournament'
    
    # Cash game settings
    small_blind: int = 5
    big_blind: int = 10
    ante: int = 0
    min_buy_in: int = 400  # Chip amount (not BB)
    max_buy_in: int = 2000  # Chip amount (not BB)
    table_size: int = 6
    betting_structure: str = "no_limit"
    rake_percentage: float = 0.05
    rake_cap: int = 5
    
    # Tournament settings (ignored for cash games)
    tier: Optional[str] = None
    stage: Optional[str] = None
    buy_in_amount: Optional[int] = None
    starting_chips: Optional[int] = None
    
    # Player setup
    players: List[PlayerSetup]


class GameSetupResponse(BaseModel):
    """Response model for game setup."""
    game_id: str
    human_player_id: Optional[str] = None


# Dependency to get the game service
def get_game_service() -> GameService:
    """Get the game service singleton."""
    return GameService.get_instance()


@router.post("/game", response_model=GameSetupResponse)
async def setup_game(
    setup: GameSetup,
    service: GameService = Depends(get_game_service),
) -> GameSetupResponse:
    """
    Set up a new game based on frontend configuration.
    
    Args:
        setup: The game setup configuration
        service: The game service
        
    Returns:
        The created game ID and human player ID (if any)
    """
    # Log the incoming request data
    import logging
    logging.warning(f"Setup data received: {setup.dict()}")
    
    try:
        human_player_id = None
        
        # Create appropriate game type
        if setup.game_mode == "cash":
            # Create cash game
            game = service.create_cash_game(
                name="Cash Game",
                min_buy_in_chips=setup.min_buy_in,
                max_buy_in_chips=setup.max_buy_in,
                small_blind=setup.small_blind,
                big_blind=setup.big_blind,
                ante=setup.ante,
                table_size=setup.table_size,
                betting_structure=setup.betting_structure,
                rake_percentage=setup.rake_percentage,
                rake_cap=setup.rake_cap
            )
            
            # Log the created game details
            logging.warning(f"Game created with id: {game.id}, min_buy_in: {game.cash_game_info.min_buy_in}, max_buy_in: {game.cash_game_info.max_buy_in}")
            
            # Add players to cash game
            for player_setup in setup.players:
                logging.warning(f"Adding player: {player_setup.name}, buy_in: {player_setup.buy_in}, is_human: {player_setup.is_human}")
                try:
                    _, player = service.add_player_to_cash_game(
                        game_id=game.id,
                        name=player_setup.name,
                        buy_in=player_setup.buy_in,
                        is_human=player_setup.is_human,
                        archetype=player_setup.archetype,
                        position=player_setup.position
                    )
                except ValueError as ve:
                    logging.error(f"Player validation error: {str(ve)}")
                    raise
                
                # Store human player ID to return to frontend
                if player_setup.is_human:
                    human_player_id = player.id
            
            # Start the game automatically
            await service.start_game(game.id)
            
        elif setup.game_mode == "tournament":
            # Tournament setup not yet implemented
            raise HTTPException(status_code=501, detail="Tournament setup not yet implemented")
        else:
            raise HTTPException(status_code=400, detail="Invalid game mode")
        
        return GameSetupResponse(
            game_id=game.id,
            human_player_id=human_player_id
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))