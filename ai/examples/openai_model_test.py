"""
Test script to verify all OpenAI models with real API calls.

This script tests each supported OpenAI model with a real API call
to ensure they are correctly implemented and operational.

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
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the service module
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.llm_service import LLMService
from ai.providers.openai_provider import OpenAIProvider

# Load environment variables
load_dotenv()

# List of all models to test
OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4.5-preview",
    "o1-pro",  # Now supported using the Responses API
    "o3-mini",
    "o4-mini"
]

# Which model tests to run (set via command line argument)
MODEL_TO_TEST = None
if len(sys.argv) > 1 and sys.argv[1] in OPENAI_MODELS:
    MODEL_TO_TEST = sys.argv[1]
    logger.info(f"Only testing model: {MODEL_TO_TEST}")
    OPENAI_MODELS = [MODEL_TO_TEST]

async def test_model(model_name):
    """Test a specific OpenAI model with a real API call."""
    api_key = os.environ.get("OPENAI_API_KEY")
    organization_id = os.environ.get("OPENAI_ORGANIZATION_ID")
    
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        return False
    
    try:
        # Initialize the provider directly with low reasoning level for reasoning models
        reasoning_level = "low" if model_name in ["o1-pro", "o3-mini", "o4-mini"] else "medium"
        provider = OpenAIProvider(
            api_key=api_key,
            model=model_name,
            reasoning_level=reasoning_level,
            organization_id=organization_id
        )
        
        # Use a simple prompt
        system_prompt = "You are a helpful assistant that provides very brief responses."
        user_prompt = "What is the capital of France? Respond in one word."
        
        # Make an API call - note that o3-mini doesn't support temperature
        logger.info(f"Testing model: {model_name}")
        response = await provider.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7 if model_name not in ["o3-mini", "o4-mini"] else None
        )
        
        logger.info(f"Model: {model_name} - Response: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Error testing model {model_name}: {str(e)}")
        return False

async def test_json_response(model_name):
    """Test a specific OpenAI model's JSON capabilities with a real API call."""
    api_key = os.environ.get("OPENAI_API_KEY")
    organization_id = os.environ.get("OPENAI_ORGANIZATION_ID")
    
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        return False
    
    try:
        # Initialize the provider directly with low reasoning level for reasoning models
        reasoning_level = "low" if model_name in ["o1-pro", "o3-mini", "o4-mini"] else "medium"
        provider = OpenAIProvider(
            api_key=api_key,
            model=model_name,
            reasoning_level=reasoning_level,
            organization_id=organization_id
        )
        
        # Use a simple prompt with JSON schema
        system_prompt = "You are a helpful assistant that provides structured responses. Please format your response as a JSON object with the fields 'city', 'country', and 'facts'."
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
        
        # Make an API call - note that o1-pro models need explicit JSON instructions
        logger.info(f"Testing JSON response with model: {model_name}")
        response = await provider.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema=json_schema,
            temperature=0.7 if model_name not in ["o3-mini", "o4-mini"] else None
        )
        
        logger.info(f"Model: {model_name} - JSON Response: {json.dumps(response, indent=2)}")
        return True
        
    except Exception as e:
        logger.error(f"Error testing JSON with model {model_name}: {str(e)}")
        return False

async def test_extended_thinking(model_name):
    """Test a specific OpenAI model's extended thinking capabilities."""
    api_key = os.environ.get("OPENAI_API_KEY")
    organization_id = os.environ.get("OPENAI_ORGANIZATION_ID")
    
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        return False
    
    try:
        # Initialize the provider directly with low reasoning level for reasoning models
        reasoning_level = "low" if model_name in ["o1-pro", "o3-mini", "o4-mini"] else "medium"
        provider = OpenAIProvider(
            api_key=api_key,
            model=model_name,
            reasoning_level=reasoning_level,
            organization_id=organization_id
        )
        
        # Use a more complex prompt that requires thinking
        system_prompt = "You are a chess assistant."
        user_prompt = "In chess, if I have a knight on f3 and a bishop on c1, " + \
                     "what are my options to develop my position?"
        
        # Make an API call with extended thinking
        logger.info(f"Testing extended thinking with model: {model_name}")
        response = await provider.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7 if model_name not in ["o3-mini", "o4-mini"] else None,
            extended_thinking=True
        )
        
        # Truncate the response if it's too long
        response_preview = response[:100] + "..." if len(response) > 100 else response
        logger.info(f"Model: {model_name} - Extended thinking response (truncated): {response_preview}")
        return True
        
    except Exception as e:
        logger.error(f"Error testing extended thinking with model {model_name}: {str(e)}")
        return False

async def main():
    """Run tests for all OpenAI models."""
    logger.info("Starting OpenAI model tests")
    
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set. Please set it in .env file or environment.")
        return
    
    results = []
    json_results = []
    thinking_results = []
    
    for model in OPENAI_MODELS:
        # Test basic completion
        success = await test_model(model)
        results.append((model, success))
        
        # Test JSON response
        json_success = await test_json_response(model)
        json_results.append((model, json_success))
        
        # Test extended thinking (o3-mini supports this natively, others use prompt enhancement)
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
    
    logger.info("\nExtended Thinking Results:")
    for model, success in thinking_results:
        logger.info(f"  {model}: {'✅ PASSED' if success else '❌ FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())