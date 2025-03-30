# Advanced Adaptation Components

This module provides advanced adaptation capabilities for poker agents, allowing them to adjust their strategies based on changing game conditions, tournament stages, and exploitable patterns.

## Components

### 1. GameStateTracker

Tracks and analyzes game dynamics over time, identifying patterns and changes that may warrant strategic adjustments.

**Key Features:**
- Maintains a sliding window of hand histories
- Tracks table aggression, position effectiveness, and stack trends
- Detects significant changes in game dynamics
- Provides weighted analysis that prioritizes recent information
- Generates strategic recommendations based on observed patterns

### 2. TournamentStageAnalyzer

Identifies the current tournament stage and provides strategic recommendations based on tournament context.

**Key Features:**
- Classifies tournament stages (early, middle, bubble, final table, late)
- Calculates ICM implications and bubble pressure
- Determines M-Zone awareness (Harrington's M)
- Provides stage-specific strategic recommendations
- Generates player-specific advice based on stack size

### 3. ExploitAnalyzer (Coming Soon)

Will identify exploitable patterns in opponents and recommend strategies to capitalize on them.

### 4. StrategyAdjuster (Coming Soon)

Will apply recommended adjustments to base strategies.

## Integration

The `AdaptationManager` class provides a unified interface for using all adaptation components together. It can be integrated with any poker agent using the `enhance_agent_with_adaptation` function, which adds the adaptation capabilities to the agent's decision-making process.

Example usage:

```python
from ai.agents.adaptation.integration import enhance_agent_with_adaptation

# Create a poker agent
agent = AdaptableAgent(llm_service)

# Enhance the agent with advanced adaptation
enhance_agent_with_adaptation(agent)

# The agent will now have access to all adaptation components
# and will include adaptation information in its decisions
```

## Tournament Stage Awareness

The TournamentStageAnalyzer component provides awareness of different tournament stages and their strategic implications:

### Early Stage
- Deep stacks and lower blind pressure
- Focus on chip accumulation without excessive risk
- Standard ranges with some speculative play

### Middle Stage
- Moderate stack depths and increasing blind pressure
- Increased aggression with position leverage
- Tighter ranges, more steal attempts

### Bubble Stage
- High ICM pressure near the money
- ICM-aware cautious play with selective aggression
- Tighter calling ranges, maintained aggression with strong hands

### Final Table
- Significant payout implications
- Dynamic play with payout ladder awareness
- Adjust strategy based on payout structure and stack sizes

### Late Stage
- In-the-money play with ladder-up considerations
- Target medium stacks afraid to bust
- Looser aggression, tighter calling

## M-Zone Awareness

The TournamentStageAnalyzer also provides awareness of Harrington's M-Zones:

### Red Zone (M < 5)
- Critical push/fold territory
- Look for any push opportunity with decent equity
- Greatly expanded shoving range

### Orange Zone (5 <= M < 10)
- High pressure zone
- Selective aggression with strong holdings
- Avoid calling all-ins without premium hands

### Yellow Zone (10 <= M < 20)
- Caution zone
- Prioritize maintaining stack above 10 BBs
- Controlled aggression

### Green Zone (M >= 20)
- Comfortable stack
- Standard play with ICM awareness
- Full strategic flexibility