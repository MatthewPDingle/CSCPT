"""
Prompts module for poker agents.
"""

from .agent_prompts import *

__all__ = [
    'POKER_ACTION_SCHEMA',
    # Archetypes
    'TAG_SYSTEM_PROMPT',
    'LAG_SYSTEM_PROMPT',
    'TIGHT_PASSIVE_SYSTEM_PROMPT',
    'CALLING_STATION_SYSTEM_PROMPT',
    'LOOSE_PASSIVE_SYSTEM_PROMPT',
    'MANIAC_SYSTEM_PROMPT',
    'BEGINNER_SYSTEM_PROMPT',
    'ADAPTABLE_SYSTEM_PROMPT',
    'GTO_SYSTEM_PROMPT',
    'SHORT_STACK_SYSTEM_PROMPT',
    'TRAPPY_SYSTEM_PROMPT'
]
