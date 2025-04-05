"""
Tests for setup API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.game_service import GameService
from app.repositories.in_memory import RepositoryFactory

client = TestClient(app)

@pytest.fixture
def reset_state():
    """Reset service state before each test."""
    GameService._reset_instance_for_testing()
    RepositoryFactory._reset_instance_for_testing()
    yield

class TestSetupAPI:
    """Test class for setup API endpoints."""
    
    def test_setup_cash_game(self, reset_state):
        """Test setting up a cash game via the setup API."""
        # Prepare request data
        data = {
            "game_mode": "cash",
            "small_blind": 5,
            "big_blind": 10,
            "min_buy_in": 400,  # Chips (not BB)
            "max_buy_in": 2000,  # Chips (not BB)
            "players": [
                {
                    "name": "Human Player",
                    "is_human": True,
                    "buy_in": 1000
                },
                {
                    "name": "AI Player",
                    "is_human": False,
                    "archetype": "TAG",
                    "buy_in": 1000
                }
            ]
        }
        
        # Send request
        response = client.post("/setup/game", json=data)
        
        # Verify success
        assert response.status_code == 200
        result = response.json()
        assert "game_id" in result
        assert "human_player_id" in result
        
        # Verify game was created correctly by fetching it
        game_service = GameService.get_instance()
        game = game_service.get_game(result["game_id"])
        
        assert game is not None
        assert game.type == "cash"
        assert game.status == "active"  # Game is started automatically
        assert len(game.players) == 2
        
        # Verify cash game info
        assert game.cash_game_info is not None
        assert game.cash_game_info.min_buy_in == 400
        assert game.cash_game_info.max_buy_in == 2000
        assert game.cash_game_info.small_blind == 5
        assert game.cash_game_info.big_blind == 10
        
        # Verify players
        human_player = next((p for p in game.players if p.id == result["human_player_id"]), None)
        assert human_player is not None
        assert human_player.name == "Human Player"
        assert human_player.is_human == True
        assert human_player.chips == 1000
        
        ai_player = next((p for p in game.players if p.id != result["human_player_id"]), None)
        assert ai_player is not None
        assert ai_player.name == "AI Player"
        assert ai_player.is_human == False
        assert ai_player.archetype == "TAG"
        assert ai_player.chips == 1000
        
    def test_setup_cash_game_invalid_buy_in(self, reset_state):
        """Test setting up a cash game with invalid buy-in."""
        # Prepare request data with a player buy-in below the minimum
        data = {
            "game_mode": "cash",
            "small_blind": 5,
            "big_blind": 10,
            "min_buy_in": 400,
            "max_buy_in": 2000,
            "players": [
                {
                    "name": "Human Player",
                    "is_human": True,
                    "buy_in": 300  # Below minimum buy-in
                }
            ]
        }
        
        # Send request
        response = client.post("/setup/game", json=data)
        
        # Verify error
        assert response.status_code == 400
        assert "buy-in" in response.json()["detail"].lower()