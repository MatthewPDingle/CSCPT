"""
Agent response parsing module.

This module provides functionality to parse and validate the structured
responses from poker agents for use in the game engine.
"""

import logging
from typing import Dict, Any, Optional, Union, List, Tuple

logger = logging.getLogger(__name__)

class AgentResponseParser:
    """Parser for agent responses to ensure they can be used by the game engine."""
    
    @staticmethod
    def parse_response(agent_response: Dict[str, Any]) -> Tuple[str, Optional[int], Dict[str, Any]]:
        """
        Parse and validate an agent response.
        
        Args:
            agent_response: The structured response from an agent
            
        Returns:
            Tuple of (action, amount, metadata) where:
                - action is a string like 'fold', 'call', 'raise'
                - amount is an optional integer (None for fold/check/call actions)
                - metadata is a dictionary with reasoning and other info
                
        Raises:
            ValueError: If the response doesn't contain required fields or has invalid values
        """
        # Validate basic structure
        if not isinstance(agent_response, dict):
            raise ValueError("Agent response must be a dictionary")
        
        # Extract required fields
        try:
            action = agent_response.get("action", "").lower()
            amount = agent_response.get("amount")
            reasoning = agent_response.get("reasoning", {})
            thinking = agent_response.get("thinking", "")
            calculations = agent_response.get("calculations", {})
        except (AttributeError, KeyError) as e:
            raise ValueError(f"Missing required field in agent response: {str(e)}")
        
        # Validate action
        valid_actions = ["fold", "check", "call", "bet", "raise", "all-in"]
        if action not in valid_actions:
            logger.warning(f"Invalid action '{action}', defaulting to fold")
            action = "fold"
            amount = None
        
        # Validate amount based on action
        if action in ["fold", "check", "call"]:
            # These actions don't need an amount (or it's determined by the game engine)
            amount = None
        elif action in ["bet", "raise", "all-in"]:
            # These actions require an amount
            if amount is None:
                raise ValueError(f"Action '{action}' requires an amount")
            try:
                amount = int(amount)
                if amount <= 0:
                    raise ValueError(f"Amount must be positive for '{action}'")
            except (TypeError, ValueError):
                raise ValueError(f"Invalid amount '{amount}' for action '{action}'")
        
        # Construct metadata with all additional information
        metadata = {
            "reasoning": reasoning,
            "thinking": thinking,
            "calculations": calculations
        }
        
        return action, amount, metadata
    
    @staticmethod
    def is_valid_response(agent_response: Dict[str, Any]) -> bool:
        """
        Check if an agent response is valid without raising exceptions.
        
        Args:
            agent_response: The structured response from an agent
            
        Returns:
            True if the response is valid, False otherwise
        """
        try:
            AgentResponseParser.parse_response(agent_response)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def apply_game_rules(
        action: str, 
        amount: Optional[int], 
        game_state: Dict[str, Any]
    ) -> Tuple[str, Optional[int]]:
        """
        Apply game rules to ensure the action and amount are valid for the current game state.
        
        Args:
            action: The action string ('fold', 'call', etc.)
            amount: The amount (if applicable)
            game_state: The current game state
            
        Returns:
            Potentially modified (action, amount) tuple that conforms to game rules
        """
        # This is a placeholder implementation
        # A real implementation would check:
        # - If player has enough chips for the action
        # - If the amount meets minimum raise requirements
        # - If the action is valid in the current game state (e.g., can't check if there's a bet)
        
        # For now, we'll just handle a simple case - if all-in and amount > stack, adjust the amount
        if action == "all-in" or (action in ["bet", "raise"] and amount is not None):
            stack = game_state.get("stack_sizes", {}).get("0", 0)  # Player's stack
            if amount > stack:
                logger.info(f"Adjusting {action} amount from {amount} to {stack} (all-in)")
                amount = stack
                action = "all-in"
        
        return action, amount