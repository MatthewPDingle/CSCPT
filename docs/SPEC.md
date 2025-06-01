# Chip Swinger Championship Poker Trainer
## Comprehensive Design and Implementation Specification

### Overview
This specification outlines the development of an interactive poker training application exclusively focused on Texas Hold'em, realistically simulating live poker scenarios. It leverages Large Language Models (LLMs) as intelligent agents representing diverse poker player archetypes, integrating advanced coaching functionalities and comprehensive statistics to guide and educate players.

### Core Features

#### Game Setup
- **Poker Variant:** Exclusively Texas Hold'em.
- **Training Environments:**
  - Cash game with configurable buy-in and blind structure
  - Tournament with customizable parameters:
    - Tournament tier (Local, Regional, National, International) defining player caliber
    - Tournament stage to start at:
      - Early stage
      - Mid stage
      - Approaching money bubble
      - After money bubble
      - Final table
    - Payout structures
- **Table Customization:** User selects default table size (2–9 players).
- **Player Archetypes:**
  - Tight Aggressive (TAG)
  - Loose Aggressive (LAG)
  - Tight Passive
  - Calling Station
  - Maniac
  - Beginner (Noob)
  - **Archetype Assignment:**
    - Cash Game: Individual selection for each opponent at the table
    - Tournament: Percentage distribution of archetypes with default mixes based on tournament tier
      - For example, Local tier might have 50% Beginner, 20% Maniac, 15% LAG, 10% Calling Station, 2% Tight Passive, 3% TAG
      - Higher tiers progressively include more skilled archetypes

#### Player Control and AI Integration
- **User-Controlled Player:**
  - User actively plays hands.
  - Stack sizes, position, and decisions managed through an intuitive UI.
- **AI-Controlled Opponents:**
  - Each opponent controlled by an LLM assigned specific playing styles explicitly, randomly, or environment-based.
  - LLM APIs: OpenAI (o3-mini-pro, GPT-4-turbo), Anthropic (Claude 3.7, Claude 3 Opus), extendable to xAI, Meta, DeepSeek.
  - AI agents build dynamic models of opponents and table dynamics based on observed gameplay:
    - Player profiles constructed from betting patterns, hand selections, and strategies.
    - Agents independently calculate pot odds, implied odds, equity, and expected value (EV).

#### Realistic Poker Mechanics Simulation
- Standard poker actions: Fold, Call, Raise, Check, Bet, All-in.
- Realistic dealing and hand progression.
- Detailed simulation of blinds, antes, betting structure, pot calculations, and side pots.

### Advanced Poker Statistics
- Statistics panel (hidden by default, toggleable by user):
  - Pot odds
  - Implied odds
  - Player aggression frequency
  - VPIP (Voluntarily Put Money in Pot)
  - PFR (Preflop Raise)
  - AF (Aggression Factor)
  - C-bet frequency
  - Fold to 3-bet frequency
  - Equity calculations
  - Opponent profiling insights

### Coaching and Educational Features
- **Interactive Coach via Chatbox:**
  - Chat-based interface similar to ChatGPT/Claude, displayed on-screen side panel.
  - Default: Post-hand constructive critiques.
  - Optional: Pre-action advice toggled on/off.
- **Interactive Dialogue:**
  - Questions like:
    - "What range do you think player X holds?"
    - "How do opponents likely perceive my hand?"
    - "Was this bluff believable? Why or why not?"
- **Constructive Criticism:**
  - Detailed feedback on suboptimal moves, reasoning, and alternative strategies.

### End-of-Betting-Round Sequence

The canonical end-of-betting-round events should always be as follows and none of these should overlap:

1. **Player Action Processed**: The last player in `to_act` makes their action via `process_action()`.
2. **Turn Highlight Removed**: `showTurnHighlight` is set to `false`, removing the yellow border from the acting player.
3. **Side Pots Created**: If any players have `PlayerStatus.ALL_IN`, `_create_side_pots()` is called to calculate side pots.
4. **Backend Notification**: `notify_round_bets_finalized()` sends WebSocket message with:
   - `player_bets`: Array of `{player_id, amount}` for each player's `current_bet`
   - `pot`: Total pot amount (sum of all `pot.amount` in `self.pots`)
5. **Chip Animation Start**: Frontend receives `round_bets_finalized` and sets `betsToAnimate` with player positions.
6. **Chip Movement**: `AnimatingBetChip` components move from player positions to pot center over 500ms (`CHIP_ANIMATION_DURATION_MS`).
7. **Pot Update**: After chips reach destination, `accumulatedPot` is updated with new total.
8. **Pot Pulse**: `flashMainPot` triggers yellow pulse animation for 500ms (`POT_FLASH_DURATION_MS`).
9. **Animation Acknowledgment**: Frontend sends `{type: 'animation_done', data: {animation_type: 'round_bets_finalized'}}`.
10. **Backend State Clear**: Upon receiving acknowledgment, backend sets all `player.current_bet = 0`.
11. **Betting Input Reset**: Frontend's `betAmount` state resets to 0, clearing the bet slider/input.
12. **Street Dealing**: If `current_round` is not `RIVER`, backend calls appropriate method:
    - `PREFLOP` → `deal_flop()` 
    - `FLOP` → `deal_turn()`
    - `TURN` → `deal_river()`
13. **Street Notification**: `notify_street_dealt()` sends message with:
    - `street`: New `current_round.name`
    - `cards`: Array of new `community_cards`
14. **Card Reveal Animation**: Frontend reveals cards with 150ms stagger (`CARD_STAGGER_DELAY_MS`) and plays sound.
15. **Street Animation Acknowledgment**: Frontend sends `{type: 'animation_done', data: {animation_type: 'street_dealt'}}`.
16. **Post-Street Pause**: 1000ms wait (`POST_STREET_PAUSE_MS`).
17. **Next Action Request**: `notify_action_request()` highlights next player in `to_act` set.

### Showdown Sequence

The canonical showdown events should always be as follows and none of these should overlap:

1. **Player Action Processed**: The last player in `to_act` makes their action via `process_action()`.
2. **Turn Highlight Removed**: `showTurnHighlight` is set to `false`, removing the yellow border from the acting player.
3. **Showdown Triggered**: `_check_betting_round_completion()` returns `true` and `current_round == RIVER`.
4. **Side Pots Finalized**: `_create_side_pots()` ensures all side pots are properly created with `eligible_players`.
5. **Final Bets Collected**: `notify_round_bets_finalized()` sends final betting round's bets.
6. **Chip Animation**: `AnimatingBetChip` components move to pot over 500ms.
7. **Pot Update & Pulse**: `accumulatedPot` updated, `flashMainPot` triggers 500ms pulse.
8. **Animation Acknowledgment**: Frontend sends `animation_done` for `round_bets_finalized`.
9. **Backend State Clear**: All `player.current_bet = 0`.
10. **Showdown State Set**: `current_round = BettingRound.SHOWDOWN`.
11. **Hands Revealed**: `notify_showdown_hands_revealed()` sends:
    - `player_hands`: Array of `{player_id, cards}` for all non-folded players
12. **Card Display**: Frontend sets `showdownHands` state, revealing all hole cards simultaneously.
13. **All-In Street Dealing** (if needed): For each missing street:
    - Backend calls `deal_flop()`, `deal_turn()`, or `deal_river()`
    - `notify_street_dealt()` sends each street
    - Frontend reveals with 150ms card stagger
    - 1000ms pause between streets
    - `animation_done` sent for each street
14. **Hand Evaluation**: Backend calls `evaluate_hands()` and `_format_hand_description()`.
15. **Winners Determined**: `_handle_showdown()` populates `hand_winners` dict with `pot_id: [players]`.
16. **Winner Notification**: `notify_pot_winners_determined()` sends:
    - `pots`: Array of `{pot_id, amount, winners: [{player_id, amount, hand_description}]}`
17. **Pot Clear Animation**: Frontend sets main pot display to 0 (visual only).
18. **Chip Distribution Animation**: `potToPlayerAnimations` creates `AnimatingBetChip` components from pot to each winner over 500ms.
19. **Animation Acknowledgment**: Frontend sends `animation_done` for `pot_winners_determined`.
20. **Chip Count Update**: Backend updates `player.chips` and sends `notify_chips_distributed()` with full game state.
21. **Visual Chip Update**: Frontend updates displayed chip counts from new game state.
22. **Animation Acknowledgment**: Frontend sends `animation_done` for `chips_distributed`.
23. **Hand Conclusion**: Backend sends `notify_hand_visually_concluded()`.
24. **Winner Highlight**: Frontend applies `winner-pulse` CSS class (500ms yellow border animation).
25. **Animation Acknowledgment**: Frontend sends `animation_done` for `hand_visually_concluded`.
26. **Post-Hand Pause**: 1000ms wait before next hand.
27. **Next Hand Setup**: Backend calls `setup_next_hand()` → `deal_new_hand()`.

### Technical Architecture

#### Frontend
- **Platform:** Web-based, extendable to mobile (React Native or Flutter).
- **UI/UX:** User-friendly, emphasizing realism and intuitive interaction.

#### Backend
- **Framework:** Python (FastAPI) for game logic and API endpoints.
- **Data Storage:** 
  - Initial: In-memory storage for prototype development
  - Production: Supabase (PostgreSQL) with managed authentication and storage
- **Real-time communication:** WebSockets.
- **Database Architecture:** 
  - Repository pattern for data access abstraction
  - Local storage adapters during development
  - Structured for easy migration to Supabase in later phases

#### AI Integration Layer
- API layer abstracting interactions with multiple LLM providers.
- Robust handling of API requests, context injection, adaptive context windowing, response parsing.

### Monetization Opportunities
- Subscription-based premium coaching features and analytics through Supabase/Stripe integration.
- In-app purchases (scenarios, advanced AI models, coaching).
- Tiered membership model with increasing features and benefits.
- Secure access control for premium features.
- Analytics dashboard for subscription performance.
- Affiliate partnerships with poker platforms/events.

### Development Phases

**Phase 1: MVP**
- Basic gameplay mechanics
- Core archetypes (limited)
- AI integration with OpenAI's o3-mini-pro
- Basic coaching feedback and statistics

**Phase 2: Core Expansion**
- Additional playing styles and detailed player profiling
- Multi-scenario training environments
- Enhanced coaching (Anthropic Claude 3.7)

**Phase 3: Advanced Analytics and Monetization**
- Comprehensive player analytics and historical tracking
- Supabase integration for managed authentication and data storage
- Full monetization features via Supabase/Stripe integration
- Expanded API integration (Meta, xAI)
- Smooth migration from local storage to cloud database

### Deliverables
- Fully functional interactive poker trainer application.
- API abstraction for diverse LLM providers.
- Modular design supporting future expansions.
- Scalable subscription-based service through Supabase.
- Secure user authentication and payment processing.
- Analytics dashboard for both gameplay and business metrics.