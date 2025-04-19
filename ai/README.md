# AI Integration for Chip Swinger Championship Poker Trainer

This module provides the AI integration layer for the Chip Swinger Championship Poker Trainer, including LLM provider abstraction, poker agents, and coaching functionality.

## Directory Structure

- `ai/` - Main AI package
  - `providers/` - LLM provider implementations
  - `agents/` - Poker agent implementations
    - `base_agent.py` - Abstract base class for all poker agents
    - `tag_agent.py` - Tight-Aggressive player implementation
    - `lag_agent.py` - Loose-Aggressive player implementation
    - `archetype_implementation_plan.md` - Detailed design document
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

# With OpenAI (o3-mini supports structured reasoning, o1-pro has built-in reasoning)
response = await llm_service.complete(
    system_prompt="You are a poker coach.",
    user_prompt="Analyze this complex hand...",
    temperature=0.7,
    provider="openai",
    extended_thinking=True  # Only affects o3-mini, o1-pro already uses advanced reasoning
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

- **Anthropic Claude** - `anthropic` - Supporting Claude 3.7 Sonnet with native Extended Thinking
- **OpenAI** - `openai` - Supporting GPT-4o (default), GPT-4o-mini, GPT-4.1, GPT-4.1-mini, GPT-4.1-nano, GPT-4.5-preview, o3-mini, o4-mini with structured JSON thinking, and o1-pro with advanced reasoning via Responses API
- **Google Gemini** - `gemini` - Supporting Gemini 2.5 Pro, Gemini 2.0 Flash, and Gemini 2.0 Flash Thinking with prompt-engineered reasoning

## Poker Agents

The AI module includes implementations of different poker player archetypes that can make decisions based on game state:

### Implemented Player Archetypes

1. **TAG (Tight-Aggressive)**
   - Disciplined, selective, value-oriented playing style
   - Focuses on premium hand selection and aggressive betting when in a hand
   - Default temperature: 0.5 (more consistent decision making)

2. **LAG (Loose-Aggressive)**
   - Creative, dynamic, pressure-oriented playing style
   - Plays a wider range of hands with frequent aggression and bluffing
   - Default temperature: 0.8 (more variable and creative play)

3. **Tight-Passive (Rock/Nit)**
   - Extremely risk-averse and conservative playing style
   - Only plays premium hands and avoids confrontation
   - Default temperature: 0.4 (highly predictable play)

4. **Calling Station**
   - Passive and call-oriented playing style
   - Overly optimistic about hand strength, reluctant to fold
   - Default intelligence: basic (limited opponent modeling)

5. **Loose-Passive (Fish)**
   - Recreational, entertainment-focused playing style
   - Plays many hands pre-flop but passively
   - Default intelligence: basic (limited opponent modeling)

6. **Maniac**
   - Ultra-aggressive with minimal hand requirements
   - Raise and re-raise constantly with little regard for hand strength
   - Default temperature: 0.9 (highly unpredictable play)

7. **Beginner**
   - Makes fundamental strategic mistakes
   - Inconsistent decision making without coherent strategy
   - Default extended_thinking: False (doesn't think deeply)

8. **Adaptable**
   - Shifts strategy based on table dynamics
   - Identifies and exploits opponent weaknesses
   - Custom implementation with strategy adjustment

9. **GTO (Game Theory Optimal)**
   - Mathematically balanced and theoretically unexploitable
   - Uses mixed strategies and range-based thinking
   - Focus on theoretically optimal play

10. **Short Stack**
    - Specialized in playing with smaller stacks
    - Push/fold focused strategy with binary decisions
    - Custom implementation with stack size awareness

11. **Trappy (Slow-Player)**
    - Deceptive and trap-setting playing style
    - Focused on disguising hand strength to induce mistakes
    - Advanced intelligence for identifying bluffing tendencies

### Agent Response Parsing

The module includes a response parser to validate and normalize agent decisions:

```python
from ai.agents import AgentResponseParser

# Parse a response from an agent
action, amount, metadata = AgentResponseParser.parse_response(agent_response)

# Apply game rules to ensure the action is valid
action, amount = AgentResponseParser.apply_game_rules(action, amount, game_state)

# Check if a response is valid
is_valid = AgentResponseParser.is_valid_response(agent_response)
```

### Using Poker Agents

```python
from ai.llm_service import LLMService
from ai.agents import TAGAgent, LAGAgent

# Initialize the service
llm_service = LLMService()

# Create agent instances with different providers
tag_agent = TAGAgent(llm_service, provider="anthropic")
lag_agent = LAGAgent(llm_service, provider="openai")

# Example game state
game_state = {
    "hand": ["As", "Kh"],  # Player's hole cards
    "community_cards": ["Jd", "Tc", "2s"],  # Board cards
    "position": "BTN",  # Button position
    "pot": 120,  # Current pot size
    "action_history": [  # Previous actions in the hand
        {"player_id": "1", "action": "fold"},
        {"player_id": "2", "action": "raise", "amount": 20},
        {"player_id": "3", "action": "call", "amount": 20}
    ],
    "stack_sizes": {  # Current chip stacks
        "0": 500,  # Current player (you)
        "1": 320,
        "2": 650,
        "3": 480
    }
}

# Game context
context = {
    "game_type": "tournament",  # or "cash"
    "stage": "middle",  # early, middle, bubble, final_table
    "blinds": [10, 20]  # Small blind, big blind
}

# Get decisions from the agents
tag_decision = await tag_agent.make_decision(game_state, context)
lag_decision = await lag_agent.make_decision(game_state, context)

# Agent response format includes thinking, action, amount, and reasoning
print(f"TAG decision: {tag_decision['action']} {tag_decision['amount']}")
print(f"TAG reasoning: {tag_decision['reasoning']['hand_assessment']}")

print(f"LAG decision: {lag_decision['action']} {lag_decision['amount']}")
print(f"LAG reasoning: {lag_decision['reasoning']['hand_assessment']}")
```

## Running Examples and Tests

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

# Run the poker agent example
python -m ai.examples.agent_example

# Run the response parser example
python -m ai.examples.parser_example

# Compare all player archetypes
python -m ai.examples.archetype_showcase
```

### Running Tests

The project includes both unit tests and integration tests:

#### Unit Tests

Unit tests use mocked responses and don't require API keys:

```bash
# Run all unit tests
python -m ai.tests.test_llm_service

# Test specific providers
python -m ai.tests.test_gemini_provider
```

#### Integration Tests

Integration tests make real API calls to verify provider behavior and require valid API keys:

```bash
# Run all integration tests for all providers
python -m ai.tests.run_integration_tests

# Test specific providers
python -m ai.examples.gemini_model_test
python -m ai.examples.openai_model_test
python -m ai.examples.anthropic_model_test

# Test all providers with a simple example
python -m ai.examples.all_providers_example
```

For detailed implementation notes and provider capabilities, see the [NOTE.md](NOTE.md) file.