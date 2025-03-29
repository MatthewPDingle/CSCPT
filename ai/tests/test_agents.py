"""
Tests for poker agent implementations.
"""

import unittest
import asyncio
from unittest.mock import AsyncMock, patch
import os

from ai.llm_service import LLMService
from ai.agents import TAGAgent, LAGAgent

class AgentTests(unittest.TestCase):
    """Test cases for poker agents."""
    
    def setUp(self):
        """Set up test environment."""
        # Check if we should skip tests requiring API keys
        self.skip_external = os.environ.get("SKIP_EXTERNAL_TESTS", "true").lower() == "true"
        
        # Create a mock LLM service for initial tests
        self.mock_llm_service = AsyncMock(spec=LLMService)
        self.mock_llm_service.complete_json = AsyncMock()
        
        # Set up mock response
        self.mock_response = {
            "thinking": "Test thinking process",
            "action": "call",
            "amount": None,
            "reasoning": {
                "hand_assessment": "Test hand assessment",
                "positional_considerations": "Test position",
                "opponent_reads": "Test opponent reads",
                "archetype_alignment": "Test alignment"
            }
        }
        self.mock_llm_service.complete_json.return_value = self.mock_response
        
        # Example game state for tests
        self.test_game_state = {
            "hand": ["As", "Kh"],
            "community_cards": ["Jd", "Tc", "2s"],
            "position": "BTN",
            "pot": 120,
            "action_history": [
                {"player_id": "1", "action": "fold"},
                {"player_id": "2", "action": "raise", "amount": 20}
            ],
            "stack_sizes": {
                "0": 500,
                "1": 320,
                "2": 650
            }
        }
        
        self.test_context = {
            "game_type": "tournament",
            "stage": "middle",
            "blinds": [10, 20]
        }
    
    def test_tag_agent_initialization(self):
        """Test that TAG agent initializes correctly."""
        agent = TAGAgent(self.mock_llm_service)
        self.assertEqual(agent.temperature, 0.5)
        self.assertTrue(isinstance(agent.get_system_prompt(), str))
        self.assertTrue(len(agent.get_system_prompt()) > 100)
    
    def test_lag_agent_initialization(self):
        """Test that LAG agent initializes correctly."""
        agent = LAGAgent(self.mock_llm_service)
        self.assertEqual(agent.temperature, 0.8)
        self.assertTrue(isinstance(agent.get_system_prompt(), str))
        self.assertTrue(len(agent.get_system_prompt()) > 100)
    
    def test_different_prompts(self):
        """Test that TAG and LAG agents have different prompts."""
        tag_agent = TAGAgent(self.mock_llm_service)
        lag_agent = LAGAgent(self.mock_llm_service)
        self.assertNotEqual(tag_agent.get_system_prompt(), lag_agent.get_system_prompt())
    
    async def async_test_make_decision(self):
        """Test the make_decision method works."""
        agent = TAGAgent(self.mock_llm_service)
        decision = await agent.make_decision(self.test_game_state, self.test_context)
        
        self.assertEqual(decision["action"], "call")
        self.assertIsNone(decision["amount"])
        self.assertEqual(decision["reasoning"]["hand_assessment"], "Test hand assessment")
        
        # Check that complete_json was called with the right arguments
        self.mock_llm_service.complete_json.assert_called_once()
        call_args = self.mock_llm_service.complete_json.call_args[1]
        self.assertEqual(call_args["temperature"], 0.5)
        self.assertEqual(call_args["provider"], None)
    
    def test_make_decision(self):
        """Wrapper to run async test."""
        asyncio.run(self.async_test_make_decision())
    
    @unittest.skipIf(True, "Skipping live API tests by default")
    async def async_test_live_tag_agent(self):
        """Test TAG agent with actual API (skipped by default)."""
        if self.skip_external:
            return
            
        # Initialize real service for this test
        llm_service = LLMService()
        agent = TAGAgent(llm_service)
        
        # Make a real decision
        decision = await agent.make_decision(self.test_game_state, self.test_context)
        
        # Basic validation of response
        self.assertIn(decision["action"], ["fold", "check", "call", "bet", "raise", "all-in"])
        self.assertIn("thinking", decision)
        self.assertIn("reasoning", decision)
    
    @unittest.skipIf(True, "Skipping live API tests by default")
    def test_live_tag_agent(self):
        """Wrapper to run async live test."""
        asyncio.run(self.async_test_live_tag_agent())

if __name__ == "__main__":
    unittest.main()