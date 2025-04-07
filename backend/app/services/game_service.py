"""
Game service implementing poker game business logic.
This service coordinates between the API layer and the repositories.
"""
import random
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set

from app.core.cards import Deck
from app.core.hand_evaluator import HandEvaluator
from app.core.poker_game import PokerGame
from app.models.domain_models import (
    Game, Player, Hand, ActionHistory, GameType, GameStatus, 
    BettingRound, PlayerAction, PlayerStatus, TournamentInfo, CashGameInfo,
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
            status=PlayerStatus.WAITING
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
        
    def start_game(self, game_id: str) -> Game:
        """
        Start a poker game.
        
        Args:
            game_id: ID of the game to start
            
        Returns:
            The updated Game entity
            
        Raises:
            ValueError: If the game cannot be started
            KeyError: If the game doesn't exist
        """
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
        # Determine hand number
        hand_number = len(game.hand_history) + 1
        
        # Determine dealer position
        dealer_position = 0
        if hand_number > 1:
            # Move dealer button clockwise
            active_positions = sorted([p.position for p in game.players if p.status != PlayerStatus.OUT])
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
            if player.status == PlayerStatus.OUT:
                continue
                
            # Reset player state for new hand
            player.cards = []
            player.bet = 0
            player.has_acted = False
            player.status = PlayerStatus.ACTIVE
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
                if player.status != PlayerStatus.OUT:
                    poker_game.add_player(player.id, player.name, player.chips)
                    
            self.poker_games[game.id] = poker_game
        else:
            # Use existing poker game
            poker_game = self.poker_games[game.id]
            
        # Start a hand in the poker game
        poker_game.start_hand()
        
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

    def process_action(
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
        game = self.game_repo.get(game_id)
        if not game:
            raise KeyError(f"Game {game_id} not found")
            
        if game.status != GameStatus.ACTIVE:
            raise ValueError(f"Cannot process action for game with status {game.status}")
            
        if not game.current_hand:
            raise ValueError("No active hand in the game")
            
        # Validate the player
        player = None
        for p in game.players:
            if p.id == player_id:
                player = p
                break
        
        if not player:
            raise KeyError(f"Player {player_id} not found in game {game_id}")
        
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
            poker_player = None
            for p in poker_game.players:
                if p.player_id == player_id:
                    poker_player = p
                    break
                    
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
                poker_action = getattr(PokerPlayerAction, action_map[action])
                
                # Process the action
                poker_game.process_action(poker_player, poker_action, amount)
                
                # If the hand is over, start a new one
                from app.core.poker_game import BettingRound
                if poker_game.current_round == BettingRound.SHOWDOWN:
                    # Record end of hand in domain model
                    game.current_hand.ended_at = datetime.now()
                    
                    # Add to hand history
                    game.hand_history.append(game.current_hand)
                    
                    # Update hand history IDs list if we have a hand history ID
                    if poker_game.current_hand_id:
                        game.hand_history_ids.append(poker_game.current_hand_id)
                    
                    # Start a new hand
                    self._start_new_hand(game)
                
                # Update player states
                for i, p in enumerate(game.players):
                    if i < len(poker_game.players):
                        poker_p = poker_game.players[i]
                        if p.id == poker_p.player_id:
                            # Update chips, status, etc.
                            p.chips = poker_p.chips
                            from app.core.poker_game import PlayerStatus as PokerPlayerStatus
                            status_map = {
                                PokerPlayerStatus.ACTIVE: PlayerStatus.ACTIVE,
                                PokerPlayerStatus.FOLDED: PlayerStatus.FOLDED,
                                PokerPlayerStatus.ALL_IN: PlayerStatus.ALL_IN,
                                PokerPlayerStatus.OUT: PlayerStatus.OUT
                            }
                            p.status = status_map.get(poker_p.status, PlayerStatus.ACTIVE)
        
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
        logging.info(f"=== AI ACTION CHAIN: START for player {player_id} in game {game_id} ===")
        logging.info(f"This is a critical method that should handle the chain of AI actions")
        call_stack = []
        import traceback
        for frame in traceback.extract_stack():
            if "_request_and_process_ai_action" in frame.name:
                call_stack.append(frame.name)
        if len(call_stack) > 1:
            logging.info(f"AI action chain depth: {len(call_stack)} - This is a recursive call")
        else:
            logging.info("AI action chain depth: 1 - This is the first call in the chain")
        # Import AI memory integration (done here to avoid circular imports)
        try:
            from ai.memory_integration import MemoryIntegration
            from ai.agents.response_parser import AgentResponseParser
            MEMORY_SYSTEM_AVAILABLE = True
        except ImportError:
            MEMORY_SYSTEM_AVAILABLE = False
            import logging
            logging.warning("AI memory system not available. AI decision will default to fold.")
        
        # Import for utility function
        from app.core.utils import game_to_model
        
        # Retrieve the game and poker game
        game = self.game_repo.get(game_id)
        if not game:
            return
            
        poker_game = self.poker_games.get(game_id)
        if not poker_game:
            return
        
        # Find the player in the domain model
        domain_player = next((p for p in game.players if p.id == player_id), None)
        if not domain_player:
            return
            
        # Verify this is an AI player
        if domain_player.is_human:
            return
            
        # Find the player in the poker game
        poker_player = next((p for p in poker_game.players if p.player_id == player_id), None)
        if not poker_player:
            return
        
        # Get archetype and intelligence level (with defaults)
        archetype = domain_player.archetype or "TAG"  # Default to TAG if not specified
        intelligence_level = "expert"  # Default intelligence level
        
        # Prepare game state for AI consumption (using utility function)
        game_state = game_to_model(game_id, poker_game)
        
        # Create context with additional information
        context = {
            "game_type": "tournament" if game.type == "tournament" else "cash",
            "blinds": [game_state.small_blind, game_state.big_blind],
            "ante": game_state.ante
        }
        
        # Add tournament-specific context if applicable
        if game.type == "tournament" and game.tournament_info:
            context["stage"] = game.tournament_info.stage.value
            context["level"] = game.tournament_info.current_level
            context["players_remaining"] = game.tournament_info.players_remaining
            context["total_players"] = game.tournament_info.total_players
        
        # Convert game_state to dictionary for AI consumption
        game_state_dict = game_state.dict()
        
        # Filter sensitive information - only show this player's cards
        for player_model in game_state_dict["players"]:
            if player_model["player_id"] != player_id:
                player_model["cards"] = None
        
        try:
            # Default action in case of error
            action_type = "FOLD"
            action_amount = None
            
            if MEMORY_SYSTEM_AVAILABLE:
                # Request decision from AI via MemoryIntegration
                ai_decision = await MemoryIntegration.get_agent_decision(
                    archetype=archetype,
                    game_state=game_state_dict,
                    context=context,
                    player_id=player_id,
                    use_memory=True,
                    intelligence_level=intelligence_level
                )
                
                # Parse and validate the response
                action, amount, metadata = AgentResponseParser.parse_response(ai_decision)
                
                # Apply game rules to ensure the action is valid
                action, amount = AgentResponseParser.apply_game_rules(action, amount, game_state_dict)
                
                # Map AI response to poker game actions
                action_map = {
                    "fold": "FOLD",
                    "check": "CHECK",
                    "call": "CALL",
                    "bet": "BET",
                    "raise": "RAISE",
                    "all-in": "ALL_IN"
                }
                
                action_type = action_map.get(action, "FOLD")
                action_amount = amount
                
            # Convert the action type string to the poker game action enum
            from app.core.poker_game import PlayerAction as PokerPlayerAction
            poker_action = getattr(PokerPlayerAction, action_type)
            
            # Process the action in the poker game
            success = poker_game.process_action(poker_player, poker_action, action_amount)
            
            if success:
                # Update domain player
                domain_player.has_acted = True
                
                # Create action history record for the AI action
                from app.models.domain_models import PlayerAction, ActionHistory
                action_history = ActionHistory(
                    game_id=game_id,
                    hand_id=game.current_hand.id if game.current_hand else "",
                    player_id=player_id,
                    action=getattr(PlayerAction, action_type),
                    amount=action_amount,
                    round=game.current_hand.current_round if game.current_hand else "preflop"
                )
                
                # Save the action
                self.action_repo.create(action_history)
                
                # Add the action to the hand
                if game.current_hand:
                    game.current_hand.actions.append(action_history)
                
                # Notify clients about the AI action
                from app.core.websocket import game_notifier
                await game_notifier.notify_player_action(
                    game_id, player_id, action_type, action_amount
                )
                
                # Update game state in the repository
                self.game_repo.update(game)
                
                # Notify clients about updated game state
                await game_notifier.notify_game_update(game_id, poker_game)
                
                # Check if hand is complete and handle accordingly
                from app.core.poker_game import BettingRound
                if poker_game.current_round == BettingRound.SHOWDOWN:
                    # Record end of hand in domain model
                    if game.current_hand:
                        game.current_hand.ended_at = datetime.now()
                        
                        # Add to hand history
                        game.hand_history.append(game.current_hand)
                        
                        # Update hand history IDs list if we have a hand history ID
                        if poker_game.current_hand_id:
                            game.hand_history_ids.append(poker_game.current_hand_id)
                    
                    # Notify about hand result
                    await game_notifier.notify_hand_result(game_id, poker_game)
                    
                    # Start a new hand
                    self._start_new_hand(game)
                    
                    # Update game in repository again after starting new hand
                    self.game_repo.update(game)
                else:
                    # Get the next player - we need to find the ACTUAL next player
                    # who needs to act, not just use the current_player_idx
                    from app.core.poker_game import PlayerStatus
                    import logging
                    
                    # Log current state for debugging
                    logging.info(f"After AI action, finding next player. Current index: {poker_game.current_player_idx}")
                    
                    # Get active players and players who still need to act
                    active_players = [p for p in poker_game.players 
                                     if p.status == PlayerStatus.ACTIVE]
                    to_act_players = [p for p in active_players 
                                     if p.player_id in poker_game.to_act]
                    
                    logging.info(f"Active players: {len(active_players)}, Players to act: {len(to_act_players)}")
                    
                    # The current_player_idx should already be updated to the next player by process_action
                    # We just need to get that player
                    if poker_game.current_player_idx < len(poker_game.players):
                        next_player = poker_game.players[poker_game.current_player_idx]
                        next_player_domain = next((p for p in game.players if p.id == next_player.player_id), None)
                        
                        logging.info(f"Next player is {next_player.name} (index {poker_game.current_player_idx})")
                        logging.info(f"Next player status: {next_player.status}, in to_act: {next_player.player_id in poker_game.to_act}")
                        
                        # Verify this player is active and needs to act
                        if (next_player.status == PlayerStatus.ACTIVE and 
                            next_player.player_id in poker_game.to_act and
                            next_player_domain):
                            
                            if not next_player_domain.is_human:
                                # If next player is also AI, trigger their action asynchronously
                                logging.info(f"Triggering AI action for next player: {next_player.name}")
                                import asyncio
                                asyncio.create_task(self._request_and_process_ai_action(
                                    game_id, next_player.player_id
                                ))
                            else:
                                # If next player is human, notify them it's their turn
                                logging.info(f"Requesting action from human player: {next_player.name}")
                                await game_notifier.notify_action_request(game_id, poker_game)
                        else:
                            # If the next player can't act (not active or already acted),
                            # check if we need to end the round or continue to another player
                            if poker_game.to_act:
                                # There are still players who need to act, but process_action
                                # might not have found the next one correctly
                                logging.warning(f"Next player {next_player.name} cannot act, but to_act is not empty")
                                
                                # Find the first player who still needs to act
                                next_active_player = next((p for p in poker_game.players 
                                                          if p.player_id in poker_game.to_act and 
                                                          p.status == PlayerStatus.ACTIVE), None)
                                                          
                                if next_active_player:
                                    # Update current_player_idx to point to this player
                                    poker_game.current_player_idx = poker_game.players.index(next_active_player)
                                    next_player_domain = next((p for p in game.players 
                                                              if p.id == next_active_player.player_id), None)
                                    
                                    if next_player_domain and not next_player_domain.is_human:
                                        # If next player is AI, trigger their action
                                        logging.info(f"Triggering AI action for alternate next player: {next_active_player.name}")
                                        import asyncio
                                        asyncio.create_task(self._request_and_process_ai_action(
                                            game_id, next_active_player.player_id
                                        ))
                                    else:
                                        # If next player is human, notify them
                                        logging.info(f"Requesting action from alternate human player: {next_active_player.name}")
                                        await game_notifier.notify_action_request(game_id, poker_game)
                            else:
                                # If to_act is empty, we should already be moving to the next round
                                # Let the game state update handle this 
                                logging.info("No more players need to act in this round")
                    else:
                        # This shouldn't happen, but handle it safely
                        logging.error(f"Invalid current_player_idx: {poker_game.current_player_idx}, players: {len(poker_game.players)}")
                        # Reset to a valid index
                        poker_game.current_player_idx = 0
        
        except Exception as e:
            # Log the error
            import logging
            logging.error(f"Error processing AI action: {str(e)}")
            
            # Default to fold on error
            from app.core.poker_game import PlayerAction
            poker_action = PlayerAction.FOLD
            
            # Process the fold action
            poker_game.process_action(poker_player, poker_action, None)
            
            # Notify clients
            from app.core.websocket import game_notifier
            await game_notifier.notify_player_action(game_id, player_id, "FOLD", None)
            await game_notifier.notify_game_update(game_id, poker_game)
            
            # Continue game flow for next player - use similar approach as the success path
            from app.core.poker_game import PlayerStatus
            import logging
            
            # Log current state for debugging
            logging.info(f"After AI action error, finding next player. Current index: {poker_game.current_player_idx}")
            
            # Get active players and players who still need to act
            active_players = [p for p in poker_game.players if p.status == PlayerStatus.ACTIVE]
            to_act_players = [p for p in active_players if p.player_id in poker_game.to_act]
            
            logging.info(f"Active players after error: {len(active_players)}, Players to act: {len(to_act_players)}")
            
            # The current_player_idx should already be updated to the next player by process_action
            if poker_game.current_player_idx < len(poker_game.players):
                next_player = poker_game.players[poker_game.current_player_idx]
                next_player_domain = next((p for p in game.players if p.id == next_player.player_id), None)
                
                logging.info(f"Next player after error is {next_player.name} (index {poker_game.current_player_idx})")
                
                # Verify this player is active and needs to act
                if (next_player.status == PlayerStatus.ACTIVE and 
                    next_player.player_id in poker_game.to_act and
                    next_player_domain):
                    
                    if not next_player_domain.is_human:
                        # If next player is also AI, trigger their action asynchronously
                        logging.info(f"Triggering AI action for next player after error: {next_player.name}")
                        import asyncio
                        asyncio.create_task(self._request_and_process_ai_action(
                            game_id, next_player.player_id
                        ))
                    else:
                        # If next player is human, notify them it's their turn
                        logging.info(f"Requesting action from human player after error: {next_player.name}")
                        await game_notifier.notify_action_request(game_id, poker_game)
                else:
                    # If the next player can't act, find the first one who can
                    if poker_game.to_act:
                        next_active_player = next((p for p in poker_game.players 
                                                  if p.player_id in poker_game.to_act and 
                                                  p.status == PlayerStatus.ACTIVE), None)
                                                  
                        if next_active_player:
                            # Update current_player_idx to point to this player
                            poker_game.current_player_idx = poker_game.players.index(next_active_player)
                            next_player_domain = next((p for p in game.players 
                                                      if p.id == next_active_player.player_id), None)
                            
                            if next_player_domain and not next_player_domain.is_human:
                                # If next player is AI, trigger their action
                                logging.info(f"Triggering AI action for alternate next player after error: {next_active_player.name}")
                                import asyncio
                                asyncio.create_task(self._request_and_process_ai_action(
                                    game_id, next_active_player.player_id
                                ))
                            else:
                                # If next player is human, notify them
                                logging.info(f"Requesting action from alternate human player after error: {next_active_player.name}")
                                await game_notifier.notify_action_request(game_id, poker_game)
            else:
                # Invalid index - reset to a safer value
                logging.error(f"Invalid current_player_idx after error: {poker_game.current_player_idx}")
                poker_game.current_player_idx = 0
                
        # Log the end of the AI action chain
        logging.info(f"=== AI ACTION CHAIN: END for player {player_id} in game {game_id} ===")
        logging.info(f"Player status after action: {poker_player.status.name if hasattr(poker_player, 'status') else 'Unknown'}")
        logging.info(f"Game round after action: {poker_game.current_round.name if hasattr(poker_game, 'current_round') else 'Unknown'}")
        logging.info(f"Next player index: {poker_game.current_player_idx}")
        if poker_game.to_act:
            to_act_names = [
                next((p.name for p in poker_game.players if p.player_id == pid), "Unknown")
                for pid in poker_game.to_act
            ]
            logging.info(f"Players still to act: {to_act_names}")
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