# AI Agents

Implements the logic and prompts for different AI player styles.

## Directory Structure (`ai/agents/`)

```
ai/agents/
├── __init__.py
├── adaptable_agent.py
├── archetype_implementation_plan.md
├── base_agent.py
├── beginner_agent.py
├── calling_station_agent.py
├── gto_agent.py
├── lag_agent.py
├── loose_passive_agent.py
├── maniac_agent.py
├── response_parser.py
├── short_stack_agent.py
├── tag_agent.py
├── tight_passive_agent.py
├── trappy_agent.py
├── adaptation/
└── models/
```

*   `__init__.py`: Initializes the `agents` directory as a Python package and exports agent classes.
*   `adaptable_agent.py`: Implements the 'Adaptable' AI player archetype that adjusts strategy based on game dynamics and opponents.
*   `archetype_implementation_plan.md`: Design document detailing the philosophy and plan for implementing various player archetypes.
*   `base_agent.py`: Defines the abstract base class (`PokerAgent`) that all player archetypes inherit from. Includes common logic for decision making and opponent profiling.
*   `beginner_agent.py`: Implements the 'Beginner' (Noob) AI player archetype.
*   `calling_station_agent.py`: Implements the 'Calling Station' AI player archetype.
*   `gto_agent.py`: Implements the 'Game Theory Optimal' (GTO) AI player archetype.
*   `lag_agent.py`: Implements the 'Loose-Aggressive' (LAG) AI player archetype.
*   `loose_passive_agent.py`: Implements the 'Loose-Passive' (Fish) AI player archetype.
*   `maniac_agent.py`: Implements the 'Maniac' AI player archetype.
*   `response_parser.py`: Contains the `AgentResponseParser` class for parsing and validating structured JSON responses from AI agents.
*   `short_stack_agent.py`: Implements the 'Short Stack' specialist AI player archetype.
*   `tag_agent.py`: Implements the 'Tight-Aggressive' (TAG) AI player archetype.
*   `tight_passive_agent.py`: Implements the 'Tight-Passive' (Rock/Nit) AI player archetype.
*   `trappy_agent.py`: Implements the 'Trappy' (Slow-Player) AI player archetype.

See subdirectory `codex.md` files for more detailed information about specific components.
