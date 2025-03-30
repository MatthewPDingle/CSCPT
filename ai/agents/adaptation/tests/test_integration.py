"""
Tests for the adaptation integration components.
"""

import unittest
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add the project root to the path to ensure imports work
project_root = str(Path(__file__).parents[4])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai.agents.adaptation.integration import AdaptationManager
from ai.agents.adaptation.tournament_analyzer import TournamentStage, MZone

class TestAdaptationManager(unittest.TestCase):
    """Test the AdaptationManager component."""
    
    def setUp(self):
        """Set up an AdaptationManager instance for testing."""
        self.manager = AdaptationManager()
    
    def test_update_from_game_state(self):
        """Test updating the manager from a game state."""
        # Create test game state and context
        game_state = {
            "hand_id": "test_hand_1",
            "action_history": [
                {"player_id": "1", "action": "raise", "amount": 100},
                {"player_id": "2", "action": "call", "amount": 100},
                {"player_id": "3", "action": "fold"}
            ],
            "players": [
                {"player_id": "1", "stack": 5000},
                {"player_id": "2", "stack": 3000},
                {"player_id": "3", "stack": 2000}
            ],
            "position": "BTN",
            "pot": 200
        }
        
        context = {
            "tournament": {
                "players_remaining": 20,
                "total_players": 100,
                "level": 10,
                "max_levels": 20,
                "in_the_money": False,
                "final_table": False,
                "paid_positions": 15,
                "blinds": [50, 100],
                "player_stacks": {
                    "1": 5000,
                    "2": 3000,
                    "3": 2000
                },
                "is_test": True
            }
        }
        
        # Update the manager
        self.manager.update_from_game_state(game_state, context)
        
        # Verify that updates were processed
        # These checks are basic sanity checks that don't rely on mocks
        self.assertEqual(self.manager.last_processed_hand_id, "test_hand_1")
        self.assertEqual(self.manager.game_state_tracker.hands_processed, 1)
        
        # Try updating with the same hand ID
        self.manager.update_from_game_state(game_state, context)
        
        # Verify that it wasn't processed again
        self.assertEqual(self.manager.game_state_tracker.hands_processed, 1)
    
    def test_get_adaptation_context(self):
        """Test getting the adaptation context."""
        # First update with some game state to have data
        game_state = {
            "hand_id": "test_hand_2",
            "action_history": [
                {"player_id": "1", "action": "raise", "amount": 100},
                {"player_id": "2", "action": "fold"},
                {"player_id": "3", "action": "fold"}
            ],
            "players": [
                {"player_id": "1", "stack": 5000},
                {"player_id": "2", "stack": 3000},
                {"player_id": "3", "stack": 2000}
            ],
            "position": "BTN",
            "pot": 150
        }
        
        context = {
            "tournament": {
                "players_remaining": 10,
                "total_players": 100,
                "level": 15,
                "paid_positions": 9,
                "in_the_money": False,
                "final_table": False,
                "blinds": [100, 200],
                "player_stacks": {
                    "1": 5000,
                    "2": 3000,
                    "3": 2000
                },
                "is_test": True
            }
        }
        
        self.manager.update_from_game_state(game_state, context)
        
        # Get the adaptation context
        adaptation_context = self.manager.get_adaptation_context(player_id="1")
        
        # Verify structure of the returned context
        self.assertIn("game_dynamics", adaptation_context)
        self.assertIn("recommended_adjustments", adaptation_context)
        self.assertIn("tournament", adaptation_context)
        
        # Check that tournament stage is BUBBLE (we're close to the money)
        self.assertEqual(
            adaptation_context["tournament"]["stage"], 
            TournamentStage.BUBBLE.name
        )
        
        # Check that player-specific recommendations are included
        self.assertIn("tournament_recommendations", adaptation_context)
    
    def test_get_strategic_adjustments(self):
        """Test getting strategic adjustments."""
        # First update with some game state
        game_state = {
            "hand_id": "test_hand_3",
            "action_history": [
                {"player_id": "1", "action": "check"},
                {"player_id": "2", "action": "bet", "amount": 100},
                {"player_id": "3", "action": "call", "amount": 100},
                {"player_id": "1", "action": "fold"}
            ],
            "players": [
                {"player_id": "1", "stack": 4900},
                {"player_id": "2", "stack": 3100},
                {"player_id": "3", "stack": 2000}
            ],
            "position": "SB",
            "pot": 200
        }
        
        context = {
            "tournament": {
                "players_remaining": 50,
                "total_players": 100,
                "level": 5,
                "paid_positions": 15,
                "in_the_money": False,
                "final_table": False,
                "blinds": [25, 50],
                "player_stacks": {
                    "1": 4900,
                    "2": 3100,
                    "3": 2000
                },
                "is_test": True
            }
        }
        
        self.manager.update_from_game_state(game_state, context)
        
        # Get strategic adjustments
        adjustments = self.manager.get_strategic_adjustments()
        
        # Verify structure
        self.assertIn("game_state_adjustments", adjustments)
        self.assertIn("tournament_adjustments", adjustments)
        
        # Check tournament adjustments match the early stage
        self.assertEqual(
            adjustments["tournament_adjustments"]["general_strategy"],
            "fundamentally sound poker with chip accumulation focus"
        )

if __name__ == "__main__":
    unittest.main()