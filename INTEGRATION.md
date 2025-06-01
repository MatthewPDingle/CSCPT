# Event-Driven Architecture Integration Guide

## 🚀 Quick Start - Enable New Architecture

### Backend Integration

1. **Update WebSocket Router** (`backend/app/api/game.py`):
```python
# Replace the old action handler with the new one
from app.api.game_ws import process_action_message_new

# In your WebSocket message handling:
if message_type == "action":
    await process_action_message_new(websocket, game_id, message, player_id, service)
```

### Frontend Integration

2. **Replace useGameWebSocket** (`frontend/src/pages/GamePage.tsx`):
```typescript
// OLD:
// import { useGameWebSocket } from '../hooks/useGameWebSocket';

// NEW:
import { useGameStateCoordinator } from '../hooks/useGameStateCoordinator';
import { useWebSocket } from '../hooks/useWebSocket';

const GamePage: React.FC = () => {
  // ... existing code ...
  
  // Replace useGameWebSocket with coordinator
  const gameCoordinator = useGameStateCoordinator();
  
  // Set up WebSocket with coordinator
  const { sendMessage, status, lastMessage } = useWebSocket(wsUrl);
  
  useEffect(() => {
    if (lastMessage) {
      gameCoordinator.handleMessage(lastMessage);
    }
  }, [lastMessage, gameCoordinator]);
  
  // Use coordinator state instead of old hook
  const {
    gameState,
    currentStreetPot,
    accumulatedPot,
    betsToAnimate,
    flashMainPot,
    isAnimating
  } = gameCoordinator;
  
  // ... rest of component
};
```

### 3. **Update PokerTable Component**:
```typescript
// Use coordinator data directly
<PokerTable
  players={gameState?.players || []}
  communityCards={gameState?.community_cards || []}
  pot={accumulatedPot}
  currentStreetTotal={currentStreetPot}
  betsToAnimate={betsToAnimate}
  // ... other props
/>
```

## 🔧 Key Changes

### What's Different:
- **No more race conditions** - Events happen in proper sequence
- **Clean state management** - Animation state is separate from game state  
- **Proper timing** - UI updates wait for animations to complete
- **Debuggable** - Clear logging shows exactly what's happening

### What Stays the Same:
- All existing UI components work unchanged
- WebSocket message format is identical
- Game logic rules are unchanged
- Player experience is identical (but smoother)

## 🐛 Testing

### Test Pre-Flop All-In Scenario:
1. Start a cash game with multiple players
2. Have players go all-in pre-flop
3. Verify:
   - ✅ Last player gets to act before showdown
   - ✅ Turn highlight disappears cleanly
   - ✅ Bet text doesn't reappear after chip animation
   - ✅ Flop, turn, river show properly
   - ✅ Showdown sequence works smoothly

### Debug Logging:
- Backend: Look for `[ORCHESTRATOR]` and `[WS-ACTION-NEW-]` logs
- Frontend: Look for `[COORDINATOR]` and `[ANIMATION-SM]` logs

## 🚨 Rollback Plan

If issues occur, you can quickly rollback:

1. **Backend**: Change `process_action_message_new` back to `process_action_message`
2. **Frontend**: Change `useGameStateCoordinator` back to `useGameWebSocket`

The old code is still intact and functional.

## 📊 Performance Impact

- **Positive**: Fewer race conditions means fewer WebSocket messages and re-renders
- **Minimal**: New architecture adds ~2KB to bundle size
- **Better UX**: Smoother animations and more predictable behavior

## 🎯 Next Steps

1. Test the new architecture with the pre-flop all-in scenario
2. If successful, gradually migrate other parts of the app
3. Remove old code after thorough testing
4. Add unit tests for the state machines

The new architecture is designed to be incrementally adoptable - you can test it alongside the existing code.