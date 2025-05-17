# WebSocket Messages

## `round_bets_finalized`
The `round_bets_finalized` event informs clients that all bets for the most recent betting round have been collected into the pot. It is triggered during the showdown sequence once `PokerGame` finishes awarding the pots. See `backend/app/core/poker_game.py` around lines 2046–2102 where `_handle_showdown` finalizes chip distribution.

### Payload
```json
{
  "type": "round_bets_finalized",
  "data": {
    "player_bets": [
      {"player_id": "p1", "amount": 50},
      {"player_id": "p2", "amount": 100}
    ],
    "pot": 150,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

- `player_bets` – list of each player's bet for that street
- `pot` – total pot value before winners are paid
