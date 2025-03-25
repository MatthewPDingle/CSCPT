"""
Unit tests for the game service.
"""
import pytest
import uuid
from datetime import datetime

from app.models.domain_models import (
    Game, Player, Hand, GameType, GameStatus, 
    PlayerStatus, PlayerAction, BettingRound
)
from app.services.game_service import GameService
from app.repositories.in_memory import (
    GameRepository, UserRepository, ActionHistoryRepository, HandRepository,
    RepositoryFactory
)


class TestGameService:
    """Tests for the GameService class."""

    @pytest.fixture
    def game_service(self):
        """Create a GameService instance for testing."""
        return GameService()

    def test_create_cash_game(self, game_service):
        """Test creating a cash game."""
        game = game_service.create_game(
            game_type=GameType.CASH,
            name="Test Cash Game",
            buy_in=1000,
            min_bet=20,
            ante=5
        )
        
        # Verify the game was created correctly
        assert game.id is not None
        assert game.type == GameType.CASH
        assert game.status == GameStatus.WAITING
        assert game.name == "Test Cash Game"
        assert game.cash_game_info is not None
        assert game.cash_game_info.buy_in == 1000
        assert game.cash_game_info.min_bet == 20
        assert game.cash_game_info.ante == 5
        assert game.tournament_info is None
        
        # Verify the game was stored in the repository
        stored_game = game_service.game_repo.get(game.id)
        assert stored_game is not None
        assert stored_game.id == game.id

    def test_create_tournament(self, game_service):
        """Test creating a tournament."""
        game = game_service.create_game(
            game_type=GameType.TOURNAMENT,
            name="Test Tournament",
            tier="National",
            stage="Beginning",
            starting_chips=50000
        )
        
        # Verify the game was created correctly
        assert game.id is not None
        assert game.type == GameType.TOURNAMENT
        assert game.status == GameStatus.WAITING
        assert game.name == "Test Tournament"
        assert game.tournament_info is not None
        assert game.tournament_info.tier == "National"
        assert game.tournament_info.stage == "Beginning"
        assert game.tournament_info.starting_chips == 50000
        assert game.cash_game_info is None
        
        # Verify the game was stored in the repository
        stored_game = game_service.game_repo.get(game.id)
        assert stored_game is not None
        assert stored_game.id == game.id

    def test_add_player(self, game_service):
        """Test adding a player to a game."""
        # Create a game first
        game = game_service.create_game(
            game_type=GameType.CASH,
            name="Test Game"
        )
        
        # Add a human player
        updated_game, player = game_service.add_player(
            game_id=game.id,
            name="Human Player",
            is_human=True
        )
        
        # Verify the player was added correctly
        assert player.id is not None
        assert player.name == "Human Player"
        assert player.is_human is True
        assert player.status == PlayerStatus.WAITING
        assert player.chips == game.cash_game_info.buy_in
        
        # Verify the player is in the game
        assert len(updated_game.players) == 1
        assert updated_game.players[0].id == player.id
        
        # Add an AI player
        updated_game, ai_player = game_service.add_player(
            game_id=game.id,
            name="AI Player",
            is_human=False,
            archetype="TAG"
        )
        
        # Verify the AI player was added correctly
        assert ai_player.id is not None
        assert ai_player.name == "AI Player"
        assert ai_player.is_human is False
        assert ai_player.archetype == "TAG"
        
        # Verify both players are in the game
        assert len(updated_game.players) == 2
        
        # Test error cases
        
        # Test adding player to non-existent game
        with pytest.raises(KeyError):
            game_service.add_player(
                game_id="non-existent-id",
                name="Test Player"
            )
            
        # Start the game to test adding a player to an active game
        game_service.start_game(game.id)
        
        # Test adding player to an active game
        with pytest.raises(ValueError):
            game_service.add_player(
                game_id=game.id,
                name="Late Player"
            )

    def test_start_game(self, game_service):
        """Test starting a game."""
        # Create a game first
        game = game_service.create_game(
            game_type=GameType.CASH,
            name="Test Game"
        )
        
        # Add players
        game_service.add_player(game_id=game.id, name="Player 1", is_human=True)
        game_service.add_player(game_id=game.id, name="Player 2", is_human=False)
        
        # Start the game
        started_game = game_service.start_game(game.id)
        
        # Verify the game was started correctly
        assert started_game.status == GameStatus.ACTIVE
        assert started_game.started_at is not None
        assert started_game.current_hand is not None
        
        # Verify the hand was created correctly
        hand = started_game.current_hand
        assert hand.id is not None
        assert hand.game_id == game.id
        assert hand.hand_number == 1
        assert len(hand.active_player_ids) == 2
        assert hand.current_round == BettingRound.PREFLOP
        
        # Verify the hand was stored in the repository
        stored_hand = game_service.hand_repo.get(hand.id)
        assert stored_hand is not None
        assert stored_hand.id == hand.id
        
        # Test error cases
        
        # Test starting a non-existent game
        with pytest.raises(KeyError):
            game_service.start_game("non-existent-id")
            
        # Test starting an already active game
        with pytest.raises(ValueError):
            game_service.start_game(game.id)
            
        # Test starting a game with insufficient players
        insufficient_game = game_service.create_game(
            game_type=GameType.CASH,
            name="Insufficient Players"
        )
        game_service.add_player(game_id=insufficient_game.id, name="Lonely Player")
        
        with pytest.raises(ValueError):
            game_service.start_game(insufficient_game.id)

    def test_process_action(self, game_service):
        """Test processing a player action."""
        # Create and start a game first
        game = game_service.create_game(
            game_type=GameType.CASH,
            name="Test Game"
        )
        
        # Add players
        _, player1 = game_service.add_player(game_id=game.id, name="Player 1", is_human=True)
        _, player2 = game_service.add_player(game_id=game.id, name="Player 2", is_human=False)
        
        # Start the game
        started_game = game_service.start_game(game.id)
        
        # Process an action
        updated_game = game_service.process_action(
            game_id=game.id,
            player_id=player1.id,
            action=PlayerAction.CALL
        )
        
        # Verify the action was recorded
        assert len(updated_game.current_hand.actions) == 1
        action = updated_game.current_hand.actions[0]
        assert action.player_id == player1.id
        assert action.action == PlayerAction.CALL
        assert action.round == BettingRound.PREFLOP
        
        # Verify the action was stored in the repository
        stored_actions = game_service.action_repo.get_by_hand(updated_game.current_hand.id)
        assert len(stored_actions) == 1
        assert stored_actions[0].id == action.id
        
        # Test error cases
        
        # Test processing action for non-existent game
        with pytest.raises(KeyError):
            game_service.process_action(
                game_id="non-existent-id",
                player_id=player1.id,
                action=PlayerAction.CALL
            )
            
        # Test processing action for non-existent player
        with pytest.raises(KeyError):
            game_service.process_action(
                game_id=game.id,
                player_id="non-existent-id",
                action=PlayerAction.CALL
            )
            
        # Test processing action for a game that's not active
        inactive_game = game_service.create_game(
            game_type=GameType.CASH,
            name="Inactive Game"
        )
        _, inactive_player = game_service.add_player(
            game_id=inactive_game.id,
            name="Inactive Player"
        )
        
        with pytest.raises(ValueError):
            game_service.process_action(
                game_id=inactive_game.id,
                player_id=inactive_player.id,
                action=PlayerAction.CALL
            )