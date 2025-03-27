# AI Integration for Chip Swinger Championship Poker Trainer

This module provides the AI integration layer for the Chip Swinger Championship Poker Trainer, including LLM provider abstraction, poker agents, and coaching functionality.

## Directory Structure

- `ai/` - Main AI package
  - `providers/` - LLM provider implementations
  - `agents/` - Poker agent implementations
  - `prompts/` - Prompt templates for different agents and scenarios
  - `examples/` - Example scripts demonstrating usage

## Configuration

The AI module can be configured using either environment variables or a JSON configuration file. For environment variables:

```
# Anthropic Configuration
ANTHROPIC_API_KEY=your_api_key
ANTHROPIC_MODEL=claude-3-7-sonnet-20250219  # Optional, this is the default
ANTHROPIC_THINKING_BUDGET=4000  # Optional, tokens for extended thinking

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o  # Options: gpt-4o, gpt-4o-mini, o1-pro, gpt-4.5-preview, o3-mini
# OPENAI_REASONING_LEVEL only applies to o3-mini (low, medium, high)
OPENAI_REASONING_LEVEL=medium
OPENAI_ORGANIZATION_ID=optional_org_id

# Google Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-pro  # Options: gemini-2.5-pro, gemini-2.0-flash, gemini-2.0-flash-thinking
# Optional generation parameters
# GEMINI_TEMPERATURE=0.7
# GEMINI_TOP_P=0.95
# GEMINI_TOP_K=0
# GEMINI_MAX_OUTPUT_TOKENS=1024

# Default provider selection
DEFAULT_LLM_PROVIDER=anthropic  # or openai, gemini
```

## Usage Examples

### Basic Usage

```python
from ai import LLMService

# Initialize the service (will use environment variables)
llm_service = LLMService()

# Generate a completion with Anthropic Claude (default)
response = await llm_service.complete(
    system_prompt="You are a helpful assistant.",
    user_prompt="What's the best strategy for beginners in poker?",
    temperature=0.7
)

# Generate a completion with OpenAI
response = await llm_service.complete(
    system_prompt="You are a helpful assistant.",
    user_prompt="What's the best strategy for beginners in poker?",
    temperature=0.7,
    provider="openai"
)
```

### Using Extended Thinking

```python
# With Anthropic Claude
response = await llm_service.complete(
    system_prompt="You are a poker coach.",
    user_prompt="Analyze this complex hand...",
    temperature=0.7,
    extended_thinking=True  # Enable extended thinking
)

# With OpenAI (o3-mini supports structured reasoning, other models use enhanced prompts)
response = await llm_service.complete(
    system_prompt="You are a poker coach.",
    user_prompt="Analyze this complex hand...",
    temperature=0.7,
    provider="openai",
    extended_thinking=True
)
```

### Generating JSON Responses

```python
json_schema = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["fold", "check", "call", "bet", "raise"]},
        "amount": {"type": "number"},
        "reasoning": {"type": "string"}
    },
    "required": ["action", "reasoning"]
}

# With Anthropic Claude
decision = await llm_service.complete_json(
    system_prompt="You are a poker player.",
    user_prompt="What action should I take with pocket aces?",
    json_schema=json_schema,
    temperature=0.7
)

# With OpenAI
decision = await llm_service.complete_json(
    system_prompt="You are a poker player.",
    user_prompt="What action should I take with pocket aces?",
    json_schema=json_schema,
    temperature=0.7,
    provider="openai"
)

# With Google Gemini
decision = await llm_service.complete_json(
    system_prompt="You are a poker player.",
    user_prompt="What action should I take with pocket aces?",
    json_schema=json_schema,
    temperature=0.7,
    provider="gemini"
)
```

## Available Providers

- **Anthropic Claude** - `anthropic` - Supporting Claude 3.7 Sonnet with Extended Thinking
- **OpenAI** - `openai` - Supporting GPT-4o (default), GPT-4o-mini, o1-pro, GPT-4.5-preview, and o3-mini
- **Google Gemini** - `gemini` - Supporting Gemini 2.5 Pro, Gemini 2.0 Flash, and Gemini 2.0 Flash Thinking

## Running Examples

To run the examples, first set your API keys:

```bash
# For Anthropic
export ANTHROPIC_API_KEY=your_api_key
python -m ai.examples.anthropic_example

# For OpenAI
export OPENAI_API_KEY=your_openai_api_key
python -m ai.examples.openai_example

# For Google Gemini
export GEMINI_API_KEY=your_gemini_api_key
python -m ai.examples.gemini_example
```