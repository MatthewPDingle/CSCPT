"""
Persistence utilities for in-memory repositories.
These utilities allow saving in-memory data to disk and loading it back.
"""
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Type, Any

from pydantic import BaseModel

from app.models.domain_models import Game, User, ActionHistory, Hand
from app.repositories.in_memory import (
    InMemoryRepository, GameRepository, UserRepository,
    ActionHistoryRepository, HandRepository, RepositoryFactory
)


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class RepositoryPersistence:
    """
    Handles saving and loading repository data to/from disk.
    Uses JSON files for persistence.
    """
    
    def __init__(self, data_dir: str = "./data"):
        """
        Initialize persistence with a data directory.
        
        Args:
            data_dir: Directory where data files will be stored
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        
    def get_file_path(self, repository_name: str) -> Path:
        """
        Get the file path for a repository's data.
        
        Args:
            repository_name: Name of the repository
            
        Returns:
            Path to the repository's data file
        """
        return self.data_dir / f"{repository_name.lower()}.json"
        
    def save_repository(self, repository: InMemoryRepository, pretty: bool = False) -> bool:
        """
        Save a repository's data to disk.
        
        Args:
            repository: The repository to save
            pretty: Whether to format the JSON for readability
            
        Returns:
            True if successful, False otherwise
        """
        repo_name = repository.__class__.__name__
        file_path = self.get_file_path(repo_name)
        
        try:
            with self.lock:
                # Get all data from repository
                with repository.lock:
                    data = {
                        "timestamp": datetime.now().isoformat(),
                        "type": repo_name,
                        "entities": [entity.dict() for entity in repository.data.values()]
                    }
                
                # Write to temporary file first for atomic operation
                temp_path = file_path.with_suffix(".tmp")
                with open(temp_path, "w") as f:
                    if pretty:
                        json.dump(data, f, indent=2, cls=DateTimeEncoder)
                    else:
                        json.dump(data, f, cls=DateTimeEncoder)
                    
                # Rename temp file to actual file (atomic on most filesystems)
                temp_path.replace(file_path)
                return True
                
        except Exception as e:
            print(f"Error saving repository {repo_name}: {e}")
            return False
    
    def load_repository(self, repository: InMemoryRepository) -> bool:
        """
        Load a repository's data from disk.
        
        Args:
            repository: The repository to load data into
            
        Returns:
            True if successful, False otherwise
        """
        repo_name = repository.__class__.__name__
        file_path = self.get_file_path(repo_name)
        
        if not file_path.exists():
            print(f"No data file found for {repo_name}")
            return False
        
        try:
            with self.lock:
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                if "type" not in data or data["type"] != repo_name:
                    print(f"Invalid data file for {repo_name}")
                    return False
                
                # Clear existing data and load from file
                with repository.lock:
                    repository.data.clear()
                    model_class = repository.model_class
                    
                    for entity_dict in data["entities"]:
                        # Convert entity dict back to model
                        entity = model_class.parse_obj(entity_dict)
                        repository.data[entity.id] = entity
                        
                return True
                
        except Exception as e:
            print(f"Error loading repository {repo_name}: {e}")
            return False


class PersistenceScheduler:
    """
    Scheduler that periodically saves repository data.
    Runs on a background thread.
    """
    
    def __init__(
        self,
        persistence: RepositoryPersistence,
        interval_seconds: int = 60,
        repositories: List[Type[InMemoryRepository]] = None
    ):
        """
        Initialize the scheduler.
        
        Args:
            persistence: The persistence utility to use
            interval_seconds: How often to save data (in seconds)
            repositories: Repository types to persist
        """
        self.persistence = persistence
        self.interval = interval_seconds
        self.repositories = repositories or [
            GameRepository,
            UserRepository,
            ActionHistoryRepository,
            HandRepository
        ]
        self.running = False
        self.thread = None
        self.factory = RepositoryFactory.get_instance()
        
    def start(self):
        """Start the scheduler on a background thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop the scheduler and save all data."""
        if not self.running:
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
            
        # Final save before stopping
        self._save_all()
        
    def _run(self):
        """Run the scheduler loop."""
        while self.running:
            # Sleep first to avoid saving empty repositories at startup
            time.sleep(self.interval)
            if not self.running:
                break
                
            self._save_all()
            
    def _save_all(self):
        """Save all repositories."""
        for repo_class in self.repositories:
            repo = self.factory.get_repository(repo_class)
            self.persistence.save_repository(repo)
            
    def save_all_now(self, pretty: bool = False):
        """
        Immediately save all repositories.
        
        Args:
            pretty: Whether to format the JSON for readability
        """
        for repo_class in self.repositories:
            repo = self.factory.get_repository(repo_class)
            self.persistence.save_repository(repo, pretty=pretty)
            
    def load_all(self):
        """Load all repositories from disk."""
        success = True
        for repo_class in self.repositories:
            repo = self.factory.get_repository(repo_class)
            if not self.persistence.load_repository(repo):
                success = False
        return success