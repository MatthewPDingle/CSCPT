# Chip Swinger Championship Poker Trainer
## Poker Engine Design

This document outlines the design of the poker engine that powers the Chip Swinger Championship Poker Trainer. The poker engine is responsible for enforcing game rules, evaluating hands, and managing game flow.

## Core Components

### 1. Card Representation

```python
class Card:
    """Represents a single playing card."""
    
    # Suits
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3
    
    # Values
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
    
    def __init__(self, value, suit):
        self.value = value
        self.suit = suit
    
    def __str__(self):
        """Returns a string representation of the card."""
        values = {
            2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
            10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'
        }
        suits = {0: 'c', 1: 'd', 2: 'h', 3: 's'}
        return f"{values[self.value]}{suits[self.suit]}"
```

### 2. Deck Management

```python
class Deck:
    """Represents a deck of 52 playing cards."""
    
    def __init__(self):
        """Creates a new deck of 52 cards."""
        self.cards = []
        self.reset()
    
    def reset(self):
        """Resets the deck to a full 52-card state."""
        self.cards = []
        for suit in range(4):
            for value in range(2, 15):
                self.cards.append(Card(value, suit))
    
    def shuffle(self):
        """Shuffles the cards in the deck."""
        random.shuffle(self.cards)
    
    def deal(self, num_cards=1):
        """Deals a specified number of cards from the deck."""
        if num_cards > len(self.cards):
            raise ValueError("Not enough cards left in the deck")
        
        dealt_cards = []
        for _ in range(num_cards):
            dealt_cards.append(self.cards.pop())
        
        return dealt_cards if num_cards > 1 else dealt_cards[0]
```

### 3. Hand Evaluation

```python
class HandEvaluator:
    """Evaluates poker hands to determine their rank."""
    
    # Hand ranks
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    
    @staticmethod
    def evaluate_hand(hole_cards, community_cards):
        """
        Evaluates the best 5-card hand from the player's hole cards
        and the community cards.
        
        Args:
            hole_cards: List of 2 Card objects (player's private cards)
            community_cards: List of up to 5 Card objects (shared cards)
            
        Returns:
            Tuple of (hand_rank, hand_value, best_hand)
            - hand_rank: Integer representing the hand type (e.g., PAIR, FLUSH)
            - hand_value: Integer score for comparing hands of the same rank
            - best_hand: List of 5 Card objects representing the best hand
        """
        all_cards = hole_cards + community_cards
        
        # Check for flush
        flush_suit = HandEvaluator._check_flush(all_cards)
        
        # Check for straight
        straight_high_card = HandEvaluator._check_straight(all_cards)
        
        # Check for straight flush
        if flush_suit is not None and straight_high_card is not None:
            flush_cards = [card for card in all_cards if card.suit == flush_suit]
            straight_flush_high_card = HandEvaluator._check_straight(flush_cards)
            
            if straight_flush_high_card is not None:
                # We have a straight flush
                best_hand = HandEvaluator._get_straight_cards(flush_cards, straight_flush_high_card)
                return (HandEvaluator.STRAIGHT_FLUSH, straight_flush_high_card, best_hand)
        
        # Count card frequencies
        card_counts = HandEvaluator._count_cards(all_cards)
        
        # Check for four of a kind
        for value, count in card_counts.items():
            if count == 4:
                quads = [card for card in all_cards if card.value == value]
                kickers = [card for card in all_cards if card.value != value]
                kickers.sort(key=lambda card: card.value, reverse=True)
                best_hand = quads + [kickers[0]]
                return (HandEvaluator.FOUR_OF_A_KIND, value, best_hand)
        
        # Check for full house
        three_value = None
        pair_value = None
        
        for value, count in card_counts.items():
            if count == 3 and (three_value is None or value > three_value):
                three_value = value
            elif count >= 2 and (pair_value is None or value > pair_value):
                pair_value = value
        
        if three_value is not None and pair_value is not None:
            trips = [card for card in all_cards if card.value == three_value]
            pair = [card for card in all_cards if card.value == pair_value]
            best_hand = trips + pair[:2]
            return (HandEvaluator.FULL_HOUSE, three_value * 100 + pair_value, best_hand)
        
        # Check for flush
        if flush_suit is not None:
            flush_cards = [card for card in all_cards if card.suit == flush_suit]
            flush_cards.sort(key=lambda card: card.value, reverse=True)
            best_hand = flush_cards[:5]
            return (HandEvaluator.FLUSH, HandEvaluator._calculate_high_card_value(best_hand), best_hand)
        
        # Check for straight
        if straight_high_card is not None:
            best_hand = HandEvaluator._get_straight_cards(all_cards, straight_high_card)
            return (HandEvaluator.STRAIGHT, straight_high_card, best_hand)
        
        # Check for three of a kind
        for value, count in card_counts.items():
            if count == 3:
                trips = [card for card in all_cards if card.value == value]
                kickers = [card for card in all_cards if card.value != value]
                kickers.sort(key=lambda card: card.value, reverse=True)
                best_hand = trips + kickers[:2]
                return (HandEvaluator.THREE_OF_A_KIND, value, best_hand)
        
        # Check for two pair
        pairs = [(value, count) for value, count in card_counts.items() if count >= 2]
        pairs.sort(reverse=True)
        
        if len(pairs) >= 2:
            high_pair_value = pairs[0][0]
            low_pair_value = pairs[1][0]
            
            high_pair = [card for card in all_cards if card.value == high_pair_value]
            low_pair = [card for card in all_cards if card.value == low_pair_value]
            
            kickers = [card for card in all_cards 
                      if card.value != high_pair_value and card.value != low_pair_value]
            kickers.sort(key=lambda card: card.value, reverse=True)
            
            best_hand = high_pair[:2] + low_pair[:2] + [kickers[0]]
            return (HandEvaluator.TWO_PAIR, high_pair_value * 100 + low_pair_value, best_hand)
        
        # Check for one pair
        for value, count in card_counts.items():
            if count == 2:
                pair = [card for card in all_cards if card.value == value]
                kickers = [card for card in all_cards if card.value != value]
                kickers.sort(key=lambda card: card.value, reverse=True)
                best_hand = pair + kickers[:3]
                return (HandEvaluator.PAIR, value, best_hand)
        
        # High card
        all_cards.sort(key=lambda card: card.value, reverse=True)
        best_hand = all_cards[:5]
        return (HandEvaluator.HIGH_CARD, HandEvaluator._calculate_high_card_value(best_hand), best_hand)
    
    @staticmethod
    def _check_flush(cards):
        """Checks if there is a flush and returns the suit if found."""
        suit_counts = {}
        for card in cards:
            suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
            if suit_counts[card.suit] >= 5:
                return card.suit
        return None
    
    @staticmethod
    def _check_straight(cards):
        """
        Checks if there is a straight and returns the high card value if found.
        Handles the special case where Ace can be used as a low card (A-5 straight).
        """
        if len(cards) < 5:
            return None
            
        values = set(card.value for card in cards)
        
        # Check for A-5 straight
        if (14 in values and  # Ace
            2 in values and
            3 in values and
            4 in values and
            5 in values):
            return 5  # 5-high straight
        
        # Check for regular straights
        for high_card in range(14, 4, -1):
            if all(high_card - i in values for i in range(5)):
                return high_card
                
        return None
    
    @staticmethod
    def _count_cards(cards):
        """Counts the occurrences of each card value."""
        counts = {}
        for card in cards:
            counts[card.value] = counts.get(card.value, 0) + 1
        return counts
    
    @staticmethod
    def _calculate_high_card_value(cards):
        """
        Calculates a unique value for comparing high card hands.
        The value is calculated as a base-15 number where each digit
        represents the value of one card in the hand.
        """
        value = 0
        multiplier = 1
        
        sorted_cards = sorted(cards, key=lambda card: card.value, reverse=True)
        
        for card in sorted_cards:
            value += card.value * multiplier
            multiplier *= 15
            
        return value
    
    @staticmethod
    def _get_straight_cards(cards, high_card):
        """Returns the 5 cards that form a straight with the given high card."""
        if high_card == 5:  # A-5 straight
            # Find the lowest card of each required value
            result = []
            for value in [14, 5, 4, 3, 2]:  # Ace, 5, 4, 3, 2
                candidates = [card for card in cards if card.value == value]
                if candidates:
                    result.append(candidates[0])
            return result
        else:
            result = []
            for value in range(high_card, high_card - 5, -1):
                candidates = [card for card in cards if card.value == value]
                if candidates:
                    result.append(candidates[0])
            return result
```

### 4. Player Management

```python
class Player:
    """Represents a player in the poker game."""
    
    def __init__(self, player_id, name, stack, seat):
        """Initialize a new player."""
        self.player_id = player_id
        self.name = name
        self.stack = stack
        self.seat = seat
        self.hole_cards = []
        self.bet = 0
        self.total_bet = 0
        self.folded = False
        self.all_in = False
        self.sitting_out = False
        self.is_dealer = False
        self.is_small_blind = False
        self.is_big_blind = False
        self.has_acted = False
    
    def reset_for_new_hand(self):
        """Reset player state for a new hand."""
        self.hole_cards = []
        self.bet = 0
        self.total_bet = 0
        self.folded = False
        self.all_in = False
        self.has_acted = False
        self.is_dealer = False
        self.is_small_blind = False
        self.is_big_blind = False
    
    def deal_card(self, card):
        """Deal a card to the player."""
        self.hole_cards.append(card)
    
    def place_bet(self, amount):
        """
        Place a bet for the player.
        
        Args:
            amount: The amount to bet
            
        Returns:
            The actual amount bet (may be less if player doesn't have enough chips)
        """
        amount_to_call = min(amount, self.stack)
        self.stack -= amount_to_call
        self.bet += amount_to_call
        self.total_bet += amount_to_call
        
        if self.stack == 0:
            self.all_in = True
            
        return amount_to_call
    
    def fold_hand(self):
        """Fold the player's hand."""
        self.folded = True
    
    def collect_winnings(self, amount):
        """Add winnings to the player's stack."""
        self.stack += amount
```

### 5. Pot Management

```python
class Pot:
    """Manages the main pot and side pots in a poker game."""
    
    def __init__(self):
        """Initialize an empty pot."""
        self.pots = [{"amount": 0, "eligible_players": set()}]
    
    def add_to_pot(self, amount, player_id):
        """
        Add chips to the pot from a player.
        
        Args:
            amount: Amount to add
            player_id: ID of the player contributing
        """
        main_pot = self.pots[0]
        main_pot["amount"] += amount
        main_pot["eligible_players"].add(player_id)
    
    def create_side_pots(self, players):
        """
        Create side pots based on all-in players.
        
        Args:
            players: List of Player objects
        """
        # Reset pots
        self.pots = [{"amount": 0, "eligible_players": set()}]
        
        # Sort players by total bet (lowest first)
        players_by_bet = sorted([p for p in players if not p.folded], 
                               key=lambda p: p.total_bet)
        
        previous_bet = 0
        
        for i, player in enumerate(players_by_bet):
            if player.total_bet > previous_bet:
                # Calculate contribution to this pot from each player
                bet_size = player.total_bet - previous_bet
                
                # All players who haven't folded and have bet this much are eligible
                eligible_players = set(p.player_id for p in players_by_bet[i:] if not p.folded)
                
                # Calculate pot amount
                pot_amount = bet_size * len(eligible_players)
                
                # Create the side pot
                if pot_amount > 0:
                    self.pots.append({
                        "amount": pot_amount,
                        "eligible_players": eligible_players
                    })
                
                previous_bet = player.total_bet
    
    def total(self):
        """Returns the total amount in all pots."""
        return sum(pot["amount"] for pot in self.pots)
    
    def award_pot(self, pot_index, player_id, amount):
        """
        Award a part of a pot to a player.
        
        Args:
            pot_index: Index of the pot to award
            player_id: ID of the player to award the pot to
            amount: Amount to award
        """
        pot = self.pots[pot_index]
        if player_id in pot["eligible_players"]:
            pot["amount"] -= amount
```

### 6. Game State Management

```python
class GameState:
    """Manages the state of a poker game."""
    
    # Game phases
    WAITING = 0
    PREFLOP = 1
    FLOP = 2
    TURN = 3
    RIVER = 4
    SHOWDOWN = 5
    
    def __init__(self, game_id, table_size, blinds, buy_in):
        """Initialize a new game state."""
        self.game_id = game_id
        self.table_size = table_size
        self.blinds = blinds
        self.min_buy_in = buy_in
        self.max_buy_in = buy_in * 10
        
        self.players = {}
        self.seats = [None] * table_size
        self.deck = Deck()
        self.community_cards = []
        self.pot = Pot()
        
        self.dealer_position = 0
        self.small_blind_position = 1
        self.big_blind_position = 2
        self.current_position = None
        self.last_aggressive_position = None
        
        self.phase = GameState.WAITING
        self.current_bet = 0
        self.min_raise = blinds["big"]
    
    def add_player(self, player_id, name, stack, seat):
        """
        Add a player to the game.
        
        Args:
            player_id: Unique ID for the player
            name: Display name for the player
            stack: Starting chip count
            seat: Seat position at the table (0-indexed)
            
        Returns:
            True if player was added successfully, False otherwise
        """
        if seat < 0 or seat >= self.table_size:
            return False
            
        if self.seats[seat] is not None:
            return False
            
        if stack < self.min_buy_in or stack > self.max_buy_in:
            return False
            
        player = Player(player_id, name, stack, seat)
        self.players[player_id] = player
        self.seats[seat] = player_id
        
        return True
    
    def remove_player(self, player_id):
        """Remove a player from the game."""
        if player_id not in self.players:
            return False
            
        player = self.players[player_id]
        self.seats[player.seat] = None
        del self.players[player_id]
        
        return True
    
    def start_hand(self):
        """Start a new hand of poker."""
        # Ensure we have at least 2 players
        active_players = [p for p in self.players.values() if not p.sitting_out]
        if len(active_players) < 2:
            return False
            
        # Reset game state
        self.deck = Deck()
        self.deck.shuffle()
        self.community_cards = []
        self.pot = Pot()
        
        for player in self.players.values():
            player.reset_for_new_hand()
            
        # Set dealer button and blinds
        self._advance_dealer_position()
        self._set_blinds()
        
        # Deal hole cards
        for player in active_players:
            player.deal_card(self.deck.deal())
            player.deal_card(self.deck.deal())
            
        # Set initial bet and position
        self.current_bet = self.blinds["big"]
        self.min_raise = self.blinds["big"]
        self.phase = GameState.PREFLOP
        self._advance_action()
        
        return True
    
    def process_player_action(self, player_id, action, amount=0):
        """
        Process a player's action in the game.
        
        Args:
            player_id: ID of the player taking action
            action: String - "fold", "check", "call", "bet", "raise"
            amount: Amount for bet or raise (if applicable)
            
        Returns:
            True if action was processed successfully, False otherwise
        """
        if self.current_position is None or self.seats[self.current_position] != player_id:
            return False
            
        player = self.players[player_id]
        
        if player.folded or player.all_in:
            return False
            
        # Handle each action type
        if action == "fold":
            player.fold_hand()
        
        elif action == "check":
            if self.current_bet > player.bet:
                return False  # Can't check if there's a bet to call
            player.has_acted = True
        
        elif action == "call":
            amount_to_call = self.current_bet - player.bet
            if amount_to_call > 0:
                actual_bet = player.place_bet(amount_to_call)
                self.pot.add_to_pot(actual_bet, player_id)
            player.has_acted = True
        
        elif action == "bet":
            if self.current_bet > 0:
                return False  # Can't bet if there's already a bet (should raise)
                
            if amount < self.min_raise:
                return False  # Bet must be at least min_raise
                
            player.place_bet(amount)
            self.pot.add_to_pot(amount, player_id)
            self.current_bet = amount
            self.min_raise = amount
            self.last_aggressive_position = self.current_position
            player.has_acted = True
        
        elif action == "raise":
            if amount < self.current_bet + self.min_raise:
                return False  # Raise must be at least min_raise more than current bet
                
            raise_amount = amount - player.bet
            player.place_bet(raise_amount)
            self.pot.add_to_pot(raise_amount, player_id)
            self.current_bet = amount
            self.min_raise = amount - self.current_bet
            self.last_aggressive_position = self.current_position
            
            # Reset action for all players since there was a raise
            for p in self.players.values():
                if not p.folded and not p.all_in and p.player_id != player_id:
                    p.has_acted = False
                    
            player.has_acted = True
        
        else:
            return False  # Invalid action
            
        # Check if hand is over
        if self._is_hand_over():
            return self._end_hand()
            
        # Otherwise, move to next player
        self._advance_action()
        
        # Check if we need to move to next street
        if self._is_street_over():
            self._advance_street()
            
        return True
    
    def _advance_dealer_position(self):
        """Advance the dealer position to the next active player."""
        active_seats = [i for i, pid in enumerate(self.seats) 
                      if pid is not None and not self.players[pid].sitting_out]
                      
        if not active_seats:
            return
            
        # Find next active seat after current dealer
        next_pos = (self.dealer_position + 1) % self.table_size
        while next_pos != self.dealer_position:
            if next_pos in active_seats:
                self.dealer_position = next_pos
                break
            next_pos = (next_pos + 1) % self.table_size
    
    def _set_blinds(self):
        """Set the small and big blind positions and collect blinds."""
        active_seats = [i for i, pid in enumerate(self.seats) 
                      if pid is not None and not self.players[pid].sitting_out]
                      
        if len(active_seats) < 2:
            return
            
        # Set dealer
        dealer_id = self.seats[self.dealer_position]
        if dealer_id:
            self.players[dealer_id].is_dealer = True
            
        # Set small blind
        sb_pos = (self.dealer_position + 1) % self.table_size
        while self.seats[sb_pos] is None or self.players[self.seats[sb_pos]].sitting_out:
            sb_pos = (sb_pos + 1) % self.table_size
            
        self.small_blind_position = sb_pos
        sb_player_id = self.seats[sb_pos]
        self.players[sb_player_id].is_small_blind = True
        sb_amount = self.players[sb_player_id].place_bet(self.blinds["small"])
        self.pot.add_to_pot(sb_amount, sb_player_id)
        
        # Set big blind
        bb_pos = (sb_pos + 1) % self.table_size
        while self.seats[bb_pos] is None or self.players[self.seats[bb_pos]].sitting_out:
            bb_pos = (bb_pos + 1) % self.table_size
            
        self.big_blind_position = bb_pos
        bb_player_id = self.seats[bb_pos]
        self.players[bb_player_id].is_big_blind = True
        bb_amount = self.players[bb_player_id].place_bet(self.blinds["big"])
        self.pot.add_to_pot(bb_amount, bb_player_id)
        
        # Action starts after the big blind
        self.last_aggressive_position = bb_pos
    
    def _advance_action(self):
        """Advance action to the next player who can act."""
        if self.current_position is None:
            if self.phase == GameState.PREFLOP:
                # Preflop: action starts after BB
                self.current_position = (self.big_blind_position + 1) % self.table_size
            else:
                # Postflop: action starts with SB
                self.current_position = self.small_blind_position
        else:
            self.current_position = (self.current_position + 1) % self.table_size
            
        # Skip inactive players or those who can't act
        while True:
            player_id = self.seats[self.current_position]
            
            if player_id is None:
                # Empty seat
                self.current_position = (self.current_position + 1) % self.table_size
                continue
                
            player = self.players[player_id]
            
            if player.sitting_out or player.folded or player.all_in:
                # Player can't act
                self.current_position = (self.current_position + 1) % self.table_size
                continue
                
            if player.has_acted and self.current_position == self.last_aggressive_position:
                # We've gone all the way around
                self._advance_street()
                continue
                
            # Found a player who can act
            break
    
    def _is_street_over(self):
        """Check if the current betting round is over."""
        active_players = [p for p in self.players.values() 
                        if not p.folded and not p.sitting_out and not p.all_in]
                        
        # If everyone has acted and the bets are matched, or everyone but one has folded
        all_acted = all(p.has_acted for p in active_players)
        bets_matched = all(p.bet == self.current_bet for p in active_players)
        
        return all_acted and bets_matched
    
    def _advance_street(self):
        """Advance to the next betting street."""
        # Reset player bets for the new street
        for player in self.players.values():
            player.bet = 0
            player.has_acted = False
            
        self.current_bet = 0
        self.min_raise = self.blinds["big"]
        
        if self.phase == GameState.PREFLOP:
            # Deal flop
            self.community_cards.extend(self.deck.deal(3))
            self.phase = GameState.FLOP
        
        elif self.phase == GameState.FLOP:
            # Deal turn
            self.community_cards.append(self.deck.deal())
            self.phase = GameState.TURN
        
        elif self.phase == GameState.TURN:
            # Deal river
            self.community_cards.append(self.deck.deal())
            self.phase = GameState.RIVER
        
        elif self.phase == GameState.RIVER:
            # Go to showdown
            self.phase = GameState.SHOWDOWN
            return self._handle_showdown()
            
        # Set current position to first active player after dealer
        self.current_position = self.small_blind_position
        self._advance_action()
    
    def _is_hand_over(self):
        """Check if the hand is over."""
        active_players = [p for p in self.players.values() 
                        if not p.folded and not p.sitting_out]
                        
        return len(active_players) == 1 or self.phase == GameState.SHOWDOWN
    
    def _end_hand(self):
        """End the current hand and determine winners."""
        active_players = [p for p in self.players.values() 
                        if not p.folded and not p.sitting_out]
                        
        if len(active_players) == 1:
            # Everyone folded except one player
            winner = active_players[0]
            winner.collect_winnings(self.pot.total())
            return True
            
        return self._handle_showdown()
    
    def _handle_showdown(self):
        """Handle the showdown at the end of a hand."""
        # Create side pots based on all-in players
        self.pot.create_side_pots(list(self.players.values()))
        
        # Evaluate each player's hand
        player_hands = {}
        for player in self.players.values():
            if not player.folded and not player.sitting_out:
                hand_rank, hand_value, best_hand = HandEvaluator.evaluate_hand(
                    player.hole_cards, self.community_cards)
                player_hands[player.player_id] = (hand_rank, hand_value, best_hand)
        
        # Award pots to winners
        for i, pot in enumerate(self.pot.pots):
            eligible_players = [pid for pid in pot["eligible_players"] 
                              if not self.players[pid].folded]
                              
            if not eligible_players:
                continue
                
            # Find the best hand among eligible players
            best_rank = -1
            best_value = -1
            winners = []
            
            for pid in eligible_players:
                rank, value, _ = player_hands[pid]
                
                if rank > best_rank or (rank == best_rank and value > best_value):
                    best_rank = rank
                    best_value = value
                    winners = [pid]
                elif rank == best_rank and value == best_value:
                    winners.append(pid)
            
            # Award pot to winners
            pot_amount = pot["amount"]
            per_winner = pot_amount // len(winners)
            
            for pid in winners:
                self.players[pid].collect_winnings(per_winner)
        
        return True
```

## Poker Engine Integration

### Integration with Backend

The poker engine will be integrated with the backend services to:

1. Validate player actions
2. Calculate correct betting amounts
3. Enforce game rules
4. Evaluate hand strengths
5. Determine winners

```python
# Example backend integration
from poker_engine import GameState, Card, HandEvaluator

async def handle_player_action(game_id, player_id, action_type, amount=0):
    # Get game state from database
    game_state = await db.get_game_state(game_id)
    
    # Process the action
    result = game_state.process_player_action(player_id, action_type, amount)
    
    if result:
        # Save updated game state
        await db.update_game_state(game_id, game_state)
        
        # Broadcast updated state to all players
        await broadcast_game_update(game_id, game_state)
        
        return True
    else:
        return False
```

### AI Agent Integration

The poker engine will provide game state information to the AI agents:

```python
async def get_ai_action(game_id, player_id, archetype):
    # Get game state
    game_state = await db.get_game_state(game_id)
    
    # Get AI-visible game state (hide other players' cards)
    visible_state = get_visible_state(game_state, player_id)
    
    # Get player's hole cards
    player = game_state.players[player_id]
    hole_cards = player.hole_cards
    
    # Query LLM for decision
    ai_decision = await ai_service.get_decision(
        archetype=archetype,
        hole_cards=hole_cards,
        visible_state=visible_state
    )
    
    # Process AI action
    return await handle_player_action(
        game_id=game_id,
        player_id=player_id,
        action_type=ai_decision["action"],
        amount=ai_decision.get("amount", 0)
    )
```

## Performance Considerations

The poker engine is designed for efficiency and performance:

1. **Optimized Hand Evaluation**: The hand evaluation algorithm uses efficient comparison techniques to determine the best 5-card hand.

2. **Memory Efficiency**: The engine minimizes object creation and uses primitive data types where possible.

3. **Computation Caching**: Frequently accessed calculations, such as pot odds, are cached rather than recalculated.

4. **Parallelizable**: The design allows for running multiple game instances in parallel.

## Testing Approach

The poker engine will be thoroughly tested using:

1. **Unit Tests**: Verify individual components like Card, Deck, and HandEvaluator
2. **Edge Case Tests**: Test unusual scenarios like multiple all-ins and split pots
3. **Game Flow Tests**: Verify the entire game flow from dealing to showdown
4. **Regression Tests**: Ensure bug fixes don't reintroduce previously fixed issues
5. **Performance Tests**: Measure and optimize engine performance for various game sizes

## Future Enhancements

Potential future enhancements to the poker engine include:

1. **Tournament Support**: Adding support for tournaments with blind increases and player eliminations
2. **Alternative Poker Variants**: Support for other poker variants beyond Texas Hold'em
3. **Advanced Statistics**: Real-time calculation of advanced poker statistics like EV and equity
4. **Hand History Replayer**: Tools for replaying and analyzing hand histories
5. **Performance Optimizations**: Further optimizations for handling high-volume games