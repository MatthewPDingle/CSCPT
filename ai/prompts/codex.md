# AI Prompts

Contains prompt templates for guiding LLM behavior.

## Directory Structure (`ai/prompts/`)

```
ai/prompts/
├── __init__.py
└── agent_prompts.py
```

*   `__init__.py`: Initializes the `prompts` package and defines the `POKER_ACTION_SCHEMA` used for agent responses. Exports archetype system prompts.
*   `agent_prompts.py`: Contains the detailed system prompts defining the characteristics and playing style for each AI player archetype.
