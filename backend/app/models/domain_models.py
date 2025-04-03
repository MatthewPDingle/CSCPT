"""
Domain models for the poker application.
These models represent the core business entities and are used throughout the application.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Set, Union, Any

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


class BettingStructure(str, Enum):
    """Betting structure for cash games."""
    NO_LIMIT = "no_limit"
    POT_LIMIT = "pot_limit"
    FIXED_LIMIT = "fixed_limit"


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
    buy_in: int  # Default buy-in amount
    min_buy_in: int  # Minimum buy-in (typically 40-100 big blinds)
    max_buy_in: int  # Maximum buy-in (typically 100-250 big blinds)
    min_bet: int  # Small blind size
    small_blind: int = 0  # Small blind size (same as min_bet, kept for clarity)
    big_blind: int = 0  # Big blind size
    betting_structure: BettingStructure = BettingStructure.NO_LIMIT
    max_bet: Optional[int] = None  # None for no-limit, set for limit games
    ante: int = 0  # Ante amount if used
    straddled: bool = False  # Whether a straddle is in play
    straddle_amount: int = 0  # Amount of the straddle if enabled
    table_size: int  # Maximum number of players at the table
    rake_percentage: float = 0.05  # Typical 5% rake
    rake_cap: int = 5  # Maximum rake amount in big blinds


class HandMetrics(BaseModel):
    """Analytics metrics for a hand."""
    preflop_raise_count: int = 0
    preflop_call_count: int = 0
    flop_cbet_attempted: bool = False
    flop_cbet_successful: bool = False
    showdown_reached: bool = False
    all_in_confrontation: bool = False
    players_seeing_flop: int = 0
    aggression_factor: float = 0.0  # (bets+raises)/calls
    largest_pot_in_game_so_far: bool = False


class ActionDetail(BaseModel):
    """Detailed record of a player action for hand history."""
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    action_type: PlayerAction
    amount: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    position_relative_to_dealer: int
    position_in_action_sequence: int
    stack_before: int
    stack_after: int
    pot_before: int = 0
    pot_after: int = 0
    bet_facing: int = 0
    all_in: bool = False


class PotResult(BaseModel):
    """Result of a pot at showdown."""
    pot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pot_name: str  # "Main Pot", "Side Pot 1", etc.
    amount: int
    eligible_players: List[str] = Field(default_factory=list)
    winners: List[str] = Field(default_factory=list)
    winning_hand_type: Optional[str] = None
    winning_hand_cards: List[str] = Field(default_factory=list)


class PlayerHandSnapshot(BaseModel):
    """Player state at the beginning of a hand."""
    player_id: str
    position: int
    name: str
    is_human: bool
    archetype: Optional[ArchetypeEnum] = None
    stack_start: int
    stack_end: int = 0
    hole_cards: List[str] = Field(default_factory=list)
    is_dealer: bool = False
    is_small_blind: bool = False
    is_big_blind: bool = False
    final_hand_rank: Optional[str] = None
    final_hand_cards: List[str] = Field(default_factory=list)
    vpip: bool = False  # Voluntarily put money in pot
    pfr: bool = False   # Pre-flop raise
    won_amount: int = 0
    showed_cards: bool = False


class HandHistory(BaseModel):
    """Complete record of a single hand played."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    hand_number: int
    timestamp_start: datetime = Field(default_factory=datetime.now)
    timestamp_end: Optional[datetime] = None
    dealer_position: int
    small_blind: int
    big_blind: int
    ante: int = 0
    table_size: int
    tournament_level: Optional[int] = None
    
    # Card information
    community_cards: List[str] = Field(default_factory=list)
    
    # Starting state
    players: List[PlayerHandSnapshot] = Field(default_factory=list)
    
    # Actions during the hand
    betting_rounds: Dict[str, List[ActionDetail]] = Field(default_factory=dict)
    
    # Results
    pot_results: List[PotResult] = Field(default_factory=list)
    total_pot: int = 0
    
    # Metrics for analytics
    metrics: HandMetrics = Field(default_factory=HandMetrics)


class PlayerStats(BaseModel):
    """Aggregated player statistics."""
    player_id: str
    hands_played: int = 0
    vpip: float = 0.0  # Voluntary Put $ In Pot %
    pfr: float = 0.0   # Pre-Flop Raise %
    af: float = 0.0    # Aggression Factor
    wtsd: float = 0.0  # Went To Showdown %
    won_at_showdown: float = 0.0  # W$SD - Won $ At Showdown %
    wapf: float = 0.0  # Won After Pre-Flop %
    cbet_attempt: float = 0.0  # Continuation Bet Attempt %
    cbet_success: float = 0.0  # Continuation Bet Success %
    three_bet: float = 0.0     # 3-Bet %
    fold_to_three_bet: float = 0.0  # Fold to 3-Bet %
    avg_win: float = 0.0     # Average winning amount
    avg_loss: float = 0.0    # Average losing amount
    biggest_win: int = 0     # Biggest pot won
    biggest_loss: int = 0    # Biggest pot lost
    bb_per_hand: float = 0.0  # Big blinds won/lost per hand


class Game(BaseModel):
    """Main game entity that holds the complete state of a poker game."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: GameType
    status: GameStatus = GameStatus.WAITING
    name: Optional[str] = None
    players: List[Player] = Field(default_factory=list)
    current_hand: Optional[Hand] = None
    hand_history: List[Hand] = Field(default_factory=list)
    hand_history_ids: List[str] = Field(default_factory=list)  # References to detailed hand histories
    # Game type specific info
    tournament_info: Optional[TournamentInfo] = None
    cash_game_info: Optional[CashGameInfo] = None
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None