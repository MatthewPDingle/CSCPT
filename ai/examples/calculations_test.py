"""
Test script to verify and debug calculations handling across different LLM providers.

This script focuses on ensuring that all model providers correctly handle the 'calculations'
field in the JSON schema responses used by poker agents.

Usage:
1. Set API keys in .env file or environment variables
2. Run: python -m ai.examples.calculations_test
"""

import os
import json
import asyncio
import logging
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up paths
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Import modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.llm_service import LLMService
from ai.prompts import POKER_ACTION_SCHEMA

async def test_provider_calculations(provider_name, llm_service):
    """Test if a provider correctly handles the calculations field."""
    logger.info(f"Testing calculations handling for provider: {provider_name}")
    
    # Use a simple poker scenario
    system_prompt = """You are a Tight-Aggressive (TAG) poker player focusing on optimal mathematical play.
Always include detailed calculations in your responses, including pot odds and equity estimates."""

    user_prompt = """
GAME STATE:
Your Hand: QS QH
Community Cards: 2S 7D QC
Position: Button
Pot Size: 75
Action History: Alice checks → Bob bets 25
Stack Sizes: You: 500, Alice: 400, Bob: 450

What's your decision? Remember to include detailed calculations showing pot odds and equity.
"""

    try:
        # Make the API call, explicitly requesting extended thinking which should help
        # ensure calculations are included
        response = await llm_service.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema=POKER_ACTION_SCHEMA,
            temperature=0.7,
            provider=provider_name,
            extended_thinking=True
        )
        
        # Log the response and check for calculations
        logger.info(f"{provider_name} response keys: {list(response.keys())}")
        
        # Check for calculations field specifically
        if 'calculations' in response:
            logger.info(f"✅ {provider_name} included 'calculations' field")
            logger.info(f"Calculations content: {json.dumps(response['calculations'], indent=2)}")
            return True
        else:
            logger.warning(f"❌ {provider_name} did not include 'calculations' field")
            logger.debug(f"Full response: {json.dumps(response, indent=2)}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing {provider_name}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_gemini_with_explicit_example(llm_service):
    """Test Gemini with an explicit example showing calculations."""
    logger.info("Testing Gemini with explicit example calculations")
    
    # System prompt that shows example
    system_prompt = """You are a Tight-Aggressive (TAG) poker player who always includes detailed calculations.

VERY IMPORTANT: Your response must include a 'calculations' field with 'pot_odds' and 'estimated_equity', like this example:
{
  "thinking": "I have a set of queens, which is very strong.",
  "action": "raise",
  "amount": 75,
  "reasoning": {
    "hand_assessment": "I have three of a kind with my pocket queens.",
    "positional_considerations": "I'm on the button with position.",
    "opponent_reads": "Bob's bet indicates strength.",
    "archetype_alignment": "As a TAG player, I should play strong hands aggressively."
  },
  "calculations": {
    "pot_odds": "To call 25 into a pot of 75 gives me 3:1 odds, requiring 25% equity.",
    "estimated_equity": "With a set of queens, I have approximately 90% equity against a likely range."
  }
}"""

    user_prompt = """
GAME STATE:
Your Hand: QS QH
Community Cards: 2S 7D QC
Position: Button
Pot Size: 75
Action History: Alice checks → Bob bets 25
Stack Sizes: You: 500, Alice: 400, Bob: 450

What's your decision? Make sure to include calculations with pot odds and equity estimates.
"""

    try:
        # Make the API call
        response = await llm_service.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema=POKER_ACTION_SCHEMA,
            temperature=0.7,
            provider="gemini",
            extended_thinking=True
        )
        
        # Log the response and check for calculations
        logger.info(f"Gemini response keys: {list(response.keys())}")
        
        # Check for calculations field specifically
        if 'calculations' in response:
            logger.info(f"✅ Gemini included 'calculations' field with explicit example")
            logger.info(f"Calculations content: {json.dumps(response['calculations'], indent=2)}")
            return True
        else:
            logger.warning(f"❌ Gemini did not include 'calculations' field even with explicit example")
            logger.debug(f"Full response: {json.dumps(response, indent=2)}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing Gemini with explicit example: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Run calculations tests for all providers."""
    logger.info("Starting calculations field tests")
    
    # Initialize LLM service
    llm_service = LLMService()
    
    # Test each available provider
    results = []
    
    # Test OpenAI first (as baseline)
    if os.environ.get("OPENAI_API_KEY"):
        openai_result = await test_provider_calculations("openai", llm_service)
        results.append(("OpenAI", openai_result))
    else:
        logger.warning("Skipping OpenAI test - no API key found")
    
    # Test Anthropic
    if os.environ.get("ANTHROPIC_API_KEY"):
        anthropic_result = await test_provider_calculations("anthropic", llm_service)
        results.append(("Anthropic", anthropic_result))
    else:
        logger.warning("Skipping Anthropic test - no API key found")
    
    # Test Gemini
    if os.environ.get("GEMINI_API_KEY"):
        gemini_result = await test_provider_calculations("gemini", llm_service)
        results.append(("Gemini", gemini_result))
        
        # Special test for Gemini with explicit example
        gemini_explicit = await test_gemini_with_explicit_example(llm_service)
        results.append(("Gemini (explicit example)", gemini_explicit))
    else:
        logger.warning("Skipping Gemini test - no API key found")
    
    # Print summary
    logger.info("\n===== TEST SUMMARY =====")
    for provider, success in results:
        logger.info(f"  {provider}: {'✅ PASSED' if success else '❌ FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())