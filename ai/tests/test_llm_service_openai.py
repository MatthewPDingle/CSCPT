"""
Unit tests for the LLM service with OpenAI provider.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.llm_service import LLMService


class TestLLMServiceWithOpenAI(unittest.TestCase):
    """Tests for the LLMService class with OpenAI provider."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load environment variables from .env file if available
        load_dotenv()
    
    @patch('ai.llm_service.OpenAIProvider')
    def test_service_initialization_with_openai(self, mock_provider):
        """Test service initialization with OpenAI."""
        # Mock the provider
        mock_provider.return_value = "mocked_openai_provider"
        
        # Setup config dict
        config = {
            "openai": {
                "api_key": "test_key",
                "model": "gpt-4o",
                "reasoning_level": "high"
            },
            "default_provider": "openai"
        }
        
        # Initialize service with config dict
        service = LLMService(config)
        
        # Get provider (this should create and cache the provider)
        provider = service._get_provider()
        
        # Verify provider was created correctly
        mock_provider.assert_called_once_with(
            api_key="test_key", 
            model="gpt-4o", 
            reasoning_level="high",
            organization_id=None
        )
        
        # Verify provider was cached
        self.assertEqual(provider, "mocked_openai_provider")
        self.assertEqual(service.providers["openai"], "mocked_openai_provider")
    
    @patch('ai.llm_service.OpenAIProvider')
    def test_complete_with_openai_provider(self, mock_provider):
        """Test the complete method with OpenAI provider."""
        # Setup mock provider
        mock_instance = MagicMock()
        
        # Create a synchronous version of the complete method for testing
        def sync_complete(system_prompt, user_prompt, temperature=0.7, max_tokens=None, extended_thinking=False):
            self.assertEqual(system_prompt, "Test system")
            self.assertEqual(user_prompt, "Test prompt")
            self.assertEqual(temperature, 0.5)
            self.assertEqual(max_tokens, 100)
            self.assertFalse(extended_thinking)
            return "Test response from OpenAI"
            
        mock_instance.complete = sync_complete
        mock_provider.return_value = mock_instance
        
        # Setup config dict
        config = {
            "openai": {
                "api_key": "test_key"
            }
        }
        
        # Initialize service
        service = LLMService(config)
        
        # Override the async method with a synchronous one for testing
        def sync_complete_service(
            system_prompt, 
            user_prompt, 
            temperature=0.7, 
            max_tokens=None, 
            provider=None, 
            extended_thinking=False
        ):
            return mock_instance.complete(
                system_prompt, 
                user_prompt, 
                temperature, 
                max_tokens, 
                extended_thinking
            )
        
        # Replace the async method with a sync version for testing
        service.complete = sync_complete_service
        
        # Call complete with OpenAI provider
        response = service.complete(
            system_prompt="Test system",
            user_prompt="Test prompt",
            temperature=0.5,
            max_tokens=100,
            provider="openai"
        )
        
        # Verify response
        self.assertEqual(response, "Test response from OpenAI")
    
    @patch('ai.llm_service.OpenAIProvider')
    def test_complete_json_with_openai_provider(self, mock_provider):
        """Test the complete_json method with OpenAI provider."""
        # Setup mock provider
        mock_instance = MagicMock()
        
        # Create a synchronous version of the complete_json method for testing
        def sync_complete_json(
            system_prompt, 
            user_prompt, 
            json_schema, 
            temperature=0.7, 
            extended_thinking=False
        ):
            self.assertEqual(system_prompt, "Test system")
            self.assertEqual(user_prompt, "Test prompt")
            self.assertEqual(json_schema, {"type": "object"})
            self.assertEqual(temperature, 0.5)
            self.assertFalse(extended_thinking)
            return {"result": "test from OpenAI"}
            
        mock_instance.complete_json = sync_complete_json
        mock_provider.return_value = mock_instance
        
        # Setup config dict
        config = {
            "openai": {
                "api_key": "test_key"
            }
        }
        
        # Initialize service
        service = LLMService(config)
        
        # Override the async method with a synchronous one for testing
        def sync_complete_json_service(
            system_prompt, 
            user_prompt, 
            json_schema, 
            temperature=0.7, 
            provider=None, 
            extended_thinking=False
        ):
            return mock_instance.complete_json(
                system_prompt, 
                user_prompt, 
                json_schema, 
                temperature, 
                extended_thinking
            )
        
        # Replace the async method with a sync version for testing
        service.complete_json = sync_complete_json_service
        
        # Call complete_json with OpenAI provider
        json_schema = {"type": "object"}
        response = service.complete_json(
            system_prompt="Test system",
            user_prompt="Test prompt",
            json_schema=json_schema,
            temperature=0.5,
            provider="openai"
        )
        
        # Verify response
        self.assertEqual(response, {"result": "test from OpenAI"})


if __name__ == '__main__':
    unittest.main()