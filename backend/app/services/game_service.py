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
            game.cash_game_info = CashGameInfo(
                buy_in=options.get("buy_in", 1000),
                min_bet=options.get("min_bet", 10),
                max_bet=options.get("max_bet"),
                ante=options.get("ante", 0),
                table_size=options.get("table_size", 6)
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
        position: Optional[int] = None
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
            
        Returns:
            Tuple of (updated game, added player)
            
        Raises:
            ValueError: If the game is not in WAITING status
            KeyError: If the game doesn't exist
        """
        game = self.game_repo.get(game_id)
        if not game:
            raise KeyError(f"Game {game_id} not found")
            
        if game.status != GameStatus.WAITING:
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
        
        # Set initial chips based on game type
        if game.type == GameType.CASH:
            player.chips = game.cash_game_info.buy_in
        else:  # Tournament
            player.chips = game.tournament_info.starting_chips
            
        # Add player to game
        game.players.append(player)
        
        # Update the game
        self.game_repo.update(game)
        
        return game, player
        
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
            else:  # Cash game
                sb = game.cash_game_info.min_bet // 2
                bb = game.cash_game_info.min_bet
                ante = game.cash_game_info.ante
                tournament_level = None
                
            # Create new poker game instance
            poker_game = PokerGame(
                small_blind=sb,
                big_blind=bb,
                ante=ante,
                game_id=game.id,
                hand_history_recorder=self.hand_history_recorder
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