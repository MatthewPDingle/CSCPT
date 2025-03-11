"""
Tests for the card representation and deck management.
"""
import pytest
from app.core.cards import Card, Suit, Rank, Deck, Hand


def test_card_creation():
    """Test creating a card with a specific rank and suit."""
    card = Card(Rank.ACE, Suit.HEARTS)
    assert card.rank == Rank.ACE
    assert card.suit == Suit.HEARTS


def test_card_equality():
    """Test card equality comparison."""
    card1 = Card(Rank.ACE, Suit.HEARTS)
    card2 = Card(Rank.ACE, Suit.HEARTS)
    card3 = Card(Rank.KING, Suit.HEARTS)
    
    assert card1 == card2
    assert card1 != card3
    assert card2 != card3


def test_card_string_representation():
    """Test string representation of cards."""
    card = Card(Rank.ACE, Suit.HEARTS)
    assert str(card) == "AH"
    
    card = Card(Rank.TEN, Suit.CLUBS)
    assert str(card) == "10C"


def test_deck_creation():
    """Test creating a new deck."""
    deck = Deck()
    assert len(deck) == 52
    
    # Ensure all cards are unique
    cards_set = set(deck.cards)
    assert len(cards_set) == 52


def test_deck_shuffle():
    """Test deck shuffling."""
    deck1 = Deck()
    deck2 = Deck()
    
    # Before shuffling, decks should be in the same order
    assert deck1.cards == deck2.cards
    
    # After shuffling one deck, they should differ
    deck1.shuffle()
    assert deck1.cards != deck2.cards


def test_deck_draw():
    """Test drawing cards from a deck."""
    deck = Deck()
    initial_count = len(deck)
    
    # Draw a card
    card = deck.draw()
    assert card is not None
    assert isinstance(card, Card)
    assert len(deck) == initial_count - 1
    
    # Draw all remaining cards
    cards = []
    while len(deck) > 0:
        cards.append(deck.draw())
    
    # Deck should be empty
    assert len(deck) == 0
    assert deck.draw() is None


def test_deck_reset():
    """Test resetting a deck after drawing cards."""
    deck = Deck()
    
    # Draw some cards
    for _ in range(10):
        deck.draw()
    
    assert len(deck) == 42
    
    # Reset and check
    deck.reset()
    assert len(deck) == 52


def test_hand_creation():
    """Test creating a hand."""
    # Empty hand
    hand = Hand()
    assert len(hand) == 0
    
    # Hand with cards
    cards = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.HEARTS)
    ]
    hand = Hand(cards)
    assert len(hand) == 2


def test_hand_add_card():
    """Test adding a card to a hand."""
    hand = Hand()
    card = Card(Rank.ACE, Suit.HEARTS)
    
    hand.add_card(card)
    assert len(hand) == 1
    assert card in hand.cards


def test_hand_clear():
    """Test clearing a hand."""
    cards = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.HEARTS)
    ]
    hand = Hand(cards)
    assert len(hand) == 2
    
    hand.clear()
    assert len(hand) == 0


def test_hand_string_representation():
    """Test string representation of a hand."""
    cards = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.HEARTS)
    ]
    hand = Hand(cards)
    
    assert str(hand) == "KH AH"  # Should be sorted by rank