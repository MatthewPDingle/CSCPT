# mypy: ignore-errors
"""
Base repository interfaces that define the contract for data access.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any, Dict

T = TypeVar("T")  # Generic type for entities


class Repository(Generic[T], ABC):
    """
    Base repository interface that defines standard CRUD operations.
    All concrete repositories should implement these methods.
    """

    @abstractmethod
    def get(self, id: str) -> Optional[T]:
        """
        Retrieve an entity by its ID.

        Args:
            id: The unique identifier of the entity

        Returns:
            The entity if found, None otherwise
        """
        pass

    @abstractmethod
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """
        List all entities matching the given filters.

        Args:
            filters: Optional dictionary of field name to filter value

        Returns:
            List of entities matching the filters
        """
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        """
        Create a new entity.

        Args:
            entity: The entity to create

        Returns:
            The created entity with any system-generated fields populated
        """
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """
        Update an existing entity.

        Args:
            entity: The entity to update with its ID and updated fields

        Returns:
            The updated entity
        """
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """
        Delete an entity by its ID.

        Args:
            id: The unique identifier of the entity to delete

        Returns:
            True if the entity was deleted, False otherwise
        """
        pass
