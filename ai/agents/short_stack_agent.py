"""
Short Stack specialist poker agent implementation.
"""

from typing import Dict, Any, Optional

from ..llm_service import LLMService
from ..prompts import SHORT_STACK_SYSTEM_PROMPT
from .base_agent import PokerAgent

class ShortStackAgent(PokerAgent):
    """
    Implementation of a Short Stack specialist poker player agent.
    
    Short Stack players specialize in playing with smaller stacks (typically 20-30 BB)
    to simplify decisions and reduce variance. They employ a push/fold strategy
    in many spots, are very selective pre-flop, and when they do enter pots, they
    frequently commit their entire stack. Their play is characterized by binary
    decisions and strong pre-flop hand selection.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "advanced",
        temperature: float = 0.5,  # More consistent/formulaic play
        extended_thinking: bool = True,
        use_persistent_memory: bool = True
    ):
        """
        Initialize a Short Stack agent.
        
        Args:
            llm_service: LLMService instance for making API calls
            provider: LLM provider to use (None for default)
            intelligence_level: Level of opponent modeling capability
            temperature: Temperature for LLM sampling (more consistent for Short Stack)
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
        Get the system prompt for the Short Stack agent.
        
        Returns:
            Short Stack system prompt
        """
        return SHORT_STACK_SYSTEM_PROMPT
    
    async def make_decision(self, game_state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a poker decision with short stack considerations.
        
        Args:
            game_state: Dictionary containing the current game state
            context: Additional context information
            
        Returns:
            Decision object with action, amount, and reasoning
        """
        # Check if player's stack is actually short relative to blinds
        stack = game_state.get("stack_sizes", {}).get("0", 0)  # Player's stack
        big_blind = context.get("blinds", [0, 20])[1]  # Second element is BB
        
        # Calculate stack in BB
        if big_blind > 0:
            stack_in_bb = stack / big_blind
        else:
            stack_in_bb = 50  # Default assumption if BB is missing
        
        # Add short stack info to context
        context["stack_in_bb"] = stack_in_bb
        context["is_short_stack"] = stack_in_bb < 30  # Consider < 30 BB as short stack
        
        # Standard decision process with short stack context included
        return await super().make_decision(game_state, context)