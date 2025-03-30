"""
Test the memory integration directly.
"""

import os
import sys
import asyncio
import tempfile
import shutil
from pprint import pprint
from datetime import datetime

# Import our local modules
from agents.models.opponent_profile import OpponentProfile, StatisticValue, OpponentNote
from agents.models.memory_service import MemoryService
from agents.models.memory_connector import MemoryConnector
from llm_service import LLMService
import prompts

# Import agent definitions if available
try:
    from agents.base_agent import PokerAgent
    from agents.tag_agent import TAGAgent
    from agents.lag_agent import LAGAgent
    from agents.adaptable_agent import AdaptableAgent
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

class AgentFactory:
    """Factory for creating poker agents."""
    
    @staticmethod
    def create_agent(archetype, use_memory=True, intelligence_level="expert"):
        """Create an agent with the specified archetype and settings."""
        if not AGENTS_AVAILABLE:
            print("Agent implementations not available")
            return None
            
        # Initialize LLM service
        llm_service = LLMService()
        
        # Create agent based on archetype
        if archetype == "TAG":
            return TAGAgent(
                llm_service=llm_service,
                intelligence_level=intelligence_level,
                use_persistent_memory=use_memory
            )
        elif archetype == "LAG":
            return LAGAgent(
                llm_service=llm_service,
                intelligence_level=intelligence_level,
                use_persistent_memory=use_memory
            )
        elif archetype == "Adaptable":
            return AdaptableAgent(
                llm_service=llm_service,
                intelligence_level=intelligence_level,
                use_persistent_memory=use_memory
            )
        else:
            print(f"Unsupported archetype: {archetype}")
            return None

class MemoryIntegration:
    """
    Simplified integration class for direct testing.
    """
    
    @classmethod
    def initialize(cls, memory_service=None):
        """Initialize the memory integration for testing."""
        # Initialize the connector with the specified memory service
        connector = MemoryConnector.get_instance()
        if memory_service:
            connector.memory_service = memory_service
        connector.enable()
        print("Memory system initialized")
        
        # Return the connector for testing
        return connector
    
    @classmethod
    async def get_agent_decision(cls, archetype, game_state, context, player_id, connector=None):
        """Get a decision from an agent using the memory system."""
        # Create an agent
        agent = AgentFactory.create_agent(archetype)
        if not agent:
            return {"action": "fold", "reason": "Agent creation failed"}
            
        # If connector specified, use its memory service
        if connector:
            # Get the memory service from the connector
            agent.memory_service = connector.memory_service
        
        # Add player_id to game state
        game_state["player_id"] = player_id
        
        # Make decision
        return await agent.make_decision(game_state, context)
    
    @classmethod
    def process_hand_history(cls, hand_data, connector=None):
        """Process a hand history to update memory."""
        if not connector:
            connector = MemoryConnector.get_instance()
        
        connector.process_hand_history(hand_data)
        print(f"Processed hand #{hand_data.get('hand_number', 'Unknown')}")


async def test_memory_integration():
    """Test the memory integration functionality."""
    # Create temporary directory for test
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary directory: {temp_dir}")
    
    try:
        # Initialize memory service
        memory_service = MemoryService(storage_dir=temp_dir)
        
        # Initialize memory integration
        connector = MemoryIntegration.initialize(memory_service)
        
        # Process a sample hand
        hand_data = {
            "hand_number": 1,
            "players": [
                {
                    "player_id": "ai1",
                    "name": "TAG Player",
                    "is_human": False,
                    "archetype": "TAG",
                    "vpip": True,
                    "pfr": True,
                    "hole_cards": ["Ah", "Kh"],
                    "won_amount": 100
                },
                {
                    "player_id": "ai2",
                    "name": "LAG Player",
                    "is_human": False,
                    "archetype": "LAG",
                    "vpip": True,
                    "pfr": False,
                    "hole_cards": ["Qd", "Jd"],
                    "won_amount": -50
                }
            ],
            "betting_rounds": {
                "PREFLOP": [
                    {"player_id": "ai1", "action_type": "raise", "amount": 20},
                    {"player_id": "ai2", "action_type": "call", "amount": 20}
                ],
                "FLOP": [
                    {"player_id": "ai1", "action_type": "bet", "amount": 30},
                    {"player_id": "ai2", "action_type": "call", "amount": 30}
                ],
                "TURN": [
                    {"player_id": "ai1", "action_type": "bet", "amount": 50},
                    {"player_id": "ai2", "action_type": "fold"}
                ]
            }
        }
        
        MemoryIntegration.process_hand_history(hand_data, connector)
        
        # Create second hand
        hand_data_2 = {
            "hand_number": 2,
            "players": [
                {
                    "player_id": "ai1",
                    "name": "TAG Player",
                    "is_human": False,
                    "archetype": "TAG",
                    "vpip": True,
                    "pfr": True,
                    "hole_cards": ["Ah", "Kh"],
                    "won_amount": 100
                },
                {
                    "player_id": "ai2",
                    "name": "LAG Player",
                    "is_human": False,
                    "archetype": "LAG",
                    "vpip": True,
                    "pfr": True,
                    "hole_cards": ["Qd", "Jd"],
                    "won_amount": -50
                }
            ],
            "betting_rounds": {
                "PREFLOP": [
                    {"player_id": "ai1", "action_type": "raise", "amount": 20},
                    {"player_id": "ai2", "action_type": "raise", "amount": 60},
                    {"player_id": "ai1", "action_type": "call", "amount": 40}
                ],
                "FLOP": [
                    {"player_id": "ai1", "action_type": "check"},
                    {"player_id": "ai2", "action_type": "bet", "amount": 80},
                    {"player_id": "ai1", "action_type": "fold"}
                ]
            }
        }
        
        MemoryIntegration.process_hand_history(hand_data_2, connector)
        
        # Get profiles
        print("\nProfiles after processing hands:")
        for player_id, profile in connector.memory_service.active_profiles.items():
            print(f"\nPlayer: {profile.name} ({player_id})")
            print(f"Hands observed: {profile.hands_observed}")
            print(f"Archetype: {profile.archetype or 'Unknown'}")
            
            print("\nStatistics:")
            for stat_name, stat in profile.stats.items():
                print(f"  {stat_name}: {stat.value} (confidence: {stat.confidence:.2f}, samples: {stat.sample_size})")
        
        # Test getting a decision with memory
        if AGENTS_AVAILABLE:
            # Create sample game state
            game_state = {
                "hand": ["Ah", "Kh"],
                "community_cards": ["Qh", "Jh", "2c"],
                "position": "BTN",
                "pot": 100,
                "action_history": [
                    {"player_id": "ai2", "action": "check"},
                    {"player_id": "ai1", "action": "bet", "amount": 50}
                ],
                "stack_sizes": {"ai1": 950, "ai2": 1000}
            }
            
            context = {
                "game_type": "cash",
                "stage": "middle",
                "blinds": [5, 10]
            }
            
            print("\nGetting decision from Adaptable agent with memory...")
            decision = await MemoryIntegration.get_agent_decision(
                archetype="Adaptable",
                game_state=game_state,
                context=context,
                player_id="ai1",
                connector=connector
            )
            
            print("\nAgent Decision:")
            print(f"Action: {decision.get('action')}")
            if decision.get('amount') is not None:
                print(f"Amount: {decision.get('amount')}")
            
            print("\nReasoning:")
            for key, value in decision.get('reasoning', {}).items():
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        return True
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory: {temp_dir}")


if __name__ == "__main__":
    asyncio.run(test_memory_integration())