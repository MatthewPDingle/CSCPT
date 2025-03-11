"""
Hand evaluation logic for poker hands.
"""
from enum import Enum, auto
from typing import Dict, List, Set, Tuple
from collections import Counter

from app.core.cards import Card, Rank, Suit


class HandRank(Enum):
    """Represents the ranking of poker hands from lowest to highest."""
    HIGH_CARD = auto()
    PAIR = auto()
    TWO_PAIR = auto()
    THREE_OF_A_KIND = auto()
    STRAIGHT = auto()
    FLUSH = auto()
    FULL_HOUSE = auto()
    FOUR_OF_A_KIND = auto()
    STRAIGHT_FLUSH = auto()
    ROYAL_FLUSH = auto()


class HandEvaluator:
    """Evaluates poker hands to determine their ranking."""
    
    @staticmethod
    def evaluate(cards: Set[Card]) -> Tuple[HandRank, List[int]]:
        """
        Evaluate a set of cards and return its poker hand ranking.
        
        Args:
            cards: A set of cards (5-7 cards typically)
            
        Returns:
            A tuple containing:
                1. The hand rank (e.g., PAIR, FLUSH)
                2. A list of values for tie-breaking, with the most important first
        """
        if len(cards) < 5:
            raise ValueError("Need at least 5 cards to evaluate a poker hand")
            
        # Check for flush
        suits = [card.suit for card in cards]
        suit_counts = Counter(suits)
        flush_suit = next((suit for suit, count in suit_counts.items() 
                          if count >= 5), None)
        
        flush_cards = None
        if flush_suit:
            flush_cards = [card for card in cards if card.suit == flush_suit]
            
        # Check for straight
        ranks = sorted([card.rank.value for card in cards], reverse=True)
        unique_ranks = sorted(set(ranks), reverse=True)
        
        # Special case for A-5 straight (Ace counts as 1)
        if set([14, 13, 12, 11, 10]).issubset(set(ranks)):
            straight_high = 14  # Royal straight
        elif set([14, 5, 4, 3, 2]).issubset(set(ranks)):
            straight_high = 5   # A-5 straight (Ace counts as 1)
        else:
            # Check for regular straights
            straight_high = None
            for i in range(len(unique_ranks) - 4):
                if unique_ranks[i] - unique_ranks[i+4] == 4:
                    straight_high = unique_ranks[i]
                    break
        
        # Check for straight flush
        straight_flush = False
        royal_flush = False
        if flush_cards and straight_high:
            flush_ranks = sorted([card.rank.value for card in flush_cards], reverse=True)
            flush_unique_ranks = sorted(set(flush_ranks), reverse=True)
            
            # Check for royal flush
            if set([14, 13, 12, 11, 10]).issubset(set(flush_ranks)):
                straight_flush = True
                royal_flush = True
                straight_high = 14
            # Check for A-5 straight flush
            elif set([14, 5, 4, 3, 2]).issubset(set(flush_ranks)):
                straight_flush = True
                straight_high = 5
            else:
                # Check for regular straight flush
                for i in range(len(flush_unique_ranks) - 4):
                    if flush_unique_ranks[i] - flush_unique_ranks[i+4] == 4:
                        straight_flush = True
                        straight_high = flush_unique_ranks[i]
                        break
        
        # Count rank occurrences
        rank_counts = Counter(card.rank.value for card in cards)
        
        # Find groups (pairs, three of a kind, etc.)
        quads = [rank for rank, count in rank_counts.items() if count == 4]
        triplets = [rank for rank, count in rank_counts.items() if count == 3]
        pairs = [rank for rank, count in rank_counts.items() if count == 2]
        
        # Sort by rank value (highest first)
        quads.sort(reverse=True)
        triplets.sort(reverse=True)
        pairs.sort(reverse=True)
        
        # Create a list of remaining ranks for kickers
        all_grouped_ranks = quads + triplets + pairs
        kickers = sorted([r for r in ranks if r not in all_grouped_ranks], reverse=True)
        
        # Determine hand rank and create tie-breaker list
        if royal_flush:
            return HandRank.ROYAL_FLUSH, [14]
        elif straight_flush:
            return HandRank.STRAIGHT_FLUSH, [straight_high]
        elif quads:
            return HandRank.FOUR_OF_A_KIND, quads + kickers[:1]
        elif triplets and pairs:
            return HandRank.FULL_HOUSE, [triplets[0], pairs[0] if len(pairs) > 0 else triplets[1]]
        elif flush_suit:
            return HandRank.FLUSH, sorted([card.rank.value for card in flush_cards], reverse=True)[:5]
        elif straight_high:
            return HandRank.STRAIGHT, [straight_high]
        elif triplets:
            return HandRank.THREE_OF_A_KIND, triplets + kickers[:2]
        elif len(pairs) >= 2:
            return HandRank.TWO_PAIR, pairs[:2] + kickers[:1]
        elif pairs:
            return HandRank.PAIR, pairs + kickers[:3]
        else:
            return HandRank.HIGH_CARD, ranks[:5]