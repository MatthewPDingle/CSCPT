# Chip Swinger Championship Poker Trainer
## Comprehensive Design and Implementation Specification

### Overview
This specification outlines the development of an interactive poker training application exclusively focused on Texas Hold'em, realistically simulating live poker scenarios. It leverages Large Language Models (LLMs) as intelligent agents representing diverse poker player archetypes, integrating advanced coaching functionalities and comprehensive statistics to guide and educate players.

### Core Features

#### Game Setup
- **Poker Variant:** Exclusively Texas Hold'em.
- **Training Environments:**
  - Cash game
  - Tournament with customizable parameters:
    - Tournament level (buy-in, stakes)
    - Tournament stage (early, mid, late, final table)
    - Player's stack size
    - Common payout structures
- **Table Customization:** User selects table size (2–9 players).
- **Player Archetypes:**
  - Tight Aggressive (TAG)
  - Loose Aggressive (LAG)
  - Tight Passive
  - Calling Station
  - Maniac
  - Beginner (Noob)
  - Custom or random assignment based on training environment

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

### Technical Architecture

#### Frontend
- **Platform:** Web-based, extendable to mobile (React Native or Flutter).
- **UI/UX:** User-friendly, emphasizing realism and intuitive interaction.

#### Backend
- **Framework:** Python (FastAPI or Django REST Framework) or Node.js.
- **Data Storage:** PostgreSQL or MongoDB.
- **Real-time communication:** WebSockets.

#### AI Integration Layer
- API layer abstracting interactions with multiple LLM providers.
- Robust handling of API requests, context injection, adaptive context windowing, response parsing.

### Monetization Opportunities
- Subscription-based premium coaching features and analytics.
- In-app purchases (scenarios, advanced AI models, coaching).
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
- Full monetization features
- Expanded API integration (Meta, xAI)

### Deliverables
- Fully functional interactive poker trainer application.
- API abstraction for diverse LLM providers.
- Modular design supporting future expansions.