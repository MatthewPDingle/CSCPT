"""
Base poker agent implementation.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple

from ..llm_service import LLMService
from ..prompts import POKER_ACTION_SCHEMA
from .models import MemoryService

logger = logging.getLogger(__name__)

class PokerAgent(ABC):
    """Base class for poker player agents."""
    
    # Class-level memory service instance shared by all agents
    _memory_service = None
    
    @classmethod
    def get_memory_service(cls) -> MemoryService:
        """
        Get the shared memory service instance.
        
        Returns:
            MemoryService instance
        """
        if cls._memory_service is None:
            # Create default memory service using home directory
            storage_dir = os.path.join(os.path.expanduser("~"), ".cscpt", "memory")
            cls._memory_service = MemoryService(storage_dir=storage_dir)
        
        return cls._memory_service
    
    def __init__(
        self,
        llm_service: LLMService,
        provider: Optional[str] = None,
        intelligence_level: str = "expert",
        temperature: float = 0.7,
        extended_thinking: bool = True,
        use_persistent_memory: bool = True
    ):
        """
        Initialize a poker agent.
        
        Args:
            llm_service: LLMService instance for making API calls
            provider: LLM provider to use (None for default)
            intelligence_level: Level of opponent modeling capability ("basic", "intermediate", "advanced", "expert")
            temperature: Temperature for LLM sampling (0.0 to 1.0)
            extended_thinking: Whether to use extended thinking mode
            use_persistent_memory: Whether to use persistent memory between sessions
        """
        self.llm_service = llm_service
        self.provider = provider
        self.intelligence_level = intelligence_level
        self.temperature = temperature
        self.extended_thinking = extended_thinking
        self.use_persistent_memory = use_persistent_memory
        
        # Initialize local opponent profiles for this session
        self.opponent_profiles = {}
        
        # Access to the memory service (if persistent memory is enabled)
        if use_persistent_memory:
            self.memory_service = self.get_memory_service()
        else:
            self.memory_service = None
        
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
        # If using persistent memory, get profiles from the memory service
        if self.use_persistent_memory and self.memory_service:
            # Get current player ID to exclude self from profiles
            my_player_id = None
            # We could add a player_id attribute to the agent in the future
            
            return self.memory_service.get_formatted_profiles(skip_players=[my_player_id] if my_player_id else None)
        
        # Otherwise, use in-session opponent profiles
        if not self.opponent_profiles:
            return "No opponent data available yet."
        
        profile_strings = []
        for player_id, profile in self.opponent_profiles.items():
            stats = []
            for stat_name, stat_value in profile.get("stats", {}).items():
                stats.append(f"[{stat_name}:{stat_value}]")
            
            notes = profile.get("notes", [])
            notes_str = f"[Noted:{','.join(notes)}]" if notes else ""
            
            exploits = profile.get("exploits", [])
            exploits_str = f"[Exploits:{','.join(exploits)}]" if exploits else ""
            
            profile_strings.append(f"Player{player_id}: {''.join(stats)} {exploits_str} {notes_str}")
        
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
        # Skip opponent modeling for basic intelligence level
        if self.intelligence_level == "basic":
            return
            
        action_history = game_state.get("action_history", [])
        if not action_history:
            return
        
        # Get the current betting round
        round_name = game_state.get("round", "PREFLOP")
        community_cards = game_state.get("community_cards", [])
        pot_size = game_state.get("pot", 0)
        
        # Determine the betting round based on community cards if not provided
        if round_name == "PREFLOP" and len(community_cards) >= 3:
            round_name = "FLOP" if len(community_cards) == 3 else "TURN" if len(community_cards) == 4 else "RIVER"
        
        # Track which players have been active this round
        active_players = set()
        preflop_raisers = set()
        preflop_callers = set()
        
        # First pass: gather information about raises and calls
        for action in action_history:
            player_id = action.get("player_id")
            if player_id is None:
                continue
                
            action_type = action.get("action", "").lower()
            
            # Track preflop actions
            if round_name == "PREFLOP":
                if action_type == "raise":
                    preflop_raisers.add(player_id)
                elif action_type == "call":
                    preflop_callers.add(player_id)
        
        # Second pass: detailed profile updates
        for action in action_history:
            player_id = action.get("player_id")
            if player_id is None:
                continue
                
            active_players.add(player_id)
            
            # Initialize or retrieve player profile
            if self.use_persistent_memory and self.memory_service:
                # Use persistent profiles from memory service
                profile = self.memory_service.get_profile(player_id)
                updates = {"hands_observed": 0, "stats": {}, "notes": []}
            else:
                # Use in-session profiles
                if player_id not in self.opponent_profiles:
                    self.opponent_profiles[player_id] = {
                        "stats": {
                            "VPIP": "Unknown",
                            "PFR": "Unknown",
                            "3Bet": "Unknown"
                        },
                        "notes": [],
                        "exploits": []
                    }
                profile = self.opponent_profiles[player_id]
            
            # Analyze the action
            action_type = action.get("action", "").lower()
            amount = action.get("amount", 0)
            
            # Track core stats
            if round_name == "PREFLOP":
                # VPIP - Voluntarily Put money In Pot
                if action_type in ["call", "raise", "bet"]:
                    if self.use_persistent_memory:
                        updates["stats"]["VPIP"] = 1.0
                    else:
                        profile["stats"]["VPIP"] = "Yes"
                
                # PFR - Preflop Raise
                if action_type in ["raise", "bet"]:
                    if self.use_persistent_memory:
                        updates["stats"]["PFR"] = 1.0
                    else:
                        profile["stats"]["PFR"] = "Yes"
                        
                # 3Bet - Three Betting
                if action_type == "raise" and action_history:
                    prev_raises = sum(1 for a in action_history if a.get("action", "").lower() == "raise")
                    if prev_raises >= 1:  # This would be at least a 3-bet
                        if self.use_persistent_memory:
                            updates["stats"]["3Bet"] = 1.0
                        else:
                            profile["stats"]["3Bet"] = "Yes"
            
            # Track post-flop tendencies
            elif round_name in ["FLOP", "TURN", "RIVER"]:
                # C-bet (continuation bet)
                if action_type in ["bet", "raise"] and player_id in preflop_raisers and round_name == "FLOP":
                    if self.use_persistent_memory:
                        updates["notes"].append({"text": "Made continuation bet on flop", "category": "betting"})
                    else:
                        if "C-bets flop" not in profile["notes"]:
                            profile["notes"].append("C-bets flop")
                
                # Check-raise
                prev_action = next((a for a in reversed(action_history) 
                                 if a.get("player_id") == player_id and a.get("action", "").lower() == "check"), None)
                if prev_action and action_type == "raise":
                    if self.use_persistent_memory:
                        updates["notes"].append({"text": f"Check-raised on {round_name.lower()}", "category": "deception"})
                    else:
                        if "Check-raises" not in profile["notes"]:
                            profile["notes"].append("Check-raises")
            
            # Note aggressive actions
            if action_type in ["raise", "bet"]:
                if round_name in ["TURN", "RIVER"]:
                    if self.use_persistent_memory:
                        updates["notes"].append({"text": f"Aggressive on {round_name.lower()}", "category": "aggression"})
                    else:
                        if "Aggressive" not in profile["notes"]:
                            profile["notes"].append("Aggressive")
            
            # Note passive actions when facing bets
            elif action_type == "call" and any(a.get("action", "").lower() in ["bet", "raise"] 
                                           for a in action_history if a != action):
                if self.use_persistent_memory:
                    updates["notes"].append({"text": f"Called bet/raise on {round_name.lower()}", "category": "passivity"})
                else:
                    if "Calls frequently" not in profile["notes"]:
                        profile["notes"].append("Calls frequently")
            
            # Identify potential exploits (advanced intelligence levels only)
            if self.intelligence_level in ["advanced", "expert"] and not self.use_persistent_memory:
                # Look for exploitable tendencies
                if "Calls frequently" in profile["notes"] and round_name in ["FLOP", "TURN", "RIVER"]:
                    if "Calls too much postflop" not in profile.get("exploits", []):
                        if "exploits" not in profile:
                            profile["exploits"] = []
                        profile["exploits"].append("Calls too much postflop")
                
                if action_type == "fold" and pot_size > 0 and round_name in ["FLOP", "TURN", "RIVER"]:
                    if "Folds to aggression" not in profile.get("exploits", []):
                        if "exploits" not in profile:
                            profile["exploits"] = []
                        profile["exploits"].append("Folds to aggression")
            
            # Apply updates to persistent memory if using it
            if self.use_persistent_memory and self.memory_service and (updates["stats"] or updates["notes"]):
                self.memory_service.update_profile(player_id, updates)
    
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
            import traceback
            logger.error(traceback.format_exc())
            
            # Determine a more intelligent fallback action based on the game state
            current_bet = game_state.get("current_bet", 0)
            
            # If there's no bet to call, check instead of folding
            if current_bet == 0:
                fallback_action = "check"
                action_reason = "checking as fallback since there's no bet to call"
            else:
                # Get player's stack size
                stack = game_state.get("stack_sizes", {}).get("0", 0)
                
                # If the call is a significant portion of stack, fold
                if current_bet > stack / 3:
                    fallback_action = "fold"
                    action_reason = f"folding as fallback - call of {current_bet} is too large relative to stack of {stack}"
                else:
                    # Otherwise try to call
                    fallback_action = "call"
                    action_reason = f"calling as fallback - bet of {current_bet} is reasonable relative to stack of {stack}"
            
            # Return a more descriptive fallback response
            return {
                "thinking": f"Error occurred in LLM response: {str(e)}\nUsing fallback logic: {action_reason}",
                "action": fallback_action,
                "amount": None,
                "reasoning": {
                    "hand_assessment": f"Error occurred, {action_reason}",
                    "positional_considerations": "Using fallback decision process",
                    "opponent_reads": "No opponent reads available due to error",
                    "archetype_alignment": f"Aligned with {self.__class__.__name__} - conservative fallback"
                }
            }
            
    def update_memory_after_hand(self, hand_data: Dict[str, Any]) -> None:
        """
        Update persistent memory after a hand is completed.
        
        Args:
            hand_data: Data about the completed hand
        """
        if not self.use_persistent_memory or not self.memory_service:
            return
            
        # Process the hand data to update player profiles
        self.memory_service.process_hand_result(hand_data)