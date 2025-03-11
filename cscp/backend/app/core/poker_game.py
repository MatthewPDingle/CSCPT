"""
Core poker game logic including betting and game flow.
"""
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple
import random

from app.core.cards import Card, Deck, Hand
from app.core.hand_evaluator import HandEvaluator, HandRank


class BettingRound(Enum):
    """Represents the different betting rounds in Texas Hold'em."""
    PREFLOP = auto()
    FLOP = auto()
    TURN = auto()
    RIVER = auto()


class PlayerAction(Enum):
    """Represents possible player actions during betting."""
    FOLD = auto()
    CHECK = auto()
    CALL = auto()
    BET = auto()
    RAISE = auto()
    ALL_IN = auto()


class PlayerStatus(Enum):
    """Represents the current status of a player in the game."""
    ACTIVE = auto()  # Still in the hand
    FOLDED = auto()  # Folded this hand
    ALL_IN = auto()  # Has gone all-in
    OUT = auto()     # Out of the game (no chips left)


class Player:
    """Represents a player in the poker game."""
    
    def __init__(self, player_id: str, name: str, chips: int, position: int):
        """
        Initialize a player.
        
        Args:
            player_id: Unique identifier for the player
            name: Player's display name
            chips: Starting chip count
            position: Position at the table (0 = button, etc.)
        """
        self.player_id = player_id
        self.name = name
        self.chips = chips
        self.position = position
        self.hand = Hand()
        self.status = PlayerStatus.ACTIVE
        self.current_bet = 0
        self.total_bet = 0
    
    def bet(self, amount: int) -> int:
        """
        Place a bet, deducting from the player's chips.
        
        Args:
            amount: Amount to bet
            
        Returns:
            The actual amount bet (may be less if player doesn't have enough)
        """
        amount = min(amount, self.chips)
        self.chips -= amount
        self.current_bet += amount
        self.total_bet += amount
        
        if self.chips == 0:
            self.status = PlayerStatus.ALL_IN
            
        return amount
    
    def reset_for_new_hand(self):
        """Reset player state for a new hand."""
        self.hand.clear()
        if self.chips > 0:
            self.status = PlayerStatus.ACTIVE
        else:
            self.status = PlayerStatus.OUT
        self.current_bet = 0
        self.total_bet = 0
    
    def __str__(self) -> str:
        """Return string representation of player."""
        return f"{self.name} ({self.chips} chips)"


class PokerGame:
    """Manages a Texas Hold'em poker game."""
    
    def __init__(self, small_blind: int, big_blind: int):
        """
        Initialize a poker game.
        
        Args:
            small_blind: Small blind amount
            big_blind: Big blind amount
        """
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.deck = Deck()
        self.players: List[Player] = []
        self.community_cards: List[Card] = []
        self.pot = 0
        self.current_round = BettingRound.PREFLOP
        self.button_position = 0
        self.current_player_idx = 0
        self.current_bet = 0
        self.min_raise = big_blind
    
    def add_player(self, player_id: str, name: str, chips: int) -> Player:
        """
        Add a player to the game.
        
        Args:
            player_id: Unique identifier for the player
            name: Player's display name
            chips: Starting chip count
            
        Returns:
            The newly created Player object
        """
        position = len(self.players)
        player = Player(player_id, name, chips, position)
        self.players.append(player)
        return player
    
    def start_hand(self):
        """Start a new hand, dealing cards to players."""
        if len(self.players) < 2:
            raise ValueError("Need at least 2 players to start a hand")
            
        # Reset game state
        self.deck.reset()
        self.deck.shuffle()
        self.community_cards = []
        self.pot = 0
        self.current_round = BettingRound.PREFLOP
        self.current_bet = 0
        self.min_raise = self.big_blind
        
        # Reset players
        for player in self.players:
            player.reset_for_new_hand()
            
        # Deal two cards to each active player
        active_players = [p for p in self.players if p.status != PlayerStatus.OUT]
        for _ in range(2):
            for player in active_players:
                card = self.deck.draw()
                if card:
                    player.hand.add_card(card)
        
        # Set positions
        self._set_positions()
        
        # Post blinds
        self._post_blinds()
        
        # Set current player (player after big blind)
        self.current_player_idx = (self.button_position + 3) % len(active_players)
        if len(active_players) == 2:  # Heads-up
            self.current_player_idx = self.button_position  # Small blind acts first
    
    def _set_positions(self):
        """Assign positions to players based on the button position."""
        active_players = [p for p in self.players if p.status != PlayerStatus.OUT]
        
        for i, player in enumerate(active_players):
            position = (i - self.button_position) % len(active_players)
            player.position = position
    
    def _post_blinds(self):
        """Post the small and big blinds."""
        active_players = [p for p in self.players if p.status != PlayerStatus.OUT]
        
        # Small blind
        sb_pos = (self.button_position + 1) % len(active_players)
        sb_player = active_players[sb_pos]
        sb_amount = sb_player.bet(self.small_blind)
        self.pot += sb_amount
        
        # Big blind
        bb_pos = (self.button_position + 2) % len(active_players)
        bb_player = active_players[bb_pos]
        bb_amount = bb_player.bet(self.big_blind)
        self.pot += bb_amount
        
        self.current_bet = self.big_blind
    
    def deal_flop(self):
        """Deal the flop (first three community cards)."""
        if self.current_round != BettingRound.PREFLOP:
            raise ValueError("Cannot deal flop: incorrect betting round")
            
        # Burn a card
        self.deck.draw()
        
        # Deal three cards
        for _ in range(3):
            card = self.deck.draw()
            if card:
                self.community_cards.append(card)
                
        self.current_round = BettingRound.FLOP
        self._reset_betting_round()
    
    def deal_turn(self):
        """Deal the turn (fourth community card)."""
        if self.current_round != BettingRound.FLOP:
            raise ValueError("Cannot deal turn: incorrect betting round")
            
        # Burn a card
        self.deck.draw()
        
        # Deal one card
        card = self.deck.draw()
        if card:
            self.community_cards.append(card)
            
        self.current_round = BettingRound.TURN
        self._reset_betting_round()
    
    def deal_river(self):
        """Deal the river (fifth community card)."""
        if self.current_round != BettingRound.TURN:
            raise ValueError("Cannot deal river: incorrect betting round")
            
        # Burn a card
        self.deck.draw()
        
        # Deal one card
        card = self.deck.draw()
        if card:
            self.community_cards.append(card)
            
        self.current_round = BettingRound.RIVER
        self._reset_betting_round()
    
    def _reset_betting_round(self):
        """Reset betting for a new round."""
        self.current_bet = 0
        self.min_raise = self.big_blind
        
        # Reset player current bets
        for player in self.players:
            player.current_bet = 0
            
        # Set first player to act (first active player after button)
        active_players = [p for p in self.players 
                          if p.status in {PlayerStatus.ACTIVE, PlayerStatus.ALL_IN}]
        self.current_player_idx = (self.button_position + 1) % len(active_players)
        
    def get_valid_actions(self, player: Player) -> List[Tuple[PlayerAction, int, int]]:
        """
        Get valid actions for the current player.
        
        Args:
            player: The player to check actions for
            
        Returns:
            List of tuples containing (action, min_amount, max_amount)
        """
        if player.status != PlayerStatus.ACTIVE:
            return []
            
        valid_actions = []
        
        # Fold is always valid
        valid_actions.append((PlayerAction.FOLD, 0, 0))
        
        call_amount = self.current_bet - player.current_bet
        
        if call_amount == 0:
            # Check is valid when no bet to call
            valid_actions.append((PlayerAction.CHECK, 0, 0))
        else:
            # Call is valid when there's a bet to call
            call_amount = min(call_amount, player.chips)
            valid_actions.append((PlayerAction.CALL, call_amount, call_amount))
        
        if player.chips > call_amount:
            # Bet/Raise is valid when player has chips beyond the call amount
            min_bet = self.current_bet + self.min_raise
            if self.current_bet == 0:
                # Bet (no previous bet)
                min_bet = self.big_blind
                valid_actions.append((PlayerAction.BET, min_bet, player.chips))
            else:
                # Raise (increasing previous bet)
                min_raise_amount = min(self.min_raise, player.chips - call_amount)
                valid_actions.append((
                    PlayerAction.RAISE, 
                    call_amount + min_raise_amount, 
                    player.chips
                ))
        
        # All-in is always valid
        valid_actions.append((PlayerAction.ALL_IN, player.chips, player.chips))
        
        return valid_actions
    
    def evaluate_hands(self) -> Dict[Player, Tuple[HandRank, List[int]]]:
        """
        Evaluate all active player hands.
        
        Returns:
            Dictionary mapping each player to their hand evaluation
        """
        results = {}
        
        for player in self.players:
            if player.status in {PlayerStatus.ACTIVE, PlayerStatus.ALL_IN}:
                # Combine player's hole cards with community cards
                all_cards = set(player.hand.cards) | set(self.community_cards)
                hand_rank, kickers = HandEvaluator.evaluate(all_cards)
                results[player] = (hand_rank, kickers)
                
        return results
    
    def move_button(self):
        """Move the button to the next active player for the next hand."""
        active_players = [p for p in self.players if p.status != PlayerStatus.OUT]
        if not active_players:
            return
            
        self.button_position = (self.button_position + 1) % len(active_players)