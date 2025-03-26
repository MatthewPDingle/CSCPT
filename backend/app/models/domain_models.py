"""
Domain models for the poker application.
These models represent the core business entities and are used throughout the application.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Set, Union

from pydantic import BaseModel, Field


class GameStatus(str, Enum):
    """Status of a game."""
    WAITING = "waiting"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class BettingRound(str, Enum):
    """Poker betting rounds."""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


class GameType(str, Enum):
    """Type of poker game."""
    CASH = "cash"
    TOURNAMENT = "tournament"


class PlayerAction(str, Enum):
    """Possible player actions in poker."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


class PlayerStatus(str, Enum):
    """Status of a player in a game."""
    ACTIVE = "active"
    FOLDED = "folded"
    ALL_IN = "all_in"
    OUT = "out"
    WAITING = "waiting"


class ArchetypeEnum(str, Enum):
    """AI player archetypes."""
    TAG = "TAG"
    LAG = "LAG"
    TIGHT_PASSIVE = "TightPassive"
    CALLING_STATION = "CallingStation"
    MANIAC = "Maniac"
    BEGINNER = "Beginner"
    UNPREDICTABLE = "Unpredictable"


class TournamentStage(str, Enum):
    """Tournament stages."""
    BEGINNING = "Beginning"
    MID = "Mid"
    MONEY_BUBBLE = "Money Bubble"
    POST_BUBBLE = "Post Bubble"
    FINAL_TABLE = "Final Table"


class TournamentTier(str, Enum):
    """Tournament tiers."""
    LOCAL = "Local"
    REGIONAL = "Regional"
    NATIONAL = "National"
    INTERNATIONAL = "International"


class User(BaseModel):
    """User entity representing a human player."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    preferences: Dict[str, Union[str, int, bool]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Player(BaseModel):
    """Player entity within a game."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    is_human: bool = False
    user_id: Optional[str] = None  # Reference to User if human player
    archetype: Optional[ArchetypeEnum] = None  # AI player type
    position: int  # Seat position at table
    chips: int = 0
    bet: int = 0
    cards: List[str] = Field(default_factory=list)  # ["Ah", "Kd"]
    status: PlayerStatus = PlayerStatus.WAITING
    has_acted: bool = False
    is_dealer: bool = False
    is_small_blind: bool = False
    is_big_blind: bool = False


class ActionHistory(BaseModel):
    """Record of a player action."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    hand_id: str
    player_id: str
    action: PlayerAction
    amount: Optional[int] = None
    round: BettingRound
    timestamp: datetime = Field(default_factory=datetime.now)


class Hand(BaseModel):
    """A single hand within a game."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    hand_number: int
    community_cards: List[str] = Field(default_factory=list)
    main_pot: int = 0
    side_pots: List[Dict[str, Union[int, Set[str]]]] = Field(default_factory=list)
    current_round: BettingRound = BettingRound.PREFLOP
    current_player_id: Optional[str] = None
    dealer_position: int = 0
    small_blind: int
    big_blind: int
    ante: int = 0
    active_player_ids: List[str] = Field(default_factory=list)
    folded_player_ids: List[str] = Field(default_factory=list)
    all_in_player_ids: List[str] = Field(default_factory=list)
    winners: List[Dict[str, Union[str, int, List[str]]]] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    actions: List[ActionHistory] = Field(default_factory=list)
    current_bet: int = 0


class BlindLevel(BaseModel):
    """Represents a single blind level in a tournament."""
    level: int
    small_blind: int
    big_blind: int
    ante: int = 0
    duration_minutes: int = 15

class TournamentInfo(BaseModel):
    """Information specific to tournament games."""
    tier: TournamentTier
    stage: TournamentStage
    payout_structure: str = "Standard"
    buy_in_amount: int
    level_duration: int  # in minutes
    starting_chips: int
    total_players: int
    starting_big_blind: int
    starting_small_blind: int
    ante_enabled: bool = False
    ante_start_level: int = 3
    rebuy_option: bool = False
    rebuy_level_cutoff: int = 5
    current_level: int = 1
    players_remaining: int
    archetype_distribution: Dict[str, int] = Field(default_factory=dict)
    blind_structure: List[BlindLevel] = Field(default_factory=list)
    current_small_blind: int = 0
    current_big_blind: int = 0
    current_ante: int = 0
    time_remaining_in_level: int = 0  # in seconds


class CashGameInfo(BaseModel):
    """Information specific to cash games."""
    buy_in: int
    min_bet: int
    max_bet: Optional[int] = None  # None for no-limit
    ante: int = 0
    straddled: bool = False
    straddle_amount: int = 0
    table_size: int


class Game(BaseModel):
    """Main game entity that holds the complete state of a poker game."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: GameType
    status: GameStatus = GameStatus.WAITING
    name: Optional[str] = None
    players: List[Player] = Field(default_factory=list)
    current_hand: Optional[Hand] = None
    hand_history: List[Hand] = Field(default_factory=list)
    # Game type specific info
    tournament_info: Optional[TournamentInfo] = None
    cash_game_info: Optional[CashGameInfo] = None
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None