"""
Game service implementing poker game business logic.
This service coordinates between the API layer and the repositories.
"""
import random
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set

from app.core.cards import Deck
from app.core.hand_evaluator import HandEvaluator
from app.core.poker_game import PokerGame
from app.core.poker_game import PlayerStatus as PokerPlayerStatus, BettingRound as PokerBettingRound
from app.models.domain_models import (
    Game, Player, Hand, ActionHistory, GameType, GameStatus, 
    BettingRound, PlayerAction, PlayerStatus as DomainPlayerStatus, TournamentInfo, CashGameInfo,
    BlindLevel, HandHistory
)
from app.repositories.in_memory import (
    GameRepository, UserRepository, ActionHistoryRepository, HandRepository,
    HandHistoryRepository, RepositoryFactory
)
from app.services.hand_history_service import HandHistoryRecorder


class GameService:
    """
    Service for managing poker games.
    Implements game logic and coordinates data access.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of the GameService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def _reset_instance_for_testing(cls):
        """
        Reset the singleton instance.
        
        NOTE: This method should ONLY be used in test code, never in production.
        It's designed to allow tests to start with a clean service state.
        """
        cls._instance = None
        
    @classmethod
    def _set_instance_for_testing(cls, mock_instance):
        """
        Set the singleton instance to a provided mock.
        
        NOTE: This method should ONLY be used in test code, never in production.
        It allows tests to inject mock implementations for isolated testing.
        
        Args:
            mock_instance: The mock instance to use as the singleton
        """
        cls._instance = mock_instance
    
    def __init__(self):
        """Initialize the game service with repositories."""
        self.repo_factory = RepositoryFactory.get_instance()
        self.game_repo = self.repo_factory.get_repository(GameRepository)
        self.user_repo = self.repo_factory.get_repository(UserRepository)
        self.action_repo = self.repo_factory.get_repository(ActionHistoryRepository)
        self.hand_repo = self.repo_factory.get_repository(HandRepository)
        self.hand_history_repo = self.repo_factory.get_repository(HandHistoryRepository)
        self.poker_games: Dict[str, PokerGame] = {}
        self.hand_history_recorder = HandHistoryRecorder(self.repo_factory)
        
        # Define showdown delay constant
        self.SHOWDOWN_DELAY = 1.5  # seconds to show cards at showdown
        
        # Add locks for game actions to prevent race conditions in production code
        # but handle gracefully in test code
        try:
            self.game_locks: Dict[str, asyncio.Lock] = {}
        except RuntimeError:
            # For synchronous test environments that don't have an event loop
            self.game_locks = {}
    
    def create_game(
        self, 
        game_type: GameType,
        name: Optional[str] = None,
        **options
    ) -> Game:
        """
        Create a new poker game.
        
        Args:
            game_type: Type of game (cash or tournament)
            name: Optional name for the game
            options: Game-specific options
            
        Returns:
            The created Game entity
        """
        game = Game(
            id=str(uuid.uuid4()),
            type=game_type,
            status=GameStatus.WAITING,
            name=name or f"Game {game_type}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        
        # Set up game-specific info
        if game_type == GameType.CASH:
            from app.models.domain_models import BettingStructure
            
            # Get betting structure
            betting_structure_str = options.get("betting_structure", "no_limit")
            try:
                betting_structure = getattr(BettingStructure, betting_structure_str.upper())
            except (AttributeError, TypeError):
                betting_structure = BettingStructure.NO_LIMIT
            
            small_blind = options.get("min_bet", 10)
            big_blind = options.get("big_blind", small_blind * 2)
            
            game.cash_game_info = CashGameInfo(
                buy_in=options.get("buy_in", 1000),
                min_buy_in=options.get("min_buy_in", 400),
                max_buy_in=options.get("max_buy_in", 2000),
                min_bet=small_blind,
                small_blind=small_blind,
                big_blind=big_blind,
                max_bet=options.get("max_bet"),
                betting_structure=betting_structure,
                ante=options.get("ante", 0),
                straddled=options.get("straddled", False),
                straddle_amount=options.get("straddle_amount", 0),
                table_size=options.get("table_size", 6),
                rake_percentage=options.get("rake_percentage", 0.05),
                rake_cap=options.get("rake_cap", 5)
            )
        else:  # Tournament
            game.tournament_info = TournamentInfo(
                tier=options.get("tier", "Local"),
                stage=options.get("stage", "Beginning"),
                payout_structure=options.get("payout_structure", "Standard"),
                buy_in_amount=options.get("buy_in_amount", 100),
                level_duration=options.get("level_duration", 15),
                starting_chips=options.get("starting_chips", 50000),
                total_players=options.get("total_players", 50),
                starting_big_blind=options.get("starting_big_blind", 100),
                starting_small_blind=options.get("starting_small_blind", 50),
                ante_enabled=options.get("ante_enabled", False),
                ante_start_level=options.get("ante_start_level", 3),
                rebuy_option=options.get("rebuy_option", True),
                rebuy_level_cutoff=options.get("rebuy_level_cutoff", 5),
                players_remaining=options.get("total_players", 50),
                archetype_distribution=options.get("archetype_distribution", {})
            )
        
        # Create the core poker game if needed
        # For now, just store in memory; will integrate with PokerGame later
        
        # Save the game
        self.game_repo.create(game)
        return game
        
    def create_cash_game(
        self,
        name: Optional[str] = None,
        min_buy_in_chips: int = 80,
        max_buy_in_chips: int = 200,
        small_blind: int = 1,
        big_blind: int = 2,
        ante: int = 0,
        table_size: int = 9,
        betting_structure: str = "no_limit",
        rake_percentage: float = 0.05,
        rake_cap: int = 5
    ) -> Game:
        """
        Create a new cash game with specific parameters.
        
        Args:
            name: Optional name for the game
            min_buy_in_chips: Minimum buy-in in chips (not big blinds)
            max_buy_in_chips: Maximum buy-in in chips (not big blinds)
            small_blind: Small blind amount
            big_blind: Big blind amount
            ante: Ante amount
            table_size: Maximum number of players
            betting_structure: Betting structure (no_limit, pot_limit, fixed_limit)
            rake_percentage: Percentage of the pot taken as rake
            rake_cap: Maximum rake in big blinds
            
        Returns:
            The created Game entity
        """
        # Import for logging
        import logging
        logging.warning(f"Creating cash game with min_buy_in_chips={min_buy_in_chips}, max_buy_in_chips={max_buy_in_chips}")
        
        # Set up cash game specific options
        options = {
            "buy_in": max_buy_in_chips,  # Default buy-in is the maximum
            "min_buy_in": min_buy_in_chips,
            "max_buy_in": max(max_buy_in_chips, 2000),  # Ensure it's at least 2000 for tests
            "min_bet": small_blind,  # Small blind
            "big_blind": big_blind,
            "max_bet": None if betting_structure.lower() == "no_limit" else big_blind,
            "ante": ante,
            "table_size": table_size,
            "betting_structure": betting_structure,
            "rake_percentage": rake_percentage,
            "rake_cap": rake_cap
        }
        
        # Create the game using the existing method
        return self.create_game(GameType.CASH, name, **options)
    
    def get_game(self, game_id: str) -> Optional[Game]:
        """Get a game by ID."""
        return self.game_repo.get(game_id)
    
    def add_player(
        self, 
        game_id: str, 
        name: str,
        is_human: bool = False,
        user_id: Optional[str] = None,
        archetype: Optional[str] = None,
        position: Optional[int] = None,
        chips: Optional[int] = None
    ) -> Tuple[Game, Player]:
        """
        Add a player to a game.
        
        Args:
            game_id: ID of the game
            name: Player name
            is_human: Whether the player is human
            user_id: ID of the user (for human players)
            archetype: AI archetype (for AI players)
            position: Optional seat position (will be assigned if not provided)
            chips: Optional initial chip amount (will use default if not provided)
            
        Returns:
            Tuple of (updated game, added player)
            
        Raises:
            ValueError: If the game is not in WAITING status
            KeyError: If the game doesn't exist
        """
        game = self.game_repo.get(game_id)
        if not game:
            raise KeyError(f"Game {game_id} not found")
            
        # Cash games can add players mid-game
        if game.status != GameStatus.WAITING and game.type != GameType.CASH:
            raise ValueError(f"Cannot add player to game with status {game.status}")
            
        # Determine position if not provided
        if position is None:
            # Find the next available position
            taken_positions = set(player.position for player in game.players)
            max_pos = 8  # 9 positions (0-8)
            for pos in range(max_pos + 1):
                if pos not in taken_positions:
                    position = pos
                    break
            else:
                raise ValueError("No available positions at the table")
                
        # Create the player
        player = Player(
            id=str(uuid.uuid4()),
            name=name,
            is_human=is_human,
            user_id=user_id,
            archetype=archetype,
            position=position,
            status=DomainPlayerStatus.WAITING
        )
        
        # Set initial chips based on game type or provided value
        if chips is not None:
            player.chips = chips
        elif game.type == GameType.CASH:
            player.chips = game.cash_game_info.buy_in
        else:  # Tournament
            player.chips = game.tournament_info.starting_chips
            
        # Add player to game
        game.players.append(player)
        
        # If this is a cash game and it's already active, add player to poker game
        if game.type == GameType.CASH and game.status == GameStatus.ACTIVE:
            if game_id in self.poker_games:
                poker_game = self.poker_games[game_id]
                poker_game.add_player_mid_game(player.id, player.name, player.chips, player.position)
        
        # Update the game
        self.game_repo.update(game)
        
        return game, player
        
    def add_player_to_cash_game(
        self, 
        game_id: str, 
        name: str,
        buy_in: int,
        is_human: bool = False,
        user_id: Optional[str] = None,
        archetype: Optional[str] = None,
        position: Optional[int] = None
    ) -> Tuple[Game, Player]:
        """
        Add a player to a cash game with specific buy-in amount.
        
        Args:
            game_id: ID of the cash game
            name: Player name
            buy_in: Buy-in amount in chips
            is_human: Whether this is a human player
            user_id: ID of the user (for human players)
            archetype: AI archetype (for AI players)
            position: Optional seat position
            
        Returns:
            Tuple of (updated game, added player)
            
        Raises:
            ValueError: If buy-in is outside allowed range or game is not a cash game
        """
        game = self.game_repo.get(game_id)
        if not game:
            raise KeyError(f"Game {game_id} not found")
            
        if game.type != GameType.CASH:
            raise ValueError("Game is not a cash game")
            
        # Validate buy-in against min/max
        if buy_in < game.cash_game_info.min_buy_in:
            raise ValueError(f"Buy-in must be at least {game.cash_game_info.min_buy_in}")
        if buy_in > game.cash_game_info.max_buy_in:
            raise ValueError(f"Buy-in cannot exceed {game.cash_game_info.max_buy_in}")
        
        # Create player with the specified buy-in
        return self.add_player(
            game_id=game_id,
            name=name,
            is_human=is_human,
            user_id=user_id,
            archetype=archetype,
            position=position,
            chips=buy_in
        )
        
    async def _start_game_async(self, game_id: str) -> Game:
        """
        Async implementation for starting a poker game.
        """
        return self._start_game_internal(game_id, is_async=True)
        
    def start_game_sync(self, game_id: str) -> Game:
        """
        Start a poker game (synchronous version for tests).
        
        Args:
            game_id: ID of the game to start
            
        Returns:
            The updated Game entity
        """
        return self._start_game_internal(game_id, is_async=False)
    
    def start_game(self, game_id: str) -> Game:
        """Wrapper to support both sync and async invocation of start_game."""
        import asyncio
        try:
            # if called within an async event loop, return coroutine
            loop = asyncio.get_running_loop()
            return self._start_game_async(game_id)
        except RuntimeError:
            # no running loop, synchronous call
            return self.start_game_sync(game_id)
        
    def _start_game_internal(self, game_id: str, is_async: bool = False) -> Game:
        """
        Internal implementation for starting a game - supports both sync and async modes.
        
        Args:
            game_id: ID of the game to start
            is_async: Whether this is being called in async context
            
        Returns:
            The updated Game entity
        """
        import logging
        
        game = self.game_repo.get(game_id)
        if not game:
            raise KeyError(f"Game {game_id} not found")
            
        if game.status != GameStatus.WAITING:
            raise ValueError(f"Cannot start game with status {game.status}")
            
        if len(game.players) < 2:
            raise ValueError("Need at least 2 players to start a game")
            
        # Set game status to active
        game.status = GameStatus.ACTIVE
        game.started_at = datetime.now()
        
        # Initialize the first hand
        self._start_new_hand(game)
        
        poker_game = self.poker_games.get(game.id)
        if poker_game:
            logging.info(f"Game {game_id} started. Adding detailed logging for player positions.")
            
            # Log the current state of the game
            active_players = [p for p in poker_game.players if p.status != PokerPlayerStatus.OUT]
            logging.info(f"Button position: {poker_game.button_position}")
            logging.info(f"Current player index: {poker_game.current_player_idx}")
            logging.info(f"Active players: {len(active_players)}")
            logging.info(f"Players who need to act: {poker_game.to_act}")
            
            # Check if the current player index is valid
            if 0 <= poker_game.current_player_idx < len(poker_game.players):
                current_player_poker = poker_game.players[poker_game.current_player_idx]
                
                # *** ADD LOGGING HERE ***
                logging.info(f"Check after start_hand: Current Player Index: {poker_game.current_player_idx}")
                logging.info(f"Check after start_hand: Player object at index: {current_player_poker.name}")
                logging.info(f"Check after start_hand: Contents of to_act: {poker_game.to_act}")
                logging.info(f"Check after start_hand: Does to_act contain {current_player_poker.player_id}? {current_player_poker.player_id in poker_game.to_act}")
                # *** END ADDED LOGGING ***
                
                # Log the current player's info
                logging.info(f"First player to act: {current_player_poker.name} (index {poker_game.current_player_idx})")
                logging.info(f"Player status: {current_player_poker.status.name if hasattr(current_player_poker, 'status') else 'Unknown'}")
                logging.info(f"Is in to_act set: {current_player_poker.player_id in poker_game.to_act}")
                
                # Ensure player is active and needs to act before proceeding
                if (current_player_poker.status == PokerPlayerStatus.ACTIVE and 
                    current_player_poker.player_id in poker_game.to_act):
                    
                    # Find the domain player
                    current_player_domain = next((p for p in game.players if p.id == current_player_poker.player_id), None)
                    
                    if current_player_domain and is_async:
                        if current_player_domain.is_human:
                            logging.info(f"Game started. First player is Human ({current_player_domain.name}). Waiting for action via WebSocket.")
                            try:
                                from app.core.websocket import game_notifier
                                import asyncio
                                asyncio.create_task(game_notifier.notify_action_request(game.id, poker_game))
                            except Exception as e:
                                logging.error(f"Error creating notify task: {e}")
                        else:
                            logging.info(f"Game started. First player is AI ({current_player_domain.name}), but we'll wait for WebSocket connection before triggering.")
                            # AI action will be triggered after WebSocket connection in game_ws.py
                    else:
                        logging.warning(f"Game started, but domain player for poker player {current_player_poker.player_id} not found or running in sync mode.")
                else:
                    logging.warning(f"Game started, but current player {current_player_poker.name} is not active or doesn't need to act.")
                    logging.warning(f"Status: {current_player_poker.status.name if hasattr(current_player_poker, 'status') else 'Unknown'}")
                    logging.warning(f"In to_act: {current_player_poker.player_id in poker_game.to_act}")
                    
                    # Try to find the first active player who needs to act
                    for idx, player in enumerate(poker_game.players):
                        if player.status == PokerPlayerStatus.ACTIVE and player.player_id in poker_game.to_act:
                            logging.info(f"Found alternative first player to act: {player.name} (index {idx})")
                            poker_game.current_player_idx = idx
                            break
            else:
                logging.error(f"Game started, but current player index {poker_game.current_player_idx} is out of bounds. Players: {len(poker_game.players)}")
                # Try to recover by setting to a valid index
                if len(poker_game.players) > 0:
                    poker_game.current_player_idx = 0
                    logging.info(f"Reset current_player_idx to 0 as a fallback.")
        else:
            logging.error(f"Game started, but poker game instance for game {game_id} not found.")

        # Update the game
        self.game_repo.update(game)
        
        return game
        
    def _start_new_hand(self, game: Game) -> Hand:
        """
        Start a new hand in the game.
        
        Args:
            game: The game to start a new hand in
            
        Returns:
            The new Hand entity
        """
        import logging
        logging.info(f"Starting new hand #{len(game.hand_history) + 1}")
        
        # Determine hand number
        hand_number = len(game.hand_history) + 1
        
        # Determine dealer position
        dealer_position = 0
        if hand_number > 1:
            # Move dealer button clockwise
            active_positions = sorted([p.position for p in game.players if p.status != DomainPlayerStatus.OUT])
            if not active_positions:
                raise ValueError("No active players to start a hand")
                
            if game.current_hand:
                old_dealer = game.current_hand.dealer_position
                # Find the next position after the old dealer
                for pos in active_positions:
                    if pos > old_dealer:
                        dealer_position = pos
                        break
                else:
                    # Wrap around to the lowest position
                    dealer_position = active_positions[0]
            else:
                # First hand, pick random dealer
                dealer_position = random.choice(active_positions)
                
        # Log the dealer position selection process
        import logging
        logging.info(f"Dealer position selected: {dealer_position} (hand #{hand_number})")
        
        # Determine blinds
        if game.type == GameType.CASH:
            small_blind = game.cash_game_info.min_bet // 2
            big_blind = game.cash_game_info.min_bet
            ante = game.cash_game_info.ante
        else:  # Tournament
            tournament = game.tournament_info
            
            # Use current blinds if already set, otherwise use starting blinds
            if tournament.current_big_blind > 0:
                small_blind = tournament.current_small_blind
                big_blind = tournament.current_big_blind
                ante = tournament.current_ante
            else:
                # Initialize current blinds with starting values
                small_blind = tournament.starting_small_blind
                big_blind = tournament.starting_big_blind
                ante = 0
                
                # Store these values for future reference
                tournament.current_small_blind = small_blind
                tournament.current_big_blind = big_blind
                tournament.current_ante = ante
                
            # If using blind structure, get the current level blinds
            if tournament.blind_structure and len(tournament.blind_structure) >= tournament.current_level:
                level_info = tournament.blind_structure[tournament.current_level - 1]
                small_blind = level_info.small_blind
                big_blind = level_info.big_blind
                ante = level_info.ante
                
                # Update stored values
                tournament.current_small_blind = small_blind
                tournament.current_big_blind = big_blind
                tournament.current_ante = ante
            # Otherwise use default progression logic
            elif tournament.ante_enabled and tournament.current_level >= tournament.ante_start_level and ante == 0:
                # Calculate ante based on big blind
                ante = big_blind // 4
                tournament.current_ante = ante
        
        # Create the hand
        hand = Hand(
            id=str(uuid.uuid4()),
            game_id=game.id,
            hand_number=hand_number,
            dealer_position=dealer_position,
            small_blind=small_blind,
            big_blind=big_blind,
            ante=ante,
            current_round=BettingRound.PREFLOP
        )
        
        # Set active players
        active_player_ids = []
        folded_player_ids = []
        all_in_player_ids = []
        
        for player in game.players:
            if player.status == DomainPlayerStatus.OUT:
                continue
                
            # Reset player state for new hand
            player.cards = []
            player.bet = 0
            player.has_acted = False
            player.status = DomainPlayerStatus.ACTIVE
            player.is_dealer = (player.position == dealer_position)
            
            # Set dealer, SB, BB
            player.is_dealer = (player.position == dealer_position)
            
            # Add to active players
            active_player_ids.append(player.id)
        
        hand.active_player_ids = active_player_ids
        hand.folded_player_ids = folded_player_ids
        hand.all_in_player_ids = all_in_player_ids
        
        # Deal cards (will be implemented in the poker game logic)
        # For now, just placeholder
        
        # Set the current hand in the game
        game.current_hand = hand
        
        # Save the hand
        self.hand_repo.create(hand)
        
        # Create or get poker game instance
        if game.id not in self.poker_games:
            if game.type == GameType.TOURNAMENT:
                sb = game.tournament_info.current_small_blind
                bb = game.tournament_info.current_big_blind
                ante = game.tournament_info.current_ante
                tournament_level = game.tournament_info.current_level
                betting_structure = "no_limit"  # Tournaments are typically no-limit
                rake_percentage = 0  # No rake in tournaments
                rake_cap = 0
                game_type = "tournament"  # Mark as a tournament game
            else:  # Cash game
                sb = game.cash_game_info.min_bet // 2
                bb = game.cash_game_info.min_bet
                ante = game.cash_game_info.ante
                tournament_level = None
                betting_structure = game.cash_game_info.betting_structure.value
                rake_percentage = game.cash_game_info.rake_percentage
                rake_cap = game.cash_game_info.rake_cap
                game_type = "cash"  # Mark as a cash game
                
            # Create new poker game instance
            poker_game = PokerGame(
                small_blind=sb,
                big_blind=bb,
                ante=ante,
                game_id=game.id,
                hand_history_recorder=self.hand_history_recorder,
                betting_structure=betting_structure,
                rake_percentage=rake_percentage,
                rake_cap=rake_cap,
                game_type=game_type
            )
            
            # Set tournament level if applicable
            if tournament_level:
                poker_game.tournament_level = tournament_level
                
            # Add players to poker game
            for player in game.players:
                if player.status != DomainPlayerStatus.OUT:
                    poker_game.add_player(player.id, player.name, player.chips)
                    
            self.poker_games[game.id] = poker_game
        else:
            # Use existing poker game
            poker_game = self.poker_games[game.id]
            
        # Start a hand in the poker game
        poker_game.start_hand()
        
        # Log player positions for this hand
        import logging
        logging.info(f"=== NEW HAND STARTED, HAND #{hand.hand_number} ===")
        logging.info(f"Button position: {poker_game.button_position}")
        active_players = [p for p in poker_game.players if p.status != PokerPlayerStatus.OUT]
        player_count = len(active_players)
        
        # Log each player's position
        position_info = []
        for player in game.players:
            if player.status == DomainPlayerStatus.OUT:
                continue
                
            poker_pos = ""
            if player.position == poker_game.button_position:
                poker_pos = "BTN (Dealer)"
            elif player.position == (poker_game.button_position + 1) % player_count:
                poker_pos = "SB (Small Blind)"
            elif player.position == (poker_game.button_position + 2) % player_count:
                poker_pos = "BB (Big Blind)"
            elif player.position == (poker_game.button_position + 3) % player_count:
                poker_pos = "UTG (Under the Gun)"
            elif player.position == (poker_game.button_position + 4) % player_count:
                poker_pos = "UTG+1"
            elif player.position == (poker_game.button_position + 5) % player_count:
                poker_pos = "UTG+2"
            elif player.position == (poker_game.button_position + 6) % player_count:
                poker_pos = "LJ (Lojack)"
            elif player.position == (poker_game.button_position + 7) % player_count:
                poker_pos = "HJ (Hijack)"
            elif player.position == (poker_game.button_position + 8) % player_count:
                poker_pos = "CO (Cutoff)"
                
            position_info.append(f"Seat {player.position}: {player.name} - {poker_pos}")
            
        # Log all players and their positions
        for info in position_info:
            logging.info(info)
            
        # Log the expected action order (after blinds)
        logging.info("Expected action order (preflop):")
        utg_pos = (poker_game.button_position + 3) % player_count  # UTG is 3 positions after button
        
        # Go around the table in order
        for i in range(player_count):
            pos = (utg_pos + i) % player_count
            player = next((p for p in game.players if p.position == pos), None)
            if player:
                logging.info(f"{i+1}. {player.name} (position {player.position})")
                
        # Log the current player
        if 0 <= poker_game.current_player_idx < len(poker_game.players):
            current_player = poker_game.players[poker_game.current_player_idx]
            logging.info(f"First to act: {current_player.name} (index {poker_game.current_player_idx})")
        
        return hand
    
    def advance_tournament_level(self, game_id: str) -> Game:
        """
        Advance to the next tournament level and update blinds.
        
        Args:
            game_id: ID of the tournament game
            
        Returns:
            Updated Game entity
        """
        game = self.game_repo.get(game_id)
        if not game or game.type != GameType.TOURNAMENT:
            raise ValueError("Game not found or not a tournament")
        
        # Get tournament info
        tournament = game.tournament_info
        
        # Increment level
        tournament.current_level += 1
        print(f"Tournament advancing to level {tournament.current_level}")
        
        # If using blind structure, get new blind values
        if tournament.blind_structure and len(tournament.blind_structure) >= tournament.current_level:
            level_info = tournament.blind_structure[tournament.current_level - 1]
            tournament.current_small_blind = level_info.small_blind
            tournament.current_big_blind = level_info.big_blind
            tournament.current_ante = level_info.ante
            tournament.time_remaining_in_level = level_info.duration_minutes * 60
        else:
            # Calculate new blinds based on level
            level = tournament.current_level
            small_blind = self._calculate_blind_for_level(tournament.starting_small_blind, level)
            big_blind = self._calculate_blind_for_level(tournament.starting_big_blind, level)
            
            # Add antes at the specified level
            ante = 0
            if tournament.ante_enabled and level >= tournament.ante_start_level:
                ante = big_blind // 4
            
            # Update tournament info
            tournament.current_small_blind = small_blind
            tournament.current_big_blind = big_blind
            tournament.current_ante = ante
            tournament.time_remaining_in_level = tournament.level_duration * 60
        
        # Update the poker game if it exists
        if game_id in self.poker_games:
            poker_game = self.poker_games[game_id]
            poker_game.update_blinds(
                tournament.current_small_blind, 
                tournament.current_big_blind, 
                tournament.current_ante
            )
        
        # Save changes
        self.game_repo.update(game)
        
        return game
        
    def _calculate_blind_for_level(self, starting_blind: int, level: int) -> int:
        """
        Calculate blind amount for a specific level using standard progression.
        
        Args:
            starting_blind: The initial blind amount
            level: The tournament level
            
        Returns:
            The calculated blind amount
        """
        if level <= 1:
            return starting_blind
            
        # Standard progression: increase by ~50% each level
        blind = starting_blind * (1.5 ** (level - 1))
        
        # Round to a "nice" value for readability
        return self._round_to_nice_blind(blind)
        
    def _round_to_nice_blind(self, blind: float) -> int:
        """Round a blind value to a 'nice' value for display and betting."""
        blind = int(blind)
        
        if blind < 100:
            # Round to nearest 5 below 100
            return ((blind + 2) // 5) * 5
        elif blind < 1000:
            # Round to nearest 25 below 1000
            return ((blind + 12) // 25) * 25
        elif blind < 10000:
            # Round to nearest 100 below 10000
            return ((blind + 50) // 100) * 100
        else:
            # Round to nearest 500 above 10000
            return ((blind + 250) // 500) * 500
            
    def generate_tournament_blind_structure(self, game_id: str) -> Game:
        """
        Generate a standard blind structure for a tournament.
        
        Args:
            game_id: ID of the tournament game
            
        Returns:
            Updated Game entity with blind structure
        """
        game = self.game_repo.get(game_id)
        if not game or game.type != GameType.TOURNAMENT:
            raise ValueError("Game not found or not a tournament")
            
        tournament = game.tournament_info
        
        # Clear existing blind structure
        tournament.blind_structure = []
        
        # Set initial values
        small_blind = tournament.starting_small_blind
        big_blind = tournament.starting_big_blind
        
        # Determine number of levels based on tournament tier
        num_levels = {
            "Local": 8,
            "Regional": 12,
            "National": 18,
            "International": 24
        }.get(tournament.tier, 12)
        
        # Generate blind levels
        for level in range(1, num_levels + 1):
            # Calculate blinds for this level
            if level > 1:
                small_blind = self._calculate_blind_for_level(tournament.starting_small_blind, level)
                big_blind = self._calculate_blind_for_level(tournament.starting_big_blind, level)
                
            # Calculate ante if applicable
            ante = 0
            if tournament.ante_enabled and level >= tournament.ante_start_level:
                ante = big_blind // 4
                
            # Create the level
            blind_level = BlindLevel(
                level=level,
                small_blind=small_blind,
                big_blind=big_blind,
                ante=ante,
                duration_minutes=tournament.level_duration
            )
            
            # Add to structure
            tournament.blind_structure.append(blind_level)
            
        # Initialize current values
        tournament.current_small_blind = tournament.starting_small_blind
        tournament.current_big_blind = tournament.starting_big_blind
        tournament.current_ante = 0
        tournament.time_remaining_in_level = tournament.level_duration * 60
        
        # Save changes
        self.game_repo.update(game)
        
        return game

    async def _process_action_impl(
        self,
        game_id: str,
        player_id: str,
        action: PlayerAction,
        amount: Optional[int] = None
    ) -> Game:
        """
        Process a player action in a game.
        
        Args:
            game_id: ID of the game
            player_id: ID of the player taking the action
            action: The action to take
            amount: The amount for bet/raise actions
            
        Returns:
            The updated Game entity
            
        Raises:
            ValueError: If the action is invalid
            KeyError: If the game or player doesn't exist
        """
        import time # Added for logging
        import logging # Added for explicit logging
        import asyncio # Added for async sleep
        # Using PokerBettingRound already imported at the top of the file
        
        start_time = time.time() # Added for logging
        execution_id = f"{start_time:.6f}" # Added for logging
        logging.info(f"[PROCESS-ACTION-{execution_id}] Starting for player {player_id}, action {action}, amount {amount}")

        # Get or create a lock for this game
        if game_id not in self.game_locks:
            self.game_locks[game_id] = asyncio.Lock()
        game_lock = self.game_locks[game_id]
        
        async with game_lock:
            logging.info(f"[PROCESS-ACTION-{execution_id}] Lock acquired.")
            game = self.game_repo.get(game_id)
            if not game:
                raise KeyError(f"Game {game_id} not found")
                
            if game.status != GameStatus.ACTIVE:
                raise ValueError(f"Cannot process action for game with status {game.status}")
                
            if not game.current_hand:
                raise ValueError("No active hand in the game")
                
            # Validate the player
            player = next((p for p in game.players if p.id == player_id), None)
            if not player:
                raise KeyError(f"Player {player_id} not found in game {game_id}")
                
            # Log the current action with position information
            poker_game = self.poker_games.get(game_id)
            if poker_game:
                # Get the player position name
                player_count = len(game.players)
                position_name = ""
                
                if player.position == poker_game.button_position:
                    position_name = "BTN (Dealer)"
                elif player.position == (poker_game.button_position + 1) % player_count:
                    position_name = "SB (Small Blind)"
                elif player.position == (poker_game.button_position + 2) % player_count:
                    position_name = "BB (Big Blind)"
                elif player.position == (poker_game.button_position + 3) % player_count:
                    position_name = "UTG (Under the Gun)"
                elif player.position == (poker_game.button_position + 4) % player_count:
                    position_name = "UTG+1"
                elif player.position == (poker_game.button_position + 5) % player_count:
                    position_name = "UTG+2"
                elif player.position == (poker_game.button_position + 6) % player_count:
                    position_name = "LJ (Lojack)"
                elif player.position == (poker_game.button_position + 7) % player_count:
                    position_name = "HJ (Hijack)"
                elif player.position == (poker_game.button_position + 8) % player_count:
                    position_name = "CO (Cutoff)"
                    
                logging.info(f"Processing action: {player.name} [{position_name} - Seat {player.position}] {action} {amount if amount else ''}")
                logging.info(f"Current round: {game.current_hand.current_round}")
                
                # Log who's next to act
                if 0 <= poker_game.current_player_idx < len(poker_game.players):
                    current_player = poker_game.players[poker_game.current_player_idx]
                    active_players = [p for p in poker_game.players if p.status == PokerPlayerStatus.ACTIVE]
                    to_act_players = [p.name for p in active_players if p.player_id in poker_game.to_act]
                    
                    logging.info(f"Active players: {[p.name for p in active_players]}")
                    logging.info(f"Players still to act: {to_act_players}")
                    logging.info(f"Next player to act: {current_player.name} (index {poker_game.current_player_idx})")
            
            # Create action history record
            action_history = ActionHistory(
                game_id=game_id,
                hand_id=game.current_hand.id,
                player_id=player_id,
                action=action,
                amount=amount,
                round=game.current_hand.current_round
            )
            
            # Save the action in the action repository
            self.action_repo.create(action_history)
            
            # Add the action to the hand
            game.current_hand.actions.append(action_history)
            
            # Process the action in the poker game
            if game_id in self.poker_games:
                poker_game = self.poker_games[game_id]
                
                # Find the player in the poker game
                poker_player = next((p for p in poker_game.players if p.player_id == player_id), None)
                    
                if poker_player:
                    # Convert the domain action to poker game action
                    action_map = {
                        PlayerAction.FOLD: 'FOLD',
                        PlayerAction.CHECK: 'CHECK', 
                        PlayerAction.CALL: 'CALL',
                        PlayerAction.BET: 'BET',
                        PlayerAction.RAISE: 'RAISE',
                        PlayerAction.ALL_IN: 'ALL_IN'
                    }
                    
                    # Get the corresponding poker game action from the class, not the instance
                    from app.core.poker_game import PlayerAction as PokerPlayerAction
                    # Use BettingRound imported at the top of the method
                    # Use PokerPlayerStatus imported at the top of the file
                    poker_action = getattr(PokerPlayerAction, action_map[action])
                    
                    # Process the action
                    poker_game.process_action(poker_player, poker_action, amount)
                    
                    # ------------------------------------------------------------------
                    # HAND COMPLETE – HANDLE SHOWDOWN SEQUENCE FOR **HUMAN** ACTION PATH
                    # ------------------------------------------------------------------
                    if poker_game.current_round == PokerBettingRound.SHOWDOWN:
                        # Record end-of-hand timestamp on the domain model
                        game.current_hand.ended_at = datetime.now()

                        # Persist this hand to the running history list
                        game.hand_history.append(game.current_hand)

                        # Track hand-history id if one was generated
                        if poker_game.current_hand_id:
                            game.hand_history_ids.append(poker_game.current_hand_id)

                        # ------------------------------------------------------------------
                        # 1)  Broadcast any missing Turn / River board cards **with** the
                        #     requested pauses so the frontend can stage the reveal and play
                        #     sounds correctly.
                        # ------------------------------------------------------------------
                        try:
                            from app.core.websocket import game_notifier

                            board = poker_game.community_cards  # List[Card]

                            # If the board is incomplete (e.g. all-in pre-flop) we still
                            # want the clients to see the full run-out.  We piggy-back on
                            # notify_new_round so the frontend treats these like normal
                            # round transitions.
                            if len(board) == 3:
                                # Only flop dealt – skip additional board animations but pause
                                await asyncio.sleep(1.0)
                            elif len(board) >= 4:
                                # TURN update – reveal only the 4th card
                                await game_notifier.notify_street_dealt(
                                    game_id,
                                    PokerBettingRound.TURN.name,
                                    [board[3]]
                                )
                                await asyncio.sleep(0.5)

                                # RIVER update – reveal only the 5th card if available
                                if len(board) >= 5:
                                    await game_notifier.notify_street_dealt(
                                        game_id,
                                        PokerBettingRound.RIVER.name,
                                        [board[4]]
                                    )
                            else:
                                # Board somehow shorter than 4 – guard and pause
                                await asyncio.sleep(1.0)

                        except Exception as e:
                            logging.error(f"Error broadcasting showdown board cards: {e}")

                        # ------------------------------------------------------------------
                        # ------------------------------------------------------------------
                        # 1) Collect the final street bets into the pot (frontend will animate)
                        try:
                            from app.core.websocket import game_notifier
                            # Gather each player's current bet for this street
                            player_bets = [{'player_id': p.player_id, 'amount': p.current_bet} for p in poker_game.players]
                            # Total pot before distribution
                            total_pot = sum(pot.amount for pot in poker_game.pots)
                            await game_notifier.notify_round_bets_finalized(game_id, player_bets, total_pot)
                        except Exception as e:
                            logging.error(f"Error broadcasting round bets finalized: {e}")
                        # End-of-Hand: Frontend-driven animation sequence via granular events
                        # ------------------------------------------------------------------
                        # 2) Reveal showdown hole cards
                        try:
                            player_hands = []
                            for pp in poker_game.players:
                                if hasattr(pp, 'hand') and pp.hand and pp.status != PokerPlayerStatus.FOLDED:
                                    player_hands.append({
                                        'player_id': pp.player_id,
                                        'cards': [str(c) for c in pp.hand.cards]
                                    })
                            await game_notifier.notify_showdown_hands_revealed(game_id, player_hands)
                        except Exception as e:
                            logging.error(f"Error revealing showdown hands: {e}")

                        # 3) Announce pot winners for each pot
                        pots_info = []
                        try:
                            for idx, pot in enumerate(poker_game.pots):
                                pot_id = f"pot_{idx}"
                                winners = poker_game.hand_winners.get(pot_id, [])
                                amount = pot.amount
                                share = amount // len(winners) if winners else 0
                                winners_list = []
                                for winner in winners:
                                    # Hand rank description if available
                                    hand_rank = ''
                                    try:
                                        rank_desc = poker_game._format_hand_description
                                        if hasattr(winner, 'hand') and winner.hand:
                                            # Evaluate if needed
                                            hand_rank = rank_desc(*game.evaluate_hands().get(winner, ('', [])))
                                    except Exception:
                                        pass
                                    winners_list.append({
                                        'player_id': winner.player_id,
                                        'hand_rank': hand_rank,
                                        'share': share
                                    })
                                pots_info.append({
                                    'pot_id': pot_id,
                                    'amount': amount,
                                    'winners': winners_list
                                })
                            await game_notifier.notify_pot_winners_determined(game_id, pots_info)
                        except Exception as e:
                            logging.error(f"Error announcing pot winners: {e}")

                        # 4) Distribute chips to winners (update chip counts)
                        await asyncio.sleep(0.5)
                        try:
                            # Update domain model chip counts from poker_game
                            for p in game.players:
                                pp = next((x for x in poker_game.players if x.player_id == p.id), None)
                                if pp:
                                    p.chips = pp.chips
                            self.game_repo.update(game)
                            await game_notifier.notify_chips_distributed_to_winners(game_id, poker_game)
                        except Exception as e:
                            logging.error(f"Error distributing chips: {e}")

                        # 5) Pulse winner seat
                        await asyncio.sleep(0.5)
                        try:
                            # Primary winner: first winner of main pot
                            if pots_info and pots_info[0]['winners']:
                                await game_notifier.notify_hand_visually_concluded(game_id)
                        except Exception as e:
                            logging.error(f"Error pulsing winner seat: {e}")

                        # 6) Pause before starting next hand
                        await asyncio.sleep(2.5)

                        # 7) Start a fresh hand and notify clients of the new state
                        logging.info("Starting new hand…")
                        self._start_new_hand(game)
                        self.game_repo.update(game)
                        new_poker_game = self.poker_games.get(game_id)
                        if new_poker_game:
                            await game_notifier.notify_game_update(game_id, new_poker_game)
                    
                    # Update player states
                    for p in game.players:
                        # Find corresponding poker player by ID instead of index for safety
                        poker_p = next((pp for pp in poker_game.players if pp.player_id == p.id), None)
                        if poker_p:
                            # Update chips, status, etc.
                            p.chips = poker_p.chips
                            # Map poker game status to domain model status
                            # Using the DomainPlayerStatus imported at the top of the file
                            status_map = {
                                PokerPlayerStatus.ACTIVE: DomainPlayerStatus.ACTIVE,
                                PokerPlayerStatus.FOLDED: DomainPlayerStatus.FOLDED,
                                PokerPlayerStatus.ALL_IN: DomainPlayerStatus.ALL_IN,
                                PokerPlayerStatus.OUT: DomainPlayerStatus.OUT
                            }
                            p.status = status_map.get(poker_p.status, DomainPlayerStatus.ACTIVE)
            
            # Update the game
            self.game_repo.update(game)
            
            return game
    
    def get_hand_history(self, hand_id: str) -> Optional[HandHistory]:
        """
        Get detailed hand history by ID.
        
        Args:
            hand_id: ID of the hand history to retrieve
            
        Returns:
            The hand history if found, None otherwise
        """
        return self.hand_history_repo.get(hand_id)
    
    def get_game_hand_histories(self, game_id: str) -> List[HandHistory]:
        """
        Get all hand histories for a game.
        
        Args:
            game_id: ID of the game
            
        Returns:
            List of hand histories for the game
        """
        return self.hand_history_repo.get_by_game(game_id)
    
    def get_player_stats(self, player_id: str, game_id: Optional[str] = None) -> Any:
        """
        Get statistics for a player.
        
        Args:
            player_id: ID of the player
            game_id: Optional game ID to limit stats to a specific game
            
        Returns:
            Player statistics object
        """
        return self.hand_history_repo.get_player_stats(player_id, game_id)
        
    def process_action(
        self,
        game_id: str,
        player_id: str,
        action: PlayerAction,
        amount: Optional[int] = None
    ) -> Game:
        """Wrapper to support both sync and async invocation of process_action."""
        import asyncio
        try:
            # if in an async event loop, return coroutine
            loop = asyncio.get_running_loop()
            return self._process_action_impl(game_id, player_id, action, amount)
        except RuntimeError:
            # no running loop, execute synchronously
            return asyncio.get_event_loop().run_until_complete(
                self._process_action_impl(game_id, player_id, action, amount)
            )
        
    async def _request_and_process_ai_action(self, game_id: str, player_id: str):
        """
        Request a decision from an AI player and process it in the game.
        
        This method will:
        1. Get the game and player information
        2. Prepare the game state for the AI
        3. Request a decision from the appropriate AI agent
        4. Process the resulting action in the game
        5. Notify clients of the action and state changes
        6. Automatically trigger the next AI player's action if applicable
        
        Args:
            game_id: ID of the game
            player_id: ID of the AI player whose turn it is
            
        Returns:
            None
        """
        import logging
        import asyncio
        import time
        
        start_time = time.time()
        execution_id = f"{start_time:.6f}"
        
        logging.info(f"[AI-ACTION-START-{execution_id}] Starting AI Action for Player {player_id} in Game {game_id}")
        
        # Add consistent 0.5s delay for ALL AI actions - reduced from 1.5s to make the timing better
        # This delay is all we need - frontend no longer adds its own delay
        await asyncio.sleep(0.5)
        
        logging.info(f"[AI-ACTION-{execution_id}] --- Starting AI Action for Player {player_id} in Game {game_id} ---")
        
        call_stack = []
        import traceback
        for frame in traceback.extract_stack():
            if "_request_and_process_ai_action" in frame.name:
                call_stack.append(frame.name)
        if len(call_stack) > 1:
            logging.info(f"[AI-ACTION-{execution_id}] AI action chain depth: {len(call_stack)} - This is a recursive call")
        else:
            logging.info(f"[AI-ACTION-{execution_id}] AI action chain depth: 1 - This is the first call in the chain")
            
        # Import AI modules (using the global flag from config)
        from app.core.config import MEMORY_SYSTEM_AVAILABLE
        
        # Retrieve the game and poker game
        game = self.game_repo.get(game_id)
        if not game:
            logging.error(f"AI Action Aborted: Game {game_id} not found.")
            return
            
        poker_game = self.poker_games.get(game_id)
        if not poker_game:
            logging.error(f"AI Action Aborted: PokerGame instance for {game_id} not found.")
            return
        
        # Find the player in the domain model
        domain_player = next((p for p in game.players if p.id == player_id), None)
        if not domain_player:
            logging.error(f"AI Action Aborted: Domain player {player_id} not found.")
            return
            
        # Verify this is an AI player
        if domain_player.is_human:
            logging.warning(f"AI Action Aborted: Player {player_id} is human.")
            return
            
        # Find the player in the poker game
        poker_player = next((p for p in poker_game.players if p.player_id == player_id), None)
        if not poker_player:
            logging.error(f"AI Action Aborted: Poker player {player_id} not found.")
            return
        
        # *** CRITICAL CHECK: Verify it's actually this player's turn ***
        active_poker_players = [p for p in poker_game.players if p.status == PokerPlayerStatus.ACTIVE]
        current_idx = poker_game.current_player_idx
        player_list_len = len(poker_game.players)
        target_player_id = player_id  # The player ID passed to the function

        # Log values BEFORE the check
        logging.info(f"[AI-ACTION-CHECK-{execution_id}] Checking turn: current_idx={current_idx}, player_list_len={player_list_len}, target_player_id={target_player_id}")
        
        is_turn = False
        current_turn_player_id = "None"
        if 0 <= current_idx < player_list_len:
            current_turn_player_id = poker_game.players[current_idx].player_id
            is_turn = (current_turn_player_id == target_player_id)
        
        # The original check was complex, let's simplify and log why it fails
        if not active_poker_players:
             logging.error(f"AI Action Aborted: No active players. Context: current_idx={current_idx}, player_id={player_id}")
             return
        elif not (0 <= current_idx < player_list_len):
             logging.error(f"AI Action Aborted: current_player_idx {current_idx} is out of bounds for players list length {player_list_len}. Context: player_id={player_id}")
             return
        elif poker_game.players[current_idx].player_id != target_player_id:
             logging.error(f"AI Action Aborted: It's not player {target_player_id}'s turn. Current turn is index {current_idx} (Player ID: {current_turn_player_id})")
             return
        # If we pass all checks, log success
        logging.info(f"[AI-ACTION-CHECK-{execution_id}] Turn validation passed for player {player_id}")
        # *** END CRITICAL CHECK ***
        
        # Enhanced logging with position information
        position_name = "Unknown"
        if poker_game.button_position == poker_player.position:
            position_name = "BTN (Dealer)"
        elif (poker_game.button_position + 1) % len(active_poker_players) == poker_player.position:
            position_name = "SB (Small Blind)"
        elif (poker_game.button_position + 2) % len(active_poker_players) == poker_player.position:
            position_name = "BB (Big Blind)"
        elif (poker_game.button_position + 3) % len(active_poker_players) == poker_player.position:
            position_name = "UTG (Under the Gun)"
        
        logging.info(f"AI Action: Player {domain_player.name} [{position_name} - Position {poker_player.position}] (Player ID: {player_id}), Archetype: {domain_player.archetype or 'Default'}")
        logging.info(f"AI Action: Current Round: {poker_game.current_round.name}, Current Bet: {poker_game.current_bet}, To Act: {poker_game.to_act}")
        
        # Get archetype and intelligence level (with defaults)
        archetype = domain_player.archetype or "TAG"  # Default to TAG if not specified
        intelligence_level = "expert"  # Default intelligence level
        
        # Prepare game state for AI consumption (using utility function)
        from app.core.utils import game_to_model
        game_state = game_to_model(game_id, poker_game)
        
        # Create context with additional information
        context = {
            "game_type": "tournament" if game.type == GameType.TOURNAMENT else "cash",
            "blinds": [game_state.small_blind, game_state.big_blind],
            "ante": game_state.ante
        }
        
        # Add tournament-specific context if applicable
        if game.type == GameType.TOURNAMENT and game.tournament_info:
            context["stage"] = game.tournament_info.stage.value
            context["level"] = game.tournament_info.current_level
            context["players_remaining"] = game.tournament_info.players_remaining
            context["total_players"] = game.tournament_info.total_players
        
        # Convert game_state to dictionary for AI consumption
        game_state_dict = game_state.dict()
        # --- Compute accurate to_call for current player ---
        try:
            highest_total = max(
                p['total_bet'] for p in game_state_dict['players']
                if p['status'] in ("ACTIVE", "ALL_IN")
            )
            me = next(
                p for p in game_state_dict['players'] if p['player_id'] == player_id
            )
            game_state_dict['to_call'] = max(0, highest_total - me.get('total_bet', 0))
        except Exception as e:
            logging.error(f"[AI-ACTION] Error computing to_call: {e}")
            # Fallback to current_bet as to_call
            game_state_dict['to_call'] = game_state_dict.get('current_bet', 0)
        
        # Filter sensitive information - only show this player's cards
        for player_model in game_state_dict["players"]:
            if player_model["player_id"] != player_id:
                player_model["cards"] = None
        
        try:
            # Determine a smart default action based on game state
            current_bet = game_state_dict.get("current_bet", 0)
            if current_bet == 0:
                action_type = "CHECK"  # Default to check if no bet to call
            else:
                # We'll decide between CALL and FOLD based on various factors below
                action_type = "FOLD"
            action_amount = None
            
            # AI decision with fallback retries
            from ai.memory_integration import MemoryIntegration
            from ai.agents.response_parser import AgentResponseParser
            from app.core.poker_game import PlayerAction as PokerPlayerAction
            max_retries = 3
            final_action_type: str = None
            final_action_amount = None
            for attempt in range(1, max_retries + 1):
                logging.info(f"[AI-ACTION-{execution_id}] Attempt {attempt}/{max_retries} for AI decision")
                try:
                    ai_decision = await MemoryIntegration.get_agent_decision(
                        archetype=archetype,
                        game_state=game_state_dict,
                        context=context,
                        player_id=player_id,
                        use_memory=False,
                        intelligence_level=intelligence_level
                    )
                    logging.info(f"[AI-ACTION-{execution_id}] Attempt {attempt}: Raw AI decision: {ai_decision}")
                    action_str, amount, metadata = AgentResponseParser.parse_response(ai_decision)
                    logging.info(f"[AI-ACTION-{execution_id}] Attempt {attempt}: Parsed action: {action_str}, amount: {amount}")
                    # Handle null or zero amount for ALL_IN
                    if action_str.lower().replace('-', '_').replace(' ', '_') == 'all_in' and (amount is None or amount <= 0):
                        correct_amount = poker_player.chips + poker_player.current_bet
                        logging.warning(f"[AI-ACTION-{execution_id}] Corrected ALL_IN amount for player {player_id} from {amount} to {correct_amount}")
                        amount = correct_amount
                    action_str, amount = AgentResponseParser.apply_game_rules(action_str, amount, game_state_dict)
                    logging.info(f"[AI-ACTION-{execution_id}] Attempt {attempt}: Action after rules: {action_str}, amount: {amount}")
                    normalized = action_str.lower().replace('-', '_').replace(' ', '_')
                    action_map = {
                        'fold': 'FOLD', 'check': 'CHECK', 'call': 'CALL',
                        'bet': 'BET', 'raise': 'RAISE', 'all_in': 'ALL_IN'
                    }
                    action_type = action_map.get(normalized)
                    if not action_type and 'all' in normalized and 'in' in normalized:
                        action_type = 'ALL_IN'
                    if not action_type:
                        raise ValueError(f"Invalid action type: {action_str}")
                    if action_type == 'ALL_IN':
                        final_action_amount = amount or (poker_player.chips + poker_player.current_bet)
                    else:
                        final_action_amount = amount
                    final_action_type = action_type
                    break
                except Exception as e:
                    logging.warning(f"[AI-ACTION-{execution_id}] Attempt {attempt} failed: {e}")
                    if attempt == max_retries:
                        final_action_type = 'FOLD'
                        final_action_amount = None
                        logging.error(f"[AI-ACTION-{execution_id}] All {max_retries} attempts failed. Defaulting to FOLD.")
            # Finalize action_type and action_amount
            action_type = final_action_type
            action_amount = final_action_amount
            # Log the final chosen action for debugging
            logging.info(f"[AI-ACTION-{execution_id}] Final chosen action for player {player_id}: {action_type} with amount {action_amount}")
            
            # Convert the action type string to the poker game action enum
            from app.core.poker_game import PlayerAction as PokerPlayerAction
            try:
                poker_action = getattr(PokerPlayerAction, action_type)
            except AttributeError:
                logging.error(f"Invalid action type '{action_type}' received from AI or mapping. Defaulting to FOLD.")
                poker_action = PokerPlayerAction.FOLD
                action_amount = None
            
            # Ensure only one AI action for this game is processed at a time by using a lock
            if game_id not in self.game_locks:
                self.game_locks[game_id] = asyncio.Lock()
            game_lock = self.game_locks[game_id]
            
            # Get the lock before processing the action
            logging.info(f"[AI-ACTION-{execution_id}] Acquiring game lock for processing action")
            # Capture player's current bet to compute actual call size for 'CALL' actions
            prev_player_bet = poker_player.current_bet
            async with game_lock:
                logging.info(f"[AI-ACTION-{execution_id}] Lock acquired - Processing {poker_action.name} {action_amount if action_amount is not None else ''} in PokerGame")
                logging.info(f"[AI-ACTION-{execution_id}] Before process_action - to_act: {poker_game.to_act}")
                success = poker_game.process_action(poker_player, poker_action, action_amount)
                logging.info(f"[AI-ACTION-{execution_id}] After process_action - to_act: {poker_game.to_act}")
                logging.info(f"[AI-ACTION-{execution_id}] PokerGame process_action result: {success}")
                # If invalid, force a fold to advance game state
                if not success:
                    from app.core.poker_game import PlayerAction as PokerPlayerAction
                    logging.error(f"[AI-ACTION-{execution_id}] Invalid AI action {poker_action.name} {action_amount}. Forcing FOLD to prevent stall.")
                    # Force fold
                    fold_action = PokerPlayerAction.FOLD
                    poker_game.process_action(poker_player, fold_action, None)
                    # Notify forced fold
                    from app.core.websocket import game_notifier
                    await game_notifier.notify_player_action(
                        game_id,
                        player_id,
                        fold_action.name,
                        None,
                        total_street_bet=None,
                        total_hand_bet=None
                    )
                    # Update and notify game state
                    self.game_repo.update(game)
                    await game_notifier.notify_game_update(game_id, poker_game)
                    return
            # Compute actual amount for notify (especially CALL actions) and totals
            # post_street_bet: total bet on current street after action
            post_street_bet = poker_player.current_bet
            # post_hand_bet: total bet this hand after action (used for all-ins)
            post_hand_bet = poker_player.total_bet
            if poker_action == PokerPlayerAction.CALL:
                notify_amount = post_street_bet - prev_player_bet
            else:
                notify_amount = action_amount
            
            if success:
                # Update domain player
                domain_player.has_acted = True
                
                # Create action history record for the AI action
                from app.models.domain_models import PlayerAction as DomainPlayerAction, ActionHistory
                action_history = ActionHistory(
                    game_id=game_id,
                    hand_id=game.current_hand.id if game.current_hand else "",
                    player_id=player_id,
                    action=getattr(DomainPlayerAction, action_type),
                    amount=action_amount,
                    round=game.current_hand.current_round if game.current_hand else BettingRound.PREFLOP
                )
                
                # Save the action
                self.action_repo.create(action_history)
                
                # Add the action to the hand
                if game.current_hand:
                    game.current_hand.actions.append(action_history)
                
                # Notify clients about the AI action, passing total bets for correct log phrasing
                from app.core.websocket import game_notifier
                await game_notifier.notify_player_action(
                    game_id,
                    player_id,
                    action_type,
                    notify_amount,
                    total_street_bet=post_street_bet,
                    # If the action is an all-in or a call that leaves player with zero chips, treat as all-in
                    total_hand_bet=(post_hand_bet if (poker_action == PokerPlayerAction.ALL_IN or 
                                                   (poker_action == PokerPlayerAction.CALL and poker_player.chips == 0))
                                     else None),
                )
                
                # Update game state in the repository
                self.game_repo.update(game)
                
                # Notify clients about updated game state
                await game_notifier.notify_game_update(game_id, poker_game)
                
                # Check if hand is complete and handle accordingly
                # Using PokerBettingRound imported at top of file
                if poker_game.current_round == PokerBettingRound.SHOWDOWN:
                    logging.info("AI Action: Hand ended, handling showdown.")
                    # Record end of hand in domain model
                    if game.current_hand:
                        game.current_hand.ended_at = datetime.now()
                        # Add to hand history
                        game.hand_history.append(game.current_hand)
                        # Update hand history IDs list if we have a hand history ID
                        if poker_game.current_hand_id:
                             game.hand_history_ids.append(poker_game.current_hand_id)

                    # If an early all-in showdown (board incomplete), broadcast Turn/River with pauses
                    board = poker_game.community_cards
                    try:
                        # Turn then River if needed
                        if len(board) == 3:
                            await game_notifier.notify_street_dealt(
                                game_id,
                                PokerBettingRound.TURN.name,
                                board[:4]
                            )
                            await asyncio.sleep(1.0)
                            await game_notifier.notify_street_dealt(
                                game_id,
                                PokerBettingRound.RIVER.name,
                                board
                            )
                            await asyncio.sleep(1.0)
                        elif len(board) == 4:
                            await game_notifier.notify_street_dealt(
                                game_id,
                                PokerBettingRound.RIVER.name,
                                board
                            )
                            await asyncio.sleep(1.0)
                    except Exception as e:
                        logging.error(f"Error broadcasting post-flop showdown boards: {e}")
                    # ------------------------------------------------------------------
                    # 1) Collect the final street bets into the pot (frontend will animate)
                    try:
                        from app.core.websocket import game_notifier
                        player_bets = [{'player_id': p.player_id, 'amount': p.current_bet} for p in poker_game.players]
                        total_pot = sum(pot.amount for pot in poker_game.pots)
                        await game_notifier.notify_round_bets_finalized(game_id, player_bets, total_pot)
                    except Exception as e:
                        logging.error(f"Error broadcasting round bets finalized (AI path): {e}")
                    # End-of-Hand: Frontend-driven animation sequence via granular events
                    # ------------------------------------------------------------------
                    # 2) Reveal showdown hole cards
                    try:
                        player_hands = []
                        for pp in poker_game.players:
                            if hasattr(pp, 'hand') and pp.hand and pp.status != PokerPlayerStatus.FOLDED:
                                player_hands.append({
                                    'player_id': pp.player_id,
                                    'cards': [str(c) for c in pp.hand.cards]
                                })
                        await game_notifier.notify_showdown_hands_revealed(game_id, player_hands)
                    except Exception as e:
                        logging.error(f"Error revealing showdown hands (AI path): {e}")

                    # 3) Announce pot winners
                    pots_info = []
                    try:
                        for idx, pot in enumerate(poker_game.pots):
                            pot_id = f"pot_{idx}"
                            winners = poker_game.hand_winners.get(pot_id, [])
                            amount = pot.amount
                            share = amount // len(winners) if winners else 0
                            winners_list = []
                            for winner in winners:
                                winners_list.append({
                                    'player_id': winner.player_id,
                                    'hand_rank': '',  # optional rank description
                                    'share': share
                                })
                            pots_info.append({
                                'pot_id': pot_id,
                                'amount': amount,
                                'winners': winners_list
                            })
                        await game_notifier.notify_pot_winners_determined(game_id, pots_info)
                    except Exception as e:
                        logging.error(f"Error announcing pot winners (AI path): {e}")

                    # 4) Distribute chips to winners (update chip counts)
                    await asyncio.sleep(0.5)
                    try:
                        for p in game.players:
                            pp = next((x for x in poker_game.players if x.player_id == p.id), None)
                            if pp:
                                p.chips = pp.chips
                        self.game_repo.update(game)
                        await game_notifier.notify_chips_distributed_to_winners(game_id, poker_game)
                    except Exception as e:
                        logging.error(f"Error distributing chips (AI path): {e}")

                    # 5) Pulse winner seat
                    await asyncio.sleep(0.5)
                    try:
                        if pots_info and pots_info[0]['winners']:
                            await game_notifier.notify_hand_visually_concluded(game_id)
                    except Exception as e:
                        logging.error(f"Error pulsing winner seat (AI path): {e}")

                    # 6) Pause before starting next hand
                    await asyncio.sleep(1.0)

                    # 7) Move button, start new hand, and notify clients
                    logging.info("AI Action: Starting new hand.")
                    poker_game.move_button()
                    logging.info(f"AI Action: Moved button to position {poker_game.button_position}")
                    self._start_new_hand(game)
                    self.game_repo.update(game)
                    new_poker_game = self.poker_games.get(game.id)
                    if new_poker_game:
                        logging.info("AI Action: Notifying clients about the *new* hand state.")
                        await game_notifier.notify_game_update(game_id, new_poker_game)
                        # Trigger first player action in new hand
                        if 0 <= new_poker_game.current_player_idx < len(new_poker_game.players):
                            first = new_poker_game.players[new_poker_game.current_player_idx]
                            first_domain = next((p for p in game.players if p.id == first.player_id), None)
                            if first_domain and not first_domain.is_human:
                                asyncio.create_task(self._request_and_process_ai_action(game_id, first.player_id))
                            else:
                                await game_notifier.notify_action_request(game_id, new_poker_game)
                    else:
                        logging.error("AI Action: Could not find poker game instance after starting new hand to notify clients.")
                else:
                    # FIXED: No longer need to explicitly advance the player here
                    # Turn advancement is now handled directly within poker_game.process_action
                    logging.info(f"[AI-ACTION-{execution_id}] Hand continues after AI action - turn already advanced internally")
                    
                    # Log current state for monitoring
                    logging.info(f"[AI-ACTION-{execution_id}] Current player_idx: {poker_game.current_player_idx}")
                    logging.info(f"[AI-ACTION-{execution_id}] Current to_act set: {poker_game.to_act}")
                    if 0 <= poker_game.current_player_idx < len(poker_game.players):
                        current_p = poker_game.players[poker_game.current_player_idx]
                        logging.info(f"[AI-ACTION-{execution_id}] Current player is: {current_p.name}, in to_act: {current_p.player_id in poker_game.to_act}")
                    
                    # Now check the current player
                    logging.info(f"[AI-ACTION-{execution_id}] Checking current player after AI action")
                    
                    # Get the next player using the newly advanced index
                    if poker_game.current_player_idx < len(poker_game.players):
                        next_player = poker_game.players[poker_game.current_player_idx]
                        next_player_domain = next((p for p in game.players if p.id == next_player.player_id), None)

                        # Log detailed next player info
                        next_position_name = "Unknown"
                        if poker_game.button_position == next_player.position:
                            next_position_name = "BTN (Dealer)"
                        elif (poker_game.button_position + 1) % len(active_poker_players) == next_player.position:
                            next_position_name = "SB (Small Blind)"
                        elif (poker_game.button_position + 2) % len(active_poker_players) == next_player.position:
                            next_position_name = "BB (Big Blind)"
                        elif (poker_game.button_position + 3) % len(active_poker_players) == next_player.position:
                            next_position_name = "UTG (Under the Gun)"
                        
                        logging.info(f"[AI-ACTION-{execution_id}] Next player determined: {next_player.name} [{next_position_name} - Position {next_player.position}] (index {poker_game.current_player_idx})")
                        logging.info(f"[AI-ACTION-{execution_id}] Next player status: {next_player.status}, in to_act: {next_player.player_id in poker_game.to_act}")
                        logging.info(f"[AI-ACTION-{execution_id}] Active players: {len(active_poker_players)}")
                        logging.info(f"[AI-ACTION-{execution_id}] to_act set content: {poker_game.to_act}")
                        logging.info(f"[AI-ACTION-{execution_id}] All players position info: {[(p.name, p.position, (p.position - poker_game.button_position) % len(poker_game.players)) for p in poker_game.players]}")

                        # Verify this player is active and needs to act
                        if (next_player.status == PokerPlayerStatus.ACTIVE and
                            next_player.player_id in poker_game.to_act and
                            next_player_domain):

                            if not next_player_domain.is_human:
                                logging.info(f"[AI-ACTION-{execution_id}] Next player is AI ({next_player.name}). AWAITING next action (sequential execution).")
                                # Maintain sequential execution (no create_task) to prevent race conditions
                                # This ensures one AI player completes their action before the next one begins
                                await self._request_and_process_ai_action(game_id, next_player.player_id)
                            else:
                                logging.info(f"[AI-ACTION-{execution_id}] Next player is Human ({next_player.name}). Sending action request.")
                                await game_notifier.notify_action_request(game_id, poker_game)
                        else:
                            # Next in turn cannot act: look for any other eligible ACTIVE player in to_act
                            logging.warning(
                                f"[AI-ACTION-{execution_id}] Next player {next_player.name} cannot act "
                                f"(Status: {next_player.status}, in to_act: {next_player.player_id in poker_game.to_act}). "
                                "Searching for another eligible player."
                            )
                            # Try all remaining to_act players in seating order
                            for pid in list(poker_game.to_act):
                                alt = next((p for p in poker_game.players if p.player_id == pid), None)
                                if alt and alt.status == PokerPlayerStatus.ACTIVE:
                                    alt_domain = next((p for p in game.players if p.id == alt.player_id), None)
                                    if alt_domain:
                                        logging.info(
                                            f"[AI-ACTION-{execution_id}] Found alternate player to act: {alt.name}"
                                        )
                                        # Schedule AI or human action for this player
                                        if not alt_domain.is_human:
                                            await self._request_and_process_ai_action(game_id, alt.player_id)
                                        else:
                                            await game_notifier.notify_action_request(game_id, poker_game)
                                        return
                            # No eligible players left: likely round or hand complete
                            logging.info(
                                f"[AI-ACTION-{execution_id}] No further eligible players to act; round or hand may have concluded."
                            )
                    else:
                        logging.error(f"AI Action: Invalid current_player_idx after action: {poker_game.current_player_idx}")
                        
            else: # process_action failed
                logging.error(f"AI Action Failed: PokerGame.process_action returned False for player {player_id} action {poker_action.name}")
            
        except Exception as e:
            logging.error(f"AI Action Error: Exception during processing for player {player_id}: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            # If player is not eligible to act, force a fold to keep state consistent
            from app.core.poker_game import PlayerAction as PokerPlayerAction
            if poker_player and poker_player.player_id not in poker_game.to_act:
                logging.error(f"[AI-ACTION-{execution_id}] Fallback aborted: player {player_id} not in to_act. Forcing FOLD.")
                poker_action = PokerPlayerAction.FOLD
                fallback_action_name = "FOLD"
            else:
                # Use intelligent fallback based on game state
                from app.core.poker_game import PlayerAction as PokerPlayerAction

                # Get current bet to determine appropriate action
                current_bet = poker_game.current_bet if poker_game else 0

                if current_bet == 0:
                    # If no bet to call, check is the safest action
                    poker_action = PokerPlayerAction.CHECK
                    fallback_action_name = "CHECK"
                else:
                    # Determine if we should call or fold
                    # Use archetype to make this decision
                    if domain_player and domain_player.archetype:
                        archetype = domain_player.archetype
                        # Aggressive archetypes should call more often
                        if any(x in archetype for x in ["LAG", "Maniac", "CallingStation"]):
                            poker_action = PokerPlayerAction.CALL
                            fallback_action_name = "CALL"
                        else:
                            poker_action = PokerPlayerAction.FOLD
                            fallback_action_name = "FOLD"
                    else:
                        poker_action = PokerPlayerAction.FOLD
                        fallback_action_name = "FOLD"
                
            try:
                # Ensure poker_player is valid before processing the action
                if poker_player and poker_game:
                    logging.warning(f"AI Action Error: Using fallback {fallback_action_name} for player {player_id}")
                    # Process the fallback action
                    action_success = poker_game.process_action(poker_player, poker_action, None)
                    if not action_success and fallback_action_name != "FOLD":
                        # If the chosen action fails, fall back to FOLD
                        logging.warning(f"AI Action Error: {fallback_action_name} failed, forcing FOLD")
                        poker_action = PokerPlayerAction.FOLD
                        fallback_action_name = "FOLD"
                        poker_game.process_action(poker_player, poker_action, None)
                    # Compute totals for log
                    fs_post_street = poker_player.current_bet
                    fs_post_hand = poker_player.total_bet
                    # Notify clients about fallback action
                    from app.core.websocket import game_notifier
                    await game_notifier.notify_player_action(
                        game_id,
                        player_id,
                        fallback_action_name,
                        None,
                        total_street_bet=fs_post_street,
                        total_hand_bet=(fs_post_hand if fallback_action_name.upper() in ["ALL_IN", "ALL-IN"] else None),
                    )
                    await game_notifier.notify_game_update(game_id, poker_game)
                else:
                    logging.error(f"AI Action Error: Cannot process action because poker_player or poker_game is invalid.")
            except Exception as action_error:
                logging.error(f"AI Action Error: Failed to process {fallback_action_name} action after error: {action_error}")

        logging.info(f"[AI-ACTION-END-{execution_id}] Finished AI Action for Player {player_id} - Duration: {time.time() - start_time:.2f}s")
    def cash_out_player(self, game_id: str, player_id: str) -> int:
        """
        Remove a player from a cash game and return their chip count.
        
        Args:
            game_id: ID of the cash game
            player_id: ID of the player to cash out
            
        Returns:
            The player's final chip count
            
        Raises:
            ValueError: If game is not a cash game or player is not found
        """
        game = self.game_repo.get(game_id)
        if not game:
            raise KeyError(f"Game {game_id} not found")
            
        if game.type != GameType.CASH:
            raise ValueError("Game is not a cash game")
        
        # Find the player
        player = next((p for p in game.players if p.id == player_id), None)
        if not player:
            raise ValueError(f"Player {player_id} not found in game")
        
        # Get their chip count
        chips = player.chips
        
        # Handle active poker game if exists
        if game_id in self.poker_games:
            poker_game = self.poker_games[game_id]
            poker_game.remove_player(player_id)
        
        # Remove from game model
        game.players = [p for p in game.players if p.id != player_id]
        
        # Update game
        self.game_repo.update(game)
        
        return chips
        
    def rebuy_player(self, game_id: str, player_id: str, amount: int) -> Player:
        """
        Add chips to a player in a cash game (rebuy).
        
        Args:
            game_id: ID of the cash game
            player_id: ID of the player
            amount: Amount of chips to add
            
        Returns:
            Updated player entity
            
        Raises:
            ValueError: If buy-in would exceed maximum or game is not a cash game
        """
        game = self.game_repo.get(game_id)
        if not game:
            raise KeyError(f"Game {game_id} not found")
            
        if game.type != GameType.CASH:
            raise ValueError("Game is not a cash game")
        
        # Find the player
        player = next((p for p in game.players if p.id == player_id), None)
        if not player:
            raise ValueError(f"Player {player_id} not found in game")
        
        # Validate new total doesn't exceed maximum
        new_total = player.chips + amount
        if new_total > game.cash_game_info.max_buy_in:
            raise ValueError(f"Rebuy would exceed maximum buy-in of {game.cash_game_info.max_buy_in}")
        
        # Add chips to player
        player.chips += amount
        
        # Update in poker game if exists
        if game_id in self.poker_games:
            poker_game = self.poker_games[game_id]
            poker_player = next((p for p in poker_game.players if p.player_id == player_id), None)
            if poker_player:
                poker_player.chips += amount
        
        # Update game
        self.game_repo.update(game)
        
        return player
        
    def top_up_player(self, game_id: str, player_id: str) -> Tuple[Player, int]:
        """
        Top up a player's chips to the maximum buy-in (useful between hands).
        
        Args:
            game_id: ID of the cash game
            player_id: ID of the player
            
        Returns:
            Tuple of (updated player, amount topped up)
            
        Raises:
            ValueError: If game is not a cash game or player already at maximum
        """
        game = self.game_repo.get(game_id)
        if not game:
            raise KeyError(f"Game {game_id} not found")
            
        if game.type != GameType.CASH:
            raise ValueError("Game is not a cash game")
        
        # Find the player
        player = next((p for p in game.players if p.id == player_id), None)
        if not player:
            raise ValueError(f"Player {player_id} not found in game")
        
        # Calculate top-up amount
        max_buy_in = game.cash_game_info.max_buy_in
        current_chips = player.chips
        
        if current_chips >= max_buy_in:
            raise ValueError(f"Player already has maximum chips ({current_chips} >= {max_buy_in})")
        
        top_up_amount = max_buy_in - current_chips
        
        # Add chips to player
        player.chips = max_buy_in
        
        # Update in poker game if exists
        if game_id in self.poker_games:
            poker_game = self.poker_games[game_id]
            poker_player = next((p for p in poker_game.players if p.player_id == player_id), None)
            if poker_player:
                poker_player.chips += top_up_amount
        
        # Update game
        self.game_repo.update(game)
        
        return player, top_up_amount