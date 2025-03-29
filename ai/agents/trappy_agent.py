"""
Trappy (Slow-Player) poker agent implementation.
"""

from typing import Dict, Any, Optional

from ..llm_service import LLMService
from ..prompts import TRAPPY_SYSTEM_PROMPT
from .base_agent import PokerAgent

class TrappyAgent(PokerAgent):
    """
    Implementation of a Trappy poker player agent.
    
    Trappy players (also known as "Slow-Players") frequently underrepresent the
    strength of their hands to induce bluffs and build larger pots. They check
    and call with strong holdings, hoping opponents will bet into them or bluff.
    Their play is characterized by deceptive actions that disguise hand strength,
    especially on early streets.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "advanced",
        temperature: float = 0.6,
        extended_thinking: bool = True
    ):
        """
        Initialize a Trappy agent.
        
        Args:
            llm_service: LLMService instance for making API calls
            provider: LLM provider to use (None for default)
            intelligence_level: Level of opponent modeling capability
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
        Get the system prompt for the Trappy agent.
        
        Returns:
            Trappy system prompt
        """
        return TRAPPY_SYSTEM_PROMPT