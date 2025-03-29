"""
Example script showcasing all poker player archetypes.
"""

import asyncio
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, List, Tuple

from ai.llm_service import LLMService
from ai.agents import (
    TAGAgent, 
    LAGAgent, 
    TightPassiveAgent,
    CallingStationAgent,
    LoosePassiveAgent,
    ManiacAgent,
    BeginnerAgent,
    AdaptableAgent,
    GTOAgent,
    ShortStackAgent,
    TrappyAgent,
    AgentResponseParser
)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Example game state - Strong hand on the flop
STRONG_HAND_GAME_STATE = {
    "hand": ["As", "Ad"],  # Pocket aces
    "community_cards": ["Jd", "Ts", "2s"],  # Decent flop for aces
    "position": "BTN",  # Button position
    "pot": 120,
    "action_history": [
        {"player_id": "1", "action": "fold"},
        {"player_id": "2", "action": "raise", "amount": 20},
        {"player_id": "3", "action": "call", "amount": 20}
    ],
    "stack_sizes": {
        "0": 500,  # Our stack
        "1": 320,
        "2": 650,
        "3": 480
    }
}

# Example game state - Marginal hand on the flop
MARGINAL_HAND_GAME_STATE = {
    "hand": ["Ks", "Qh"],  # KQ offsuit
    "community_cards": ["Jd", "Ts", "2s"],  # Straight draw
    "position": "BTN",  # Button position
    "pot": 120,
    "action_history": [
        {"player_id": "1", "action": "fold"},
        {"player_id": "2", "action": "raise", "amount": 20},
        {"player_id": "3", "action": "call", "amount": 20}
    ],
    "stack_sizes": {
        "0": 500,  # Our stack
        "1": 320,
        "2": 650,
        "3": 480
    }
}

# Example context
EXAMPLE_CONTEXT = {
    "game_type": "tournament",
    "stage": "middle",
    "blinds": [10, 20]
}

async def get_agent_decisions(
    llm_service: LLMService,
    provider: str,
    game_state: Dict[str, Any]
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Get decisions from all archetypes for the same scenario.
    
    Args:
        llm_service: LLM service instance
        provider: LLM provider to use
        game_state: Game state to analyze
        
    Returns:
        List of (archetype_name, decision) tuples
    """
    # Create all agent types
    agents = [
        ("TAG", TAGAgent(llm_service, provider=provider)),
        ("LAG", LAGAgent(llm_service, provider=provider)),
        ("Tight-Passive", TightPassiveAgent(llm_service, provider=provider)),
        ("Calling Station", CallingStationAgent(llm_service, provider=provider)),
        ("Loose-Passive", LoosePassiveAgent(llm_service, provider=provider)),
        ("Maniac", ManiacAgent(llm_service, provider=provider)),
        ("Beginner", BeginnerAgent(llm_service, provider=provider)),
        ("Adaptable", AdaptableAgent(llm_service, provider=provider)),
        ("GTO", GTOAgent(llm_service, provider=provider)),
        ("Short Stack", ShortStackAgent(llm_service, provider=provider)),
        ("Trappy", TrappyAgent(llm_service, provider=provider))
    ]
    
    # Get decisions
    decisions = []
    for name, agent in agents:
        logger.info(f"Getting decision from {name} agent...")
        try:
            decision = await agent.make_decision(game_state, EXAMPLE_CONTEXT)
            decisions.append((name, decision))
        except Exception as e:
            logger.error(f"Error getting decision from {name} agent: {e}")
            # Create a default error response
            error_decision = {
                "thinking": f"Error occurred: {str(e)}",
                "action": "fold",
                "amount": None,
                "reasoning": {
                    "hand_assessment": "Error occurred",
                    "positional_considerations": "Error occurred",
                    "opponent_reads": "Error occurred", 
                    "archetype_alignment": "Error occurred"
                }
            }
            decisions.append((name, error_decision))
    
    return decisions

def display_decision_comparison(decisions: List[Tuple[str, Dict[str, Any]]]):
    """
    Display a comparison of decisions from different archetypes.
    
    Args:
        decisions: List of (archetype_name, decision) tuples
    """
    print("\nDecision Comparison:")
    print("=" * 80)
    print(f"{'Archetype':<15} {'Action':<10} {'Amount':<10} {'Hand Assessment':<45}")
    print("-" * 80)
    
    for name, decision in decisions:
        action = decision.get("action", "error")
        amount = decision.get("amount", "")
        if amount is None:
            amount = ""
        hand_assessment = decision.get("reasoning", {}).get("hand_assessment", "")
        if len(hand_assessment) > 45:
            hand_assessment = hand_assessment[:42] + "..."
            
        print(f"{name:<15} {action:<10} {amount:<10} {hand_assessment:<45}")
    
    print("=" * 80)
    
    # Analyze variance in decisions
    actions = {}
    for name, decision in decisions:
        action = decision.get("action", "error")
        if action not in actions:
            actions[action] = []
        actions[action].append(name)
    
    print("\nAnalysis of Decision Variance:")
    for action, archetypes in actions.items():
        print(f"{action}: {len(archetypes)} archetypes - {', '.join(archetypes)}")

async def main():
    """Run the archetype showcase example."""
    # Initialize the LLM service
    llm_service = LLMService()
    
    # Determine which provider to use based on available API keys
    provider = "anthropic"  # Default
    
    # Get decisions for the strong hand scenario
    print("\n========== STRONG HAND SCENARIO (Pocket Aces) ==========")
    print("Hand: As Ad, Board: Jd Ts 2s, Position: Button\n")
    strong_hand_decisions = await get_agent_decisions(llm_service, provider, STRONG_HAND_GAME_STATE)
    display_decision_comparison(strong_hand_decisions)
    
    # Get decisions for the marginal hand scenario
    print("\n========== MARGINAL HAND SCENARIO (KQ with Straight Draw) ==========")
    print("Hand: Ks Qh, Board: Jd Ts 2s, Position: Button\n")
    marginal_hand_decisions = await get_agent_decisions(llm_service, provider, MARGINAL_HAND_GAME_STATE)
    display_decision_comparison(marginal_hand_decisions)
    
    # Save the detailed output to a file for further analysis
    with open("archetype_decisions.json", "w") as f:
        output = {
            "strong_hand": {name: decision for name, decision in strong_hand_decisions},
            "marginal_hand": {name: decision for name, decision in marginal_hand_decisions}
        }
        json.dump(output, f, indent=2)
    
    print("\nDetailed decision data saved to archetype_decisions.json")

if __name__ == "__main__":
    asyncio.run(main())