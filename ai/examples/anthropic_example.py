"""
Example demonstrating how to use the Anthropic provider with the LLM service.
"""

import os
import asyncio
import logging
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

import sys
# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables from .env file
env_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / '.env'
load_dotenv(dotenv_path=env_path)

from ai import LLMService

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Example of using the LLM service with Anthropic provider."""
    
    # Make sure the API key is in the environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable is not set")
        return
    
    logger.info(f"Found API key (starting with): {api_key[:10]}...")
    
    # Initialize the LLM service
    llm_service = LLMService()
    
    # Example 1: Simple text completion
    system_prompt = "You are a helpful assistant specialized in poker strategy."
    user_prompt = "What's the difference between a TAG and LAG playing style in poker?"
    
    logger.info("Asking about poker strategies...")
    response = await llm_service.complete(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.7
    )
    
    logger.info(f"Response: {response}")
    
    # Example 2: JSON structured response
    json_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["fold", "check", "call", "bet", "raise"]},
            "amount": {"type": "number"},
            "reasoning": {"type": "string"}
        },
        "required": ["action", "reasoning"]
    }
    
    system_prompt = "You are a tight-aggressive poker player."
    user_prompt = """
    You're playing Texas Hold'em and have A♠ K♠ in early position.
    The blinds are 10/20, and you have 1,000 chips.
    No one has acted yet. What's your action?
    """
    
    logger.info("Asking for a poker decision...")
    response_json = await llm_service.complete_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        json_schema=json_schema,
        temperature=0.7
    )
    
    logger.info(f"JSON Response: {response_json}")
    
    # Example 3: Using extended thinking mode
    system_prompt = "You are a poker coach analyzing a complex hand."
    user_prompt = """
    Analyze this poker hand situation:
    - You have Q♣ Q♥ in middle position
    - Flop is K♠ Q♠ 7♦ (you flopped three of a kind)
    - The pot is 100 chips
    - You have 500 chips left
    - Opponent in early position bets 75 chips
    - There are two more players yet to act after you
    
    What's the optimal play here and why?
    """
    
    logger.info("Asking for a complex hand analysis with extended thinking...")
    response = await llm_service.complete(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.7,  # This will be automatically set to 1.0 for extended thinking
        max_tokens=5000,  # Ensure this is greater than thinking_budget_tokens
        extended_thinking=True
    )
    
    logger.info(f"Extended thinking response: {response}")

if __name__ == "__main__":
    asyncio.run(main())