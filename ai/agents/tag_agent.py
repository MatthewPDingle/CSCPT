"""
Tight-Aggressive (TAG) poker agent implementation.
"""

from typing import Dict, Any, Optional

from ..llm_service import LLMService
from ..prompts import TAG_SYSTEM_PROMPT
from .base_agent import PokerAgent

class TAGAgent(PokerAgent):
    """
    Implementation of a Tight-Aggressive poker player agent.
    TAG players are disciplined, selective, and value-oriented.
    They play a narrow range of strong hands and are aggressive when they enter pots.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "expert",
        temperature: float = 0.5,  # Lower temperature for more consistent play
        extended_thinking: bool = True
    ):
        """
        Initialize a TAG agent.
        
        Args:
            llm_service: LLMService instance for making API calls
            provider: LLM provider to use (None for default)
            intelligence_level: Level of opponent modeling capability
            temperature: Temperature for LLM sampling (defaults lower for TAG)
            extended_thinking: Whether to use extended thinking mode
        """
        super().__init__(
            llm_service=llm_service,
            provider=provider,
            intelligence_level=intelligence_level,
            temperature=temperature,
            extended_thinking=extended_thinking
        )
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the TAG agent.
        
        Returns:
            TAG system prompt
        """
        return TAG_SYSTEM_PROMPT