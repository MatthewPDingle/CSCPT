"""
Tests for game WebSocket API endpoints.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, WebSocketDisconnect

from app.api.game_ws import router as game_ws_router
from app.core.poker_game import PokerGame, PlayerAction, PlayerStatus, BettingRound
from app.core.websocket import ConnectionManager, GameStateNotifier

# Create test app
app = FastAPI()
app.include_router(game_ws_router)

# Mock active games and game_notifier for testing
mock_active_games = {}
mock_game = MagicMock()
mock_game.players = []
mock_game.current_round = BettingRound.PREFLOP

# Setup patching for tests
@pytest.fixture
def mock_game_dependencies(monkeypatch):
    """Patch dependencies for game WebSocket tests."""
    monkeypatch.setattr("app.api.game_ws.active_games", mock_active_games)
    monkeypatch.setattr("app.api.game_ws.connection_manager", MagicMock())
    monkeypatch.setattr("app.api.game_ws.game_notifier", MagicMock())
    
    # Setup async methods
    monkeypatch.setattr("app.api.game_ws.connection_manager.connect", AsyncMock())
    monkeypatch.setattr("app.api.game_ws.game_notifier.notify_game_update", AsyncMock())
    monkeypatch.setattr("app.api.game_ws.game_notifier.notify_action_request", AsyncMock())


def test_websocket_game_not_found():
    """Test connecting to a non-existent game."""
    mock_active_games.clear()
    
    with patch("app.api.game_ws.active_games", {}):
        with TestClient(app) as client:
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect("/ws/game/non_existent_game"):
                    pass


def test_websocket_player_not_found():
    """Test connecting with a non-existent player ID."""
    mock_game = MagicMock()
    mock_game.players = []
    
    with patch("app.api.game_ws.active_games", {"test_game": mock_game}):
        with TestClient(app) as client:
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect("/ws/game/test_game?player_id=non_existent_player"):
                    pass


@pytest.mark.asyncio
async def test_process_action_message():
    """Test processing an action message."""
    from app.api.game_ws import process_action_message
    
    # Mock dependencies
    mock_websocket = AsyncMock()
    mock_message = {
        "type": "action",
        "data": {
            "action": "FOLD",
            "amount": None
        }
    }
    
    # Mock game with player
    mock_game = MagicMock()
    mock_player = MagicMock()
    mock_player.player_id = "player1"
    mock_player.status = PlayerStatus.ACTIVE
    mock_game.players = [mock_player]
    
    # Mock valid actions
    mock_game.get_valid_actions.return_value = [(PlayerAction.FOLD, None)]
    mock_game.current_player_idx = 0
    mock_active_players = [mock_player]
    mock_game.players = mock_active_players
    
    # Mock process_action
    mock_game.process_action.return_value = True
    
    # Patch dependencies
    with patch("app.api.game_ws.active_games", {"game1": mock_game}), \
         patch("app.api.game_ws.connection_manager") as mock_conn_manager, \
         patch("app.api.game_ws.PlayerAction") as mock_player_action, \
         patch("app.api.game_ws.game_notifier") as mock_notifier:
        
        # Setup player action enum
        mock_player_action.__getitem__.return_value = PlayerAction.FOLD
        
        # Setup async methods
        mock_conn_manager.send_personal_message = AsyncMock()
        mock_notifier.notify_player_action = AsyncMock()
        mock_notifier.notify_game_update = AsyncMock()
        mock_notifier.notify_action_request = AsyncMock()
        
        # Call process_action_message
        await process_action_message(mock_websocket, "game1", mock_message, "player1")
        
        # Verify game.process_action was called
        mock_game.process_action.assert_called_once()
        
        # Verify notifications were sent
        mock_notifier.notify_player_action.assert_called_once()
        mock_notifier.notify_game_update.assert_called_once()


@pytest.mark.asyncio
async def test_process_chat_message():
    """Test processing a chat message."""
    from app.api.game_ws import process_chat_message
    
    # Mock dependencies
    mock_websocket = AsyncMock()
    mock_message = {
        "type": "chat",
        "data": {
            "text": "Hello, world!",
            "target": "table"
        }
    }
    
    # Mock game with player
    mock_game = MagicMock()
    mock_player = MagicMock()
    mock_player.player_id = "player1"
    mock_player.name = "Player 1"
    mock_game.players = [mock_player]
    
    # Patch dependencies
    with patch("app.api.game_ws.active_games", {"game1": mock_game}), \
         patch("app.api.game_ws.connection_manager") as mock_conn_manager:
        
        # Setup async methods
        mock_conn_manager.broadcast_to_game = AsyncMock()
        mock_conn_manager.send_personal_message = AsyncMock()
        
        # Call process_chat_message
        await process_chat_message(mock_websocket, "game1", mock_message, "player1")
        
        # Verify broadcast was called
        mock_conn_manager.broadcast_to_game.assert_called_once()
        
        # Verify chat message
        call_args = mock_conn_manager.broadcast_to_game.call_args[0]
        assert call_args[0] == "game1"
        assert call_args[1]["type"] == "chat"
        assert call_args[1]["data"]["from"] == "Player 1"
        assert call_args[1]["data"]["text"] == "Hello, world!"