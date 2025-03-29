"""
Example script demonstrating the use of the agent response parser.
"""

import asyncio
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

from ai.llm_service import LLMService
from ai.agents import TAGAgent, LAGAgent, AgentResponseParser

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Example game state
EXAMPLE_GAME_STATE = {
    "hand": ["As", "Kh"],
    "community_cards": ["Jd", "Tc", "2s"],
    "position": "BTN",
    "pot": 120,
    "action_history": [
        {"player_id": "1", "action": "fold"},
        {"player_id": "2", "action": "raise", "amount": 20},
        {"player_id": "3", "action": "call", "amount": 20}
    ],
    "stack_sizes": {
        "0": 200,  # Our stack (limited for demonstration)
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

async def main():
    """Run the parser example."""
    # Initialize the LLM service
    llm_service = LLMService()
    
    # Create both agent types
    tag_agent = TAGAgent(llm_service, provider="anthropic")
    lag_agent = LAGAgent(llm_service, provider="anthropic")
    
    # Get decisions from each agent
    logger.info("Getting decision from TAG agent...")
    tag_decision = await tag_agent.make_decision(EXAMPLE_GAME_STATE, EXAMPLE_CONTEXT)
    
    logger.info("Getting decision from LAG agent...")
    lag_decision = await lag_agent.make_decision(EXAMPLE_GAME_STATE, EXAMPLE_CONTEXT)
    
    # Parse decisions using the response parser
    logger.info("Parsing TAG agent response...")
    try:
        tag_action, tag_amount, tag_metadata = AgentResponseParser.parse_response(tag_decision)
        logger.info(f"Parsed TAG decision: {tag_action} {tag_amount if tag_amount else ''}")
    except ValueError as e:
        logger.error(f"Error parsing TAG response: {e}")
        tag_action, tag_amount = "fold", None
    
    logger.info("Parsing LAG agent response...")
    try:
        lag_action, lag_amount, lag_metadata = AgentResponseParser.parse_response(lag_decision)
        logger.info(f"Parsed LAG decision: {lag_action} {lag_amount if lag_amount else ''}")
    except ValueError as e:
        logger.error(f"Error parsing LAG response: {e}")
        lag_action, lag_amount = "fold", None
    
    # Apply game rules to ensure the actions are valid
    tag_action, tag_amount = AgentResponseParser.apply_game_rules(
        tag_action, tag_amount, EXAMPLE_GAME_STATE
    )
    
    lag_action, lag_amount = AgentResponseParser.apply_game_rules(
        lag_action, lag_amount, EXAMPLE_GAME_STATE
    )
    
    # Show final adjusted decisions
    print("\nFinal Adjusted Decisions:")
    print(f"TAG: {tag_action} {tag_amount if tag_amount else ''}")
    print(f"LAG: {lag_action} {lag_amount if lag_amount else ''}")
    
    # Demonstrate how this would integrate with a game engine
    print("\nGame Engine Integration Example:")
    print("--------------------------------")
    
    def simulate_game_action(player_type, action, amount):
        """Simulate how a game engine would use the parsed response."""
        if action == "fold":
            return f"{player_type} player folds."
        elif action == "check":
            return f"{player_type} player checks."
        elif action == "call":
            return f"{player_type} player calls."
        elif action in ["bet", "raise"]:
            return f"{player_type} player raises to {amount}."
        elif action == "all-in":
            return f"{player_type} player goes all-in for {amount}!"
        else:
            return f"{player_type} player makes an invalid move."
    
    print(simulate_game_action("TAG", tag_action, tag_amount))
    print(simulate_game_action("LAG", lag_action, lag_amount))

if __name__ == "__main__":
    asyncio.run(main())