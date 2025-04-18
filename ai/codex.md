# AI Layer

Handles interaction with Large Language Models (LLMs), defines player agent behaviors, and manages AI memory.

## Directory Structure (`ai/`)

```
ai/
├── README.md
├── __init__.py
├── config.py
├── llm_service.py
├── memory_integration.py
├── requirements.txt
├── .env.example
├── .gitignore
├── agents/
├── examples/
├── prompts/
├── providers/
└── tests/
```

*   `README.md`: Explains the AI module, its structure, configuration, and usage examples.
*   `__init__.py`: Initializes the `ai` directory as a Python package. Exports key classes like `AIConfig` and `LLMService`.
*   `config.py`: Handles loading and managing configuration for AI services (API keys, models) from environment variables or files.
*   `llm_service.py`: Core service for interacting with different LLM providers through a unified interface. Abstracts provider-specific implementations. *(Note: Provided file content is a mock for testing)*.
*   `memory_integration.py`: Facilitates interaction between the backend and the AI memory system. Contains logic for fetching agent decisions and processing hand history for memory updates. *(Note: Provided file content is a test script)*.
*   `requirements.txt`: Lists Python dependencies required specifically for the AI module.
*   `.env.example`: Example file showing necessary environment variables for API keys and configuration.
*   `.gitignore`: Specifies files and directories to be ignored by Git within the `ai` module.

See subdirectory `codex.md` files for more detailed information about specific components.
