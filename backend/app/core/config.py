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

# Animation timing configuration (in seconds)
# These should match the frontend animation durations
ANIMATION_TIMEOUTS = {
    "round_bets_finalized": 2.0,    # 0.5s chip movement + 0.5s pot flash + buffer
    "street_dealt_flop": 2.5,       # 3 cards staggered + 1s pause + buffer
    "street_dealt_turn": 2.0,       # 1 card + 1s pause + buffer  
    "street_dealt_river": 2.0,      # 1 card + 1s pause + buffer
    "street_dealt": 2.0,            # Generic street dealing
    "showdown_hands_revealed": 1.5, # Card reveal + pause
    "pot_winners_determined": 1.5,  # Pot clearing + chip animation
    "chips_distributed": 1.0,       # Chip count updates
    "hand_visually_concluded": 1.5, # Winner pulse + pause
}

# Fallback sleep durations if animation acknowledgment times out
ANIMATION_FALLBACK_DELAYS = {
    "round_bets_finalized": 1.0,    # 0.5s + 0.5s
    "street_dealt_flop": 1.5,       # Cards + pause
    "street_dealt_turn": 1.2,       # Card + pause
    "street_dealt_river": 1.2,      # Card + pause
    "street_dealt": 1.2,            # Generic
    "showdown_hands_revealed": 1.0,
    "pot_winners_determined": 1.0,
    "chips_distributed": 0.5,
    "hand_visually_concluded": 1.0,
}