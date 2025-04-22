"""
Base poker agent implementation.
"""

import logging
import json
import os
from datetime import datetime
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
    
    def _build_opponent_profile_string(self, names_map: Optional[Dict[str, str]] = None) -> str:
        """
        Build a string representation of opponent profiles, using player names when provided.

        Args:
            names_map: Optional mapping from player_id to player name

        Returns:
            Formatted string of opponent profiles
        """
        # If using persistent memory, get profiles from the memory service
        if self.use_persistent_memory and self.memory_service:
            # Fallback to memory_service output (IDs may appear here)
            return self.memory_service.get_formatted_profiles()
        # Otherwise, use in-session opponent profiles
        if not self.opponent_profiles:
            return "No opponent data available yet."
        profile_strings = []
        for player_id, profile in self.opponent_profiles.items():
            # Determine display name
            display = names_map.get(player_id, f"Player{player_id}") if names_map else f"Player{player_id}"
            # Stats
            stats = []
            for stat_name, stat_value in profile.get("stats", {}).items():
                stats.append(f"[{stat_name}:{stat_value}]")
            # Notes
            notes = profile.get("notes", [])
            notes_str = f"[Noted:{','.join(notes)}]" if notes else ""
            # Exploits
            exploits = profile.get("exploits", [])
            exploits_str = f"[Exploits:{','.join(exploits)}]" if exploits else ""
            profile_strings.append(f"{display}: {''.join(stats)} {exploits_str} {notes_str}".strip())
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
        
        # Normalize card representations into strings
        hand_cards: List[str] = []
        for h in hand:
            if isinstance(h, dict):
                hand_cards.append(h.get('rank', '') + h.get('suit', ''))
            else:
                hand_cards.append(str(h))
        comm_cards: List[str] = []
        for c in community_cards:
            if isinstance(c, dict):
                comm_cards.append(c.get('rank', '') + c.get('suit', ''))
            else:
                comm_cards.append(str(c))
        # Prepare mapping of player IDs to names for readable logs
        names_map = game_state.get('player_names', {})
        # Format stack sizes using player names
        stack_str = ", ".join([
            f"{names_map.get(pid, pid)}: {stack}"
            for pid, stack in stack_sizes.items()
        ])
        # Format the state as a string
        formatted_state = f"""
GAME STATE:
Your Hand: {' '.join(hand_cards)}
Community Cards: {' '.join(comm_cards) if comm_cards else 'None'}
Position: {position}
Pot Size: {pot}
Action History: {self._format_action_history(action_history, names_map)}
Stack Sizes: {stack_str}
"""
        return formatted_state
    
    def _format_action_history(
        self,
        action_history: List[Dict[str, Any]],
        names_map: Dict[str, str]
    ) -> str:
        """Format the action history into a readable string, replacing IDs with names."""
        if not action_history:
            return "No actions yet."

        formatted_actions = []
        for action in action_history:
            pid = action.get("player_id", "Unknown")
            name = names_map.get(pid, pid)
            action_type = action.get("action", "Unknown")
            amount = action.get("amount", None)

            if amount is not None:
                formatted_actions.append(f"{name} {action_type} {amount}")
            else:
                formatted_actions.append(f"{name} {action_type}")

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
        # --- Prepare nested and flattened game states ---
        # Keep the raw nested state for full JSON
        nested_state = game_state
        # Build flattened state for formatting, include a name map so we can show player names
        players = nested_state.get('players', []) or []
        # Map player IDs to names for logging
        player_names = {p.get('player_id'): p.get('name') for p in players if p.get('player_id')}
        # Identify this agent's player entry
        player_entry = next((p for p in players if p.get('player_id') == getattr(self, 'player_id', None)), None)
        hand = player_entry.get('cards', []) if player_entry else []
        position = player_entry.get('position') if player_entry else None
        flat_state = {
            'hand': hand,
            'community_cards': nested_state.get('community_cards', []),
            'position': position,
            'pot': nested_state.get('total_pot', 0),
            'action_history': nested_state.get('action_history', []),
            'stack_sizes': {p.get('player_id'): p.get('chips', 0) for p in players},
            'player_names': player_names,
            'round': nested_state.get('current_round'),
            'current_bet': nested_state.get('current_bet', 0)
        }
        # Update opponent profiles based on game state
        if self.intelligence_level != "basic":
            self._update_opponent_profiles(flat_state)
        # Format state summary and full JSON
        formatted_state = self._format_game_state(flat_state)
        try:
            # Prepare JSON for full game state: rename current_bet, substitute IDs with names in pots and action history
            raw_nested = dict(nested_state)
            # Build ID → name map from players list
            players_list = raw_nested.get('players', []) or []
            id_to_name = {p.get('player_id'): p.get('name') for p in players_list if p.get('player_id') and p.get('name')}
            # Rename top-level current_bet to to_call
            if 'current_bet' in raw_nested:
                raw_nested['to_call'] = raw_nested.pop('current_bet')
            # Replace eligible_player_ids with names in each pot
            pots = raw_nested.get('pots')
            if isinstance(pots, list):
                for pot in pots:
                    if 'eligible_player_ids' in pot:
                        ids = pot.pop('eligible_player_ids') or []
                        pot['eligible_player_names'] = [id_to_name.get(pid, pid) for pid in ids]
            # Replace player_id with name in action history entries
            history = raw_nested.get('action_history')
            if isinstance(history, list):
                for entry in history:
                    pid = entry.pop('player_id', None)
                    if pid is not None:
                        entry['name'] = id_to_name.get(pid, pid)
            raw_state = json.dumps(raw_nested, indent=2)
        except Exception:
            raw_state = str(nested_state)
        # Build opponent profiles string, using player names where available
        names_map = flat_state.get('player_names', {}) if isinstance(flat_state, dict) else {}
        opponent_profiles = self._build_opponent_profile_string(names_map)

        # Build user prompt including formatted state, full JSON, opponent profiles, and context
        user_prompt = f"""
{formatted_state}

FULL GAME STATE JSON:
{raw_state}

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
        # Log system and user prompts to per-player logs
        try:
            # Determine agent name for logging
            players_list = nested_state.get('players', [])
            agent_name = next(
                (p.get('name') for p in players_list if p.get('player_id') == getattr(self, 'player_id', None)),
                getattr(self, 'player_id', 'unknown')
            )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            logs_dir = os.path.expanduser("~/.cscpt/player_logs")
            os.makedirs(logs_dir, exist_ok=True)
            # Write prompts to file
            to_path = os.path.join(logs_dir, f"{timestamp}_{agent_name}_to.log")
            with open(to_path, 'w') as f:
                f.write("SYSTEM PROMPT:\n")
                f.write(system_prompt + "\n\n")
                f.write("USER PROMPT:\n")
                f.write(user_prompt)
        except Exception:
            logger.warning("Failed to write per-player prompt log", exc_info=True)
        
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
            
            # Reorder fields for clearer human output: thinking, calculations, reasoning, action, amount
            try:
                ordered = {}
                for key in ('thinking', 'calculations', 'reasoning', 'action', 'amount'):
                    if key in response:
                        ordered[key] = response[key]
                # Append any other keys afterwards
                for key, val in response.items():
                    if key not in ordered:
                        ordered[key] = val
                response = ordered
            except Exception:
                # If reordering fails, keep original
                pass
            logger.debug(f"Agent decision: {response}")
            # Log response to per-player log
            try:
                from_path = os.path.join(logs_dir, f"{timestamp}_{agent_name}_from.log")
                with open(from_path, 'w') as f:
                    f.write(json.dumps(response, indent=2))
            except Exception:
                logger.warning("Failed to write per-player response log", exc_info=True)
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