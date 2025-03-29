"""
Loose-Aggressive (LAG) poker agent implementation.
"""

from typing import Dict, Any, Optional

from ..llm_service import LLMService
from ..prompts import LAG_SYSTEM_PROMPT
from .base_agent import PokerAgent

class LAGAgent(PokerAgent):
    """
    Implementation of a Loose-Aggressive poker player agent.
    LAG players are creative, dynamic, and pressure-oriented.
    They play a wide range of hands and apply constant pressure with aggressive betting.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "expert",
        temperature: float = 0.8,  # Higher temperature for more creative play
        extended_thinking: bool = True
    ):
        """
        Initialize a LAG agent.
        
        Args:
            llm_service: LLMService instance for making API calls
            provider: LLM provider to use (None for default)
            intelligence_level: Level of opponent modeling capability
            temperature: Temperature for LLM sampling (defaults higher for LAG)
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
        Get the system prompt for the LAG agent.
        
        Returns:
            LAG system prompt
        """
        return LAG_SYSTEM_PROMPT