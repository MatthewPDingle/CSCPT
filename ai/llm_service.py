"""
LLM Service module for interacting with different LLM providers.
"""

import logging
from typing import Dict, Any, Optional, Union, List

from .config import AIConfig
from .providers import LLMProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.openai_provider import OpenAIProvider
from .providers.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with Language Model APIs."""
    
    def __init__(self, config: Optional[Union[Dict[str, Any], str]] = None):
        """
        Initialize the LLM service.
        
        Args:
            config: Either a configuration dictionary, a path to a config file,
                  or None to use environment variables
        """
        # Load configuration
        if isinstance(config, dict):
            self.config = config
            self.ai_config = None  # We'll use the provided dict directly
        else:
            self.ai_config = AIConfig(config_path=config if isinstance(config, str) else None)
            self.config = {}  # Will be populated on demand
        
        self.providers = {}  # Cache for initialized providers
    
    def _get_provider(self, provider_name: Optional[str] = None) -> LLMProvider:
        """
        Get or initialize a provider instance.
        
        Args:
            provider_name: Name of the provider to use, or None for default
            
        Returns:
            An instance of a LLMProvider
        """
        # Determine which provider to use
        if provider_name is None:
            if self.ai_config:
                provider_name = self.ai_config.get_default_provider()
            else:
                provider_name = self.config.get("default_provider", "anthropic")
        
        # Return from cache if already initialized
        if provider_name in self.providers:
            return self.providers[provider_name]
        
        # Initialize the requested provider
        if provider_name == "anthropic":
            if self.ai_config:
                provider_config = self.ai_config.get_provider_config("anthropic")
            else:
                provider_config = self.config.get("anthropic", {})
            
            # Extract necessary parameters
            api_key = provider_config.get("api_key")
            if not api_key:
                raise ValueError("Anthropic API key not configured")
                
            model = provider_config.get("model", "claude-3-7-sonnet-20250219")
            thinking_budget = provider_config.get("thinking_budget_tokens", 4000)
            
            # Create and cache the provider
            provider = AnthropicProvider(api_key=api_key, model=model, thinking_budget_tokens=thinking_budget)
            self.providers[provider_name] = provider
            return provider
            
        elif provider_name == "openai":
            if self.ai_config:
                provider_config = self.ai_config.get_provider_config("openai")
            else:
                provider_config = self.config.get("openai", {})
            
            # Extract necessary parameters
            api_key = provider_config.get("api_key")
            if not api_key:
                raise ValueError("OpenAI API key not configured")
                
            model = provider_config.get("model", "gpt-4o")
            reasoning_level = provider_config.get("reasoning_level", "medium")
            organization_id = provider_config.get("organization_id")
            
            # Create and cache the provider
            provider = OpenAIProvider(
                api_key=api_key, 
                model=model, 
                reasoning_level=reasoning_level,
                organization_id=organization_id
            )
            self.providers[provider_name] = provider
            return provider
            
        elif provider_name == "gemini":
            if self.ai_config:
                provider_config = self.ai_config.get_provider_config("gemini")
            else:
                provider_config = self.config.get("gemini", {})
            
            # Extract necessary parameters
            api_key = provider_config.get("api_key")
            if not api_key:
                raise ValueError("Gemini API key not configured")
                
            model = provider_config.get("model", "gemini-1.5-pro")
            generation_config = provider_config.get("generation_config", {})
            
            # Create and cache the provider
            provider = GeminiProvider(
                api_key=api_key, 
                model=model, 
                generation_config=generation_config
            )
            self.providers[provider_name] = provider
            return provider
            
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
    
    async def complete(self, 
                     system_prompt: str, 
                     user_prompt: str, 
                     temperature: Optional[float] = None, 
                     max_tokens: Optional[int] = None,
                     provider: Optional[str] = None,
                     extended_thinking: bool = False) -> str:
        """
        Generate a completion from the LLM.
        
        Args:
            system_prompt: System message for the LLM
            user_prompt: User message for the LLM
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            provider: Name of the provider to use, or None for default
            extended_thinking: Whether to use extended thinking mode
            
        Returns:
            The LLM's response text
        """
        provider_instance = self._get_provider(provider)
        
        try:
            return await provider_instance.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                extended_thinking=extended_thinking
            )
        except Exception as e:
            logger.error(f"Error in LLM completion: {str(e)}")
            raise
    
    async def complete_json(self, 
                          system_prompt: str, 
                          user_prompt: str, 
                          json_schema: Dict[str, Any], 
                          temperature: Optional[float] = None,
                          provider: Optional[str] = None,
                          extended_thinking: bool = False) -> Dict[str, Any]:
        """
        Generate a JSON-structured completion from the LLM.
        
        Args:
            system_prompt: System message for the LLM
            user_prompt: User message for the LLM
            json_schema: JSON schema to validate against
            temperature: Sampling temperature (0.0 to 1.0)
            provider: Name of the provider to use, or None for default
            extended_thinking: Whether to use extended thinking mode
            
        Returns:
            Parsed JSON response
        """
        provider_instance = self._get_provider(provider)
        
        try:
            return await provider_instance.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_schema=json_schema,
                temperature=temperature,
                extended_thinking=extended_thinking
            )
        except Exception as e:
            logger.error(f"Error in LLM JSON completion: {str(e)}")
            raise