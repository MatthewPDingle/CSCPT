"""
AI integration package for Chip Swinger Championship Poker Trainer.

This package provides abstractions for LLM providers, AI poker agents, and coaching.
"""

from .config import AIConfig
from .llm_service import LLMService

__all__ = ['AIConfig', 'LLMService']