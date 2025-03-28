"""
OpenAI API provider implementation.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List, Union, Literal

from . import LLMProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    """Provider implementation for OpenAI API."""
    
    # Default model
    DEFAULT_MODEL = "gpt-4o"
    
    # Available reasoning levels (mainly for o3-mini)
    REASONING_LEVELS = {
        "low": {"temperature": 0.7, "reasoning_steps": 1},
        "medium": {"temperature": 0.8, "reasoning_steps": 3},
        "high": {"temperature": 0.9, "reasoning_steps": 5}
    }
    
    # Model mapping with specific capabilities and requirements
    MODEL_MAP = {
        "gpt-4o": {
            "id": "gpt-4o", 
            "supports_reasoning": False,
            "max_tokens_param": "max_output_tokens",
            "supports_json_schema": False,
            "uses_responses_endpoint": True,
            "supports_temperature": True
        },
        "gpt-4o-mini": {
            "id": "gpt-4o-mini", 
            "supports_reasoning": False,
            "max_tokens_param": "max_output_tokens",
            "supports_json_schema": False,
            "uses_responses_endpoint": True,
            "supports_temperature": True
        },
        "o1-pro": {
            "id": "o1-pro", 
            "supports_reasoning": True,  # Has advanced reasoning by default
            "max_tokens_param": "max_output_tokens",
            "supports_json_schema": False,  # Does not support native JSON schema
            "uses_responses_endpoint": True,
            "supports_temperature": False,  # o1-pro doesn't support temperature parameter
            "has_native_reasoning": True
        },
        "gpt-4.5-preview": {
            "id": "gpt-4.5-preview", 
            "supports_reasoning": False,
            "max_tokens_param": "max_output_tokens",
            "supports_json_schema": False,
            "uses_responses_endpoint": True,
            "supports_temperature": True
        },
        "o3-mini": {
            "id": "o3-mini", 
            "supports_reasoning": True,
            "max_tokens_param": "max_output_tokens",
            "supports_json_schema": True,
            "uses_responses_endpoint": True,
            "supports_temperature": False,  # o3-mini doesn't support temperature
            "has_native_reasoning": True
        }
    }
    
    def __init__(self, 
                api_key: str, 
                model: str = DEFAULT_MODEL, 
                reasoning_level: str = "medium",
                organization_id: Optional[str] = None):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model identifier (default: gpt-4o)
            reasoning_level: Reasoning level (low, medium, high) - applies to o3-mini
            organization_id: OpenAI organization ID (optional)
        """
        self.api_key = api_key
        self.organization_id = organization_id
        
        # Set model
        if model not in self.MODEL_MAP:
            logger.warning(f"Model {model} not recognized, using default: {self.DEFAULT_MODEL}")
            model = self.DEFAULT_MODEL
        self.model = self.MODEL_MAP[model]["id"]
        self.supports_reasoning = self.MODEL_MAP[model]["supports_reasoning"]
        
        # Set reasoning level
        if reasoning_level not in self.REASONING_LEVELS:
            logger.warning(f"Reasoning level {reasoning_level} not recognized, using medium")
            reasoning_level = "medium"
        self.reasoning_level = reasoning_level
        self.reasoning_config = self.REASONING_LEVELS[reasoning_level]
        
        # Import OpenAI here to avoid global import issues
        try:
            from openai import OpenAI
            # Only set the organization header if provided, otherwise let OpenAI use the default from the API key
            if organization_id:
                self.client = OpenAI(
                    api_key=api_key, 
                    organization=organization_id  # This is the proper way to set the organization
                )
            else:
                self.client = OpenAI(api_key=api_key)
        except ImportError:
            logger.error("Failed to import openai library. Please install with: pip install openai")
            raise
    
    async def complete(self, 
                     system_prompt: str, 
                     user_prompt: str, 
                     temperature: Optional[float] = None, 
                     max_tokens: Optional[int] = None,
                     extended_thinking: bool = False) -> str:
        """
        Generate a completion using OpenAI Responses API.
        
        Args:
            system_prompt: System message for context
            user_prompt: User message/query
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            extended_thinking: Whether to use extended reasoning (similar to Anthropic's extended thinking)
            
        Returns:
            The generated text response
        """
        # Get model-specific capabilities from MODEL_MAP
        model_name = next((k for k, v in self.MODEL_MAP.items() if v["id"] == self.model), None)
        model_info = self.MODEL_MAP.get(model_name or self.model, {})
        max_tokens_param = model_info.get("max_tokens_param", "max_tokens")
        supports_json_schema = model_info.get("supports_json_schema", False)
        supports_temperature = model_info.get("supports_temperature", True)
        
        # Determine temperature if supported by the model
        if temperature is None:
            temperature = self.reasoning_config["temperature"]
        
        # Set default max_tokens if not specified
        if max_tokens is None:
            max_tokens = 1024
            
        # Prepare system prompt with extended thinking if requested
        enhanced_system_prompt = system_prompt
        if extended_thinking:
            if self.supports_reasoning:
                # For models that support reasoning, add explicit instructions
                enhanced_system_prompt += "\n\nPlease provide detailed step-by-step reasoning before giving your final answer."
            else:
                # For models that don't support explicit reasoning, just modify the prompt
                logger.info(f"Model {self.model} doesn't support explicit reasoning. Using standard prompt enhancement.")
                enhanced_system_prompt += "\n\nPlease think step by step and provide a detailed analysis before sharing your final conclusion."
                
        # Prepare the input format for the Responses API
        input_messages = [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": enhanced_system_prompt}]
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_prompt}]
            }
        ]
        
        # Build parameters for the Responses API
        params = {
            "model": self.model,
            "input": input_messages
        }
        
        # Add reasoning parameter based on model capabilities
        if self.supports_reasoning:
            model_info = self.MODEL_MAP.get(self.model, {})
            if model_info.get("has_native_reasoning", False):
                # For models that support native reasoning
                params["reasoning"] = {"effort": "high" if extended_thinking else self.reasoning_level}
            
        # Code interpreter tools are optional and only if supported by the account
        # We'll skip for now since they might not be available
        
        # Add temperature if the model supports it
        if supports_temperature:
            params["temperature"] = temperature
            
        # Add max_tokens parameter - only if it's supported
        if max_tokens is not None:
            params[max_tokens_param] = max_tokens
            
        try:
            # Use the Responses API endpoint
            response = self.client.responses.create(**params)
            
            # Extract the text from the response
            text_response = ""
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        for content in item.content:
                            if hasattr(content, 'text') and content.text:
                                text_response += content.text.strip()
            
            # If we have a response, try to extract JSON thinking if extended_thinking was requested
            if text_response and extended_thinking and self.supports_reasoning:
                try:
                    # Try to parse as JSON to extract thinking
                    result = json.loads(text_response)
                    if "thinking" in result and "response" in result:
                        # Log the thinking process for debugging
                        logger.debug(f"Extended thinking: {json.dumps(result['thinking'])}")
                        return result["response"]
                except (json.JSONDecodeError, KeyError) as e:
                    logger.debug(f"Response not in JSON format with thinking: {e}")
                    # If not in JSON format, return as is
            
            # Return the full text response
            return text_response if text_response else str(response)
                
        except Exception as e:
            logger.error(f"Error calling OpenAI Responses API: {str(e)}")
            raise
    
    async def complete_json(self, 
                          system_prompt: str, 
                          user_prompt: str, 
                          json_schema: Dict[str, Any], 
                          temperature: Optional[float] = None,
                          extended_thinking: bool = False) -> Dict[str, Any]:
        """
        Generate a JSON-structured completion using OpenAI Responses API.
        
        Args:
            system_prompt: System message for context
            user_prompt: User message/query
            json_schema: JSON schema to validate against
            temperature: Sampling temperature (0.0 to 1.0)
            extended_thinking: Whether to use extended reasoning
            
        Returns:
            Parsed JSON response
        """
        # Get model-specific capabilities from MODEL_MAP
        model_name = next((k for k, v in self.MODEL_MAP.items() if v["id"] == self.model), None)
        model_info = self.MODEL_MAP.get(model_name or self.model, {})
        max_tokens_param = model_info.get("max_tokens_param", "max_tokens")
        supports_json_schema = model_info.get("supports_json_schema", False)
        supports_temperature = model_info.get("supports_temperature", True)
        
        # Determine temperature
        if temperature is None:
            temperature = self.reasoning_config["temperature"]
        
        # Set default max_tokens
        max_tokens = 1024
        
        # Enhance system prompt to include JSON schema instructions
        schema_instruction = f"Your response must be a valid JSON object that follows this structure: {json.dumps(json_schema)}"
        enhanced_system_prompt = f"{system_prompt}\n\n{schema_instruction}"
        
        # Add extended thinking instructions if requested
        if extended_thinking:
            if self.supports_reasoning:
                # For models that support reasoning, add explicit instructions
                if supports_json_schema:
                    # For models that support both reasoning and JSON schema
                    enhanced_system_prompt += "\n\nPlease provide detailed step-by-step reasoning in the 'thinking' field before giving your final result."
                else:
                    # For models that support reasoning but not JSON schema
                    enhanced_system_prompt += "\n\nPlease provide detailed step-by-step reasoning before giving your final answer in JSON format."
            else:
                # For models that don't support explicit reasoning
                enhanced_system_prompt += "\n\nPlease think step by step before formulating your response in JSON format."
                
        # Prepare the input format for the Responses API
        input_messages = [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": enhanced_system_prompt}]
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_prompt}]
            }
        ]
        
        # Build parameters for the Responses API
        params = {
            "model": self.model,
            "input": input_messages
        }
        
        # For models that support JSON schema (like o3-mini but not o1-pro)
        model_info = self.MODEL_MAP.get(self.model, {})
        
        # Responses API doesn't seem to support response_format directly for o1-pro, gpt-4o, etc.
        # Add explicit instructions to the system prompt instead
        enhanced_system_text = f"Your response must be a valid JSON object that follows this structure: {json.dumps(json_schema)}\n\nUse valid JSON format with keys and values in your response."
        if enhanced_system_text not in input_messages[0]["content"][0]["text"]:
            input_messages[0]["content"][0]["text"] += "\n\n" + enhanced_system_text
            
        # Add response format only for models we know support it (o3-mini)
        if self.model == "o3-mini":
            if supports_json_schema:
                # If extended thinking is requested and model supports reasoning, create an extended schema
                if extended_thinking and self.supports_reasoning:
                    extended_schema = {
                        "type": "object",
                        "properties": {
                            "thinking": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "A detailed step-by-step analysis"
                            },
                            "result": json_schema
                        },
                        "required": ["thinking", "result"]
                    }
                    params["response_format"] = {
                        "type": "json_schema",
                        "schema": extended_schema
                    }
                else:
                    # Standard JSON schema
                    params["response_format"] = {
                        "type": "json_schema",
                        "schema": json_schema
                    }
            else:
                # For models that don't support JSON schema but do support response_format
                params["response_format"] = {"type": "json_object"}
        
        # Add reasoning parameter based on model capabilities
        if self.supports_reasoning:
            if model_info.get("has_native_reasoning", False):
                # For models that support native reasoning
                params["reasoning"] = {"effort": "high" if extended_thinking else self.reasoning_level}
        
        # Code interpreter tools are optional and only if supported by the account
        # We'll skip for now since they might not be available
        
        # Add temperature if the model supports it
        if supports_temperature and temperature is not None:
            params["temperature"] = temperature
            
        # Add max_tokens parameter - only if it's supported
        if max_tokens is not None:
            params[max_tokens_param] = max_tokens
        
        try:
            # Use the Responses API endpoint
            response = self.client.responses.create(**params)
            
            # Extract the text from the response
            response_text = ""
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        for content in item.content:
                            if hasattr(content, 'text') and content.text:
                                response_text += content.text.strip()
            
            # Try to parse the JSON response
            try:
                result = json.loads(response_text)
                
                # If extended thinking was used and model supports it, extract the final result
                if extended_thinking and self.supports_reasoning:
                    # Check if the response has the thinking/result structure
                    if "thinking" in result and "result" in result:
                        # Log the thinking process for debugging
                        logger.debug(f"Extended thinking: {json.dumps(result['thinking'])}")
                        return result["result"]
                
                return result
                
            except json.JSONDecodeError:
                # Try to extract JSON with regex patterns
                json_patterns = [
                    r'```json\s*([\s\S]*?)\s*```',  # Code block with json tag
                    r'```\s*([\s\S]*?)\s*```',      # Any code block
                    r'{[\s\S]*}'                    # Any JSON object
                ]
                
                for pattern in json_patterns:
                    match = re.search(pattern, response_text)
                    if match:
                        try:
                            text_to_parse = match.group(1) if pattern.startswith('```') else match.group(0)
                            return json.loads(text_to_parse)
                        except (json.JSONDecodeError, IndexError):
                            continue
                
                # If we couldn't extract JSON, raise error
                raise ValueError(f"Failed to parse JSON from responses endpoint response: {response_text}")
                
        except Exception as e:
            logger.error(f"Error calling OpenAI Responses API: {str(e)}")
            raise