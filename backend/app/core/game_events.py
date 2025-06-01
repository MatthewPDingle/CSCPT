"""
Event-driven architecture for poker game actions.

This module implements the Command Pattern and Event-Driven Architecture
to separate game logic from UI coordination, eliminating race conditions.
"""
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any, TYPE_CHECKING
from dataclasses import dataclass

# Avoid circular imports by using TYPE_CHECKING
if TYPE_CHECKING:
    from app.core.poker_game import Player, BettingRound, PlayerAction


class GameEventType(Enum):
    """Types of events that can occur during game action processing."""
    PLAYER_ACTION_PROCESSED = auto()
    BETTING_ROUND_COMPLETED = auto()
    STREET_DEALING_REQUIRED = auto()
    SHOWDOWN_TRIGGERED = auto()
    HAND_COMPLETED = auto()
    EARLY_SHOWDOWN_TRIGGERED = auto()


class AnimationSequence(Enum):
    """Animation sequences that need to be coordinated."""
    NONE = auto()
    CHIP_COLLECTION = auto()
    STREET_DEALING = auto()
    SHOWDOWN_REVEAL = auto()
    HAND_CONCLUSION = auto()


@dataclass
class PlayerBet:
    """Represents a player's bet for animation purposes."""
    player_id: str
    amount: int


@dataclass
class StreetCards:
    """Represents cards to be dealt for a street."""
    street_name: str
    cards: List[Any]  # Card objects


@dataclass
class GameActionResult:
    """
    Value object that encapsulates the result of a game action.
    
    This follows the Command Pattern - the action processing returns
    a result object that describes what happened, and the EventOrchestrator
    decides how to notify clients.
    
    Principles applied:
    - Single Responsibility: Only describes what happened
    - Immutability: Read-only after creation
    - Value Object: No identity, only values matter
    """
    success: bool
    events: List[GameEventType]
    
    # Current game state
    current_round: Any  # BettingRound
    current_player_id: Optional[str]
    to_act: Set[str]
    
    # Action details
    action_player_id: str
    action_type: Any  # PlayerAction
    action_amount: Optional[int]
    
    # Animation requirements
    animation_sequence: AnimationSequence
    player_bets: Optional[List[PlayerBet]] = None
    total_pot: Optional[int] = None
    street_cards: Optional[StreetCards] = None
    
    # Showdown data
    is_showdown: bool = False
    is_early_showdown: bool = False
    remaining_streets: List[str] = None
    
    # Turn management
    turn_highlight_removed: bool = False
    next_player_id: Optional[str] = None
    
    # Error information
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate the result object after creation."""
        if not self.success and not self.error_message:
            raise ValueError("Failed actions must have an error message")
        
        if self.remaining_streets is None:
            self.remaining_streets = []


@dataclass
class EventContext:
    """
    Context object for event processing.
    
    Contains all the information needed to coordinate notifications
    and animations in the correct sequence.
    """
    game_id: str
    poker_game: Any  # PokerGame instance
    action_result: GameActionResult
    
    # WebSocket connection manager
    connection_manager: Any = None
    
    # Animation delays and configuration
    animation_config: Dict[str, int] = None
    
    def __post_init__(self):
        """Set default animation configuration."""
        if self.animation_config is None:
            self.animation_config = {
                "chip_animation_duration": 500,
                "pot_flash_duration": 500,
                "card_stagger_delay": 150,
                "post_street_pause": 1000,
                "showdown_pause": 1500
            }