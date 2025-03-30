"""
Integration utilities for the adaptation components.

This module provides utilities for integrating the adaptation components
with the existing agent architecture.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from ..base_agent import PokerAgent
from .game_state_tracker import GameStateTracker
from .tournament_analyzer import TournamentStageAnalyzer

logger = logging.getLogger(__name__)

class AdaptationManager:
    """
    Manages adaptation components for poker agents.
    
    This class provides a unified interface for using all adaptation
    components together and integrating them with the agent architecture.
    """
    
    def __init__(self):
        """Initialize the adaptation manager."""
        self.game_state_tracker = GameStateTracker()
        self.tournament_analyzer = TournamentStageAnalyzer()
        
        # Track last processed hand ID to avoid reprocessing
        self.last_processed_hand_id = None
    
    def update_from_game_state(self, game_state: Dict[str, Any], context: Dict[str, Any]) -> None:
        """
        Update all adaptation components from a game state.
        
        Args:
            game_state: Current game state information
            context: Additional context information
        """
        # Extract hand ID if available
        hand_id = game_state.get("hand_id")
        if hand_id and hand_id == self.last_processed_hand_id:
            # Skip if we've already processed this hand
            return
            
        self.last_processed_hand_id = hand_id
        
        # Update game state tracker
        self.game_state_tracker.update(game_state)
        
        # Extract tournament information from context
        tournament_state = context.get("tournament", {})
        if tournament_state:
            self.tournament_analyzer.update(tournament_state)
    
    def get_adaptation_context(self, player_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a combined adaptation context for decision making.
        
        Args:
            player_id: Optional player ID for player-specific recommendations
            
        Returns:
            Dictionary with adaptation context
        """
        adaptation_context = {
            "game_dynamics": self.game_state_tracker.get_dynamics_assessment(),
            "recommended_adjustments": self.game_state_tracker.get_recommended_adjustments()
        }
        
        # Add tournament context if available
        tournament_assessment = self.tournament_analyzer.get_assessment()
        if tournament_assessment and tournament_assessment.get("stage") != "UNKNOWN":
            adaptation_context["tournament"] = tournament_assessment
            
            # Add player-specific tournament recommendations if player_id provided
            if player_id:
                adaptation_context["tournament_recommendations"] = (
                    self.tournament_analyzer.get_recommendations_for_player(player_id)
                )
        
        return adaptation_context
    
    def get_strategic_adjustments(self) -> Dict[str, Any]:
        """
        Get strategic adjustments based on all adaptation components.
        
        Returns:
            Dictionary with strategic adjustments
        """
        adjustments = {
            "game_state_adjustments": self.game_state_tracker.get_recommended_adjustments()
        }
        
        # Add tournament stage adjustments if available
        tournament_assessment = self.tournament_analyzer.get_assessment()
        if tournament_assessment and tournament_assessment.get("stage") != "UNKNOWN":
            adjustments["tournament_adjustments"] = tournament_assessment.get("recommendations", {})
        
        return adjustments

def enhance_agent_with_adaptation(agent: PokerAgent) -> None:
    """
    Enhance a poker agent with adaptation capabilities.
    
    This function adds adaptation components to an existing agent instance.
    
    Args:
        agent: The poker agent to enhance
    """
    if not hasattr(agent, "adaptation_manager"):
        agent.adaptation_manager = AdaptationManager()
        
        # Store original make_decision method
        original_make_decision = agent.make_decision
        
        async def enhanced_make_decision(game_state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            """Enhanced decision making with adaptation."""
            # Update adaptation manager
            agent.adaptation_manager.update_from_game_state(game_state, context)
            
            # Enhance context with adaptation information
            adapted_context = context.copy()
            adapted_context["adaptation"] = agent.adaptation_manager.get_adaptation_context()
            
            # Get player ID if available
            player_id = game_state.get("player_id")
            if player_id:
                adapted_context["adaptation"]["tournament_recommendations"] = (
                    agent.adaptation_manager.get_recommendations_for_player(player_id)
                )
            
            # Call original method with enhanced context
            decision = await original_make_decision(game_state, adapted_context)
            
            # Enhance decision with adaptation information
            if "reasoning" in decision:
                # Add adaptation reasoning
                adjustments = agent.adaptation_manager.get_strategic_adjustments()
                adaptation_summary = _get_adaptation_summary(adjustments)
                
                decision["reasoning"]["adaptation"] = adaptation_summary
            
            return decision
        
        # Replace the make_decision method
        agent.make_decision = enhanced_make_decision

def _get_adaptation_summary(adjustments: Dict[str, Any]) -> str:
    """Create a concise summary of adaptation adjustments."""
    summary_parts = []
    
    # Add game state adjustments
    game_adjustments = adjustments.get("game_state_adjustments", {})
    for key, adjustment in game_adjustments.items():
        if isinstance(adjustment, dict) and "description" in adjustment:
            summary_parts.append(adjustment["description"])
    
    # Add tournament adjustments
    tournament_adjustments = adjustments.get("tournament_adjustments", {})
    general_strategy = tournament_adjustments.get("general_strategy")
    if general_strategy:
        summary_parts.append(f"Tournament strategy: {general_strategy}")
    
    # Combine parts
    if summary_parts:
        return "; ".join(summary_parts)
    else:
        return "Standard play based on current conditions"