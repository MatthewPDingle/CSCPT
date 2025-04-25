"""
Unit tests for the LLM service with Gemini provider.
"""

import unittest
import os
import json
from unittest.mock import patch, MagicMock

import sys
import asyncio
from typing import Dict, Any

# Ensure paths are correct for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.llm_service import LLMService
from ai.providers.gemini_provider import GeminiProvider


class TestLLMServiceGemini(unittest.TestCase):
    """Test cases for LLM service with Gemini provider."""
    
    # Constants for model testing
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_0_FLASH_THINKING = "gemini-2.0-flash-thinking"
    # New flash preview model
    GEMINI_2_5_FLASH = "gemini-2.5-flash-preview-04-17"
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks
        self.provider_mock = MagicMock(spec=GeminiProvider)
        self.provider_mock.complete.return_value = "Test response"
        self.provider_mock.complete_json.return_value = {"result": "test"}
        
        # Mock the GeminiProvider class
        self.provider_class_patch = patch('ai.llm_service.GeminiProvider', return_value=self.provider_mock)
        self.provider_class_mock = self.provider_class_patch.start()
        
        # Create configuration with test values
        self.config = {
            "gemini": {
                "api_key": "test_key",
                "model": "gemini-2.5-pro",
                "generation_config": {
                    "temperature": 0.8,
                    "top_p": 0.9
                }
            },
            "default_provider": "gemini"
        }
        
        # Create service instance
        self.service = LLMService(config=self.config)
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.provider_class_patch.stop()
    
    def test_all_model_initializations(self):
        """Test that all Gemini models are initialized correctly with the service."""
        # Models to test
        models = [
            self.GEMINI_2_5_PRO,
            self.GEMINI_2_5_FLASH,
            self.GEMINI_2_0_FLASH,
            self.GEMINI_2_0_FLASH_THINKING
        ]
        
        for model in models:
            # Create a new configuration with this model
            config = {
                "gemini": {
                    "api_key": "test_key",
                    "model": model,
                    "generation_config": {"temperature": 0.8, "top_p": 0.9}
                },
                "default_provider": "gemini"
            }
            
            # Reset the mock
            self.provider_class_mock.reset_mock()
            
            # Create a new service with this config
            service = LLMService(config=config)
            
            # Get the provider (this should initialize it)
            provider = service._get_provider("gemini")
            
            # Check that the provider class was called with the correct args
            self.provider_class_mock.assert_called_once_with(
                api_key="test_key",
                model=model,
                generation_config={"temperature": 0.8, "top_p": 0.9}
            )
            
            # Check that we got the mock provider
            self.assertEqual(provider, self.provider_mock)
            
            print(f"Verified LLM service integration with model: {model}")
    
    def test_provider_initialization(self):
        """Test that the Gemini provider is initialized correctly with default model."""
        # Get the provider (this should initialize it)
        provider = self.service._get_provider("gemini")
        
        # Check that the provider class was called with the correct args
        self.provider_class_mock.assert_called_once_with(
            api_key="test_key",
            model="gemini-2.5-pro",
            generation_config={"temperature": 0.8, "top_p": 0.9}
        )
        
        # Check that we got the mock provider
        self.assertEqual(provider, self.provider_mock)
    
    def test_default_provider(self):
        """Test that Gemini is used as the default provider when configured."""
        # Get the default provider
        provider = self.service._get_provider()
        
        # Should be the Gemini provider
        self.assertEqual(provider, self.provider_mock)
    
    def test_complete(self):
        """Test the complete method with Gemini provider."""
        # Run the complete method
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.service.complete(
            system_prompt="Test system",
            user_prompt="Test user",
            temperature=0.7,
            provider="gemini"
        ))
        
        # Check that the provider's complete method was called correctly
        self.provider_mock.complete.assert_called_once_with(
            system_prompt="Test system",
            user_prompt="Test user",
            temperature=0.7,
            max_tokens=None,
            extended_thinking=False
        )
        
        # Check the response
        self.assertEqual(response, "Test response")
    
    def test_complete_json(self):
        """Test the complete_json method with Gemini provider."""
        # Define a test schema
        schema = {"type": "object", "properties": {"result": {"type": "string"}}}
        
        # Run the complete_json method
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.service.complete_json(
            system_prompt="Test system",
            user_prompt="Test user",
            json_schema=schema,
            provider="gemini"
        ))
        
        # Check that the provider's complete_json method was called correctly
        self.provider_mock.complete_json.assert_called_once_with(
            system_prompt="Test system",
            user_prompt="Test user",
            json_schema=schema,
            temperature=None,
            extended_thinking=False
        )
        
        # Check the response
        self.assertEqual(response, {"result": "test"})
    
    def test_extended_thinking_all_models(self):
        """Test extended thinking integration with all models."""
        # Models to test
        models = [self.GEMINI_2_5_PRO, self.GEMINI_2_0_FLASH, self.GEMINI_2_0_FLASH_THINKING]
        
        for model in models:
            # Create a new configuration with this model
            config = {
                "gemini": {
                    "api_key": "test_key",
                    "model": model,
                    "generation_config": {"temperature": 0.8, "top_p": 0.9}
                },
                "default_provider": "gemini"
            }
            
            # Reset the mock
            self.provider_mock.reset_mock()
            self.provider_class_mock.reset_mock()
            
            # Create a new service with this config
            service = LLMService(config=config)
            
            # Run the complete method with extended thinking
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(service.complete(
                system_prompt="Test system",
                user_prompt="Test user",
                provider="gemini",
                extended_thinking=True
            ))
            
            # Check that extended_thinking was passed to the provider
            call_kwargs = self.provider_mock.complete.call_args[1]
            self.assertTrue(call_kwargs["extended_thinking"])
            
            print(f"Verified extended thinking with model: {model}")
            
            # Do the same test with JSON completion
            json_schema = {"type": "object", "properties": {"result": {"type": "string"}}}
            self.provider_mock.reset_mock()
            
            response = loop.run_until_complete(service.complete_json(
                system_prompt="Test system",
                user_prompt="Test user",
                json_schema=json_schema,
                provider="gemini",
                extended_thinking=True
            ))
            
            # Check that extended_thinking was passed to the provider
            call_kwargs = self.provider_mock.complete_json.call_args[1]
            self.assertTrue(call_kwargs["extended_thinking"])
            
            print(f"Verified extended thinking JSON with model: {model}")
    
    def test_extended_thinking(self):
        """Test the complete method with extended thinking enabled."""
        # Run the complete method with extended thinking
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.service.complete(
            system_prompt="Test system",
            user_prompt="Test user",
            provider="gemini",
            extended_thinking=True
        ))
        
        # Check that extended_thinking was passed to the provider
        call_kwargs = self.provider_mock.complete.call_args[1]
        self.assertTrue(call_kwargs["extended_thinking"])


# Helper function to run tests synchronously
def run_sync_test(async_func):
    """Run an async test function synchronously."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_func)


if __name__ == "__main__":
    unittest.main()