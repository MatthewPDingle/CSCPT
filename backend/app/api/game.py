"""
Game API endpoints for the poker application.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
import uuid
import asyncio

from app.core.poker_game import (
    PokerGame,
    Player,
    PlayerAction,
    PlayerStatus,
    BettingRound,
)
from app.models.game_models import (
    CardModel,
    PlayerModel,
    GameStateModel,
    ActionRequest,
    ActionResponse,
    PotModel,
)
from app.core.websocket import game_notifier
from app.services.game_service import GameService
from app.core.utils import game_to_model, format_winners
from app.models.domain_models import GameType

router = APIRouter(prefix="/game", tags=["game"])


# Dependency to get the game service
def get_game_service() -> GameService:
    """Get the game service singleton (wrapped for sync/async consistency)."""
    svc = GameService.get_instance()
    # Proxy routes start_game and process_action to always return an awaitable in async contexts
    class GameServiceProxy:
        def __init__(self, service):
            self._svc = service
        def __getattr__(self, name):
            return getattr(self._svc, name)
        async def start_game(self, game_id: str):
            import asyncio
            res = self._svc.start_game(game_id)
            if asyncio.iscoroutine(res):
                return await res
            return res
        async def process_action(self, game_id: str, player_id: str, action, amount=None):
            import asyncio
            res = self._svc.process_action(game_id, player_id, action, amount)
            if asyncio.iscoroutine(res):
                return await res
            return res
    return GameServiceProxy(svc)


@router.post("/create", response_model=GameStateModel)
async def create_game(
    small_blind: int = 10,
    big_blind: int = 20,
    service: GameService = Depends(get_game_service),
) -> GameStateModel:
    """
    Create a new poker game.

    Args:
        small_blind: The small blind amount
        big_blind: The big blind amount
        service: The game service

    Returns:
        The initial game state
    """
    # Create a new game using the service
    game = service.create_game(
        game_type=GameType.CASH,
        min_bet=big_blind,
        small_blind=small_blind,
        big_blind=big_blind,
    )

    # Get the PokerGame instance
    poker_game = service.poker_games.get(game.id)
    if not poker_game:
        # Create poker game if not present
        poker_game = PokerGame(
            small_blind=small_blind,
            big_blind=big_blind,
            game_id=game.id,
            hand_history_recorder=service.hand_history_recorder,
        )
        service.poker_games[game.id] = poker_game

    return GameStateModel(
        game_id=game.id,
        players=[],
        community_cards=[],
        pots=[PotModel(name="Main Pot", amount=0, eligible_player_ids=[])],
        total_pot=0,
        current_round="PREFLOP",
        button_position=0,
        current_player_idx=0,
        current_bet=0,
        small_blind=small_blind,
        big_blind=big_blind,
    )


@router.post("/join/{game_id}", response_model=PlayerModel)
async def join_game(
    game_id: str,
    player_name: str,
    buy_in: int = 1000,
    service: GameService = Depends(get_game_service),
) -> PlayerModel:
    """
    Join an existing poker game.

    Args:
        game_id: The ID of the game to join
        player_name: The display name of the player
        buy_in: The amount of chips to start with
        service: The game service

    Returns:
        The created player object
    """
    try:
        # Call the service to add a player
        game, player = service.add_player(
            game_id=game_id, name=player_name, is_human=True
        )

        # Get the poker game
        poker_game = service.poker_games.get(game_id)
        if not poker_game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Add player to poker game if needed
        poker_player = next(
            (p for p in poker_game.players if p.player_id == player.id), None
        )
        if not poker_player:
            poker_player = poker_game.add_player(player.id, player_name, buy_in)

        # Return the player model
        return PlayerModel(
            player_id=player.id,
            name=player_name,
            chips=buy_in,
            position=player.position,
            status=player.status.name,
            current_bet=0,
            total_bet=0,
            cards=None,  # No cards yet
        )

    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/start/{game_id}", response_model=GameStateModel)
async def start_game(
    game_id: str, service: GameService = Depends(get_game_service)
) -> GameStateModel:
    """
    Start a poker game, dealing cards to players.

    Args:
        game_id: The ID of the game to start
        service: The game service

    Returns:
        The updated game state
    """
    try:
        # Start the game using the service
        game = await service.start_game(game_id)

        # Get the poker game
        poker_game = service.poker_games.get(game_id)
        if not poker_game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Notify WebSocket clients
        asyncio.create_task(game_notifier.notify_game_update(game_id, poker_game))

        # Send action request to first player
        asyncio.create_task(game_notifier.notify_action_request(game_id, poker_game))

        # Convert to API model
        return game_to_model(game_id, poker_game)

    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/next-hand/{game_id}", response_model=GameStateModel)
async def next_hand(
    game_id: str, service: GameService = Depends(get_game_service)
) -> GameStateModel:
    """
    Start the next hand in an existing game.

    Args:
        game_id: The ID of the game
        service: The game service

    Returns:
        The updated game state
    """
    try:
        # Get the poker game
        poker_game = service.poker_games.get(game_id)
        if not poker_game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Check if current hand is complete
        if poker_game.current_round != BettingRound.SHOWDOWN:
            raise HTTPException(status_code=400, detail="Current hand is not complete")

        # Move the button and start a new hand
        poker_game.move_button()
        game = service._start_new_hand(service.get_game(game_id))

        # Notify WebSocket clients
        asyncio.create_task(game_notifier.notify_game_update(game_id, poker_game))

        # Send action request to first player
        asyncio.create_task(game_notifier.notify_action_request(game_id, poker_game))

        # Convert to API model
        return game_to_model(game_id, poker_game)

    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/action/{game_id}", response_model=ActionResponse)
async def player_action(
    game_id: str,
    action_request: ActionRequest,
    service: GameService = Depends(get_game_service),
) -> ActionResponse:
    """
    Process a player action (bet, fold, etc).

    Args:
        game_id: The ID of the game
        action_request: The action to perform
        service: The game service

    Returns:
        The result of the action and updated game state
    """
    try:
        # Get the poker game
        poker_game = service.poker_games.get(game_id)
        if not poker_game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Find the player
        player = next(
            (p for p in poker_game.players if p.player_id == action_request.player_id),
            None,
        )

        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        # Validate it's the player's turn
        active_players = [
            p
            for p in poker_game.players
            if p.status in {PlayerStatus.ACTIVE, PlayerStatus.ALL_IN}
        ]
        if active_players[poker_game.current_player_idx].player_id != player.player_id:
            return ActionResponse(
                success=False,
                message="Not your turn to act",
                game_state=game_to_model(game_id, poker_game),
            )

        # Get valid actions
        valid_actions = poker_game.get_valid_actions(player)
        valid_action_types = [a[0] for a in valid_actions]

        # Parse and validate the action
        try:
            action = PlayerAction[action_request.action]
        except KeyError:
            return ActionResponse(
                success=False,
                message=f"Invalid action. Valid actions: {[a.name for a in valid_action_types]}",
                game_state=game_to_model(game_id, poker_game),
            )

        if action not in valid_action_types:
            return ActionResponse(
                success=False,
                message=f"Invalid action. Valid actions: {[a.name for a in valid_action_types]}",
                game_state=game_to_model(game_id, poker_game),
            )

        # Process the action through the service
        from app.models.domain_models import PlayerAction as DomainPlayerAction

        action_map = {
            PlayerAction.FOLD: DomainPlayerAction.FOLD,
            PlayerAction.CHECK: DomainPlayerAction.CHECK,
            PlayerAction.CALL: DomainPlayerAction.CALL,
            PlayerAction.BET: DomainPlayerAction.BET,
            PlayerAction.RAISE: DomainPlayerAction.RAISE,
            PlayerAction.ALL_IN: DomainPlayerAction.ALL_IN,
        }
        domain_action = action_map.get(action)

        # Process in both service (for history) and directly in poker game (for current state)
        game = await service.process_action(
            game_id, player.player_id, domain_action, action_request.amount
        )
        success = await poker_game.process_action(player, action, action_request.amount)

        if not success:
            return ActionResponse(
                success=False,
                message=f"Failed to process action {action.name}",
                game_state=game_to_model(game_id, poker_game),
            )

        # Notify WebSocket clients about the action and updated state,
        # passing totals for clear poker terminology
        post_street_bet = player.current_bet
        post_hand_bet = player.total_bet
        asyncio.create_task(
            game_notifier.notify_player_action(
                game_id,
                player.player_id,
                action.name,
                action_request.amount,
                total_street_bet=post_street_bet,
                total_hand_bet=(post_hand_bet if action == PlayerAction.ALL_IN else None),
            )
        )

        asyncio.create_task(game_notifier.notify_game_update(game_id, poker_game))

        # Check if we need to automatically advance the game (e.g., when all players have checked/called)
        # This happens when the betting round is complete but we're not at showdown yet
        if poker_game.current_round == BettingRound.SHOWDOWN:
            # Notify about hand results
            asyncio.create_task(game_notifier.notify_hand_result(game_id, poker_game))

            # Hand is complete, get new game state
            return ActionResponse(
                success=True,
                message=f"Hand complete. Winners: {format_winners(poker_game)}",
                game_state=game_to_model(game_id, poker_game),
            )
        else:
            # Send action request to next player
            asyncio.create_task(
                game_notifier.notify_action_request(game_id, poker_game)
            )

        # Return success
        return ActionResponse(
            success=True,
            message=f"Action {action.name} processed",
            game_state=game_to_model(game_id, poker_game),
        )

    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ai-move/{game_id}", response_model=ActionResponse)
async def trigger_ai_move(
    game_id: str,
    service: GameService = Depends(get_game_service),
) -> ActionResponse:
    """
    DEBUG ENDPOINT: Manually triggers the current player to make an AI move.
    
    WARNING: This endpoint is for debugging purposes only. In normal gameplay,
    AI players should act automatically through the chain of actions in the backend.
    Using this endpoint may disrupt the natural flow of the game and cause unexpected behavior.
    
    Args:
        game_id: The ID of the game
        service: The game service
        
    Returns:
        The result of the action
    """
    import logging
    logging.warning(
        "DEBUG AI MOVE ENDPOINT CALLED: This is a debug-only endpoint and should not be used "
        "in normal gameplay. AI players should act automatically."
    )
    try:
        # Get the poker game
        poker_game = service.poker_games.get(game_id)
        if not poker_game:
            raise HTTPException(status_code=404, detail="Game not found")
            
        # Get the current player
        active_players = [
            p for p in poker_game.players
            if p.status in {PlayerStatus.ACTIVE, PlayerStatus.ALL_IN}
        ]
        
        if not active_players or poker_game.current_player_idx >= len(active_players):
            raise HTTPException(status_code=400, detail="No active player to move")
            
        current_player = active_players[poker_game.current_player_idx]
        
        # Get the domain player to check if it's AI
        game = service.get_game(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
            
        domain_player = next((p for p in game.players if p.id == current_player.player_id), None)
        if not domain_player:
            raise HTTPException(status_code=404, detail="Player not found")
            
        # If it's a human player, treat it like an AI for testing
        if domain_player.is_human:
            import logging
            logging.warning(f"Treating human player {domain_player.name} as AI for testing purposes")
        
        # Trigger the AI action
        import logging
        try:
            logging.info(f"Requesting AI action for player {current_player.name} in game {game_id}")
            # Use the service method for requesting AI action
            await service._request_and_process_ai_action(game_id, current_player.player_id)
            
            # Get updated game state after AI move - poker_game should already be updated
            # Use the same poker_game instance as it should have been updated by _request_and_process_ai_action
            updated_poker_game = poker_game
            logging.info(f"Using updated poker game for game {game_id}")
                
            # Return success with updated game state
            logging.info(f"AI move successfully triggered for player {current_player.name}")
            return ActionResponse(
                success=True,
                message=f"AI move triggered for player {current_player.name}",
                game_state=game_to_model(game_id, updated_poker_game),
            )
        except Exception as e:
            logging.error(f"Error processing AI action: {str(e)}")
            # Still return a success response to avoid CORS issues
            return ActionResponse(
                success=False,
                message=f"Error triggering AI move: {str(e)}",
                game_state=game_to_model(game_id, poker_game),
            )
            
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))