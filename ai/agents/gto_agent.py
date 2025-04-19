"""
GTO (Game Theory Optimal) poker agent implementation.
"""

from typing import Dict, Any, Optional

from ..llm_service import LLMService
from ..prompts import GTO_SYSTEM_PROMPT
from .base_agent import PokerAgent

class GTOAgent(PokerAgent):
    """
    Implementation of a GTO (Game Theory Optimal) poker player agent.
    
    GTO players aim to play a mathematically balanced strategy that is
    theoretically unexploitable. They make decisions based on ranges rather
    than specific hands, use mixed strategies in many situations, and maintain
    proper bet sizing and frequencies. Their play is characterized by balanced
    actions that make opponents indifferent between their options.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "expert",  # Highest intelligence required
        temperature: float = 0.7,  # Need some randomness for mixed strategies
        extended_thinking: bool = True,
        use_persistent_memory: bool = True
    ):
        """
        Initialize a GTO agent.
        
        Args:
            llm_service: LLMService instance for making API calls
            provider: LLM provider to use (None for default)
            intelligence_level: Level of opponent modeling capability (default: expert)
            temperature: Temperature for LLM sampling
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
        Get the system prompt for the GTO agent.
        
        Returns:
            GTO system prompt
        """
        return GTO_SYSTEM_PROMPT