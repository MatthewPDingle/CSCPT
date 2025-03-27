"""
Example script demonstrating the use of the Google Gemini provider.

This script shows how to use the Gemini provider for:
1. Basic text completion
2. JSON-structured responses
3. Extended thinking/reasoning

To use this example:
1. Set your Gemini API key in the .env file or as an environment variable
2. Run this script

Required environment variables:
- GEMINI_API_KEY: Your Google Gemini API key
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

async def basic_completion():
    """Demonstrate basic text completion with Gemini."""
    llm_service = LLMService()
    
    system_prompt = "You are a helpful assistant for poker strategy."
    user_prompt = "What's the probability of flopping a flush when holding two suited cards?"
    
    try:
        response = await llm_service.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            provider="gemini"
        )
        
        print("\n=== Basic Completion ===")
        print(f"Q: {user_prompt}")
        print(f"A: {response}")
        
    except Exception as e:
        logger.error(f"Error in basic completion: {str(e)}")

async def json_completion():
    """Demonstrate JSON-structured completion with Gemini."""
    llm_service = LLMService()
    
    system_prompt = "You are a poker hand analyzer."
    user_prompt = "Analyze this poker hand: Player A has Ace-King suited, Player B has pocket Queens. The flop is A-Q-5 rainbow."
    
    # Define a JSON schema for the response
    json_schema = {
        "type": "object",
        "properties": {
            "player_a": {
                "type": "object",
                "properties": {
                    "hand": {"type": "string"},
                    "hand_strength": {"type": "string"},
                    "equity_percentage": {"type": "number"},
                    "potential_draws": {"type": "array", "items": {"type": "string"}}
                }
            },
            "player_b": {
                "type": "object",
                "properties": {
                    "hand": {"type": "string"},
                    "hand_strength": {"type": "string"},
                    "equity_percentage": {"type": "number"},
                    "potential_draws": {"type": "array", "items": {"type": "string"}}
                }
            },
            "analysis": {"type": "string"}
        }
    }
    
    try:
        response = await llm_service.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema=json_schema,
            provider="gemini"
        )
        
        print("\n=== JSON Completion ===")
        print(f"Q: {user_prompt}")
        print(f"A: {json.dumps(response, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error in JSON completion: {str(e)}")

async def extended_thinking_completion():
    """Demonstrate extended thinking/reasoning with Gemini."""
    llm_service = LLMService()
    
    system_prompt = "You are a poker strategy coach teaching about complex situations."
    user_prompt = "In a 6-max No-Limit Hold'em game, I'm in the cutoff with J♥T♥. The UTG player raises to 3BB, and the player in the hijack calls. What should I do and why?"
    
    try:
        response = await llm_service.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            provider="gemini",
            extended_thinking=True  # Enable extended thinking
        )
        
        print("\n=== Extended Thinking Completion ===")
        print(f"Q: {user_prompt}")
        print(f"A: {response}")
        
    except Exception as e:
        logger.error(f"Error in extended thinking completion: {str(e)}")

async def comparison_test():
    """Compare the different model options for Gemini."""
    llm_service = LLMService()
    
    system_prompt = "You are a poker expert analyzing a difficult decision."
    user_prompt = "Should I call an all-in bet with AK suited when facing a tight player who has QQ on a board of A-7-2 rainbow?"
    
    models = ["gemini-2.5-pro", "gemini-2.0-flash", "gemini-2.0-flash-thinking"]
    
    for model in models:
        # We need to modify config for each test
        if llm_service.ai_config and "gemini" in llm_service.ai_config.config:
            original_model = llm_service.ai_config.config["gemini"]["model"]
            llm_service.ai_config.config["gemini"]["model"] = model
            # Clear any cached provider
            if "gemini" in llm_service.providers:
                del llm_service.providers["gemini"]
        
        try:
            print(f"\n=== Model: {model} ===")
            response = await llm_service.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                provider="gemini",
                extended_thinking=True  # Try with extended thinking for all models
            )
            
            print(f"Q: {user_prompt}")
            print(f"A: {response}")
            
        except Exception as e:
            logger.error(f"Error with model {model}: {str(e)}")
        
        # Restore original model setting
        if llm_service.ai_config and "gemini" in llm_service.ai_config.config:
            llm_service.ai_config.config["gemini"]["model"] = original_model
            # Clear the cached provider
            if "gemini" in llm_service.providers:
                del llm_service.providers["gemini"]

async def main():
    """Run all the examples."""
    logger.info("Starting Gemini API examples")
    
    if not os.environ.get("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable not set. Please set it in .env file or environment.")
        return
    
    await basic_completion()
    await json_completion()
    await extended_thinking_completion()
    await comparison_test()
    
    logger.info("Completed all examples")

if __name__ == "__main__":
    asyncio.run(main())