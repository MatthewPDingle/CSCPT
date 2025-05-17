# mypy: ignore-errors
"""
Unit tests for the domain models.
"""

import pytest
import uuid
from datetime import datetime

from app.models.domain_models import (
    Game,
    Player,
    Hand,
    ActionHistory,
    User,
    GameType,
    GameStatus,
    PlayerStatus,
    PlayerAction,
    BettingRound,
    TournamentInfo,
    CashGameInfo,
    ArchetypeEnum,
    TournamentStage,
    TournamentTier,
    BettingStructure,
)


class TestDomainModels:
    """Tests for the domain models."""

    def test_user_model(self):
        """Test User model creation and defaults."""
        # Test with minimal fields
        user = User(username="testuser")
        assert user.id is not None
        assert user.username == "testuser"
        assert isinstance(user.preferences, dict)
        assert user.preferences == {}
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

        # Test with all fields
        user_id = str(uuid.uuid4())
        created_at = datetime.now()
        updated_at = datetime.now()
        preferences = {"theme": "dark", "notifications": True}

        user = User(
            id=user_id,
            username="testuser",
            preferences=preferences,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert user.id == user_id
        assert user.username == "testuser"
        assert user.preferences == preferences
        assert user.created_at == created_at
        assert user.updated_at == updated_at

    def test_player_model(self):
        """Test Player model creation and defaults."""
        # Test with minimal fields
        player = Player(name="Test Player", position=0)
        assert player.id is not None
        assert player.name == "Test Player"
        assert player.position == 0
        assert player.is_human is False
        assert player.user_id is None
        assert player.archetype is None
        assert player.chips == 0
        assert player.bet == 0
        assert isinstance(player.cards, list)
        assert player.cards == []
        assert player.status == PlayerStatus.WAITING
        assert player.has_acted is False
        assert player.is_dealer is False
        assert player.is_small_blind is False
        assert player.is_big_blind is False

        # Test with all fields
        player_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        player = Player(
            id=player_id,
            name="Test Player",
            is_human=True,
            user_id=user_id,
            archetype=ArchetypeEnum.TAG,
            position=1,
            chips=1000,
            bet=50,
            cards=["Ah", "Kd"],
            status=PlayerStatus.ACTIVE,
            has_acted=True,
            is_dealer=True,
            is_small_blind=False,
            is_big_blind=False,
        )

        assert player.id == player_id
        assert player.name == "Test Player"
        assert player.is_human is True
        assert player.user_id == user_id
        assert player.archetype == ArchetypeEnum.TAG
        assert player.position == 1
        assert player.chips == 1000
        assert player.bet == 50
        assert player.cards == ["Ah", "Kd"]
        assert player.status == PlayerStatus.ACTIVE
        assert player.has_acted is True
        assert player.is_dealer is True
        assert player.is_small_blind is False
        assert player.is_big_blind is False

    def test_hand_model(self):
        """Test Hand model creation and defaults."""
        game_id = str(uuid.uuid4())

        # Test with minimal fields
        hand = Hand(game_id=game_id, hand_number=1, small_blind=5, big_blind=10)

        assert hand.id is not None
        assert hand.game_id == game_id
        assert hand.hand_number == 1
        assert hand.small_blind == 5
        assert hand.big_blind == 10
        assert hand.ante == 0
        assert isinstance(hand.community_cards, list)
        assert hand.community_cards == []
        assert hand.main_pot == 0
        assert isinstance(hand.side_pots, list)
        assert hand.side_pots == []
        assert hand.current_round == BettingRound.PREFLOP
        assert hand.current_player_id is None
        assert hand.dealer_position == 0
        assert isinstance(hand.active_player_ids, list)
        assert hand.active_player_ids == []
        assert isinstance(hand.folded_player_ids, list)
        assert hand.folded_player_ids == []
        assert isinstance(hand.all_in_player_ids, list)
        assert hand.all_in_player_ids == []
        assert isinstance(hand.winners, list)
        assert hand.winners == []
        assert isinstance(hand.started_at, datetime)
        assert hand.ended_at is None
        assert isinstance(hand.actions, list)
        assert hand.actions == []
        assert hand.current_bet == 0

    def test_action_history_model(self):
        """Test ActionHistory model creation and defaults."""
        game_id = str(uuid.uuid4())
        hand_id = str(uuid.uuid4())
        player_id = str(uuid.uuid4())

        # Test with minimal fields
        action = ActionHistory(
            game_id=game_id,
            hand_id=hand_id,
            player_id=player_id,
            action=PlayerAction.CALL,
            round=BettingRound.PREFLOP,
        )

        assert action.id is not None
        assert action.game_id == game_id
        assert action.hand_id == hand_id
        assert action.player_id == player_id
        assert action.action == PlayerAction.CALL
        assert action.amount is None
        assert action.round == BettingRound.PREFLOP
        assert isinstance(action.timestamp, datetime)

        # Test with all fields
        action_id = str(uuid.uuid4())
        timestamp = datetime.now()

        action = ActionHistory(
            id=action_id,
            game_id=game_id,
            hand_id=hand_id,
            player_id=player_id,
            action=PlayerAction.RAISE,
            amount=100,
            round=BettingRound.FLOP,
            timestamp=timestamp,
        )

        assert action.id == action_id
        assert action.game_id == game_id
        assert action.hand_id == hand_id
        assert action.player_id == player_id
        assert action.action == PlayerAction.RAISE
        assert action.amount == 100
        assert action.round == BettingRound.FLOP
        assert action.timestamp == timestamp

    def test_tournament_info_model(self):
        """Test TournamentInfo model creation and defaults."""
        # Test with minimal fields
        tournament_info = TournamentInfo(
            tier=TournamentTier.LOCAL,
            stage=TournamentStage.BEGINNING,
            buy_in_amount=100,
            level_duration=15,
            starting_chips=50000,
            total_players=50,
            starting_big_blind=100,
            starting_small_blind=50,
            players_remaining=50,
        )

        assert tournament_info.tier == TournamentTier.LOCAL
        assert tournament_info.stage == TournamentStage.BEGINNING
        assert tournament_info.payout_structure == "Standard"
        assert tournament_info.buy_in_amount == 100
        assert tournament_info.level_duration == 15
        assert tournament_info.starting_chips == 50000
        assert tournament_info.total_players == 50
        assert tournament_info.starting_big_blind == 100
        assert tournament_info.starting_small_blind == 50
        assert tournament_info.ante_enabled is False
        assert tournament_info.ante_start_level == 3
        assert tournament_info.rebuy_option is False
        assert tournament_info.rebuy_level_cutoff == 5
        assert tournament_info.current_level == 1
        assert tournament_info.players_remaining == 50
        assert isinstance(tournament_info.archetype_distribution, dict)
        assert tournament_info.archetype_distribution == {}

    def test_cash_game_info_model(self):
        """Test CashGameInfo model creation and defaults."""
        # Test with minimal fields
        cash_game_info = CashGameInfo(
            buy_in=1000, min_buy_in=400, max_buy_in=2000, min_bet=10, table_size=6
        )

        assert cash_game_info.buy_in == 1000
        assert cash_game_info.min_buy_in == 400
        assert cash_game_info.max_buy_in == 2000
        assert cash_game_info.min_bet == 10
        assert cash_game_info.max_bet is None
        assert cash_game_info.ante == 0
        assert cash_game_info.straddled is False
        assert cash_game_info.straddle_amount == 0
        assert cash_game_info.table_size == 6
        assert cash_game_info.betting_structure == BettingStructure.NO_LIMIT
        assert cash_game_info.rake_percentage == 0.05
        assert cash_game_info.rake_cap == 5

    def test_cash_game_info_with_betting_structures(self):
        """Test CashGameInfo with different betting structures."""
        # Test No Limit
        no_limit_game = CashGameInfo(
            buy_in=1000,
            min_buy_in=400,
            max_buy_in=2000,
            min_bet=10,
            table_size=6,
            betting_structure=BettingStructure.NO_LIMIT,
        )
        assert no_limit_game.betting_structure == BettingStructure.NO_LIMIT
        assert no_limit_game.max_bet is None  # No max bet in No Limit

        # Test Pot Limit
        pot_limit_game = CashGameInfo(
            buy_in=1000,
            min_buy_in=400,
            max_buy_in=2000,
            min_bet=10,
            table_size=6,
            betting_structure=BettingStructure.POT_LIMIT,
        )
        assert pot_limit_game.betting_structure == BettingStructure.POT_LIMIT

        # Test Fixed Limit
        fixed_limit_game = CashGameInfo(
            buy_in=1000,
            min_buy_in=400,
            max_buy_in=2000,
            min_bet=10,
            max_bet=20,  # Fixed limit has a max bet
            table_size=6,
            betting_structure=BettingStructure.FIXED_LIMIT,
        )
        assert fixed_limit_game.betting_structure == BettingStructure.FIXED_LIMIT
        assert fixed_limit_game.max_bet == 20

    def test_cash_game_rake_settings(self):
        """Test rake settings in CashGameInfo."""
        # Test default rake
        default_rake_game = CashGameInfo(
            buy_in=1000, min_buy_in=400, max_buy_in=2000, min_bet=10, table_size=6
        )
        assert default_rake_game.rake_percentage == 0.05
        assert default_rake_game.rake_cap == 5

        # Test custom rake
        custom_rake_game = CashGameInfo(
            buy_in=1000,
            min_buy_in=400,
            max_buy_in=2000,
            min_bet=10,
            table_size=6,
            rake_percentage=0.03,
            rake_cap=3,
        )
        assert custom_rake_game.rake_percentage == 0.03
        assert custom_rake_game.rake_cap == 3

        # Test no rake
        no_rake_game = CashGameInfo(
            buy_in=1000,
            min_buy_in=400,
            max_buy_in=2000,
            min_bet=10,
            table_size=6,
            rake_percentage=0,
            rake_cap=0,
        )
        assert no_rake_game.rake_percentage == 0
        assert no_rake_game.rake_cap == 0

    def test_game_model(self):
        """Test Game model creation and defaults."""
        # Test with minimal fields
        game = Game(type=GameType.CASH)

        assert game.id is not None
        assert game.type == GameType.CASH
        assert game.status == GameStatus.WAITING
        assert game.name is None
        assert isinstance(game.players, list)
        assert game.players == []
        assert game.current_hand is None
        assert isinstance(game.hand_history, list)
        assert game.hand_history == []
        assert game.tournament_info is None
        assert game.cash_game_info is None
        assert isinstance(game.created_at, datetime)
        assert isinstance(game.updated_at, datetime)
        assert game.started_at is None
        assert game.ended_at is None

        # Test with tournament info
        tournament_info = TournamentInfo(
            tier=TournamentTier.LOCAL,
            stage=TournamentStage.BEGINNING,
            buy_in_amount=100,
            level_duration=15,
            starting_chips=50000,
            total_players=50,
            starting_big_blind=100,
            starting_small_blind=50,
            players_remaining=50,
        )

        game = Game(
            type=GameType.TOURNAMENT,
            name="Test Tournament",
            tournament_info=tournament_info,
        )

        assert game.type == GameType.TOURNAMENT
        assert game.name == "Test Tournament"
        assert game.tournament_info == tournament_info
        assert game.cash_game_info is None

        # Test with cash game info
        cash_game_info = CashGameInfo(
            buy_in=1000, min_buy_in=400, max_buy_in=2000, min_bet=10, table_size=6
        )

        game = Game(
            type=GameType.CASH, name="Test Cash Game", cash_game_info=cash_game_info
        )

        assert game.type == GameType.CASH
        assert game.name == "Test Cash Game"
        assert game.cash_game_info == cash_game_info
        assert game.tournament_info is None
