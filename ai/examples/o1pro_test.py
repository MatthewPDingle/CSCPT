"""
Simple test script for o1-pro using the Responses API.
"""

import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_o1_pro_responses():
    """Test o1-pro with the Responses API"""
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return
    
    client = OpenAI(api_key=api_key)
    
    # Test 1: Basic completion
    logger.info("Testing o1-pro with basic completion")
    try:
        response = client.responses.create(
            model="o1-pro",
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": "You are a helpful assistant that provides very brief responses."}]
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": "What is the capital of France? Respond in one word."}]
                }
            ]
        )
        
        # Try to extract the response
        logger.info(f"Response: {response}")
        for item in response.output:
            if hasattr(item, 'content'):
                for content in item.content:
                    if hasattr(content, 'text'):
                        logger.info(f"Output text: {content.text}")
    
    except Exception as e:
        logger.error(f"Error with basic completion: {str(e)}")
    
    # Test 2: With reasoning 
    logger.info("\nTesting o1-pro with reasoning")
    try:
        response = client.responses.create(
            model="o1-pro",
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": "You are a chess assistant."}]
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": "In chess, if I have a knight on f3 and a bishop on c1, what are my options to develop my position?"}]
                }
            ],
            reasoning={"effort": "high"}
        )
        
        # Try to extract the response
        logger.info(f"Response: {response}")
        for item in response.output:
            if hasattr(item, 'content'):
                for content in item.content:
                    if hasattr(content, 'text'):
                        logger.info(f"Output text: {content.text}")
    
    except Exception as e:
        logger.error(f"Error with reasoning: {str(e)}")
    
    # Test 3: JSON output
    logger.info("\nTesting o1-pro with JSON output")
    try:
        response = client.responses.create(
            model="o1-pro",
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": "You are a helpful assistant. Provide responses in JSON format with fields 'city', 'country', and 'facts'."}]
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": "What is the capital of France and what is it known for?"}]
                }
            ],
            # tools parameter removed since it's not supported by all accounts
        )
        
        # Try to extract the response
        logger.info(f"Response: {response}")
        for item in response.output:
            if hasattr(item, 'content'):
                for content in item.content:
                    if hasattr(content, 'text'):
                        logger.info(f"Output text: {content.text}")
    
    except Exception as e:
        logger.error(f"Error with JSON output: {str(e)}")

if __name__ == "__main__":
    test_o1_pro_responses()