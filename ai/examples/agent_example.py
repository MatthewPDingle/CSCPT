"""
Example script demonstrating the use of poker agents.
"""

import asyncio
import json
import os
import logging
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

from ai.llm_service import LLMService
from ai.agents import TAGAgent, LAGAgent

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

async def main():
    """Run the agent example."""
    # Print available API keys for debugging
    print("API Keys Available:")
    print(f"Anthropic: {'Yes' if os.environ.get('ANTHROPIC_API_KEY') else 'No'}")
    print(f"OpenAI: {'Yes' if os.environ.get('OPENAI_API_KEY') else 'No'}")
    print(f"Gemini: {'Yes' if os.environ.get('GEMINI_API_KEY') else 'No'}")
    print()
    
    # Initialize the LLM service
    llm_service = LLMService()
    
    # Determine which provider to use based on available API keys
    provider = "anthropic"  # Default
    if not os.environ.get('ANTHROPIC_API_KEY'):
        if os.environ.get('OPENAI_API_KEY'):
            provider = "openai"
        elif os.environ.get('GEMINI_API_KEY'):
            provider = "gemini"
    
    print(f"Using provider: {provider}")
    
    # Create both agent types
    tag_agent = TAGAgent(llm_service, provider=provider)
    lag_agent = LAGAgent(llm_service, provider=provider)
    
    # Get decisions from each agent for the same scenario
    logger.info("Getting decision from TAG agent...")
    tag_decision = await tag_agent.make_decision(EXAMPLE_GAME_STATE, EXAMPLE_CONTEXT)
    
    logger.info("Getting decision from LAG agent...")
    lag_decision = await lag_agent.make_decision(EXAMPLE_GAME_STATE, EXAMPLE_CONTEXT)
    
    # Print the decisions
    print("\nTAG Agent Decision:")
    print(json.dumps(tag_decision, indent=2))
    
    print("\nLAG Agent Decision:")
    print(json.dumps(lag_decision, indent=2))
    
    # Compare the decisions
    print("\nComparison:")
    print(f"TAG action: {tag_decision['action']}" + 
          (f" {tag_decision['amount']}" if tag_decision['amount'] is not None else ""))
    print(f"LAG action: {lag_decision['action']}" + 
          (f" {lag_decision['amount']}" if lag_decision['amount'] is not None else ""))

if __name__ == "__main__":
    asyncio.run(main())