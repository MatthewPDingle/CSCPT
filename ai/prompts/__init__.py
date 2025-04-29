"""
Prompts module for poker agents.
"""

# JSON Schema for poker actions
POKER_ACTION_SCHEMA = {
    "type": "object",
    "required": ["thinking", "action", "amount", "reasoning"],
    "properties": {
        "thinking": {
            "type": "string",
            "description": "Your internal thought process analyzing the situation"
        },
        "action": {
            "type": "string",
            "enum": ["fold", "check", "call", "bet", "raise", "all-in"],
            "description": "The poker action to take"
        },
        "amount": {
            "type": ["number", "null"],
            "description": "The total amount you are committing with this action, including any chips already bet this round: for calls, the amount needed to call; for raises, the total bet-to amount; for all-in, your entire stack; null for fold or check actions"
        },
        "reasoning": {
            "type": "object",
            "required": ["hand_assessment", "positional_considerations", "opponent_reads", "archetype_alignment"],
            "properties": {
                "hand_assessment": {
                    "type": "string",
                    "description": "Assessment of current hand strength and potential"
                },
                "positional_considerations": {
                    "type": "string",
                    "description": "How position influenced this decision"
                },
                "opponent_reads": {
                    "type": "string",
                    "description": "What you've observed about opponents' tendencies"
                },
                "archetype_alignment": {
                    "type": "string",
                    "description": "How this decision aligns with your player archetype"
                }
            }
        },
        "calculations": {
            "type": "object",
            "properties": {
                "pot_odds": {
                    "type": "string",
                    "description": "Calculated pot odds if relevant"
                },
                "estimated_equity": {
                    "type": "string",
                    "description": "Estimated equity against opponent ranges"
                }
            }
        }
    }
}

# Archetype system prompts (import full prompts from agent_prompts)
from .agent_prompts import (
    TAG_SYSTEM_PROMPT,
    LAG_SYSTEM_PROMPT,
    TIGHT_PASSIVE_SYSTEM_PROMPT,
    CALLING_STATION_SYSTEM_PROMPT,
    LOOSE_PASSIVE_SYSTEM_PROMPT,
    MANIAC_SYSTEM_PROMPT,
    BEGINNER_SYSTEM_PROMPT,
    ADAPTABLE_SYSTEM_PROMPT,
    GTO_SYSTEM_PROMPT,
    SHORT_STACK_SYSTEM_PROMPT,
    TRAPPY_SYSTEM_PROMPT,
    POKER_ACTION_SCHEMA  # ensure schema is available
)