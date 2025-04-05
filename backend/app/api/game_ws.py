"""
WebSocket endpoints for real-time game communication.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from typing import Optional, Dict, Any
import json
from datetime import datetime
import asyncio

from app.core.websocket import connection_manager, game_notifier
from app.core.poker_game import PokerGame, PlayerAction, PlayerStatus, BettingRound
from app.services.game_service import GameService
from app.core.utils import game_to_model

router = APIRouter(prefix="/ws", tags=["websocket"])


# Dependency to get the game service
def get_game_service() -> GameService:
    """Get the game service singleton."""
    return GameService.get_instance()


@router.websocket("/game/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_id: str,
    player_id: Optional[str] = Query(None),
    service: GameService = Depends(get_game_service),
):
    """
    WebSocket endpoint for real-time game updates.

    Args:
        websocket: The WebSocket connection
        game_id: The ID of the game to connect to
        player_id: The ID of the player connecting (None for observers)
        service: The game service
    """
    # Add logging for debugging
    import logging
    logging.warning(f"WebSocket connection attempt - game_id: {game_id}, player_id: {player_id}")
    
    # Verify game exists
    game = service.get_game(game_id)
    if not game:
        logging.error(f"WebSocket connection failed - Game {game_id} not found")
        await websocket.close(code=1008, reason="Game not found")
        return

    # Get the poker game
    poker_game = service.poker_games.get(game_id)
    if not poker_game:
        logging.error(f"WebSocket connection failed - Poker game {game_id} not found")
        await websocket.close(code=1008, reason="Game not found")
        return

    # Verify player exists (if a player_id was provided)
    if player_id:
        player = next((p for p in poker_game.players if p.player_id == player_id), None)
        if not player:
            logging.error(f"WebSocket connection failed - Player {player_id} not found in game {game_id}")
            logging.warning(f"Available players: {[(p.player_id, p.name) for p in poker_game.players]}")
            await websocket.close(code=1008, reason="Player not found")
            return
        logging.warning(f"Player {player.name} connected via WebSocket")

    # Accept the connection
    await connection_manager.connect(websocket, game_id, player_id)

    try:
        import logging
        
        # Variable to track if state has been sent to avoid duplicates
        game_state_sent = False
        
        logging.warning(f"Sending initial game state for game {game_id}")
        
        # Send initial game state
        await game_notifier.notify_game_update(game_id, poker_game)
        game_state_sent = True

        # If it's this player's turn, send action request
        if player_id:
            active_players = [
                p
                for p in poker_game.players
                if p.status in {PlayerStatus.ACTIVE, PlayerStatus.ALL_IN}
            ]
            if (
                active_players
                and poker_game.current_player_idx < len(active_players)
                and active_players[poker_game.current_player_idx].player_id == player_id
            ):
                logging.warning(f"Requesting action from player {player_id}")
                await game_notifier.notify_action_request(game_id, poker_game)

        # Process messages
        while True:
            try:
                # Wait for message with timeout
                logging.warning(f"Waiting for messages from {player_id if player_id else 'observer'}")
                data = await websocket.receive_text()
                logging.warning(f"Received message from {player_id if player_id else 'observer'}: {data[:100]}...")
            except Exception as e:
                # Exception during message receive is normal on client disconnect
                logging.warning(f"Exception waiting for message: {str(e)}")
                break

            try:
                # Parse the message
                message = json.loads(data)

                # Process based on message type
                if message.get("type") == "action":
                    await process_action_message(
                        websocket, game_id, message, player_id, service
                    )
                elif message.get("type") == "chat":
                    await process_chat_message(
                        websocket, game_id, message, player_id, service
                    )
                elif message.get("type") == "ping":
                    # Respond to heartbeat
                    import logging
                    logging.warning(f"Received ping, sending pong to {player_id}")
                    # Include the same timestamp from the ping in the pong response
                    try:
                        await connection_manager.send_personal_message(
                            websocket,
                            {"type": "pong", "timestamp": message.get("timestamp")},
                        )
                        # Don't send game state on every ping - it causes too many updates
                        # We only refresh every few pings if needed
                        if message.get("needsRefresh") == True:
                            logging.warning("Client requested game state refresh")
                            poker_game = service.poker_games.get(game_id)
                            if poker_game:
                                await game_notifier.notify_game_update(game_id, poker_game)
                    except Exception as e:
                        logging.error(f"Error sending pong: {str(e)}")
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {str(e)}")
                await connection_manager.send_personal_message(
                    websocket,
                    {
                        "type": "error",
                        "data": {
                            "code": "invalid_format",
                            "message": "Invalid message format",
                        },
                    },
                )

    except WebSocketDisconnect:
        # Handle disconnect
        import logging
        logging.warning(f"WebSocket disconnected for player {player_id if player_id else 'observer'}")
        connection_manager.disconnect(websocket)
    except Exception as e:
        # Handle other exceptions
        import logging
        import traceback
        logging.error(f"Error in WebSocket connection: {str(e)}")
        logging.error(traceback.format_exc())
        connection_manager.disconnect(websocket)


async def process_action_message(
    websocket: WebSocket,
    game_id: str,
    message: Dict[str, Any],
    player_id: Optional[str],
    service: GameService,
):
    """
    Process a player action WebSocket message.

    Args:
        websocket: The WebSocket connection
        game_id: The ID of the game
        message: The parsed message
        player_id: The ID of the player (None for observers)
        service: The game service
    """
    if not player_id:
        # Observers can't perform actions
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {
                    "code": "not_authorized",
                    "message": "Observers cannot perform actions",
                },
            },
        )
        return

    # Get the poker game from the service
    poker_game = service.poker_games.get(game_id)
    if not poker_game:
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {"code": "game_not_found", "message": "Game not found"},
            },
        )
        return

    # Get the player
    player = next((p for p in poker_game.players if p.player_id == player_id), None)
    if not player:
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {"code": "player_not_found", "message": "Player not found"},
            },
        )
        return

    # Extract action data
    action_data = message.get("data", {})
    action_type_str = action_data.get("action")
    action_amount = action_data.get("amount")

    # Validate it's the player's turn
    active_players = [
        p
        for p in poker_game.players
        if p.status in {PlayerStatus.ACTIVE, PlayerStatus.ALL_IN}
    ]
    if (
        not active_players
        or active_players[poker_game.current_player_idx].player_id != player_id
    ):
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {"code": "not_your_turn", "message": "Not your turn to act"},
            },
        )
        return

    # Parse and validate the action
    try:
        action_type = PlayerAction[action_type_str.upper()]
    except (KeyError, AttributeError):
        valid_actions = poker_game.get_valid_actions(player)
        valid_action_types = [a[0] for a in valid_actions]

        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {
                    "code": "invalid_action",
                    "message": f"Invalid action. Valid actions: {[a.name for a in valid_action_types]}",
                },
            },
        )
        return

    # Validate the action is allowed
    valid_actions = poker_game.get_valid_actions(player)
    valid_action_types = [a[0] for a in valid_actions]

    if action_type not in valid_action_types:
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {
                    "code": "invalid_action",
                    "message": f"Invalid action. Valid actions: {[a.name for a in valid_action_types]}",
                },
            },
        )
        return

    # Process the action through both service and poker game
    from app.models.domain_models import PlayerAction as DomainPlayerAction

    action_map = {
        PlayerAction.FOLD: DomainPlayerAction.FOLD,
        PlayerAction.CHECK: DomainPlayerAction.CHECK,
        PlayerAction.CALL: DomainPlayerAction.CALL,
        PlayerAction.BET: DomainPlayerAction.BET,
        PlayerAction.RAISE: DomainPlayerAction.RAISE,
        PlayerAction.ALL_IN: DomainPlayerAction.ALL_IN,
    }
    domain_action = action_map.get(action_type)

    # Process in service (for history)
    try:
        service.process_action(game_id, player_id, domain_action, action_amount)
    except Exception as e:
        print(f"Error processing action in service: {str(e)}")

    # Process directly in poker game for current state
    success = poker_game.process_action(player, action_type, action_amount)

    if not success:
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {
                    "code": "action_failed",
                    "message": f"Failed to process action {action_type.name}",
                },
            },
        )
        return

    # Notify about player action
    await game_notifier.notify_player_action(
        game_id, player_id, action_type.name, action_amount
    )

    # Notify about updated game state
    await game_notifier.notify_game_update(game_id, poker_game)

    # If hand is complete, notify about results
    if poker_game.current_round == BettingRound.SHOWDOWN:
        await game_notifier.notify_hand_result(game_id, poker_game)
    else:
        # Check if next player is AI
        active_players = [p for p in poker_game.players 
                         if p.status in {PlayerStatus.ACTIVE, PlayerStatus.ALL_IN}]
        
        if active_players and poker_game.current_player_idx < len(active_players):
            next_player = active_players[poker_game.current_player_idx]
            # Find the domain model for the next player to check if AI
            game = service.get_game(game_id)
            if game:
                next_player_domain = next((p for p in game.players if p.id == next_player.player_id), None)
                
                if next_player_domain and not next_player_domain.is_human:
                    # AI player's turn - trigger AI action asynchronously
                    import asyncio
                    asyncio.create_task(service._request_and_process_ai_action(
                        game_id, next_player.player_id
                    ))
                    return  # AI will handle the turn, no need to send action request
        
        # Send action request to next player (if human)
        await game_notifier.notify_action_request(game_id, poker_game)


async def process_chat_message(
    websocket: WebSocket,
    game_id: str,
    message: Dict[str, Any],
    player_id: Optional[str],
    service: GameService,
):
    """
    Process a chat WebSocket message.

    Args:
        websocket: The WebSocket connection
        game_id: The ID of the game
        message: The parsed message
        player_id: The ID of the player (None for observers)
        service: The game service
    """
    # Get the poker game
    poker_game = service.poker_games.get(game_id)
    if not poker_game:
        return

    # Get the sender name
    sender_name = "Observer"
    if player_id:
        player = next((p for p in poker_game.players if p.player_id == player_id), None)
        if player:
            sender_name = player.name

    # Extract chat data
    chat_data = message.get("data", {})
    text = chat_data.get("text", "").strip()
    target = chat_data.get("target", "table")

    # Validate text
    if not text or len(text) > 500:  # Limit message length
        return

    # Create chat message
    chat_message = {
        "type": "chat",
        "data": {
            "from": sender_name,
            "text": text,
            "timestamp": datetime.now().isoformat(),
        },
    }

    # Handle based on target
    if target == "table":
        # Broadcast to all players
        await connection_manager.broadcast_to_game(game_id, chat_message)
    elif target == "coach":
        # Coach messages would be handled by a separate system
        # For now, just acknowledge receipt
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "chat_confirmation",
                "data": {"received": True, "timestamp": datetime.now().isoformat()},
            },
        )
