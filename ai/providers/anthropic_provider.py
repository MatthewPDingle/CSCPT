"""
Anthropic Claude provider implementation.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List, Union

from . import LLMProvider

logger = logging.getLogger(__name__)

class AnthropicProvider(LLMProvider):
    """Provider implementation for Anthropic Claude API."""
    
    def __init__(self, api_key: str, model: str = "claude-3-7-sonnet-20250219", thinking_budget_tokens: int = 4000):
        """
        Initialize the Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            model: Model identifier (default: claude-3-7-sonnet-20250219)
            thinking_budget_tokens: Number of tokens allocated for extended thinking
        """
        self.api_key = api_key
        self.model = model
        self.thinking_budget_tokens = thinking_budget_tokens
        
        # Import anthropic here to avoid global import issues
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            logger.error("Failed to import anthropic library. Please install with: pip install anthropic")
            raise
    
    async def complete(self, 
                     system_prompt: str, 
                     user_prompt: str, 
                     temperature: float = 0.7, 
                     max_tokens: Optional[int] = None,
                     extended_thinking: bool = False) -> str:
        """
        Generate a completion using Anthropic Claude API.
        
        Args:
            system_prompt: System message for context
            user_prompt: User message/query
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            extended_thinking: Whether to use extended thinking mode
            
        Returns:
            The generated text response
        """
        # Set appropriate max_tokens
        if max_tokens is None:
            max_tokens = 1024
            
        # Anthropic's extended thinking requires max_tokens > thinking_budget_tokens
        if extended_thinking:
            if max_tokens <= self.thinking_budget_tokens:
                max_tokens = self.thinking_budget_tokens + 1024  # Make sure we have enough tokens for both thinking and response
                logger.debug(f"Increased max_tokens to {max_tokens} to accommodate extended thinking")
            
            # API requires temperature=1.0 when extended thinking is enabled
            logger.debug(f"Setting temperature to 1.0 for extended thinking (was {temperature})")
            temperature = 1.0

        params = {
            "model": self.model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if extended_thinking:
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget_tokens
            }
        
        try:
            # Note: Using sync API here - the Anthropic library doesn't appear to expose
            # async methods, but we keep the async interface for consistency with other providers
            response = self.client.messages.create(**params)
            
            # If we used extended thinking, we might want to log or use the thinking content
            has_thinking = False
            for content_item in response.content:
                if hasattr(content_item, 'type') and content_item.type == "thinking":
                    thinking_content = content_item.thinking
                    logger.debug(f"Extended thinking: {thinking_content}")
                    has_thinking = True
            
            # Extract the text content from the response
            for content_item in response.content:
                if hasattr(content_item, 'type') and content_item.type == "text":
                    return content_item.text
            
            # Fallback if no text content found (older API versions)
            if hasattr(response, 'content') and isinstance(response.content, list) and len(response.content) > 0:
                if hasattr(response.content[0], 'text'):
                    return response.content[0].text
                    
            # Last resort fallback
            return str(response.content)
            
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            raise
    
    async def complete_json(self, 
                          system_prompt: str, 
                          user_prompt: str, 
                          json_schema: Dict[str, Any], 
                          temperature: float = 0.7,
                          extended_thinking: bool = False) -> Dict[str, Any]:
        """
        Generate a JSON-structured completion using Anthropic Claude API.
        
        Args:
            system_prompt: System message for context
            user_prompt: User message/query
            json_schema: JSON schema to validate against
            temperature: Sampling temperature (0.0 to 1.0)
            extended_thinking: Whether to use extended thinking mode
            
        Returns:
            Parsed JSON response
        """
        # Add instructions to generate valid JSON
        json_instruction = f"Respond with a JSON object that follows this schema: {json.dumps(json_schema)}"
        combined_prompt = f"{user_prompt}\n\n{json_instruction}"
        
        response_text = await self.complete(
            system_prompt=system_prompt,
            user_prompt=combined_prompt,
            temperature=temperature,
            extended_thinking=extended_thinking
        )
        
        # Extract and parse the JSON response
        try:
            # Try to parse the entire response as JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON with regex
            json_pattern = r'```json\s*([\s\S]*?)\s*```'
            match = re.search(json_pattern, response_text)
            if match:
                return json.loads(match.group(1))
            else:
                # Try one more pattern that might capture JSON
                json_pattern = r'{[\s\S]*}'
                match = re.search(json_pattern, response_text)
                if match:
                    return json.loads(match.group(0))
                else:
                    logger.error(f"Could not extract valid JSON from response: {response_text}")
                    raise ValueError("Could not extract valid JSON from response")