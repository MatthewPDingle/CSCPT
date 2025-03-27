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
            chat = model_with_system.start_chat(history=[])
            
            # Send the user prompt
            try:
                response = chat.send_message(reasoning_prompt)
                
                # Process the response to extract the final answer
                # Safely extract the text
                if hasattr(response, 'text'):
                    content = response.text
                elif hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        if parts and len(parts) > 0:
                            content = parts[0].text
                        else:
                            content = str(response)
                    else:
                        content = str(response)
                else:
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
                
                # Send the user prompt
                response = chat.send_message(user_prompt)
                
                # Safely extract the text
                if hasattr(response, 'text'):
                    return response.text
                elif hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        if parts and len(parts) > 0:
                            return parts[0].text
                
                # Fallback to string representation
                return str(response)
                
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
            
        # Add instructions to generate valid JSON
        json_instruction = f"{system_prompt}\n\nRespond with a valid JSON object that follows this schema: {json.dumps(json_schema)}"
        
        # Initialize a model with the system instruction
        # Some models might not support JSON mode
        try:
            # Set response_mime_type in generation_config, not as a direct parameter
            generation_config["response_mime_type"] = "application/json"
            
            # Add JSON schema to the generation config
            generation_config["response_schema"] = json_schema
        except Exception as e:
            # If setting JSON mode fails, we'll extract JSON manually from the text response
            logger.debug(f"Setting JSON mode failed, will extract manually: {str(e)}")
        
        model_with_json = self.genai.GenerativeModel(
            model_name=self.model,
            generation_config=self.genai.GenerationConfig(**generation_config),
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
                
                # Start a chat session and send the prompt
                chat = model_with_json.start_chat(history=[])
                response = chat.send_message(reasoning_prompt)
                
                # Safely extract the text
                if hasattr(response, 'text'):
                    response_text = response.text
                elif hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        if parts and len(parts) > 0:
                            response_text = parts[0].text
                        else:
                            response_text = str(response)
                    else:
                        response_text = str(response)
                else:
                    response_text = str(response)
                
                # Try to extract the JSON part
                json_pattern = r"(?i)json:\s*```(?:json)?\s*([\s\S]*?)\s*```"
                match = re.search(json_pattern, response_text)
                
                if match:
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError:
                        # Try one more pattern that might capture JSON
                        json_pattern = r'{[\s\S]*}'
                        match = re.search(json_pattern, response_text)
                        if match:
                            return json.loads(match.group(0))
                        else:
                            logger.error(f"Could not extract valid JSON from response: {response_text}")
                            raise ValueError("Could not extract valid JSON from response")
                else:
                    # If no JSON section was found, try to parse the whole response as JSON
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError:
                        # Try to extract any JSON object in the text
                        json_pattern = r'{[\s\S]*}'
                        match = re.search(json_pattern, response_text)
                        if match:
                            return json.loads(match.group(0))
                        else:
                            logger.error(f"Could not extract valid JSON from response: {response_text}")
                            raise ValueError("Could not extract valid JSON from response")
            else:
                # Standard JSON request without extended thinking
                # Start a chat session and send the prompt
                chat = model_with_json.start_chat(history=[])
                response = chat.send_message(user_prompt)
                
                # Safely extract the text
                if hasattr(response, 'text'):
                    response_text = response.text
                elif hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        if parts and len(parts) > 0:
                            response_text = parts[0].text
                        else:
                            response_text = str(response)
                    else:
                        response_text = str(response)
                else:
                    response_text = str(response)
                
                # Parse the JSON response
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    # Try to extract JSON with regex patterns
                    patterns = [
                        r'```json\s*([\s\S]*?)\s*```',  # Code block with json tag
                        r'```\s*([\s\S]*?)\s*```',      # Any code block
                        r'{[\s\S]*}'                    # Any JSON object
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, response_text)
                        if match:
                            try:
                                return json.loads(match.group(1) if pattern.startswith('```') else match.group(0))
                            except (json.JSONDecodeError, IndexError):
                                continue
                    
                    logger.error(f"Could not extract valid JSON from response: {response_text}")
                    raise ValueError("Could not extract valid JSON from response")
                    
        except Exception as e:
            logger.error(f"Error generating JSON with Gemini API: {str(e)}")
            raise