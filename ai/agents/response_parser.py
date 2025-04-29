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
            # Get the action field and log the original value
            raw_action = agent_response.get("action", "")
            logger.debug(f"Raw action from agent: '{raw_action}'")
            
            # Try to convert to string and lowercase if needed
            if isinstance(raw_action, str):
                action = raw_action.lower()
            else:
                action = str(raw_action).lower()
                logger.warning(f"Action was not a string, converted from {type(raw_action)} to '{action}'")
            
            # Get amount (ensuring it's an integer if present)
            raw_amount = agent_response.get("amount")
            if raw_amount is not None:
                try:
                    amount = int(raw_amount)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid amount format '{raw_amount}', keeping as is for validation later")
                    amount = raw_amount
            else:
                amount = None
                
            # Get other metadata
            reasoning = agent_response.get("reasoning", {})
            thinking = agent_response.get("thinking", "")
            calculations = agent_response.get("calculations", {})
            
            logger.debug(f"Extracted fields - action: '{action}', amount: {amount}")
        except (AttributeError, KeyError) as e:
            logger.error(f"Missing required field in agent response: {str(e)}")
            return "check", None, {"reasoning": {}, "thinking": f"Error: {str(e)}"}
        
        # Normalize action string to handle different formats
        normalized_action = action.lower().replace('_', '-').strip()
        
        # Additional normalization for all-in variations
        if "all" in normalized_action and "in" in normalized_action:
            normalized_action = "all-in"
            logger.info(f"Normalized '{action}' to 'all-in'")
            
        # Extended list of valid actions with known variations
        valid_actions = ["fold", "check", "call", "bet", "raise", "all-in"]
        valid_action_map = {
            # Standard actions
            "fold": "fold", "check": "check", "call": "call", 
            "bet": "bet", "raise": "raise", "all-in": "all-in",
            # Alternative formats
            "allin": "all-in", "all_in": "all-in", "allin": "all-in",
            "all in": "all-in"
        }
        
        # Try to map to a valid action
        if normalized_action in valid_action_map:
            action = valid_action_map[normalized_action]
            logger.info(f"Mapped '{normalized_action}' to valid action '{action}'")
        elif normalized_action not in valid_actions:
            logger.warning(f"Invalid action '{action}' (normalized: '{normalized_action}'), using smart fallback")
            # Default to 'check' rather than 'fold' when possible
            action = "check"  
            amount = None
        
        # Validate amount based on action
        # Note: Do NOT automatically discard the amount for a CALL, because
        # the agent may be intentionally specifying an explicit call size
        # (e.g. an all-in call that is smaller than the bet-to amount).  The
        # game-rules pass will make the final decision about whether the
        # supplied amount is usable.
        if action in ["fold", "check"]:
            # These actions never require an amount.
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
        
        This method also normalizes common variants of action types, especially for all-in actions.
        """
        # Normalize the action first to handle variations like "all in", "all_in", etc.
        original_action = action
        if action and "all" in action.lower() and "in" in action.lower():
            action = "all-in"
            logger.info(f"Normalized '{original_action}' to 'all-in' in apply_game_rules")
            
        # Now continue with regular processing
        """
        Apply game rules to ensure the action and amount are valid for the current game state.
        
        Args:
            action: The action string ('fold', 'call', etc.)
            amount: The amount (if applicable)
            game_state: The current game state
            
        Returns:
            Potentially modified (action, amount) tuple that conforms to game rules
        """
        # Determine the player's stack based on the current player index
        players = game_state.get("players", [])
        current_idx = game_state.get("current_player_idx", 0)
        try:
            stack = int(players[current_idx].get("chips", 0))
        except Exception:
            stack = 0
        # Current bet to call
        current_bet = int(game_state.get("current_bet", 0))
        # Minimum raise amount (default to double the current bet)
        min_raise = int(game_state.get("min_raise", current_bet * 2))
        
        # Log the current state for debugging
        logger.info(f"Applying game rules for action: {action}, amount: {amount}")
        logger.info(f"Player stack: {stack}, Current bet: {current_bet}, Min raise: {min_raise}")

        # ------------------------------------------------------------------
        # 1. Fix common AI error: attempting to "raise" when no bet exists.
        # ------------------------------------------------------------------
        if action == "raise" and current_bet == 0:
            logger.warning(
                "AI attempted a RAISE when there is no current bet. Converting to BET."
            )
            action = "bet"
        
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
                
        elif action in ["raise", "bet"]:
            # Handle raise/bet amounts
            if amount is None:
                amount = min_raise  # Default to min raise if not specified
                logger.info(f"No amount specified for {action}, using min raise: {amount}")

            # If raise amount below minimum, use pot-sized raise
            if action == "raise" and amount < min_raise:
                # Compute pot-sized raise: current_bet + total_pot
                total_pot = int(game_state.get("total_pot", 0))
                new_amount = current_bet + total_pot
                # Ensure at least min_raise
                if new_amount < min_raise:
                    new_amount = min_raise
                # Cap at stack as all-in
                if new_amount >= stack:
                    logger.info(f"Pot-sized raise {new_amount} exceeds stack {stack}, using all-in {stack}")
                    action = "all-in"
                    amount = stack
                else:
                    logger.info(f"Adjusted raise to pot-sized amount {new_amount}")
                    amount = new_amount
            # Cap at stack size for any bet/raise
            if amount > stack:
                logger.info(f"Adjusting {action} amount from {amount} to {stack} (all-in)")
                amount = stack
                action = "all-in"
                
        elif action == "all-in":
            # For all-in, always use player's entire stack regardless of provided amount
            original_amount = amount
            amount = stack
            logger.info(f"All-in: Using full stack size {stack} (original requested amount: {original_amount})")
            
        # Preferred fallback cascade (final safety check):
        # If action can't be executed, try to degrade gracefully rather than defaulting to fold
        
        # If player has no chips, force fold
        if stack <= 0:
            logger.warning("Player has no chips. Forcing fold.")
            return "fold", None
            
        # If the action is ALREADY an all-in we purposely allow it even when
        # the stack is less than the amount to call – that is exactly what an
        # all-in means.  Therefore the insufficient-stack check should only
        # apply to non-all-in actions.
        if stack < current_bet and action in ["call", "raise", "bet"]:
            if current_bet == 0:
                logger.warning(
                    f"Not enough chips for {action}, but can check. Converting to check."
                )
                return "check", None
            else:
                logger.warning(
                    f"Not enough chips ({stack}) to cover bet of {current_bet}. Converting to all-in."
                )
                return "all-in", stack
        
        return action, amount