# Enhanced Archetype Memory System

This module implements a sophisticated memory and opponent modeling system for poker player archetypes, as outlined in the archetype implementation plan.

## Components

### 1. OpponentProfile

Detailed representation of opponent behaviors and tendencies, including:
- Statistical tracking (VPIP, PFR, etc.)
- Action tendencies in specific situations
- Hand range assessment
- Qualitative notes and observations
- Archetype detection
- Exploitability analysis

### 2. MemoryService

Persistent memory service that:
- Manages opponent profiles across sessions
- Stores and retrieves player data
- Tracks statistical trends over time
- Identifies exploitation opportunities
- Provides formatted opponent data for LLM prompts

### 3. MemoryConnector

Integration layer that connects the memory system to the game backend:
- Processes hand histories
- Updates profiles from observed actions
- Simplifies integration with minimal dependencies
- Provides backend-friendly data format

## Integration Points

### In Base Agent

The base PokerAgent class has been enhanced to:
- Access the shared memory service
- Process and update opponent profiles during gameplay
- Leverage memory for opponent modeling
- Update profiles after hand completion

### In Adaptable Agent

The AdaptableAgent has special enhancements:
- Dynamically adjusts strategy based on memory insights
- Implements sophisticated exploitation mechanisms
- Uses persistent memory for long-term opponent tracking
- Identifies and responds to table dynamics

## Usage

### Basic Memory Access

```python
from ai.agents.models import MemoryConnector

# Get singleton connector
connector = MemoryConnector.get_instance()

# Get a player profile
profile = connector.get_player_profile(player_id="123", name="Player123")

# Process a complete hand
connector.process_hand_history(hand_history)
```

### Archetype Integration

```python
from ai.agents import PokerAgent, AdaptableAgent

# Create agent with memory enabled
agent = AdaptableAgent(llm_service, use_persistent_memory=True)

# Make decision with enhanced memory
decision = await agent.make_decision(game_state, context)

# Update memory after hand
agent.update_memory_after_hand(hand_data)
```

## Future Enhancements

- **Session-level Memory**: Implement session-specific adaptations
- **Cross-game Learning**: Learn from patterns across multiple games
- **Dynamic Archetype Blending**: Adjust archetype behavior based on memory
- **Adaptation Metrics**: Track effectiveness of adaptation strategies
- **Multi-player Relationship Modeling**: Model relationships between player styles