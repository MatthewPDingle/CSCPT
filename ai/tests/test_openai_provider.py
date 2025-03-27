"""
Unit tests for the OpenAI provider implementation.
"""

import os
import unittest
import json
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.providers.openai_provider import OpenAIProvider


class TestOpenAIProvider(unittest.TestCase):
    """Tests for the OpenAIProvider class."""
    
    # Constants for all supported OpenAI models
    MODELS = {
        "gpt-4o": {"supports_reasoning": False},
        "gpt-4o-mini": {"supports_reasoning": False},
        "o1-pro": {"supports_reasoning": False},
        "gpt-4.5-preview": {"supports_reasoning": False},
        "o3-mini": {"supports_reasoning": True}
    }
    
    def setUp(self):
        """Set up test fixtures."""
        # Load environment variables from .env file if available
        load_dotenv()
        
        # Skip tests if API key not available
        if not os.environ.get("OPENAI_API_KEY"):
            self.skipTest("OPENAI_API_KEY environment variable is not set")
        
        self.api_key = os.environ.get("OPENAI_API_KEY")
    
    def test_all_model_initializations(self):
        """Test initialization with all supported models."""
        for model_name, capabilities in self.MODELS.items():
            with self.subTest(model=model_name):
                with patch('openai.OpenAI') as mock_openai:
                    # Create mock OpenAI client
                    mock_client = MagicMock()
                    mock_openai.return_value = mock_client
                    
                    # Initialize provider with this model
                    provider = OpenAIProvider(api_key=self.api_key, model=model_name)
                    
                    # Verify OpenAI client was initialized with correct API key
                    mock_openai.assert_called_once()
                    self.assertEqual(mock_openai.call_args[1]["api_key"], self.api_key)
                    
                    # Verify model was set correctly
                    self.assertEqual(provider.model, model_name)
                    
                    # Verify reasoning capability flag is set correctly
                    self.assertEqual(provider.supports_reasoning, capabilities["supports_reasoning"])
                    
                    print(f"Verified model: {model_name}, supports_reasoning={capabilities['supports_reasoning']}")
    
    @patch('openai.OpenAI')
    def test_initialization(self, mock_openai):
        """Test provider initialization with default model."""
        # Create mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Initialize provider
        provider = OpenAIProvider(api_key=self.api_key)
        
        # Verify OpenAI client was initialized with correct API key
        mock_openai.assert_called_once()
        self.assertEqual(mock_openai.call_args[1]["api_key"], self.api_key)
        
        # Verify default model
        self.assertEqual(provider.model, "gpt-4o")
    
    @patch('openai.OpenAI')
    def test_initialization_with_org_id(self, mock_openai):
        """Test provider initialization with organization ID."""
        # Create mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Initialize provider with organization ID
        org_id = "org-123456"
        provider = OpenAIProvider(api_key=self.api_key, organization_id=org_id)
        
        # Verify OpenAI client was initialized with organization ID
        mock_openai.assert_called_once()
        self.assertEqual(mock_openai.call_args[1]["api_key"], self.api_key)
        self.assertEqual(mock_openai.call_args[1]["organization"], org_id)
    
    @patch('openai.OpenAI')
    def test_complete(self, mock_openai):
        """Test the complete method."""
        # Setup mock OpenAI client and response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Create mock completion response
        mock_message = MagicMock()
        mock_message.content = "This is a test response"
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        # Set the mock response for chat.completions.create
        mock_client.chat.completions.create.return_value = mock_response
        
        # Initialize provider
        provider = OpenAIProvider(api_key=self.api_key)
        
        # Create a synchronous test function
        def sync_complete():
            system_prompt = "You are a test assistant"
            user_prompt = "This is a test"
            
            # Call the provider's complete method
            response = provider.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )
            
            # Since the method is async in signature but implemented synchronously,
            # we need this workaround to get the result
            if hasattr(response, "__await__"):
                try:
                    while True:
                        response.__await__().__next__()
                except StopIteration as e:
                    response = e.value
            
            return response
        
        # Run the test
        response = sync_complete()
        
        # Verify the response
        self.assertEqual(response, "This is a test response")
        
        # Verify API call parameters
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        
        self.assertEqual(call_kwargs["model"], "gpt-4o")
        self.assertEqual(call_kwargs["temperature"], 0.7)
        self.assertEqual(call_kwargs["messages"][0]["role"], "system")
        self.assertEqual(call_kwargs["messages"][0]["content"], "You are a test assistant")
        self.assertEqual(call_kwargs["messages"][1]["role"], "user")
        self.assertEqual(call_kwargs["messages"][1]["content"], "This is a test")
    
    def test_extended_thinking_all_models(self):
        """Test extended thinking with all supported models."""
        # Set up mock responses for each case
        json_response_content = json.dumps({
            "thinking": ["Step 1: Consider X", "Step 2: Analyze Y", "Step 3: Conclude Z"],
            "response": "This is a test response with JSON thinking"
        })
        
        text_response_content = "This is a test response with text thinking"
        
        for model_name, capabilities in self.MODELS.items():
            with self.subTest(model=model_name):
                with patch('openai.OpenAI') as mock_openai:
                    # Setup mock OpenAI client and appropriate response
                    mock_client = MagicMock()
                    mock_openai.return_value = mock_client
                    
                    # Create mock completion response
                    mock_message = MagicMock()
                    # Use JSON for models with structured reasoning, plain text for others
                    if capabilities["supports_reasoning"]:
                        mock_message.content = json_response_content
                    else:
                        mock_message.content = text_response_content
                    
                    mock_choice = MagicMock()
                    mock_choice.message = mock_message
                    
                    mock_response = MagicMock()
                    mock_response.choices = [mock_choice]
                    
                    # Set the mock response for chat.completions.create
                    mock_client.chat.completions.create.return_value = mock_response
                    
                    # Initialize provider with this model
                    provider = OpenAIProvider(api_key=self.api_key, model=model_name)
                    
                    # Create a synchronous test function
                    def sync_complete():
                        system_prompt = "You are a test assistant"
                        user_prompt = "This is a test requiring analysis"
                        
                        # Call the provider's complete method with extended thinking
                        response = provider.complete(
                            system_prompt=system_prompt,
                            user_prompt=user_prompt,
                            temperature=0.7,
                            extended_thinking=True
                        )
                        
                        # Handle async/sync conversion
                        if hasattr(response, "__await__"):
                            try:
                                while True:
                                    response.__await__().__next__()
                            except StopIteration as e:
                                response = e.value
                        
                        return response
                    
                    # Run the test
                    response = sync_complete()
                    
                    # Verify API call parameters
                    mock_client.chat.completions.create.assert_called_once()
                    call_kwargs = mock_client.chat.completions.create.call_args[1]
                    
                    self.assertEqual(call_kwargs["model"], model_name)
                    self.assertEqual(call_kwargs["temperature"], 0.7)
                    
                    # Check system prompt and response format based on model capabilities
                    if capabilities["supports_reasoning"]:
                        # Should use JSON structure for reasoning
                        self.assertEqual(call_kwargs["response_format"]["type"], "json_object")
                        self.assertIn("thinking", call_kwargs["response_format"]["schema"]["properties"])
                        # Response should be extracted from JSON
                        self.assertEqual(response, "This is a test response with JSON thinking")
                    else:
                        # Should use text format and enhanced prompt
                        self.assertEqual(call_kwargs["response_format"]["type"], "text")
                        # Check for enhanced prompt
                        system_content = call_kwargs["messages"][0]["content"]
                        self.assertIn("Please think step by step", system_content)
                        # Response should be returned as is
                        self.assertEqual(response, text_response_content)
                    
                    print(f"Verified extended thinking for {model_name}, supports_reasoning={capabilities['supports_reasoning']}")
    
    @patch('openai.OpenAI')
    def test_complete_with_extended_thinking(self, mock_openai):
        """Test the complete method with extended thinking using o3-mini."""
        # Setup mock OpenAI client and response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Create mock completion response with JSON content
        mock_message = MagicMock()
        mock_message.content = json.dumps({
            "thinking": ["Step 1: Consider X", "Step 2: Analyze Y", "Step 3: Conclude Z"],
            "response": "This is a test response with thinking"
        })
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        # Set the mock response for chat.completions.create
        mock_client.chat.completions.create.return_value = mock_response
        
        # Initialize provider with o3-mini which supports reasoning
        provider = OpenAIProvider(api_key=self.api_key, model="o3-mini")
        
        # Create a synchronous test function
        def sync_complete():
            system_prompt = "You are a test assistant"
            user_prompt = "This is a test requiring analysis"
            
            # Call the provider's complete method with extended thinking
            response = provider.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                extended_thinking=True
            )
            
            # Handle async/sync conversion
            if hasattr(response, "__await__"):
                try:
                    while True:
                        response.__await__().__next__()
                except StopIteration as e:
                    response = e.value
            
            return response
        
        # Run the test
        response = sync_complete()
        
        # Verify the response (should be the "response" field of the JSON)
        self.assertEqual(response, "This is a test response with thinking")
        
        # Verify API call parameters
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        
        self.assertEqual(call_kwargs["model"], "o3-mini")
        self.assertEqual(call_kwargs["temperature"], 0.7)
        
        # Check that system prompt includes request for reasoning
        system_content = call_kwargs["messages"][0]["content"]
        self.assertIn("Please provide detailed step-by-step reasoning", system_content)
        
        # Check response format
        self.assertEqual(call_kwargs["response_format"]["type"], "json_object")
        self.assertIn("thinking", call_kwargs["response_format"]["schema"]["properties"])
    
    def test_json_completion_all_models(self):
        """Test JSON completion with all supported models."""
        # Define JSON schema
        json_schema = {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["fold", "check", "call", "bet", "raise"]},
                "amount": {"type": "number"},
                "reasoning": {"type": "string"}
            },
            "required": ["action", "reasoning"]
        }
        
        # Standard JSON response
        standard_json_content = json.dumps({
            "action": "raise",
            "amount": 100,
            "reasoning": "This is a test reasoning"
        })
        
        # Extended thinking JSON response (for models that support reasoning)
        extended_json_content = json.dumps({
            "thinking": ["Step 1: Evaluate position", "Step 2: Consider bet sizing"],
            "result": {
                "action": "raise",
                "amount": 150,
                "reasoning": "This is a test reasoning with extended thinking"
            }
        })
        
        for model_name, capabilities in self.MODELS.items():
            # Test standard JSON completion
            with self.subTest(model=model_name, extended_thinking=False):
                with patch('openai.OpenAI') as mock_openai:
                    # Setup mock OpenAI client and response
                    mock_client = MagicMock()
                    mock_openai.return_value = mock_client
                    
                    # Create mock completion response
                    mock_message = MagicMock()
                    mock_message.content = standard_json_content
                    
                    mock_choice = MagicMock()
                    mock_choice.message = mock_message
                    
                    mock_response = MagicMock()
                    mock_response.choices = [mock_choice]
                    
                    # Set the mock response for chat.completions.create
                    mock_client.chat.completions.create.return_value = mock_response
                    
                    # Initialize provider with this model
                    provider = OpenAIProvider(api_key=self.api_key, model=model_name)
                    
                    # Create a synchronous test function
                    def sync_complete_json():
                        system_prompt = "You are a poker player"
                        user_prompt = "What should I do with pocket aces?"
                        
                        # Call the provider's complete_json method
                        response = provider.complete_json(
                            system_prompt=system_prompt,
                            user_prompt=user_prompt,
                            json_schema=json_schema,
                            temperature=0.7
                        )
                        
                        # Handle async/sync conversion
                        if hasattr(response, "__await__"):
                            try:
                                while True:
                                    response.__await__().__next__()
                            except StopIteration as e:
                                response = e.value
                        
                        return response
                    
                    # Run the test
                    response = sync_complete_json()
                    
                    # Verify the response
                    self.assertEqual(response["action"], "raise")
                    self.assertEqual(response["amount"], 100)
                    self.assertEqual(response["reasoning"], "This is a test reasoning")
                    
                    # Verify API call parameters
                    mock_client.chat.completions.create.assert_called_once()
                    call_kwargs = mock_client.chat.completions.create.call_args[1]
                    
                    self.assertEqual(call_kwargs["model"], model_name)
                    self.assertEqual(call_kwargs["temperature"], 0.7)
                    
                    # Verify JSON schema is included in system message
                    self.assertIn("Your response must be a valid JSON object", call_kwargs["messages"][0]["content"])
                    
                    # Verify response_format
                    self.assertEqual(call_kwargs["response_format"]["type"], "json_object")
                    
                    print(f"Verified JSON completion for {model_name}")
            
            # Test JSON completion with extended thinking
            with self.subTest(model=model_name, extended_thinking=True):
                with patch('openai.OpenAI') as mock_openai:
                    # Setup mock OpenAI client and response
                    mock_client = MagicMock()
                    mock_openai.return_value = mock_client
                    
                    # Create mock completion response - different for reasoning models
                    mock_message = MagicMock()
                    if capabilities["supports_reasoning"]:
                        mock_message.content = extended_json_content
                    else:
                        mock_message.content = standard_json_content
                    
                    mock_choice = MagicMock()
                    mock_choice.message = mock_message
                    
                    mock_response = MagicMock()
                    mock_response.choices = [mock_choice]
                    
                    # Set the mock response for chat.completions.create
                    mock_client.chat.completions.create.return_value = mock_response
                    
                    # Initialize provider with this model
                    provider = OpenAIProvider(api_key=self.api_key, model=model_name)
                    
                    # Create a synchronous test function
                    def sync_complete_json_extended():
                        system_prompt = "You are a poker player"
                        user_prompt = "What should I do with pocket aces?"
                        
                        # Call the provider's complete_json method with extended thinking
                        response = provider.complete_json(
                            system_prompt=system_prompt,
                            user_prompt=user_prompt,
                            json_schema=json_schema,
                            temperature=0.7,
                            extended_thinking=True
                        )
                        
                        # Handle async/sync conversion
                        if hasattr(response, "__await__"):
                            try:
                                while True:
                                    response.__await__().__next__()
                            except StopIteration as e:
                                response = e.value
                        
                        return response
                    
                    # Run the test
                    response = sync_complete_json_extended()
                    
                    # Verify the response based on model capabilities
                    if capabilities["supports_reasoning"]:
                        # For reasoning models, expect the 'result' field
                        self.assertEqual(response["action"], "raise")
                        self.assertEqual(response["amount"], 150)
                        self.assertEqual(response["reasoning"], "This is a test reasoning with extended thinking")
                    else:
                        # For non-reasoning models, expect standard response
                        self.assertEqual(response["action"], "raise")
                        self.assertEqual(response["amount"], 100)
                        self.assertEqual(response["reasoning"], "This is a test reasoning")
                    
                    # Verify API call parameters
                    mock_client.chat.completions.create.assert_called_once()
                    call_kwargs = mock_client.chat.completions.create.call_args[1]
                    
                    self.assertEqual(call_kwargs["model"], model_name)
                    
                    # Check for proper response format based on model capabilities
                    if capabilities["supports_reasoning"]:
                        # Extended thinking capable models should have combined schema
                        self.assertIn("thinking", call_kwargs["response_format"]["schema"]["properties"])
                        self.assertIn("result", call_kwargs["response_format"]["schema"]["properties"])
                    
                    print(f"Verified JSON completion with extended thinking for {model_name}, supports_reasoning={capabilities['supports_reasoning']}")
    
    @patch('openai.OpenAI')
    def test_complete_json(self, mock_openai):
        """Test the complete_json method with the default model."""
        # Setup mock OpenAI client and response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Create mock completion response
        mock_message = MagicMock()
        mock_message.content = json.dumps({
            "action": "raise",
            "amount": 100,
            "reasoning": "This is a test reasoning"
        })
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        # Set the mock response for chat.completions.create
        mock_client.chat.completions.create.return_value = mock_response
        
        # Initialize provider
        provider = OpenAIProvider(api_key=self.api_key)
        
        # Create a synchronous test function
        def sync_complete_json():
            system_prompt = "You are a poker player"
            user_prompt = "What should I do with pocket aces?"
            json_schema = {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["fold", "check", "call", "bet", "raise"]},
                    "amount": {"type": "number"},
                    "reasoning": {"type": "string"}
                },
                "required": ["action", "reasoning"]
            }
            
            # Call the provider's complete_json method
            response = provider.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_schema=json_schema,
                temperature=0.7
            )
            
            # Handle async/sync conversion
            if hasattr(response, "__await__"):
                try:
                    while True:
                        response.__await__().__next__()
                except StopIteration as e:
                    response = e.value
            
            return response
        
        # Run the test
        response = sync_complete_json()
        
        # Verify the response
        self.assertEqual(response["action"], "raise")
        self.assertEqual(response["amount"], 100)
        self.assertEqual(response["reasoning"], "This is a test reasoning")
        
        # Verify API call parameters
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        
        self.assertEqual(call_kwargs["model"], "gpt-4o")
        self.assertEqual(call_kwargs["temperature"], 0.7)
        
        # Verify JSON schema is included in system message
        self.assertIn("Your response must be a valid JSON object", call_kwargs["messages"][0]["content"])
        
        # Verify response_format
        self.assertEqual(call_kwargs["response_format"]["type"], "json_object")


if __name__ == '__main__':
    unittest.main()