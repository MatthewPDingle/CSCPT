"""
Card representation and deck management for the poker engine.
"""
from enum import Enum, auto
from typing import List, Optional, Set
import random


class Suit(Enum):
    """Represents the four suits in a standard deck of cards."""
    CLUBS = auto()
    DIAMONDS = auto()
    HEARTS = auto()
    SPADES = auto()
    
    def __str__(self) -> str:
        """Return string representation of suit."""
        return self.name.capitalize()


class Rank(Enum):
    """Represents the 13 card ranks in a standard deck."""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14
    
    def __str__(self) -> str:
        """Return string representation of rank."""
        if self.value <= 10:
            return str(self.value)
        return self.name[0]


class Card:
    """Represents a single playing card with a rank and suit."""
    
    def __init__(self, rank: Rank, suit: Suit):
        """
        Initialize a card with a rank and suit.
        
        Args:
            rank: The card's rank (2-A)
            suit: The card's suit (clubs, diamonds, hearts, spades)
        """
        self.rank = rank
        self.suit = suit
    
    def __eq__(self, other: object) -> bool:
        """Check if two cards are equal."""
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self) -> int:
        """Generate hash for the card."""
        return hash((self.rank, self.suit))
    
    def __str__(self) -> str:
        """Return string representation of card."""
        return f"{self.rank}{self.suit.name[0]}"
    
    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"Card({self.rank}, {self.suit})"


class Deck:
    """Represents a standard 52-card deck."""
    
    def __init__(self):
        """Initialize a new deck with all 52 cards."""
        self.cards: List[Card] = []
        self.reset()
    
    def reset(self):
        """Reset the deck to a full 52-card deck."""
        self.cards = [
            Card(rank, suit)
            for suit in Suit
            for rank in Rank
        ]
    
    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)
    
    def draw(self) -> Optional[Card]:
        """
        Draw a card from the top of the deck.
        
        Returns:
            A card if the deck is not empty, None otherwise.
        """
        if not self.cards:
            return None
        return self.cards.pop()
    
    def __len__(self) -> int:
        """Return the number of cards left in the deck."""
        return len(self.cards)


class Hand:
    """Represents a poker hand (the cards held by a player)."""
    
    def __init__(self, cards: Optional[List[Card]] = None):
        """
        Initialize a hand with optional starting cards.
        
        Args:
            cards: Optional list of cards to start with
        """
        self.cards: Set[Card] = set(cards) if cards else set()
    
    def add_card(self, card: Card):
        """
        Add a card to the hand.
        
        Args:
            card: The card to add
        """
        self.cards.add(card)
    
    def clear(self):
        """Clear all cards from the hand."""
        self.cards.clear()
    
    def __len__(self) -> int:
        """Return the number of cards in the hand."""
        return len(self.cards)
    
    def __str__(self) -> str:
        """Return string representation of hand."""
        return " ".join(str(card) for card in sorted(
            self.cards, 
            key=lambda c: (c.rank.value, c.suit.value)
        ))