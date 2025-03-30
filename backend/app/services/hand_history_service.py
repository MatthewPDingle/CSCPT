"""
Hand history tracking service.
This service is responsible for recording and analyzing hand histories.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Set

from app.core.poker_game import BettingRound, PlayerAction, Player, Pot
from app.models.domain_models import (
    HandHistory, PlayerHandSnapshot, ActionDetail, PotResult, 
    HandMetrics, PlayerAction as DomainPlayerAction
)
from app.repositories.in_memory import HandHistoryRepository, RepositoryFactory

# Import memory integration if available
try:
    from ai.memory_integration import MemoryIntegration
    MEMORY_SYSTEM_AVAILABLE = True
except ImportError:
    MEMORY_SYSTEM_AVAILABLE = False


class HandHistoryRecorder:
    """Records hand history during gameplay."""
    
    def __init__(self, repo_factory=None):
        if repo_factory is None:
            repo_factory = RepositoryFactory.get_instance()
        self.hand_history_repo = repo_factory.get_repository(HandHistoryRepository)
        self.current_hand: Optional[HandHistory] = None
        self.action_sequence: int = 0  # For tracking order of actions
        self.game_id: Optional[str] = None
        
    def start_hand(self, game_id: str, hand_number: int, players: List[Player], 
                  dealer_pos: int, sb: int, bb: int, ante: int,
                  tournament_level: Optional[int] = None) -> str:
        """
        Start recording a new hand.
        
        Args:
            game_id: Unique identifier of the game
            hand_number: Current hand number in the game
            players: List of players in the hand
            dealer_pos: Dealer position index
            sb: Small blind amount
            bb: Big blind amount
            ante: Ante amount
            tournament_level: Current tournament level (if applicable)
            
        Returns:
            The ID of the created hand history
        """
        self.game_id = game_id
        self.current_hand = HandHistory(
            game_id=game_id,
            hand_number=hand_number,
            dealer_position=dealer_pos,
            small_blind=sb,
            big_blind=bb,
            ante=ante,
            table_size=len(players),
            tournament_level=tournament_level,
            betting_rounds={
                "PREFLOP": [],
                "FLOP": [],
                "TURN": [],
                "RIVER": []
            }
        )
        
        # Record initial player states
        for player in players:
            # Skip players who are out of the game
            if hasattr(player, 'status') and player.status.name == "OUT":
                continue
                
            # Determine position relative to button
            position_rel_btn = (player.position - dealer_pos) % len(players)
            
            snapshot = PlayerHandSnapshot(
                player_id=player.player_id,
                position=player.position,
                name=player.name,
                is_human=getattr(player, 'is_human', False),
                archetype=getattr(player, 'archetype', None),
                stack_start=player.chips,
                is_dealer=(player.position == dealer_pos),
                is_small_blind=(position_rel_btn == 1),
                is_big_blind=(position_rel_btn == 2),
                hole_cards=[str(c) for c in player.hand.cards] if hasattr(player.hand, 'cards') else []
            )
            self.current_hand.players.append(snapshot)
        
        self.action_sequence = 0
        
        # Save the initial hand state to the repository
        self.hand_history_repo.create(self.current_hand)
        
        return self.current_hand.id
    
    def record_action(self, player_id: str, action_type: PlayerAction, 
                     amount: Optional[int] = None, betting_round: BettingRound = None,
                     player: Optional[Player] = None, pot_before: int = 0, pot_after: int = 0,
                     bet_facing: int = 0) -> None:
        """
        Record a player action.
        
        Args:
            player_id: ID of the player taking the action
            action_type: The action being taken
            amount: Amount of the bet/raise/call (if applicable)
            betting_round: Current betting round
            player: Player object reference (for stack information)
            pot_before: Pot size before action
            pot_after: Pot size after action
            bet_facing: Current bet the player is facing
        """
        if not self.current_hand or not betting_round:
            return
        
        # Skip recording if player or betting round is invalid
        if not player or not hasattr(betting_round, 'name'):
            return
            
        # Convert core poker game action to domain model action
        action_map = {
            PlayerAction.FOLD: DomainPlayerAction.FOLD,
            PlayerAction.CHECK: DomainPlayerAction.CHECK,
            PlayerAction.CALL: DomainPlayerAction.CALL,
            PlayerAction.BET: DomainPlayerAction.BET,
            PlayerAction.RAISE: DomainPlayerAction.RAISE,
            PlayerAction.ALL_IN: DomainPlayerAction.ALL_IN
        }
        domain_action = action_map.get(action_type)
        if not domain_action:
            return
            
        # Calculate position relative to dealer
        dealer_pos = self.current_hand.dealer_position
        player_pos = player.position
        position_rel_dealer = (player_pos - dealer_pos) % len(self.current_hand.players)
        
        # Record action with stack information
        stack_before = player.chips + (amount or 0)  # Add amount back for stack before
        stack_after = player.chips
        
        action = ActionDetail(
            player_id=player_id,
            action_type=domain_action,
            amount=amount,
            position_relative_to_dealer=position_rel_dealer,
            position_in_action_sequence=self.action_sequence,
            stack_before=stack_before,
            stack_after=stack_after,
            pot_before=pot_before,
            pot_after=pot_after,
            bet_facing=bet_facing,
            all_in=(player.chips == 0)
        )
        
        # Update metrics
        self._update_metrics(action, betting_round)
        
        # Add to appropriate betting round
        round_key = betting_round.name
        if round_key in self.current_hand.betting_rounds:
            self.current_hand.betting_rounds[round_key].append(action)
        
        self.action_sequence += 1
        
        # Update the hand history in the repository
        self.hand_history_repo.update(self.current_hand)
        
        # Mark VPIP and PFR for player in hand
        if betting_round.name == "PREFLOP":
            for p in self.current_hand.players:
                if p.player_id == player_id:
                    if domain_action in [DomainPlayerAction.CALL, DomainPlayerAction.BET, 
                                      DomainPlayerAction.RAISE, DomainPlayerAction.ALL_IN]:
                        p.vpip = True
                    if domain_action in [DomainPlayerAction.BET, DomainPlayerAction.RAISE, 
                                      DomainPlayerAction.ALL_IN]:
                        p.pfr = True
        
        # Update memory system with action info
        if MEMORY_SYSTEM_AVAILABLE:
            try:
                # Only update for AI players
                for p in self.current_hand.players:
                    if p.player_id == player_id and not p.is_human:
                        # Get additional game state info if needed
                        game_state = {
                            "pot": pot_after,
                            "bet_facing": bet_facing,
                            "round": betting_round.name
                        }
                        
                        # Update memory with this action
                        MemoryIntegration.update_from_action(
                            player_id=player_id,
                            action_type=action_type.name,
                            amount=amount,
                            betting_round=betting_round.name,
                            game_state=game_state
                        )
                        break
            except Exception as e:
                # Don't let memory errors disrupt the game
                print(f"Memory update error: {str(e)}")
    
    def record_community_cards(self, cards: List, round_name: str) -> None:
        """
        Record community cards being dealt.
        
        Args:
            cards: List of community cards
            round_name: The current betting round name
        """
        if not self.current_hand:
            return
        
        # Convert cards to string representation
        card_strings = []
        for card in cards:
            card_strings.append(str(card))
        
        self.current_hand.community_cards = card_strings
        
        # Update the hand history in the repository
        self.hand_history_repo.update(self.current_hand)
        
        # Update players seeing flop metric
        if round_name == "FLOP":
            # Count players who haven't folded preflop
            folded_ids = set()
            for action in self.current_hand.betting_rounds.get("PREFLOP", []):
                if action.action_type == DomainPlayerAction.FOLD:
                    folded_ids.add(action.player_id)
                    
            active_count = len(self.current_hand.players) - len(folded_ids)
            self.current_hand.metrics.players_seeing_flop = active_count
    
    def record_pot_results(self, pots: List[Pot], hand_evaluations: Dict) -> None:
        """
        Record the pot results at showdown.
        
        Args:
            pots: List of pot objects from the poker game
            hand_evaluations: Dictionary mapping winners to pots
        """
        if not self.current_hand:
            return
            
        self.current_hand.total_pot = sum(pot.amount for pot in pots)
        
        # Only set showdown_reached to True if we have real showdown data
        # Check if we have winning hand information, which indicates a real showdown
        has_showdown_data = False
        for pot_key in hand_evaluations:
            if pot_key.endswith('_hand') or pot_key.endswith('_cards'):
                has_showdown_data = True
                break
                
        self.current_hand.metrics.showdown_reached = has_showdown_data
        
        for i, pot in enumerate(pots):
            pot_result = PotResult(
                pot_name=pot.name if hasattr(pot, 'name') else f"Pot {i}",
                amount=pot.amount,
                eligible_players=list(pot.eligible_players) if hasattr(pot, 'eligible_players') else []
            )
            
            # Add winners from hand evaluations
            pot_key = pot.name if hasattr(pot, 'name') else f"pot_{i}"
            winners = hand_evaluations.get(pot_key, [])
            
            # Extract player IDs from winners (which might be Player objects)
            if winners:
                if hasattr(winners[0], 'player_id'):
                    pot_result.winners = [p.player_id for p in winners]
                else:
                    pot_result.winners = winners
                    
            # Record winning hand if available (format depends on poker game implementation)
            if pot_result.winners and f"{pot_key}_hand" in hand_evaluations:
                winning_hand = hand_evaluations[f"{pot_key}_hand"]
                pot_result.winning_hand_type = winning_hand.name if hasattr(winning_hand, 'name') else str(winning_hand)
                
                if f"{pot_key}_cards" in hand_evaluations:
                    cards = hand_evaluations[f"{pot_key}_cards"]
                    pot_result.winning_hand_cards = [str(c) for c in cards]
                
            self.current_hand.pot_results.append(pot_result)
            
            # Update player won_amount values
            for player in self.current_hand.players:
                if player.player_id in pot_result.winners:
                    # Split pot evenly among winners
                    split_amount = pot_result.amount // len(pot_result.winners)
                    player.won_amount += split_amount
            
        # Update the hand history in the repository
        self.hand_history_repo.update(self.current_hand)
    
    def end_hand(self, players: List[Player]) -> str:
        """
        Finalize the hand history record.
        
        Args:
            players: List of player objects at the end of the hand
            
        Returns:
            ID of the completed hand history
        """
        if not self.current_hand:
            return ""
            
        self.current_hand.timestamp_end = datetime.now()
        
        # Update final player states
        for player in players:
            for p in self.current_hand.players:
                if p.player_id == player.player_id:
                    p.stack_end = player.chips
                    p.won_amount = player.chips - p.stack_start
                    
                    # Record final hand for players who didn't fold
                    if hasattr(player, 'status') and player.status.name != "FOLDED":
                        if hasattr(player, 'hand') and hasattr(player.hand, 'cards'):
                            p.showed_cards = True
                            p.hole_cards = [str(c) for c in player.hand.cards]
        
        # Calculate final metrics
        self._calculate_final_metrics()
        
        # Save the hand history
        self.hand_history_repo.create(self.current_hand)
        
        # Return the hand history ID
        hand_id = self.current_hand.id
        
        # Process the completed hand in the memory system
        if MEMORY_SYSTEM_AVAILABLE:
            try:
                # Convert the hand history to a dictionary for memory processing
                hand_dict = self.current_hand.dict()
                
                # Process in memory system
                MemoryIntegration.process_hand_history(hand_dict)
            except Exception as e:
                # Don't let memory errors disrupt the game
                print(f"Error processing hand in memory system: {str(e)}")
        
        # Reset current hand
        self.current_hand = None
        self.action_sequence = 0
        
        return hand_id
        
    def _update_metrics(self, action: ActionDetail, betting_round: BettingRound) -> None:
        """
        Update metrics based on a player action.
        
        Args:
            action: The player action being recorded
            betting_round: The current betting round
        """
        if not self.current_hand:
            return
            
        metrics = self.current_hand.metrics
        
        # Update round-specific metrics
        if betting_round.name == "PREFLOP":
            if action.action_type == DomainPlayerAction.RAISE:
                metrics.preflop_raise_count += 1
            elif action.action_type == DomainPlayerAction.CALL:
                metrics.preflop_call_count += 1
                
        # Track c-bet attempts
        if betting_round.name == "FLOP":
            # Check if this player was the last aggressor preflop
            preflop_actions = self.current_hand.betting_rounds.get("PREFLOP", [])
            last_aggressor = None
            
            # Find the last aggressor from preflop
            for pa in preflop_actions:
                if pa.action_type in [DomainPlayerAction.BET, DomainPlayerAction.RAISE]:
                    last_aggressor = pa.player_id
            
            # Check if current player was last aggressor and is now betting
            if last_aggressor == action.player_id:
                if action.action_type in [DomainPlayerAction.BET, DomainPlayerAction.RAISE]:
                    metrics.flop_cbet_attempted = True
                    
                    # Check if c-bet was successful (everybody folded afterward)
                    flop_actions = self.current_hand.betting_rounds.get("FLOP", [])
                    if all(a.action_type == DomainPlayerAction.FOLD 
                         for a in flop_actions 
                         if a.player_id != action.player_id 
                         and a.position_in_action_sequence > action.position_in_action_sequence):
                        metrics.flop_cbet_successful = True
        
        # Mark all-in confrontation
        if action.all_in:
            all_in_count = sum(1 for a in 
                             [a for round_actions in self.current_hand.betting_rounds.values() 
                              for a in round_actions]
                             if a.all_in)
            if all_in_count >= 2:
                metrics.all_in_confrontation = True
    
    def _calculate_final_metrics(self) -> None:
        """Calculate final metrics for the hand."""
        if not self.current_hand:
            return
            
        metrics = self.current_hand.metrics
        
        # Calculate aggression factor
        aggressive_actions = 0
        passive_actions = 0
        
        for round_name, actions in self.current_hand.betting_rounds.items():
            for action in actions:
                if action.action_type in [DomainPlayerAction.BET, DomainPlayerAction.RAISE]:
                    aggressive_actions += 1
                elif action.action_type == DomainPlayerAction.CALL:
                    passive_actions += 1
        
        if passive_actions > 0:
            metrics.aggression_factor = aggressive_actions / passive_actions
            
        # Try to determine if this was the largest pot in the game so far
        # This would require comparing with other hands in the game, which we'll implement in a future version
        
        # For now, we'll leave largest_pot_in_game_so_far as False