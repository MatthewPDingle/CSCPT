"""
Tests for the WebSocket game API.
These tests verify that the WebSocket endpoints correctly interact with the GameService.
"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
import uuid

from fastapi.testclient import TestClient
from app.main import app
from app.services.game_service import GameService
from app.core.poker_game import PokerGame, PlayerStatus, PlayerAction, BettingRound
from app.models.domain_models import Game, Player, PlayerAction as DomainPlayerAction
from app.core.websocket import connection_manager, game_notifier


@pytest.fixture
def test_client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_service():
    """
    Create a mock GameService for testing.
    
    This fixture leverages the testing hooks in GameService to properly
    substitute a mock for the singleton instance during tests.
    """
    # Reset the singleton before and after test
    GameService._reset_instance_for_testing()
    
    # Create a mock service
    mock_service = MagicMock(spec=GameService)
    
    # Set it as the singleton instance
    GameService._set_instance_for_testing(mock_service)
    
    # Return the mock for test assertions
    yield mock_service
    
    # Clean up after test
    GameService._reset_instance_for_testing()


@pytest.fixture
def mock_game():
    """Create a mock Game instance."""
    game = MagicMock(spec=Game)
    game.id = str(uuid.uuid4())
    game.status = "ACTIVE"
    game.players = []
    return game


@pytest.fixture
def mock_poker_game():
    """Create a mock PokerGame instance."""
    poker_game = MagicMock(spec=PokerGame)
    poker_game.small_blind = 10
    poker_game.big_blind = 20
    poker_game.current_round = BettingRound.PREFLOP
    poker_game.players = []
    poker_game.community_cards = []
    poker_game.pots = []
    poker_game.button_position = 0
    poker_game.current_player_idx = 0
    poker_game.current_bet = 0
    return poker_game


@pytest.fixture
def mock_connection_manager():
    """Create a mock WebSocket connection manager."""
    with patch('app.api.game_ws.connection_manager') as mock_cm:
        mock_cm.connect = AsyncMock()
        mock_cm.disconnect = MagicMock()
        mock_cm.send_personal_message = AsyncMock()
        mock_cm.broadcast_to_game = AsyncMock()
        yield mock_cm


@pytest.fixture
def mock_game_notifier():
    """Create a mock game notifier."""
    with patch('app.api.game_ws.game_notifier') as mock_notifier:
        mock_notifier.notify_game_update = AsyncMock()
        mock_notifier.notify_action_request = AsyncMock()
        mock_notifier.notify_player_action = AsyncMock()
        mock_notifier.notify_hand_result = AsyncMock()
        yield mock_notifier


# Due to the complexity of testing WebSockets directly with pytest,
# we'll test the process_action_message function directly
class TestGameWebSocketApi:
    """Test suite for the game WebSocket API."""

    @pytest.mark.asyncio
    async def test_process_action_message(self, mock_service, mock_game, mock_poker_game, 
                                         mock_connection_manager, mock_game_notifier):
        """Test processing an action message via WebSocket."""
        from app.api.game_ws import process_action_message
        
        # Setup mock game and player
        game_id = mock_game.id
        player_id = str(uuid.uuid4())
        
        mock_service.get_game.return_value = mock_game
        mock_service.poker_games = {game_id: mock_poker_game}
        
        # Create a mock player
        mock_player = MagicMock()
        mock_player.player_id = player_id
        mock_player.status = PlayerStatus.ACTIVE
        mock_poker_game.players = [mock_player]
        mock_poker_game.current_player_idx = 0
        
        # Setup valid actions
        mock_poker_game.get_valid_actions.return_value = [
            (PlayerAction.CALL, 10),
            (PlayerAction.FOLD, None)
        ]
        
        # Setup process_action to succeed
        mock_poker_game.process_action.return_value = True
        
        # Create WebSocket message
        message = {
            "type": "action",
            "data": {
                "action": "CALL",
                "amount": 10
            }
        }
        
        # Create mock WebSocket
        mock_websocket = AsyncMock()
        
        # Call the function
        await process_action_message(mock_websocket, game_id, message, player_id, mock_service)
        
        # Verify service was called correctly
        mock_service.process_action.assert_called_once()
        # Check that process_action was called with the correct arguments
        # The game_ws.py file calls it with positional args: process_action(game_id, player_id, domain_action, action_amount)
        call_args, call_kwargs = mock_service.process_action.call_args
        # Check positional args
        assert call_args[0] == game_id
        assert call_args[1] == player_id
        assert isinstance(call_args[2], DomainPlayerAction)
        assert call_args[3] == 10
        
        # Verify poker_game.process_action was called
        mock_poker_game.process_action.assert_called_once()
        args, kwargs = mock_poker_game.process_action.call_args
        assert args[0] == mock_player  # Player
        assert args[1] == PlayerAction.CALL  # Action
        assert args[2] == 10  # Amount
        
        # Verify notifications were sent
        mock_game_notifier.notify_player_action.assert_called_once_with(
            game_id, player_id, PlayerAction.CALL.name, 10
        )
        mock_game_notifier.notify_game_update.assert_called_once_with(
            game_id, mock_poker_game
        )
        
    @pytest.mark.asyncio
    async def test_process_action_message_invalid_action(self, mock_service, mock_game, 
                                                       mock_poker_game, mock_connection_manager):
        """Test processing an invalid action via WebSocket."""
        from app.api.game_ws import process_action_message
        
        # Setup mock game and player
        game_id = mock_game.id
        player_id = str(uuid.uuid4())
        
        mock_service.get_game.return_value = mock_game
        mock_service.poker_games = {game_id: mock_poker_game}
        
        # Create a mock player
        mock_player = MagicMock()
        mock_player.player_id = player_id
        mock_player.status = PlayerStatus.ACTIVE
        mock_poker_game.players = [mock_player]
        mock_poker_game.current_player_idx = 0
        
        # Setup valid actions (not including the action we'll send)
        mock_poker_game.get_valid_actions.return_value = [
            (PlayerAction.FOLD, None),
            (PlayerAction.CHECK, None)
        ]
        
        # Create WebSocket message with invalid action
        message = {
            "type": "action",
            "data": {
                "action": "RAISE",  # Not in valid actions
                "amount": 20
            }
        }
        
        # Create mock WebSocket
        mock_websocket = AsyncMock()
        
        # Call the function
        await process_action_message(mock_websocket, game_id, message, player_id, mock_service)
        
        # Verify error message was sent
        mock_connection_manager.send_personal_message.assert_called_once()
        args, kwargs = mock_connection_manager.send_personal_message.call_args
        assert args[0] == mock_websocket
        assert args[1]["type"] == "error"
        assert "invalid_action" in args[1]["data"]["code"]
        
        # Verify no action was processed
        mock_service.process_action.assert_not_called()
        mock_poker_game.process_action.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_process_action_message_not_players_turn(self, mock_service, mock_game, 
                                                         mock_poker_game, mock_connection_manager):
        """Test processing an action when it's not the player's turn."""
        from app.api.game_ws import process_action_message
        
        # Setup mock game and players
        game_id = mock_game.id
        player1_id = str(uuid.uuid4())
        player2_id = str(uuid.uuid4())
        
        mock_service.get_game.return_value = mock_game
        mock_service.poker_games = {game_id: mock_poker_game}
        
        # Create two mock players
        mock_player1 = MagicMock()
        mock_player1.player_id = player1_id
        mock_player1.status = PlayerStatus.ACTIVE
        
        mock_player2 = MagicMock()
        mock_player2.player_id = player2_id
        mock_player2.status = PlayerStatus.ACTIVE
        
        # Set current player to player2
        mock_poker_game.players = [mock_player1, mock_player2]
        mock_poker_game.current_player_idx = 1  # Player 2's turn
        
        # Create WebSocket message from player1 (not their turn)
        message = {
            "type": "action",
            "data": {
                "action": "CALL",
                "amount": 10
            }
        }
        
        # Create mock WebSocket
        mock_websocket = AsyncMock()
        
        # Call the function with player1
        await process_action_message(mock_websocket, game_id, message, player1_id, mock_service)
        
        # Verify error message was sent
        mock_connection_manager.send_personal_message.assert_called_once()
        args, kwargs = mock_connection_manager.send_personal_message.call_args
        assert args[0] == mock_websocket
        assert args[1]["type"] == "error"
        assert "not_your_turn" in args[1]["data"]["code"]
        
        # Verify no action was processed
        mock_service.process_action.assert_not_called()
        mock_poker_game.process_action.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_process_chat_message(self, mock_service, mock_game, mock_poker_game, 
                                       mock_connection_manager):
        """Test processing a chat message via WebSocket."""
        from app.api.game_ws import process_chat_message
        
        # Setup mock game and player
        game_id = mock_game.id
        player_id = str(uuid.uuid4())
        
        mock_service.get_game.return_value = mock_game
        mock_service.poker_games = {game_id: mock_poker_game}
        
        # Create a mock player
        mock_player = MagicMock()
        mock_player.player_id = player_id
        mock_player.name = "Test Player"
        mock_poker_game.players = [mock_player]
        
        # Create WebSocket message
        message = {
            "type": "chat",
            "data": {
                "text": "Hello, world!",
                "target": "table"
            }
        }
        
        # Create mock WebSocket
        mock_websocket = AsyncMock()
        
        # Call the function
        await process_chat_message(mock_websocket, game_id, message, player_id, mock_service)
        
        # Verify broadcast was sent
        mock_connection_manager.broadcast_to_game.assert_called_once()
        args, kwargs = mock_connection_manager.broadcast_to_game.call_args
        assert args[0] == game_id
        assert args[1]["type"] == "chat"
        assert args[1]["data"]["from"] == "Test Player"
        assert args[1]["data"]["text"] == "Hello, world!"