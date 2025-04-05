"""
Tests for game WebSocket API endpoints.
"""
import pytest
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, WebSocketDisconnect

from app.api.game_ws import router as game_ws_router
from app.core.poker_game import PokerGame, PlayerAction, PlayerStatus, BettingRound
from app.core.websocket import ConnectionManager, GameStateNotifier
from app.services.game_service import GameService
from app.models.domain_models import Game, PlayerAction as DomainPlayerAction

# Create test app
app = FastAPI()
app.include_router(game_ws_router)

# Mock service for testing
mock_service = MagicMock(spec=GameService)
mock_poker_game = MagicMock(spec=PokerGame)
mock_game_instance = MagicMock(spec=Game)
mock_game_instance.id = str(uuid.uuid4())
mock_poker_game.players = []
mock_poker_game.current_round = BettingRound.PREFLOP

# Setup patching for tests
@pytest.fixture
def mock_game_dependencies(monkeypatch):
    """Patch dependencies for game WebSocket tests."""
    # Set up GameService mock
    monkeypatch.setattr("app.api.game_ws.get_game_service", lambda: mock_service)
    mock_service.poker_games = {mock_game_instance.id: mock_poker_game}
    mock_service.get_game.return_value = mock_game_instance
    
    # Set up other dependencies
    monkeypatch.setattr("app.api.game_ws.connection_manager", MagicMock())
    monkeypatch.setattr("app.api.game_ws.game_notifier", MagicMock())
    
    # Setup async methods
    monkeypatch.setattr("app.api.game_ws.connection_manager.connect", AsyncMock())
    monkeypatch.setattr("app.api.game_ws.game_notifier.notify_game_update", AsyncMock())
    monkeypatch.setattr("app.api.game_ws.game_notifier.notify_action_request", AsyncMock())


def test_websocket_game_not_found():
    """Test connecting to a non-existent game."""
    # Set up service to return None for get_game (game not found)
    with patch("app.api.game_ws.get_game_service") as mock_get_service:
        mock_service = MagicMock(spec=GameService)
        mock_service.get_game.return_value = None
        mock_get_service.return_value = mock_service
        
        with TestClient(app) as client:
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect("/ws/game/non_existent_game"):
                    pass


def test_websocket_player_not_found():
    """Test connecting with a non-existent player ID."""
    # Create mocks
    game_id = "test_game"
    mock_game = MagicMock(spec=Game)
    mock_poker_game = MagicMock(spec=PokerGame)
    mock_poker_game.players = []  # No players in the game
    
    # Set up service mock
    with patch("app.api.game_ws.get_game_service") as mock_get_service:
        mock_service = MagicMock(spec=GameService)
        mock_service.get_game.return_value = mock_game
        mock_service.poker_games = {game_id: mock_poker_game}
        mock_get_service.return_value = mock_service
        
        with TestClient(app) as client:
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect(f"/ws/game/{game_id}?player_id=non_existent_player"):
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
    
    # Game ID and player ID for the test
    game_id = "game1"
    player_id = "player1"
    
    # Mock game with player
    mock_game_instance = MagicMock(spec=Game)
    mock_poker_game = MagicMock(spec=PokerGame)
    mock_player = MagicMock()
    mock_player.player_id = player_id
    mock_player.status = PlayerStatus.ACTIVE
    
    # Set up player in the poker game
    mock_poker_game.players = [mock_player]
    mock_poker_game.get_valid_actions.return_value = [(PlayerAction.FOLD, None)]
    mock_poker_game.current_player_idx = 0
    mock_poker_game.process_action.return_value = True
    mock_poker_game.current_round = BettingRound.FLOP  # Not SHOWDOWN to avoid notification
    
    # Mock service
    mock_service = MagicMock(spec=GameService)
    # Create a mock game with players attribute for domain model checking
    mock_domain_game = MagicMock()
    mock_domain_game.players = [MagicMock(id=player_id, is_human=True)]
    mock_service.get_game.return_value = mock_domain_game
    mock_service.poker_games = {game_id: mock_poker_game}
    mock_service.process_action.return_value = mock_domain_game
    
    # Patch dependencies
    with patch("app.api.game_ws.connection_manager") as mock_conn_manager, \
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
        await process_action_message(mock_websocket, game_id, mock_message, player_id, mock_service)
        
        # Verify service.process_action was called
        mock_service.process_action.assert_called_once()
        
        # Verify poker_game.process_action was called
        mock_poker_game.process_action.assert_called_once()
        
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
    
    # Game ID and player ID for the test
    game_id = "game1"
    player_id = "player1"
    
    # Mock game with player
    mock_game_instance = MagicMock(spec=Game)
    mock_poker_game = MagicMock(spec=PokerGame)
    mock_player = MagicMock()
    mock_player.player_id = player_id
    mock_player.name = "Player 1"
    mock_poker_game.players = [mock_player]
    mock_poker_game.current_round = BettingRound.FLOP  # To avoid issues with round attribute
    
    # Mock service
    mock_service = MagicMock(spec=GameService)
    # Create a mock game with players attribute for domain model checking
    mock_domain_game = MagicMock()
    mock_domain_game.players = [MagicMock(id=player_id, is_human=True)]
    mock_service.get_game.return_value = mock_domain_game
    mock_service.poker_games = {game_id: mock_poker_game}
    mock_service.process_action.return_value = mock_domain_game
    
    # Patch dependencies
    with patch("app.api.game_ws.connection_manager") as mock_conn_manager:
        
        # Setup async methods
        mock_conn_manager.broadcast_to_game = AsyncMock()
        mock_conn_manager.send_personal_message = AsyncMock()
        
        # Call process_chat_message
        await process_chat_message(mock_websocket, game_id, mock_message, player_id, mock_service)
        
        # Verify broadcast was called
        mock_conn_manager.broadcast_to_game.assert_called_once()
        
        # Verify chat message
        call_args = mock_conn_manager.broadcast_to_game.call_args[0]
        assert call_args[0] == game_id
        assert call_args[1]["type"] == "chat"
        assert call_args[1]["data"]["from"] == "Player 1"
        assert call_args[1]["data"]["text"] == "Hello, world!"