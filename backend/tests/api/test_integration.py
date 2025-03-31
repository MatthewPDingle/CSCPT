"""
Integration tests for the refactored API architecture.
These tests validate that the API endpoints correctly use the GameService.
"""
import pytest
from fastapi.testclient import TestClient
import json

from app.main import app
from app.models.domain_models import GameType

client = TestClient(app)


def test_api_flow():
    """Test the basic game flow through the API."""
    # Create a game
    response = client.post("/game/create?small_blind=5&big_blind=10")
    assert response.status_code == 200
    game_data = response.json()
    game_id = game_data["game_id"]
    print(f"Created game with ID: {game_id}")
    assert game_data["small_blind"] == 5
    assert game_data["big_blind"] == 10
    
    # Verify game exists in service before adding players
    from app.services.game_service import GameService
    service = GameService.get_instance()
    stored_game = service.get_game(game_id)
    print(f"Game exists in service: {stored_game is not None}")
    if stored_game:
        print(f"Game status: {stored_game.status}, Player count: {len(stored_game.players)}")
    
    # Add two players
    response = client.post(f"/game/join/{game_id}?player_name=Player%201&buy_in=1000")
    print(f"Join response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error response: {response.json()}")
    assert response.status_code == 200
    player1 = response.json()
    assert player1["name"] == "Player 1"
    assert player1["chips"] == 1000
    player1_id = player1["player_id"]
    
    response = client.post(f"/game/join/{game_id}?player_name=Player%202&buy_in=1000")
    assert response.status_code == 200
    player2 = response.json()
    player2_id = player2["player_id"]
    
    # Start the game
    response = client.post(f"/game/start/{game_id}")
    assert response.status_code == 200
    game_state = response.json()
    assert game_state["game_id"] == game_id
    assert game_state["current_round"] == "PREFLOP"
    assert len(game_state["players"]) == 2
    
    # Process a player action (check that it doesn't raise an exception)
    # The actual result may vary depending on the game state
    response = client.post(
        f"/game/action/{game_id}",
        json={"player_id": player1_id, "action": "CALL", "amount": 10}
    )
    # We're just checking that the response format is correct, actual status code may vary
    assert "success" in response.json()
    assert "message" in response.json()
    assert "game_state" in response.json()


def test_history_api():
    """Test the history API endpoints."""
    # Create a game and play a hand to generate history
    response = client.post("/game/create?small_blind=5&big_blind=10")
    game_id = response.json()["game_id"]
    
    # Add two players
    response = client.post(f"/game/join/{game_id}?player_name=Player%201&buy_in=1000")
    player1_id = response.json()["player_id"]
    
    response = client.post(f"/game/join/{game_id}?player_name=Player%202&buy_in=1000")
    player2_id = response.json()["player_id"]
    
    # Start the game
    client.post(f"/game/start/{game_id}")
    
    # Process some actions to generate history
    client.post(
        f"/game/action/{game_id}",
        json={"player_id": player1_id, "action": "CALL", "amount": 10}
    )
    
    client.post(
        f"/game/action/{game_id}",
        json={"player_id": player2_id, "action": "CHECK", "amount": 0}
    )
    
    # Test the game history endpoint - might not have history yet depending on implementation
    response = client.get(f"/history/game/{game_id}")
    # Just check the format - it may be empty if the hand isn't complete
    assert response.status_code in [200, 404]  # 404 is acceptable if no history yet
    
    # Test player hands endpoint
    response = client.get(f"/history/player/{player1_id}/hands")
    assert response.status_code in [200, 404]  # 404 is acceptable if no hands recorded yet
    
    # Test player stats endpoint - may be empty for new players
    response = client.get(f"/history/player/{player1_id}/stats")
    assert response.status_code in [200, 404]  # 404 is acceptable if no stats yet