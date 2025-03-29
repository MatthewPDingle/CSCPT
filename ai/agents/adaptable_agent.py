"""
Adaptable poker agent implementation.
"""

from typing import Dict, Any, Optional, List

from ..llm_service import LLMService
from ..prompts import ADAPTABLE_SYSTEM_PROMPT
from .base_agent import PokerAgent

class AdaptableAgent(PokerAgent):
    """
    Implementation of an Adaptable poker player agent.
    
    Adaptable players change their strategy based on table dynamics and
    opponent tendencies. They can shift gears from tight to loose or from
    passive to aggressive as the situation demands. They actively identify
    exploitable patterns in opponents and adjust accordingly, making them
    challenging to play against effectively.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "expert",  # Highest intelligence required
        temperature: float = 0.6,  # Balanced temperament
        extended_thinking: bool = True
    ):
        """
        Initialize an Adaptable agent.
        
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
            extended_thinking=extended_thinking
        )
        
        # Track adaptation strategy
        self.current_strategy = "balanced"  # Start balanced, then adapt
        self.observed_exploits = []
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the Adaptable agent.
        
        Returns:
            Adaptable system prompt
        """
        return ADAPTABLE_SYSTEM_PROMPT
    
    async def make_decision(self, game_state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a poker decision based on the current game state with adaptation.
        
        This overrides the base method to include adaptation information in the prompt.
        
        Args:
            game_state: Dictionary containing the current game state
            context: Additional context information
            
        Returns:
            Decision object with action, amount, and reasoning
        """
        # Update opponent profiles and adaptation strategy
        self._update_adaptation_strategy(game_state)
        
        # Standard decision process with adaptation info included
        return await super().make_decision(game_state, context)
    
    def _update_adaptation_strategy(self, game_state: Dict[str, Any]) -> None:
        """
        Update the agent's adaptation strategy based on observed gameplay.
        
        Args:
            game_state: Current game state with action history
        """
        # This would analyze opponent tendencies and determine optimal counter-strategies
        # For now, this is a placeholder implementation
        action_history = game_state.get("action_history", [])
        
        if not action_history:
            return
        
        # Simple adaptation logic (would be more sophisticated in a real implementation)
        passive_count = 0
        aggressive_count = 0
        
        for action in action_history:
            action_type = action.get("action", "").lower()
            if action_type in ["check", "call"]:
                passive_count += 1
            elif action_type in ["bet", "raise"]:
                aggressive_count += 1
        
        # Determine simple adaptation strategy
        if aggressive_count > passive_count * 2:
            # Against very aggressive players, tighten up and trap
            self.current_strategy = "counter-aggressive"
            if "excessive aggression" not in self.observed_exploits:
                self.observed_exploits.append("excessive aggression")
        elif passive_count > aggressive_count * 2:
            # Against passive players, become more aggressive
            self.current_strategy = "exploit-passive" 
            if "excessive passivity" not in self.observed_exploits:
                self.observed_exploits.append("excessive passivity")
        else:
            # Balanced table
            self.current_strategy = "balanced"