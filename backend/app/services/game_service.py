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
    BettingRound, PlayerAction, PlayerStatus, TournamentInfo, CashGameInfo
)
from app.repositories.in_memory import (
    GameRepository, UserRepository, ActionHistoryRepository, HandRepository,
    RepositoryFactory
)


class GameService:
    """
    Service for managing poker games.
    Implements game logic and coordinates data access.
    """
    
    def __init__(self):
        """Initialize the game service with repositories."""
        factory = RepositoryFactory.get_instance()
        self.game_repo = factory.get_repository(GameRepository)
        self.user_repo = factory.get_repository(UserRepository)
        self.action_repo = factory.get_repository(ActionHistoryRepository)
        self.hand_repo = factory.get_repository(HandRepository)
        self.poker_games: Dict[str, PokerGame] = {}
    
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
            small_blind = game.tournament_info.starting_small_blind
            big_blind = game.tournament_info.starting_big_blind
            ante = 0
            if game.tournament_info.ante_enabled and game.tournament_info.current_level >= game.tournament_info.ante_start_level:
                ante = big_blind // 4
        
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
        
        return hand
    
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
            
        # TODO: Implement the actual poker logic for processing actions
        # For now, just record the action
        
        # Create action history record
        action_history = ActionHistory(
            game_id=game_id,
            hand_id=game.current_hand.id,
            player_id=player_id,
            action=action,
            amount=amount,
            round=game.current_hand.current_round
        )
        
        # Save the action
        self.action_repo.create(action_history)
        
        # Add the action to the hand
        game.current_hand.actions.append(action_history)
        
        # Update the game
        self.game_repo.update(game)
        
        return game