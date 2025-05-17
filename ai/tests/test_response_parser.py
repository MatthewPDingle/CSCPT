"""
Tests for agent response parser.
"""

import unittest
from ai.agents.response_parser import AgentResponseParser

class ResponseParserTests(unittest.TestCase):
    """Test cases for the agent response parser."""
    
    def test_valid_fold_response(self):
        """Test parsing a valid fold response."""
        response = {
            "thinking": "I have a weak hand and facing a large bet.",
            "action": "fold",
            "amount": None,
            "reasoning": {
                "hand_assessment": "Weak hand with no draws",
                "positional_considerations": "Out of position",
                "opponent_reads": "Opponent rarely bluffs",
                "archetype_alignment": "Folding weak hands is TAG strategy"
            }
        }
        
        action, amount, metadata = AgentResponseParser.parse_response(response)
        
        self.assertEqual(action, "fold")
        self.assertIsNone(amount)
        self.assertEqual(metadata["reasoning"]["hand_assessment"], "Weak hand with no draws")
        
    def test_valid_raise_response(self):
        """Test parsing a valid raise response."""
        response = {
            "thinking": "I have a strong hand and want to build the pot.",
            "action": "raise",
            "amount": 100,
            "reasoning": {
                "hand_assessment": "Top pair top kicker",
                "positional_considerations": "In position",
                "opponent_reads": "Opponent is calling station",
                "archetype_alignment": "Raising for value is TAG strategy"
            }
        }
        
        action, amount, metadata = AgentResponseParser.parse_response(response)
        
        self.assertEqual(action, "raise")
        self.assertEqual(amount, 100)
        self.assertEqual(metadata["reasoning"]["hand_assessment"], "Top pair top kicker")
    
    def test_invalid_action(self):
        """Test handling an invalid action."""
        response = {
            "thinking": "I want to limp in.",
            "action": "limp",  # Invalid action
            "amount": 10,
            "reasoning": {
                "hand_assessment": "Speculative hand",
                "positional_considerations": "Early position",
                "opponent_reads": "Tight table",
                "archetype_alignment": "Playing carefully"
            }
        }
        
        # Should gracefully fallback to check without raising an exception
        action, amount, metadata = AgentResponseParser.parse_response(response)

        self.assertEqual(action, "check")
        self.assertIsNone(amount)
    
    def test_missing_amount_for_raise(self):
        """Test raising an exception when amount is missing for a raise."""
        response = {
            "thinking": "I have a strong hand and want to build the pot.",
            "action": "raise",
            "amount": None,  # Missing required amount
            "reasoning": {
                "hand_assessment": "Top pair top kicker",
                "positional_considerations": "In position",
                "opponent_reads": "Opponent is calling station",
                "archetype_alignment": "Raising for value is TAG strategy"
            }
        }
        
        # Should fallback to a call when no amount is provided
        action, amount, _ = AgentResponseParser.parse_response(response)

        self.assertEqual(action, "call")
        self.assertIsNone(amount)
    
    def test_negative_amount(self):
        """Test raising an exception when amount is negative."""
        response = {
            "thinking": "I have a strong hand and want to build the pot.",
            "action": "raise",
            "amount": -50,  # Negative amount
            "reasoning": {
                "hand_assessment": "Top pair top kicker",
                "positional_considerations": "In position",
                "opponent_reads": "Opponent is calling station",
                "archetype_alignment": "Raising for value is TAG strategy"
            }
        }
        
        # Should fallback to a call when amount is invalid
        action, amount, _ = AgentResponseParser.parse_response(response)

        self.assertEqual(action, "call")
        self.assertIsNone(amount)
    
    def test_is_valid_response(self):
        """Test the is_valid_response method."""
        valid_response = {
            "thinking": "I have a weak hand.",
            "action": "fold",
            "amount": None,
            "reasoning": {
                "hand_assessment": "Weak hand",
                "positional_considerations": "Out of position",
                "opponent_reads": "Opponent rarely bluffs",
                "archetype_alignment": "Folding weak hands is TAG strategy"
            }
        }
        
        invalid_response = {
            "thinking": "I have a strong hand.",
            "action": "raise",
            # Missing amount
            "reasoning": {
                "hand_assessment": "Strong hand",
                "positional_considerations": "In position",
                "opponent_reads": "Opponent is calling station",
                "archetype_alignment": "Raising for value is TAG strategy"
            }
        }
        
        self.assertTrue(AgentResponseParser.is_valid_response(valid_response))
        # Parser no longer raises for missing amounts so this should be valid
        self.assertTrue(AgentResponseParser.is_valid_response(invalid_response))
    
    def test_apply_game_rules(self):
        """Test applying game rules to adjust actions and amounts."""
        # Test all-in adjustment
        game_state = {
            "players": [{"chips": 75}],
            "current_player_idx": 0,
            "current_bet": 0,
        }

        action, amount = AgentResponseParser.apply_game_rules("raise", 100, game_state)
        
        self.assertEqual(action, "all-in")
        self.assertEqual(amount, 75)

if __name__ == "__main__":
    unittest.main()