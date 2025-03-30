"""
Memory service for poker agents to track and analyze opponent behavior across games.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta

from .opponent_profile import OpponentProfile, StatisticValue

logger = logging.getLogger(__name__)

class MemoryService:
    """
    Service for managing poker player memory across sessions.
    Handles opponent profiles and strategic adaptations.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the memory service.
        
        Args:
            storage_dir: Directory to store memory data. If None, uses default location.
        """
        if storage_dir is None:
            # Use default location in the user's home directory
            home_dir = os.path.expanduser("~")
            self.storage_dir = os.path.join(home_dir, ".cscpt", "memory")
        else:
            self.storage_dir = storage_dir
            
        # Create directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Track active profiles in memory
        self.active_profiles: Dict[str, OpponentProfile] = {}
        
        # Load existing profiles
        self._load_profiles()
    
    def _get_profile_path(self, player_id: str) -> str:
        """Get the file path for a player profile."""
        return os.path.join(self.storage_dir, f"player_{player_id}.json")
    
    def _load_profiles(self) -> None:
        """Load all existing profiles from storage."""
        try:
            for file_path in Path(self.storage_dir).glob("player_*.json"):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        profile = OpponentProfile.parse_obj(data)
                        self.active_profiles[profile.player_id] = profile
                except Exception as e:
                    logger.error(f"Error loading profile from {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error scanning profiles directory: {str(e)}")
    
    def _save_profile(self, profile: OpponentProfile) -> bool:
        """
        Save a profile to storage.
        
        Args:
            profile: The opponent profile to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._get_profile_path(profile.player_id)
            with open(file_path, "w") as f:
                f.write(profile.json(indent=2))
            return True
        except Exception as e:
            logger.error(f"Error saving profile for player {profile.player_id}: {str(e)}")
            return False
    
    def get_profile(self, player_id: str, name: Optional[str] = None) -> OpponentProfile:
        """
        Get a player's profile, creating it if it doesn't exist.
        
        Args:
            player_id: The player's unique identifier
            name: Optional player name for new profiles
            
        Returns:
            The player's profile
        """
        if player_id not in self.active_profiles:
            # Create new profile
            self.active_profiles[player_id] = OpponentProfile(
                player_id=player_id,
                name=name or f"Player{player_id}"
            )
        
        # Update last observed timestamp
        profile = self.active_profiles[player_id]
        profile.last_observed = datetime.now()
        
        return profile
    
    def update_profile(self, player_id: str, updates: Dict[str, Any]) -> Optional[OpponentProfile]:
        """
        Update a player's profile with new information.
        
        Args:
            player_id: The player's unique identifier
            updates: Dictionary of updates to apply
            
        Returns:
            The updated profile, or None if the player wasn't found
        """
        profile = self.get_profile(player_id)
        
        # Apply statistical updates
        for stat_name, stat_value in updates.get("stats", {}).items():
            if isinstance(stat_value, dict):
                profile.update_statistic(
                    name=stat_name,
                    value=stat_value.get("value", 0),
                    sample_size=stat_value.get("sample_size", 1),
                    confidence=stat_value.get("confidence")
                )
            else:
                # Simple value update
                profile.update_statistic(name=stat_name, value=stat_value)
        
        # Add notes
        for note in updates.get("notes", []):
            if isinstance(note, str):
                profile.add_note(note=note)
            elif isinstance(note, dict):
                profile.add_note(
                    note=note.get("text", ""),
                    category=note.get("category", "general"),
                    hand_id=note.get("hand_id"),
                    confidence=note.get("confidence", 0.5)
                )
        
        # Update hands observed
        if "hands_observed" in updates:
            profile.hands_observed += updates["hands_observed"]
        
        # Detect archetype based on statistics
        if profile.hands_observed >= 10:
            profile.archetype = profile.assess_archetype()
            
        # Identify exploitable tendencies
        profile.identify_exploits()
        
        # Save the updated profile
        self._save_profile(profile)
        
        return profile
    
    def process_hand_result(self, hand_data: Dict[str, Any]) -> None:
        """
        Process the results of a hand to update player profiles.
        
        Args:
            hand_data: Data from a completed hand
        """
        # Extract players
        players = hand_data.get("players", [])
        for player in players:
            player_id = player.get("player_id")
            if not player_id:
                continue
                
            # Skip updating for human players
            if player.get("is_human", False):
                continue
                
            # Prepare updates
            updates = {
                "hands_observed": 1,
                "stats": {},
                "notes": []
            }
            
            # Update core stats
            if player.get("vpip") is not None:
                vpip_value = 1.0 if player.get("vpip") else 0.0
                # Get existing VPIP or default to this value
                profile = self.get_profile(player_id, player.get("name"))
                current_vpip = 0.0
                current_samples = 0
                
                if "VPIP" in profile.stats:
                    stat = profile.stats["VPIP"]
                    if isinstance(stat.value, (int, float)):
                        current_vpip = float(stat.value)
                        current_samples = stat.sample_size
                
                # Calculate new VPIP percentage
                total_samples = current_samples + 1
                new_vpip = ((current_vpip * current_samples) + vpip_value) / total_samples
                
                updates["stats"]["VPIP"] = {
                    "value": new_vpip,
                    "sample_size": 1,
                    "confidence": min(0.3 + (total_samples / 100), 0.9)
                }
            
            # Update PFR (Pre-Flop Raise) stat
            if player.get("pfr") is not None:
                pfr_value = 1.0 if player.get("pfr") else 0.0
                # Get existing PFR or default to this value
                profile = self.get_profile(player_id, player.get("name"))
                current_pfr = 0.0
                current_samples = 0
                
                if "PFR" in profile.stats:
                    stat = profile.stats["PFR"]
                    if isinstance(stat.value, (int, float)):
                        current_pfr = float(stat.value)
                        current_samples = stat.sample_size
                
                # Calculate new PFR percentage
                total_samples = current_samples + 1
                new_pfr = ((current_pfr * current_samples) + pfr_value) / total_samples
                
                updates["stats"]["PFR"] = {
                    "value": new_pfr,
                    "sample_size": 1,
                    "confidence": min(0.3 + (total_samples / 100), 0.9)
                }
            
            # Add behavioral notes based on patterns
            if player.get("showed_cards") and player.get("won_amount", 0) > 0:
                updates["notes"].append({
                    "text": f"Won showdown with {', '.join(player.get('hole_cards', []))}",
                    "category": "showdown"
                })
            
            # Process actions across betting rounds
            # This would extract more detailed stats based on the action history
            
            # Finally apply all updates
            self.update_profile(player_id, updates)
    
    def get_formatted_profiles(self, skip_players: Optional[List[str]] = None) -> str:
        """
        Get a formatted string of all active profiles for use in LLM prompts.
        
        Args:
            skip_players: Optional list of player IDs to exclude
            
        Returns:
            Formatted string with player profiles
        """
        if not self.active_profiles:
            return "No opponent data available yet."
            
        skip_ids = set(skip_players or [])
        profile_strings = []
        
        # Include only recently observed profiles (within last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        
        for player_id, profile in self.active_profiles.items():
            if player_id in skip_ids:
                continue
                
            if profile.last_observed >= recent_cutoff:
                profile_strings.append(profile.get_formatted_string())
        
        if not profile_strings:
            return "No recent opponent data available."
            
        return "\n".join(profile_strings)