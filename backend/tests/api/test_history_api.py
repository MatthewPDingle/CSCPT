# mypy: ignore-errors
"""
Tests for the history API endpoints.
These tests verify that the historical data endpoints correctly interact with the GameService.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import uuid
from datetime import datetime

from app.main import app
from app.services.game_service import GameService
from app.models.domain_models import Game, HandHistory, PlayerHandSnapshot, PlayerStats


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
    return game


@pytest.fixture
def mock_hand_history():
    """Create a mock HandHistory instance."""
    hand_id = str(uuid.uuid4())
    game_id = str(uuid.uuid4())

    history = MagicMock(spec=HandHistory)
    history.id = hand_id
    history.game_id = game_id
    history.hand_number = 1
    history.timestamp_start = datetime.now()
    history.timestamp_end = datetime.now()
    history.players = [
        MagicMock(spec=PlayerHandSnapshot),
        MagicMock(spec=PlayerHandSnapshot),
    ]

    # Setup dict method to return serialized data
    history.dict.return_value = {
        "id": hand_id,
        "game_id": game_id,
        "hand_number": 1,
        "players": [],
    }

    return history


@pytest.fixture
def mock_player_stats():
    """Create mock player statistics."""
    player_id = str(uuid.uuid4())

    stats = MagicMock(spec=PlayerStats)
    stats.player_id = player_id
    stats.hands_played = 10
    stats.hands_won = 3
    stats.vpip = 0.7
    stats.pfr = 0.3

    # Setup dict method to return serialized data
    stats.dict.return_value = {
        "player_id": player_id,
        "hands_played": 10,
        "hands_won": 3,
        "vpip": 0.7,
        "pfr": 0.3,
    }

    return stats


class TestHistoryApi:
    """Test suite for the history API endpoints."""

    def test_get_game_hand_histories(
        self, test_client, mock_service, mock_game, mock_hand_history
    ):
        """Test retrieving hand histories for a game."""
        game_id = mock_game.id

        # Setup mock responses
        mock_service.get_game.return_value = mock_game
        mock_service.get_game_hand_histories.return_value = [mock_hand_history]

        # Make request
        response = test_client.get(f"/history/game/{game_id}")

        # Verify response
        assert response.status_code == 200

        # Verify service was called correctly
        mock_service.get_game.assert_called_once_with(game_id)
        mock_service.get_game_hand_histories.assert_called_once_with(game_id)

        # Verify response content
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == mock_hand_history.id
        assert data[0]["game_id"] == mock_hand_history.game_id
        assert data[0]["hand_number"] == 1

    def test_get_game_hand_histories_error_handling(self, test_client, mock_service):
        """Test error handling when retrieving hand histories."""
        # Setup mock response to raise KeyError (game not found)
        mock_service.get_game.return_value = None

        # Make request
        response = test_client.get("/history/game/nonexistent")

        # Verify response
        assert response.status_code == 404
        assert "Game not found" in response.json().get("detail")

    def test_get_hand_history(
        self, test_client, mock_service, mock_game, mock_hand_history
    ):
        """Test retrieving a specific hand history."""
        game_id = mock_game.id
        hand_id = mock_hand_history.id

        # Setup mock responses
        mock_service.get_game.return_value = mock_game
        mock_service.get_hand_history.return_value = mock_hand_history

        # Ensure the mock hand history belongs to the mock game
        mock_hand_history.game_id = game_id

        # Setup dict/model_dump method on mock
        hand_dict = {
            "id": hand_id,
            "game_id": game_id,
            "hand_number": 1,
            "players": [],
            "community_cards": [],
            "betting_rounds": {},
            "pot_results": [],
        }
        # Handle both Pydantic v1 (dict) and v2 (model_dump)
        mock_hand_history.dict.return_value = hand_dict
        if hasattr(mock_hand_history, "model_dump"):
            mock_hand_history.model_dump.return_value = hand_dict

        # Make request
        response = test_client.get(f"/history/hand/{game_id}/{hand_id}")

        # Verify response
        assert response.status_code == 200

        # Verify service was called correctly
        mock_service.get_game.assert_called_once_with(game_id)
        mock_service.get_hand_history.assert_called_once_with(hand_id)

        # Verify response content
        data = response.json()
        assert data["id"] == hand_id
        assert data["game_id"] == game_id
        assert data["hand_number"] == 1

    def test_get_hand_history_error_handling(
        self, test_client, mock_service, mock_game
    ):
        """Test error handling when retrieving a specific hand history."""
        game_id = mock_game.id
        hand_id = str(uuid.uuid4())

        # Setup game exists but hand history doesn't
        mock_service.get_game.return_value = mock_game
        mock_service.get_hand_history.return_value = None

        # Make request
        response = test_client.get(f"/history/hand/{game_id}/{hand_id}")

        # Verify response
        assert response.status_code == 404
        assert "Hand history not found" in response.json().get("detail")

        # Setup hand history exists but belongs to different game
        mock_hand_history = MagicMock(spec=HandHistory)
        mock_hand_history.game_id = str(uuid.uuid4())  # Different game ID
        mock_service.get_hand_history.return_value = mock_hand_history

        # Make request
        response = test_client.get(f"/history/hand/{game_id}/{hand_id}")

        # Verify response
        assert response.status_code == 403
        assert "Hand does not belong to this game" in response.json().get("detail")

    def test_get_player_statistics(self, test_client, mock_service, mock_player_stats):
        """Test retrieving player statistics."""
        player_id = mock_player_stats.player_id

        # Setup mock responses
        mock_service.get_player_stats.return_value = mock_player_stats

        # Setup dict/model_dump method on mock
        stats_dict = {
            "player_id": player_id,
            "hands_played": 10,
            "hands_won": 3,
            "vpip": 0.7,
            "pfr": 0.3,
        }
        # Handle both Pydantic v1 (dict) and v2 (model_dump)
        mock_player_stats.dict.return_value = stats_dict
        if hasattr(mock_player_stats, "model_dump"):
            mock_player_stats.model_dump.return_value = stats_dict

        # Make request
        response = test_client.get(f"/history/player/{player_id}/stats")

        # Verify response
        assert response.status_code == 200

        # Verify service was called correctly
        mock_service.get_player_stats.assert_called_once_with(player_id, None)

        # Verify response content
        data = response.json()
        assert data["player_id"] == player_id
        assert data["hands_played"] == 10
        assert data["hands_won"] == 3
        assert data["vpip"] == 0.7
        assert data["pfr"] == 0.3

        # Test with game_id parameter
        game_id = str(uuid.uuid4())
        mock_service.get_player_stats.reset_mock()

        # Make request with game_id
        response = test_client.get(
            f"/history/player/{player_id}/stats?game_id={game_id}"
        )

        # Verify service was called correctly
        mock_service.get_player_stats.assert_called_once_with(player_id, game_id)

    def test_get_player_statistics_error_handling(self, test_client, mock_service):
        """Test error handling when retrieving player statistics."""
        player_id = str(uuid.uuid4())

        # Setup mock response to return None (stats not found)
        mock_service.get_player_stats.return_value = None

        # Make request
        response = test_client.get(f"/history/player/{player_id}/stats")

        # Verify response
        assert response.status_code == 404
        assert "Player or stats not found" in response.json().get("detail")

    def test_get_player_hands(self, test_client, mock_service, mock_hand_history):
        """Test retrieving hands played by a player."""
        player_id = str(uuid.uuid4())

        # Setup mock responses
        # Get a mock repository that'll return our hand history
        mock_repo = MagicMock()
        mock_repo.get_by_player.return_value = [mock_hand_history]

        # Setup the repo factory attribute and its get_repository method
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_repo

        # Setup hand_history_repo attribute with a __class__ attribute
        # that can be used by the repository factory
        from app.repositories.in_memory import HandHistoryRepository

        mock_hand_history_repo = MagicMock(spec=HandHistoryRepository)
        mock_hand_history_repo.__class__ = HandHistoryRepository

        # Setup mock service
        mock_service.repo_factory = mock_repo_factory
        mock_service.hand_history_repo = mock_hand_history_repo

        # Setup dict/model_dump method on mock hand history
        hand_dict = {
            "id": mock_hand_history.id,
            "game_id": mock_hand_history.game_id,
            "hand_number": 1,
            "players": [],
            "community_cards": [],
            "betting_rounds": {},
            "pot_results": [],
            "timestamp_start": datetime.now(),
        }
        # Handle both Pydantic v1 (dict) and v2 (model_dump)
        mock_hand_history.dict.return_value = hand_dict
        if hasattr(mock_hand_history, "model_dump"):
            mock_hand_history.model_dump.return_value = hand_dict

        # Make sure the sorting by timestamp will work
        mock_hand_history.timestamp_start = datetime.now()

        # Make request
        response = test_client.get(f"/history/player/{player_id}/hands")

        # Verify response
        assert response.status_code == 200

        # Verify service/repo was called correctly
        mock_repo_factory.get_repository.assert_called_once()
        mock_repo.get_by_player.assert_called_once_with(player_id)

        # Verify response content
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == mock_hand_history.id
        assert data[0]["game_id"] == mock_hand_history.game_id

        # Test with game_id filter and limit
        game_id = mock_hand_history.game_id
        mock_repo_factory.get_repository.reset_mock()
        mock_repo.get_by_player.reset_mock()

        # Make request with game_id and limit
        response = test_client.get(
            f"/history/player/{player_id}/hands?game_id={game_id}&limit=5"
        )

        # Verify repo was called correctly
        mock_repo_factory.get_repository.assert_called_once()
        mock_repo.get_by_player.assert_called_once_with(player_id)

        # Verify filtering was applied
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Only one history that matches game_id
