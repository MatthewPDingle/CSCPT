# mypy: ignore-errors
"""
Unit tests for the in-memory repository implementation.
"""

import pytest
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from app.models.domain_models import User, Game, GameType, GameStatus
from app.repositories.in_memory import InMemoryRepository


class TestInMemoryRepository:
    """Tests for the InMemoryRepository class."""

    def test_create_entity(self):
        """Test creating an entity in the repository."""
        repo = InMemoryRepository(User)
        user = User(id=str(uuid.uuid4()), username="testuser")

        # Create the entity
        created = repo.create(user)

        # Verify it was created
        assert created.id == user.id
        assert created.username == user.username

        # Verify it's in the repository
        assert len(repo.data) == 1
        assert user.id in repo.data

    def test_get_entity(self):
        """Test retrieving an entity from the repository."""
        repo = InMemoryRepository(User)
        user_id = str(uuid.uuid4())
        user = User(id=user_id, username="testuser")
        repo.create(user)

        # Get the entity
        retrieved = repo.get(user_id)

        # Verify it was retrieved correctly
        assert retrieved is not None
        assert retrieved.id == user_id
        assert retrieved.username == "testuser"

        # Verify we get a copy, not the original
        assert retrieved is not user
        assert retrieved is not repo.data[user_id]

        # Test getting non-existent entity
        non_existent = repo.get("non-existent-id")
        assert non_existent is None

    def test_update_entity(self):
        """Test updating an entity in the repository."""
        repo = InMemoryRepository(User)
        user_id = str(uuid.uuid4())
        user = User(id=user_id, username="testuser")
        repo.create(user)

        # Update the entity
        updated_user = User(id=user_id, username="newname")
        result = repo.update(updated_user)

        # Verify the update was successful
        assert result.username == "newname"

        # Verify the repository was updated
        stored = repo.get(user_id)
        assert stored.username == "newname"

        # Test updating non-existent entity
        non_existent = User(id="non-existent-id", username="test")
        with pytest.raises(KeyError):
            repo.update(non_existent)

    def test_delete_entity(self):
        """Test deleting an entity from the repository."""
        repo = InMemoryRepository(User)
        user_id = str(uuid.uuid4())
        user = User(id=user_id, username="testuser")
        repo.create(user)

        # Delete the entity
        result = repo.delete(user_id)

        # Verify the deletion was successful
        assert result is True
        assert user_id not in repo.data
        assert repo.get(user_id) is None

        # Test deleting non-existent entity
        result = repo.delete("non-existent-id")
        assert result is False

    def test_list_entities(self):
        """Test listing entities from the repository."""
        repo = InMemoryRepository(User)

        # Create some test users
        user1 = User(id=str(uuid.uuid4()), username="user1")
        user2 = User(id=str(uuid.uuid4()), username="user2")
        user3 = User(id=str(uuid.uuid4()), username="user3")

        repo.create(user1)
        repo.create(user2)
        repo.create(user3)

        # List all entities
        all_users = repo.list()
        assert len(all_users) == 3

        # Verify we get copies, not the originals
        for user in all_users:
            assert user is not repo.data[user.id]

        # Test filtering
        filtered = repo.list({"username": "user2"})
        assert len(filtered) == 1
        assert filtered[0].username == "user2"

        # Test filtering with no matches
        filtered = repo.list({"username": "non-existent"})
        assert len(filtered) == 0

    def test_updated_at_field(self):
        """Test that updated_at field is updated when an entity is updated."""
        repo = InMemoryRepository(Game)
        game_id = str(uuid.uuid4())
        game = Game(id=game_id, type=GameType.CASH, status=GameStatus.WAITING)

        # Create the entity
        repo.create(game)
        original_updated_at = repo.get(game_id).updated_at

        # Wait a bit to ensure time difference
        time.sleep(0.001)

        # Update the entity
        updated_game = repo.get(game_id)
        updated_game.name = "Updated Game"
        repo.update(updated_game)

        # Verify updated_at was updated
        new_updated_at = repo.get(game_id).updated_at
        assert new_updated_at > original_updated_at

    def test_thread_safety(self):
        """Test thread safety of the repository operations."""
        repo = InMemoryRepository(Game)
        num_threads = 10
        operations_per_thread = 100

        # Function to perform concurrent operations
        def concurrent_operations(thread_id):
            results = []
            for i in range(operations_per_thread):
                # Create a game
                game_id = f"{thread_id}-{i}"
                game = Game(id=game_id, type=GameType.CASH, status=GameStatus.WAITING)
                repo.create(game)

                # Get the game
                retrieved = repo.get(game_id)
                assert retrieved is not None
                assert retrieved.id == game_id

                # Update the game
                retrieved.name = f"Updated {thread_id}-{i}"
                repo.update(retrieved)

                # Delete half of the games
                if i % 2 == 0:
                    repo.delete(game_id)
                else:
                    results.append(game_id)

            return results

        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(concurrent_operations, i) for i in range(num_threads)
            ]
            remaining_games = []
            for future in futures:
                remaining_games.extend(future.result())

        # Verify the final state
        all_games = repo.list()
        assert len(all_games) == len(remaining_games)
        for game_id in remaining_games:
            game = repo.get(game_id)
            assert game is not None
            assert game.name == f"Updated {game_id}"
