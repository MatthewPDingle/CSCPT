# Showdown Sequence Fix Documentation

## Issues Identified

### 1. Turn Highlight Persistence
**Problem**: When the last player goes all-in triggering a showdown, the turn highlight remains on that player throughout the showdown sequence.

**Root Cause**: The `showdown_transition` WebSocket message was not being sent when `_handle_showdown` was called directly from the all-in path in `process_action`.

**Fix Applied**: Added `notify_showdown_transition` call at the beginning of `_handle_showdown` method in `/home/therealpananon/cscpt/backend/app/core/poker_game.py`.

### 2. Bet Text Reappearing
**Problem**: After chip animation completes, bet text boxes briefly reappear next to players before being cleared.

**Root Cause**: The `suppressBetStack` prop only checked `betsToAnimate` array, which is cleared after 500ms. However, `bettingRoundAnimating` remains true for the full animation sequence (1000ms+), and game state still has non-zero `current_bet` values during this gap.

**Fix Applied**: Updated `suppressBetStack` logic in `/home/therealpananon/cscpt/frontend/src/components/poker/PokerTable.tsx` to also check `bettingRoundAnimating` state.

## Code Changes

### Backend: `/home/therealpananon/cscpt/backend/app/core/poker_game.py`
```python
async def _handle_showdown(self) -> bool:
    # Send showdown transition notification to clear UI elements
    if self.game_id:
        try:
            from app.core.websocket import game_notifier
            logging.warning(f"[SHOWDOWN] Sending showdown_transition notification for game {self.game_id}")
            await game_notifier.notify_showdown_transition(self.game_id)
        except Exception as e:
            logging.error(f"[SHOWDOWN] Error sending showdown transition notification: {e}")
```

### Frontend: `/home/therealpananon/cscpt/frontend/src/components/poker/PokerTable.tsx`
```typescript
suppressBetStack={
  betsToAnimate.some(b => b.playerId === playerId) || 
  (bettingRoundAnimating && player.current_bet > 0)
}
```

## Architectural Recommendations

### Short-term (Implemented)
1. Direct fix to send `showdown_transition` message from `_handle_showdown`
2. Enhanced bet suppression logic to cover entire animation sequence
3. Added comprehensive logging to track event sequences

### Long-term (Recommended)
1. **Event-Driven Architecture**: All paths to showdown should go through the Event Orchestrator
   - Create a `ShowdownEvent` that can be triggered from `process_action`
   - Let the orchestrator handle the full showdown sequence
   - This ensures consistent event flow regardless of how showdown is triggered

2. **Animation State Machine**: Implement a formal state machine for animation sequences
   - States: IDLE, COLLECTING_BETS, POT_FLASH, DISTRIBUTING_CHIPS, etc.
   - This prevents timing issues and makes the flow more predictable

3. **Immediate State Updates**: Clear `current_bet` values in game state immediately when animation starts
   - Frontend should rely on animation state, not game state, during animations
   - This prevents visual artifacts during state transitions

## Testing Recommendations

1. Test all-in scenarios with various player counts
2. Test rapid actions during animation sequences
3. Test network delays/timeouts during animations
4. Verify side pot calculations and distributions

## Event Sequence Verification

The canonical showdown sequence should now properly execute:
1. Last player action processed
2. **Turn highlight removed via showdown_transition message** ✓
3. Side pots created if needed
4. Betting round finalized with animations
5. **Bet displays suppressed during entire animation sequence** ✓
6. Streets dealt if needed (all-in scenario)
7. Hands revealed and winners determined
8. Chips distributed to winners
9. Next hand setup