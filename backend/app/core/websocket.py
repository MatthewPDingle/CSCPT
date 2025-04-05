"""
WebSocket connection management for real-time game updates.
"""
from typing import Dict, List, Set, Optional
from fastapi import WebSocket
import json
import copy
from datetime import datetime

from app.core.poker_game import PokerGame, PlayerStatus
from app.core.utils import game_to_model


class ConnectionManager:
    """Manages WebSocket connections for real-time game updates."""
    
    def __init__(self):
        # Maps game_id -> set of connected WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Maps WebSocket -> player_id
        self.socket_player_map: Dict[WebSocket, str] = {}
        
    async def connect(self, websocket: WebSocket, game_id: str, player_id: Optional[str] = None):
        """
        Connect a WebSocket to a game.
        
        Args:
            websocket: The WebSocket connection
            game_id: The ID of the game to connect to
            player_id: The ID of the player connecting (None for observers)
        """
        await websocket.accept()
        
        # Initialize game connections set if it doesn't exist
        if game_id not in self.active_connections:
            self.active_connections[game_id] = set()
            
        # Add the connection
        self.active_connections[game_id].add(websocket)
        self.socket_player_map[websocket] = player_id
        
    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket.
        
        Args:
            websocket: The WebSocket to disconnect
        """
        # Find the game this websocket belongs to
        for game_id, connections in list(self.active_connections.items()):
            if websocket in connections:
                connections.remove(websocket)
                # Clean up empty games
                if not connections:
                    del self.active_connections[game_id]
                break
                
        # Remove from player map
        if websocket in self.socket_player_map:
            del self.socket_player_map[websocket]
    
    async def broadcast_to_game(self, game_id: str, message: dict):
        """
        Broadcast a message to all players in a game.
        
        Args:
            game_id: The ID of the game
            message: The message to broadcast
        """
        import logging
        if game_id not in self.active_connections:
            logging.warning(f"Cannot broadcast to game {game_id}: no active connections")
            return
            
        # Convert message to JSON string
        json_message = json.dumps(message)
        
        # Send to all connections in the game
        disconnected = []
        connection_count = len(self.active_connections[game_id])
        logging.warning(f"Broadcasting to {connection_count} connection(s) in game {game_id}")
        
        for connection in self.active_connections[game_id]:
            try:
                await connection.send_text(json_message)
            except RuntimeError as e:
                logging.error(f"Error sending message: {str(e)}")
                # Connection is closed
                disconnected.append(connection)
            except Exception as e:
                logging.error(f"Unexpected error sending message: {str(e)}")
                disconnected.append(connection)
                
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """
        Send a message to a specific player.
        
        Args:
            websocket: The WebSocket to send to
            message: The message to send
        """
        import logging
        
        # Skip if websocket is not in our maps (likely already closed)
        if websocket not in self.socket_player_map:
            logging.warning("Cannot send message: WebSocket not found in player map")
            return
            
        player_id = self.socket_player_map.get(websocket, 'unknown')
        msg_type = message.get('type', 'unknown')
        logging.warning(f"Sending personal message of type '{msg_type}' to player {player_id}")
        
        # Check if websocket is in any active connection before sending
        is_active = False
        for game_connections in self.active_connections.values():
            if websocket in game_connections:
                is_active = True
                break
                
        if not is_active:
            logging.warning(f"WebSocket for player {player_id} not in active connections, removing from maps")
            self.disconnect(websocket)
            return
        
        # Serialize message
        try:
            json_message = json.dumps(message)
        except Exception as e:
            logging.error(f"Error serializing message: {str(e)}")
            return
        
        # Send the message
        try:
            await websocket.send_text(json_message)
        except RuntimeError as e:
            logging.error(f"Error sending personal message: {str(e)}")
            # Connection is closed, clean up
            self.disconnect(websocket)
        except Exception as e:
            logging.error(f"Unexpected error sending personal message: {str(e)}")
            self.disconnect(websocket)
    
    async def send_to_player(self, game_id: str, player_id: str, message: dict):
        """
        Send a message to a specific player in a game.
        
        Args:
            game_id: The ID of the game
            player_id: The ID of the player
            message: The message to send
        """
        import logging
        if game_id not in self.active_connections:
            logging.warning(f"Cannot send to player {player_id} in game {game_id}: game not found")
            return
            
        json_message = json.dumps(message)
        
        # Find the player's connection and send
        disconnected = []
        found_player = False
        
        for connection in self.active_connections[game_id]:
            if self.socket_player_map.get(connection) == player_id:
                found_player = True
                logging.warning(f"Sending message of type '{message.get('type')}' to player {player_id}")
                try:
                    await connection.send_text(json_message)
                except RuntimeError as e:
                    logging.error(f"Error sending to player {player_id}: {str(e)}")
                    # Connection is closed
                    disconnected.append(connection)
                except Exception as e:
                    logging.error(f"Unexpected error sending to player {player_id}: {str(e)}")
                    disconnected.append(connection)
        
        if not found_player:
            logging.warning(f"No active connection found for player {player_id} in game {game_id}")
                
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    def get_player_connections(self, game_id: str) -> Dict[str, List[WebSocket]]:
        """
        Get a mapping of player_id -> WebSockets for a game.
        A player might have multiple connections (e.g., multiple tabs).
        
        Args:
            game_id: The ID of the game
            
        Returns:
            A dictionary mapping player IDs to lists of WebSocket connections
        """
        result: Dict[str, List[WebSocket]] = {}
        if game_id not in self.active_connections:
            return result
            
        for connection in self.active_connections[game_id]:
            player_id = self.socket_player_map.get(connection)
            if player_id:
                if player_id not in result:
                    result[player_id] = []
                result[player_id].append(connection)
                
        return result
        
    def get_connections_for_game(self, game_id: str) -> Set[WebSocket]:
        """
        Get all connections for a game.
        
        Args:
            game_id: The ID of the game
            
        Returns:
            A set of WebSocket connections
        """
        return self.active_connections.get(game_id, set())


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
        logging.warning(f"Notifying game update for game {game_id}")
        
        # Get all connections for this game
        connections = self.connection_manager.get_connections_for_game(game_id)
        if not connections:
            logging.warning(f"No connections found for game {game_id}")
            return
            
        # Get player connections
        player_connections = self.connection_manager.get_player_connections(game_id)
        logging.warning(f"Found {len(player_connections)} player connections")
        
        # Use the function provided or the default imported function
        model_func = game_to_model_func or game_to_model
        
        # Convert game state
        try:
            game_state = model_func(game_id, game)
            logging.warning(f"Generated game state for game {game_id}")
        except Exception as e:
            import traceback
            logging.error(f"Error generating game state: {str(e)}")
            logging.error(traceback.format_exc())
            return
        
        import logging
        # Track processed connections to avoid double-sending
        processed_sockets = set()
        
        # For players, send personalized game state (with their cards visible)
        for player_id, player_sockets in player_connections.items():
            filtered_state = copy.deepcopy(game_state)
            
            # Filter cards - only show this player's cards
            for player_model in filtered_state.players:
                if player_model.player_id != player_id:
                    player_model.cards = None
            
            # Send personalized game state to each of the player's connections
            try:
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
            except Exception as e:
                import traceback
                logging.error(f"Error preparing game state message: {str(e)}")
                logging.error(traceback.format_exc())
        
        # For observers (connections without player_id), send game state with all cards hidden
        # Exclude any connections we've already sent to
        observer_connections = [conn for conn in connections if conn not in processed_sockets]
        
        if observer_connections:
            observer_state = copy.deepcopy(game_state)
            
            # Hide all player cards for observers
            for player_model in observer_state.players:
                player_model.cards = None
            
            # Send observer game state
            try:
                state_dict = observer_state.dict()
                
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
            except Exception as e:
                import traceback
                logging.error(f"Error preparing observer game state message: {str(e)}")
                logging.error(traceback.format_exc())
    
    async def notify_player_action(self, game_id: str, player_id: str, action: str, amount: Optional[int] = None):
        """
        Notify all clients about a player action.
        
        Args:
            game_id: The ID of the game
            player_id: The ID of the player who took the action
            action: The action taken
            amount: The amount (for bet/raise/call)
        """
        message = {
            "type": "player_action",
            "data": {
                "player_id": player_id,
                "action": action,
                "amount": amount,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await self.connection_manager.broadcast_to_game(game_id, message)
    
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
        
        for action, params in valid_actions:
            options.append(action.name)
            if action.name == "CALL":
                call_amount = params
            elif action.name == "RAISE":
                min_raise = params[0]
                max_raise = params[1]
        
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
        
        await self.connection_manager.send_to_player(game_id, current_player.player_id, message)


# Create game notifier instance
game_notifier = GameStateNotifier(connection_manager)