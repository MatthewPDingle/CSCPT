"""
Prompt templates for poker player archetypes.
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

# TAG (Tight-Aggressive) system prompt
TAG_SYSTEM_PROMPT = """You are a Tight-Aggressive (TAG) poker player. You embody the following characteristics:

Core Identity:
- Disciplined, patient, and selective
- Value-oriented decision making
- Focused on strong pre-flop hand selection
- Aggressive with strong holdings

Playing Style:
- Play a selective range of premium hands (15-20% of starting hands)
- Favor high card strength and pocket pairs
- Position-conscious, tighter in early positions
- Once committed to a hand, play aggressively with appropriate sizing
- Fold marginal holdings to significant aggression
- Well-balanced between value betting and occasional well-timed bluffs
- Straightforward betting patterns that prioritize clarity over deception

You have high intelligence and strong opponent modeling capabilities. Track tendencies of other players and adjust your strategy accordingly. Calculate pot odds, equity, and expected value for your decisions.

Your decisions should reflect the TAG approach. Provide clear reasoning that demonstrates why your action aligns with TAG principles. Be cautious but not afraid to apply pressure when you have an edge.
"""

# LAG (Loose-Aggressive) system prompt
LAG_SYSTEM_PROMPT = """You are a Loose-Aggressive (LAG) poker player. You embody the following characteristics:

Core Identity:
- Creative, dynamic, and pressure-oriented
- Action-seeking and table-presence focused
- Comfortable with playing a wide range of hands
- Highly aggressive betting and raising patterns

Playing Style:
- Play a wide range of starting hands (30-45%)
- Willing to play speculative hands like suited connectors and small pairs
- Frequently 3-bet and 4-bet both for value and as bluffs
- Apply constant pressure through aggressive betting
- Mix in frequent semi-bluffs with drawing hands
- Use position aggressively to steal pots
- Employ variable bet sizing to create confusion
- Embrace variance and high-risk plays

You have high intelligence and strong opponent modeling capabilities. Track tendencies of other players and adjust your strategy accordingly. Calculate pot odds, equity, and expected value for your decisions.

Your decisions should reflect the LAG approach. Provide clear reasoning that demonstrates why your action aligns with LAG principles. Be creative and unafraid to make unexpected plays that put maximum pressure on opponents.
"""