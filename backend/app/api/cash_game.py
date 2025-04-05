"""
Cash game API endpoints for the poker application.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.models.domain_models import GameType, BettingStructure
from app.services.game_service import GameService

router = APIRouter(prefix="/cash-games", tags=["cash-games"])


class PlayerResponse(BaseModel):
    """Response model for player operations."""
    id: str
    name: str
    chips: int
    position: int
    status: str


class GameResponse(BaseModel):
    """Response model for game operations."""
    id: str
    name: str
    status: str
    type: str
    players: List[PlayerResponse]


class CashGameRequest(BaseModel):
    """Request model for creating a cash game."""
    name: Optional[str] = None
    min_buy_in: int = 40  # In big blinds (will be converted to chips)
    max_buy_in: int = 100  # In big blinds (will be converted to chips)
    small_blind: int = 1
    big_blind: int = 2
    ante: int = 0
    table_size: int = 9
    betting_structure: str = "no_limit"
    rake_percentage: float = 0.05
    rake_cap: int = 5


class PlayerRequest(BaseModel):
    """Request model for adding a player to a game."""
    name: str
    buy_in: int
    is_human: bool = False
    user_id: Optional[str] = None
    archetype: Optional[str] = None
    position: Optional[int] = None


class RebuyRequest(BaseModel):
    """Request model for rebuying chips."""
    amount: int


@router.post("/", response_model=GameResponse)
async def create_cash_game(game_request: CashGameRequest):
    """Create a new cash game."""
    game_service = GameService.get_instance()
    
    try:
        # Convert big blind multiples to actual chip amounts
        min_buy_in_chips = game_request.min_buy_in * game_request.big_blind
        max_buy_in_chips = game_request.max_buy_in * game_request.big_blind
        
        game = game_service.create_cash_game(
            name=game_request.name,
            min_buy_in_chips=min_buy_in_chips,
            max_buy_in_chips=max_buy_in_chips,
            small_blind=game_request.small_blind,
            big_blind=game_request.big_blind,
            ante=game_request.ante,
            table_size=game_request.table_size,
            betting_structure=game_request.betting_structure,
            rake_percentage=game_request.rake_percentage,
            rake_cap=game_request.rake_cap
        )
        return GameResponse(
            id=game.id,
            name=game.name,
            status=game.status.value,
            type=game.type.value,
            players=[PlayerResponse(
                id=p.id,
                name=p.name,
                chips=p.chips,
                position=p.position,
                status=p.status.value
            ) for p in game.players]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/players", response_model=PlayerResponse)
async def add_player_to_cash_game(game_id: str, player_request: PlayerRequest):
    """Add a player to a cash game with specified buy-in."""
    game_service = GameService.get_instance()
    try:
        _, player = game_service.add_player_to_cash_game(
            game_id=game_id,
            name=player_request.name,
            buy_in=player_request.buy_in,
            is_human=player_request.is_human,
            user_id=player_request.user_id,
            archetype=player_request.archetype,
            position=player_request.position
        )
        return PlayerResponse(
            id=player.id,
            name=player.name,
            chips=player.chips,
            position=player.position,
            status=player.status.value
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/players/{player_id}/cashout")
async def cash_out_player(game_id: str, player_id: str):
    """Remove a player from a cash game and return their final chip count."""
    game_service = GameService.get_instance()
    try:
        chips = game_service.cash_out_player(game_id, player_id)
        return {"success": True, "chips": chips}
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/players/{player_id}/rebuy", response_model=PlayerResponse)
async def rebuy_player(game_id: str, player_id: str, rebuy_request: RebuyRequest):
    """Add chips to a player in a cash game (rebuy)."""
    game_service = GameService.get_instance()
    try:
        player = game_service.rebuy_player(game_id, player_id, rebuy_request.amount)
        return PlayerResponse(
            id=player.id,
            name=player.name,
            chips=player.chips,
            position=player.position,
            status=player.status.value
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/players/{player_id}/topup", response_model=PlayerResponse)
async def top_up_player(game_id: str, player_id: str):
    """Top up a player's chips to the maximum buy-in amount."""
    game_service = GameService.get_instance()
    try:
        player, amount = game_service.top_up_player(game_id, player_id)
        return PlayerResponse(
            id=player.id,
            name=player.name,
            chips=player.chips,
            position=player.position,
            status=player.status.value,
            added_chips=amount
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))