"""
In-memory implementation of repositories.
These repositories store data in memory and provide thread-safe access.
"""
import copy
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, TypeVar, Generic, Any, Type

from pydantic import BaseModel

from app.models.domain_models import Game, User, ActionHistory, Hand, HandHistory, PlayerStats, PlayerAction
from app.repositories.base import Repository

T = TypeVar('T', bound=BaseModel)


class InMemoryRepository(Generic[T], Repository[T]):
    """
    Generic in-memory repository implementation that can store any Pydantic model.
    Thread-safe for concurrent access with a read-write lock.
    """
    
    def __init__(self, model_class: Type[T]):
        """
        Initialize a new in-memory repository.
        
        Args:
            model_class: The Pydantic model class this repository will store
        """
        self.model_class = model_class
        self.data: Dict[str, T] = {}
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        
    def get(self, id: str) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: The ID of the entity to retrieve
            
        Returns:
            A deep copy of the entity if found, None otherwise
        """
        with self.lock:
            entity = self.data.get(id)
            if entity:
                # Return a deep copy to prevent accidental mutations
                return copy.deepcopy(entity)
            return None
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """
        List entities matching the given filters.
        
        Args:
            filters: Optional dictionary of field names to filter values
            
        Returns:
            List of entities matching the filters
        """
        with self.lock:
            if not filters:
                # Return all entities if no filters provided
                return [copy.deepcopy(entity) for entity in self.data.values()]
            
            # Apply filters
            result = []
            for entity in self.data.values():
                # Use model_dump() instead of dict() for Pydantic v2 compatibility
                try:
                    entity_dict = entity.model_dump()
                except AttributeError:
                    # Fallback for older Pydantic versions
                    entity_dict = entity.dict()
                
                matches = True
                
                for key, value in filters.items():
                    # Handle nested keys with dot notation (e.g., "user.name")
                    if "." in key:
                        parts = key.split(".")
                        nested_value = entity_dict
                        for part in parts:
                            if isinstance(nested_value, dict) and part in nested_value:
                                nested_value = nested_value[part]
                            else:
                                matches = False
                                break
                        if nested_value != value:
                            matches = False
                    # Simple key match
                    elif key not in entity_dict or entity_dict[key] != value:
                        matches = False
                        
                if matches:
                    result.append(copy.deepcopy(entity))
                    
            return result
    
    def create(self, entity: T) -> T:
        """
        Create a new entity.
        
        Args:
            entity: The entity to create
            
        Returns:
            A copy of the created entity
        """
        with self.lock:
            # Ensure the entity has an ID
            try:
                entity_dict = entity.model_dump()
            except AttributeError:
                # Fallback for older Pydantic versions
                entity_dict = entity.dict()
                
            if "id" not in entity_dict or not entity_dict["id"]:
                raise ValueError("Entity must have an ID")
                
            # Store a copy of the entity
            entity_id = entity_dict["id"]
            self.data[entity_id] = copy.deepcopy(entity)
            
            # Return a copy to prevent accidental mutations
            return copy.deepcopy(entity)
    
    def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
            
        Returns:
            A copy of the updated entity
            
        Raises:
            KeyError: If the entity doesn't exist
        """
        with self.lock:
            try:
                entity_dict = entity.model_dump()
            except AttributeError:
                # Fallback for older Pydantic versions
                entity_dict = entity.dict()
                
            entity_id = entity_dict["id"]
            
            if entity_id not in self.data:
                raise KeyError(f"Entity with ID {entity_id} not found")
                
            # Update "updated_at" field if it exists in the model
            if hasattr(entity, "updated_at"):
                entity.updated_at = datetime.now()
                
            # Store a copy of the updated entity
            self.data[entity_id] = copy.deepcopy(entity)
            
            # Return a copy to prevent accidental mutations
            return copy.deepcopy(entity)
    
    def delete(self, id: str) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            id: The ID of the entity to delete
            
        Returns:
            True if the entity was deleted, False if it didn't exist
        """
        with self.lock:
            if id in self.data:
                del self.data[id]
                return True
            return False


# Concrete repository implementations
class GameRepository(InMemoryRepository[Game]):
    """Repository for Game entities."""
    def __init__(self):
        super().__init__(Game)
        
    def get_active_games(self) -> List[Game]:
        """Get all active games."""
        from app.models.domain_models import GameStatus
        return self.list({"status": GameStatus.ACTIVE})
        
    def get_games_by_player(self, player_id: str) -> List[Game]:
        """Get all games a player is participating in."""
        result = []
        with self.lock:
            for game in self.data.values():
                if any(player.id == player_id for player in game.players):
                    result.append(copy.deepcopy(game))
        return result


class UserRepository(InMemoryRepository[User]):
    """Repository for User entities."""
    def __init__(self):
        super().__init__(User)
        
    def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        users = self.list({"username": username})
        return users[0] if users else None


class ActionHistoryRepository(InMemoryRepository[ActionHistory]):
    """Repository for ActionHistory entities."""
    def __init__(self):
        super().__init__(ActionHistory)
        
    def get_by_game(self, game_id: str) -> List[ActionHistory]:
        """Get all actions for a game."""
        return self.list({"game_id": game_id})
        
    def get_by_hand(self, hand_id: str) -> List[ActionHistory]:
        """Get all actions for a specific hand."""
        return self.list({"hand_id": hand_id})


class HandRepository(InMemoryRepository[Hand]):
    """Repository for Hand entities."""
    def __init__(self):
        super().__init__(Hand)
        
    def get_by_game(self, game_id: str) -> List[Hand]:
        """Get all hands for a game."""
        return self.list({"game_id": game_id})


class HandHistoryRepository(InMemoryRepository[HandHistory]):
    """Repository for HandHistory entities."""
    def __init__(self):
        super().__init__(HandHistory)
        
    def get_by_game(self, game_id: str) -> List[HandHistory]:
        """Get all hand histories for a game."""
        return self.list({"game_id": game_id})
        
    def get_by_player(self, player_id: str) -> List[HandHistory]:
        """Get all hands a player participated in."""
        result = []
        with self.lock:
            for hand in self.data.values():
                player_ids = [p.player_id for p in hand.players]
                if player_id in player_ids:
                    result.append(copy.deepcopy(hand))
        return result
        
    def get_player_stats(self, player_id: str, game_id: Optional[str] = None) -> PlayerStats:
        """
        Calculate aggregate stats for a player.
        
        Args:
            player_id: ID of the player to calculate stats for
            game_id: Optional game ID to limit stats to a specific game
            
        Returns:
            A PlayerStats object with calculated statistics
        """
        hands = self.get_by_player(player_id)
        
        # Filter by game_id if provided
        if game_id:
            hands = [h for h in hands if h.game_id == game_id]
            
        if not hands:
            return PlayerStats(player_id=player_id)
            
        # Initialize stats
        stats = PlayerStats(player_id=player_id)
        stats.hands_played = len(hands)
        
        # Counters for various stats
        vpip_count = 0
        pfr_count = 0
        showdown_count = 0
        won_showdown_count = 0
        aggressive_actions = 0
        passive_actions = 0
        cbet_attempts = 0
        cbet_successes = 0
        won_after_preflop = 0
        total_winnings = 0
        total_losses = 0
        win_count = 0
        loss_count = 0
        
        # Calculate stats from hands
        for hand in hands:
            # Find player in hand
            player = next((p for p in hand.players if p.player_id == player_id), None)
            if not player:
                continue
                
            # VPIP and PFR
            if player.vpip:
                vpip_count += 1
            if player.pfr:
                pfr_count += 1
                
            # Showdown stats
            if hand.metrics.showdown_reached:
                showdown_count += 1
                if player.won_amount > 0:
                    won_showdown_count += 1
                    
            # Aggression stats
            for round_name, actions in hand.betting_rounds.items():
                for action in actions:
                    if action.player_id == player_id:
                        if action.action_type in [PlayerAction.BET, PlayerAction.RAISE]:
                            aggressive_actions += 1
                        elif action.action_type == PlayerAction.CALL:
                            passive_actions += 1
                            
            # C-bet stats
            preflop_actions = hand.betting_rounds.get("PREFLOP", [])
            if preflop_actions and preflop_actions[-1].player_id == player_id:
                flop_actions = hand.betting_rounds.get("FLOP", [])
                if flop_actions:
                    first_to_act = next((a for a in flop_actions 
                                       if a.player_id == player_id), None)
                    if first_to_act and first_to_act.action_type in [PlayerAction.BET, PlayerAction.RAISE]:
                        cbet_attempts += 1
                        if all(a.action_type == PlayerAction.FOLD 
                             for a in flop_actions 
                             if a.player_id != player_id and a.position_in_action_sequence > first_to_act.position_in_action_sequence):
                            cbet_successes += 1
            
            # Won without showdown
            if player.won_amount > 0 and not hand.metrics.showdown_reached:
                won_after_preflop += 1
                
            # Winnings and losses
            if player.won_amount > 0:
                total_winnings += player.won_amount
                win_count += 1
                stats.biggest_win = max(stats.biggest_win, player.won_amount)
            elif player.won_amount < 0:
                total_losses += abs(player.won_amount)
                loss_count += 1
                stats.biggest_loss = max(stats.biggest_loss, abs(player.won_amount))
                
        # Calculate percentages and averages
        if stats.hands_played > 0:
            stats.vpip = vpip_count / stats.hands_played * 100
            stats.pfr = pfr_count / stats.hands_played * 100
            stats.wapf = won_after_preflop / stats.hands_played * 100
            stats.bb_per_hand = (total_winnings - total_losses) / stats.hands_played
            
        if showdown_count > 0:
            stats.wtsd = showdown_count / stats.hands_played * 100
            stats.won_at_showdown = won_showdown_count / showdown_count * 100
            
        if passive_actions > 0:
            stats.af = aggressive_actions / passive_actions
            
        if cbet_attempts > 0:
            stats.cbet_attempt = cbet_attempts / stats.hands_played * 100
            stats.cbet_success = cbet_successes / cbet_attempts * 100
            
        if win_count > 0:
            stats.avg_win = total_winnings / win_count
            
        if loss_count > 0:
            stats.avg_loss = total_losses / loss_count
            
        return stats


# Factory to get repository instances
class RepositoryFactory:
    """Factory class to get repository instances."""
    _instance = None
    _repositories = {}
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of the factory."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def _reset_instance_for_testing(cls):
        """
        Reset the singleton instance and all repositories.
        
        NOTE: This method should ONLY be used in test code, never in production.
        It's designed to allow tests to start with clean repositories.
        """
        cls._instance = None
        cls._repositories = {}
    
    def get_repository(self, repo_type) -> Repository:
        """
        Get a repository instance of the specified type.
        
        Args:
            repo_type: The repository class
            
        Returns:
            An instance of the repository
        """
        repo_name = repo_type.__name__
        if repo_name not in self._repositories:
            self._repositories[repo_name] = repo_type()
        return self._repositories[repo_name]