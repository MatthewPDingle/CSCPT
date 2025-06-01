"""
EventOrchestrator - Coordinates all game events and UI notifications.

This class implements the Orchestrator Pattern to manage complex
event sequences and eliminate race conditions.

Responsibilities:
- Take GameActionResult and coordinate all notifications
- Ensure proper sequencing of events
- Handle animation timing and acknowledgments
- Manage state transitions cleanly

Principles applied:
- Single Responsibility: Only handles event coordination
- Separation of Concerns: Game logic separate from UI coordination
- Command Pattern: Executes sequences based on action results
- Strategy Pattern: Different handling for different event types
"""
import asyncio
import logging
from typing import Dict, List, Optional
from app.core.game_events import (
    GameActionResult, EventContext, GameEventType, 
    AnimationSequence, PlayerBet, StreetCards
)
from app.core.websocket import game_notifier
from app.core.config import ANIMATION_FALLBACK_DELAYS


class EventOrchestrator:
    """
    Orchestrates game events and UI notifications in proper sequence.
    
    This is the central coordinator that takes action results and
    ensures all notifications happen in the correct order.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def handle_action_result(self, context: EventContext) -> None:
        """
        Main entry point for handling action results.
        
        Takes a GameActionResult and coordinates all necessary
        notifications and animations in the proper sequence.
        
        Args:
            context: EventContext containing all necessary information
        """
        result = context.action_result
        
        if not result.success:
            await self._handle_action_error(context)
            return
        
        self.logger.info(f"[ORCHESTRATOR] Processing action result for {result.action_player_id}")
        self.logger.info(f"[ORCHESTRATOR] Events: {[e.name for e in result.events]}")
        self.logger.info(f"[ORCHESTRATOR] Animation sequence: {result.animation_sequence.name}")
        
        # Step 1: Always notify about the player action first
        await self._notify_player_action(context)
        
        # Step 2: Remove turn highlight if required
        if result.turn_highlight_removed:
            await self._notify_turn_highlight_removed(context)
        
        # Step 3: Handle specific event sequences
        if GameEventType.SHOWDOWN_TRIGGERED in result.events:
            await self._handle_showdown_sequence(context)
        elif GameEventType.EARLY_SHOWDOWN_TRIGGERED in result.events:
            await self._handle_early_showdown_sequence(context)
        elif GameEventType.BETTING_ROUND_COMPLETED in result.events:
            await self._handle_betting_round_completion(context)
        elif GameEventType.HAND_COMPLETED in result.events:
            await self._handle_hand_completion(context)
        else:
            # Normal action, continue betting round
            await self._handle_continued_betting(context)
    
    async def _notify_player_action(self, context: EventContext) -> None:
        """Notify clients about the player action."""
        result = context.action_result
        
        # Calculate total bets for the notification
        post_street_bet = None
        post_hand_bet = None
        
        # Get the actual player object to access bet amounts
        poker_game = context.poker_game
        player = next((p for p in poker_game.players if p.player_id == result.action_player_id), None)
        
        if player:
            post_street_bet = player.current_bet
            if result.action_type.name == 'ALL_IN':
                post_hand_bet = player.total_bet
        
        await game_notifier.notify_player_action(
            context.game_id,
            result.action_player_id,
            result.action_type.name,
            result.action_amount,
            total_street_bet=post_street_bet,
            total_hand_bet=post_hand_bet
        )
    
    async def _notify_turn_highlight_removed(self, context: EventContext) -> None:
        """Remove turn highlight for the acting player."""
        await game_notifier.notify_turn_highlight_removed(
            context.game_id, 
            context.action_result.action_player_id
        )
    
    async def _handle_showdown_sequence(self, context: EventContext) -> None:
        """
        Handle full showdown sequence with proper coordination.
        
        This implements the canonical showdown sequence:
        1. Notify showdown transition (clears highlights)
        2. Finalize bets with animation
        3. Deal remaining streets if needed
        4. Reveal hands and determine winners
        """
        self.logger.info(f"[ORCHESTRATOR] Starting showdown sequence")
        
        # Step 1: Explicit showdown transition
        await game_notifier.notify_showdown_transition(context.game_id)
        
        # Step 2: Finalize current betting round
        await self._finalize_betting_round(context)
        
        # Step 3: Deal remaining streets if this is an all-in scenario
        result = context.action_result
        if result.remaining_streets:
            await self._deal_remaining_streets(context)
        
        # Step 4: Update game state to SHOWDOWN
        await game_notifier.notify_game_update(context.game_id, context.poker_game)
        
        # Step 5: Handle showdown hands revelation and results
        # (This will be handled by the existing showdown logic in game_ws.py)
    
    async def _handle_early_showdown_sequence(self, context: EventContext) -> None:
        """Handle early showdown (one player remaining)."""
        self.logger.info(f"[ORCHESTRATOR] Starting early showdown sequence")
        
        # Early showdown follows same pattern but no hand revelation needed
        await game_notifier.notify_showdown_transition(context.game_id)
        await self._finalize_betting_round(context)
        await game_notifier.notify_game_update(context.game_id, context.poker_game)
    
    async def _handle_betting_round_completion(self, context: EventContext) -> None:
        """Handle normal betting round completion (deal next street)."""
        self.logger.info(f"[ORCHESTRATOR] Handling betting round completion")
        
        # Finalize bets and deal next street
        await self._finalize_betting_round(context)
        
        if context.action_result.street_cards:
            await self._deal_street(context, context.action_result.street_cards)
        
        # Update game state and request next action
        await game_notifier.notify_game_update(context.game_id, context.poker_game)
        await game_notifier.notify_action_request(context.game_id, context.poker_game)
    
    async def _handle_continued_betting(self, context: EventContext) -> None:
        """Handle normal action that continues the betting round."""
        self.logger.info(f"[ORCHESTRATOR] Continuing betting round")
        
        # Just update game state and request next action
        await game_notifier.notify_game_update(context.game_id, context.poker_game)
        await game_notifier.notify_action_request(context.game_id, context.poker_game)
    
    async def _handle_hand_completion(self, context: EventContext) -> None:
        """Handle complete hand ending."""
        self.logger.info(f"[ORCHESTRATOR] Handling hand completion")
        
        await game_notifier.notify_game_update(context.game_id, context.poker_game)
        # Hand completion notifications will be handled by existing logic
    
    async def _finalize_betting_round(self, context: EventContext) -> None:
        """
        Finalize betting round with proper chip animation sequence.
        
        This implements the canonical chip animation sequence:
        1. Notify round bets finalized
        2. Wait for animation acknowledgment
        3. Clear player bets in game state
        """
        result = context.action_result
        
        if result.player_bets and result.total_pot is not None:
            # Convert PlayerBet objects to the format expected by notify_round_bets_finalized
            player_bets_data = [
                {"player_id": bet.player_id, "amount": bet.amount}
                for bet in result.player_bets
            ]
            
            self.logger.info(f"[ORCHESTRATOR] Finalizing bets: {len(player_bets_data)} players, pot: {result.total_pot}")
            
            # Send the notification
            await game_notifier.notify_round_bets_finalized(
                context.game_id, 
                player_bets_data, 
                result.total_pot
            )
            
            # Wait for animation acknowledgment
            try:
                await game_notifier.wait_for_animation(
                    context.game_id, "round_bets_finalized"
                )
                self.logger.info(f"[ORCHESTRATOR] Chip animation acknowledged")
            except asyncio.TimeoutError:
                self.logger.warning(f"[ORCHESTRATOR] Chip animation timeout, using fallback")
                await asyncio.sleep(
                    ANIMATION_FALLBACK_DELAYS.get("round_bets_finalized", 1000) / 1000.0
                )
            
            # Clear bets in game state after animation
            for player in context.poker_game.players:
                player.current_bet = 0
    
    async def _deal_remaining_streets(self, context: EventContext) -> None:
        """Deal all remaining streets for all-in scenarios."""
        result = context.action_result
        poker_game = context.poker_game
        
        for street_name in result.remaining_streets:
            self.logger.info(f"[ORCHESTRATOR] Dealing {street_name}")
            
            # Deal the street in the game logic
            if street_name == "FLOP" and len(poker_game.community_cards) == 0:
                poker_game.deal_flop()
                cards = poker_game.community_cards[-3:]
            elif street_name == "TURN" and len(poker_game.community_cards) == 3:
                poker_game.deal_turn()
                cards = [poker_game.community_cards[-1]]
            elif street_name == "RIVER" and len(poker_game.community_cards) == 4:
                poker_game.deal_river()
                cards = [poker_game.community_cards[-1]]
            else:
                continue  # Skip if cards already dealt
            
            # Notify and wait for animation
            await game_notifier.notify_street_dealt(
                context.game_id, street_name, cards
            )
            
            try:
                await game_notifier.wait_for_animation(
                    context.game_id, f"street_dealt_{street_name.lower()}"
                )
            except asyncio.TimeoutError:
                fallback_key = f"street_dealt_{street_name.lower()}"
                delay = ANIMATION_FALLBACK_DELAYS.get(fallback_key, 1000)
                await asyncio.sleep(delay / 1000.0)
    
    async def _deal_street(self, context: EventContext, street_cards: StreetCards) -> None:
        """Deal a single street."""
        await game_notifier.notify_street_dealt(
            context.game_id, 
            street_cards.street_name, 
            street_cards.cards
        )
        
        try:
            animation_key = f"street_dealt_{street_cards.street_name.lower()}"
            await game_notifier.wait_for_animation(context.game_id, animation_key)
        except asyncio.TimeoutError:
            fallback_key = f"street_dealt_{street_cards.street_name.lower()}"
            delay = ANIMATION_FALLBACK_DELAYS.get(fallback_key, 1000)
            await asyncio.sleep(delay / 1000.0)
    
    async def _handle_action_error(self, context: EventContext) -> None:
        """Handle failed actions."""
        result = context.action_result
        
        await game_notifier.send_error_to_player(
            context.game_id,
            result.action_player_id,
            {
                "code": "action_failed",
                "message": result.error_message or "Action failed"
            }
        )


# Create singleton instance
event_orchestrator = EventOrchestrator()