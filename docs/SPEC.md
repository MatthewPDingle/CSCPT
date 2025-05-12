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

When a betting round completes (and the hand continues), the frontend must follow these non-overlapping steps:
1. The last player action is received and applied.
2. The Bets text box resets to 0.
3. All player bet indicators from that round animate into the Pot text box (0.5s).
4. The Pot text box updates to the new total and pulses yellow (0.5s).
5. If additional streets remain (Flop, Turn, River), reveal the next street:
   a. Flop: reveal three cards at once with sound, then pause 1s.
   b. Turn: reveal one card with sound, then pause 1s.
   c. River: reveal one card with sound, then pause 1s.
6. After the pause, gameplay resumes with the next betting round.

### Showdown Sequence (All-In Runout)

When the hand proceeds to showdown, the frontend must follow these non-overlapping steps:
1. The last player action is received and applied.
2. The Bets text box resets to 0.
3. Player bets animate into the Pot text box (0.5s).
4. The Pot text box updates to the new total and pulses yellow (0.5s).
5. All players reveal their hole cards face-up (pause 1s).
6. If undealt community cards remain, reveal each street with sound and a 1s pause:
   a. Flop: three cards reveal, sound, pause 1s.
   b. Turn: one card reveal, sound, pause 1s.
   c. River: one card reveal, sound, pause 1s.
7. Repeat steps 5–6 until all streets are shown.
8. Reset the Pot text box to 0.
9. Animate the Pot icon moving to the winning player(s) (0.5s).
10. Update the winning player(s)’ chip count.
11. Pulse the winning player(s)’ seat with a yellow border (0.5s).
12. Pause 1s to allow players to absorb the result.
13. Proceed to set up and deal the next hand.

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