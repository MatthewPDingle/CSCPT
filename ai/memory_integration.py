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
from ai.agents.models.opponent_profile import OpponentProfile, StatisticValue, OpponentNote
from ai.agents.models.memory_service import MemoryService
from ai.agents.models.memory_connector import MemoryConnector
from ai.llm_service import LLMService
# 'prompts' module unused in this integration; removed to fix import errors

# Import agent definitions if available
try:
    from agents.base_agent import PokerAgent
    from agents.tag_agent import TAGAgent
    from agents.lag_agent import LAGAgent
    from agents.adaptable_agent import AdaptableAgent
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

# AgentFactory has been removed - agents are now created directly in game_service.py

class MemoryIntegration:
    """
    Simplified integration class for direct testing.
    """
    # Class-level reference to the memory service for easy access
    _memory_service = None
    _memory_enabled = False
    
    @classmethod
    def initialize(cls, memory_service=None, enable_memory=True):
        """
        Initialize the memory integration.
        
        Args:
            memory_service: Optional memory service to use
            enable_memory: Whether to enable memory by default
            
        Returns:
            The memory connector instance
        """
        # Initialize the connector with the specified memory service
        connector = MemoryConnector.get_instance()
        if memory_service:
            connector.memory_service = memory_service
            cls._memory_service = memory_service
        else:
            cls._memory_service = connector.memory_service
        
        # Enable/disable memory based on parameter
        if enable_memory:
            connector.enable()
            cls._memory_enabled = True
            print("Memory system initialized and enabled")
        else:
            connector.disable()
            cls._memory_enabled = False
            print("Memory system initialized but disabled")
        
        # Return the connector for testing
        return connector
    
    @classmethod
    def is_memory_enabled(cls):
        """Check if memory system is enabled."""
        if hasattr(cls, '_memory_enabled'):
            return cls._memory_enabled
        return False
    
    @classmethod
    def enable_memory(cls):
        """Enable the memory system."""
        connector = MemoryConnector.get_instance()
        connector.enable()
        cls._memory_enabled = True
        cls._memory_service = connector.memory_service
        
    @classmethod
    def disable_memory(cls):
        """Disable the memory system."""
        connector = MemoryConnector.get_instance()
        connector.disable()
        cls._memory_enabled = False
    
    @classmethod
    def get_all_profiles(cls):
        """Get all player profiles."""
        if not cls._memory_service:
            return []
        
        return [
            profile.to_dict() 
            for player_id, profile in cls._memory_service.active_profiles.items()
        ]
    
    @classmethod
    def get_player_profile(cls, player_id):
        """Get a specific player's profile."""
        if not cls._memory_service:
            return None
            
        profile = cls._memory_service.get_profile(player_id)
        if profile:
            return profile.to_dict()
        return None
    
    @classmethod
    async def get_agent_decision(cls, 
                                archetype: str, 
                                game_state: dict, 
                                context: dict, 
                                player_id: str, 
                                use_memory: bool = True,
                                intelligence_level: str = "expert") -> dict:
        """
        Get a decision from an AI agent of a specific archetype.
        
        Args:
            archetype: The agent archetype (e.g., "TAG", "LAG", "Adaptable")
            game_state: Current game state
            context: Additional context information
            player_id: ID of the player making the decision
            use_memory: Whether to use player memory/profiles
            intelligence_level: Agent intelligence level
            
        Returns:
            A decision object with action, amount, and reasoning
        """
        import logging
        from ai.llm_service import LLMService
        import importlib
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Default to OpenAI provider (GPT-4o) per requirements
        provider = "openai"
        
        # Map archetype strings to agent classes
        archetype_map = {
            "TAG": "TAGAgent",
            "LAG": "LAGAgent",
            "TightPassive": "TightPassiveAgent",
            "LoosePassive": "LoosePassiveAgent",
            "CallingStation": "CallingStationAgent",
            "Maniac": "ManiacAgent", 
            "Beginner": "BeginnerAgent",
            "Adaptable": "AdaptableAgent",
            "GTO": "GTOAgent",
            "ShortStack": "ShortStackAgent",
            "Trappy": "TrappyAgent"
        }
        
        # Handle case variations in archetype names
        archetype = archetype.replace(" ", "")
        agent_class_name = archetype_map.get(archetype, "TAGAgent")  # Default to TAG if not found
        
        try:
            # Dynamically import the appropriate agent class
            agent_module = importlib.import_module(f"ai.agents.{agent_class_name.lower()}")
            agent_class = getattr(agent_module, agent_class_name)
            
            # Create agent instance
            agent = agent_class(
                llm_service=llm_service,
                provider=provider,
                intelligence_level=intelligence_level,
                temperature=0.7,
                extended_thinking=True,
                use_persistent_memory=use_memory
            )
            
            # Get the decision from the agent
            logging.info(f"Requesting decision from {agent_class_name} with provider {provider}")
            decision = await agent.make_decision(game_state, context)
            logging.info(f"Received decision from agent: {decision}")
            
            return decision
            
        except (ImportError, AttributeError) as e:
            logging.error(f"Error loading agent class {agent_class_name}: {e}")
            # Fallback to a default decision
            return {
                "thinking": f"Error loading agent: {str(e)}",
                "action": "check" if game_state.get("current_bet", 0) == 0 else "call",
                "amount": None,
                "reasoning": {
                    "hand_assessment": "Using fallback decision due to agent loading error",
                    "positional_considerations": "Default reasoning",
                    "opponent_reads": "Default reasoning",
                    "archetype_alignment": f"Attempted to use {archetype} archetype"
                }
            }
        except Exception as e:
            logging.error(f"Unexpected error in get_agent_decision: {e}")
            import traceback
            logging.error(traceback.format_exc())
            
            # More lenient fallback that prefers checking to folding when possible
            current_bet = game_state.get("current_bet", 0)
            if current_bet == 0:
                action = "check"  # If no bet to call, check instead of fold
            else:
                action = "call"   # Try to call if there's a bet
                
                # If we can't afford the call, then fold
                player_stack = game_state.get("stack_sizes", {}).get("0", 0)
                if player_stack < current_bet:
                    action = "fold"
            
            return {
                "thinking": f"Error in agent decision: {str(e)}",
                "action": action,
                "amount": None,
                "reasoning": {
                    "hand_assessment": "Using fallback decision due to error",
                    "positional_considerations": "Default reasoning",
                    "opponent_reads": "Default reasoning", 
                    "archetype_alignment": f"Attempted to use {archetype} archetype"
                }
            }
    
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