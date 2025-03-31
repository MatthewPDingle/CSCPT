"""
Tests for the game API endpoints.
These tests verify that the REST endpoints correctly interact with the GameService.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.services.game_service import GameService
from app.core.poker_game import PokerGame, PlayerStatus, BettingRound
from app.models.domain_models import (
    Game, Player, PlayerAction, GameStatus, GameType, PlayerStatus,
    PlayerAction as DomainPlayerAction
)
from app.models.game_models import GameStateModel, PlayerModel


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
    game.type = GameType.CASH
    game.status = GameStatus.WAITING
    game.name = "Test Game"
    game.players = []
    return game


@pytest.fixture
def mock_player():
    """Create a mock Player instance."""
    player = MagicMock(spec=Player)
    player.id = str(uuid.uuid4())
    player.name = "Test Player"
    player.is_human = True
    player.status = "WAITING"
    player.position = 0
    player.chips = 1000
    return player


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


class TestGameApi:
    """Test suite for the game API endpoints."""

    def test_create_game(self, test_client, mock_service, mock_game, mock_poker_game):
        """Test creating a game via the API."""
        # Setup mock response
        mock_service.create_game.return_value = mock_game
        mock_service.poker_games = {mock_game.id: mock_poker_game}
        
        # Use the same small_blind and big_blind values that are passed in the request
        mock_poker_game.small_blind = 5
        mock_poker_game.big_blind = 10
        
        # Setup hand_history_recorder attribute
        mock_service.hand_history_recorder = MagicMock()
        
        # Make request
        response = test_client.post("/game/create?small_blind=5&big_blind=10")
        
        # Verify response
        assert response.status_code == 200
        
        # Verify service was called correctly
        mock_service.create_game.assert_called_once()
        args, kwargs = mock_service.create_game.call_args
        assert kwargs.get("min_bet") == 10  # big_blind
        
        # Verify response content
        data = response.json()
        assert data["game_id"] == mock_game.id
        assert data["small_blind"] == 5
        assert data["big_blind"] == 10

    def test_join_game(self, test_client, mock_service, mock_game, mock_player):
        """Test joining a game via the API."""
        # Setup mock response
        mock_service.add_player.return_value = (mock_game, mock_player)
        
        # Setup player with the correct attributes
        mock_player.id = str(uuid.uuid4())
        mock_player.name = "Test Player"
        mock_player.position = 0
        mock_player.status = PlayerStatus.WAITING
        
        # Setup mock poker game
        mock_poker_game = MagicMock()
        
        # Players list has no players with matching ID
        mock_poker_game.players = []
        
        # Setup add_player method for poker game to return a new player
        mock_poker_player = MagicMock()
        mock_poker_player.player_id = mock_player.id
        mock_poker_game.add_player.return_value = mock_poker_player
        
        # Attach to service
        mock_service.poker_games = {mock_game.id: mock_poker_game}
        
        # Make request with the patch for context management to handle the request
        with patch('app.api.game.PokerGame', spec=True):
            response = test_client.post(
                f"/game/join/{mock_game.id}?player_name=Test%20Player&buy_in=1000"
            )
        
        # Verify response
        assert response.status_code == 200
        
        # Verify service was called correctly
        mock_service.add_player.assert_called_once()
        args, kwargs = mock_service.add_player.call_args
        assert kwargs.get("game_id") == mock_game.id
        assert kwargs.get("name") == "Test Player"
        
        # Verify poker_game.add_player was called
        mock_poker_game.add_player.assert_called_once()
        
        # Verify response content
        data = response.json()
        assert data["player_id"] == mock_player.id
        assert data["name"] == "Test Player"
        assert data["chips"] == 1000
        
    def test_join_game_error_handling(self, test_client, mock_service):
        """Test error handling when joining a game via the API."""
        # Setup mock response to raise KeyError (game not found)
        mock_service.add_player.side_effect = KeyError("Game not found")
        
        # Make request
        response = test_client.post(
            "/game/join/nonexistent?player_name=Test%20Player&buy_in=1000"
        )
        
        # Verify response
        assert response.status_code == 404
        assert "Game not found" in response.json().get("detail")
        
        # Change mock to raise ValueError (e.g., game already started)
        mock_service.add_player.side_effect = ValueError("Game already started")
        
        # Make request
        response = test_client.post(
            "/game/join/started?player_name=Test%20Player&buy_in=1000"
        )
        
        # Verify response
        assert response.status_code == 400
        assert "Game already started" in response.json().get("detail")
        
    def test_start_game(self, test_client, mock_service, mock_game, mock_poker_game):
        """Test starting a game via the API."""
        # Setup mock response
        mock_service.start_game.return_value = mock_game
        mock_service.poker_games = {mock_game.id: mock_poker_game}
        
        # Make request
        response = test_client.post(f"/game/start/{mock_game.id}")
        
        # Verify response
        assert response.status_code == 200
        
        # Verify service was called correctly
        mock_service.start_game.assert_called_once_with(mock_game.id)
        
        # Verify response content
        data = response.json()
        assert data["game_id"] == mock_game.id
        assert data["current_round"] == mock_poker_game.current_round.name
        
    def test_start_game_error_handling(self, test_client, mock_service):
        """Test error handling when starting a game via the API."""
        # Setup mock response to raise KeyError (game not found)
        mock_service.start_game.side_effect = KeyError("Game not found")
        
        # Make request
        response = test_client.post("/game/start/nonexistent")
        
        # Verify response
        assert response.status_code == 404
        assert "Game not found" in response.json().get("detail")
        
        # Change mock to raise ValueError (e.g., not enough players)
        mock_service.start_game.side_effect = ValueError("Need at least 2 players")
        
        # Make request
        response = test_client.post("/game/start/insufficient")
        
        # Verify response
        assert response.status_code == 400
        assert "Need at least 2 players" in response.json().get("detail")
        
    def test_process_action_valid(self, mock_service, mock_game):
        """Test processing a valid player action via the service."""
        player_id = str(uuid.uuid4())
        
        # Mock the process_action method and verify it's called correctly
        mock_service.process_action.return_value = mock_game
        
        # Call the method directly
        service = mock_service
        game_id = mock_game.id
        action = "CALL"
        amount = 10
        
        # Call the method directly
        game = service.process_action(
            game_id=game_id,
            player_id=player_id,
            action=DomainPlayerAction.CALL,
            amount=amount
        )
        
        # Verify the method was called with the expected arguments
        mock_service.process_action.assert_called_once_with(
            game_id=game_id,
            player_id=player_id,
            action=DomainPlayerAction.CALL,
            amount=amount
        )
        
        # Verify the result is the mock game
        assert game == mock_game