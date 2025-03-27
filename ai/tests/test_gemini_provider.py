"""
Unit tests for the Gemini provider.
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

from ai.providers.gemini_provider import GeminiProvider


class TestGeminiProvider(unittest.TestCase):
    """Test cases for the Gemini provider."""
    
    # Constants for model testing
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_PRO_ID = "gemini-2.5-pro-exp-03-25"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_0_FLASH_ID = "gemini-2.0-flash-001"
    GEMINI_2_0_FLASH_THINKING = "gemini-2.0-flash-thinking"
    GEMINI_2_0_FLASH_THINKING_ID = "gemini-2.0-flash-thinking-exp-01-21"
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_key"
        self.default_model = "gemini-2.5-pro"
        
        # Mock the entire google.generativeai module
        self.genai_mock = MagicMock()
        self.model_mock = MagicMock()
        self.chat_mock = MagicMock()
        
        # Set up response for the chat mock
        self.chat_mock.send_message.return_value.text = "This is a test response"
        
        # Set up model mock to return the chat mock
        self.model_mock.start_chat.return_value = self.chat_mock
        
        # Set up genai mock to return the model mock
        self.genai_mock.GenerativeModel.return_value = self.model_mock
        
        # Apply the mock
        self.module_patcher = patch.dict('sys.modules', {
            'google.generativeai': self.genai_mock
        })
        self.module_patcher.start()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.module_patcher.stop()
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        provider = GeminiProvider(api_key=self.api_key)
        
        # Check that the API was configured
        self.genai_mock.configure.assert_called_once_with(api_key=self.api_key)
        
        # Check that the model was initialized correctly
        self.genai_mock.GenerativeModel.assert_called_once()
        model_call_kwargs = self.genai_mock.GenerativeModel.call_args[1]
        self.assertEqual(model_call_kwargs['model_name'], "gemini-2.5-pro-exp-03-25")
    
    def test_all_model_configurations(self):
        """Test initialization with all supported model configurations."""
        # Test each model configuration
        models_to_test = [
            (self.GEMINI_2_5_PRO, self.GEMINI_2_5_PRO_ID, True),  # model name, expected ID, supports_reasoning
            (self.GEMINI_2_0_FLASH, self.GEMINI_2_0_FLASH_ID, False),
            (self.GEMINI_2_0_FLASH_THINKING, self.GEMINI_2_0_FLASH_THINKING_ID, True)
        ]
        
        for model_name, expected_id, supports_reasoning in models_to_test:
            # Reset mocks for each iteration
            self.genai_mock.GenerativeModel.reset_mock()
            
            # Initialize with this model
            provider = GeminiProvider(api_key=self.api_key, model=model_name)
            
            # Check the model was initialized correctly with the proper ID
            model_call_kwargs = self.genai_mock.GenerativeModel.call_args[1]
            self.assertEqual(model_call_kwargs['model_name'], expected_id)
            
            # Check that supports_reasoning was set correctly
            self.assertEqual(provider.supports_reasoning, supports_reasoning)
            
            # Print verification
            print(f"Verified model: {model_name} -> {expected_id}, supports_reasoning={supports_reasoning}")
    
    def test_init_with_custom_model(self):
        """Test initialization with a specific custom model."""
        custom_model = self.GEMINI_2_0_FLASH
        provider = GeminiProvider(api_key=self.api_key, model=custom_model)
        
        # Check the model was initialized correctly
        model_call_kwargs = self.genai_mock.GenerativeModel.call_args[1]
        self.assertEqual(model_call_kwargs['model_name'], self.GEMINI_2_0_FLASH_ID)
    
    def test_init_with_custom_generation_config(self):
        """Test initialization with custom generation config."""
        custom_config = {
            "temperature": 0.9,
            "top_p": 0.8,
            "max_output_tokens": 2000
        }
        
        provider = GeminiProvider(
            api_key=self.api_key,
            generation_config=custom_config
        )
        
        # Check that the generation config was applied
        model_call_kwargs = self.genai_mock.GenerativeModel.call_args[1]
        generation_config = model_call_kwargs['generation_config']
        
        self.assertEqual(generation_config["temperature"], 0.9)
        self.assertEqual(generation_config["top_p"], 0.8)
        self.assertEqual(generation_config["max_output_tokens"], 2000)
    
    def test_init_with_invalid_model(self):
        """Test initialization with an invalid model name."""
        invalid_model = "nonexistent-model"
        provider = GeminiProvider(api_key=self.api_key, model=invalid_model)
        
        # Should fall back to the default model
        model_call_kwargs = self.genai_mock.GenerativeModel.call_args[1]
        self.assertEqual(model_call_kwargs['model_name'], "gemini-2.5-pro-exp-03-25")
    
    def test_complete(self):
        """Test the complete method."""
        provider = GeminiProvider(api_key=self.api_key)
        
        # Reset any initialization calls to start_chat
        self.model_mock.reset_mock()
        
        # Run the complete method (need to handle async)
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(provider.complete(
            system_prompt="You are a test assistant",
            user_prompt="This is a test",
            temperature=0.8
        ))
        
        # Check that at least one call was made to start_chat with the system prompt
        self.model_mock.start_chat.assert_called()
        chat_args = self.model_mock.start_chat.call_args[1]
        self.assertEqual(chat_args["system_instruction"], "You are a test assistant")
        
        # Check that the user message was sent
        self.chat_mock.send_message.assert_called_once_with("This is a test")
        
        # Check the response
        self.assertEqual(response, "This is a test response")
    
    def test_extended_thinking_all_models(self):
        """Test extended thinking capability with all supported models."""
        # Set up a reasoned response format
        reasoning_response = (
            "Reasoning: Here's my step-by-step reasoning...\n\n"
            "1. First point\n2. Second point\n\n"
            "Response: This is the final reasoned answer."
        )
        self.chat_mock.send_message.return_value.text = reasoning_response
        
        # Test each model's extended thinking capability
        models_to_test = [
            (self.GEMINI_2_5_PRO, True),  # model name, supports_reasoning
            (self.GEMINI_2_0_FLASH, False),
            (self.GEMINI_2_0_FLASH_THINKING, True)
        ]
        
        for model_name, supports_reasoning in models_to_test:
            # Reset mocks
            self.genai_mock.reset_mock()
            self.model_mock.reset_mock()
            self.chat_mock.reset_mock()
            
            # Create provider with this model
            provider = GeminiProvider(api_key=self.api_key, model=model_name)
            
            # Verify the provider has the correct supports_reasoning value
            self.assertEqual(provider.supports_reasoning, supports_reasoning)
            
            # Run complete with extended thinking
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(provider.complete(
                system_prompt="You are a test assistant",
                user_prompt="This is a test",
                extended_thinking=True
            ))
            
            # For models that support reasoning, verify the response extraction
            if supports_reasoning:
                self.assertEqual(response, "This is the final reasoned answer.")
            else:
                # For models that don't support reasoning, just verify the response is returned
                self.assertEqual(response, reasoning_response)
            
            print(f"Tested extended thinking for {model_name}, supports_reasoning={supports_reasoning}")
    
    def test_complete_with_extended_thinking(self):
        """Test the complete method with extended thinking for the default model."""
        # Set up a more complex response for reasoning
        reasoning_response = (
            "Reasoning: Here's my step-by-step reasoning...\n\n"
            "1. First point\n2. Second point\n\n"
            "Response: This is the final reasoned answer."
        )
        self.chat_mock.send_message.return_value.text = reasoning_response
        
        provider = GeminiProvider(api_key=self.api_key)
        
        # Run the complete method with extended thinking
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(provider.complete(
            system_prompt="You are a test assistant",
            user_prompt="This is a test",
            extended_thinking=True
        ))
        
        # Should extract just the response part
        self.assertEqual(response, "This is the final reasoned answer.")
    
    def test_complete_json(self):
        """Test the complete_json method."""
        # Set up a JSON response
        json_response = '{"key": "value", "number": 42}'
        self.chat_mock.send_message.return_value.text = json_response
        
        provider = GeminiProvider(api_key=self.api_key)
        
        # Define a JSON schema
        schema = {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "number": {"type": "number"}
            }
        }
        
        # Run the complete_json method
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(provider.complete_json(
            system_prompt="You are a test assistant",
            user_prompt="Return a JSON object",
            json_schema=schema
        ))
        
        # Check the parsed response
        self.assertEqual(response["key"], "value")
        self.assertEqual(response["number"], 42)
    
    def test_json_response_all_models(self):
        """Test JSON response handling across all supported models."""
        # Set up a JSON response in a code block (common response format)
        code_block_response = (
            "Here's the JSON you requested:\n\n"
            "```json\n"
            '{"key": "value", "number": 42}\n'
            "```"
        )
        self.chat_mock.send_message.return_value.text = code_block_response
        
        # Define a JSON schema
        schema = {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "number": {"type": "number"}
            }
        }
        
        # Test each model
        models_to_test = [self.GEMINI_2_5_PRO, self.GEMINI_2_0_FLASH, self.GEMINI_2_0_FLASH_THINKING]
        
        for model_name in models_to_test:
            # Reset mocks
            self.genai_mock.reset_mock()
            self.model_mock.reset_mock()
            self.chat_mock.reset_mock()
            
            # Create provider with this model
            provider = GeminiProvider(api_key=self.api_key, model=model_name)
            
            # Run complete_json method
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(provider.complete_json(
                system_prompt="You are a test assistant",
                user_prompt="Return a JSON object",
                json_schema=schema
            ))
            
            # Check the parsed response
            self.assertEqual(response["key"], "value")
            self.assertEqual(response["number"], 42)
            
            # Test with extended thinking
            response = loop.run_until_complete(provider.complete_json(
                system_prompt="You are a test assistant",
                user_prompt="Return a JSON object",
                json_schema=schema,
                extended_thinking=True
            ))
            
            # Check the parsed response
            self.assertEqual(response["key"], "value")
            self.assertEqual(response["number"], 42)
            
            print(f"Tested JSON completion for {model_name}")
    
    def test_complete_json_with_code_block(self):
        """Test the complete_json method with a response in a code block."""
        # Set up a response with the JSON in a code block
        code_block_response = (
            "Here's the JSON you requested:\n\n"
            "```json\n"
            '{"key": "value", "number": 42}\n'
            "```"
        )
        self.chat_mock.send_message.return_value.text = code_block_response
        
        provider = GeminiProvider(api_key=self.api_key)
        
        # Define a JSON schema
        schema = {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "number": {"type": "number"}
            }
        }
        
        # Run the complete_json method
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(provider.complete_json(
            system_prompt="You are a test assistant",
            user_prompt="Return a JSON object",
            json_schema=schema
        ))
        
        # Check the parsed response
        self.assertEqual(response["key"], "value")
        self.assertEqual(response["number"], 42)


# Helper function to run tests synchronously
def run_sync_test(async_func):
    """Run an async test function synchronously."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_func)


if __name__ == "__main__":
    unittest.main()