"""
Tests for cash game mechanics in the poker game.
"""
import pytest
from app.core.poker_game import PokerGame, PlayerAction, Player, PlayerStatus, BettingRound
from app.models.domain_models import BettingStructure

class TestCashGameMechanics:
    """Test class for cash game specific mechanics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a poker game with default settings
        self.poker_game = PokerGame(
            small_blind=5,
            big_blind=10,
            ante=0,
            game_id="test_game",
            betting_structure="no_limit",
            rake_percentage=0.05,
            rake_cap=5
        )
        
        # Add three players
        self.player1 = self.poker_game.add_player("player1", "Player 1", 1000)
        self.player2 = self.poker_game.add_player("player2", "Player 2", 1000)
        self.player3 = self.poker_game.add_player("player3", "Player 3", 1000)
        
        # Start a hand
        self.poker_game.start_hand()
        
    def test_add_player_mid_game(self):
        """Test adding a player during an active game."""
        # Add a new player mid-game
        player4 = self.poker_game.add_player_mid_game("player4", "Player 4", 1000)
        
        # Verify player was added
        assert len(self.poker_game.players) == 4
        assert player4.player_id == "player4"
        assert player4.name == "Player 4"
        assert player4.chips == 1000
        
        # Verify player status is OUT (waiting for next hand)
        assert player4.status == PlayerStatus.OUT
        
    def test_remove_player(self):
        """Test removing a player (cash out)."""
        # Initial chip count
        assert len(self.poker_game.players) == 3
        
        # Remove a player
        chips = self.poker_game.remove_player("player2")
        
        # Verify player was removed
        assert len(self.poker_game.players) == 2
        assert chips == 995  # Player2 posted big blind (10 - 5 = 5 less than 1000)
        
        # Verify remaining players
        player_ids = [p.player_id for p in self.poker_game.players]
        assert "player1" in player_ids
        assert "player2" not in player_ids
        assert "player3" in player_ids
        
    def test_rake_calculation(self):
        """Test rake calculation for different pot sizes."""
        # Small pot (below threshold)
        small_pot = 50
        rake = self.poker_game.calculate_rake(small_pot)
        assert rake == 0  # No rake for very small pots
        
        # Medium pot
        medium_pot = 200
        rake = self.poker_game.calculate_rake(medium_pot)
        assert rake == 10  # 5% of 200 = 10
        
        # Large pot (above cap)
        large_pot = 2000
        rake = self.poker_game.calculate_rake(large_pot)
        assert rake == 50  # Capped at 5 big blinds (5 * 10 = 50)
        
    def test_collect_rake(self):
        """Test rake collection from pots."""
        # Medium pot
        medium_pot = 200
        adjusted_pot, rake = self.poker_game.collect_rake(medium_pot)
        assert rake == 10
        assert adjusted_pot == 190  # Original pot minus rake
        
        # Large pot
        large_pot = 2000
        adjusted_pot, rake = self.poker_game.collect_rake(large_pot)
        assert rake == 50  # Capped at 5 big blinds
        assert adjusted_pot == 1950  # Original pot minus rake
        
    def test_no_limit_betting(self):
        """Test no-limit betting validation."""
        # Set up no-limit game
        no_limit_game = PokerGame(
            small_blind=5,
            big_blind=10,
            ante=0,
            betting_structure="no_limit"
        )
        player = Player("player1", "Player 1", 1000, 0)
        
        # Minimum bet (1 BB)
        assert no_limit_game.validate_bet_for_betting_structure(PlayerAction.BET, 10, player) is True
        
        # Large bet is allowed in no-limit
        assert no_limit_game.validate_bet_for_betting_structure(PlayerAction.BET, 1000, player) is True
        
        # Below minimum bet
        assert no_limit_game.validate_bet_for_betting_structure(PlayerAction.BET, 5, player) is False
        
    def test_pot_limit_betting(self):
        """Test pot-limit betting maximum enforced."""
        # Set up pot-limit game
        pot_limit_game = PokerGame(
            small_blind=5,
            big_blind=10,
            ante=0,
            betting_structure="pot_limit"
        )
        player = Player("player1", "Player 1", 1000, 0)
        
        # Set current pot size
        pot_limit_game.pots[0].amount = 100
        
        # Valid bet within pot limits
        assert pot_limit_game.validate_bet_for_betting_structure(PlayerAction.BET, 100, player) is True
        
        # Bet larger than pot is not allowed
        assert pot_limit_game.validate_bet_for_betting_structure(PlayerAction.BET, 101, player) is False
        
        # Raising
        pot_limit_game.current_bet = 50
        # For raise, player can bet up to: call amount + (pot + current bet)
        # Call amount = 50, pot = 100, current bet = 50
        # so max raise = 50 + (100 + 50) = 200
        player.current_bet = 0  # Player hasn't bet yet
        
        # Testing valid raise (at max allowed)
        assert pot_limit_game.validate_bet_for_betting_structure(PlayerAction.RAISE, 200, player) is True
        
        # Testing invalid raise (exceeds max allowed)
        assert pot_limit_game.validate_bet_for_betting_structure(PlayerAction.RAISE, 201, player) is False
        
    def test_fixed_limit_betting(self):
        """Test fixed-limit betting sizes enforced."""
        # Set up fixed-limit game
        fixed_limit_game = PokerGame(
            small_blind=5,
            big_blind=10,
            ante=0,
            betting_structure="fixed_limit"
        )
        player = Player("player1", "Player 1", 1000, 0)
        
        # Preflop/flop betting = 1 BB
        fixed_limit_game.current_round = BettingRound.PREFLOP
        assert fixed_limit_game.validate_bet_for_betting_structure(PlayerAction.BET, 10, player) is True
        assert fixed_limit_game.validate_bet_for_betting_structure(PlayerAction.BET, 20, player) is False
        
        fixed_limit_game.current_round = BettingRound.FLOP
        assert fixed_limit_game.validate_bet_for_betting_structure(PlayerAction.BET, 10, player) is True
        assert fixed_limit_game.validate_bet_for_betting_structure(PlayerAction.BET, 20, player) is False
        
        # Turn/river betting = 2 BB
        fixed_limit_game.current_round = BettingRound.TURN
        assert fixed_limit_game.validate_bet_for_betting_structure(PlayerAction.BET, 20, player) is True
        assert fixed_limit_game.validate_bet_for_betting_structure(PlayerAction.BET, 10, player) is False
        
        fixed_limit_game.current_round = BettingRound.RIVER
        assert fixed_limit_game.validate_bet_for_betting_structure(PlayerAction.BET, 20, player) is True
        assert fixed_limit_game.validate_bet_for_betting_structure(PlayerAction.BET, 10, player) is False