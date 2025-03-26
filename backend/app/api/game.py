"""
Game API endpoints for the poker application.
"""
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import uuid

from app.core.poker_game import PokerGame, Player, PlayerAction, PlayerStatus
from app.models.game_models import (
    CardModel, 
    PlayerModel, 
    GameStateModel, 
    ActionRequest, 
    ActionResponse
)

router = APIRouter(prefix="/game", tags=["game"])

# In-memory storage of active games
active_games: Dict[str, PokerGame] = {}


@router.post("/create", response_model=GameStateModel)
async def create_game(small_blind: int = 10, big_blind: int = 20) -> GameStateModel:
    """
    Create a new poker game.
    
    Args:
        small_blind: The small blind amount
        big_blind: The big blind amount
        
    Returns:
        The initial game state
    """
    game_id = str(uuid.uuid4())
    game = PokerGame(small_blind=small_blind, big_blind=big_blind)
    active_games[game_id] = game
    
    return GameStateModel(
        game_id=game_id,
        players=[],
        community_cards=[],
        pots=[PotModel(name="Main Pot", amount=0, eligible_player_ids=[])],
        total_pot=0,
        current_round="PREFLOP",
        button_position=0,
        current_player_idx=0,
        current_bet=0,
        small_blind=small_blind,
        big_blind=big_blind
    )


@router.post("/join/{game_id}", response_model=PlayerModel)
async def join_game(
    game_id: str, 
    player_name: str, 
    buy_in: int = 1000
) -> PlayerModel:
    """
    Join an existing poker game.
    
    Args:
        game_id: The ID of the game to join
        player_name: The display name of the player
        buy_in: The amount of chips to start with
        
    Returns:
        The created player object
    """
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")
        
    game = active_games[game_id]
    
    # Create a unique player ID
    player_id = str(uuid.uuid4())
    
    # Add player to the game
    player = game.add_player(player_id, player_name, buy_in)
    
    # Return the player model
    return PlayerModel(
        player_id=player_id,
        name=player_name,
        chips=buy_in,
        position=player.position,
        status=player.status.name,
        current_bet=0,
        total_bet=0,
        cards=None  # No cards yet
    )


@router.post("/start/{game_id}", response_model=GameStateModel)
async def start_game(game_id: str) -> GameStateModel:
    """
    Start a poker game, dealing cards to players.
    
    Args:
        game_id: The ID of the game to start
        
    Returns:
        The updated game state
    """
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")
        
    game = active_games[game_id]
    
    if len(game.players) < 2:
        raise HTTPException(
            status_code=400, 
            detail="Need at least 2 players to start a game"
        )
        
    # Start the hand
    game.start_hand()
    
    # Convert to API model
    return _game_to_model(game_id, game)


@router.post("/next-hand/{game_id}", response_model=GameStateModel)
async def next_hand(game_id: str) -> GameStateModel:
    """
    Start the next hand in an existing game.
    
    Args:
        game_id: The ID of the game
        
    Returns:
        The updated game state
    """
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")
        
    game = active_games[game_id]
    
    # Check if current hand is complete
    if game.current_round != BettingRound.SHOWDOWN:
        raise HTTPException(
            status_code=400, 
            detail="Current hand is not complete"
        )
        
    # Move the button
    game.move_button()
    
    # Start new hand
    game.start_hand()
    
    # Convert to API model
    return _game_to_model(game_id, game)


@router.post("/action/{game_id}", response_model=ActionResponse)
async def player_action(
    game_id: str, 
    action_request: ActionRequest
) -> ActionResponse:
    """
    Process a player action (bet, fold, etc).
    
    Args:
        game_id: The ID of the game
        action_request: The action to perform
        
    Returns:
        The result of the action and updated game state
    """
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")
        
    game = active_games[game_id]
    
    # Find the player
    player = next(
        (p for p in game.players if p.player_id == action_request.player_id), 
        None
    )
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
        
    # Validate it's the player's turn
    active_players = [p for p in game.players 
                     if p.status in {PlayerStatus.ACTIVE, PlayerStatus.ALL_IN}]
    if active_players[game.current_player_idx].player_id != player.player_id:
        return ActionResponse(
            success=False,
            message="Not your turn to act",
            game_state=_game_to_model(game_id, game)
        )
        
    # Get valid actions
    valid_actions = game.get_valid_actions(player)
    valid_action_types = [a[0] for a in valid_actions]
    
    # Parse and validate the action
    try:
        action = PlayerAction[action_request.action]
    except KeyError:
        return ActionResponse(
            success=False,
            message=f"Invalid action. Valid actions: {[a.name for a in valid_action_types]}",
            game_state=_game_to_model(game_id, game)
        )
        
    if action not in valid_action_types:
        return ActionResponse(
            success=False,
            message=f"Invalid action. Valid actions: {[a.name for a in valid_action_types]}",
            game_state=_game_to_model(game_id, game)
        )
        
    # Process the action
    amount = action_request.amount
    success = game.process_action(player, action, amount)
    
    if not success:
        return ActionResponse(
            success=False,
            message=f"Failed to process action {action.name}",
            game_state=_game_to_model(game_id, game)
        )
    
    # Check if we need to automatically advance the game (e.g., when all players have checked/called)
    # This happens when the betting round is complete but we're not at showdown yet
    if game.current_round == BettingRound.SHOWDOWN:
        # Hand is complete, get new game state
        return ActionResponse(
            success=True,
            message=f"Hand complete. Winners: {_format_winners(game)}",
            game_state=_game_to_model(game_id, game)
        )
    
    # Return success
    return ActionResponse(
        success=True,
        message=f"Action {action.name} processed",
        game_state=_game_to_model(game_id, game)
    )


def _format_winners(game: PokerGame) -> str:
    """Format the winners for the response message."""
    if not game.hand_winners:
        return "No winners yet"
        
    result = []
    for pot_id, winners in game.hand_winners.items():
        winner_names = [p.name for p in winners]
        
        # Find the pot amount by pot name
        pot_amount = 0
        for pot in game.pots:
            if pot.name == pot_id or f"pot_{pot_id}" == pot_id:
                pot_amount = pot.amount
                break
        
        pot_display = f"{pot_id} (${pot_amount})"
        
        if len(winner_names) == 1:
            result.append(f"{winner_names[0]} wins {pot_display}")
        else:
            result.append(f"{', '.join(winner_names)} split {pot_display}")
            
    return "; ".join(result)


def _game_to_model(game_id: str, game: PokerGame) -> GameStateModel:
    """
    Convert a PokerGame to a GameStateModel for API responses.
    
    Args:
        game_id: The ID of the game
        game: The PokerGame instance
        
    Returns:
        A GameStateModel representing the game state
    """
    # Convert community cards
    community_cards = [
        CardModel(
            rank=str(card.rank),
            suit=card.suit.name[0]
        )
        for card in game.community_cards
    ]
    
    # Convert players
    players = []
    for player in game.players:
        # Only include player's cards if they have been dealt
        cards = None
        if player.hand and len(player.hand.cards) > 0:
            cards = [
                CardModel(
                    rank=str(card.rank),
                    suit=card.suit.name[0]
                )
                for card in player.hand.cards
            ]
            
        players.append(
            PlayerModel(
                player_id=player.player_id,
                name=player.name,
                chips=player.chips,
                position=player.position,
                status=player.status.name,
                current_bet=player.current_bet,
                total_bet=player.total_bet,
                cards=cards
            )
        )
    
    # Convert pots
    pots = []
    for pot in game.pots:
        pots.append(
            PotModel(
                name=pot.name or "Pot",
                amount=pot.amount,
                eligible_player_ids=list(pot.eligible_players)
            )
        )
    
    # If no pots, create a default main pot
    if not pots:
        pots = [PotModel(name="Main Pot", amount=0, eligible_player_ids=[])]
    
    # Calculate total pot amount
    total_pot = sum(pot.amount for pot in game.pots)
    
    # Create the game state model
    return GameStateModel(
        game_id=game_id,
        players=players,
        community_cards=community_cards,
        pots=pots,
        total_pot=total_pot,
        current_round=game.current_round.name,
        button_position=game.button_position,
        current_player_idx=game.current_player_idx,
        current_bet=game.current_bet,
        small_blind=game.small_blind,
        big_blind=game.big_blind
    )