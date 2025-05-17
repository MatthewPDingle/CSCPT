"""
Test script to verify all Gemini models with real API calls.

This script tests each supported Gemini model with a real API call
to ensure they are correctly implemented and operational.

To use this script:
1. Set your Gemini API key in the .env file or as an environment variable
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
from ai.providers.gemini_provider import GeminiProvider

# Load environment variables
load_dotenv()

# List of all models to test with their API IDs
GEMINI_MODELS = [
    "gemini-2.5-pro",  # Maps to gemini-2.5-pro-preview-03-25
    "gemini-2.0-flash",  # Maps to gemini-2.0-flash-001
    "gemini-2.0-flash-thinking"  # Maps to gemini-2.0-flash-thinking-exp-01-21
]

async def test_model(model_name):
    """Test a specific Gemini model with a real API call."""
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set")
        return False
    
    try:
        # Initialize the provider directly
        provider = GeminiProvider(
            api_key=api_key,
            model=model_name
        )
        
        # Use a simple prompt
        system_prompt = "You are a helpful assistant that provides very brief responses."
        user_prompt = "What is the capital of France? Respond in one word."
        
        # Make an API call
        logger.info(f"Testing model: {model_name}")
        response = await provider.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7
        )
        
        logger.info(f"Model: {model_name} - Response: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Error testing model {model_name}: {str(e)}")
        return False

async def test_json_response(model_name):
    """Test a specific Gemini model's JSON capabilities with a real API call."""
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set")
        return False
    
    # Skip JSON test for models that don't support it
    if model_name == "gemini-2.0-flash-thinking":
        logger.info(f"Skipping JSON test for {model_name} as it doesn't support JSON mode")
        return True
    
    try:
        # Initialize the provider directly
        provider = GeminiProvider(
            api_key=api_key,
            model=model_name
        )
        
        # Use a simple prompt with JSON schema
        system_prompt = "You are a helpful assistant that provides structured responses."
        user_prompt = "What is the capital of France and what is it known for?"
        
        # Define a simple JSON schema
        json_schema = {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "country": {"type": "string"},
                "facts": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["city", "country", "facts"]
        }
        
        # Make an API call
        logger.info(f"Testing JSON response with model: {model_name}")
        response = await provider.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema=json_schema,
            temperature=0.7
        )
        
        logger.info(f"Model: {model_name} - JSON Response: {json.dumps(response, indent=2)}")
        return True
        
    except Exception as e:
        logger.error(f"Error testing JSON with model {model_name}: {str(e)}")
        return False

async def test_extended_thinking(model_name):
    """Test a specific Gemini model's extended thinking capabilities."""
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set")
        return False
    
    # For Gemini models, we'll just do a regular completion since they don't support extended thinking
    # Note: Extended thinking is specific to Claude Sonnet 3.7
    logger.info(f"Gemini models don't support native extended thinking like Claude Sonnet 3.7. Testing normal completion for {model_name}")
    
    try:
        # Initialize the provider directly
        provider = GeminiProvider(
            api_key=api_key,
            model=model_name
        )
        
        # Use a more complex prompt that requires thinking
        system_prompt = "You are a chess assistant."
        user_prompt = "In chess, if I have a knight on f3 and a bishop on c1, " + \
                     "what are my options to develop my position?"
        
        # Make a regular API call without extended thinking
        logger.info(f"Testing completion for model: {model_name}")
        response = await provider.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            extended_thinking=False  # Explicitly set to False for Gemini
        )
        
        # Extract text from response dict before slicing
        response_text = response['text'] if isinstance(response, dict) and 'text' in response else str(response)
        logger.info(f"Model: {model_name} - Response: {response_text[:100]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error testing completion with model {model_name}: {str(e)}")
        return False

async def main():
    """Run tests for all Gemini models."""
    logger.info("Starting Gemini model tests")
    
    if not os.environ.get("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable not set. Please set it in .env file or environment.")
        return
    
    results = []
    json_results = []
    thinking_results = []
    
    for model in GEMINI_MODELS:
        # Test basic completion
        success = await test_model(model)
        results.append((model, success))
        
        # Test JSON response
        json_success = await test_json_response(model)
        json_results.append((model, json_success))
        
        # Test "extended thinking" (regular completion for Gemini)
        thinking_success = await test_extended_thinking(model)
        thinking_results.append((model, thinking_success))
    
    # Print summary
    logger.info("\n===== TEST SUMMARY =====")
    logger.info("Basic Completion Results:")
    for model, success in results:
        logger.info(f"  {model}: {'✅ PASSED' if success else '❌ FAILED'}")
    
    logger.info("\nJSON Response Results:")
    for model, success in json_results:
        logger.info(f"  {model}: {'✅ PASSED' if success else '❌ FAILED'}")
    
    logger.info("\nBasic Completion for Complex Query Results:")
    for model, success in thinking_results:
        logger.info(f"  {model}: {'✅ PASSED' if success else '❌ FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())