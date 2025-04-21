"""
Real LLMService dispatcher for integrating actual providers.
"""
import os
import logging
import json
from typing import Dict, Any, Optional

from ai.config import AIConfig
from ai.providers.anthropic_provider import AnthropicProvider
from ai.providers.openai_provider import OpenAIProvider
from ai.providers.gemini_provider import GeminiProvider

import logging
# Logger for LLM messages
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Configure file logging for LLM requests/responses
_log_path = os.environ.get(
    'LLM_LOG_PATH',
    os.path.join(os.path.expanduser('~'), '.cscpt', 'llm_messages.log')
)
os.makedirs(os.path.dirname(_log_path), exist_ok=True)
_fh = logging.FileHandler(_log_path)
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(_fh)
# Also attach the same handler to the top-level 'ai' logger to capture provider logs,
# but stop propagation so they don’t bubble up to the console.
ai_root_logger = logging.getLogger('ai')
ai_root_logger.setLevel(logging.DEBUG)
ai_root_logger.addHandler(_fh)
# Prevent ai.* log records from propagating to the root logger (which prints to console)
ai_root_logger.propagate = False

class LLMService:
    """Dispatcher that selects and invokes real LLM providers based on config."""
    def __init__(self, config_path: Optional[str] = None):
        """
        Load AI configuration and prepare provider cache.

        Args:
            config_path: Optional path to JSON config file
        """
        self.config = AIConfig(config_path)
        self.default_provider = self.config.get_default_provider()
        self.providers: Dict[str, Any] = {}
        logger.info(f"LLMService initialized with default provider: {self.default_provider}")

    def _get_provider(self, provider_name: Optional[str] = None) -> Any:
        """
        Get or create a provider instance.

        Args:
            provider_name: One of 'anthropic', 'openai', 'gemini'
        Returns:
            Provider instance
        """
        name = provider_name or self.default_provider
        if name in self.providers:
            return self.providers[name]
        cfg = self.config.get_provider_config(name)
        if name == 'anthropic':
            prov = AnthropicProvider(
                api_key=cfg['api_key'],
                model=cfg.get('model'),
                thinking_budget_tokens=cfg.get('thinking_budget_tokens', 4000)
            )
        elif name == 'openai':
            prov = OpenAIProvider(
                api_key=cfg['api_key'],
                model=cfg.get('model'),
                reasoning_level=cfg.get('reasoning_level', 'medium'),
                organization_id=cfg.get('organization_id')
            )
        elif name == 'gemini':
            prov = GeminiProvider(
                api_key=cfg['api_key'],
                model=cfg.get('model'),
                generation_config=cfg.get('generation_config', {})
            )
        else:
            raise ValueError(f"Unknown LLM provider: {name}")
        self.providers[name] = prov
        return prov

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        provider: Optional[str] = None,
        extended_thinking: bool = False
    ) -> str:
        """
        Request a text completion.

        Returns the raw text response from the LLM.
        """
        prov = self._get_provider(provider)
        logger.debug(
            "complete() -> provider=%s, temp=%s, max_tokens=%s, extended=%s",
            provider or self.default_provider,
            temperature,
            max_tokens,
            extended_thinking
        )
        logger.debug("System prompt:\n%s", system_prompt)
        logger.debug("User prompt:\n%s", user_prompt)
        resp = await prov.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            extended_thinking=extended_thinking
        )
        logger.debug("Response: %s", resp)
        return resp

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Dict[str, Any],
        temperature: Optional[float] = None,
        provider: Optional[str] = None,
        extended_thinking: bool = False
    ) -> Dict[str, Any]:
        """
        Request a JSON-structured completion.

        Returns the parsed JSON response.
        """
        prov = self._get_provider(provider)
        logger.debug(
            "complete_json() -> provider=%s, temp=%s, extended=%s",
            provider or self.default_provider,
            temperature,
            extended_thinking
        )
        logger.debug("System prompt:\n%s", system_prompt)
        logger.debug("User prompt:\n%s", user_prompt)
        logger.debug("JSON schema:\n%s", json.dumps(json_schema, indent=2))
        resp = await prov.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema=json_schema,
            temperature=temperature,
            extended_thinking=extended_thinking
        )
        logger.debug("JSON Response: %s", json.dumps(resp, indent=2))
        return resp