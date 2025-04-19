"""
Tight-Passive (Rock/Nit) poker agent implementation.
"""

from typing import Dict, Any, Optional

from ..llm_service import LLMService
from ..prompts import TIGHT_PASSIVE_SYSTEM_PROMPT
from .base_agent import PokerAgent

class TightPassiveAgent(PokerAgent):
    """
    Implementation of a Tight-Passive poker player agent.
    
    Tight-Passive players (also known as "Rocks" or "Nits") are extremely selective
    with their starting hands but tend to play cautiously even with strong holdings.
    They rarely bluff, fold to aggression unless they have very strong hands,
    and prefer calling to raising.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "expert",
        temperature: float = 0.4,  # Lower temperature for predictable, conservative play
        extended_thinking: bool = True,
        use_persistent_memory: bool = True
    ):
        """
        Initialize a Tight-Passive agent.
        
        Args:
            llm_service: LLMService instance for making API calls
            provider: LLM provider to use (None for default)
            intelligence_level: Level of opponent modeling capability
            temperature: Temperature for LLM sampling (defaults lower for Tight-Passive)
            extended_thinking: Whether to use extended thinking mode
        """
        super().__init__(
            llm_service=llm_service,
            provider=provider,
            intelligence_level=intelligence_level,
            temperature=temperature,
            extended_thinking=extended_thinking,
            use_persistent_memory=use_persistent_memory
        )
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the Tight-Passive agent.
        
        Returns:
            Tight-Passive system prompt
        """
        return TIGHT_PASSIVE_SYSTEM_PROMPT