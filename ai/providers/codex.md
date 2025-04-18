# AI Providers

Contains the implementations for interacting with specific LLM APIs.

## Directory Structure (`ai/providers/`)

```
ai/providers/
├── __init__.py
├── anthropic_provider.py
├── gemini_provider.py
└── openai_provider.py
```

*   `__init__.py`: Initializes the `providers` package, defines the abstract `LLMProvider` base class, and exports the concrete provider implementations.
*   `anthropic_provider.py`: Implementation for interacting with the Anthropic Claude API.
*   `gemini_provider.py`: Implementation for interacting with the Google Gemini API.
*   `openai_provider.py`: Implementation for interacting with the OpenAI API (using the Responses API).
