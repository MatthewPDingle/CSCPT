"""
Test script specifically for GPT-4o-mini JSON schema issue.

This script specifically tests GPT-4o-mini with a JSON schema
response to verify the fix for schema format handling.

To use this script:
1. Set your OpenAI API key in the .env file or as an environment variable
2. Run this script
"""

import os
import json
import asyncio
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the service module
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.llm_service import LLMService
from ai.providers.openai_provider import OpenAIProvider
from ai.prompts import POKER_ACTION_SCHEMA

# Load environment variables
load_dotenv()

async def test_gpt4o_mini_schema():
    """Test GPT-4o-mini with JSON schema to verify unwrapping logic works."""
    api_key = os.environ.get("OPENAI_API_KEY")
    organization_id = os.environ.get("OPENAI_ORGANIZATION_ID")
    
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        return False
    
    try:
        # Initialize provider directly
        provider = OpenAIProvider(
            api_key=api_key,
            model="gpt-4o-mini",
            reasoning_level="medium",
            organization_id=organization_id
        )
        
        # Simplified poker scenario system prompt
        system_prompt = """You are a tight-passive poker player. Your playing style is characterized by:
- Playing few hands (tight)
- Being cautious and risk-averse
- Preferring to call rather than raise (passive)
- Avoiding confrontation
- Looking for strong hands before committing chips
- Being patient and waiting for premium hands

Provide your poker decision in JSON format according to the schema provided.
"""
        
        # User prompt with a simple poker scenario
        user_prompt = """
GAME STATE:
Your Hand: JD KH
Community Cards: None
Position: Middle Position
Pot Size: 12
Action History: Alice posts small blind 5 → Bob calls 5
Stack Sizes: You: 200, Alice: 320, Bob: 650

Based on the current situation, what action will you take? Analyze the hand, consider pot odds, evaluate opponent tendencies, and make a decision that aligns with your playing style.
"""
        
        # Test JSON response with schema
        logger.info("Testing GPT-4o-mini JSON schema response")
        response = await provider.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema=POKER_ACTION_SCHEMA,
            temperature=0.7
        )
        
        logger.info(f"JSON Response Structure (keys): {list(response.keys())}")
        logger.info(f"Full Response: {json.dumps(response, indent=2)}")
        
        # Verify the response doesn't contain schema structure
        if "type" in response and "properties" in response:
            logger.error("FAILED: Response still contains schema structure")
            return False
        
        if "thinking" in response and "action" in response and "amount" in response:
            logger.info("SUCCESS: Response has been properly unwrapped")
            return True
        else:
            logger.error("FAILED: Response is missing required fields")
            return False
            
    except Exception as e:
        logger.error(f"Error testing GPT-4o-mini: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Run the GPT-4o-mini schema test."""
    logger.info("Starting GPT-4o-mini schema test")
    
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set. Please set it in .env file or environment.")
        return
    
    success = await test_gpt4o_mini_schema()
    
    # Print summary
    logger.info("\n===== TEST SUMMARY =====")
    logger.info(f"GPT-4o-mini schema unwrapping: {'✅ PASSED' if success else '❌ FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())