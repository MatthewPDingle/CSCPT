"""
Tests for AI integration with the backend.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json
from fastapi.testclient import TestClient
from fastapi import WebSocket

from app.main import app
from app.services.game_service import GameService
from app.models.domain_models import GameType, GameStatus, PlayerStatus, PlayerAction
from app.core.poker_game import PlayerAction as PokerPlayerAction
from app.core.poker_game import BettingRound, PlayerStatus as PokerPlayerStatus

# Required for the tests to work
client = TestClient(app)

@pytest.fixture
def reset_game_service():
    """Reset the game service before and after each test."""
    GameService._reset_instance_for_testing()
    yield
    GameService._reset_instance_for_testing()

@pytest.fixture
def mock_memory_integration():
    """Mock the memory integration."""
    with patch('ai.memory_integration.MemoryIntegration') as mock:
        # Mock the async get_agent_decision method
        mock.get_agent_decision = AsyncMock(return_value={"action": "fold", "reasoning": {}})
        mock.is_memory_enabled.return_value = True
        yield mock

@pytest.mark.asyncio
async def test_ai_turn_triggering(reset_game_service, mock_memory_integration):
    """Test that AI turns are triggered correctly."""
    # Set up a game with human and AI players
    service = GameService.get_instance()
    game = service.create_cash_game(
        name="Test Game",
        min_buy_in=40,
        max_buy_in=100,
        small_blind=1,
        big_blind=2
    )
    
    # Add a human player
    human_player, _ = service.add_player(
        game_id=game.id,
        name="Human Player",
        is_human=True,
        position=0
    )
    
    # Add an AI player
    ai_player, _ = service.add_player(
        game_id=game.id,
        name="AI Player",
        is_human=False,
        archetype="TAG",
        position=1
    )
    
    # Start the game
    service.start_game(game.id)
    
    # Verify the game has started
    assert game.status == GameStatus.ACTIVE
    assert service.poker_games.get(game.id) is not None
    
    # Mock the notify methods since we're not testing WebSockets here
    with patch('app.core.websocket.GameStateNotifier') as mock_notifier:
        mock_notifier_instance = MagicMock()
        mock_notifier_instance.notify_player_action = AsyncMock()
        mock_notifier_instance.notify_game_update = AsyncMock()
        mock_notifier_instance.notify_action_request = AsyncMock()
        mock_notifier_instance.notify_hand_result = AsyncMock()
        mock_notifier.return_value = mock_notifier_instance
        
        from app.core.websocket import game_notifier
        game_notifier.notify_player_action = AsyncMock()
        game_notifier.notify_game_update = AsyncMock()
        game_notifier.notify_action_request = AsyncMock()
        game_notifier.notify_hand_result = AsyncMock()
        
        # Directly test the _request_and_process_ai_action method
        poker_game = service.poker_games[game.id]
        
        # Determine which player is active now (should be either SB or BB)
        active_players = [p for p in poker_game.players 
                         if p.status == PokerPlayerStatus.ACTIVE]
        current_player = active_players[poker_game.current_player_idx]
        
        # Get the current player's ID
        current_player_id = current_player.player_id
        
        # Find whether it's the human or AI player
        from_domain_current_player = next((p for p in game.players if p.id == current_player_id), None)
        
        # If current player is human, make a move to get to AI's turn
        if from_domain_current_player.is_human:
            # Mock process_action to make a human action
            poker_game.process_action(current_player, PokerPlayerAction.CALL, None)
            
            # Update current_player to the next player
            active_players = [p for p in poker_game.players 
                             if p.status == PokerPlayerStatus.ACTIVE]
            current_player = active_players[poker_game.current_player_idx]
            current_player_id = current_player.player_id
            
            # Verify it's now the AI player's turn
            from_domain_current_player = next((p for p in game.players if p.id == current_player_id), None)
            assert not from_domain_current_player.is_human
        
        # Now test the AI action processing
        await service._request_and_process_ai_action(game.id, current_player_id)
        
        # Verify that the AI action was processed
        mock_memory_integration.get_agent_decision.assert_called_once()
        
        # Verify notifications were sent
        game_notifier.notify_player_action.assert_called_once()
        game_notifier.notify_game_update.assert_called_once()
        
        # Since the action was a fold, we expect the hand to be over or next player to act
        if poker_game.current_round == BettingRound.SHOWDOWN:
            game_notifier.notify_hand_result.assert_called_once()
        else:
            # Check if notify_action_request was called or another AI turn was triggered
            # This depends on whether the next player is human or AI
            active_players = [p for p in poker_game.players 
                             if p.status == PokerPlayerStatus.ACTIVE]
            if active_players:
                next_player = active_players[poker_game.current_player_idx]
                next_player_domain = next((p for p in game.players if p.id == next_player.player_id), None)
                
                if next_player_domain.is_human:
                    game_notifier.notify_action_request.assert_called_once()
        
@pytest.mark.asyncio        
async def test_consecutive_ai_turns(reset_game_service, mock_memory_integration):
    """Test handling of consecutive AI turns."""
    # Set up a game with multiple AI players
    service = GameService.get_instance()
    game = service.create_cash_game(
        name="Test Game",
        min_buy_in=40,
        max_buy_in=100,
        small_blind=1,
        big_blind=2
    )
    
    # Add AI players
    ai_player1, _ = service.add_player(
        game_id=game.id,
        name="AI Player 1",
        is_human=False,
        archetype="TAG",
        position=0
    )
    
    ai_player2, _ = service.add_player(
        game_id=game.id,
        name="AI Player 2",
        is_human=False,
        archetype="LAG",
        position=1
    )
    
    # Start the game
    service.start_game(game.id)
    
    # Verify the game has started
    assert game.status == GameStatus.ACTIVE
    assert service.poker_games.get(game.id) is not None
    
    # Mock the notify methods since we're not testing WebSockets here
    with patch('app.core.websocket.GameStateNotifier') as mock_notifier:
        mock_notifier_instance = MagicMock()
        mock_notifier_instance.notify_player_action = AsyncMock()
        mock_notifier_instance.notify_game_update = AsyncMock()
        mock_notifier_instance.notify_action_request = AsyncMock()
        mock_notifier_instance.notify_hand_result = AsyncMock()
        mock_notifier.return_value = mock_notifier_instance
        
        from app.core.websocket import game_notifier
        game_notifier.notify_player_action = AsyncMock()
        game_notifier.notify_game_update = AsyncMock()
        game_notifier.notify_action_request = AsyncMock()
        game_notifier.notify_hand_result = AsyncMock()
        
        # Directly test the _request_and_process_ai_action method for the first AI player
        poker_game = service.poker_games[game.id]
        
        # Determine which player is active now (should be SB)
        active_players = [p for p in poker_game.players 
                         if p.status == PokerPlayerStatus.ACTIVE]
        current_player = active_players[poker_game.current_player_idx]
        
        # Get the current player's ID
        current_player_id = current_player.player_id
        
        # Mock ai action to be a check, so game continues
        mock_memory_integration.get_agent_decision.return_value = {"action": "check", "reasoning": {}}
        
        # Process the AI action
        await service._request_and_process_ai_action(game.id, current_player_id)
        
        # Verify the action was processed
        mock_memory_integration.get_agent_decision.assert_called_once()
        game_notifier.notify_player_action.assert_called_once()
        game_notifier.notify_game_update.assert_called_once()
        
        # Reset the mocks for the next player
        mock_memory_integration.get_agent_decision.reset_mock()
        game_notifier.notify_player_action.reset_mock()
        game_notifier.notify_game_update.reset_mock()
        
        # Get the next active player (should be the second AI player)
        active_players = [p for p in poker_game.players 
                         if p.status == PokerPlayerStatus.ACTIVE]
        next_player = active_players[poker_game.current_player_idx]
        next_player_id = next_player.player_id
        
        # Verify it's a different player
        assert next_player_id != current_player_id
        
        # Process the second AI action
        await service._request_and_process_ai_action(game.id, next_player_id)
        
        # Verify the second action was processed
        mock_memory_integration.get_agent_decision.assert_called_once()
        game_notifier.notify_player_action.assert_called_once()
        game_notifier.notify_game_update.assert_called_once()
        
        # Since there are only 2 players, we expect the hand to move to the next round
        from app.core.poker_game import BettingRound
        assert poker_game.current_round in [BettingRound.FLOP, BettingRound.SHOWDOWN]

@pytest.mark.asyncio
async def test_error_handling_in_ai_action(reset_game_service, mock_memory_integration):
    """Test error handling when AI processing fails."""
    # Set up a game with an AI player
    service = GameService.get_instance()
    game = service.create_cash_game(
        name="Test Game",
        min_buy_in=40,
        max_buy_in=100,
        small_blind=1,
        big_blind=2
    )
    
    # Add an AI player
    ai_player, _ = service.add_player(
        game_id=game.id,
        name="AI Player",
        is_human=False,
        archetype="TAG",
        position=0
    )
    
    # Add another player to keep the game going
    human_player, _ = service.add_player(
        game_id=game.id,
        name="Human Player",
        is_human=True,
        position=1
    )
    
    # Start the game
    service.start_game(game.id)
    
    # Mock the notify methods
    with patch('app.core.websocket.GameStateNotifier') as mock_notifier:
        mock_notifier_instance = MagicMock()
        mock_notifier_instance.notify_player_action = AsyncMock()
        mock_notifier_instance.notify_game_update = AsyncMock()
        mock_notifier_instance.notify_action_request = AsyncMock()
        mock_notifier_instance.notify_hand_result = AsyncMock()
        mock_notifier.return_value = mock_notifier_instance
        
        from app.core.websocket import game_notifier
        game_notifier.notify_player_action = AsyncMock()
        game_notifier.notify_game_update = AsyncMock()
        game_notifier.notify_action_request = AsyncMock()
        game_notifier.notify_hand_result = AsyncMock()
        
        # Make the AI service raise an exception
        mock_memory_integration.get_agent_decision.side_effect = Exception("Test error")
        
        # Determine which player is active 
        poker_game = service.poker_games[game.id]
        active_players = [p for p in poker_game.players 
                         if p.status == PokerPlayerStatus.ACTIVE]
        current_player = active_players[poker_game.current_player_idx]
        current_player_id = current_player.player_id
        
        # Get the domain player
        from_domain_current_player = next((p for p in game.players if p.id == current_player_id), None)
        
        # If current player is human, make a move to get to AI's turn
        if from_domain_current_player.is_human:
            # Mock process_action to make a human action
            poker_game.process_action(current_player, PokerPlayerAction.CALL, None)
            
            # Update current_player to the next player
            active_players = [p for p in poker_game.players 
                             if p.status == PokerPlayerStatus.ACTIVE]
            current_player = active_players[poker_game.current_player_idx]
            current_player_id = current_player.player_id
            
            # Verify it's now the AI player's turn
            from_domain_current_player = next((p for p in game.players if p.id == current_player_id), None)
            assert not from_domain_current_player.is_human
        
        # Process the AI action that will fail
        await service._request_and_process_ai_action(game.id, current_player_id)
        
        # Verify the error handling
        mock_memory_integration.get_agent_decision.assert_called_once()
        
        # The AI should fold on error
        game_notifier.notify_player_action.assert_called_once_with(game.id, current_player_id, "FOLD", None)
        game_notifier.notify_game_update.assert_called_once()
        
        # Verify the player status is now folded
        player_in_game = next((p for p in poker_game.players if p.player_id == current_player_id), None)
        assert player_in_game.status == PokerPlayerStatus.FOLDED

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])