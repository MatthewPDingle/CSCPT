"""
Configuration module for application-wide settings and flags.
This module should be importable by any other module to avoid circular imports.
"""
import os

# Flag for memory system availability - will be set in main.py
MEMORY_SYSTEM_AVAILABLE = False

# Add any other global configuration variables here
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
DATA_DIR = os.environ.get("DATA_DIR", "./data")