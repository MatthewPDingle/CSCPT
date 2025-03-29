"""
Maniac poker agent implementation.
"""

from typing import Dict, Any, Optional

from ..llm_service import LLMService
from ..prompts import MANIAC_SYSTEM_PROMPT
from .base_agent import PokerAgent

class ManiacAgent(PokerAgent):
    """
    Implementation of a Maniac poker player agent.
    
    Maniacs are ultra-aggressive players who raise and re-raise constantly,
    often with little regard for their actual hand strength. They apply maximum
    pressure in most situations, making them unpredictable and potentially
    dangerous, though they can also spew chips with reckless plays. Their style
    is characterized by extremely high aggression, minimal hand requirements,
    and a seemingly chaotic betting pattern.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "intermediate",  # Can be clever but not disciplined
        temperature: float = 0.9,  # High temperature for unpredictable play
        extended_thinking: bool = True
    ):
        """
        Initialize a Maniac agent.
        
        Args:
            llm_service: LLMService instance for making API calls
            provider: LLM provider to use (None for default)
            intelligence_level: Level of opponent modeling capability
            temperature: Temperature for LLM sampling (defaults high for Maniac)
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
        Get the system prompt for the Maniac agent.
        
        Returns:
            Maniac system prompt
        """
        return MANIAC_SYSTEM_PROMPT