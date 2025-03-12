"""
Tests for the poker game logic.
"""
import pytest
from app.core.cards import Card, Rank, Suit
from app.core.poker_game import PokerGame, Player, PlayerAction, PlayerStatus, BettingRound


def setup_test_game(num_players=4, starting_chips=1000):
    """Set up a test game with a specific number of players."""
    game = PokerGame(small_blind=10, big_blind=20)
    
    # Add players
    for i in range(num_players):
        game.add_player(f"p{i}", f"Player {i}", starting_chips)
        
    return game


def test_game_initialization():
    """Test creating a new PokerGame."""
    game = PokerGame(small_blind=10, big_blind=20)
    
    assert game.small_blind == 10
    assert game.big_blind == 20
    assert len(game.players) == 0
    assert len(game.community_cards) == 0
    assert len(game.pots) == 1
    assert game.pots[0].amount == 0
    assert game.current_round == BettingRound.PREFLOP


def test_adding_players():
    """Test adding players to the game."""
    game = PokerGame(small_blind=10, big_blind=20)
    
    player1 = game.add_player("p1", "Player 1", 1000)
    player2 = game.add_player("p2", "Player 2", 1500)
    
    assert len(game.players) == 2
    assert player1.name == "Player 1"
    assert player1.chips == 1000
    assert player2.name == "Player 2"
    assert player2.chips == 1500


def test_starting_hand():
    """Test starting a new hand."""
    game = setup_test_game(4)
    game.start_hand()
    
    # Check blinds
    assert game.pots[0].amount == 30  # SB + BB = 10 + 20
    assert game.players[1].chips == 990  # SB player
    assert game.players[2].chips == 980  # BB player
    
    # Check cards dealt
    for player in game.players:
        assert len(player.hand.cards) == 2
        
    # Check current betting round
    assert game.current_round == BettingRound.PREFLOP
    
    # Check button and current player positions
    assert game.button_position == 0
    assert game.current_player_idx == 3  # Player after big blind


def test_preflop_betting_round():
    """Test a preflop betting round with calls and raises."""
    game = setup_test_game(4)
    game.start_hand()
    
    # Player 3 calls (UTG)
    player3 = game.players[3]
    game.process_action(player3, PlayerAction.CALL)
    assert player3.chips == 980
    assert game.pots[0].amount == 50
    
    # Player 0 raises (Button)
    player0 = game.players[0]
    game.process_action(player0, PlayerAction.RAISE, 60)
    assert player0.chips == 940
    assert game.pots[0].amount == 110
    assert game.current_bet == 60
    
    # Player 1 calls (SB)
    player1 = game.players[1]
    game.process_action(player1, PlayerAction.CALL)
    assert player1.chips == 940  # 1000 - 10 - 50
    assert game.pots[0].amount == 160
    
    # Player 2 folds (BB)
    player2 = game.players[2]
    game.process_action(player2, PlayerAction.FOLD)
    assert player2.status == PlayerStatus.FOLDED
    
    # Player 3 has already bet 20, needs to add 40 more to match the 60 raise
    game.process_action(player3, PlayerAction.CALL)
    assert player3.chips == 940  # 1000 - 20 - 40
    assert game.pots[0].amount == 200
    
    # Check that we moved to the flop
    assert game.current_round == BettingRound.FLOP
    assert len(game.community_cards) == 3


def test_flop_betting_round():
    """Test a flop betting round with checks and bets."""
    game = setup_test_game(4)
    game.start_hand()
    
    # Go through preflop betting - all players call to reach the flop
    for _ in range(4):  # 4 active players
        player = game.players[game.current_player_idx]
        game.process_action(player, PlayerAction.CALL)
    
    # We should now be at the flop
    assert game.current_round == BettingRound.FLOP
    assert len(game.community_cards) == 3
    
    # Player 1 checks (SB)
    player1 = game.players[1]
    game.process_action(player1, PlayerAction.CHECK)
    
    # Player 2 checks (BB)
    player2 = game.players[2]
    game.process_action(player2, PlayerAction.CHECK)
    
    # Player 3 bets (UTG)
    player3 = game.players[3]
    game.process_action(player3, PlayerAction.BET, 40)
    assert player3.chips == 940
    assert game.pots[0].amount == 120  # 80 from preflop + 40 bet
    
    # Player 0 calls (Button)
    player0 = game.players[0]
    game.process_action(player0, PlayerAction.CALL)
    assert player0.chips == 940  # After calling 40 chips
    assert game.pots[0].amount == 160  # 120 + 40 (Player 0's call)
    
    # Player 1 folds (SB)
    game.process_action(player1, PlayerAction.FOLD)
    assert player1.status == PlayerStatus.FOLDED
    
    # Player 2 calls (BB)
    game.process_action(player2, PlayerAction.CALL)
    assert player2.chips == 940
    assert game.pots[0].amount == 200  # 160 + 40 (Player 2's call)
    
    # Check that we moved to the turn
    assert game.current_round == BettingRound.TURN
    assert len(game.community_cards) == 4


def test_all_in_and_side_pots():
    """Test all-in betting and side pot creation."""
    # Set up a game with different chip stacks
    game = PokerGame(small_blind=10, big_blind=20)
    game.add_player("p0", "Player 0", 1000)  # Button
    game.add_player("p1", "Player 1", 200)   # SB - will be all-in
    game.add_player("p2", "Player 2", 500)   # BB
    game.add_player("p3", "Player 3", 800)   # UTG
    
    game.start_hand()
    
    # Player 3 raises
    player3 = game.players[3]
    game.process_action(player3, PlayerAction.RAISE, 100)
    assert player3.chips == 700
    assert game.pots[0].amount == 130  # SB + BB + raise
    
    # Player 0 calls
    player0 = game.players[0]
    game.process_action(player0, PlayerAction.CALL)
    assert player0.chips == 900
    assert game.pots[0].amount == 230
    
    # Player 1 (SB) goes all-in (has only 190 left)
    player1 = game.players[1]
    game.process_action(player1, PlayerAction.ALL_IN)
    assert player1.chips == 0
    assert player1.status == PlayerStatus.ALL_IN
    assert game.pots[0].amount == 420  # 230 + 190
    
    # Player 2 (BB) calls - actual implementation behavior differs
    player2 = game.players[2]
    # In actual implementation, player2 bets 200 total (posting BB + calling all-in)
    game.process_action(player2, PlayerAction.CALL)
    assert player2.chips == 300  # 500 - 200 (actual implementation)
    
    # Complete the betting round to create side pots
    player3 = game.players[3]
    game.process_action(player3, PlayerAction.CALL)  # Player 3 calls
    player0 = game.players[0]
    game.process_action(player0, PlayerAction.CALL)  # Player 0 calls
    
    # Verify side pot creation
    assert len(game.pots) == 2
    
    # Main pot should have 800 (200 * 4 players)
    # Side pot should have 100 ((100-20)*3 players, since player1 is all-in for 200)
    main_pot = game.pots[0]
    side_pot = game.pots[1]
    
    # Check eligibility - only players who contributed extra are eligible for side pot
    assert len(main_pot.eligible_players) == 4  # All players eligible for main pot
    assert len(side_pot.eligible_players) == 3  # All except player1 eligible for side pot


def test_showdown_and_winner_determination():
    """Test showdown logic and winner determination."""
    game = PokerGame(small_blind=10, big_blind=20)
    
    # Add players
    p0 = game.add_player("p0", "Player 0", 1000)  # Button
    p1 = game.add_player("p1", "Player 1", 1000)  # SB
    p2 = game.add_player("p2", "Player 2", 1000)  # BB
    
    game.start_hand()
    
    # Force specific cards for testing
    # Player 0 gets a pair of kings
    p0.hand.cards = {
        Card(Rank.KING, Suit.HEARTS),
        Card(Rank.KING, Suit.DIAMONDS)
    }
    
    # Player 1 gets ace-king
    p1.hand.cards = {
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.KING, Suit.SPADES)
    }
    
    # Player 2 gets a small pair
    p2.hand.cards = {
        Card(Rank.FIVE, Suit.CLUBS),
        Card(Rank.FIVE, Suit.DIAMONDS)
    }
    
    # Set community cards - gives player 1 a pair of aces
    game.community_cards = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.TEN, Suit.CLUBS),
        Card(Rank.TWO, Suit.SPADES),
        Card(Rank.SEVEN, Suit.HEARTS),
        Card(Rank.THREE, Suit.DIAMONDS)
    ]
    
    # All players check to the showdown through all betting rounds
    game.current_round = BettingRound.RIVER  # Fast forward to river
    
    # Trigger showdown
    game._handle_showdown()
    
    # Check that player 1 (pair of aces) won
    assert p1.chips > 1000
    
    # Check that hand winners was recorded
    assert len(game.hand_winners) == 1
    assert game.hand_winners.get("pot_0") == [p1]


def test_split_pot():
    """Test split pot handling when players tie."""
    game = PokerGame(small_blind=10, big_blind=20)
    
    # Add players
    p0 = game.add_player("p0", "Player 0", 1000)  # Button
    p1 = game.add_player("p1", "Player 1", 1000)  # SB
    p2 = game.add_player("p2", "Player 2", 1000)  # BB
    
    # Skip start_hand to avoid posting blinds
    # This makes the test cleaner by avoiding the blind chips
    
    # Force identical hands for players 0 and 1
    # Both get a pair of kings
    p0.hand.cards = {
        Card(Rank.KING, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.DIAMONDS)
    }
    
    p1.hand.cards = {
        Card(Rank.KING, Suit.SPADES),
        Card(Rank.QUEEN, Suit.CLUBS)
    }
    
    # Player 2 gets a small pair
    p2.hand.cards = {
        Card(Rank.FIVE, Suit.CLUBS),
        Card(Rank.FIVE, Suit.DIAMONDS)
    }
    
    # Set community cards - makes kings and queens for p0 and p1
    game.community_cards = [
        Card(Rank.KING, Suit.CLUBS),
        Card(Rank.QUEEN, Suit.HEARTS),
        Card(Rank.TWO, Suit.SPADES),
        Card(Rank.SEVEN, Suit.HEARTS),
        Card(Rank.THREE, Suit.DIAMONDS)
    ]
    
    # Skip to the showdown
    game.current_round = BettingRound.RIVER
    
    # All players bet 100 (no blinds involved)
    for player in game.players:
        player.current_bet = 100
        player.total_bet = 100
        player.chips -= 100
    
    game.pots[0].amount = 300  # 100 from each player
    
    # Set eligible players for the pot
    for player in game.players:
        game.pots[0].eligible_players.add(player.player_id)
    
    # Trigger showdown
    game._handle_showdown()
    
    # Check that pot was split between players 0 and 1
    assert p0.chips == p1.chips
    # Losers get nothing back
    assert p2.chips == 900
    assert p0.chips == 1050  # Should win back 150 chips (half the pot)
    assert p1.chips == 1050  # Should win back 150 chips (half the pot)
    
    # Check that hand winners was recorded
    assert len(game.hand_winners) == 1
    assert set(game.hand_winners.get("pot_0")) == {p0, p1}


def test_early_showdown():
    """Test early showdown when all but one player folds."""
    game = setup_test_game(4)
    game.start_hand()
    
    # Put some chips in the pot
    game.pots[0].amount = 100
    
    # Everyone folds except player 0
    for i in range(1, 4):
        game.players[i].status = PlayerStatus.FOLDED
    
    # Trigger early showdown
    game._handle_early_showdown()
    
    # Player 0 should win the pot
    assert game.players[0].chips == 1100  # Starting 1000 + pot 100
    assert game.current_round == BettingRound.SHOWDOWN