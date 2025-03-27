"""
Provider abstraction layer for LLM services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union

class LLMProvider(ABC):
    """Base abstract class for LLM providers."""
    
    @abstractmethod
    async def complete(self, 
                      system_prompt: str, 
                      user_prompt: str, 
                      temperature: float = 0.7, 
                      max_tokens: Optional[int] = None,
                      extended_thinking: bool = False) -> str:
        """
        Generate a completion using the provider's API.
        
        Args:
            system_prompt: System message for context
            user_prompt: User message/query
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            extended_thinking: Whether to use extended thinking capabilities
            
        Returns:
            The generated text response
        """
        pass
    
    @abstractmethod
    async def complete_json(self, 
                          system_prompt: str, 
                          user_prompt: str, 
                          json_schema: Dict[str, Any], 
                          temperature: float = 0.7,
                          extended_thinking: bool = False) -> Dict[str, Any]:
        """
        Generate a JSON-structured completion using the provider's API.
        
        Args:
            system_prompt: System message for context
            user_prompt: User message/query
            json_schema: JSON schema to validate against
            temperature: Sampling temperature (0.0 to 1.0)
            extended_thinking: Whether to use extended thinking capabilities
            
        Returns:
            Parsed JSON response
        """
        pass

# Import specific providers
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider

__all__ = ['LLMProvider', 'AnthropicProvider', 'OpenAIProvider', 'GeminiProvider']