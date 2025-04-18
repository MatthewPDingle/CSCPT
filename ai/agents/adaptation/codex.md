# AI Agent Adaptation

Modules responsible for advanced agent adaptation based on game context.

## Directory Structure (`ai/agents/adaptation/`)

```
ai/agents/adaptation/
├── README.md
├── __init__.py
├── exploit_analyzer.py
├── game_state_tracker.py
├── integration.py
├── strategy_adjuster.py
├── tournament_analyzer.py
├── examples/
└── tests/
```

*   `README.md`: Explains the advanced adaptation components and their purpose.
*   `__init__.py`: Initializes the `adaptation` directory as a Python package.
*   `exploit_analyzer.py`: Analyzes opponent behavior to identify exploitable patterns (currently a placeholder).
*   `game_state_tracker.py`: Tracks and analyzes game dynamics (aggression, stack trends) over time.
*   `integration.py`: Provides utilities (`AdaptationManager`, `enhance_agent_with_adaptation`) to integrate adaptation components into agents.
*   `strategy_adjuster.py`: Applies recommended strategic adjustments to agent behavior (currently a placeholder).
*   `tournament_analyzer.py`: Analyzes the current tournament stage (early, bubble, final table) and provides strategic recommendations.
*   `examples/`: Contains examples demonstrating the adaptation components.
*   `tests/`: Contains unit tests for the adaptation components.
