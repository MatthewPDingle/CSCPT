"""
Base poker agent implementation.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple

from ..llm_service import LLMService
from ..prompts import POKER_ACTION_SCHEMA

logger = logging.getLogger(__name__)

class PokerAgent(ABC):
    """Base class for poker player agents."""
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "expert",
        temperature: float = 0.7,
        extended_thinking: bool = True
    ):
        """
        Initialize a poker agent.
        
        Args:
            llm_service: LLMService instance for making API calls
            provider: LLM provider to use (None for default)
            intelligence_level: Level of opponent modeling capability ("basic", "intermediate", "advanced", "expert")
            temperature: Temperature for LLM sampling (0.0 to 1.0)
            extended_thinking: Whether to use extended thinking mode
        """
        self.llm_service = llm_service
        self.provider = provider
        self.intelligence_level = intelligence_level
        self.temperature = temperature
        self.extended_thinking = extended_thinking
        
        # Initialize opponent modeling data structure
        self.opponent_profiles = {}
        
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent archetype.
        
        Returns:
            System prompt string
        """
        pass
    
    def _build_opponent_profile_string(self) -> str:
        """
        Build a string representation of opponent profiles.
        
        Returns:
            Formatted string of opponent profiles
        """
        if not self.opponent_profiles:
            return "No opponent data available yet."
        
        profile_strings = []
        for player_id, profile in self.opponent_profiles.items():
            stats = []
            for stat_name, stat_value in profile.get("stats", {}).items():
                stats.append(f"[{stat_name}:{stat_value}]")
            
            notes = profile.get("notes", [])
            notes_str = f"[Noted:{','.join(notes)}]" if notes else ""
            
            profile_strings.append(f"Player{player_id}: {''.join(stats)} {notes_str}")
        
        return "\n".join(profile_strings)
    
    def _format_game_state(self, game_state: Dict[str, Any]) -> str:
        """
        Format the game state into a readable string for the LLM.
        
        Args:
            game_state: Dictionary containing the current game state
            
        Returns:
            Formatted string representation of the game state
        """
        # Extract game state components
        hand = game_state.get("hand", [])
        community_cards = game_state.get("community_cards", [])
        position = game_state.get("position", "")
        pot = game_state.get("pot", 0)
        action_history = game_state.get("action_history", [])
        stack_sizes = game_state.get("stack_sizes", {})
        
        # Format the state as a string
        formatted_state = f"""
GAME STATE:
Your Hand: {' '.join(hand)}
Community Cards: {' '.join(community_cards) if community_cards else 'None'}
Position: {position}
Pot Size: {pot}
Action History: {self._format_action_history(action_history)}
Stack Sizes: {self._format_stack_sizes(stack_sizes)}
"""
        return formatted_state
    
    def _format_action_history(self, action_history: List[Dict[str, Any]]) -> str:
        """Format the action history into a readable string."""
        if not action_history:
            return "No actions yet."
        
        formatted_actions = []
        for action in action_history:
            player_id = action.get("player_id", "Unknown")
            action_type = action.get("action", "Unknown")
            amount = action.get("amount", None)
            
            if amount is not None:
                formatted_actions.append(f"Player{player_id} {action_type} {amount}")
            else:
                formatted_actions.append(f"Player{player_id} {action_type}")
        
        return " → ".join(formatted_actions)
    
    def _format_stack_sizes(self, stack_sizes: Dict[str, int]) -> str:
        """Format the stack sizes into a readable string."""
        return ", ".join([f"Player{player_id}: {stack}" for player_id, stack in stack_sizes.items()])
    
    def _update_opponent_profiles(self, game_state: Dict[str, Any]) -> None:
        """
        Update opponent profiles based on observed actions.
        
        Args:
            game_state: Current game state with action history
        """
        action_history = game_state.get("action_history", [])
        if not action_history:
            return
        
        # This is a simple implementation - in a real system, this would be more sophisticated
        for action in action_history:
            player_id = action.get("player_id")
            if player_id is None:
                continue
                
            # Initialize player profile if it doesn't exist
            if player_id not in self.opponent_profiles:
                self.opponent_profiles[player_id] = {
                    "stats": {
                        "VPIP": "Unknown",
                        "PFR": "Unknown",
                        "3Bet": "Unknown"
                    },
                    "notes": []
                }
            
            # This is where we'd update stats based on observed actions
            # For now, we'll just add a placeholder implementation
            
            # Example: Note aggressive actions
            action_type = action.get("action", "").lower()
            if action_type in ["raise", "bet"]:
                profile = self.opponent_profiles[player_id]
                if "Aggressive" not in profile["notes"]:
                    profile["notes"].append("Aggressive")
    
    async def make_decision(self, game_state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a poker decision based on the current game state.
        
        Args:
            game_state: Dictionary containing the current game state
            context: Additional context information
            
        Returns:
            Decision object with action, amount, and reasoning
        """
        # Update opponent profiles based on game state
        if self.intelligence_level != "basic":
            self._update_opponent_profiles(game_state)
        
        # Format the game state and opponent profiles
        formatted_state = self._format_game_state(game_state)
        opponent_profiles = self._build_opponent_profile_string()
        
        # Build user prompt
        user_prompt = f"""
{formatted_state}

OPPONENT PROFILES:
{opponent_profiles}

GAME CONTEXT:
Game Type: {context.get('game_type', 'Unknown')}
Stage: {context.get('stage', 'Unknown')}
Blinds: {context.get('blinds', [0, 0])}

Based on the current situation, what action will you take? Analyze the hand, consider pot odds, evaluate opponent tendencies, and make a decision that aligns with your playing style.
"""
        
        # Get the system prompt for this agent
        system_prompt = self.get_system_prompt()
        
        # Make the API call
        try:
            response = await self.llm_service.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_schema=POKER_ACTION_SCHEMA,
                temperature=self.temperature,
                provider=self.provider,
                extended_thinking=self.extended_thinking
            )
            
            logger.debug(f"Agent decision: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error making agent decision: {str(e)}")
            # Fallback to a safe default response
            return {
                "thinking": f"Error occurred: {str(e)}",
                "action": "fold",
                "amount": None,
                "reasoning": {
                    "hand_assessment": "Error occurred, folding as a safe default",
                    "positional_considerations": "N/A",
                    "opponent_reads": "N/A",
                    "archetype_alignment": "N/A"
                }
            }