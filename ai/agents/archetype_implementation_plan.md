# Poker Player Archetype Implementation Plan

## Philosophy: "Guided Freedom" Approach

We'll implement player archetypes using a balanced approach that:
- Provides clear archetype characteristics and principles without rigid rules
- Leverages LLMs' ability to embody personas and make contextual decisions
- Enables tracking and comparison of different prompting strategies

## Core Archetype Implementation

### 1. Prompt Engineering Approaches

We'll test multiple prompting strategies:

**A. Pure Description Method**
- Rich qualitative descriptions of archetype's poker philosophy 
- No explicit hand ranges or mathematical formulas
- Example: "TAG players are patient, disciplined, and value-driven..."

**B. Principles + Examples Method**
- Core principles paired with example scenarios/responses
- Models learn by example rather than explicit rules
- Example: "When facing a 3-bet with marginal holdings, TAG players typically..."

**C. Guided Parameters Method**
- Flexible guidelines with soft boundaries
- Focus on decision-making process rather than rigid formulas
- Example: "As a LAG, you typically play 30-45% of hands, but adapt based on table dynamics..."

### 2. Intelligence/Skill Parameters

We'll implement a configurable "intelligence" parameter that affects:

**Opponent Modeling Capacity**
- **Basic**: Remembers limited information about 1-2 recent opponents
- **Intermediate**: Tracks statistical patterns across multiple opponents
- **Advanced**: Builds sophisticated player profiles with nuanced tendencies
- **Expert**: Identifies exploitable patterns and adapts strategy accordingly

**Memory Capacity**
- Scales with intelligence level - higher intelligence allows tracking more hands/players
- Ability to distinguish signal from noise in opponent behavior

**Default Setting**: Maximum intelligence (using full LLM capabilities) unless specified otherwise

### 2. Initial Archetypes to Implement

**TAG (Tight-Aggressive)**
- **Core Identity**: Disciplined, selective, value-oriented
- **Decision Principles**: Position-aware, strong hand requirements, clear post-flop plan
- **Key Behaviors**: Premium hand selection, straightforward betting, value extraction

**LAG (Loose-Aggressive)**
- **Core Identity**: Creative, unpredictable, pressure-focused
- **Decision Principles**: Leverages fold equity, balances ranges, creates tough decisions
- **Key Behaviors**: Wide range pre-flop, frequent aggression, varied sizing

## Technical Implementation

### 1. Input Structure
```json
{
  "game_state": {
    "hand": ["As", "Kh"],
    "community_cards": ["Jd", "Tc", "2s"],
    "pot": 120,
    "position": "BTN",
    "action_history": [...],
    "stack_sizes": {...}
  },
  "opponent_profiles": {...},
  "context": {
    "game_type": "tournament",
    "stage": "middle",
    "blinds": [10, 20],
    "player_archetype": "TAG"
  }
}
```

### 2. Output Structure
```json
{
  "thinking": "I have AK with a J-T-2 board, giving me top pair top kicker. I'm in position on the button which is advantageous. Villain has folded to continuation bets in similar spots. The pot is 120 and effective stacks are still deep. My hand is strong but vulnerable to draws. As a TAG player, this is a clear value betting spot where I should protect my hand and extract value.",
  
  "action": "raise",
  "amount": 80,
  "reasoning": {
    "hand_assessment": "Top pair top kicker, strong but vulnerable",
    "positional_considerations": "Button position gives advantage",
    "opponent_reads": "Villain has shown weakness to continuation bets",
    "archetype_alignment": "Raising for value aligns with TAG approach"
  },
  "calculations": {
    "pot_odds": "3:1",
    "estimated_equity": "70%"
  }
}
```

The `thinking` field provides an explicit reasoning process that:
- Works for both reasoning and non-reasoning models
- Shows internal deliberation before decision-making
- Helps with debugging and understanding model behavior
- Maintains transparency in the decision process

### 3. Memory and Tracking System

**Opponent Profile Format:**
```
Player2: [VPIP:30%][PFR:22%][3Bet:12%][FoldTo3Bet:60%][CBet:75%]
[Noted:BluffsRivers,WeakVsCheckRaise,OvervaluesTopPair]
```

**Implementation Options:**
- In-context memory (limited by window size)
- Session persistence using simple storage
- Compressed notation for efficiency

## Testing and Evaluation Framework

### 1. Archetype Fidelity Metrics
- **Statistical Tracking**: VPIP, PFR, 3bet%, etc.
- **Decision Pattern Analysis**: Classification of plays against archetype expectations
- **Consistency Scoring**: Variance in approach across similar situations
- **Leaderboards**: Track which prompting strategies best maintain archetype characteristics

### 2. Performance Evaluation
- Win rate in controlled environments
- Decision quality assessment
- Adaptivity to changing conditions
- Expert review of critical hand histories

### 3. A/B Testing Framework
- Identical scenarios with different prompting approaches
- Evaluation of which prompting strategy produces:
  - Most authentic archetype behavior
  - Strongest play
  - Most consistent decisions

### 4. ELO Rating System (Future)
- Implement ELO ratings for different models/prompts
- Track performance across multiple games
- Create tournament structures to identify strongest approaches
- Historical performance tracking across versions

## Implementation Roadmap

### Phase 1: Basic Archetype Framework (Current Focus)
- Implement TAG and LAG archetypes
- Test different prompting strategies
- Develop basic evaluation metrics

### Phase 2: Enhanced Archetypes with Memory
- Add opponent modeling capabilities
- Implement session-to-session memory
- Add more nuanced archetypes (Nit, Calling Station, etc.)

### Phase 3: Advanced Adaptation
- Implement dynamic adjustment to changing conditions
- Add tournament stage awareness
- Create exploit-aware behaviors

### Phase 4: Optimization and Refinement
- Performance tuning based on evaluation data
- Prompt optimization for consistency and strength
- Implementation of meta-strategy capabilities

## Known Challenges & Mitigation

1. **Style Drift**
   - **Solution**: Regular reinforcement of archetype characteristics
   - **Monitoring**: Track key metrics to detect drift

2. **Calculation Reliability**
   - **Solution**: Self-verification steps in prompt
   - **Fallback**: Pre-calculated common scenarios

3. **Context Window Limitations**
   - **Solution**: Compressed notation for histories
   - **Alternative**: External memory systems

4. **Provider Inconsistencies**
   - **Solution**: Provider-specific prompt adjustments
   - **Testing**: Cross-provider comparison framework