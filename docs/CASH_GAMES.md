# Cash Game Implementation

This document details the implementation of cash game mechanics in the Chip Swinger Championship Poker Trainer application.

## Overview

Cash games (also known as ring games) differ from tournaments in several key ways:
- Players can join and leave at any time
- Blinds remain constant
- Players can rebuy or top up their chip stacks
- The house typically takes a rake (percentage of each pot)

Our implementation provides a fully-featured cash game experience with configurable parameters.

## Key Components

### Domain Models

The following domain models were enhanced or created to support cash games:

1. **BettingStructure Enum**
   ```python
   class BettingStructure(str, Enum):
       """Betting structure for cash games."""
       NO_LIMIT = "no_limit"
       POT_LIMIT = "pot_limit"
       FIXED_LIMIT = "fixed_limit"
   ```

2. **CashGameInfo Model**
   ```python
   class CashGameInfo(BaseModel):
       """Information specific to cash games."""
       buy_in: int  # Default buy-in amount
       min_buy_in: int  # Minimum buy-in (typically 40-100 big blinds)
       max_buy_in: int  # Maximum buy-in (typically 100-250 big blinds)
       min_bet: int  # Small blind size
       small_blind: int = 0  # Small blind size
       big_blind: int = 0  # Big blind size
       betting_structure: BettingStructure = BettingStructure.NO_LIMIT
       max_bet: Optional[int] = None  # None for no-limit, set for limit games
       ante: int = 0  # Ante amount if used
       straddled: bool = False  # Whether a straddle is in play
       straddle_amount: int = 0  # Amount of the straddle if enabled
       table_size: int  # Maximum number of players at the table
       rake_percentage: float = 0.05  # Typical 5% rake
       rake_cap: int = 5  # Maximum rake amount in big blinds
   ```

### Core Game Logic

The `PokerGame` class was enhanced with the following cash game features:

1. **Game Type Identification**
   ```python
   def __init__(self, small_blind: int, big_blind: int, ante: int = 0, 
                game_id: str = None, hand_history_recorder=None, 
                betting_structure: str = "no_limit",
                rake_percentage: float = 0.05, rake_cap: int = 5,
                game_type: str = None):
       # Configuration for cash game vs. tournament
       self.game_type = game_type  # "cash" or "tournament"
   ```

2. **Player Management**
   ```python
   def add_player_mid_game(self, player_id: str, name: str, chips: int, position: int = None) -> Player:
       """Add a player to an ongoing cash game."""
       # Implementation details
       
   def remove_player(self, player_id: str) -> int:
       """Remove a player from the game (cash out)."""
       # Implementation details
   ```

3. **Rake Calculation**
   ```python
   def calculate_rake(self, pot_amount: int) -> int:
       """Calculate rake based on pot size and configured rake rules."""
       # No rake on tiny pots (e.g., less than 10 BB)
       if pot_amount < self.big_blind * 10:
           return 0
       
       # Calculate rake
       rake = int(pot_amount * self.rake_percentage)
       
       # Cap the rake
       max_rake = self.big_blind * self.rake_cap
       rake = min(rake, max_rake)
       
       return rake
       
   def collect_rake(self, pot_amount: int) -> Tuple[int, int]:
       """Calculate and remove rake from a pot."""
       # Implementation details
   ```

4. **Betting Structure Validation**
   ```python
   def validate_bet_for_betting_structure(self, action: PlayerAction, amount: int, player: Player) -> bool:
       """Validate a bet or raise based on the betting structure."""
       # No-Limit, Pot-Limit, and Fixed-Limit implementation details
   ```

### Game Service Layer

The `GameService` was enhanced with the following cash game operations:

1. **Cash Game Creation**
   ```python
   def create_cash_game(self, name: Optional[str] = None, 
                       min_buy_in_chips: int = 80, max_buy_in_chips: int = 200,
                       small_blind: int = 1, big_blind: int = 2,
                       ante: int = 0, table_size: int = 9,
                       betting_structure: str = "no_limit",
                       rake_percentage: float = 0.05, rake_cap: int = 5) -> Game:
       """Create a new cash game with specific parameters."""
       # Implementation details
   ```

   > **Important Note on Buy-In Values**: 
   > - The `/api/cash_game.py` endpoints accept `min_buy_in` and `max_buy_in` as multiples of big blinds
   > - The `/api/setup.py` endpoints accept `min_buy_in` and `max_buy_in` as chip amounts directly
   > - Internally, `GameService.create_cash_game` now expects chip amounts directly via `min_buy_in_chips` and `max_buy_in_chips`

2. **Player Management**
   ```python
   def add_player_to_cash_game(self, game_id: str, name: str, 
                             buy_in: int, is_human: bool = False, 
                             user_id: Optional[str] = None, 
                             archetype: Optional[str] = None,
                             position: Optional[int] = None) -> Tuple[Game, Player]:
       """Add a player to a cash game with specific buy-in amount."""
       # Implementation details
       
   def rebuy_player(self, game_id: str, player_id: str, amount: int) -> Player:
       """Add chips to a player in a cash game (rebuy)."""
       # Implementation details
       
   def top_up_player(self, game_id: str, player_id: str) -> Tuple[Player, int]:
       """Top up a player's chips to the maximum buy-in."""
       # Implementation details
       
   def cash_out_player(self, game_id: str, player_id: str) -> int:
       """Remove a player from a cash game and return their chip count."""
       # Implementation details
   ```

### API Layer

We created a dedicated API router for cash game operations:

```python
@router.post("/", response_model=GameResponse)
async def create_cash_game(game_request: CashGameRequest):
    """Create a new cash game."""
    # Implementation details

@router.post("/{game_id}/players", response_model=PlayerResponse)
async def add_player_to_cash_game(game_id: str, player_request: PlayerRequest):
    """Add a player to a cash game with specified buy-in."""
    # Implementation details

@router.post("/{game_id}/players/{player_id}/cashout")
async def cash_out_player(game_id: str, player_id: str):
    """Remove a player from a cash game and return their final chip count."""
    # Implementation details

@router.post("/{game_id}/players/{player_id}/rebuy", response_model=PlayerResponse)
async def rebuy_player(game_id: str, player_id: str, rebuy_request: RebuyRequest):
    """Add chips to a player in a cash game (rebuy)."""
    # Implementation details

@router.post("/{game_id}/players/{player_id}/topup", response_model=PlayerResponse)
async def top_up_player(game_id: str, player_id: str):
    """Top up a player's chips to the maximum buy-in amount."""
    # Implementation details
```

## Testing

Extensive tests were created to validate the cash game functionality:

1. **Core Game Mechanics Tests**: Testing the cash game specific additions to the poker game engine
   - Rake calculation and collection
   - Adding/removing players mid-game
   - Betting structure validation

2. **Game Service Tests**: Testing the service layer for cash games
   - Cash game creation with different parameters
   - Player management operations (add, rebuy, top-up, cash-out)

3. **API Tests**: Testing the REST endpoints for cash games
   - Cash game creation endpoint
   - Player management endpoints
   - Error handling and validation

4. **Integration Tests**: Full end-to-end testing of cash game scenarios
   - Complete game flow from creation to player actions
   - Mid-game player changes
   - Multiple rebuy operations

## Future Enhancements

Potential future improvements to the cash game implementation include:

1. **Straddle Support**: Enhanced support for straddle bets
2. **Blind Timer**: Optional timer for increasing blinds in cash games
3. **Time-based Rake**: Support for time-based rake collection (common in casinos)
4. **Run it Twice**: Option to run the board multiple times in all-in situations
5. **Rabbit Hunting**: Option to see what cards would have come after a hand ends early

## Conclusion

The cash game implementation provides a comprehensive and realistic cash game experience with all the essential features expected in a poker training application. The implementation is modular, well-tested, and integrates seamlessly with the existing tournament and AI features of the system.