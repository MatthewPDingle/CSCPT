"""
Beginner poker agent implementation.
"""

from typing import Dict, Any, Optional

from ..llm_service import LLMService
from ..prompts import BEGINNER_SYSTEM_PROMPT
from .base_agent import PokerAgent

class BeginnerAgent(PokerAgent):
    """
    Implementation of a Beginner poker player agent.
    
    Beginners make fundamental mistakes and show inconsistent decision making.
    They overvalue weak hands, don't understand positional advantages,
    miscalculate odds, call too much with draws, and generally lack a coherent
    strategy. Their play is characterized by basic errors, misconceptions about
    hand strength, and failure to adjust to table dynamics.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "basic",  # Low intelligence by default
        temperature: float = 0.7,  # Somewhat random play
        extended_thinking: bool = False  # No extended thinking (doesn't think deeply)
    ):
        """
        Initialize a Beginner agent.
        
        Args:
            llm_service: LLMService instance for making API calls
            provider: LLM provider to use (None for default)
            intelligence_level: Level of opponent modeling capability (default: basic)
            temperature: Temperature for LLM sampling
            extended_thinking: Whether to use extended thinking mode (default: False)
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
        Get the system prompt for the Beginner agent.
        
        Returns:
            Beginner system prompt
        """
        return BEGINNER_SYSTEM_PROMPT