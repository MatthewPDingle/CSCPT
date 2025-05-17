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
## `street_dealt`
The `street_dealt` event notifies clients that a new community card street has been dealt. It is emitted whenever the flop, turn, or river is revealed, including during early all-in showdowns when the remaining board cards are rolled out.

### Payload
```json
{
  "type": "street_dealt",
  "data": {
    "street": "FLOP",
    "cards": ["Ah", "Kd", "Qs"],
    "timestamp": "2024-01-01T12:00:02Z"
  }
}
```

- `street` – name of the street dealt (`FLOP`, `TURN`, or `RIVER`)
- `cards` – list of card strings revealed for this street

## `showdown_hands_revealed`
The `showdown_hands_revealed` event instructs clients to flip over the hole cards of all remaining players. It follows `round_bets_finalized` when a hand reaches showdown.

### Payload
```json
{
  "type": "showdown_hands_revealed",
  "data": {
    "player_hands": [
      {"player_id": "p1", "cards": ["As", "Ah"]},
      {"player_id": "p2", "cards": ["Kd", "Kh"]}
    ],
    "timestamp": "2024-01-01T12:00:04Z"
  }
}
```

- `player_hands` – list of each non‑folded player's hole cards

## `pot_winners_determined`
After evaluating the showdown, `pot_winners_determined` announces which players won each pot and their shares.

### Payload
```json
{
  "type": "pot_winners_determined",
  "data": {
    "pots": [
      {
        "pot_id": "pot_0",
        "amount": 150,
        "winners": [
          {"player_id": "p2", "hand_rank": "Two Pair", "share": 150}
        ]
      }
    ],
    "timestamp": "2024-01-01T12:00:05Z"
  }
}
```

- `pots` – details of each pot including winners and amounts

## `chips_distributed`
Once pot animations complete, chip stacks are updated and `chips_distributed` sends the refreshed game state.

### Payload
```json
{
  "type": "chips_distributed",
  "data": {
    "game_id": "game123",
    "players": [
      {"player_id": "p1", "chips": 1000},
      {"player_id": "p2", "chips": 1200}
    ]
  }
}
```

- `data` – complete updated game state reflecting new chip counts

## `hand_visually_concluded`
The `hand_visually_concluded` event signals that all winner animations have finished and the table is ready for the next hand. It is emitted after `chips_distributed` and the final winner pulse.

### Payload
```json
{
  "type": "hand_visually_concluded",
  "data": {
    "timestamp": "2024-01-01T12:00:07Z"
  }
}
```
