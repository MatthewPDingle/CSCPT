# AI Agent Memory Models

Defines the data structures and services for the AI's memory system.

## Directory Structure (`ai/agents/models/`)

```
ai/agents/models/
├── README.md
├── __init__.py
├── memory_connector.py
├── memory_service.py
└── opponent_profile.py
```

*   `README.md`: Documentation for the enhanced archetype memory system.
*   `__init__.py`: Initializes the `models` directory as a Python package.
*   `memory_connector.py`: Provides a simplified interface (`MemoryConnector`) for the backend to interact with the memory system.
*   `memory_service.py`: Implements the `MemoryService` class, managing persistent storage and retrieval of opponent profiles.
*   `opponent_profile.py`: Defines the Pydantic models (`OpponentProfile`, `StatisticValue`, `OpponentNote`) for storing opponent data.
