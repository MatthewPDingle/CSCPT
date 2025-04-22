"""
Configuration module for AI components.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AIConfig:
    """Configuration handler for AI services."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the AI configuration.
        
        Args:
            config_path: Path to the config JSON file (optional)
                         If not provided, will use environment variables
        """
        self.config = {}
        
        if config_path:
            self._load_from_file(config_path)
        else:
            self._load_from_env()
    
    def _load_from_file(self, config_path: str) -> None:
        """
        Load configuration from a JSON file.
        
        Args:
            config_path: Path to the config JSON file
        """
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                logger.info(f"Loaded AI configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {str(e)}")
            # Fall back to environment variables
            self._load_from_env()
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Anthropic configuration
        if os.environ.get("ANTHROPIC_API_KEY"):
            self.config["anthropic"] = {
                "api_key": os.environ.get("ANTHROPIC_API_KEY"),
                "model": os.environ.get("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219"),
                "thinking_budget_tokens": int(os.environ.get("ANTHROPIC_THINKING_BUDGET", "4000"))
            }
            logger.info("Loaded Anthropic configuration from environment variables")
        else:
            logger.warning("No Anthropic API key found in environment variables")
        
        # OpenAI configuration
        if os.environ.get("OPENAI_API_KEY"):
            # Default to o4-mini for AI opponents
            self.config["openai"] = {
                "api_key": os.environ.get("OPENAI_API_KEY"),
                # 'OPENAI_MODEL' env var can override this
                "model": os.environ.get("OPENAI_MODEL", "o4-mini"),
                "reasoning_level": os.environ.get("OPENAI_REASONING_LEVEL", "medium"),
                "organization_id": os.environ.get("OPENAI_ORGANIZATION_ID")
            }
            logger.info("Loaded OpenAI configuration from environment variables")
        else:
            logger.warning("No OpenAI API key found in environment variables")
            
        # Gemini configuration
        if os.environ.get("GEMINI_API_KEY"):
            # Build generation config from environment variables
            generation_config = {}
            if os.environ.get("GEMINI_TEMPERATURE"):
                generation_config["temperature"] = float(os.environ.get("GEMINI_TEMPERATURE"))
            if os.environ.get("GEMINI_TOP_P"):
                generation_config["top_p"] = float(os.environ.get("GEMINI_TOP_P"))
            if os.environ.get("GEMINI_TOP_K"):
                generation_config["top_k"] = int(os.environ.get("GEMINI_TOP_K"))
            if os.environ.get("GEMINI_MAX_OUTPUT_TOKENS"):
                generation_config["max_output_tokens"] = int(os.environ.get("GEMINI_MAX_OUTPUT_TOKENS"))
            
            self.config["gemini"] = {
                "api_key": os.environ.get("GEMINI_API_KEY"),
                "model": os.environ.get("GEMINI_MODEL", "gemini-2.5-pro"),
                "generation_config": generation_config
            }
            logger.info("Loaded Gemini configuration from environment variables")
        else:
            logger.warning("No Gemini API key found in environment variables")
        
        # Settings for provider selection
        self.config["default_provider"] = os.environ.get("DEFAULT_LLM_PROVIDER", "anthropic")
    
    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific provider.
        
        Args:
            provider_name: Name of the provider (e.g., "anthropic")
            
        Returns:
            Provider configuration dict
        """
        if provider_name not in self.config:
            raise ValueError(f"Configuration for provider '{provider_name}' not found")
        
        return self.config[provider_name]
    
    def get_default_provider(self) -> str:
        """
        Get the name of the default LLM provider.
        
        Returns:
            Provider name string
        """
        return self.config.get("default_provider", "anthropic")
    
    def is_provider_configured(self, provider_name: str) -> bool:
        """
        Check if a provider is configured.
        
        Args:
            provider_name: Name of the provider to check
            
        Returns:
            True if the provider is configured, False otherwise
        """
        return provider_name in self.config and "api_key" in self.config[provider_name]