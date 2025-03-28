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
from app.api.game import active_games, _game_to_model

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/game/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    game_id: str, 
    player_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time game updates.
    
    Args:
        websocket: The WebSocket connection
        game_id: The ID of the game to connect to
        player_id: The ID of the player connecting (None for observers)
    """
    # Verify game exists
    if game_id not in active_games:
        await websocket.close(code=1008, reason="Game not found")
        return
        
    game = active_games[game_id]
    
    # Verify player exists (if a player_id was provided)
    if player_id:
        player = next((p for p in game.players if p.player_id == player_id), None)
        if not player:
            await websocket.close(code=1008, reason="Player not found")
            return
    
    # Accept the connection
    await connection_manager.connect(websocket, game_id, player_id)
    
    try:
        # Send initial game state
        await game_notifier.notify_game_update(game_id, game, _game_to_model)
        
        # If it's this player's turn, send action request
        if player_id:
            active_players = [p for p in game.players 
                             if p.status in {PlayerStatus.ACTIVE, PlayerStatus.ALL_IN}]
            if (active_players and 
                game.current_player_idx < len(active_players) and 
                active_players[game.current_player_idx].player_id == player_id):
                await game_notifier.notify_action_request(game_id, game)
        
        # Process messages
        while True:
            # Wait for message
            data = await websocket.receive_text()
            
            try:
                # Parse the message
                message = json.loads(data)
                
                # Process based on message type
                if message.get("type") == "action":
                    await process_action_message(websocket, game_id, message, player_id)
                elif message.get("type") == "chat":
                    await process_chat_message(websocket, game_id, message, player_id)
                elif message.get("type") == "ping":
                    # Respond to heartbeat
                    await connection_manager.send_personal_message(
                        websocket, 
                        {"type": "pong", "timestamp": message.get("timestamp")}
                    )
            except json.JSONDecodeError:
                await connection_manager.send_personal_message(
                    websocket,
                    {
                        "type": "error",
                        "data": {
                            "code": "invalid_format",
                            "message": "Invalid message format"
                        }
                    }
                )
                
    except WebSocketDisconnect:
        # Handle disconnect
        connection_manager.disconnect(websocket)


async def process_action_message(
    websocket: WebSocket, 
    game_id: str, 
    message: Dict[str, Any], 
    player_id: Optional[str]
):
    """
    Process a player action WebSocket message.
    
    Args:
        websocket: The WebSocket connection
        game_id: The ID of the game
        message: The parsed message
        player_id: The ID of the player (None for observers)
    """
    if not player_id:
        # Observers can't perform actions
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {
                    "code": "not_authorized",
                    "message": "Observers cannot perform actions"
                }
            }
        )
        return
        
    if game_id not in active_games:
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {
                    "code": "game_not_found",
                    "message": "Game not found"
                }
            }
        )
        return
        
    game = active_games[game_id]
    
    # Get the player
    player = next((p for p in game.players if p.player_id == player_id), None)
    if not player:
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {
                    "code": "player_not_found",
                    "message": "Player not found"
                }
            }
        )
        return
    
    # Extract action data
    action_data = message.get("data", {})
    action_type_str = action_data.get("action")
    action_amount = action_data.get("amount")
    
    # Validate it's the player's turn
    active_players = [p for p in game.players 
                     if p.status in {PlayerStatus.ACTIVE, PlayerStatus.ALL_IN}]
    if not active_players or active_players[game.current_player_idx].player_id != player_id:
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {
                    "code": "not_your_turn",
                    "message": "Not your turn to act"
                }
            }
        )
        return
    
    # Parse and validate the action
    try:
        action_type = PlayerAction[action_type_str.upper()]
    except (KeyError, AttributeError):
        valid_actions = game.get_valid_actions(player)
        valid_action_types = [a[0] for a in valid_actions]
        
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {
                    "code": "invalid_action",
                    "message": f"Invalid action. Valid actions: {[a.name for a in valid_action_types]}"
                }
            }
        )
        return
    
    # Validate the action is allowed
    valid_actions = game.get_valid_actions(player)
    valid_action_types = [a[0] for a in valid_actions]
    
    if action_type not in valid_action_types:
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {
                    "code": "invalid_action",
                    "message": f"Invalid action. Valid actions: {[a.name for a in valid_action_types]}"
                }
            }
        )
        return
    
    # Process the action
    success = game.process_action(player, action_type, action_amount)
    
    if not success:
        await connection_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "data": {
                    "code": "action_failed",
                    "message": f"Failed to process action {action_type.name}"
                }
            }
        )
        return
    
    # Notify about player action
    await game_notifier.notify_player_action(
        game_id, 
        player_id, 
        action_type.name, 
        action_amount
    )
    
    # Notify about updated game state
    await game_notifier.notify_game_update(game_id, game, _game_to_model)
    
    # If hand is complete, notify about results
    if game.current_round == BettingRound.SHOWDOWN:
        await game_notifier.notify_hand_result(game_id, game)
    else:
        # Send action request to next player
        await game_notifier.notify_action_request(game_id, game)


async def process_chat_message(
    websocket: WebSocket, 
    game_id: str, 
    message: Dict[str, Any], 
    player_id: Optional[str]
):
    """
    Process a chat WebSocket message.
    
    Args:
        websocket: The WebSocket connection
        game_id: The ID of the game
        message: The parsed message
        player_id: The ID of the player (None for observers)
    """
    if game_id not in active_games:
        return
        
    game = active_games[game_id]
    
    # Get the sender name
    sender_name = "Observer"
    if player_id:
        player = next((p for p in game.players if p.player_id == player_id), None)
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
            "timestamp": datetime.now().isoformat()
        }
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
                "data": {
                    "received": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
        )