"""
WebSocket connection management for real-time game updates.
"""
from typing import Dict, List, Set, Optional
from fastapi import WebSocket
import json
import copy
import asyncio
from datetime import datetime
from app.services.game_service import GameService

from app.core.poker_game import PokerGame, PlayerStatus
from app.core.utils import game_to_model


class ConnectionManager:
    """Manages WebSocket connections for real-time game updates."""
    
    def __init__(self):
        # Maps game_id -> set of connected WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Maps WebSocket -> player_id
        self.socket_player_map: Dict[WebSocket, str] = {}
        # Maps WebSocket -> game_id
        self.socket_game_map: Dict[WebSocket, str] = {}
        # Lock for concurrent access to connection dictionaries
        self.lock = asyncio.Lock()
        
    async def connect(self, websocket: WebSocket, game_id: str, player_id: Optional[str] = None):
        """
        Connect a WebSocket to a game.
        
        Args:
            websocket: The WebSocket connection
            game_id: The ID of the game to connect to
            player_id: The ID of the player connecting (None for observers)
        """
        import logging
        
        # First accept the WebSocket connection
        await websocket.accept()
        
        logging.warning(f"Beginning connect process for WebSocket {id(websocket)} to game {game_id}")
        
        # Use a lock to prevent race conditions in the connection maps
        async with self.lock:
            logging.warning(f"Acquired lock for connect to game {game_id}")
            
            # Initialize game connections set if it doesn't exist
            if game_id not in self.active_connections:
                self.active_connections[game_id] = set()
                logging.warning(f"Created new connection set for game {game_id}")
            
            # For safety, clean up any existing connection for this player in this game
            if player_id:
                for existing_ws in list(self.active_connections.get(game_id, set())):
                    if self.socket_player_map.get(existing_ws) == player_id:
                        logging.warning(f"Found existing connection for player {player_id}, removing it")
                        if existing_ws != websocket:  # Don't remove the one we're adding
                            try:
                                self.active_connections[game_id].remove(existing_ws)
                                if existing_ws in self.socket_player_map:
                                    del self.socket_player_map[existing_ws]
                                if existing_ws in self.socket_game_map:
                                    del self.socket_game_map[existing_ws]
                                logging.warning(f"Removed old WebSocket {id(existing_ws)} for player {player_id}")
                            except Exception as e:
                                logging.error(f"Error removing old connection: {str(e)}")
            
            # Add the new connection to all maps atomically
            try:
                self.active_connections[game_id].add(websocket)
                self.socket_player_map[websocket] = player_id
                self.socket_game_map[websocket] = game_id
                logging.warning(f"Stored game_id {game_id} for WebSocket connection {id(websocket)}")
                
                # Log a status report to debug connection tracking
                connections_in_game = len(self.active_connections[game_id])
                total_connections = sum(len(conns) for conns in self.active_connections.values())
                player_map_size = len(self.socket_player_map)
                game_map_size = len(self.socket_game_map)
                
                logging.warning(f"Connection registration complete. Stats: " +
                               f"connections in game: {connections_in_game}, " +
                               f"total connections: {total_connections}, " +
                               f"player map size: {player_map_size}, " +
                               f"game map size: {game_map_size}")
            except Exception as e:
                logging.error(f"Error adding connection to maps: {str(e)}")
                import traceback
                logging.error(traceback.format_exc())
        
    async def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket.
        
        Args:
            websocket: The WebSocket to disconnect
        """
        import logging
        import traceback
        
        try:
            # Use lock for atomic disconnection
            async with self.lock:
                logging.warning(f"Acquired lock for disconnect of WebSocket {id(websocket)}")
                
                # Don't disconnect if websocket isn't in any of our maps
                in_player_map = websocket in self.socket_player_map
                in_game_map = websocket in self.socket_game_map
                
                if not in_player_map and not in_game_map:
                    logging.warning(f"Ignoring disconnect for WebSocket {id(websocket)} not found in maps")
                    return
                    
                # First log the status of the websocket
                logging.warning(f"Disconnecting WebSocket {id(websocket)} - "
                              f"in player map: {in_player_map}, "
                              f"in game map: {in_game_map}")
                    
                # Get player ID and game ID for logging
                player_id = self.socket_player_map.get(websocket, 'unknown')
                game_id = self.socket_game_map.get(websocket, 'unknown')
                
                # Find the game this websocket belongs to
                found_in_game = False
                for g_id, connections in list(self.active_connections.items()):
                    if websocket in connections:
                        connections.remove(websocket)
                        found_in_game = True
                        logging.warning(f"Removed WebSocket {id(websocket)} for player {player_id} from game {g_id}")
                        # Clean up empty games
                        if not connections:
                            del self.active_connections[g_id]
                            logging.warning(f"Removed empty game {g_id} from active_connections")
                        break
                        
                if not found_in_game:
                    logging.warning(f"WebSocket {id(websocket)} for player {player_id} not found in any active game connections")
                    
                # Remove from player map
                if in_player_map:
                    del self.socket_player_map[websocket]
                    logging.warning(f"Removed player {player_id} mapping for WebSocket {id(websocket)}")
                    
                # Remove from game map
                if in_game_map:
                    logging.warning(f"Removing game_id {game_id} for WebSocket connection {id(websocket)}")
                    del self.socket_game_map[websocket]
                    
        except Exception as e:
            logging.error(f"Error during WebSocket disconnect: {str(e)}")
            logging.error(traceback.format_exc())
    
    async def broadcast_to_game(self, game_id: str, message: dict):
        """
        Broadcast a message to all players in a game.
        
        Args:
            game_id: The ID of the game
            message: The message to broadcast
        """
        import logging
        
        # Get active connections atomically
        connections_to_broadcast = []
        
        async with self.lock:
            if game_id not in self.active_connections:
                logging.warning(f"Cannot broadcast to game {game_id}: no active connections")
                return
            
            # Make a copy of the connections to avoid modification during iteration
            connections_to_broadcast = list(self.active_connections[game_id])
            connection_count = len(connections_to_broadcast)
            logging.warning(f"Broadcasting to {connection_count} connection(s) in game {game_id}")
            
        # Convert message to JSON string
        json_message = json.dumps(message)
        
        # Send to all connections in the game (outside the lock to avoid blocking)
        disconnected = []
        
        for connection in connections_to_broadcast:
            try:
                await connection.send_text(json_message)
            except RuntimeError as e:
                logging.error(f"Error sending message: {str(e)}")
                # Connection is closed
                disconnected.append(connection)
            except Exception as e:
                logging.error(f"Unexpected error sending message: {str(e)}")
                disconnected.append(connection)
                
        # Clean up disconnected connections outside the loop
        for connection in disconnected:
            await self.disconnect(connection)
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """
        Send a message to a specific player.
        
        Args:
            websocket: The WebSocket to send to
            message: The message to send
        """
        import logging
        import traceback
        import json
        
        if websocket is None:
            logging.warning("Cannot send message: WebSocket is None")
            return
        
        # Check if the websocket is properly registered
        websocket_valid = False
        player_id = 'unknown'
        
        # Use the lock to check connection state atomically
        async with self.lock:
            # Skip if websocket is not in our maps (likely already closed)
            if websocket not in self.socket_player_map:
                logging.warning(f"Cannot send message: WebSocket {id(websocket)} not found in player map")
                return
                
            player_id = self.socket_player_map.get(websocket, 'unknown')
            
            # Check if websocket is in any active connection before sending
            # This is critical for detecting inconsistency issues
            websocket_valid = False
            found_game_id = None
            
            # Check if we have a valid game_id in the socket_game_map
            if websocket in self.socket_game_map:
                found_game_id = self.socket_game_map[websocket]
                if found_game_id in self.active_connections:
                    if websocket in self.active_connections[found_game_id]:
                        websocket_valid = True
                        logging.debug(f"Found valid connection for player {player_id} in game {found_game_id}")
            
            # If websocket isn't valid, this indicates a data consistency issue that should be logged
            # We no longer attempt to "fix" it by re-adding, as this masked the underlying problem
            if not websocket_valid:
                logging.error(f"DATA CONSISTENCY ERROR: WebSocket {id(websocket)} for player {player_id} "
                              f"present in socket_player_map but not in active_connections for game {found_game_id}. "
                              f"This indicates a state inconsistency.")
                
                # Log more details about the connection maps to help diagnose
                active_games = list(self.active_connections.keys())
                player_map_size = len(self.socket_player_map)
                game_map_size = len(self.socket_game_map)
                
                logging.error(f"Connection maps state: active games: {active_games}, "
                              f"player map size: {player_map_size}, game map size: {game_map_size}")
                
                # Instead of attempting to "fix" with a re-add, we abort sending the message
                # This forces the issues to be addressed at their root cause
                return
        
        # Get message type for logging
        msg_type = message.get('type', 'unknown')
        
        # Only log non-routine messages
        if msg_type not in ['pong']:
            logging.warning(f"Sending personal message of type '{msg_type}' to player {player_id}")
        
        # Serialize message
        try:
            # Try serializing with more debug info
            logging.debug(f"Serializing message: {message}")
            if not isinstance(message, dict):
                logging.warning(f"Message is not a dict, it's a {type(message)}")
                message = {"type": "error", "data": {"message": "Internal error: Invalid message format"}}
                
            json_message = json.dumps(message)
            message_preview = json_message[:100] + ('...' if len(json_message) > 100 else '')
            logging.debug(f"Serialized message: {message_preview}")
        except Exception as e:
            logging.error(f"Error serializing message: {str(e)}")
            logging.error(traceback.format_exc())
            logging.error(f"Problematic message: {str(message)[:200]}")
            return
        
        # Send the message
        try:
            # Check state before sending to avoid cryptic errors
            if hasattr(websocket, "client_state") and websocket.client_state.name == "DISCONNECTED":
                logging.warning(f"WebSocket for player {player_id} is in DISCONNECTED state, cannot send")
                await self.disconnect(websocket)
                return
                
            await websocket.send_text(json_message)
            logging.debug(f"Successfully sent message of type {msg_type} to {player_id}")
        except RuntimeError as e:
            # Common runtime errors from FastAPI WebSockets
            if "disconnected" in str(e) or "closed" in str(e):
                logging.warning(f"WebSocket for player {player_id} is already disconnected: {str(e)}")
            else:
                logging.error(f"Runtime error sending message to {player_id}: {str(e)}")
                logging.error(traceback.format_exc())
            # Connection is closed, clean up
            await self.disconnect(websocket)
        except ConnectionResetError as e:
            logging.warning(f"Connection reset sending to {player_id}: {str(e)}")
            await self.disconnect(websocket)
        except Exception as e:
            logging.error(f"Unexpected error sending message to {player_id}: {str(e)}")
            logging.error(traceback.format_exc())
            await self.disconnect(websocket)
    
    async def send_to_player(self, game_id: str, player_id: str, message: dict, max_retries: int = 2) -> bool:
        """
        Send a message to a specific player in a game.
        
        Args:
            game_id: The ID of the game
            player_id: The ID of the player
            message: The message to send
            max_retries: Maximum number of retries if the player isn't found
            
        Returns:
            True if message was successfully sent, False otherwise
        """
        import logging
        import asyncio
        
        # Check game exists with lock
        player_connections = []
        
        async with self.lock:
            if game_id not in self.active_connections:
                logging.warning(f"Cannot send to player {player_id} in game {game_id}: game not found")
                return False
            
            # Find all connections for this player atomically
            for connection in self.active_connections[game_id]:
                mapped_player = self.socket_player_map.get(connection)
                if mapped_player == player_id:
                    player_connections.append(connection)
        
        # If no connections found initially, no need to go further
        if not player_connections:
            logging.warning(f"No connections found for player {player_id} in game {game_id}")
            # We'll retry later if needed
        else:
            logging.warning(f"Found {len(player_connections)} connection(s) for player {player_id}")
            
        json_message = json.dumps(message)
        message_sent = False
        
        # Attempt to find and send to the player
        for retry in range(max_retries + 1):  # +1 for initial attempt
            # If we don't have player connections yet, try to get them again
            if not player_connections and retry > 0:
                async with self.lock:
                    logging.warning(f"Retry {retry}/{max_retries}: Refreshing connection map for player {player_id}")
                    logging.warning(f"Connection map state: game_id={game_id}, player_id={player_id}")
                    
                    if game_id in self.active_connections:
                        logging.warning(f"  - connections count for game: {len(self.active_connections[game_id])}")
                        for conn in self.active_connections[game_id]:
                            mapped_player = self.socket_player_map.get(conn, 'unknown')
                            logging.warning(f"    - connection {id(conn)} maps to player {mapped_player}")
                            if mapped_player == player_id:
                                player_connections.append(conn)
                                logging.warning(f"    - added connection {id(conn)} to player_connections")
            
            # Now try to send to all player connections
            disconnected = []
            
            for connection in player_connections:
                try:
                    if retry == 0:
                        logging.warning(f"Sending message of type '{message.get('type')}' to player {player_id}")
                    else:
                        logging.warning(f"Retry {retry}/{max_retries}: Sending message of type '{message.get('type')}' to player {player_id}")
                        
                    await connection.send_text(json_message)
                    # Message sent successfully
                    message_sent = True
                    break
                except RuntimeError as e:
                    logging.error(f"Error sending to player {player_id}: {str(e)}")
                    # Connection is closed
                    disconnected.append(connection)
                except Exception as e:
                    logging.error(f"Unexpected error sending to player {player_id}: {str(e)}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections - remove from our local list first
            for connection in disconnected:
                if connection in player_connections:
                    player_connections.remove(connection)
                await self.disconnect(connection)
                
            # If message was sent successfully, exit the loop
            if message_sent:
                break
                
            # If we still haven't found the player or sending failed, wait a bit and retry
            if not message_sent and retry < max_retries:
                logging.warning(f"Retry {retry+1}/{max_retries}: Message not sent to player {player_id}, waiting before retry")
                # Wait a bit before retrying
                await asyncio.sleep(1.0)
            elif not message_sent:
                logging.warning(f"Failed to send message to player {player_id} in game {game_id} after {max_retries} retries")
            
        return message_sent  # Return True if message was sent, False otherwise
    
    async def get_player_connections(self, game_id: str) -> Dict[str, List[WebSocket]]:
        """
        Get a mapping of player_id -> WebSockets for a game.
        A player might have multiple connections (e.g., multiple tabs).
        
        Args:
            game_id: The ID of the game
            
        Returns:
            A dictionary mapping player IDs to lists of WebSocket connections
        """
        result: Dict[str, List[WebSocket]] = {}
        
        async with self.lock:
            if game_id not in self.active_connections:
                return result
                
            for connection in self.active_connections[game_id]:
                player_id = self.socket_player_map.get(connection)
                if player_id:
                    if player_id not in result:
                        result[player_id] = []
                    result[player_id].append(connection)
                    
        return result
        
    async def get_connections_for_game(self, game_id: str) -> Set[WebSocket]:
        """
        Get all connections for a game.
        
        Args:
            game_id: The ID of the game
            
        Returns:
            A set of WebSocket connections
        """
        async with self.lock:
            return set(self.active_connections.get(game_id, set()))


# Create global connection manager instance
connection_manager = ConnectionManager()


class GameStateNotifier:
    """Utility for broadcasting game state updates."""
    
    def __init__(self, connection_mgr: ConnectionManager):
        self.connection_manager = connection_mgr
        
    async def notify_game_update(self, game_id: str, game: PokerGame, game_to_model_func=None):
        """
        Notify all clients about a game state update.
        
        Args:
            game_id: The ID of the game
            game: The PokerGame instance
            game_to_model_func: Function to convert game to model (optional, uses imported by default)
        """
        import logging
        import traceback
        import json
        
        logging.warning(f"Notifying game update for game {game_id}")

        # Validate input parameters
        if not game_id:
            logging.error("Game ID is required for notify_game_update")
            return
            
        if not game:
            logging.error(f"No game instance provided for game {game_id}")
            return
            
        # Get all connections for this game
        connections = await self.connection_manager.get_connections_for_game(game_id)
        if not connections:
            logging.warning(f"No connections found for game {game_id}")
            return
            
        # Get player connections
        player_connections = await self.connection_manager.get_player_connections(game_id)
        logging.warning(f"Found {len(player_connections)} player connections")
        
        # Use the function provided or the default imported function
        model_func = game_to_model_func or game_to_model
        
        # Convert game state
        try:
            game_state = model_func(game_id, game)
            logging.warning(f"Generated game state for game {game_id} with {len(game_state.players)} players")
            
            # Log a summary of the game state for debugging
            player_summary = ", ".join([f"{p.name}({p.status})" for p in game_state.players])
            logging.warning(f"Game state contains players: {player_summary}")
            
            # Validate that the game state can be properly serialized to catch errors early
            try:
                state_dict = game_state.dict()
                # Try to serialize to JSON to catch any serialization issues before sending
                json.dumps(state_dict)
            except Exception as json_error:
                logging.error(f"Error serializing game state to JSON: {str(json_error)}")
                logging.error(traceback.format_exc())
                return
                
        except Exception as e:
            logging.error(f"Error generating game state: {str(e)}")
            logging.error(traceback.format_exc())
            return
        
        # Track processed connections to avoid double-sending
        processed_sockets = set()
        
        # For players, send personalized game state (with their cards visible)
        for player_id, player_sockets in player_connections.items():
            # Skip if no sockets for this player
            if not player_sockets:
                continue
                
            try:
                filtered_state = copy.deepcopy(game_state)
                
                # Filter cards - only show this player's cards
                for player_model in filtered_state.players:
                    if player_model.player_id != player_id:
                        player_model.cards = None
                
                # Convert to a dict with error handling
                state_dict = filtered_state.dict()
                
                message = {
                    "type": "game_state",
                    "data": state_dict
                }
                
                logging.warning(f"Sending game state to player {player_id}")
                
                for socket in player_sockets:
                    if socket in processed_sockets:
                        logging.warning(f"Skipping already processed socket for player {player_id}")
                        continue
                        
                    try:
                        await self.connection_manager.send_personal_message(socket, message)
                        processed_sockets.add(socket)
                        # Remove from connections to avoid sending observer state to the same socket
                        if socket in connections:
                            connections.remove(socket)
                    except Exception as e:
                        logging.error(f"Error sending to player {player_id}: {str(e)}")
                        logging.error(traceback.format_exc())
            except Exception as e:
                logging.error(f"Error preparing game state message for player {player_id}: {str(e)}")
                logging.error(traceback.format_exc())
                # Continue with other players despite error
        
        # For observers (connections without player_id), send game state with all cards hidden
        # Exclude any connections we've already sent to
        observer_connections = [conn for conn in connections if conn not in processed_sockets]
        
        if observer_connections:
            try:
                observer_state = copy.deepcopy(game_state)
                
                # Hide all player cards for observers
                for player_model in observer_state.players:
                    player_model.cards = None
                
                # Send observer game state
                try:
                    state_dict = observer_state.dict()
                    
                    # Verify serialization before sending
                    try:
                        json.dumps(state_dict)
                    except Exception as json_error:
                        logging.error(f"Error serializing observer game state to JSON: {str(json_error)}")
                        logging.error(traceback.format_exc())
                        return
                    
                    message = {
                        "type": "game_state",
                        "data": state_dict
                    }
                    
                    logging.warning(f"Sending observer game state to {len(observer_connections)} connections")
                    
                    for socket in observer_connections:
                        if socket in processed_sockets:
                            continue
                        try:
                            await self.connection_manager.send_personal_message(socket, message)
                            processed_sockets.add(socket)
                        except Exception as e:
                            logging.error(f"Error sending to observer: {str(e)}")
                            logging.error(traceback.format_exc())
                            # Continue with other observers
                except Exception as e:
                    logging.error(f"Error preparing observer game state dict: {str(e)}")
                    logging.error(traceback.format_exc())
            except Exception as e:
                logging.error(f"Error preparing observer game state: {str(e)}")
                logging.error(traceback.format_exc())
    
    async def notify_player_action(self, game_id: str, player_id: str, action: str, amount: Optional[int] = None):
        """
        Notify all clients about a player action and log it.
        
        Args:
            game_id: The ID of the game
            player_id: The ID of the player who took the action
            action: The action taken
            amount: The amount (for bet/raise/call)
        """
        # Find player name
        player_name = "Unknown Player"
        try:
            service = GameService.get_instance() # Need GameService here
            game = service.get_game(game_id)
            if game:
                 player = next((p for p in game.players if p.id == player_id), None)
                 if player:
                     player_name = player.name
        except Exception:
             pass # Ignore errors finding name for log

        # Create descriptive log message
        log_text = f"{player_name} {action.lower()}"
        if amount is not None and action.upper() in ["BET", "RAISE", "CALL", "ALL_IN"]:
             log_text += f" {amount}"

        action_message = {
            "type": "player_action",
            "data": {
                "player_id": player_id,
                "action": action,
                "amount": amount,
                "timestamp": datetime.now().isoformat()
            }
        }

        log_message = {
            "type": "action_log",
            "data": {
                 "text": log_text,
                 "timestamp": datetime.now().isoformat()
            }
        }

        await self.connection_manager.broadcast_to_game(game_id, action_message)
        await self.connection_manager.broadcast_to_game(game_id, log_message) # Broadcast log message
    
    async def notify_hand_result(self, game_id: str, game: PokerGame):
        """
        Notify all clients about hand results.
        
        Args:
            game_id: The ID of the game
            game: The PokerGame instance
        """
        if game.current_hand_id is None:
            return
            
        result_message = {
            "type": "hand_result",
            "data": {
                "handId": game.current_hand_id,
                "winners": [],
                "players": [],
                "board": [str(card) for card in game.community_cards],
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Add winner information
        for pot_id, winners in game.hand_winners.items():
            # Find pot amount
            pot_amount = 0
            for pot in game.pots:
                if pot.name == pot_id or f"pot_{pot_id}" == pot_id:
                    pot_amount = pot.amount
                    break
            
            # Add each winner
            for winner in winners:
                winner_info = {
                    "player_id": winner.player_id,
                    "name": winner.name,
                    "amount": pot_amount // len(winners),  # Split pot evenly
                }
                
                # Add hand information if available
                if hasattr(winner, 'hand') and winner.hand:
                    winner_info["cards"] = [str(card) for card in winner.hand.cards]
                    if hasattr(winner.hand, 'hand_rank'):
                        winner_info["hand_rank"] = str(winner.hand.hand_rank)
                
                result_message["data"]["winners"].append(winner_info)
        
        # Add player information (including their cards for showdown)
        for player in game.players:
            player_info = {
                "player_id": player.player_id,
                "name": player.name,
                "folded": player.status == PlayerStatus.FOLDED,
            }
            
            # Only include cards for active players at showdown
            if player.status != PlayerStatus.FOLDED and hasattr(player, 'hand') and player.hand:
                player_info["cards"] = [str(card) for card in player.hand.cards]
            
            result_message["data"]["players"].append(player_info)
        
        # Broadcast to all players
        await self.connection_manager.broadcast_to_game(game_id, result_message)
    
    async def notify_action_request(self, game_id: str, game: PokerGame):
        """
        Notify the current player that it's their turn to act.
        Only sends action requests to human players.
        
        Args:
            game_id: The ID of the game
            game: The PokerGame instance
        """
        active_players = [p for p in game.players 
                         if p.status in {PlayerStatus.ACTIVE, PlayerStatus.ALL_IN}]
        if not active_players or game.current_player_idx >= len(active_players):
            return
            
        current_player = active_players[game.current_player_idx]
        
        # Import necessary modules
        import logging
        from app.services.game_service import GameService
        
        # Check if player is human before sending action request
        try:
            # Get the game service
            service = GameService.get_instance()
            game_obj = service.get_game(game_id)
            
            if game_obj:
                # Find the player in the domain model
                player = next((p for p in game_obj.players if p.id == current_player.player_id), None)
                
                # If player is not human, we don't send an action request
                if player and not player.is_human:
                    return
        except Exception as e:
            logging.error(f"Error checking if player is human: {str(e)}")
            # If we can't determine if the player is human, proceed with the action request
        
        # Continue with regular action request for human players
        valid_actions = game.get_valid_actions(current_player)
        
        # Create action options
        options = []
        call_amount = 0
        min_raise = 0
        max_raise = 0
        
        for action_tuple in valid_actions:
            action = action_tuple[0]  # First element is the action
            options.append(action.name)
            
            if action.name == "CALL":
                call_amount = action_tuple[1]  # Second element is min_amount for CALL
            elif action.name == "RAISE" and len(action_tuple) >= 3:
                min_raise = action_tuple[1]  # Second element is min_amount for RAISE
                max_raise = action_tuple[2]  # Third element is max_amount for RAISE
        
        message = {
            "type": "action_request",
            "data": {
                "handId": game.current_hand_id,
                "player_id": current_player.player_id,
                "options": options,
                "callAmount": call_amount,
                "minRaise": min_raise,
                "maxRaise": max_raise,
                "timeLimit": 30,  # Default time limit
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Send to the current player with retries
        import asyncio
        for retry in range(3):  # Try up to 3 times
            try:
                if retry > 0:
                    # Add delay before retrying
                    logging.warning(f"Retry {retry}/3: Sending action request to player {current_player.player_id}")
                    await asyncio.sleep(1.0 * retry)  # Increasing delay with each retry
                    
                # Use the enhanced send_to_player with retries
                success = await self.connection_manager.send_to_player(
                    game_id, 
                    current_player.player_id, 
                    message,
                    max_retries=2  # Additional retries within the send_to_player method
                )
                
                if success:
                    logging.warning(f"Successfully sent action request to player {current_player.player_id}")
                    break  # Exit retry loop if successful
                else:
                    # If not successful even with retries, try manual reconnection
                    logging.warning(f"Failed to send action request, attempting connection recovery")
                
            except Exception as retry_error:
                logging.error(f"Error sending action request (attempt {retry+1}/3): {str(retry_error)}")
                if retry == 2:  # Last retry
                    logging.error(f"Failed to send action request after all retries")
                    import traceback
                    logging.error(traceback.format_exc())


# Create game notifier instance
game_notifier = GameStateNotifier(connection_manager)