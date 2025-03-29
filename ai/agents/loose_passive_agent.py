"""
Loose-Passive (Fish) poker agent implementation.
"""

from typing import Dict, Any, Optional

from ..llm_service import LLMService
from ..prompts import LOOSE_PASSIVE_SYSTEM_PROMPT
from .base_agent import PokerAgent

class LoosePassiveAgent(PokerAgent):
    """
    Implementation of a Loose-Passive poker player agent, commonly known as a "Fish".
    
    Loose-Passive players play a wide range of starting hands but rarely take
    aggressive actions. They like to see flops cheaply, call too much with
    weak draws, and don't extract value with their strong hands. Unlike
    Calling Stations, they're defined by their loose pre-flop play combined
    with passive post-flop tendencies.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "basic",  # Lower intelligence by default
        temperature: float = 0.6,
        extended_thinking: bool = True
    ):
        """
        Initialize a Loose-Passive agent.
        
        Args:
            llm_service: LLMService instance for making API calls
            provider: LLM provider to use (None for default)
            intelligence_level: Level of opponent modeling capability (default: basic)
            temperature: Temperature for LLM sampling
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
        Get the system prompt for the Loose-Passive agent.
        
        Returns:
            Loose-Passive system prompt
        """
        return LOOSE_PASSIVE_SYSTEM_PROMPT