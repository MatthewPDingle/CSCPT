# mypy: ignore-errors
"""
Unit tests for the game service.
"""

import pytest
import uuid
from datetime import datetime

from app.models.domain_models import (
    Game,
    Player,
    Hand,
    GameType,
    GameStatus,
    PlayerStatus,
    PlayerAction,
    BettingRound,
)
from app.services.game_service import GameService
from app.repositories.in_memory import (
    GameRepository,
    UserRepository,
    ActionHistoryRepository,
    HandRepository,
    RepositoryFactory,
)


class TestGameService:
    """Tests for the GameService class."""

    @pytest.fixture
    def game_service(self):
        """Create a GameService instance for testing."""
        return GameService.get_instance()

    def test_create_cash_game(self, game_service):
        """Test creating a cash game."""
        game = game_service.create_game(
            game_type=GameType.CASH,
            name="Test Cash Game",
            buy_in=1000,
            min_bet=20,
            ante=5,
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
            starting_chips=50000,
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
        game = game_service.create_game(game_type=GameType.CASH, name="Test Game")

        # Add a human player
        updated_game, player = game_service.add_player(
            game_id=game.id, name="Human Player", is_human=True
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
            game_id=game.id, name="AI Player", is_human=False, archetype="TAG"
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
            game_service.add_player(game_id="non-existent-id", name="Test Player")

        # Start the game to test adding a player to an active game
        game_service.start_game(game.id)

        # For cash games, we now allow adding players mid-game
        # So this should NOT raise an error
        _, late_player = game_service.add_player(game_id=game.id, name="Late Player")

        # Verify the player was added correctly
        assert (
            late_player.status == PlayerStatus.WAITING
        )  # New players wait for next hand

    def test_start_game(self, game_service):
        """Test starting a game."""
        # Create a game first
        game = game_service.create_game(game_type=GameType.CASH, name="Test Game")

        # Add players
        game_service.add_player(game_id=game.id, name="Player 1", is_human=True)
        game_service.add_player(game_id=game.id, name="Player 2", is_human=False)

        # Start the game (use synchronous version for tests)
        started_game = game_service.start_game_sync(game.id)

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
            game_service.start_game_sync("non-existent-id")

        # Test starting an already active game
        with pytest.raises(ValueError):
            game_service.start_game_sync(game.id)

        # Test starting a game with insufficient players
        insufficient_game = game_service.create_game(
            game_type=GameType.CASH, name="Insufficient Players"
        )
        game_service.add_player(game_id=insufficient_game.id, name="Lonely Player")

        with pytest.raises(ValueError):
            game_service.start_game_sync(insufficient_game.id)

    def test_process_action(self, game_service):
        """Test processing a player action."""
        # Create and start a game first
        game = game_service.create_game(game_type=GameType.CASH, name="Test Game")

        # Add players
        _, player1 = game_service.add_player(
            game_id=game.id, name="Player 1", is_human=True
        )
        _, player2 = game_service.add_player(
            game_id=game.id, name="Player 2", is_human=False
        )

        # Start the game (use synchronous version for tests)
        started_game = game_service.start_game_sync(game.id)

        # Process an action
        updated_game = game_service.process_action(
            game_id=game.id, player_id=player1.id, action=PlayerAction.CALL
        )

        # Verify the action was recorded in domain model
        assert len(updated_game.current_hand.actions) == 1
        action = updated_game.current_hand.actions[0]
        assert action.player_id == player1.id
        assert action.action == PlayerAction.CALL
        assert action.round == BettingRound.PREFLOP

        # Verify the action was stored in the repository
        stored_actions = game_service.action_repo.get_by_hand(
            updated_game.current_hand.id
        )
        assert len(stored_actions) == 1
        assert stored_actions[0].id == action.id

        # Verify the action was processed in the PokerGame instance
        poker_game = game_service.poker_games.get(game.id)
        assert poker_game is not None

        # Test error cases

        # Test processing action for non-existent game
        with pytest.raises(KeyError):
            game_service.process_action(
                game_id="non-existent-id",
                player_id=player1.id,
                action=PlayerAction.CALL,
            )

        # Test processing action for non-existent player
        with pytest.raises(KeyError):
            game_service.process_action(
                game_id=game.id, player_id="non-existent-id", action=PlayerAction.CALL
            )

        # Test processing action for a game that's not active
        inactive_game = game_service.create_game(
            game_type=GameType.CASH, name="Inactive Game"
        )
        _, inactive_player = game_service.add_player(
            game_id=inactive_game.id, name="Inactive Player"
        )

        with pytest.raises(ValueError):
            game_service.process_action(
                game_id=inactive_game.id,
                player_id=inactive_player.id,
                action=PlayerAction.CALL,
            )

    def test_tournament_blind_structure_generation(self, game_service):
        """Test generating a blind structure for a tournament."""
        game = game_service.create_game(
            game_type=GameType.TOURNAMENT,
            name="Blind Structure Test",
            tier="Regional",
            stage="Beginning",
            starting_chips=10000,
            starting_big_blind=100,
            starting_small_blind=50,
            ante_enabled=True,
            ante_start_level=3,
        )

        # Generate blind structure
        game = game_service.generate_tournament_blind_structure(game.id)

        # Verify structure was created
        assert game.tournament_info.blind_structure is not None
        assert len(game.tournament_info.blind_structure) > 0

        # Verify first level matches starting blinds
        level1 = game.tournament_info.blind_structure[0]
        assert level1.level == 1
        assert level1.small_blind == 50
        assert level1.big_blind == 100
        assert level1.ante == 0  # No ante at level 1

        # Verify level 3 has antes
        level3 = game.tournament_info.blind_structure[2]
        assert level3.level == 3
        assert level3.ante > 0

    def test_tournament_blind_progression(self, game_service):
        """Test advancing tournament levels and blind increases."""
        game = game_service.create_game(
            game_type=GameType.TOURNAMENT,
            name="Blind Progression Test",
            tier="Local",
            stage="Beginning",
            starting_chips=10000,
            starting_big_blind=100,
            starting_small_blind=50,
            ante_enabled=True,
            ante_start_level=3,
        )

        # Add players
        _, player1 = game_service.add_player(
            game_id=game.id, name="Player 1", is_human=True
        )
        _, player2 = game_service.add_player(
            game_id=game.id, name="Player 2", is_human=False, archetype="TAG"
        )

        # Start the game (use synchronous version for tests)
        game = game_service.start_game_sync(game.id)

        # Verify initial blind values
        assert game.current_hand.small_blind == 50
        assert game.current_hand.big_blind == 100
        assert game.current_hand.ante == 0

        # Advance to level 2
        game = game_service.advance_tournament_level(game.id)

        # Verify level was updated
        assert game.tournament_info.current_level == 2

        # The current hand still has old blinds, but tournament info has new values
        assert game.tournament_info.current_small_blind > 50
        assert game.tournament_info.current_big_blind > 100
        assert game.tournament_info.current_ante == 0  # Still no ante at level 2

        # Advance to level 3 (ante should start)
        game = game_service.advance_tournament_level(game.id)

        # Verify ante is now set in tournament info
        assert game.tournament_info.current_level == 3
        assert game.tournament_info.current_ante > 0

    def test_tournament_blind_structure_calculation(self, game_service):
        """Test blind calculation formulas and rounding."""
        # Test the internal blind calculation method
        starting_blind = 100

        # Level 1 should be the starting blind
        level1_blind = game_service._calculate_blind_for_level(starting_blind, 1)
        assert level1_blind == starting_blind

        # Level 2 should be ~1.5x the starting blind
        level2_blind = game_service._calculate_blind_for_level(starting_blind, 2)
        assert 145 <= level2_blind <= 155  # Allowing for rounding

        # Level 5 should be significantly higher
        level5_blind = game_service._calculate_blind_for_level(starting_blind, 5)
        assert level5_blind > 300  # At least 3x the starting blind

        # Test the rounding to nice numbers
        assert game_service._round_to_nice_blind(13) == 15
        assert game_service._round_to_nice_blind(98) == 100
        assert game_service._round_to_nice_blind(490) == 500
        assert game_service._round_to_nice_blind(1200) == 1200
        assert game_service._round_to_nice_blind(9200) == 9200
        assert (
            game_service._round_to_nice_blind(12200) == 12000
        )  # For values > 10K, rounds to nearest 500

    def test_ante_calculation_in_tournament(self, game_service):
        """Test ante calculation for different tournament levels."""
        # Create a tournament with standard ante settings
        game = game_service.create_game(
            game_type=GameType.TOURNAMENT,
            name="Ante Test",
            tier="National",
            stage="Beginning",
            starting_chips=10000,
            starting_big_blind=100,
            starting_small_blind=50,
            ante_enabled=True,
            ante_start_level=3,
        )

        # Generate blind structure
        game = game_service.generate_tournament_blind_structure(game.id)

        # Add players and start the game
        game_service.add_player(game_id=game.id, name="Player 1", is_human=True)
        game_service.add_player(game_id=game.id, name="Player 2", is_human=False)
        game = game_service.start_game(game.id)

        # Verify initial values
        assert game.current_hand.ante == 0  # No ante at level 1

        # Check level 1-2 (no antes)
        assert game.tournament_info.blind_structure[0].ante == 0
        assert game.tournament_info.blind_structure[1].ante == 0

        # Check level 3+ (with antes)
        for i in range(2, len(game.tournament_info.blind_structure)):
            level = game.tournament_info.blind_structure[i]
            assert level.ante > 0

            # Antes should be around 25% of the big blind
            bb = level.big_blind
            expected_ante = bb // 4
            assert (
                abs(level.ante - expected_ante) <= bb // 10
            )  # Allow some deviation due to rounding

    def test_domain_model_and_poker_game_sync(self, game_service):
        """Test synchronization between domain model and PokerGame instance."""
        # Create a game
        game = game_service.create_game(
            game_type=GameType.CASH, name="Sync Test", min_bet=10
        )

        # Add players
        _, player1 = game_service.add_player(
            game_id=game.id, name="Player 1", is_human=True
        )
        _, player2 = game_service.add_player(
            game_id=game.id, name="Player 2", is_human=True
        )

        # Start the game (creates PokerGame instance)
        started_game = game_service.start_game(game.id)

        # Verify PokerGame instance is created
        poker_game = game_service.poker_games.get(game.id)
        assert poker_game is not None

        # Verify players are synced
        assert len(poker_game.players) == 2
        assert poker_game.players[0].player_id == started_game.players[0].id
        assert poker_game.players[0].name == started_game.players[0].name

        # Process an action
        updated_game = game_service.process_action(
            game_id=game.id, player_id=player1.id, action=PlayerAction.CALL
        )

        # Verify action is reflected in both domain model and PokerGame
        assert len(updated_game.current_hand.actions) > 0

        # Process another action that changes the betting round
        updated_game = game_service.process_action(
            game_id=game.id, player_id=player2.id, action=PlayerAction.CALL
        )

        # If this moved to FLOP, community cards should be dealt in PokerGame
        if poker_game.current_round == BettingRound.FLOP:
            assert len(poker_game.community_cards) == 3  # 3 flop cards

    def test_hand_history_recording(self, game_service):
        """Test that hand history is properly recorded during gameplay."""
        # Create and start a game
        game = game_service.create_game(game_type=GameType.CASH, name="History Test")

        # Add players
        _, player1 = game_service.add_player(
            game_id=game.id, name="Player 1", is_human=True
        )
        _, player2 = game_service.add_player(
            game_id=game.id, name="Player 2", is_human=True
        )

        # Start the game (use synchronous version for tests)
        started_game = game_service.start_game_sync(game.id)

        # Process some actions to complete a hand
        game_service.process_action(
            game_id=game.id, player_id=player1.id, action=PlayerAction.CALL
        )

        game_service.process_action(
            game_id=game.id, player_id=player2.id, action=PlayerAction.CHECK
        )

        # Get the hand histories for the game
        histories = game_service.get_game_hand_histories(game.id)

        # Basic assertions to verify hand history is being recorded
        assert len(histories) >= 1

        # Detailed checks on the first history
        history = histories[0]
        assert history.game_id == game.id
        assert history.hand_number == 1
        assert len(history.players) >= 2
        assert history.timestamp_start is not None
