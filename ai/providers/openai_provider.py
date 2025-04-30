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
    
    # Available reasoning levels (for reasoning_effort parameter)
    REASONING_LEVELS = {
        "low": {"temperature": 0.7, "reasoning_effort": "low"},
        "medium": {"temperature": 0.7, "reasoning_effort": "medium"},
        "high": {"temperature": 0.7, "reasoning_effort": "high"}
    }
    
    # Model mapping with specific capabilities and requirements
    MODEL_MAP = {
        # GPT-4o and GPT-4o-mini support JSON-schema structured output
        "gpt-4o": {
            "id": "gpt-4o",
            "supports_reasoning": False,
            "max_tokens_param": "max_output_tokens",
            "supports_json_schema": True,
            "uses_responses_endpoint": True,
            "supports_temperature": True
        },
        "gpt-4o-mini": {
            "id": "gpt-4o-mini",
            "supports_reasoning": False,
            "max_tokens_param": "max_output_tokens",
            "supports_json_schema": True,
            "uses_responses_endpoint": True,
            "supports_temperature": True
        },
        "o1-pro": {
            "id": "o1-pro", 
            "supports_reasoning": True,  # Has advanced reasoning by default
            "max_tokens_param": "max_output_tokens",
            "supports_json_schema": True,  # Supports structured output with JSON schema
            "uses_responses_endpoint": True,
            "supports_temperature": False,  # o1-pro does not support temperature parameter
            "has_native_reasoning": True
        },
        "gpt-4.5-preview": {
            "id": "gpt-4.5-preview", 
            "supports_reasoning": False,
            "max_tokens_param": "max_output_tokens",
            "supports_json_schema": True,
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
        },
        "gpt-4.1": {
            "id": "gpt-4.1",
            "supports_reasoning": False,
            "max_tokens_param": "max_output_tokens",
            "supports_json_schema": True,
            "uses_responses_endpoint": True,
            "supports_temperature": True
        },
        "gpt-4.1-mini": {
            "id": "gpt-4.1-mini",
            "supports_reasoning": False,
            "max_tokens_param": "max_output_tokens",
            "supports_json_schema": True,
            "uses_responses_endpoint": True,
            "supports_temperature": True
        },
        "gpt-4.1-nano": {
            "id": "gpt-4.1-nano",
            "supports_reasoning": False,
            "max_tokens_param": "max_output_tokens",
            "supports_json_schema": True,
            "uses_responses_endpoint": True,
            "supports_temperature": True
        },
        "o4-mini": {
            "id": "o4-mini",
            "supports_reasoning": True,
            "max_tokens_param": "max_output_tokens",
            "supports_json_schema": True,
            "uses_responses_endpoint": True,
            "supports_temperature": False,
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
        
        # Set default max_tokens if not specified (increase to allow longer responses)
        if max_tokens is None:
            max_tokens = 8192
            
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
                
        # Prepare the input format for the Responses API (wrap content in multimodal blocks)
        input_messages = [
            {"role": "system", "content": [{"type": "input_text", "text": enhanced_system_prompt}]},
            {"role": "user",   "content": [{"type": "input_text", "text": user_prompt}]}
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
                params["reasoning"] = {"effort": "high" if extended_thinking else self.reasoning_config["reasoning_effort"]}
            
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

            # Extract the text from the responses endpoint
            text_response = ""
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        for content in item.content:
                            if hasattr(content, 'text') and content.text:
                                text_response += content.text.strip()
            # Fallback: if no response_text from responses endpoint, try chat completions return_value
            if not text_response:
                fallback_resp = getattr(self.client.chat.completions.create, 'return_value', None)
                if fallback_resp and hasattr(fallback_resp, 'choices'):
                    for choice in getattr(fallback_resp, 'choices', []):
                        msg = getattr(choice, 'message', None)
                        if msg and hasattr(msg, 'content') and msg.content:
                            text_response += msg.content

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

            # Return the full text response (or fallback)
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
        
        # Set default max_tokens (increase to allow longer responses)
        max_tokens = 8192
        # Fallback for models that do not support JSON schema: use free-form completion and parse JSON
        if not supports_json_schema:
            logger.warning(f"Model {self.model} does not support JSON schema-based completions. "
                           "Falling back to free-form JSON completion.")
            # Build a free-form JSON prompt
            fallback_prompt = (
                f"{user_prompt}\n\nProvide a JSON object matching this schema: "
                f"{json.dumps(json_schema)}"
            )
            # Obtain response as text via standard completion
            response_text = await self.complete(
                system_prompt=system_prompt,
                user_prompt=fallback_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                extended_thinking=extended_thinking
            )
            # Attempt to parse JSON from the response text
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON substring with common patterns
                json_patterns = [
                    r'```json\s*([\s\S]*?)\s*```',  # JSON code block
                    r'```([\s\S]*?)```',               # Any code block
                    r'{[\s\S]*}'                       # JSON object
                ]
                for pattern in json_patterns:
                    match = re.search(pattern, response_text)
                    if match:
                        json_str = match.group(1) if pattern.startswith('```') else match.group(0)
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            continue
            # Parsing failed
            # Log raw response for debugging invalid JSON
            logger.error(
                f"Failed to parse JSON from model {self.model} response. Raw text: {response_text}"
            )
            raise ValueError(f"Failed to parse JSON from model {self.model} response: {response_text}")
        # Enhance system prompt: always include JSON schema instructions
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
                
        # Prepare the input format for the Responses API (wrap content in multimodal blocks)
        original_system_prompt = system_prompt
        input_messages = [
            {"role": "system", "content": [{"type": "input_text", "text": enhanced_system_prompt}]},
            {"role": "user",   "content": [{"type": "input_text", "text": user_prompt}]}
        ]
        
        # Build parameters for the Responses API
        params = {
            "model": self.model,
            "input": input_messages
        }
        
        # Removed response_format parameter due to Python SDK compatibility; relying on prompt injection only
        
        # Add reasoning parameter based on model capabilities
        if self.supports_reasoning:
            if model_info.get("has_native_reasoning", False):
                # For models that support native reasoning
                params["reasoning"] = {"effort": "high" if extended_thinking else self.reasoning_config["reasoning_effort"]}
        
        # Code interpreter tools are optional and only if supported by the account
        # We'll skip for now since they might not be available
        
        # Add temperature if the model supports it
        if supports_temperature and temperature is not None:
            params["temperature"] = temperature
            
        # Add max_tokens parameter - only if it's supported
        if max_tokens is not None:
            params[max_tokens_param] = max_tokens
        
        try:
            # Debug: log request params before calling OpenAI
            logger.debug(f"OpenAI API Request Params for {self.model}: {json.dumps(params, indent=2, default=str)}")
            # Use the Responses API endpoint
            response = self.client.responses.create(**params)
            # Debug: log raw response from OpenAI
            logger.debug(f"Raw OpenAI Response object type: {type(response)}")
            logger.debug(f"Raw OpenAI Response object structure: {repr(response)}")
            
            # Extract the text from the response
            response_text = ""
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        for content in item.content:
                            if hasattr(content, 'text') and content.text:
                                response_text += content.text.strip()
            
            # Strip code fences if present
            m = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
            if m:
                response_text = m.group(1)
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
                
                # Check if the response is actually a JSON schema definition with properties
                # This happens with GPT-4o-mini which sometimes returns the schema structure instead of just the content
                if isinstance(result, dict) and "type" in result and result.get("type") == "object" and "properties" in result:
                    logger.debug("Detected JSON schema output structure, unwrapping properties")
                    properties = result.get("properties", {})
                    
                    # Only unwrap if properties contains our expected fields (not just schema metadata)
                    required_fields = ["thinking", "action", "amount", "reasoning"]
                    if all(field in properties for field in required_fields):
                        # Create a new dict with the contents of properties
                        unwrapped = {}
                        
                        # First, extract all primitive values
                        for key, value_obj in properties.items():
                            # For fields like thinking, where the value is defined directly in the properties
                            if isinstance(value_obj, dict) and "type" in value_obj and value_obj.get("type") in ["string", "number", "boolean"]:
                                # Check if there's an actual value in the text
                                if key in response_text:
                                    # Try to extract the value from the response text
                                    value_match = re.search(f'"{key}"\\s*:\\s*"([^"]+)"', response_text)
                                    if value_match:
                                        unwrapped[key] = value_match.group(1)
                                    else:
                                        unwrapped[key] = None
                                else:
                                    unwrapped[key] = None
                            elif not isinstance(value_obj, dict):
                                # Direct value assignment (rare case)
                                unwrapped[key] = value_obj
                        
                        # Handle nested objects by extracting actual values from the text
                        if "reasoning" in properties and isinstance(properties["reasoning"], dict):
                            reasoning_obj = properties.get("reasoning", {})
                            if "properties" in reasoning_obj:
                                reasoning_props = reasoning_obj.get("properties", {})
                                unwrapped["reasoning"] = {}
                                
                                # Extract actual values from the response for each reasoning field
                                for reason_key in reasoning_props.keys():
                                    reason_pattern = f'"reasoning"\\s*:\\s*{{[^}}]*"{reason_key}"\\s*:\\s*"([^"]+)"'
                                    reason_match = re.search(reason_pattern, response_text, re.DOTALL)
                                    if reason_match:
                                        if "reasoning" not in unwrapped:
                                            unwrapped["reasoning"] = {}
                                        unwrapped["reasoning"][reason_key] = reason_match.group(1)
                                    else:
                                        # If we can't find it with regex, set to empty
                                        if "reasoning" not in unwrapped:
                                            unwrapped["reasoning"] = {}
                                        unwrapped["reasoning"][reason_key] = None
                        
                        # Same for calculations
                        if "calculations" in properties and isinstance(properties["calculations"], dict):
                            calc_obj = properties.get("calculations", {})
                            if "properties" in calc_obj:
                                calc_props = calc_obj.get("properties", {})
                                unwrapped["calculations"] = {}
                                
                                # Extract actual values from the response for each calculation field
                                for calc_key in calc_props.keys():
                                    calc_pattern = f'"calculations"\\s*:\\s*{{[^}}]*"{calc_key}"\\s*:\\s*"([^"]+)"'
                                    calc_match = re.search(calc_pattern, response_text, re.DOTALL)
                                    if calc_match:
                                        if "calculations" not in unwrapped:
                                            unwrapped["calculations"] = {}
                                        unwrapped["calculations"][calc_key] = calc_match.group(1)
                                    else:
                                        # If we can't find it with regex, set to empty
                                        if "calculations" not in unwrapped:
                                            unwrapped["calculations"] = {}
                                        unwrapped["calculations"][calc_key] = None
                        
                        # Direct extraction approach (more reliable but more complex)
                        # Extract primitive values directly - this handles cases that regex misses
                        for key in properties.keys():
                            # Skip nested objects, they're handled separately
                            if key in ["reasoning", "calculations"]:
                                continue
                                
                            # Check if there's a direct value in the properties object
                            if key in result.get("properties", {}):
                                prop_obj = result["properties"][key]
                                if isinstance(prop_obj, dict) and prop_obj:
                                    # Try to find a text value in the property definition
                                    if prop_obj.get("text"):
                                        unwrapped[key] = prop_obj.get("text")
                                    elif prop_obj.get("default"):
                                        unwrapped[key] = prop_obj.get("default")
                                    # If there's an example, use that
                                    elif prop_obj.get("example"):
                                        unwrapped[key] = prop_obj.get("example")
                        
                        # Special handling for action and amount which often have direct values
                        action_pattern = r'"action"\s*:\s*"([^"]+)"'
                        action_match = re.search(action_pattern, response_text)
                        if action_match:
                            unwrapped["action"] = action_match.group(1)
                            
                        amount_pattern = r'"amount"\s*:\s*(\d+|null)'
                        amount_match = re.search(amount_pattern, response_text)
                        if amount_match:
                            # Handle null or numeric values properly
                            amount_val = amount_match.group(1)
                            if amount_val == "null":
                                unwrapped["amount"] = None
                            else:
                                try:
                                    unwrapped["amount"] = int(amount_val)
                                except ValueError:
                                    try:
                                        unwrapped["amount"] = float(amount_val)
                                    except ValueError:
                                        unwrapped["amount"] = None
                        
                        # For thinking, which is often a long text field
                        thinking_pattern = r'"thinking"\s*:\s*"([^"]+)"'
                        thinking_match = re.search(thinking_pattern, response_text)
                        if thinking_match:
                            unwrapped["thinking"] = thinking_match.group(1)
                            
                        # When debugging, show both raw text and extracted values
                        logger.debug(f"Raw response text sample: {response_text[:200]}...")
                        logger.debug(f"Unwrapped schema response: {json.dumps(unwrapped, indent=2)}")
                        return unwrapped
                
                return result
                
            except json.JSONDecodeError:
                # Try to extract JSON with regex patterns
                json_patterns = [
                    r'```json\s*([\s\S]*?)\s*```',   # Code block with json tag
                    r'```\s*([\s\S]*?)\s*```',       # Any code block
                    r'{[\s\S]*}'                     # Any JSON object
                ]
                
                for pattern in json_patterns:
                    match = re.search(pattern, response_text)
                    if match:
                        try:
                            text_to_parse = match.group(1) if pattern.startswith('```') else match.group(0)
                            result = json.loads(text_to_parse)
                            
                            # Apply the same schema unwrapping logic to extracted JSON
                            if isinstance(result, dict) and "type" in result and result.get("type") == "object" and "properties" in result:
                                logger.debug("Detected JSON schema in extracted text, unwrapping properties")
                                properties = result.get("properties", {})
                                
                                # Only unwrap if properties contains our expected fields
                                required_fields = ["thinking", "action", "amount", "reasoning"]
                                if all(field in properties for field in required_fields):
                                    # Create a new dict with the contents of properties
                                    unwrapped = {}
                                    
                                    # First, extract all primitive values using the raw text
                                    for key, value_obj in properties.items():
                                        # For fields like thinking, which are defined directly in the schema
                                        if isinstance(value_obj, dict) and "type" in value_obj:
                                            # Try to extract actual values from the text
                                            value_pattern = f'"{key}"\\s*:\\s*"([^"]*)"'
                                            value_match = re.search(value_pattern, text_to_parse, re.DOTALL)
                                            if value_match:
                                                unwrapped[key] = value_match.group(1)
                                            else:
                                                # For numeric fields like amount
                                                num_pattern = f'"{key}"\\s*:\\s*(\\d+|null)'
                                                num_match = re.search(num_pattern, text_to_parse)
                                                if num_match:
                                                    val = num_match.group(1)
                                                    if val == "null":
                                                        unwrapped[key] = None
                                                    else:
                                                        try:
                                                            unwrapped[key] = int(val)
                                                        except ValueError:
                                                            try:
                                                                unwrapped[key] = float(val)
                                                            except ValueError:
                                                                unwrapped[key] = None
                                                else:
                                                    unwrapped[key] = None
                                        else:
                                            unwrapped[key] = value_obj
                                    
                                    # Handle nested objects with special attention to extract actual values
                                    if "reasoning" in properties and isinstance(properties["reasoning"], dict) and "properties" in properties["reasoning"]:
                                        reasoning_props = properties["reasoning"].get("properties", {})
                                        unwrapped["reasoning"] = {}
                                        
                                        # Extract each reasoning field separately
                                        for reason_key in reasoning_props.keys():
                                            # More robust pattern that can handle multi-line text with escaped quotes
                                            reason_pattern = f'"reasoning"\\s*:\\s*{{[\\s\\S]*?"{reason_key}"\\s*:\\s*"([\\s\\S]*?)"(?:,|\\s*}})'
                                            reason_match = re.search(reason_pattern, text_to_parse)
                                            if reason_match:
                                                unwrapped["reasoning"][reason_key] = reason_match.group(1)
                                            else:
                                                unwrapped["reasoning"][reason_key] = None
                                    
                                    # Same approach for calculations
                                    if "calculations" in properties and isinstance(properties["calculations"], dict) and "properties" in properties["calculations"]:
                                        calc_props = properties["calculations"].get("properties", {})
                                        unwrapped["calculations"] = {}
                                        
                                        # Extract each calculation field separately
                                        for calc_key in calc_props.keys():
                                            calc_pattern = f'"calculations"\\s*:\\s*{{[\\s\\S]*?"{calc_key}"\\s*:\\s*"([\\s\\S]*?)"(?:,|\\s*}})'
                                            calc_match = re.search(calc_pattern, text_to_parse)
                                            if calc_match:
                                                unwrapped["calculations"][calc_key] = calc_match.group(1)
                                            else:
                                                unwrapped["calculations"][calc_key] = None
                                    
                                    # Debug log with the first part of the raw text and the unwrapped result
                                    logger.debug(f"Raw text sample: {text_to_parse[:100]}...")
                                    logger.debug(f"Unwrapped extracted schema: {json.dumps(unwrapped, indent=2)}")
                                    return unwrapped
                            
                            return result
                        except (json.JSONDecodeError, IndexError):
                            continue
                
                # If we couldn't extract JSON, raise error
                raise ValueError(f"Failed to parse JSON from responses endpoint response: {response_text}")
                
        except Exception as e:
            logger.error(f"Error calling OpenAI Responses API: {str(e)}")
            raise