# mypy: ignore-errors
"""
Tests for the poker hand evaluator.
"""

import pytest
from app.core.cards import Card, Suit, Rank, Hand
from app.core.hand_evaluator import HandEvaluator, HandRank


def test_high_card():
    """Test high card evaluation."""
    cards = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.DIAMONDS),
        Card(Rank.QUEEN, Suit.SPADES),
        Card(Rank.NINE, Suit.CLUBS),
        Card(Rank.SEVEN, Suit.HEARTS),
    }

    rank, kickers = HandEvaluator.evaluate(cards)

    assert rank == HandRank.HIGH_CARD
    assert kickers[0] == 14  # Ace


def test_one_pair():
    """Test one pair evaluation."""
    cards = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.DIAMONDS),
        Card(Rank.KING, Suit.SPADES),
        Card(Rank.QUEEN, Suit.CLUBS),
        Card(Rank.NINE, Suit.HEARTS),
    }

    rank, kickers = HandEvaluator.evaluate(cards)

    assert rank == HandRank.PAIR
    assert kickers[0] == 14  # Ace pair


def test_two_pair():
    """Test two pair evaluation."""
    cards = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.DIAMONDS),
        Card(Rank.KING, Suit.SPADES),
        Card(Rank.KING, Suit.CLUBS),
        Card(Rank.NINE, Suit.HEARTS),
    }

    rank, kickers = HandEvaluator.evaluate(cards)

    assert rank == HandRank.TWO_PAIR
    assert kickers[0] == 14  # Ace pair
    assert kickers[1] == 13  # King pair


def test_three_of_a_kind():
    """Test three of a kind evaluation."""
    cards = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.DIAMONDS),
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.KING, Suit.CLUBS),
        Card(Rank.NINE, Suit.HEARTS),
    }

    rank, kickers = HandEvaluator.evaluate(cards)

    assert rank == HandRank.THREE_OF_A_KIND
    assert kickers[0] == 14  # Ace triplet


def test_straight():
    """Test straight evaluation."""
    cards = {
        Card(Rank.TEN, Suit.HEARTS),
        Card(Rank.NINE, Suit.DIAMONDS),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.SEVEN, Suit.CLUBS),
        Card(Rank.SIX, Suit.HEARTS),
    }

    rank, kickers = HandEvaluator.evaluate(cards)

    assert rank == HandRank.STRAIGHT
    assert kickers[0] == 10  # Ten high straight


def test_flush():
    """Test flush evaluation."""
    cards = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.HEARTS),
        Card(Rank.TEN, Suit.HEARTS),
        Card(Rank.SEVEN, Suit.HEARTS),
        Card(Rank.THREE, Suit.HEARTS),
    }

    rank, kickers = HandEvaluator.evaluate(cards)

    assert rank == HandRank.FLUSH
    assert kickers[0] == 14  # Ace high flush


def test_full_house():
    """Test full house evaluation."""
    cards = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.DIAMONDS),
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.KING, Suit.CLUBS),
        Card(Rank.KING, Suit.HEARTS),
    }

    rank, kickers = HandEvaluator.evaluate(cards)

    assert rank == HandRank.FULL_HOUSE
    assert kickers[0] == 14  # Ace triplet
    assert kickers[1] == 13  # King pair


def test_four_of_a_kind():
    """Test four of a kind evaluation."""
    cards = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.DIAMONDS),
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.KING, Suit.HEARTS),
    }

    rank, kickers = HandEvaluator.evaluate(cards)

    assert rank == HandRank.FOUR_OF_A_KIND
    assert kickers[0] == 14  # Ace quad


def test_straight_flush():
    """Test straight flush evaluation."""
    cards = {
        Card(Rank.TEN, Suit.HEARTS),
        Card(Rank.NINE, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.HEARTS),
        Card(Rank.SEVEN, Suit.HEARTS),
        Card(Rank.SIX, Suit.HEARTS),
    }

    rank, kickers = HandEvaluator.evaluate(cards)

    assert rank == HandRank.STRAIGHT_FLUSH
    assert kickers[0] == 10  # Ten high straight flush


def test_royal_flush():
    """Test royal flush evaluation."""
    cards = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.HEARTS),
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.TEN, Suit.HEARTS),
    }

    rank, kickers = HandEvaluator.evaluate(cards)

    assert rank == HandRank.ROYAL_FLUSH
    assert kickers[0] == 14  # Ace high royal flush


def test_seven_card_hand():
    """Test evaluating the best 5-card hand from 7 cards."""
    cards = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.HEARTS),
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.TEN, Suit.HEARTS),
        Card(Rank.TWO, Suit.DIAMONDS),
        Card(Rank.THREE, Suit.CLUBS),
    }

    rank, kickers = HandEvaluator.evaluate(cards)

    assert rank == HandRank.ROYAL_FLUSH
    assert kickers[0] == 14  # Should find the royal flush among the 7 cards


def test_low_ace_straight():
    """Test A-5 straight (where Ace counts as 1)."""
    cards = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.TWO, Suit.DIAMONDS),
        Card(Rank.THREE, Suit.CLUBS),
        Card(Rank.FOUR, Suit.SPADES),
        Card(Rank.FIVE, Suit.HEARTS),
    }

    rank, kickers = HandEvaluator.evaluate(cards)

    assert rank == HandRank.STRAIGHT
    assert kickers[0] == 5  # Five high straight
