"""
Google Gemini API provider implementation.
"""

import json
import re
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union, Literal

from . import LLMProvider

# Ensure a default asyncio event loop is available for get_event_loop(), and patch it to avoid RuntimeError
_orig_get_event_loop = asyncio.get_event_loop
def _patched_get_event_loop():
    try:
        return _orig_get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
asyncio.get_event_loop = _patched_get_event_loop

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    """Provider implementation for Google's Gemini API."""
    
    # Default model
    DEFAULT_MODEL = "gemini-2.5-pro"
    
    # Model mapping with capabilities
    MODEL_MAP = {
        "gemini-2.5-pro": {"id": "gemini-2.5-pro-preview-03-25", "supports_reasoning": True},
        "gemini-2.5-pro-preview": {"id": "gemini-2.5-pro-preview-03-25", "supports_reasoning": True},
        "gemini-2.5-pro-preview-03-25": {"id": "gemini-2.5-pro-preview-03-25", "supports_reasoning": True},
        # New flash preview model, with structured output & reasoning support
        "gemini-2.5-flash-preview-04-17": {"id": "gemini-2.5-flash-preview-04-17", "supports_reasoning": True},
        "gemini-2.0-flash": {"id": "gemini-2.0-flash-001", "supports_reasoning": False},
        "gemini-2.0-flash-thinking": {"id": "gemini-2.0-flash-thinking-exp-01-21", "supports_reasoning": True},
    }
    
    def _create_example_json(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an example JSON object based on the schema to use as a formatting example.
        
        Args:
            schema: The JSON schema to base the example on
            
        Returns:
            An example JSON object that follows the schema format
        """
        # Generate a more realistic example for a poker decision
        if ("properties" in schema and 
            "action" in schema.get("properties", {}) and 
            "amount" in schema.get("properties", {})):
            
            # Create a detailed example with explicit calculations to guide the model
            return {
                "thinking": "I have pocket aces (AA) which is the strongest possible starting hand. I'm in early position, so I should raise to build the pot and narrow the field.",
                "action": "raise",
                "amount": 20,
                "reasoning": {
                    "hand_assessment": "Pocket aces (AA) is the strongest starting hand. It's a premium hand that should be played aggressively.",
                    "positional_considerations": "I'm in early position, so I want to raise to build the pot with my strong hand.",
                    "opponent_reads": "The players behind me have been calling raises frequently. I want to charge them to see a flop.",
                    "archetype_alignment": "As a tight-aggressive player, I want to play my premium hands strongly and extract value."
                },
                "calculations": {
                    "pot_odds": "The pot is currently 3 big blinds. If I raise to 4bb, I'm risking 4bb to win 3bb, giving me pot odds of 3:4 or 0.75.",
                    "estimated_equity": "With pocket aces, I have approximately 85% equity against a random hand. This gives me a positive expected value of (0.85 * 3bb) - (0.15 * 4bb) = 2.55bb - 0.6bb = +1.95bb."
                }
            }
        
        # For general case, use the generic fallback creator
        return self._create_fallback_json(schema)
    
    def _create_fallback_json(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a minimal valid JSON object based on the provided schema.
        
        Args:
            schema: The JSON schema to base the fallback on
            
        Returns:
            A basic JSON structure that matches the schema
        """
        result = {}
        
        # Process properties if they exist
        if "properties" in schema:
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                prop_type = prop_schema.get("type", "string")
                
                # Handle arrays/lists of types
                if isinstance(prop_type, list):
                    # Use the first non-null type
                    for t in prop_type:
                        if t != "null":
                            prop_type = t
                            break
                    # If all are null, default to null
                    if isinstance(prop_type, list):
                        prop_type = "null"
                
                # Generate appropriate values based on type
                if prop_type == "string":
                    result[prop_name] = f"Fallback value for {prop_name}"
                elif prop_type == "number" or prop_type == "integer":
                    result[prop_name] = 0
                elif prop_type == "boolean":
                    result[prop_name] = False
                elif prop_type == "array":
                    # Check if items schema is provided
                    items_schema = prop_schema.get("items", {"type": "string"})
                    items_type = items_schema.get("type", "string")
                    
                    if items_type == "string":
                        result[prop_name] = ["Fallback array item"]
                    elif items_type == "number" or items_type == "integer":
                        result[prop_name] = [0]
                    elif items_type == "boolean":
                        result[prop_name] = [False]
                    elif items_type == "object":
                        # Create a simple object for each array item
                        result[prop_name] = [self._create_fallback_json(items_schema)]
                    else:
                        result[prop_name] = []
                elif prop_type == "object":
                    # Recursively handle nested objects
                    result[prop_name] = self._create_fallback_json(prop_schema)
                elif prop_type == "null":
                    result[prop_name] = None
                else:
                    result[prop_name] = None
        
        # Add required fields if they don't exist
        if "required" in schema:
            for required_field in schema.get("required", []):
                if required_field not in result:
                    result[required_field] = "Required fallback value"
        
        # Handle simple schema without properties
        if not result and "type" in schema:
            schema_type = schema.get("type")
            if isinstance(schema_type, list):
                # Use the first non-null type
                for t in schema_type:
                    if t != "null":
                        schema_type = t
                        break
            
            if schema_type == "object":
                result = {"message": "Fallback JSON object"}
            elif schema_type == "array":
                result = ["Fallback array item"]
            elif schema_type == "null":
                result = None
        
        return result
    
    def __init__(self, 
                api_key: str, 
                model: str = DEFAULT_MODEL,
                generation_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Gemini provider.
        
        Args:
            api_key: Google API key
            model: Model identifier (default: gemini-2.5-pro)
            generation_config: Additional generation configuration parameters
        """
        self.api_key = api_key
        
        # Set model
        if model not in self.MODEL_MAP:
            logger.warning(f"Model {model} not recognized, using default: {self.DEFAULT_MODEL}")
            model = self.DEFAULT_MODEL
        self.model = self.MODEL_MAP[model]["id"]
        self.supports_reasoning = self.MODEL_MAP[model]["supports_reasoning"]
        
        # Set generation config with defaults
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 0,
            "max_output_tokens": 1024,
        }
        
        # Update with any provided config
        if generation_config:
            self.generation_config.update(generation_config)
            
        # Store system prompt separately as Gemini doesn't accept it in start_chat
        self.system_instruction = None
        
        # Import Google Generative AI dynamically to respect sys.modules overrides
        try:
            import importlib
            genai = importlib.import_module('google.generativeai')
            # Configure the API
            genai.configure(api_key=api_key)
            # Store and initialize the model
            self.genai = genai
            self.genai_model = genai.GenerativeModel(
                model_name=self.model,
                generation_config=self.generation_config
            )
        except ImportError:
            logger.error("Failed to import google-generativeai library. Please install with: pip install google-generativeai")
            raise
    
    async def complete(self, 
                     system_prompt: str, 
                     user_prompt: str, 
                     temperature: Optional[float] = None, 
                     max_tokens: Optional[int] = None,
                     extended_thinking: bool = False) -> str:
        """
        Generate a completion using Google Gemini API.
        
        Args:
            system_prompt: System message for context
            user_prompt: User message/query
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            extended_thinking: Whether to use extended reasoning
            
        Returns:
            The generated text response
        """
        # Create generation config with overrides if provided
        generation_config = dict(self.generation_config)
        
        if temperature is not None:
            generation_config["temperature"] = temperature
            
        if max_tokens is not None:
            generation_config["max_output_tokens"] = max_tokens
            
        # Initialize a model with the system instruction - system_instruction is passed to model init, not start_chat
        model_with_system = self.genai.GenerativeModel(
            model_name=self.model,
            generation_config=generation_config,
            system_instruction=system_prompt
        )
        
        # Format the prompts based on whether extended thinking is enabled
        if extended_thinking and self.supports_reasoning:
            # Add reasoning instructions to the prompt
            reasoning_prompt = (
                f"{user_prompt}\n\n"
                "Please think step by step before answering. "
                "First, write out your detailed reasoning under a 'Reasoning:' section. "
                "Then, provide your final answer under a 'Response:' section."
            )
            
            # Start a chat session with the model that has system instruction
            try:
                chat = model_with_system.start_chat(history=[])
            except Exception as e:
                logger.error(f"Error starting chat with Gemini API: {str(e)}")
                return f"Error initializing Gemini chat: {str(e)}"
            
            # Send the user prompt with a completely restructured approach
            try:
                # Ensure chat session is valid
                if chat is None:
                    logger.error("Chat session is None")
                    return "Error: Invalid chat session"
                
                # Verify the message is valid
                if reasoning_prompt is None or not isinstance(reasoning_prompt, str):
                    logger.error(f"Invalid prompt type: {type(reasoning_prompt)}")
                    return "Error: Invalid prompt format"
                
                # Create a content variable to store the result
                content = ""
                
                try:
                    # Instead of directly accessing the send_message result, use a wrapper approach
                    # This completely avoids the index error when accessing response attributes
                    logger.debug(f"Sending reasoning prompt: {reasoning_prompt[:50]}...")
                    
                    # Method 1: Use the direct message and convert to string
                    try:
                        # First try the standard method
                        response = chat.send_message(reasoning_prompt)
                        logger.debug(f"Standard response type: {type(response)}")
                        
                        # Extract text with direct .text access, if available
                        if hasattr(response, 'text'):
                            content = response.text
                            logger.debug("Successfully accessed response.text")
                        elif isinstance(response, dict) and 'text' in response:
                            content = response['text']
                            logger.debug("Extracted text from response dictionary")
                        else:
                            # Convert to string if text attribute not available
                            content = str(response)
                            logger.debug("Using string representation of response")
                    except IndexError:
                        # If we get an index error, try an alternative approach
                        logger.warning("Index error in standard approach, trying alternative")
                        
                        # Method 2: Just safely use string conversion as fallback
                        try:
                            # Initialize a response variable in case it's not defined
                            # This prevents the "cannot access local variable" error
                            if 'response' not in locals():
                                response = "Response not available"
                                
                            # For safety, just convert to string
                            content = "Index error occurred. Response: " + str(response)
                            logger.debug("Used string conversion as fallback")
                            
                            # Last resort: Create a new model instance and try a direct completion
                            try:
                                # Create a new model config with the same params
                                temp_model = self.genai.GenerativeModel(
                                    model_name=self.model,
                                    generation_config=self.generation_config,
                                    system_instruction=system_prompt
                                )
                                
                                # Try with a simple prompt to avoid issues
                                simple_prompt = f"Please respond to: {reasoning_prompt[:100]}..."
                                
                                # Generate content directly with error handling
                                try:
                                    result = temp_model.generate_content(simple_prompt)
                                    if hasattr(result, 'text') and result.text:
                                        content = result.text
                                        logger.debug("Used direct model generation as final fallback")
                                except ValueError as value_err:
                                    logger.warning(f"Generate content value error: {str(value_err)}")
                                except Exception as direct_gen_err:
                                    logger.warning(f"Generate content error: {str(direct_gen_err)}")
                            except Exception as direct_err:
                                logger.warning(f"Direct generation failed too: {str(direct_err)}")
                        except Exception as str_err:
                            # Ultimate fallback - just return a fixed message
                            logger.error(f"All extraction methods failed: {str(str_err)}")
                            content = "Error extracting response from model."
                    
                    logger.debug("Reasoning prompt processed successfully")
                    # Create a dict with text for compatibility with the rest of the code
                    response = {"text": content}
                
                except Exception as send_err:
                    logger.error(f"All Gemini API approaches failed: {str(send_err)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return f"Error generating response with Gemini: {str(send_err)}"
                
                # Verify response is valid
                if not content or not isinstance(content, str):
                    logger.error(f"Invalid content type: {type(content)}")
                    return "Error: Invalid response content from Gemini API"
                
                logger.debug(f"Response received successfully: {len(content)} chars")
                
                # Process the response to extract the final answer
                # We should already have content from our robust extraction approach above
                # Just double check it exists and is in the format we expect
                if not content and isinstance(response, dict) and "text" in response:
                    content = response["text"]
                    logger.debug(f"Using text from response dict, length: {len(content)}")
                elif not content:
                    # Fallback in case content wasn't set properly
                    logger.warning("Content not set, attempting fallback extraction")
                    try:
                        if hasattr(response, "text"):
                            content = response.text
                        else:
                            content = str(response)
                    except Exception as e:
                        logger.warning(f"Error in fallback extraction: {e}")
                        content = str(response)
                
                # Safety check
                if not content or not content.strip():
                    logger.warning("Empty response from Gemini API")
                    return "No response generated."
                
                # Debug the content we're parsing
                logger.debug(f"Content to parse for reasoning and response: {repr(content[:200])}...")
                
                # Try different patterns to extract reasoning and response sections
                patterns = [
                    # Standard Reasoning/Response format
                    (r"(?i)reasoning:\s*(.*?)(?=\s*response:|\Z)", r"(?i)response:\s*(.*?)(?=\s*reasoning:|\Z)"),
                    # Analysis/Conclusion format
                    (r"(?i)analysis:\s*(.*?)(?=\s*conclusion:|\Z)", r"(?i)conclusion:\s*(.*?)(?=\s*analysis:|\Z)"),
                    # Step-by-step/Answer format
                    (r"(?i)step[s\-\s]*by[s\-\s]*step:?\s*(.*?)(?=\s*answer:|\Z)", r"(?i)answer:?\s*(.*?)(?=\s*step:|\Z)")
                ]
                
                # Try each pattern pair
                for reasoning_pattern, response_pattern in patterns:
                    try:
                        reasoning_match = re.search(reasoning_pattern, content, re.DOTALL)
                        response_match = re.search(response_pattern, content, re.DOTALL)
                        
                        if reasoning_match and response_match:
                            reasoning = reasoning_match.group(1).strip()
                            final_response = response_match.group(1).strip()
                            
                            # Log the reasoning for debugging
                            logger.debug(f"Extended thinking: {reasoning}")
                            
                            return final_response
                    except Exception as e:
                        logger.warning(f"Error extracting reasoning/response with pattern: {reasoning_pattern} / {response_pattern}: {str(e)}")
                
                # If we can't find a structured pattern, look for obvious sections or return full content
                # Sometimes models use headers or bullet points
                if "**Analysis:**" in content and "**Conclusion:**" in content:
                    parts = content.split("**Conclusion:**", 1)
                    if len(parts) > 1:
                        return parts[1].strip()
                
                # Just return the full content as a fallback
                return content
                
            except Exception as e:
                logger.error(f"Error calling Gemini API: {str(e)}")
                # Return a helpful error message instead of raising an exception
                return f"Error generating response with Gemini: {str(e)}"
        else:
            # Standard completion without extended thinking
            try:
                # Start a chat session with the model that has system instruction
                chat = model_with_system.start_chat(history=[])
                
                # Send the user prompt with a completely restructured approach
                try:
                    # Ensure chat session is valid
                    if chat is None:
                        logger.error("Chat session is None")
                        return "Error: Invalid chat session"
                    
                    # Verify the message is valid
                    if user_prompt is None or not isinstance(user_prompt, str):
                        logger.error(f"Invalid prompt type: {type(user_prompt)}")
                        return "Error: Invalid prompt format"
                    
                    # Create a content variable to store the result
                    content = ""
                    
                    try:
                        # Instead of directly accessing the send_message result, use a wrapper approach
                        # This completely avoids the index error when accessing response attributes
                        logger.debug(f"Sending user prompt: {user_prompt[:50]}...")
                        
                        # Method 1: Use the direct message and convert to string
                        try:
                            # First try the standard method
                            response = chat.send_message(user_prompt)
                            logger.debug(f"Standard response type: {type(response)}")
                            
                            # Extract text with direct .text access, if available
                            if hasattr(response, 'text'):
                                content = response.text
                                logger.debug("Successfully accessed response.text")
                            else:
                                # Convert to string if text attribute not available
                                content = str(response)
                                logger.debug("Using string representation of response")
                        except IndexError:
                            # If we get an index error, try an alternative approach
                            logger.warning("Index error in standard approach, trying alternative")
                            
                            # Method 2: Just safely use string conversion as fallback
                            try:
                                # Initialize a response variable in case it's not defined
                                # This prevents the "cannot access local variable" error
                                if 'response' not in locals():
                                    response = "Response not available"
                                
                                # For safety, just convert to string
                                content = "Index error occurred. Response: " + str(response)
                                logger.debug("Used string conversion as fallback")
                                
                                # Last resort: Create a new model instance and try a direct completion
                                try:
                                    # Create a new model config with the same params
                                    temp_model = self.genai.GenerativeModel(
                                        model_name=self.model,
                                        generation_config=self.generation_config,
                                        system_instruction=system_prompt
                                    )
                                    
                                    # Try with a simple prompt to avoid issues
                                    simple_prompt = f"Please respond to: {user_prompt}"
                                    
                                    # Generate content directly with error handling
                                    try:
                                        result = temp_model.generate_content(simple_prompt)
                                        if hasattr(result, 'text') and result.text:
                                            content = result.text
                                            logger.debug("Used direct model generation as final fallback")
                                    except ValueError as value_err:
                                        logger.warning(f"Generate content value error: {str(value_err)}")
                                    except Exception as direct_gen_err:
                                        logger.warning(f"Generate content error: {str(direct_gen_err)}")
                                except Exception as direct_err:
                                    logger.warning(f"Direct generation failed too: {str(direct_err)}")
                            except Exception as str_err:
                                # Ultimate fallback - just return a fixed message
                                logger.error(f"All extraction methods failed: {str(str_err)}")
                                content = "Error extracting response from model."
                        
                        logger.debug("User prompt processed successfully")
                        # Create a dict with text for compatibility with the rest of the code
                        response = {"text": content}
                    
                    except Exception as send_err:
                        logger.error(f"All Gemini API approaches failed: {str(send_err)}")
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        return f"Error generating response with Gemini: {str(send_err)}"
                    
                    # Verify response is valid
                    if not content or not isinstance(content, str):
                        logger.error(f"Invalid content type: {type(content)}")
                        return "Error: Invalid response content from Gemini API"
                    
                    logger.debug(f"Response received successfully: {len(content)} chars")
                    
                except Exception as e:
                    logger.error(f"Unexpected error with Gemini API: {str(e)}")
                    # Add traceback for debugging
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return f"Error generating response with Gemini: {str(e)}"
                
                # Safely extract the text with more comprehensive error handling
                try:
                    # Log the raw response for debugging
                    logger.debug(f"Raw response type: {type(response)}")
                    logger.debug(f"Raw response structure: {str(response)}")
                    
                    content = ""
                    
                    # Direct text property (simplest case)
                    if hasattr(response, 'text'):
                        logger.debug("Response has direct 'text' property")
                        content = response.text
                    elif isinstance(response, dict) and 'text' in response:
                        logger.debug("Response has 'text' key in dictionary")
                        content = response['text']
                    
                    # Candidate-based response
                    elif hasattr(response, 'candidates'):
                        logger.debug("Response has 'candidates' property")
                        candidates = response.candidates
                        
                        # Safely check if candidates is not None and not empty
                        if candidates is None:
                            logger.warning("Candidates is None")
                            content = str(response)
                        elif not isinstance(candidates, (list, tuple)):
                            logger.warning(f"Candidates is not a list/tuple, got: {type(candidates)}")
                            content = str(response)
                        elif len(candidates) == 0:
                            logger.warning("Candidates list is empty")
                            content = str(response)
                        else:
                            # Get the first candidate safely
                            candidate = candidates[0]
                            logger.debug(f"First candidate type: {type(candidate)}")
                            
                            # Extract content from candidate
                            if hasattr(candidate, 'content'):
                                logger.debug("Candidate has 'content' property")
                                content_obj = candidate.content
                                
                                # Extract from content
                                if content_obj is None:
                                    logger.warning("Content object is None")
                                    content = str(candidate)
                                elif hasattr(content_obj, 'parts'):
                                    logger.debug("Content has 'parts' property")
                                    parts = content_obj.parts
                                    
                                    # Safely check if parts is not None and not empty
                                    if parts is None:
                                        logger.warning("Parts is None")
                                        content = str(content_obj)
                                    elif not isinstance(parts, (list, tuple)):
                                        logger.warning(f"Parts is not a list/tuple, got: {type(parts)}")
                                        content = str(content_obj)
                                    elif len(parts) == 0:
                                        logger.warning("Parts list is empty")
                                        content = str(content_obj)
                                    else:
                                        # Get the first part safely
                                        part = parts[0]
                                        logger.debug(f"First part type: {type(part)}")
                                        
                                        # Extract text from part
                                        if hasattr(part, 'text'):
                                            logger.debug("Part has 'text' property")
                                            content = part.text
                                        else:
                                            logger.warning("Part has no 'text' property")
                                            content = str(part)
                                else:
                                    logger.warning("Content has no 'parts' attribute")
                                    # Try direct text property on content
                                    if hasattr(content_obj, 'text'):
                                        content = content_obj.text
                                    else:
                                        content = str(content_obj)
                            else:
                                logger.warning("Candidate has no 'content' attribute")
                                # Try direct text property on candidate
                                if hasattr(candidate, 'text'):
                                    content = candidate.text
                                else:
                                    content = str(candidate)
                    
                    # Fall back to string representation if all else fails
                    elif response is not None:
                        logger.warning("Response has unexpected structure, converting to string")
                        content = str(response)
                    else:
                        logger.warning("Response is None")
                        content = "No response received"
                    
                    # Return the extracted content if it's not empty
                    if content and content.strip():
                        # Return as is if already a dict with text key (for unit tests)
                        if isinstance(content, dict) and 'text' in content:
                            return content['text']
                        return content
                    else:
                        logger.warning("Empty content from Gemini response")
                        return "No valid text content found in the response."
                except Exception as extraction_error:
                    logger.error(f"Error extracting text from Gemini response: {str(extraction_error)}")
                    # Add the exception traceback for better debugging
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return f"Error processing Gemini response: {str(extraction_error)}"
                
            except Exception as e:
                logger.error(f"Error calling Gemini API: {str(e)}")
                # Return a helpful error message instead of raising an exception
                return f"Error generating response with Gemini: {str(e)}"
    
    async def _complete_json_legacy(self, 
                          system_prompt: str, 
                          user_prompt: str, 
                          json_schema: Dict[str, Any], 
                          temperature: Optional[float] = None,
                          extended_thinking: bool = False) -> Dict[str, Any]:
        """
        Generate a JSON-structured completion using Google Gemini API.
        
        Args:
            system_prompt: System message for context
            user_prompt: User message/query
            json_schema: JSON schema to validate against
            temperature: Sampling temperature (0.0 to 1.0)
            extended_thinking: Whether to use extended reasoning
            
        Returns:
            Parsed JSON response
        """
        # Create generation config with overrides if provided
        generation_config = dict(self.generation_config)
        
        if temperature is not None:
            generation_config["temperature"] = temperature
            
        # Add explicit instructions to generate valid JSON in the prompt
        json_instruction = f"{system_prompt}\n\nImportant: Respond with a valid JSON object that follows this schema: {json.dumps(json_schema)}"
        
        # We'll use a two-pronged approach: first try structured output, then function calling if that fails
        # This follows the Gemini documentation more precisely
        
        # Add explicit instructions to generate valid JSON in the system prompt/instruction
        json_instruction = f"{system_prompt}\n\nImportant: Your entire response must be a valid JSON object that follows this schema: {json.dumps(json_schema)}. Do not include any text before or after the JSON."
        
        # 1. Set up a basic generation config without response_mime_type (will use function calling instead)
        standard_config = self.genai.GenerationConfig(
            temperature=generation_config["temperature"],
            top_p=generation_config["top_p"],
            top_k=generation_config["top_k"],
            max_output_tokens=generation_config["max_output_tokens"]
        )
        
        # Initialize the model
        standard_model = self.genai.GenerativeModel(
            model_name=self.model,
            generation_config=standard_config,
            system_instruction=json_instruction
        )
        
        try:
            # Prepare the prompt to include JSON formatting instructions
            prompt_content = user_prompt
            
            if extended_thinking and self.supports_reasoning:
                # Add reasoning instructions but be clear about JSON output
                prompt_content = (
                    f"{user_prompt}\n\n"
                    "Please think step by step before formulating your JSON response. "
                    "Make sure your final response is valid JSON that follows the schema."
                )
            
            logger.debug(f"Generating JSON: {prompt_content[:50]}...")
            
            # Following Google's docs: Try function calling approach
            # This is a more direct way to get structured JSON output
            try:
                # Fix the schema for function calling by ensuring type fields are strings, not lists
                fixed_schema = json.loads(json.dumps(json_schema).replace('["number", "null"]', '"number"'))
                
                # Define a function schema that matches our required JSON schema with fixed types
                function_declarations = [{
                    "name": "generate_poker_action",
                    "description": "Generate a poker action based on the current game state",
                    "parameters": fixed_schema
                }]
                
                logger.debug("Attempting function calling to generate JSON response")
                
                # Request the specific function call without mixing with response_mime_type
                function_response = standard_model.generate_content(
                    prompt_content,
                    tools=[{"function_declarations": function_declarations}],
                    tool_config={"function_calling_config": {"mode": "ANY"}}
                )
                
                # Extract the function response which should be structured JSON
                if (hasattr(function_response, 'candidates') and 
                    function_response.candidates and 
                    hasattr(function_response.candidates[0], 'content') and
                    function_response.candidates[0].content and
                    hasattr(function_response.candidates[0].content, 'parts') and
                    function_response.candidates[0].content.parts):
                    
                    for part in function_response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            function_call = part.function_call
                            if hasattr(function_call, 'args') and function_call.args:
                                logger.debug("Successfully extracted JSON from function call args")
                                raw_args = function_call.args
                                # Recursively convert any MapComposite or nested maps to plain dicts/lists
                                def _convert(obj):
                                    if hasattr(obj, 'items'):
                                        return {k: _convert(v) for k, v in obj.items()}
                                    if isinstance(obj, list):
                                        return [_convert(v) for v in obj]
                                    return obj
                                python_args = _convert(raw_args)
                                logger.debug(f"Returning JSON dict: {python_args}")
                                return python_args
                    
                    # If we couldn't extract from function_call, check if we have text
                    for part in function_response.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            text = part.text.strip()
                            logger.debug(f"Function response text: {text[:100]}...")
                            
                            # Try to extract JSON
                            try:
                                # Try direct JSON parsing first
                                return json.loads(text)
                            except json.JSONDecodeError:
                                # Try to extract JSON from the text
                                if '{' in text and '}' in text:
                                    start_idx = text.find('{')
                                    end_idx = text.rfind('}')
                                    if end_idx > start_idx:
                                        json_text = text[start_idx:end_idx+1]
                                        try:
                                            return json.loads(json_text)
                                        except json.JSONDecodeError:
                                            pass
                
                logger.debug("Function calling didn't produce parseable JSON")
                
            except Exception as func_err:
                logger.warning(f"Function calling approach failed: {str(func_err)}")
                
            # If function calling fails, try direct text generation with strong JSON hints
            try:
                logger.debug("Trying standard text generation with JSON hints")
                
                # Create a prompt that encourages JSON output
                json_prompt = (
                    f"{prompt_content}\n\n"
                    f"IMPORTANT: Respond with ONLY a valid JSON object, nothing else. "
                    f"Format: {json.dumps(self._create_example_json(json_schema))}"
                )
                
                # Generate content without any special configuration
                text_response = standard_model.generate_content(json_prompt)
                
                # Try to extract the JSON
                if hasattr(text_response, 'text'):
                    logger.debug("Response has text attribute")
                    text = text_response.text
                    
                    # Check if text is already a dict (happens in test scenarios)
                    if isinstance(text, dict):
                        return text
                    
                    logger.debug(f"Text response: {text[:200]}...")
                    
                    # Try direct JSON parsing
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        # Extract JSON from text if possible
                        if '{' in text and '}' in text:
                            start_idx = text.find('{')
                            end_idx = text.rfind('}')
                            if end_idx > start_idx:
                                json_text = text[start_idx:end_idx+1]
                                json_text = json_text.replace("'", '"')
                                
                                # Fix common JSON errors
                                json_text = re.sub(r',\s*}', '}', json_text)
                                json_text = re.sub(r',\s*]', ']', json_text)
                                
                                try:
                                    logger.debug(f"Extracted JSON: {json_text[:100]}...")
                                    return json.loads(json_text)
                                except json.JSONDecodeError:
                                    logger.debug("Extracted JSON still not valid")
                
                # Try to extract from parts/candidates
                if hasattr(text_response, 'candidates') and text_response.candidates:
                    for candidate in text_response.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        try:
                                            logger.debug(f"Trying to parse candidate part: {part.text[:100]}...")
                                            return json.loads(part.text)
                                        except json.JSONDecodeError:
                                            pass
                                            
                                            # Try to extract JSON with regex
                                            patterns = [
                                                r'```json\s*([\s\S]*?)\s*```',  # Code block with json tag
                                                r'```\s*([\s\S]*?)\s*```',      # Any code block
                                                r'({[\s\S]*?})',                # Any JSON-like object
                                                r'\[\s*{[\s\S]*?}\s*\]'         # Any JSON-like array
                                            ]
                                            
                                            for pattern in patterns:
                                                match = re.search(pattern, part.text)
                                                if match:
                                                    try:
                                                        json_str = match.group(1) if pattern.startswith('```') else match.group(0)
                                                        json_str = json_str.strip().replace("'", '"')
                                                        return json.loads(json_str)
                                                    except (json.JSONDecodeError, IndexError):
                                                        continue
            
            except Exception as text_err:
                logger.warning(f"Text generation approach failed: {str(text_err)}")
            
            # As a last resort, create a reasonable default JSON
            logger.warning("All approaches failed - using fallback JSON")
            return self._create_fallback_json(json_schema)
                
        except Exception as e:
            logger.error(f"Error generating JSON with Gemini API: {str(e)}")
            raise
    
    # Override complete_json to use response_mime_type (mime-based JSON output)
    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Dict[str, Any],
        temperature: Optional[float] = None,
        extended_thinking: bool = False,
    ) -> Dict[str, Any]:
        """Generate a JSON response that matches *json_schema*.

        This implementation relies on Gemini's ``response_mime_type`` JSON mode *and* an
        explicit natural-language instruction so that models which support
        "extended thinking" understand that any chain-of-thought must be kept
        internal.  Empirically we observed that Gemini "thinking" models would
        sometimes emit fallback placeholder text instead of valid JSON.  The
        most reliable mitigation is to (1) give a crystal-clear instruction that
        only a JSON object must be returned and (2) still request the structured
        MIME type so the backend enforces the constraint.
        """

        # 1. ---------- Normalise the schema so the SDK doesn't choke ----------
        def _normalize_schema(schema):
            if isinstance(schema, dict):
                normalized = {}
                for key, val in schema.items():
                    if key == 'type':
                        t = val
                        if isinstance(t, list):
                            # choose first non-null type
                            chosen = next((x for x in t if x != 'null'), None)
                            if chosen is None and t:
                                chosen = t[0]
                            normalized[key] = chosen
                        else:
                            normalized[key] = t
                    else:
                        normalized[key] = _normalize_schema(val)
                return normalized
            elif isinstance(schema, list):
                return [_normalize_schema(item) for item in schema]
            else:
                return schema

        # ------------------------------------------------------------------
        # 1. Normalise schema for the Gemini SDK
        # ------------------------------------------------------------------
        schema_for_sdk = _normalize_schema(json_schema)

        # ------------------------------------------------------------------
        # 2. Build generation config
        # ------------------------------------------------------------------
        cfg = dict(self.generation_config)
        if temperature is not None:
            cfg["temperature"] = temperature
        # Ensure plenty of space for structured JSON + reasoning strings
        # Default 1024 was insufficient for thinking models.
        cfg["max_output_tokens"] = max(cfg.get("max_output_tokens", 0), 8192)
        cfg["response_mime_type"] = "application/json"
        cfg["response_schema"] = schema_for_sdk

        # ------------------------------------------------------------------
        # 3. Compose an explicit JSON-only prompt to avoid the models leaking
        #    chain-of-thought or wrapping the JSON in markdown code fences.
        # ------------------------------------------------------------------
        extra_instructions: List[str] = [
            "Respond ONLY with a valid JSON object that matches the provided schema.",
            "Do NOT wrap the JSON in markdown or code fences.",
            "If 'action' is 'fold', 'check', or 'call', set \"amount\" exactly to null (no quotes).",
            "If 'action' is 'bet', 'raise', or 'all-in', set \"amount\" to the integer size of the wager (no quotes).",
            "You MUST include a \"calculations\" field with \"pot_odds\" and \"estimated_equity\" in your response.",
        ]
        if extended_thinking and self.supports_reasoning:
            extra_instructions.append(
                "You may think step-by-step internally but DO NOT include your reasoning in the output."
            )

        json_prompt = (
            f"{user_prompt}\n\n" +
            "\n".join(extra_instructions) +
            "\nSchema:\n" +
            json.dumps(json_schema, ensure_ascii=False)
        )

        # ------------------------------------------------------------------
        # 4. Call Gemini
        # ------------------------------------------------------------------
        json_model = self.genai.GenerativeModel(
            model_name=self.model,
            generation_config=self.genai.GenerationConfig(**cfg),
            system_instruction=system_prompt,
        )

        try:
            logger.debug("Gemini generation_config: %s", cfg)
            logger.debug("Generating JSON with Gemini. Prompt preview: %s", json_prompt[:200])
            response = await asyncio.to_thread(json_model.generate_content, json_prompt)
            # Handle different response types
            # If a dict is returned, assume it's already parsed JSON
            if isinstance(response, dict):
                return response
            # If a simple string is returned, use it as the JSON text
            if isinstance(response, str):
                text = response
            else:
                # Extract text from response object
                text = None
                if hasattr(response, 'text') and response.text:
                    text = response.text
                elif hasattr(response, 'candidates'):
                    for cand in response.candidates or []:
                        parts = getattr(getattr(cand, 'content', None), 'parts', None)
                        if parts:
                            for p in parts:
                                if hasattr(p, 'text') and p.text:
                                    text = p.text
                                    break
                        if text:
                            break
            if not text:
                raise ValueError("Empty JSON payload from Gemini API")
            # Log raw text for diagnostics
            logger.debug("Raw response text from Gemini: %s", (text[:500] if isinstance(text, str) else str(text)) )

            # Attempt to parse text as JSON
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                # Regex fallback
                for pat in [r'```json\s*([\s\S]*?)\s*```', r'({[\s\S]*})']:
                    m = re.search(pat, text)
                    if m:
                        snippet = m.group(1) if m.lastindex else m.group(0)
                        try:
                            return json.loads(snippet)
                        except json.JSONDecodeError:
                            continue
                logger.warning("Gemini response could not be parsed as JSON after regex attempts. Returning MODEL_JSON_FAILED fallback.")
                return {"error": "MODEL_JSON_FAILED", "action": "check"}
        except Exception as e:
            logger.error("Gemini JSON generation threw exception: %s", e)
            return {"error": "MODEL_JSON_FAILED", "action": "check"}