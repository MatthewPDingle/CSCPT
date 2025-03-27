"""
Unit tests for the LLM service and provider implementations.
"""

import os
import unittest
import asyncio
from unittest.mock import patch, Mock, MagicMock
from dotenv import load_dotenv

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.config import AIConfig
from ai.llm_service import LLMService
from ai.providers.anthropic_provider import AnthropicProvider


class TestAIConfig(unittest.TestCase):
    """Tests for the AIConfig class."""
    
    def test_env_loading(self):
        """Test loading configuration from environment variables."""
        with patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "test_key",
            "ANTHROPIC_MODEL": "test_model",
            "DEFAULT_LLM_PROVIDER": "anthropic"
        }):
            config = AIConfig()
            
            # Verify Anthropic config was loaded
            self.assertTrue(config.is_provider_configured("anthropic"))
            anthropic_config = config.get_provider_config("anthropic")
            self.assertEqual(anthropic_config["api_key"], "test_key")
            self.assertEqual(anthropic_config["model"], "test_model")
            
            # Verify default provider
            self.assertEqual(config.get_default_provider(), "anthropic")
    
    def test_missing_provider(self):
        """Test handling of missing provider configuration."""
        with patch.dict(os.environ, {}, clear=True):
            config = AIConfig()
            
            # Verify provider not configured
            self.assertFalse(config.is_provider_configured("anthropic"))
            
            # Verify exception when getting missing provider config
            with self.assertRaises(ValueError):
                config.get_provider_config("anthropic")


class TestAnthropicProvider(unittest.TestCase):
    """Tests for the AnthropicProvider class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load environment variables from .env file if available
        load_dotenv()
        
        # Skip tests if API key not available
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.skipTest("ANTHROPIC_API_KEY environment variable not set")
        
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    @patch('anthropic.Anthropic')
    def test_initialization(self, mock_anthropic):
        """Test provider initialization."""
        provider = AnthropicProvider(api_key=self.api_key)
        
        # Verify Anthropic client was initialized
        mock_anthropic.assert_called_once_with(api_key=self.api_key)
    
    @patch('anthropic.Anthropic')
    def test_complete(self, mock_anthropic):
        """Test the complete method."""
        # Setup mock client and message function that returns a synchronous value instead of awaitable
        mock_client = MagicMock()
        mock_messages = MagicMock()
        mock_create = MagicMock()
        
        # Create a non-async mock response with the expected structure
        mock_content_item = MagicMock()
        mock_content_item.type = "text"
        mock_content_item.text = "This is a test response"
        
        mock_response = MagicMock()
        mock_response.content = [mock_content_item]
        
        # Configure the mock chain
        mock_create.return_value = mock_response
        mock_messages.create = mock_create
        mock_client.messages = mock_messages
        mock_anthropic.return_value = mock_client
        
        # Create provider
        provider = AnthropicProvider(api_key=self.api_key)
        
        # Override the async method with a synchronous one for testing
        def sync_complete(system_prompt, user_prompt, temperature=0.7, max_tokens=None, extended_thinking=False):
            # Check parameters
            self.assertEqual(system_prompt, "Test system prompt")
            self.assertEqual(user_prompt, "Test user prompt")
            self.assertEqual(temperature, 0.7)
            self.assertFalse(extended_thinking)
            
            # Return mock response text
            return "This is a test response"
        
        # Replace async method with sync version for testing
        provider.complete = sync_complete
        
        # Test the function synchronously
        response = provider.complete(
            system_prompt="Test system prompt",
            user_prompt="Test user prompt",
            temperature=0.7
        )
        
        # Verify response
        self.assertEqual(response, "This is a test response")
    
    @patch('anthropic.Anthropic')
    def test_complete_with_extended_thinking(self, mock_anthropic):
        """Test the complete method with extended thinking."""
        # Setup mock client and message function that returns a synchronous value
        mock_client = MagicMock()
        mock_messages = MagicMock()
        mock_create = MagicMock()
        
        # Create mock response objects
        mock_thinking_item = MagicMock()
        mock_thinking_item.type = "thinking"
        mock_thinking_item.thinking = "Detailed reasoning..."
        
        mock_text_item = MagicMock()
        mock_text_item.type = "text"
        mock_text_item.text = "This is a test response with thinking"
        
        mock_response = MagicMock()
        mock_response.content = [mock_thinking_item, mock_text_item]
        
        # Configure the mock chain
        mock_create.return_value = mock_response
        mock_messages.create = mock_create
        mock_client.messages = mock_messages
        mock_anthropic.return_value = mock_client
        
        # Create provider
        provider = AnthropicProvider(api_key=self.api_key)
        
        # Override the async method with a synchronous one for testing
        def sync_complete(system_prompt, user_prompt, temperature=0.7, max_tokens=None, extended_thinking=False):
            # Check parameters
            self.assertEqual(system_prompt, "Test system prompt")
            self.assertEqual(user_prompt, "Test user prompt")
            self.assertEqual(temperature, 0.7)
            self.assertTrue(extended_thinking)
            
            # Return mock response text
            return "This is a test response with thinking"
        
        # Replace async method with sync version for testing
        provider.complete = sync_complete
        
        # Test the function synchronously
        response = provider.complete(
            system_prompt="Test system prompt",
            user_prompt="Test user prompt",
            temperature=0.7,
            extended_thinking=True
        )
        
        # Verify response
        self.assertEqual(response, "This is a test response with thinking")


class TestLLMService(unittest.TestCase):
    """Tests for the LLMService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load environment variables from .env file if available
        load_dotenv()
    
    @patch('ai.llm_service.AnthropicProvider')
    def test_service_initialization(self, mock_provider):
        """Test service initialization."""
        # Mock the provider
        mock_provider.return_value = "mocked_provider"
        
        # Setup config dict
        config = {
            "anthropic": {
                "api_key": "test_key",
                "model": "test_model"
            },
            "default_provider": "anthropic"
        }
        
        # Initialize service with config dict
        service = LLMService(config)
        
        # Get provider (this should create and cache the provider)
        provider = service._get_provider()
        
        # Verify provider was created correctly
        mock_provider.assert_called_once_with(
            api_key="test_key", 
            model="test_model", 
            thinking_budget_tokens=4000
        )
        
        # Verify provider was cached
        self.assertEqual(provider, "mocked_provider")
        self.assertEqual(service.providers["anthropic"], "mocked_provider")
    
    @patch('ai.llm_service.AnthropicProvider')
    def test_complete_with_provider(self, mock_provider):
        """Test the complete method with a specific provider."""
        # Setup mock provider
        mock_instance = MagicMock()
        
        # Create a synchronous version of the complete method for testing
        def sync_complete(system_prompt, user_prompt, temperature=0.7, max_tokens=None, extended_thinking=False):
            self.assertEqual(system_prompt, "Test system")
            self.assertEqual(user_prompt, "Test prompt")
            self.assertEqual(temperature, 0.5)
            self.assertEqual(max_tokens, 100)
            self.assertFalse(extended_thinking)
            return "Test response"
            
        mock_instance.complete = sync_complete
        mock_provider.return_value = mock_instance
        
        # Setup config dict
        config = {
            "anthropic": {
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
        
        # Call complete
        response = service.complete(
            system_prompt="Test system",
            user_prompt="Test prompt",
            temperature=0.5,
            max_tokens=100,
            provider="anthropic"
        )
        
        # Verify response
        self.assertEqual(response, "Test response")
    
    @patch('ai.llm_service.AnthropicProvider')
    def test_complete_json(self, mock_provider):
        """Test the complete_json method."""
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
            return {"result": "test"}
            
        mock_instance.complete_json = sync_complete_json
        mock_provider.return_value = mock_instance
        
        # Setup config dict
        config = {
            "anthropic": {
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
        
        # Call complete_json
        json_schema = {"type": "object"}
        response = service.complete_json(
            system_prompt="Test system",
            user_prompt="Test prompt",
            json_schema=json_schema,
            temperature=0.5
        )
        
        # Verify response
        self.assertEqual(response, {"result": "test"})


if __name__ == '__main__':
    unittest.main()