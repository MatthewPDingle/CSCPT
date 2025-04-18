# AI Tests

Contains tests for the AI layer components.

## Directory Structure (`ai/tests/`)

```
ai/tests/
├── __init__.py
├── run_integration_tests.py
├── run_tests.py
├── test_agents.py
├── test_gemini_provider.py
├── test_llm_service.py
├── test_llm_service_gemini.py
├── test_llm_service_openai.py
├── test_openai_provider.py
└── test_response_parser.py
```

*   `__init__.py`: Initializes the `tests` package.
*   `run_integration_tests.py`: Script to run integration tests against live LLM APIs using the example scripts.
*   `run_tests.py`: Script to discover and run all unit tests within the `ai/tests` directory.
*   `test_agents.py`: Unit tests for the various `PokerAgent` implementations.
*   `test_gemini_provider.py`: Unit tests specifically for the `GeminiProvider` (likely using mocks).
*   `test_llm_service.py`: Unit tests for the `LLMService` abstraction layer and potentially Anthropic provider mocks.
*   `test_llm_service_gemini.py`: Unit tests focused on the `LLMService` integration with the Gemini provider mock.
*   `test_llm_service_openai.py`: Unit tests focused on the `LLMService` integration with the OpenAI provider mock.
*   `test_openai_provider.py`: Unit tests specifically for the `OpenAIProvider` (likely using mocks).
*   `test_response_parser.py`: Unit tests for the `AgentResponseParser`.
