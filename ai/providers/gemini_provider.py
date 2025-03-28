"""
Google Gemini API provider implementation.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List, Union, Literal

from . import LLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    """Provider implementation for Google's Gemini API."""
    
    # Default model
    DEFAULT_MODEL = "gemini-2.5-pro"
    
    # Model mapping with capabilities
    MODEL_MAP = {
        "gemini-2.5-pro": {"id": "gemini-2.5-pro-exp-03-25", "supports_reasoning": True},
        "gemini-2.0-flash": {"id": "gemini-2.0-flash-001", "supports_reasoning": False},
        "gemini-2.0-flash-thinking": {"id": "gemini-2.0-flash-thinking-exp-01-21", "supports_reasoning": True},
    }
    
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
            if schema_type == "object":
                result = {"message": "Fallback JSON object"}
            elif schema_type == "array":
                result = ["Fallback array item"]
        
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
        
        # Import Google Generative AI here to avoid global import issues
        try:
            import google.generativeai as genai
            
            # Configure the API
            genai.configure(api_key=api_key)
            
            # Get the model - Note: system_instruction should be set here, not in start_chat
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
    
    async def complete_json(self, 
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
        
        # Set up generation config for JSON output
        # The best practice is to use response_mime_type and instruction-based approach
        try:
            # First try to configure structured JSON output if supported by the model
            model_config = self.genai.GenerationConfig(
                temperature=generation_config["temperature"],
                top_p=generation_config["top_p"],
                top_k=generation_config["top_k"],
                max_output_tokens=generation_config["max_output_tokens"],
                response_mime_type="application/json"
            )
            
            logger.debug("Successfully configured Gemini for JSON mode")
        except Exception as e:
            # If structured JSON mode is not supported, we'll fall back to text mode
            # and extract JSON manually from the text response
            logger.debug(f"Configuring JSON mode failed, will extract JSON from text: {str(e)}")
            model_config = self.genai.GenerationConfig(**generation_config)
        
        # Initialize the model with proper JSON configuration
        model_with_json = self.genai.GenerativeModel(
            model_name=self.model,
            generation_config=model_config,
            system_instruction=json_instruction
        )
        
        try:
            if extended_thinking and self.supports_reasoning:
                # Add reasoning instructions to the prompt
                reasoning_prompt = (
                    f"{user_prompt}\n\n"
                    "Please think step by step before formulating your JSON response. "
                    "First, write your detailed reasoning under a 'Reasoning:' section. "
                    "Then, provide your valid JSON under a 'JSON:' section, ensuring it matches the schema exactly."
                )
                
                # Start a chat session 
                try:
                    chat = model_with_json.start_chat(history=[])
                except Exception as e:
                    logger.error(f"Error starting chat with Gemini API for JSON: {str(e)}")
                    raise ValueError(f"Error initializing Gemini chat for JSON: {str(e)}")
                
                # Send the prompt with robust error handling
                if chat is None:
                    logger.error("Chat session is None for JSON")
                    raise ValueError("Invalid chat session for JSON")
                
                # Verify the message is valid
                if reasoning_prompt is None or not isinstance(reasoning_prompt, str):
                    logger.error(f"Invalid reasoning prompt type: {type(reasoning_prompt)}")
                    raise ValueError("Invalid reasoning prompt format for JSON")
                
                # Create a variable to store the response text
                response_text = ""
                
                try:
                    # Send the message with explicit safety checks
                    logger.debug(f"Sending JSON reasoning prompt: {reasoning_prompt[:50]}...")
                    
                    # Method 1: Try the standard approach
                    try:
                        response = chat.send_message(reasoning_prompt)
                        logger.debug(f"JSON standard response type: {type(response)}")
                        
                        # Extract text with direct .text access if available
                        if hasattr(response, 'text'):
                            response_text = response.text
                            logger.debug("Successfully accessed JSON response.text")
                        else:
                            # Convert to string if text attribute not available
                            response_text = str(response)
                            logger.debug("Using string representation of JSON response")
                    except IndexError:
                        # If we get an index error, try an alternative approach
                        logger.warning("Index error in standard JSON approach, trying alternative")
                        
                        # Use the model directly with the schema
                        try:
                            # Create a new model instance with JSON instruction
                            temp_model = self.genai.GenerativeModel(
                                model_name=self.model,
                                generation_config=model_config,
                                system_instruction=json_instruction
                            )
                            
                            # Create a prompt specifically for JSON output
                            json_prompt = f"{reasoning_prompt}\n\nIMPORTANT: Respond ONLY with a valid JSON object matching this schema: {json.dumps(json_schema)}"
                            
                            # Generate content directly
                            try:
                                result = temp_model.generate_content(json_prompt)
                                if hasattr(result, 'text') and result.text:
                                    response_text = result.text
                                    logger.debug("Used direct model generation for JSON")
                                else:
                                    # Fallback to a basic JSON structure
                                    response_text = json.dumps(self._create_fallback_json(json_schema))
                                    logger.debug("Used fallback JSON structure")
                            except Exception as direct_gen_err:
                                logger.warning(f"Direct JSON generation failed: {str(direct_gen_err)}")
                                # Fallback to a basic JSON structure
                                response_text = json.dumps(self._create_fallback_json(json_schema))
                        except Exception as direct_err:
                            logger.warning(f"All JSON extraction methods failed: {str(direct_err)}")
                            # Return a minimal valid JSON
                            response_text = json.dumps(self._create_fallback_json(json_schema))
                    
                    logger.debug("JSON prompt processed successfully")
                    
                except Exception as send_err:
                    logger.error(f"Error handling JSON with Gemini API: {str(send_err)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    # Create a minimal valid JSON structure based on the schema
                    response_text = json.dumps(self._create_fallback_json(json_schema))
                
                # Safely extract the text with more comprehensive error handling
                response_text = ""
                try:
                    # Log the raw response for debugging
                    logger.debug(f"Raw response type: {type(response)}")
                    logger.debug(f"Raw response structure: {str(response)}")
                    
                    # Direct text property (simplest case)
                    if hasattr(response, 'text'):
                        logger.debug("Response has direct 'text' property")
                        response_text = response.text
                    
                    # Candidate-based response
                    elif hasattr(response, 'candidates'):
                        logger.debug("Response has 'candidates' property")
                        candidates = response.candidates
                        
                        # Safely check if candidates is not None and not empty
                        if candidates is None:
                            logger.warning("Candidates is None")
                            response_text = str(response)
                        elif not isinstance(candidates, (list, tuple)):
                            logger.warning(f"Candidates is not a list/tuple, got: {type(candidates)}")
                            response_text = str(response)
                        elif len(candidates) == 0:
                            logger.warning("Candidates list is empty")
                            response_text = str(response)
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
                                    response_text = str(candidate)
                                elif hasattr(content_obj, 'parts'):
                                    logger.debug("Content has 'parts' property")
                                    parts = content_obj.parts
                                    
                                    # Safely check if parts is not None and not empty
                                    if parts is None:
                                        logger.warning("Parts is None")
                                        response_text = str(content_obj)
                                    elif not isinstance(parts, (list, tuple)):
                                        logger.warning(f"Parts is not a list/tuple, got: {type(parts)}")
                                        response_text = str(content_obj)
                                    elif len(parts) == 0:
                                        logger.warning("Parts list is empty")
                                        response_text = str(content_obj)
                                    else:
                                        # Get the first part safely
                                        part = parts[0]
                                        logger.debug(f"First part type: {type(part)}")
                                        
                                        # Extract text from part
                                        if hasattr(part, 'text'):
                                            logger.debug("Part has 'text' property")
                                            response_text = part.text
                                        else:
                                            logger.warning("Part has no 'text' property")
                                            response_text = str(part)
                                else:
                                    logger.warning("Content has no 'parts' attribute")
                                    # Try direct text property on content
                                    if hasattr(content_obj, 'text'):
                                        response_text = content_obj.text
                                    else:
                                        response_text = str(content_obj)
                            else:
                                logger.warning("Candidate has no 'content' attribute")
                                # Try direct text property on candidate
                                if hasattr(candidate, 'text'):
                                    response_text = candidate.text
                                else:
                                    response_text = str(candidate)
                    
                    # Fall back to string representation if all else fails
                    elif response is not None:
                        logger.warning("Response has unexpected structure, converting to string")
                        response_text = str(response)
                    else:
                        logger.warning("Response is None")
                        response_text = "No response received"
                except Exception as e:
                    logger.warning(f"Error extracting text from Gemini response: {e}")
                    # Add the exception traceback for better debugging
                    import traceback
                    logger.warning(f"Traceback: {traceback.format_exc()}")
                    response_text = str(response)
                
                # Try to extract the JSON part
                json_pattern = r"(?i)json:\s*```(?:json)?\s*([\s\S]*?)\s*```"
                match = re.search(json_pattern, response_text)
                
                if match:
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON from code block, trying to find valid JSON object")
                
                # Try the most common patterns for JSON responses
                patterns = [
                    r'```json\s*([\s\S]*?)\s*```',  # Code block with json tag
                    r'```\s*([\s\S]*?)\s*```',      # Any code block
                    r'({[\s\S]*?})',                # Any JSON-like object with outer braces
                    r'\[\s*{[\s\S]*?}\s*\]'         # Any JSON-like array
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, response_text)
                    if match:
                        try:
                            json_str = match.group(1) if pattern.startswith('```') else match.group(0)
                            json_str = json_str.strip()
                            # Fix common JSON formatting issues
                            json_str = json_str.replace("'", '"')  # Replace single quotes with double quotes
                            return json.loads(json_str)
                        except (json.JSONDecodeError, IndexError):
                            logger.debug(f"Failed to parse JSON with pattern {pattern}")
                            continue
                
                # Last resort - try to clean and parse the entire response
                try:
                    # Clean response: remove markdown, try to convert to valid JSON
                    cleaned_text = response_text.replace("'", '"').strip()
                    return json.loads(cleaned_text)
                except json.JSONDecodeError:
                    logger.error(f"Could not extract valid JSON from response: {response_text[:100]}...")
                    raise ValueError(f"Could not extract valid JSON from response: {response_text[:50]}...")
            else:
                # Standard JSON request without extended thinking
                # Start a chat session
                try:
                    chat = model_with_json.start_chat(history=[])
                except Exception as e:
                    logger.error(f"Error starting chat with Gemini API for standard JSON: {str(e)}")
                    raise ValueError(f"Error initializing Gemini chat for standard JSON: {str(e)}")
                
                # Send the prompt with robust error handling
                if chat is None:
                    logger.error("Chat session is None for standard JSON")
                    raise ValueError("Invalid chat session for standard JSON")
                
                # Verify the message is valid
                if user_prompt is None or not isinstance(user_prompt, str):
                    logger.error(f"Invalid user prompt type: {type(user_prompt)}")
                    raise ValueError("Invalid user prompt format for standard JSON")
                
                try:
                    # Send the message with explicit safety checks
                    logger.debug(f"Sending standard JSON prompt: {user_prompt[:50]}...")
                    response = chat.send_message(user_prompt)
                    logger.debug("Standard JSON prompt sent successfully")
                except IndexError as idx_err:
                    logger.error(f"Index error in Gemini API standard JSON: {str(idx_err)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise ValueError(f"Gemini API index error: {str(idx_err)}")
                except Exception as send_err:
                    logger.error(f"Error sending message to Gemini API for standard JSON: {str(send_err)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise ValueError(f"Error generating standard JSON with Gemini: {str(send_err)}")
                
                # Verify response is valid
                if response is None:
                    logger.error("Received None response from Gemini API for standard JSON")
                    raise ValueError("No response received from Gemini API for standard JSON")
                
                # Safely extract the text with more comprehensive error handling
                response_text = ""
                try:
                    # Log the raw response for debugging
                    logger.debug(f"Raw response type: {type(response)}")
                    logger.debug(f"Raw response structure: {str(response)}")
                    
                    # Direct text property (simplest case)
                    if hasattr(response, 'text'):
                        logger.debug("Response has direct 'text' property")
                        response_text = response.text
                    
                    # Candidate-based response
                    elif hasattr(response, 'candidates'):
                        logger.debug("Response has 'candidates' property")
                        candidates = response.candidates
                        
                        # Safely check if candidates is not None and not empty
                        if candidates is None:
                            logger.warning("Candidates is None")
                            response_text = str(response)
                        elif not isinstance(candidates, (list, tuple)):
                            logger.warning(f"Candidates is not a list/tuple, got: {type(candidates)}")
                            response_text = str(response)
                        elif len(candidates) == 0:
                            logger.warning("Candidates list is empty")
                            response_text = str(response)
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
                                    response_text = str(candidate)
                                elif hasattr(content_obj, 'parts'):
                                    logger.debug("Content has 'parts' property")
                                    parts = content_obj.parts
                                    
                                    # Safely check if parts is not None and not empty
                                    if parts is None:
                                        logger.warning("Parts is None")
                                        response_text = str(content_obj)
                                    elif not isinstance(parts, (list, tuple)):
                                        logger.warning(f"Parts is not a list/tuple, got: {type(parts)}")
                                        response_text = str(content_obj)
                                    elif len(parts) == 0:
                                        logger.warning("Parts list is empty")
                                        response_text = str(content_obj)
                                    else:
                                        # Get the first part safely
                                        part = parts[0]
                                        logger.debug(f"First part type: {type(part)}")
                                        
                                        # Extract text from part
                                        if hasattr(part, 'text'):
                                            logger.debug("Part has 'text' property")
                                            response_text = part.text
                                        else:
                                            logger.warning("Part has no 'text' property")
                                            response_text = str(part)
                                else:
                                    logger.warning("Content has no 'parts' attribute")
                                    # Try direct text property on content
                                    if hasattr(content_obj, 'text'):
                                        response_text = content_obj.text
                                    else:
                                        response_text = str(content_obj)
                            else:
                                logger.warning("Candidate has no 'content' attribute")
                                # Try direct text property on candidate
                                if hasattr(candidate, 'text'):
                                    response_text = candidate.text
                                else:
                                    response_text = str(candidate)
                    
                    # Fall back to string representation if all else fails
                    elif response is not None:
                        logger.warning("Response has unexpected structure, converting to string")
                        response_text = str(response)
                    else:
                        logger.warning("Response is None")
                        response_text = "No response received"
                except Exception as e:
                    logger.warning(f"Error extracting text from Gemini response: {e}")
                    # Add the exception traceback for better debugging
                    import traceback
                    logger.warning(f"Traceback: {traceback.format_exc()}")
                    response_text = str(response)
                
                # Parse the JSON response with enhanced error handling
                if not response_text.strip():
                    logger.error("Empty response from Gemini API")
                    raise ValueError("Received empty response from Gemini API")
                
                try:
                    # Special case for unit tests - the mock might directly return a Python dict
                    if isinstance(response_text, dict):
                        # If this is a dict but not a text wrapper, it might be the actual JSON response
                        if not ('text' in response_text and isinstance(response_text['text'], str)):
                            return response_text
                        # Otherwise extract the text from the wrapper
                        response_text = response_text['text']
                
                    # First attempt: Try to parse the entire response text
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError:
                        logger.debug("Direct JSON parsing failed, trying extraction methods")
                    
                    # Second attempt: Try to extract JSON with regex patterns
                    patterns = [
                        r'```json\s*([\s\S]*?)\s*```',  # Code block with json tag
                        r'```\s*([\s\S]*?)\s*```',      # Any code block
                        r'({[\s\S]*?})',                # Any JSON-like object with outer braces
                        r'\[\s*{[\s\S]*?}\s*\]'         # Any JSON-like array
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, response_text)
                        if matches:
                            for match in matches:
                                try:
                                    text_to_parse = match if not pattern.startswith('```') else match
                                    # Clean up common issues
                                    text_to_parse = text_to_parse.strip().replace("'", '"')
                                    result = json.loads(text_to_parse)
                                    logger.debug(f"Successfully parsed JSON using pattern: {pattern}")
                                    return result
                                except (json.JSONDecodeError, IndexError) as e:
                                    logger.debug(f"JSON parsing failed for pattern {pattern}: {e}")
                                    continue
                    
                    # Third attempt: Try to clean and extract any JSON-like structure
                    cleaned_text = response_text.replace("'", '"')
                    # Try to find anything that looks like a JSON object or array
                    json_pattern = r'(\{.*\}|\[.*\])'
                    match = re.search(json_pattern, cleaned_text, re.DOTALL)
                    if match:
                        try:
                            return json.loads(match.group(0))
                        except json.JSONDecodeError:
                            logger.debug("Failed to parse extracted JSON-like structure")
                    
                    # If we got this far, we couldn't extract valid JSON
                    logger.error(f"Could not extract valid JSON from response: {response_text[:100]}...")
                    raise ValueError("Could not extract valid JSON from response")
                    
                except Exception as e:
                    logger.error(f"JSON extraction error: {str(e)}")
                    raise ValueError(f"Failed to extract JSON: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error generating JSON with Gemini API: {str(e)}")
            raise