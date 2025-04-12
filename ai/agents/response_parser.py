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
            logger.error("Agent response is not a dictionary, defaulting to check")
            return "check", None, {"reasoning": {}, "thinking": "Error: Invalid response format"}
        
        # Extract required fields
        try:
            action = agent_response.get("action", "").lower()
            amount = agent_response.get("amount")
            reasoning = agent_response.get("reasoning", {})
            thinking = agent_response.get("thinking", "")
            calculations = agent_response.get("calculations", {})
        except (AttributeError, KeyError) as e:
            logger.error(f"Missing required field in agent response: {str(e)}")
            return "check", None, {"reasoning": {}, "thinking": f"Error: {str(e)}"}
        
        # Validate action
        valid_actions = ["fold", "check", "call", "bet", "raise", "all-in"]
        if action not in valid_actions:
            logger.warning(f"Invalid action '{action}', using smart fallback")
            # Default to 'check' rather than 'fold' when possible
            action = "check"  
            amount = None
        
        # Validate amount based on action
        if action in ["fold", "check", "call"]:
            # These actions don't need an amount (or it's determined by the game engine)
            amount = None
        elif action in ["bet", "raise", "all-in"]:
            # These actions require an amount
            if amount is None:
                logger.warning(f"Action '{action}' requires an amount but none provided, using call instead")
                action = "call"
                amount = None
            else:
                try:
                    amount = int(amount)
                    if amount <= 0:
                        logger.warning(f"Amount must be positive for '{action}', using call instead")
                        action = "call"
                        amount = None
                except (TypeError, ValueError):
                    logger.warning(f"Invalid amount '{amount}' for action '{action}', using call instead")
                    action = "call"
                    amount = None
        
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
        # Get player stack and current bet
        stack = game_state.get("stack_sizes", {}).get("0", 0)  # Player's stack
        current_bet = game_state.get("current_bet", 0)  # Current bet to call
        min_raise = game_state.get("min_raise", current_bet * 2)  # Minimum raise amount
        
        # Log the current state for debugging
        logger.info(f"Applying game rules for action: {action}, amount: {amount}")
        logger.info(f"Player stack: {stack}, Current bet: {current_bet}, Min raise: {min_raise}")
        
        # Check if action is appropriate given the current state
        if action == "check" and current_bet > 0:
            logger.warning(f"Cannot check when there's a bet of {current_bet}. Converting to call.")
            action = "call"
            amount = None
            
        elif action == "call":
            # If call amount is more than player's stack, convert to all-in
            if current_bet >= stack:
                logger.info(f"Call amount {current_bet} exceeds stack {stack}. Converting to all-in.")
                action = "all-in"
                amount = stack
                
        elif action == "raise" or action == "bet":
            # Handle raise/bet amounts
            if amount is None:
                amount = min_raise  # Default to min raise if not specified
                logger.info(f"No amount specified for {action}, using min raise: {amount}")
                
            # Ensure min raise
            if amount < min_raise and action == "raise":
                logger.warning(f"Raise amount {amount} below min raise {min_raise}. Adjusting.")
                amount = min_raise
                
            # Cap at stack size
            if amount > stack:
                logger.info(f"Adjusting {action} amount from {amount} to {stack} (all-in)")
                amount = stack
                action = "all-in"
                
        elif action == "all-in":
            amount = stack
            logger.info(f"All-in with stack size: {stack}")
            
        # Preferred fallback cascade (final safety check):
        # If action can't be executed, try to degrade gracefully rather than defaulting to fold
        
        # If player has no chips, force fold
        if stack <= 0:
            logger.warning("Player has no chips. Forcing fold.")
            return "fold", None
            
        # If player can't call and action requires chips, switch to check if possible or fold
        if stack < current_bet and action in ["call", "raise", "bet", "all-in"]:
            if current_bet == 0:
                logger.warning(f"Not enough chips for {action}, but can check. Converting to check.")
                return "check", None
            else:
                logger.warning(f"Not enough chips ({stack}) to call bet of {current_bet}. Forcing fold.")
                return "fold", None
        
        return action, amount