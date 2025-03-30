"""
Adaptable poker agent implementation.
"""

from typing import Dict, Any, Optional, List

from ..llm_service import LLMService
from ..prompts import ADAPTABLE_SYSTEM_PROMPT
from .base_agent import PokerAgent
from .adaptation.integration import enhance_agent_with_adaptation

class AdaptableAgent(PokerAgent):
    """
    Implementation of an Adaptable poker player agent.
    
    Adaptable players change their strategy based on table dynamics and
    opponent tendencies. They can shift gears from tight to loose or from
    passive to aggressive as the situation demands. They actively identify
    exploitable patterns in opponents and adjust accordingly, making them
    challenging to play against effectively.
    
    This implementation includes advanced adaptation capabilities:
    - Game state tracking and dynamic adjustment
    - Tournament stage awareness
    - Exploitation detection and implementation
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "expert",  # Highest intelligence required
        temperature: float = 0.6,  # Balanced temperament
        extended_thinking: bool = True,
        use_persistent_memory: bool = True,
        use_advanced_adaptation: bool = True  # Enable advanced adaptation
    ):
        """
        Initialize an Adaptable agent.
        
        Args:
            llm_service: LLMService instance for making API calls
            provider: LLM provider to use (None for default)
            intelligence_level: Level of opponent modeling capability (default: expert)
            temperature: Temperature for LLM sampling
            extended_thinking: Whether to use extended thinking mode
            use_persistent_memory: Whether to use persistent memory between sessions
            use_advanced_adaptation: Whether to use advanced adaptation components
        """
        super().__init__(
            llm_service=llm_service,
            provider=provider,
            intelligence_level=intelligence_level,
            temperature=temperature,
            extended_thinking=extended_thinking,
            use_persistent_memory=use_persistent_memory
        )
        
        # Track adaptation strategy
        self.current_strategy = "balanced"  # Start balanced, then adapt
        self.observed_exploits = []
        self.player_archetypes = {}  # Map player_id to detected archetype
        self.last_strategy_update = 0  # Track when we last updated the strategy
        
        # Enable advanced adaptation if requested
        self.use_advanced_adaptation = use_advanced_adaptation
        if use_advanced_adaptation:
            enhance_agent_with_adaptation(self)
    
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
        # If we're using advanced adaptation, the integration logic will handle everything
        if self.use_advanced_adaptation and hasattr(self, "adaptation_manager"):
            # The original make_decision is replaced by the enhanced version
            # in enhance_agent_with_adaptation, which will already include
            # advanced adaptation components
            return await super().make_decision(game_state, context)
        
        # Legacy adaptation behavior if advanced adaptation is disabled
        # Update opponent profiles and adaptation strategy
        self._update_adaptation_strategy(game_state)
        
        # Enhance the context with adaptation strategy
        adapted_context = context.copy()
        adapted_context["adaptation_strategy"] = self.current_strategy
        adapted_context["observed_exploits"] = self.observed_exploits
        
        # Standard decision process with adaptation info included
        decision = await super().make_decision(game_state, adapted_context)
        
        # Add adaptation information to the response
        if "reasoning" in decision:
            decision["reasoning"]["adaptation_strategy"] = f"Using {self.current_strategy} strategy based on table dynamics"
        
        return decision
    
    def _update_adaptation_strategy(self, game_state: Dict[str, Any]) -> None:
        """
        Update the agent's adaptation strategy based on observed gameplay.
        
        Args:
            game_state: Current game state with action history
        """
        action_history = game_state.get("action_history", [])
        
        if not action_history:
            return
            
        # Don't update strategy too frequently - only after significant new information
        # Only update if we have enough new actions 
        if len(action_history) <= self.last_strategy_update + 3:
            return
            
        self.last_strategy_update = len(action_history)
        
        # Analyze action types to determine table dynamics
        passive_count = 0
        aggressive_count = 0
        
        for action in action_history:
            action_type = action.get("action", "").lower()
            if action_type in ["check", "call"]:
                passive_count += 1
            elif action_type in ["bet", "raise"]:
                aggressive_count += 1
        
        # Get player IDs at the table
        player_ids = set(a.get("player_id") for a in action_history if a.get("player_id") is not None)
        
        # Advanced adaptation based on memory service (if available)
        if self.use_persistent_memory and self.memory_service:
            # Analyze detected archetypes from memory service
            table_archetypes = {}
            for player_id in player_ids:
                profile = self.memory_service.get_profile(player_id)
                if profile.archetype and profile.hands_observed >= 10:
                    self.player_archetypes[player_id] = profile.archetype
                    if profile.archetype in table_archetypes:
                        table_archetypes[profile.archetype] += 1
                    else:
                        table_archetypes[profile.archetype] = 1
            
            # Identify most common archetypes at the table
            if table_archetypes:
                # Determine if table is aggressive or passive based on archetypes
                aggressive_archetypes = sum(table_archetypes.get(a, 0) for a in 
                                         ["LAG", "Maniac", "Trappy"])
                passive_archetypes = sum(table_archetypes.get(a, 0) for a in 
                                       ["TightPassive", "CallingStation", "LoosePassive", "Beginner"])
                
                # Get the identified exploits from profiles
                all_exploits = []
                for player_id in player_ids:
                    if player_id in self.memory_service.active_profiles:
                        profile = self.memory_service.active_profiles[player_id]
                        all_exploits.extend(profile.exploitable_tendencies)
                
                # Update our observed exploits with what the memory service has identified
                for exploit in all_exploits:
                    if exploit not in self.observed_exploits:
                        self.observed_exploits.append(exploit)
                
                # Determine adaptation strategy based on combined analysis
                if aggressive_archetypes > passive_archetypes:
                    self.current_strategy = "counter-aggressive"
                elif passive_archetypes > aggressive_archetypes:
                    self.current_strategy = "exploit-passive"
                elif "Folds to aggression" in all_exploits:
                    self.current_strategy = "apply-pressure"
                elif "Calls too much postflop" in all_exploits:
                    self.current_strategy = "value-heavy"
                else:
                    # Fallback to the basic approach
                    if aggressive_count > passive_count * 2:
                        self.current_strategy = "counter-aggressive"
                    elif passive_count > aggressive_count * 2:
                        self.current_strategy = "exploit-passive"
                    else:
                        self.current_strategy = "balanced"
                
                return
        
        # Basic adaptation logic (used if memory service isn't available)
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