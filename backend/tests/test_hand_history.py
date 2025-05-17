# mypy: ignore-errors
"""
Tests for the hand history tracking functionality.
"""

import unittest
import json
from datetime import datetime


# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


from app.core.poker_game import PokerGame, PlayerAction, PlayerStatus
from app.services.hand_history_service import HandHistoryRecorder
from app.repositories.in_memory import HandHistoryRepository, RepositoryFactory
from app.models.domain_models import (
    HandHistory,
    PotResult,
    ActionDetail,
    PlayerHandSnapshot,
    HandMetrics,
)


class TestHandHistory(unittest.TestCase):
    """Tests for hand history tracking."""

    def setUp(self):
        """Set up the test environment."""
        self.repo_factory = RepositoryFactory.get_instance()
        self.recorder = HandHistoryRecorder(self.repo_factory)
        self.hand_history_repo = self.repo_factory.get_repository(HandHistoryRepository)

        # Create a game for testing
        self.game = PokerGame(
            small_blind=10,
            big_blind=20,
            ante=5,
            game_id="test_game_id",
            hand_history_recorder=self.recorder,
        )

        # Add some players
        self.player1 = self.game.add_player("player1", "Player 1", 1000)
        self.player2 = self.game.add_player("player2", "Player 2", 1000)
        self.player3 = self.game.add_player("player3", "Player 3", 1000)

        # Start hand
        self.game.start_hand()

    def test_hand_history_creation(self):
        """Test that hand history is created when starting a hand."""
        # Check that the hand ID is set
        self.assertIsNotNone(self.game.current_hand_id)

        # Get hand history from repo
        hand_history = self.hand_history_repo.get(self.game.current_hand_id)

        # Verify basic details
        self.assertIsNotNone(hand_history)
        self.assertEqual(hand_history.game_id, "test_game_id")
        self.assertEqual(hand_history.hand_number, 1)
        self.assertEqual(hand_history.small_blind, 10)
        self.assertEqual(hand_history.big_blind, 20)
        self.assertEqual(hand_history.ante, 5)
        self.assertEqual(len(hand_history.players), 3)

        # Check that players were recorded
        player_ids = [p.player_id for p in hand_history.players]
        self.assertIn("player1", player_ids)
        self.assertIn("player2", player_ids)
        self.assertIn("player3", player_ids)

        # Check betting rounds were initialized
        self.assertIn("PREFLOP", hand_history.betting_rounds)
        self.assertIn("FLOP", hand_history.betting_rounds)
        self.assertIn("TURN", hand_history.betting_rounds)
        self.assertIn("RIVER", hand_history.betting_rounds)

        # Check player initial stack values were recorded
        player1 = next(p for p in hand_history.players if p.player_id == "player1")
        self.assertEqual(player1.stack_start, 1000)

        # Check positions were recorded properly
        dealer = next(p for p in hand_history.players if p.is_dealer)
        sb = next(p for p in hand_history.players if p.is_small_blind)
        bb = next(p for p in hand_history.players if p.is_big_blind)

        self.assertIsNotNone(dealer)
        self.assertIsNotNone(sb)
        self.assertIsNotNone(bb)
        self.assertNotEqual(dealer.player_id, sb.player_id)
        self.assertNotEqual(dealer.player_id, bb.player_id)
        self.assertNotEqual(sb.player_id, bb.player_id)

    def test_action_recording(self):
        """Test that player actions are recorded in the hand history."""
        # Play some actions
        self.game.process_action(self.player1, PlayerAction.FOLD)
        self.game.process_action(self.player2, PlayerAction.RAISE, 60)
        self.game.process_action(self.player3, PlayerAction.CALL, 60)

        # Get hand history from repo
        hand_history = self.hand_history_repo.get(self.game.current_hand_id)

        # Verify actions were recorded
        preflop_actions = hand_history.betting_rounds["PREFLOP"]
        self.assertEqual(len(preflop_actions), 3)

        # Check first action (FOLD)
        self.assertEqual(preflop_actions[0].player_id, "player1")
        self.assertEqual(preflop_actions[0].action_type, "fold")

        # Check second action (RAISE)
        self.assertEqual(preflop_actions[1].player_id, "player2")
        self.assertEqual(preflop_actions[1].action_type, "raise")
        self.assertEqual(preflop_actions[1].amount, 60)

        # Check third action (CALL)
        self.assertEqual(preflop_actions[2].player_id, "player3")
        self.assertEqual(preflop_actions[2].action_type, "call")
        self.assertEqual(preflop_actions[2].amount, 60)

        # Verify VPIP and PFR were tracked
        player1 = next(p for p in hand_history.players if p.player_id == "player1")
        player2 = next(p for p in hand_history.players if p.player_id == "player2")
        player3 = next(p for p in hand_history.players if p.player_id == "player3")

        self.assertFalse(player1.vpip)  # Folded, no money in pot
        self.assertTrue(player2.vpip)  # Raised
        self.assertTrue(player2.pfr)  # Raised preflop
        self.assertTrue(player3.vpip)  # Called
        self.assertFalse(player3.pfr)  # Didn't raise

        # Verify pot size changes were recorded
        self.assertTrue(preflop_actions[1].pot_before < preflop_actions[1].pot_after)
        self.assertTrue(preflop_actions[2].pot_before < preflop_actions[2].pot_after)

        # Verify bet size changes were recorded
        self.assertTrue(preflop_actions[1].amount > 0)
        self.assertTrue(preflop_actions[2].amount > 0)

    def test_complete_hand(self):
        """Test a complete hand with showdown and winners."""
        # Create a new game
        self.hand_history_repo.data.clear()  # Clear repository
        game = PokerGame(
            small_blind=10,
            big_blind=20,
            ante=5,
            game_id="test_game_id",
            hand_history_recorder=self.recorder,
        )

        # Add players
        player1 = game.add_player("player1", "Player 1", 1000)
        player2 = game.add_player("player2", "Player 2", 1000)

        # Start hand
        game.start_hand()
        hand_id = game.current_hand_id

        # Record the hand history ID
        hand_id = game.current_hand_id

        # Basic actions - player1 folds, player2 wins
        game.process_action(player1, PlayerAction.FOLD)

        # Hand should be over
        self.assertEqual(game.current_round.name, "SHOWDOWN")

        # Get hand history
        hand_history = self.hand_history_repo.get(hand_id)

        # Verify hand exists
        self.assertIsNotNone(hand_history)

        # Verify hand was completed
        self.assertIsNotNone(hand_history.timestamp_end)

        # Check preflop actions were recorded
        self.assertEqual(len(hand_history.betting_rounds["PREFLOP"]), 1)

        # Check pot results exist
        self.assertTrue(len(hand_history.pot_results) > 0)

        # Verify player2 won
        player2_snapshot = next(
            p for p in hand_history.players if p.player_id == "player2"
        )
        self.assertTrue(player2_snapshot.won_amount > 0)

    def test_early_hand_ending(self):
        """Test a hand that ends early when everyone folds to one player."""
        # Create a fresh game for this test
        self.hand_history_repo.data.clear()
        game = PokerGame(
            small_blind=10,
            big_blind=20,
            ante=5,
            game_id="test_game_id",
            hand_history_recorder=self.recorder,
        )

        # Add 3 players
        player1 = game.add_player("player1", "Player 1", 1000)
        player2 = game.add_player("player2", "Player 2", 1000)
        player3 = game.add_player("player3", "Player 3", 1000)

        # Start hand
        game.start_hand()
        hand_id = game.current_hand_id

        # Everyone folds except player3
        game.process_action(player1, PlayerAction.FOLD)
        game.process_action(player2, PlayerAction.FOLD)

        # Hand should be over
        self.assertEqual(game.current_round.name, "SHOWDOWN")

        # Get the hand history
        hand_history = self.hand_history_repo.get(hand_id)

        # Verify hand exists
        self.assertIsNotNone(hand_history)

        # Check that only preflop actions were recorded
        self.assertEqual(len(hand_history.betting_rounds["PREFLOP"]), 2)
        self.assertEqual(len(hand_history.betting_rounds["FLOP"]), 0)

        # Check pot results - should have at least one pot
        self.assertGreater(len(hand_history.pot_results), 0)

        # Check that the pot contains ante + blinds
        total_pot = sum(pot.amount for pot in hand_history.pot_results)
        expected_pot = 3 * 5 + 10 + 20  # 3 players x ante + SB + BB
        self.assertEqual(total_pot, expected_pot)

        # Verify player3 won without showdown
        player3_snapshot = next(
            (p for p in hand_history.players if p.player_id == "player3"), None
        )
        self.assertIsNotNone(player3_snapshot)
        self.assertGreater(player3_snapshot.won_amount, 0)

        # End time should be set
        self.assertIsNotNone(hand_history.timestamp_end)

        # Metrics should show this wasn't a showdown
        self.assertFalse(hand_history.metrics.showdown_reached)

    def test_all_in_confrontation(self):
        """Test a hand with all-in actions."""
        # Create a fresh game
        self.hand_history_repo.data.clear()  # Clear repository
        game = PokerGame(
            small_blind=10,
            big_blind=20,
            ante=5,
            game_id="test_game_id",
            hand_history_recorder=self.recorder,
        )

        # Add players
        player1 = game.add_player("player1", "Player 1", 1000)
        player2 = game.add_player("player2", "Player 2", 1000)
        player3 = game.add_player("player3", "Player 3", 100)  # Less chips

        # Start hand
        game.start_hand()
        hand_id = game.current_hand_id

        # Player1 raises, player2 reraises, player3 all-in, player1 calls
        game.process_action(player1, PlayerAction.RAISE, 60)
        game.process_action(player2, PlayerAction.RAISE, 120)
        game.process_action(player3, PlayerAction.ALL_IN, 100)
        game.process_action(player1, PlayerAction.CALL, 80)

        # All players have acted, so betting round should end and we should get to showdown
        # (since player3 is all-in and there's no more betting to do)

        # Verify the round advanced to showdown
        self.assertEqual(game.current_round.name, "SHOWDOWN")

        # Get hand history after hand is complete
        hand_history = self.hand_history_repo.get(hand_id)

        # Verify hand exists
        self.assertIsNotNone(hand_history)

        # Check that the all-in flag was recorded
        preflop_actions = hand_history.betting_rounds["PREFLOP"]
        all_in_action = next(
            (a for a in preflop_actions if a.player_id == "player3"), None
        )
        self.assertIsNotNone(all_in_action)
        self.assertTrue(all_in_action.all_in)

        # Metrics should show this was an all-in confrontation
        self.assertTrue(hand_history.metrics.all_in_confrontation)

        # Check side pots were created - we should have at least a main pot and a side pot
        self.assertGreaterEqual(len(hand_history.pot_results), 2)

        # Verify total pot matches expected contributions
        expected_pot = (
            (3 * 5) + 10 + 20 + 40 + 100 + 80
        )  # ante + SB + BB + initial raise + all-in + call
        total_pot = sum(pot.amount for pot in hand_history.pot_results)
        self.assertEqual(total_pot, expected_pot)

        # Check player3's eligibility is limited to the main pot
        pots_by_size = sorted(
            hand_history.pot_results, key=lambda p: p.amount, reverse=True
        )
        if len(pots_by_size) >= 2:
            main_pot = pots_by_size[1]  # Main pot is usually smaller than side pot
            side_pot = pots_by_size[0]  # Side pot is usually larger

            # Either player3 should be in main pot but not side pot,
            # or the pot names should indicate main pot and side pot
            if "player3" in main_pot.eligible_players:
                self.assertNotIn("player3", side_pot.eligible_players)
            else:
                # Check by pot names
                main_pot = next(
                    (p for p in hand_history.pot_results if "Main" in p.pot_name), None
                )
                if main_pot:
                    self.assertIn("player3", main_pot.eligible_players)

    def test_player_stats_after_simple_hand(self):
        """Test player statistics calculation after a simple hand."""
        # Create a new game
        self.hand_history_repo.data.clear()  # Clear repository
        game = PokerGame(
            small_blind=10,
            big_blind=20,
            ante=5,
            game_id="test_game_id",
            hand_history_recorder=self.recorder,
        )

        # Add players
        player1 = game.add_player("player1", "Player 1", 1000)
        player2 = game.add_player("player2", "Player 2", 1000)

        # Start hand
        game.start_hand()
        hand_id = game.current_hand_id

        # Simple hand - player1 folds, player2 wins
        game.process_action(player1, PlayerAction.FOLD)

        # Get player stats
        stats1 = self.hand_history_repo.get_player_stats("player1")
        stats2 = self.hand_history_repo.get_player_stats("player2")

        # Check basic stats for all players
        self.assertEqual(stats1.hands_played, 1)
        self.assertEqual(stats2.hands_played, 1)

        # Check VPIP and PFR
        self.assertEqual(stats1.vpip, 0.0)  # Didn't put money voluntarily
        self.assertEqual(stats1.pfr, 0.0)  # Didn't raise preflop
        self.assertEqual(stats2.vpip, 0.0)  # Wasn't voluntary (blinds)
        self.assertEqual(stats2.pfr, 0.0)  # Didn't raise preflop

        # Player 2 won
        self.assertTrue(stats2.biggest_win > 0)
        self.assertEqual(stats2.biggest_loss, 0)

    def test_serialization(self):
        """Test that hand histories can be serialized and deserialized."""
        # Create a new game
        self.hand_history_repo.data.clear()  # Clear repository
        game = PokerGame(
            small_blind=10,
            big_blind=20,
            ante=5,
            game_id="test_game_id",
            hand_history_recorder=self.recorder,
        )

        # Add players
        player1 = game.add_player("player1", "Player 1", 1000)
        player2 = game.add_player("player2", "Player 2", 1000)

        # Start hand
        game.start_hand()
        hand_id = game.current_hand_id

        # Simple hand - player1 folds
        game.process_action(player1, PlayerAction.FOLD)

        # Get hand history
        hand_history = self.hand_history_repo.get(hand_id)

        # Verify hand exists
        self.assertIsNotNone(hand_history)

        # Serialize to dict/JSON
        # Note: Using model_dump() is recommended for Pydantic v2+, but for compatibility with both v1 and v2:
        try:
            hand_dict = hand_history.model_dump()
        except AttributeError:
            hand_dict = hand_history.dict()

        hand_json = json.dumps(hand_dict, cls=DateTimeEncoder)

        # Verify it can be deserialized
        hand_dict2 = json.loads(hand_json)
        # Use model_validate for Pydantic v2 compatibility
        try:
            hand_history2 = HandHistory.model_validate(hand_dict2)
        except AttributeError:
            # Fallback for Pydantic v1
            hand_history2 = HandHistory.parse_obj(hand_dict2)

        # Check key fields were preserved
        self.assertEqual(hand_history.id, hand_history2.id)
        self.assertEqual(hand_history.game_id, hand_history2.game_id)
        self.assertEqual(len(hand_history.players), len(hand_history2.players))

        # Check betting rounds were preserved
        for round_name in ["PREFLOP", "FLOP", "TURN", "RIVER"]:
            self.assertEqual(
                len(hand_history.betting_rounds.get(round_name, [])),
                len(hand_history2.betting_rounds.get(round_name, [])),
            )

        # Check that player info is preserved
        original_player = hand_history.players[0]
        deserialized_player = hand_history2.players[0]
        self.assertEqual(original_player.player_id, deserialized_player.player_id)
        self.assertEqual(original_player.name, deserialized_player.name)

    def test_game_with_multiple_hands(self):
        """Test that multiple hands in a game are tracked correctly."""
        # Create a new game
        self.hand_history_repo.data.clear()  # Clear repository
        game = PokerGame(
            small_blind=10,
            big_blind=20,
            ante=5,
            game_id="test_game_id",
            hand_history_recorder=self.recorder,
        )

        # Add players
        player1 = game.add_player("player1", "Player 1", 1000)
        player2 = game.add_player("player2", "Player 2", 1000)

        # Start first hand
        game.start_hand()
        first_hand_id = game.current_hand_id

        # Simple hand - player1 folds
        game.process_action(player1, PlayerAction.FOLD)

        # Start second hand
        game.move_button()
        game.start_hand()
        second_hand_id = game.current_hand_id

        # Make sure we got a new hand ID
        self.assertNotEqual(first_hand_id, second_hand_id)

        # Play second hand - player2 folds
        game.process_action(player2, PlayerAction.FOLD)

        # Get hands by game
        game_hands = self.hand_history_repo.get_by_game("test_game_id")

        # Should have both hands
        self.assertEqual(len(game_hands), 2)

        # Check hand numbers
        hands_by_number = sorted(game_hands, key=lambda h: h.hand_number)
        self.assertEqual(hands_by_number[0].hand_number, 1)
        self.assertEqual(hands_by_number[1].hand_number, 2)

        # Check that hands have different dealer positions
        self.assertNotEqual(
            hands_by_number[0].dealer_position, hands_by_number[1].dealer_position
        )


if __name__ == "__main__":
    unittest.main()
