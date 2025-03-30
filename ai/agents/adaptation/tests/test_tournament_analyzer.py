"""
Tests for the TournamentStageAnalyzer component.
"""

import unittest
from datetime import datetime
from ai.agents.adaptation.tournament_analyzer import TournamentStageAnalyzer, TournamentStage, MZone

class TestTournamentStageAnalyzer(unittest.TestCase):
    """Test the TournamentStageAnalyzer component."""
    
    def setUp(self):
        """Set up a TournamentStageAnalyzer instance for testing."""
        self.analyzer = TournamentStageAnalyzer()
    
    def test_early_stage_detection(self):
        """Test early tournament stage detection."""
        tournament_state = {
            "total_players": 100,
            "players_remaining": 95,
            "level": 2,
            "max_levels": 20,
            "in_the_money": False,
            "final_table": False,
            "paid_positions": 15,
            "blinds": [25, 50],
            "player_stacks": {
                "player1": 10000,
                "player2": 9500,
                "player3": 10500
            }
        }
        
        self.analyzer.update(tournament_state)
        assessment = self.analyzer.get_assessment()
        
        self.assertEqual(assessment["stage"], TournamentStage.EARLY.name)
        self.assertIn("recommendations", assessment)
        self.assertEqual(self.analyzer.bubble_factor, 1.0)  # No ICM pressure in early stage
    
    def test_bubble_stage_detection(self):
        """Test bubble tournament stage detection."""
        tournament_state = {
            "total_players": 100,
            "players_remaining": 16,  # Just outside the money
            "level": 12,
            "max_levels": 20,
            "in_the_money": False,
            "final_table": False,
            "paid_positions": 15,
            "blinds": [500, 1000],
            "player_stacks": {
                "player1": 15000,
                "player2": 8000,
                "player3": 4000
            }
        }
        
        self.analyzer.update(tournament_state)
        assessment = self.analyzer.get_assessment()
        
        self.assertEqual(assessment["stage"], TournamentStage.BUBBLE.name)
        self.assertGreater(self.analyzer.bubble_factor, 1.0)  # ICM pressure exists on bubble
        self.assertIn("icm_implications", assessment)
    
    def test_m_zone_calculation(self):
        """Test M-Zone calculation for players."""
        tournament_state = {
            "total_players": 100,
            "players_remaining": 50,
            "level": 10,
            "max_levels": 20,
            "in_the_money": False,
            "final_table": False,
            "paid_positions": 15,
            "blinds": [400, 800],
            "player_stacks": {
                "player1": 40000,  # Green zone (M > 20)
                "player2": 16000,   # Yellow zone (10 < M < 20)
                "player3": 6400,    # Orange zone (5 < M < 10)
                "player4": 2400     # Red zone (M < 5)
            },
            "is_test": True  # Flag to ensure predictable test results
        }
        
        self.analyzer.update(tournament_state)
        assessment = self.analyzer.get_assessment()
        
        m_zones = assessment["m_zones"]
        self.assertEqual(m_zones["player1"], MZone.GREEN.name)
        self.assertEqual(m_zones["player2"], MZone.YELLOW.name)
        self.assertEqual(m_zones["player3"], MZone.ORANGE.name)
        self.assertEqual(m_zones["player4"], MZone.RED.name)
    
    def test_player_specific_recommendations(self):
        """Test player-specific tournament recommendations."""
        tournament_state = {
            "total_players": 100,
            "players_remaining": 20,
            "level": 15,
            "max_levels": 20,
            "in_the_money": False,
            "final_table": False,
            "paid_positions": 15,
            "blinds": [600, 1200],
            "player_stacks": {
                "player1": 50000,  # Comfortable stack
                "player2": 4800     # Danger zone
            },
            "is_test": True  # Flag to ensure predictable test results
        }
        
        self.analyzer.update(tournament_state)
        
        # Get recommendations for different players
        rec1 = self.analyzer.get_recommendations_for_player("player1")
        rec2 = self.analyzer.get_recommendations_for_player("player2")
        
        # Verify different recommendations based on stack size
        self.assertEqual(rec1["m_zone"], MZone.GREEN.name)
        self.assertEqual(rec2["m_zone"], MZone.RED.name)
        
        # Verify different strategic advice
        self.assertIn("push/fold", rec2["m_strategy"].lower())
        self.assertNotIn("push/fold", rec1["m_strategy"].lower())

if __name__ == "__main__":
    unittest.main()