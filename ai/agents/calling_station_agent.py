"""
Calling Station poker agent implementation.
"""

from typing import Dict, Any, Optional

from ..llm_service import LLMService
from ..prompts import CALLING_STATION_SYSTEM_PROMPT
from .base_agent import PokerAgent

class CallingStationAgent(PokerAgent):
    """
    Implementation of a Calling Station poker player agent.
    
    Calling Stations are characterized by their tendency to call excessively
    with marginal hands and draws. They rarely fold when they should and don't
    raise enough even with strong holdings. They play passively and don't
    apply pressure, making them exploitable but occasionally frustrating when
    they hit unlikely draws.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "basic",  # Lower intelligence by default
        temperature: float = 0.5,
        extended_thinking: bool = True,
        use_persistent_memory: bool = True
    ):
        """
        Initialize a Calling Station agent.
        
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
            extended_thinking=extended_thinking,
            use_persistent_memory=use_persistent_memory
        )
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the Calling Station agent.
        
        Returns:
            Calling Station system prompt
        """
        return CALLING_STATION_SYSTEM_PROMPT