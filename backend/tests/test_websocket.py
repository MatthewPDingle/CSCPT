"""
Tests for WebSocket implementation.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.core.websocket import ConnectionManager, GameStateNotifier
from app.core.poker_game import PokerGame, PlayerAction, PlayerStatus, BettingRound

# Create test app for WebSocket testing
app = FastAPI()
connection_manager = ConnectionManager()

@pytest.mark.skip(reason="WebSocket endpoint test may cause conflicts with AI integration")
@app.websocket("/ws/test")
async def test_ws_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket, "test_game", "test_player")
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await connection_manager.broadcast_to_game("test_game", {"echo": message})
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


class TestConnectionManager:
    """Tests for the WebSocket connection manager."""
    
    def test_init(self):
        """Test connection manager initialization."""
        manager = ConnectionManager()
        assert isinstance(manager.active_connections, dict)
        assert isinstance(manager.socket_player_map, dict)
        assert len(manager.active_connections) == 0
    
    @pytest.mark.asyncio
    async def test_connect(self):
        """Test connecting a WebSocket."""
        manager = ConnectionManager()
        
        # Mock WebSocket
        mock_ws = AsyncMock()
        
        # Connect WebSocket
        await manager.connect(mock_ws, "test_game", "test_player")
        
        # Verify connection was accepted
        mock_ws.accept.assert_called_once()
        
        # Verify connection was added to active connections
        assert "test_game" in manager.active_connections
        assert mock_ws in manager.active_connections["test_game"]
        assert manager.socket_player_map[mock_ws] == "test_player"
    
    def test_disconnect(self):
        """Test disconnecting a WebSocket."""
        manager = ConnectionManager()
        
        # Setup mock connections
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        
        # Add connections to manager
        manager.active_connections["game1"] = {mock_ws1}
        manager.active_connections["game2"] = {mock_ws2}
        manager.socket_player_map[mock_ws1] = "player1"
        manager.socket_player_map[mock_ws2] = "player2"
        
        # Disconnect WebSocket
        manager.disconnect(mock_ws1)
        
        # Verify connection was removed
        assert "game1" not in manager.active_connections
        assert mock_ws1 not in manager.socket_player_map
        assert "game2" in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_broadcast_to_game(self):
        """Test broadcasting to all connections in a game."""
        manager = ConnectionManager()
        
        # Setup mock connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        
        # Add connections to manager
        manager.active_connections["game1"] = {mock_ws1, mock_ws2}
        
        # Broadcast message
        test_message = {"type": "test", "data": "test_data"}
        await manager.broadcast_to_game("game1", test_message)
        
        # Verify message was sent to all connections
        expected_json = json.dumps(test_message)
        mock_ws1.send_text.assert_called_once_with(expected_json)
        mock_ws2.send_text.assert_called_once_with(expected_json)
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending a message to a specific WebSocket."""
        manager = ConnectionManager()
        
        # Setup mock connection
        mock_ws = AsyncMock()
        
        # Send personal message
        test_message = {"type": "test", "data": "test_data"}
        await manager.send_personal_message(mock_ws, test_message)
        
        # Verify message was sent
        expected_json = json.dumps(test_message)
        mock_ws.send_text.assert_called_once_with(expected_json)
    
    @pytest.mark.asyncio
    async def test_send_to_player(self):
        """Test sending a message to a specific player."""
        manager = ConnectionManager()
        
        # Setup mock connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        
        # Add connections to manager
        manager.active_connections["game1"] = {mock_ws1, mock_ws2}
        manager.socket_player_map[mock_ws1] = "player1"
        manager.socket_player_map[mock_ws2] = "player2"
        
        # Send message to player
        test_message = {"type": "test", "data": "test_data"}
        await manager.send_to_player("game1", "player1", test_message)
        
        # Verify message was sent to correct player
        expected_json = json.dumps(test_message)
        mock_ws1.send_text.assert_called_once_with(expected_json)
        mock_ws2.send_text.assert_not_called()


class TestGameStateNotifier:
    """Tests for the GameStateNotifier."""
    
    @pytest.mark.asyncio
    async def test_notify_game_update(self):
        """Test notifying about game state updates."""
        # Mock dependencies
        mock_manager = MagicMock()
        mock_manager.get_connections_for_game.return_value = {AsyncMock()}
        mock_manager.get_player_connections.return_value = {"player1": [AsyncMock()]}
        mock_manager.send_personal_message = AsyncMock()
        
        mock_game = MagicMock()
        mock_game_to_model = MagicMock()
        mock_game_to_model.return_value.dict.return_value = {"game": "state"}
        
        # Create notifier with mock manager
        notifier = GameStateNotifier(mock_manager)
        
        # Call notify method
        await notifier.notify_game_update("game1", mock_game, mock_game_to_model)
        
        # Verify manager methods were called
        mock_manager.get_connections_for_game.assert_called_once_with("game1")
        mock_manager.get_player_connections.assert_called_once_with("game1")
        assert mock_manager.send_personal_message.call_count > 0
    
    @pytest.mark.asyncio
    async def test_notify_player_action(self):
        """Test notifying about player actions."""
        # Mock dependencies
        mock_manager = MagicMock()
        mock_manager.broadcast_to_game = AsyncMock()
        
        # Create notifier with mock manager
        notifier = GameStateNotifier(mock_manager)
        
        # Call notify method
        await notifier.notify_player_action("game1", "player1", "FOLD")
        
        # Verify broadcast was called with correct message
        mock_manager.broadcast_to_game.assert_called_once()
        call_args = mock_manager.broadcast_to_game.call_args[0]
        assert call_args[0] == "game1"
        assert call_args[1]["type"] == "player_action"
        assert call_args[1]["data"]["player_id"] == "player1"
        assert call_args[1]["data"]["action"] == "FOLD"
    
    @pytest.mark.asyncio
    async def test_notify_hand_result(self):
        """Test notifying about hand results."""
        # Mock dependencies
        mock_manager = MagicMock()
        mock_manager.broadcast_to_game = AsyncMock()
        
        mock_game = MagicMock()
        mock_game.current_hand_id = "hand1"
        mock_game.community_cards = []
        mock_game.hand_winners = {"Main Pot": []}
        mock_game.pots = []
        mock_game.players = []
        
        # Create notifier with mock manager
        notifier = GameStateNotifier(mock_manager)
        
        # Call notify method
        await notifier.notify_hand_result("game1", mock_game)
        
        # Verify broadcast was called with correct message
        mock_manager.broadcast_to_game.assert_called_once()
        call_args = mock_manager.broadcast_to_game.call_args[0]
        assert call_args[0] == "game1"
        assert call_args[1]["type"] == "hand_result"
        assert call_args[1]["data"]["handId"] == "hand1"
    
    @pytest.mark.asyncio
    async def test_notify_action_request(self):
        """Test notifying the current player that it's their turn."""
        # Mock dependencies
        mock_manager = MagicMock()
        mock_manager.send_to_player = AsyncMock()
        
        mock_player = MagicMock()
        mock_player.player_id = "player1"
        mock_player.status = PlayerStatus.ACTIVE
        
        mock_game = MagicMock()
        mock_game.players = [mock_player]
        mock_game.current_player_idx = 0
        mock_game.get_valid_actions.return_value = [(PlayerAction.FOLD, None)]
        
        # Setup active_players filter to work correctly
        mock_active_players = [mock_player]
        mock_game.players = mock_active_players
        
        # Create notifier with mock manager
        notifier = GameStateNotifier(mock_manager)
        
        # Call notify method
        await notifier.notify_action_request("game1", mock_game)
        
        # Verify send_to_player was called with correct message
        mock_manager.send_to_player.assert_called_once()
        call_args = mock_manager.send_to_player.call_args[0]
        assert call_args[0] == "game1"
        assert call_args[1] == "player1"
        assert call_args[2]["type"] == "action_request"


@pytest.mark.asyncio
async def test_websocket_endpoint_integration():
    """Integration test for WebSocket endpoint."""
    # Create test client
    client = TestClient(app)
    
    # Connect to WebSocket
    with client.websocket_connect("/ws/test") as websocket:
        # Send a message
        websocket.send_json({"message": "test"})
        
        # Receive the echo response
        response = websocket.receive_json()
        
        # Verify response
        assert response["echo"]["message"] == "test"