# Memory System Documentation

This document provides detailed information about the memory system implementation for Chip Swinger Championship Poker Trainer. The memory system enables AI players to track opponent behaviors and adapt their strategies across sessions.

## Overview

The memory system provides player archetypes with the ability to:

1. **Track Opponent Statistics**: VPIP, PFR, and other key poker metrics
2. **Maintain Qualitative Notes**: Observations about specific tendencies
3. **Identify Exploitable Patterns**: Areas where opponents can be exploited
4. **Adapt Strategically**: Change tactics based on observed behaviors
5. **Persist Information**: Maintain memory across game sessions

## Architecture

The memory system consists of the following components:

### Core Models

- **OpponentProfile**: Comprehensive model for tracking player behaviors
- **StatisticValue**: Represents statistical measurements with confidence levels
- **OpponentNote**: Stores qualitative observations about opponents

### Memory Service

- **MemoryService**: Manages persistent storage of player profiles
- **MemoryConnector**: Provides simplified interface for backend components
- **Integration API**: Centralized functions for integration with the game

### Backend Integration

- **HandHistoryRecorder Integration**: Updates memory based on completed hands
- **API Endpoints**: Web endpoints for querying and managing memory
- **Fast Path Integration**: Direct integration with action processing

## Implementation Details

### Opponent Profile

Each opponent profile stores the following information:

- **Basic Information**: Player ID, name, detected archetype
- **Statistics**: Key poker metrics (VPIP, PFR, etc.) with confidence levels
- **Notes**: Qualitative observations with timestamps and categories
- **Exploitability Assessment**: Detected weaknesses that can be exploited
- **History Data**: Number of hands observed, first/last observation times

Each statistic tracks:
- The current value
- Confidence level (0.0-1.0)
- Sample size
- Last update timestamp

### Memory Service

The memory service manages profiles and provides methods for:

- **Profile Management**: Creating, retrieving, and updating profiles
- **Hand Processing**: Processing complete hand histories
- **Action Analysis**: Updating profiles based on individual actions
- **Formatted Output**: Generating LLM-friendly representations

### Persistence

Profiles are stored as JSON files in a designated directory (`~/.cscpt/memory/` by default):

```json
{
  "player_id": "player123",
  "name": "Player 123",
  "archetype": "TAG",
  "stats": {
    "VPIP": {
      "value": 0.23,
      "confidence": 0.75,
      "sample_size": 42,
      "last_updated": "2025-03-30T14:52:33.123456"
    },
    "PFR": {
      "value": 0.18,
      "confidence": 0.7,
      "sample_size": 42,
      "last_updated": "2025-03-30T14:52:33.123456"
    }
  },
  "notes": [
    {
      "id": "note_1",
      "note": "Bluffs river frequently",
      "category": "bluffing",
      "hand_id": "hand_123",
      "timestamp": "2025-03-30T14:30:22.123456",
      "confidence": 0.8
    }
  ],
  "exploitable_tendencies": [
    "Folds to 3-bets",
    "Overvalues top pair"
  ],
  "hands_observed": 42
}
```

## Using the Memory System

### In Base Agent

The base PokerAgent class has been enhanced to:
- Access the shared memory service
- Process and update opponent profiles during gameplay
- Leverage memory for opponent modeling
- Update profiles after hand completion

```python
# Access the memory service
memory_service = PokerAgent.get_memory_service()

# Get formatted profiles for LLM prompt
profiles_string = memory_service.get_formatted_profiles()
```

### In Adaptable Agent

The AdaptableAgent has special enhancements:
- Dynamically adjusts strategy based on memory insights
- Implements sophisticated exploitation mechanisms
- Uses persistent memory for long-term opponent tracking
- Identifies and responds to table dynamics

```python
# In the Adaptable agent
def _update_adaptation_strategy(self, game_state: Dict[str, Any]) -> None:
    # Get player archetypes from memory
    table_archetypes = {}
    for player_id in player_ids:
        profile = self.memory_service.get_profile(player_id)
        if profile.archetype and profile.hands_observed >= 10:
            table_archetypes[profile.archetype] = table_archetypes.get(profile.archetype, 0) + 1
            
    # Adapt strategy based on table composition
    if aggressive_archetypes > passive_archetypes:
        self.current_strategy = "counter-aggressive"
    elif passive_archetypes > aggressive_archetypes:
        self.current_strategy = "exploit-passive"
```

### In Backend

The memory system integrates with the HandHistoryRecorder to process completed hands:

```python
# In HandHistoryRecorder.end_hand()
if MEMORY_SYSTEM_AVAILABLE:
    try:
        # Convert the hand history to a dictionary
        hand_dict = self.current_hand.dict()
        
        # Process in memory system
        MemoryIntegration.process_hand_history(hand_dict)
    except Exception as e:
        print(f"Error processing hand in memory system: {str(e)}")
```

### In API

The memory system exposes several API endpoints:

```
GET /ai/status - Get status of memory system
POST /ai/decision - Get a decision from an AI agent
GET /ai/profiles - Get all player profiles
GET /ai/profiles/{player_id} - Get a specific player's profile
POST /ai/memory/enable - Enable memory features
POST /ai/memory/disable - Disable memory features
DELETE /ai/memory/clear - Clear all memory data
```

## Memory Integration Flow

1. **Initialization**:
   - Memory service is initialized during application startup
   - Default storage location is created if it doesn't exist
   - Existing profiles are loaded if available

2. **Action Recording**:
   - Player actions during gameplay are recorded via HandHistoryRecorder
   - Actions update player statistics (VPIP, PFR, etc.)
   - Notes are generated based on observed patterns

3. **Hand Processing**:
   - Complete hands are processed after completion
   - Statistics are updated with weighted averaging
   - Archetype detection runs after sufficient hands

4. **Decision Influence**:
   - Agent decisions incorporate memory data
   - Adaptable agents modify strategies based on table
   - Exploitable tendencies guide decision making

5. **Persistence**:
   - Profiles are saved automatically after updates
   - Memory persists between application restarts
   - Profiles can be backed up or transferred

## Configuration Options

The memory system offers several configuration options:

1. **Enable/Disable**: Memory features can be enabled or disabled
2. **Storage Location**: Default is `~/.cscpt/memory/` but can be changed
3. **Intelligence Levels**: Different levels of opponent modeling
   - Basic: No opponent modeling
   - Intermediate: Simple statistics
   - Advanced: Full statistics with pattern recognition
   - Expert: Complete modeling with exploit detection

## Testing

The memory system includes comprehensive tests:

1. **Unit Tests**: Tests for individual components
2. **Integration Tests**: Tests for component interactions
3. **End-to-End Tests**: Tests for complete workflows
4. **Manual Tests**: Interactive test script for exploration

Run tests with:
```
cd ai
python test_memory_system.py
```

## Future Enhancements

Potential future enhancements include:

1. **Database Integration**
   - Move from file-based storage to a proper database
   - Support for concurrent access and transactions

2. **Advanced Analytics**
   - Pattern recognition across multiple hands
   - More sophisticated archetype detection
   - Correlation analysis between behaviors

3. **Enhanced Visualization**
   - UI components to display opponent profiles
   - Visualizations of player tendencies
   - Recommendation system for exploiting opponents

4. **Learning System**
   - Self-improving agents that learn from past encounters
   - Shared knowledge base across agent instances
   - Meta-learning for strategy optimization