"""
Connector service to integrate memory system with the game backend.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List, Set

from .memory_service import MemoryService
from .opponent_profile import OpponentProfile

logger = logging.getLogger(__name__)

class MemoryConnector:
    """
    Connector to integrate the memory service with the game backend.
    
    This provides hooks for the backend to use the memory system without
    direct dependencies on the AI module.
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls) -> "MemoryConnector":
        """
        Get or create the singleton instance.
        
        Returns:
            MemoryConnector instance
        """
        if cls._instance is None:
            cls._instance = MemoryConnector()
        return cls._instance
    
    def __init__(self):
        """Initialize the memory connector."""
        self.memory_service = MemoryService()
        self._enabled = True
    
    def enable(self) -> None:
        """Enable the memory system."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable the memory system (no recording or retrieval)."""
        self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if memory system is enabled."""
        return self._enabled
    
    def process_hand_history(self, hand_history: Dict[str, Any]) -> None:
        """
        Process a complete hand history to update memory.
        
        Args:
            hand_history: Complete hand history data
        """
        if not self._enabled:
            return
            
        try:
            self.memory_service.process_hand_result(hand_history)
            logger.debug(f"Processed hand history for memory: hand {hand_history.get('hand_number')}")
        except Exception as e:
            logger.error(f"Error processing hand history for memory: {str(e)}")
    
    def get_player_profile(self, player_id: str, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a player's profile data.
        
        Args:
            player_id: The player ID
            name: Optional player name for new profiles
            
        Returns:
            Dictionary with profile data
        """
        if not self._enabled:
            return {
                "player_id": player_id,
                "name": name or f"Player{player_id}",
                "stats": {},
                "notes": []
            }
            
        try:
            profile = self.memory_service.get_profile(player_id, name)
            return {
                "player_id": profile.player_id,
                "name": profile.name,
                "archetype": profile.archetype,
                "stats": {k: v.value for k, v in profile.stats.items()},
                "notes": [n.note for n in profile.notes[:5]],  # Just the 5 most recent notes
                "exploits": profile.exploitable_tendencies,
                "hands_observed": profile.hands_observed
            }
        except Exception as e:
            logger.error(f"Error getting player profile: {str(e)}")
            return {
                "player_id": player_id,
                "name": name or f"Player{player_id}",
                "stats": {},
                "notes": []
            }
    
    def get_all_profiles(self) -> List[Dict[str, Any]]:
        """
        Get all available player profiles.
        
        Returns:
            List of player profile dictionaries
        """
        if not self._enabled:
            return []
            
        try:
            profiles = []
            for player_id, profile in self.memory_service.active_profiles.items():
                profiles.append({
                    "player_id": profile.player_id,
                    "name": profile.name,
                    "archetype": profile.archetype,
                    "stats": {k: (str(v.value) if not isinstance(v.value, str) else v.value) 
                             for k, v in profile.stats.items()},
                    "exploits": profile.exploitable_tendencies,
                    "hands_observed": profile.hands_observed
                })
            return profiles
        except Exception as e:
            logger.error(f"Error getting all profiles: {str(e)}")
            return []
    
    def update_profile_from_action(self, 
                                  player_id: str, 
                                  action_type: str, 
                                  amount: Optional[int] = None, 
                                  betting_round: str = "PREFLOP",
                                  game_state: Optional[Dict[str, Any]] = None) -> None:
        """
        Update a player profile based on an observed action.
        
        Args:
            player_id: The player taking the action
            action_type: Type of action (fold, check, call, bet, raise, all-in)
            amount: Amount of the action (if applicable)
            betting_round: Current betting round
            game_state: Additional game state information
        """
        if not self._enabled:
            return
            
        try:
            # Simple action-based update
            updates = {
                "hands_observed": 0,
                "stats": {},
                "notes": []
            }
            
            # Track statistics for different betting rounds
            if betting_round == "PREFLOP":
                if action_type.lower() in ["call", "bet", "raise", "all-in"]:
                    updates["stats"]["VPIP"] = 1.0
                
                if action_type.lower() in ["bet", "raise", "all-in"]:
                    updates["stats"]["PFR"] = 1.0
            
            # Add note about the action
            updates["notes"].append({
                "text": f"{action_type.capitalize()} {amount if amount else ''} on {betting_round.lower()}",
                "category": "action"
            })
            
            # Apply the updates
            self.memory_service.update_profile(player_id, updates)
            
        except Exception as e:
            logger.error(f"Error updating profile from action: {str(e)}")
    
    def clear_all_memory(self) -> None:
        """Clear all memory data (for testing purposes)."""
        try:
            # Reset active profiles
            self.memory_service.active_profiles = {}
            logger.info("All memory data cleared")
        except Exception as e:
            logger.error(f"Error clearing memory: {str(e)}")