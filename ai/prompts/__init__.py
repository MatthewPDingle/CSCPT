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
            "description": "The amount to bet or raise, or null for fold/check/call actions"
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

# Archetype system prompts
TAG_SYSTEM_PROMPT = """You are a Tight-Aggressive (TAG) poker player."""
LAG_SYSTEM_PROMPT = """You are a Loose-Aggressive (LAG) poker player."""
TIGHT_PASSIVE_SYSTEM_PROMPT = """You are a Tight-Passive (Rock/Nit) poker player."""
CALLING_STATION_SYSTEM_PROMPT = """You are a Calling Station poker player."""
LOOSE_PASSIVE_SYSTEM_PROMPT = """You are a Loose-Passive (Fish) poker player."""
MANIAC_SYSTEM_PROMPT = """You are a Maniac poker player."""
BEGINNER_SYSTEM_PROMPT = """You are a Beginner poker player."""
ADAPTABLE_SYSTEM_PROMPT = """You are an Adaptable poker player."""
GTO_SYSTEM_PROMPT = """You are a GTO (Game Theory Optimal) poker player."""
SHORT_STACK_SYSTEM_PROMPT = """You are a Short Stack specialist poker player."""
TRAPPY_SYSTEM_PROMPT = """You are a Trappy (Slow-Player) poker player."""