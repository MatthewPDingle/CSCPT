"""
Comprehensive example showing all three providers working together.

This script demonstrates using the LLM abstraction layer with all three providers
(Anthropic, OpenAI, and Gemini) using the same prompts. This shows how the
abstraction allows seamless switching between providers.

To use this script:
1. Set your API keys in the .env file for all providers you want to test
2. Run this script
"""

import os
import json
import asyncio
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the service module
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.llm_service import LLMService

# Load environment variables
load_dotenv()

# Define providers to test
PROVIDERS = ["anthropic", "openai", "gemini"]

# Define common prompts for all tests
SYSTEM_PROMPT = "You are a helpful poker strategy assistant."
USER_PROMPT = "What's the optimal strategy for playing pocket Aces pre-flop in Texas Hold'em?"

JSON_SYSTEM_PROMPT = "You are a poker hand analyzer."
JSON_USER_PROMPT = "Analyze this poker hand: Player 1 has K♠Q♠, Player 2 has A♥A♦. The flop is K♥8♠2♦."
JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "player1": {
            "type": "object",
            "properties": {
                "hand": {"type": "string"},
                "hand_strength": {"type": "string"},
                "win_probability": {"type": "number"}
            }
        },
        "player2": {
            "type": "object",
            "properties": {
                "hand": {"type": "string"},
                "hand_strength": {"type": "string"},
                "win_probability": {"type": "number"}
            }
        },
        "analysis": {"type": "string"}
    }
}

THINKING_SYSTEM_PROMPT = "You are a poker probability expert."
THINKING_USER_PROMPT = (
    "Calculate the probability of improving to a flush when you have 4 spades "
    "after the flop in Texas Hold'em. Show your work step by step."
)

async def test_provider(provider, service):
    """Test all capabilities for a given provider."""
    logger.info(f"============ Testing {provider.upper()} Provider ============")
    
    # Basic completion
    logger.info(f"\n--- Basic Completion Test ({provider}) ---")
    try:
        response = await service.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=USER_PROMPT,
            provider=provider,
            temperature=0.7
        )
        logger.info(f"Response (truncated): {response[:150]}...")
    except Exception as e:
        logger.error(f"Error in basic completion: {str(e)}")
    
    # JSON completion
    logger.info(f"\n--- JSON Completion Test ({provider}) ---")
    try:
        response = await service.complete_json(
            system_prompt=JSON_SYSTEM_PROMPT,
            user_prompt=JSON_USER_PROMPT,
            json_schema=JSON_SCHEMA,
            provider=provider,
            temperature=0.7
        )
        logger.info(f"JSON Response: {json.dumps(response, indent=2)}")
    except Exception as e:
        logger.error(f"Error in JSON completion: {str(e)}")
    
    # Extended thinking
    logger.info(f"\n--- Extended Thinking Test ({provider}) ---")
    try:
        response = await service.complete(
            system_prompt=THINKING_SYSTEM_PROMPT,
            user_prompt=THINKING_USER_PROMPT,
            provider=provider,
            temperature=0.7,
            extended_thinking=True
        )
        logger.info(f"Extended thinking response (truncated): {response[:150]}...")
    except Exception as e:
        logger.error(f"Error in extended thinking: {str(e)}")

async def main():
    """Run tests for all configured providers."""
    logger.info("Starting comprehensive provider tests")
    
    # Initialize the service
    service = LLMService()
    
    # Test each provider that has an API key configured
    for provider in PROVIDERS:
        config_var = f"{provider.upper()}_API_KEY"
        if os.environ.get(config_var):
            await test_provider(provider, service)
        else:
            logger.warning(f"Skipping {provider} (no API key found in {config_var})")
    
    logger.info("\nAll tests completed")

if __name__ == "__main__":
    asyncio.run(main())