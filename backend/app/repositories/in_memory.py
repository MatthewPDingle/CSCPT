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

from app.models.domain_models import Game, User, ActionHistory, Hand
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
                return list(copy.deepcopy(self.data.values()))
            
            # Apply filters
            result = []
            for entity in self.data.values():
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