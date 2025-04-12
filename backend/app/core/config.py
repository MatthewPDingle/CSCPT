"""
Configuration module for application-wide settings and flags.
This module should be importable by any other module to avoid circular imports.
"""
import os

# Flag for memory system availability - will be set in main.py
# Setting to True by default, main.py will override if imports fail
MEMORY_SYSTEM_AVAILABLE = True

# Add any other global configuration variables here
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
DATA_DIR = os.environ.get("DATA_DIR", "./data")