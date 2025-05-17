# mypy: ignore-errors
"""
Unit tests for the repository persistence layer.
"""

import os
import json
import pytest
import shutil
import tempfile
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

from app.models.domain_models import User, Game, GameType, GameStatus
from app.repositories.in_memory import InMemoryRepository, GameRepository
from app.repositories.persistence import RepositoryPersistence, PersistenceScheduler


class TestRepositoryPersistence:
    """Tests for the RepositoryPersistence class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test data files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up
        shutil.rmtree(temp_dir)

    def test_save_and_load_repository(self, temp_dir):
        """Test saving a repository to disk and loading it back."""
        # Create a repository with some data
        repo = InMemoryRepository(User)
        user1 = User(id=str(uuid.uuid4()), username="user1")
        user2 = User(id=str(uuid.uuid4()), username="user2")
        repo.create(user1)
        repo.create(user2)

        # Create a persistence instance
        persistence = RepositoryPersistence(data_dir=temp_dir)

        # Save the repository
        result = persistence.save_repository(repo)
        assert result is True

        # Verify the file was created
        file_path = Path(temp_dir) / "inmemoryrepository.json"
        assert file_path.exists()

        # Load the data into a new repository
        new_repo = InMemoryRepository(User)
        result = persistence.load_repository(new_repo)
        assert result is True

        # Verify the data was loaded correctly
        assert len(new_repo.data) == 2
        assert user1.id in new_repo.data
        assert user2.id in new_repo.data
        assert new_repo.data[user1.id].username == "user1"
        assert new_repo.data[user2.id].username == "user2"

    def test_load_nonexistent_file(self, temp_dir):
        """Test loading from a non-existent file."""
        repo = InMemoryRepository(User)
        persistence = RepositoryPersistence(data_dir=temp_dir)

        # Attempt to load a non-existent file
        result = persistence.load_repository(repo)
        assert result is False
        assert len(repo.data) == 0

    def test_save_and_load_complex_model(self, temp_dir):
        """Test saving and loading a more complex model."""
        # Create a game repository with complex data
        repo = GameRepository()
        game_id = str(uuid.uuid4())
        game = Game(
            id=game_id,
            type=GameType.CASH,
            status=GameStatus.WAITING,
            name="Test Game",
            players=[],
        )
        repo.create(game)

        # Create a persistence instance
        persistence = RepositoryPersistence(data_dir=temp_dir)

        # Save the repository
        result = persistence.save_repository(repo)
        assert result is True

        # Load the data into a new repository
        new_repo = GameRepository()
        result = persistence.load_repository(new_repo)
        assert result is True

        # Verify the data was loaded correctly
        assert len(new_repo.data) == 1
        assert game_id in new_repo.data
        loaded_game = new_repo.data[game_id]
        assert loaded_game.type == GameType.CASH
        assert loaded_game.status == GameStatus.WAITING
        assert loaded_game.name == "Test Game"

    def test_file_corruption_recovery(self, temp_dir):
        """Test recovery from a corrupted data file."""
        # Create a repository with some data
        repo = InMemoryRepository(User)
        user = User(id=str(uuid.uuid4()), username="user")
        repo.create(user)

        # Create a persistence instance
        persistence = RepositoryPersistence(data_dir=temp_dir)

        # Save the repository
        persistence.save_repository(repo)

        # Corrupt the file
        file_path = Path(temp_dir) / "inmemoryrepository.json"
        with open(file_path, "w") as f:
            f.write("this is not valid JSON")

        # Attempt to load the corrupted file
        new_repo = InMemoryRepository(User)
        result = persistence.load_repository(new_repo)
        assert result is False
        assert len(new_repo.data) == 0


class TestPersistenceScheduler:
    """Tests for the PersistenceScheduler class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test data files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up
        shutil.rmtree(temp_dir)

    def test_scheduler_startup_shutdown(self, temp_dir):
        """Test starting and stopping the persistence scheduler."""
        persistence = RepositoryPersistence(data_dir=temp_dir)
        scheduler = PersistenceScheduler(
            persistence=persistence,
            interval_seconds=0.1,  # Short interval for testing
            repositories=[GameRepository],
        )

        # Start the scheduler
        scheduler.start()
        assert scheduler.running is True
        assert scheduler.thread is not None
        assert scheduler.thread.is_alive()

        # Stop the scheduler
        scheduler.stop()
        assert scheduler.running is False
        assert not scheduler.thread.is_alive()

    def test_scheduled_saving(self, temp_dir):
        """Test that the scheduler periodically saves data."""
        # Create a game repository with data
        repo = GameRepository()
        game_id = str(uuid.uuid4())
        game = Game(
            id=game_id, type=GameType.CASH, status=GameStatus.WAITING, name="Test Game"
        )
        repo.create(game)

        # Override the repository factory for testing
        from app.repositories.in_memory import RepositoryFactory

        factory_instance = RepositoryFactory.get_instance()
        factory_instance._repositories = {"GameRepository": repo}

        # Create persistence and scheduler
        persistence = RepositoryPersistence(data_dir=temp_dir)
        scheduler = PersistenceScheduler(
            persistence=persistence,
            interval_seconds=0.1,  # Short interval for testing
            repositories=[GameRepository],
        )

        # Start the scheduler
        scheduler.start()

        # Wait for at least one save cycle
        time.sleep(0.2)

        # Verify the file was created
        file_path = Path(temp_dir) / "gamerepository.json"
        assert file_path.exists()

        # Stop the scheduler
        scheduler.stop()

        # Update the game and manually trigger a save
        game = repo.get(game_id)
        game.name = "Updated Game"
        repo.update(game)
        scheduler.save_all_now(pretty=True)

        # Verify the changes were saved
        with open(file_path, "r") as f:
            data = json.load(f)
            entities = data["entities"]
            assert len(entities) == 1
            assert entities[0]["name"] == "Updated Game"

        # Create a new repository and load the data
        new_repo = GameRepository()
        factory_instance._repositories = {"GameRepository": new_repo}
        scheduler.load_all()

        # Verify the data was loaded correctly
        loaded_game = new_repo.get(game_id)
        assert loaded_game is not None
        assert loaded_game.name == "Updated Game"
