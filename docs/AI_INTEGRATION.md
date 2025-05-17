# Chip Swinger Championship Poker Trainer
## AI Integration Design

This document outlines the AI integration design for the Chip Swinger Championship Poker Trainer, detailing how Large Language Models (LLMs) are utilized to create realistic poker opponents and provide coaching feedback.

## Overview

The AI integration in the Chip Swinger Championship Poker Trainer consists of three primary components:

1. **LLM Provider Abstraction Layer**: A unified interface for interacting with multiple LLM providers (Anthropic Claude, OpenAI GPT, Google Gemini)
2. **AI Poker Agents**: LLM-powered agents that play as opponents with distinct playing styles and adaptive capabilities
3. **AI Poker Coach**: An LLM-powered coach that provides analysis, feedback, and strategic advice

All components rely on well-engineered prompt templates, context management, and response parsing to create realistic and educational poker experiences.

## LLM Provider Abstraction Layer

The LLM service provides a unified interface across multiple providers, allowing for seamless switching while maintaining consistent behavior.

### Provider Implementation Status

#### 1. Anthropic Provider
- **Status**: Successfully implemented
- **Supported Models**: claude-3-7-sonnet-20250219
- **Features**:
  - Basic completion ✅
  - JSON completion ✅
  - Extended thinking ✅
- **Notes**:
  - Extended thinking requires temperature=1.0 as per API requirements
  - Thinking budget tokens configurable via environment variables

#### 2. OpenAI Provider
- **Status**: Successfully implemented
- **Supported Models**: gpt-4o, gpt-4o-mini, gpt-4.5-preview, o3-mini, o1-pro
- **Features**:
  - Basic completion ✅
  - JSON completion ✅
  - Native reasoning ✅ (o1-pro, o3-mini only)
- **Notes**:
  - All models use the Responses API endpoint for consistency
  - Enhanced JSON extraction for models that return code blocks
  - o3-mini does not support temperature parameter
  - o1-pro does not support temperature parameter
  - o1-pro and o3-mini are native reasoning models with dedicated reasoning API parameters
  - Other models use prompt enhancement for step-by-step thinking

#### 3. Gemini Provider
- **Status**: Successfully implemented
- **Supported Models**: gemini-2.5-pro, gemini-2.0-flash, gemini-2.0-flash-thinking
- **Features**:
  - Basic completion ✅
  - JSON completion ✅ (for supported models)
  - Native reasoning ✅ (gemini-2.5-pro, gemini-2.0-flash-thinking)
- **Notes**:
  - Robust error handling for different API response structures
  - Enhanced extraction of responses with multi-layer fallback mechanisms
  - Comprehensive null checking to prevent "list index out of range" errors
  - Fallback JSON creation when API responses are incomplete or malformed
  - gemini-2.0-flash-thinking does not support JSON mode
  - gemini-2.5-pro and gemini-2.0-flash-thinking are native reasoning models
  - gemini-2.0-flash uses prompt enhancement for step-by-step thinking

### Common Interface

The LLM service provides a unified interface for all providers:

```python
async def complete(
    system_prompt: str,
    user_prompt: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    provider: Optional[str] = None,
    extended_thinking: bool = False
) -> str
```

```python
async def complete_json(
    system_prompt: str,
    user_prompt: str,
    json_schema: Dict[str, Any],
    temperature: Optional[float] = None,
    provider: Optional[str] = None,
    extended_thinking: bool = False
) -> Dict[str, Any]
```

### Feature Comparison

| Feature | Anthropic Claude | OpenAI GPT | Google Gemini |
|---------|-----------------|------------|---------------|
| Basic text generation | ✅ | ✅ | ✅ |
| JSON structured output | ✅ | ✅ | ✅ (most models) |
| Reasoning Models | ✅ (Sonnet 3.7 with Extended Thinking) | ✅ (o1-pro, o3-mini) | ✅ (gemini-2.5-pro, gemini-2.0-flash-thinking) |
| API Endpoint | Messages API | Responses API | GenerativeLanguage API |
| Temperature control | ✅ (not available with Extended Thinking) | ❌ (o1-pro, o3-mini), ✅ (others) | ✅ |

## AI Poker Agents

### Player Archetypes

The system implements 11 distinct player archetypes, each with a specific playing style. These archetypes are implemented using a "Guided Freedom" approach that provides clear characteristics and principles without rigid rules, leveraging LLMs' ability to embody personas and make contextual decisions.

#### Core Archetypes

1. **TAG (Tight-Aggressive)**
   - **Core Identity**: Disciplined, selective, value-oriented
   - **Decision Principles**: Position-aware, strong hand requirements, clear post-flop plan
   - **Key Behaviors**: Premium hand selection, straightforward betting, value extraction
   - **Default Settings**: Temperature 0.5 (more consistent decision making)

2. **LAG (Loose-Aggressive)**
   - **Core Identity**: Creative, unpredictable, pressure-focused
   - **Decision Principles**: Leverages fold equity, balances ranges, creates tough decisions
   - **Key Behaviors**: Wide range pre-flop, frequent aggression, varied sizing
   - **Default Settings**: Temperature 0.8 (more variable and creative play)

3. **TightPassive (Rock/Nit)**
   - **Core Identity**: Conservative, risk-averse, value-focused
   - **Decision Principles**: Prefers premium hands, avoids confrontation, minimizes variance
   - **Key Behaviors**: Selective hand choice, calling over raising, cautious post-flop play
   - **Default Settings**: Temperature 0.4 (highly predictable play)

4. **CallingStation**
   - **Core Identity**: Passive, draw-chasing, pot-committed
   - **Decision Principles**: Focuses on absolute hand value rather than relative strength
   - **Key Behaviors**: Frequent calling, chase draws regardless of odds, rarely folds once invested
   - **Default Settings**: Basic intelligence (limited opponent modeling)

5. **LoosePassive (Fish)**
   - **Core Identity**: Curious, speculative, passive
   - **Decision Principles**: Plays many hands but cautiously
   - **Key Behaviors**: Wide pre-flop range, minimal aggression, can fold to pressure
   - **Default Settings**: Basic intelligence (limited opponent modeling)

6. **Maniac**
   - **Core Identity**: Hyper-aggressive, unpredictable, action-oriented
   - **Decision Principles**: Maximum pressure, disregards conventional strategy
   - **Key Behaviors**: Constant aggression, very wide range, frequent bluffing
   - **Default Settings**: Temperature 0.9 (highly unpredictable play)

7. **Beginner**
   - **Core Identity**: Inexperienced, fundamental errors, basic understanding
   - **Decision Principles**: Simplistic hand valuation, limited strategic depth
   - **Key Behaviors**: Plays too many hands, fails to consider position, overvalues weak holdings
   - **Default Settings**: Extended thinking disabled (doesn't think deeply)

8. **Adaptable**
   - **Core Identity**: Observant, flexible, exploitative
   - **Decision Principles**: Adjusts strategy based on opponents and table dynamics
   - **Key Behaviors**: Changes gear as needed, identifies and exploits weaknesses
   - **Default Settings**: Custom implementation with strategy adjustment, memory-enhanced

9. **GTO (Game Theory Optimal)**
   - **Core Identity**: Balanced, mathematical, unexploitable
   - **Decision Principles**: Range-based thinking, balanced actions, mixed strategies
   - **Key Behaviors**: Proper bet sizing, balanced ranges, theoretically sound plays
   - **Default Settings**: Expert intelligence, extended thinking enabled

10. **ShortStack**
    - **Core Identity**: Stack-aware, simplified decision tree, push/fold expert
    - **Decision Principles**: Leverages fold equity, simplifies decisions with shallow stack
    - **Key Behaviors**: Aggressive pre-flop play, commitment decisions, ICM awareness
    - **Default Settings**: Custom implementation with stack size awareness

11. **Trappy (Slow-Player)**
    - **Core Identity**: Deceptive, patient, value-maximizing
    - **Decision Principles**: Underrepresent hand strength to induce action
    - **Key Behaviors**: Check-raising, delayed aggression, inducing bluffs
    - **Default Settings**: Advanced intelligence for identifying bluffing tendencies

### Implementation Approach

The implementation of these archetypes follows a "Guided Freedom" approach with three primary prompt engineering strategies:

1. **Pure Description Method**
   - Rich qualitative descriptions of the archetype's poker philosophy
   - No explicit hand ranges or mathematical formulas
   - Example: "TAG players are patient, disciplined, and value-driven..."

2. **Principles + Examples Method**
   - Core principles paired with example scenarios/responses
   - Models learn by example rather than explicit rules
   - Example: "When facing a 3-bet with marginal holdings, TAG players typically..."

3. **Guided Parameters Method**
   - Flexible guidelines with soft boundaries
   - Focus on decision-making process rather than rigid formulas
   - Example: "As a LAG, you typically play 30-45% of hands, but adapt based on table dynamics..."

### Intelligence and Skill Parameters

Each agent can be configured with different "intelligence" levels that affect:

- **Opponent Modeling Capacity**
  - **Basic**: Remembers limited information about 1-2 recent opponents
  - **Intermediate**: Tracks statistical patterns across multiple opponents
  - **Advanced**: Builds sophisticated player profiles with nuanced tendencies
  - **Expert**: Identifies exploitable patterns and adapts strategy accordingly

- **Memory Capacity**
  - Scales with intelligence level - higher intelligence allows tracking more hands/players
  - Ability to distinguish signal from noise in opponent behavior

By default, agents use the maximum intelligence level unless specified otherwise.

### Agent Implementation

```python
class PokerAgent:
    """Base class for poker agents."""
    
    def __init__(self, agent_id, archetype, llm_service):
        """Initialize a poker agent."""
        self.agent_id = agent_id
        self.archetype = archetype
        self.llm_service = llm_service
        self.memory = []
        self.prompt_templates = self._load_prompt_templates()
    
    def _load_prompt_templates(self):
        """Load prompt templates for the agent's archetype."""
        with open(f'prompts/{self.archetype.lower()}_agent.txt', 'r') as file:
            system_prompt = file.read()
        
        return {
            "system": system_prompt,
            "decision": self._load_decision_template(),
            "reflection": self._load_reflection_template()
        }
    
    def _load_decision_template(self):
        """Load the decision prompt template."""
        return """
        You are playing as a {archetype} poker player.
        
        Current game state:
        - Your cards: {hole_cards}
        - Community cards: {community_cards}
        - Your stack: {stack}
        - Current pot: {pot}
        - Current bet: {current_bet}
        - Your current bet: {player_bet}
        - Position: {position}
        - Players remaining: {players_remaining}
        - Player actions this round: {player_actions}
        - Previous street actions: {previous_actions}
        
        What action do you take (fold, check, call, bet, raise) and why?
        If betting or raising, specify the amount.
        
        Respond in JSON format:
        {{
            "action": "fold|check|call|bet|raise",
            "amount": 0,
            "reasoning": "Your thought process..."
        }}
        """
    
    def _load_reflection_template(self):
        """Load the reflection prompt template."""
        return """
        Reflect on the hand you just played:
        
        Your cards: {hole_cards}
        Community cards: {community_cards}
        Your actions: {player_actions}
        All player actions: {all_actions}
        Hand result: {result}
        
        How do you feel about your play? What would you do differently? 
        How will this affect your future strategy against these players?
        """
    
    async def make_decision(self, game_state, player_id):
        """
        Make a poker decision based on the current game state.
        
        Args:
            game_state: Current state of the poker game
            player_id: ID of the player making the decision
            
        Returns:
            Dict with action, amount, and reasoning
        """
        # Extract relevant information from game state
        visible_state = self._create_visible_state(game_state, player_id)
        
        # Update agent memory with new information
        self._update_memory(visible_state)
        
        # Create the context for the LLM
        context = self._prepare_decision_context(visible_state)
        
        # Make API call to LLM
        response = await self.llm_service.complete(
            system_prompt=self.prompt_templates["system"],
            user_prompt=context,
            temperature=0.7,
            max_tokens=500
        )
        
        # Parse the response
        parsed_decision = self._parse_decision(response)
        
        # Update memory with decision
        self._add_decision_to_memory(parsed_decision)
        
        return parsed_decision
    
    def _create_visible_state(self, game_state, player_id):
        """
        Create a view of the game state visible to this player.
        Hide other players' hole cards.
        """
        visible_state = copy.deepcopy(game_state)
        
        # Hide other players' hole cards
        for pid, player in visible_state.players.items():
            if pid != player_id:
                player.hole_cards = ["HIDDEN", "HIDDEN"]
        
        return visible_state
    
    def _update_memory(self, visible_state):
        """Update agent memory with new game state information."""
        # Extract relevant game state information
        game_snapshot = {
            "phase": visible_state.phase,
            "community_cards": [str(card) for card in visible_state.community_cards],
            "pot": visible_state.pot.total(),
            "player_actions": self._extract_player_actions(visible_state),
            "timestamp": time.time()
        }
        
        # Add to memory, keeping memory window manageable
        self.memory.append(game_snapshot)
        if len(self.memory) > 50:  # Keep last 50 states
            self.memory = self.memory[-50:]
    
    def _extract_player_actions(self, game_state):
        """Extract player actions from the game state."""
        # Implementation depends on game state structure
        # Return a structured representation of player actions
        pass
    
    def _prepare_decision_context(self, visible_state):
        """Prepare the context for the LLM decision."""
        player = visible_state.players[self.agent_id]
        
        # Format hole cards
        hole_cards = ", ".join([str(card) for card in player.hole_cards])
        
        # Format community cards
        community_cards = ", ".join([str(card) for card in visible_state.community_cards]) if visible_state.community_cards else "None"
        
        # Format player actions
        current_round_actions = self._format_current_round_actions(visible_state)
        previous_actions = self._format_previous_actions(visible_state)
        
        # Get positional information
        position = self._determine_position(visible_state, self.agent_id)
        
        # Format the decision prompt
        decision_prompt = self.prompt_templates["decision"].format(
            archetype=self.archetype,
            hole_cards=hole_cards,
            community_cards=community_cards,
            stack=player.stack,
            pot=visible_state.pot.total(),
            current_bet=visible_state.current_bet,
            player_bet=player.bet,
            position=position,
            players_remaining=self._count_active_players(visible_state),
            player_actions=current_round_actions,
            previous_actions=previous_actions
        )
        
        return decision_prompt
    
    def _format_current_round_actions(self, game_state):
        """Format the actions taken in the current betting round."""
        # Implementation depends on game state structure
        pass
    
    def _format_previous_actions(self, game_state):
        """Format the actions taken in previous betting rounds."""
        # Implementation depends on game state structure
        pass
    
    def _determine_position(self, game_state, player_id):
        """Determine the player's position (early, middle, late, blind)."""
        # Implementation depends on game state structure
        pass
    
    def _count_active_players(self, game_state):
        """Count the number of active players (not folded or all-in)."""
        return len([p for p in game_state.players.values() 
                  if not p.folded and not p.sitting_out])
    
    def _parse_decision(self, response):
        """Parse the LLM response into a structured decision."""
        try:
            # Extract JSON from response
            # This might need regex or other parsing depending on LLM output format
            decision_json = json.loads(response)
            
            # Validate the decision format
            if "action" not in decision_json:
                raise ValueError("Response missing 'action' field")
                
            if decision_json["action"] in ["bet", "raise"] and "amount" not in decision_json:
                decision_json["amount"] = 0
                
            return decision_json
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback to a default decision if parsing fails
            return {
                "action": "fold",
                "amount": 0,
                "reasoning": "Decision parsing failed: " + str(e)
            }
    
    def _add_decision_to_memory(self, decision):
        """Add the agent's decision to memory."""
        if self.memory:
            self.memory[-1]["agent_decision"] = decision
    
    async def reflect_on_hand(self, hand_history):
        """
        Reflect on a completed hand to adapt future strategy.
        
        Args:
            hand_history: Complete history of the hand
        
        Returns:
            Reflection insights that can influence future decisions
        """
        reflection_prompt = self.prompt_templates["reflection"].format(
            hole_cards=", ".join([str(card) for card in hand_history["hole_cards"]]),
            community_cards=", ".join([str(card) for card in hand_history["community_cards"]]),
            player_actions=self._format_player_actions(hand_history, self.agent_id),
            all_actions=self._format_all_actions(hand_history),
            result=hand_history["result"]
        )
        
        response = await self.llm_service.complete(
            system_prompt=self.prompt_templates["system"],
            user_prompt=reflection_prompt,
            temperature=0.7,
            max_tokens=500
        )
        
        # Update agent memory with reflection
        self._add_reflection_to_memory(response)
        
        return response
    
    def _format_player_actions(self, hand_history, player_id):
        """Format the actions taken by a specific player in the hand."""
        # Implementation depends on hand history structure
        pass
    
    def _format_all_actions(self, hand_history):
        """Format all player actions in the hand."""
        # Implementation depends on hand history structure
        pass
    
    def _add_reflection_to_memory(self, reflection):
        """Add the agent's reflection to memory."""
        self.memory.append({
            "type": "reflection",
            "content": reflection,
            "timestamp": time.time()
        })
```

### Agent Factory

```python
class PokerAgentFactory:
    """Factory for creating poker agents of different archetypes."""
    
    def __init__(self, llm_service):
        """Initialize the agent factory."""
        self.llm_service = llm_service
        self.agent_classes = {
            "TAG": TAGAgent,
            "LAG": LAGAgent,
            "TIGHT_PASSIVE": TightPassiveAgent,
            "CALLING_STATION": CallingStationAgent,
            "MANIAC": ManiacAgent,
            "BEGINNER": BeginnerAgent
        }
    
    def create_agent(self, agent_id, archetype):
        """
        Create a poker agent of the specified archetype.
        
        Args:
            agent_id: Unique identifier for the agent
            archetype: The agent's playing style (TAG, LAG, etc.)
            
        Returns:
            A PokerAgent instance of the appropriate subclass
        """
        if archetype not in self.agent_classes:
            raise ValueError(f"Unsupported agent archetype: {archetype}")
            
        agent_class = self.agent_classes[archetype]
        return agent_class(agent_id, archetype, self.llm_service)
```

### Agent Subclasses

```python
class TAGAgent(PokerAgent):
    """Tight Aggressive poker agent."""
    
    def _load_prompt_templates(self):
        """Load TAG-specific prompt templates."""
        templates = super()._load_prompt_templates()
        # Add or modify templates specific to TAG strategy
        return templates
    
    def _prepare_decision_context(self, visible_state):
        """Prepare TAG-specific decision context."""
        context = super()._prepare_decision_context(visible_state)
        # Add TAG-specific context elements
        return context


class LAGAgent(PokerAgent):
    """Loose Aggressive poker agent."""
    
    def _load_prompt_templates(self):
        """Load LAG-specific prompt templates."""
        templates = super()._load_prompt_templates()
        # Add or modify templates specific to LAG strategy
        return templates
    
    def _prepare_decision_context(self, visible_state):
        """Prepare LAG-specific decision context."""
        context = super()._prepare_decision_context(visible_state)
        # Add LAG-specific context elements
        return context


# Similar implementations for other agent types...
```

### LLM Service

```python
class LLMService:
    """Service for interacting with Language Model APIs."""
    
    def __init__(self, api_config):
        """Initialize the LLM service."""
        self.api_config = api_config
        self.client = self._initialize_client()
        
    def _initialize_client(self):
        """Initialize the appropriate API client based on config."""
        provider = self.api_config.get("provider", "openai")
        
        if provider == "openai":
            return OpenAIClient(self.api_config["openai"])
        elif provider == "anthropic":
            return AnthropicClient(self.api_config["anthropic"])
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
            
    async def complete(self, system_prompt, user_prompt, temperature=0.7, max_tokens=None):
        """
        Generate a completion from the LLM.
        
        Args:
            system_prompt: System message for the LLM
            user_prompt: User message for the LLM
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            The LLM's response text
        """
        return await self.client.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
    async def complete_json(self, system_prompt, user_prompt, json_schema, temperature=0.7):
        """
        Generate a JSON-structured completion from the LLM.
        
        Args:
            system_prompt: System message for the LLM
            user_prompt: User message for the LLM
            json_schema: JSON schema to validate against
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Parsed JSON response
        """
        return await self.client.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema=json_schema,
            temperature=temperature
        )
```

### Provider-Specific Clients

```python
class OpenAIClient:
    """Client for OpenAI API."""
    
    def __init__(self, config):
        """Initialize the OpenAI client."""
        self.api_key = config["api_key"]
        self.model = config.get("model", "gpt-4-turbo")
        import openai
        openai.api_key = self.api_key
        self.client = openai.Client()
        
    async def complete(self, system_prompt, user_prompt, temperature=0.7, max_tokens=None):
        """Generate a completion using OpenAI."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
            
        response = await self.client.chat.completions.create(**params)
        return response.choices[0].message.content
        
    async def complete_json(self, system_prompt, user_prompt, json_schema, temperature=0.7):
        """Generate a JSON-structured completion using OpenAI."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)


class AnthropicClient:
    """Client for Anthropic API."""
    
    def __init__(self, config):
        """Initialize the Anthropic client."""
        self.api_key = config["api_key"]
        self.model = config.get("model", "claude-3-7-sonnet-20240229")
        import anthropic
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
    async def complete(self, system_prompt, user_prompt, temperature=0.7, max_tokens=None):
        """Generate a completion using Anthropic Claude."""
        params = {
            "model": self.model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": temperature
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
            
        response = await self.client.messages.create(**params)
        return response.content[0].text
        
    async def complete_json(self, system_prompt, user_prompt, json_schema, temperature=0.7):
        """Generate a JSON-structured completion using Anthropic Claude."""
        # Add instructions to generate valid JSON
        json_instruction = f"Respond with a JSON object that follows this schema: {json.dumps(json_schema)}"
        combined_prompt = f"{user_prompt}\n\n{json_instruction}"
        
        response_text = await self.complete(
            system_prompt=system_prompt,
            user_prompt=combined_prompt,
            temperature=temperature
        )
        
        # Extract and parse the JSON response
        # This might need regex or other parsing depending on Claude's output format
        try:
            # Try to parse the entire response as JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON with regex
            import re
            json_pattern = r'```json\s*([\s\S]*?)\s*```'
            match = re.search(json_pattern, response_text)
            if match:
                return json.loads(match.group(1))
            else:
                raise ValueError("Could not extract valid JSON from response")
```

## AI Poker Coach

### Coach Implementation

```python
class PokerCoach:
    """AI poker coach that provides analysis and advice."""
    
    def __init__(self, llm_service):
        """Initialize the poker coach."""
        self.llm_service = llm_service
        self.prompt_templates = self._load_prompt_templates()
        self.conversation_history = []
        
    def _load_prompt_templates(self):
        """Load the coach prompt templates."""
        with open('prompts/coach_system.txt', 'r') as file:
            system_prompt = file.read()
            
        return {
            "system": system_prompt,
            "hand_analysis": self._load_hand_analysis_template(),
            "strategy_advice": self._load_strategy_advice_template(),
            "opponent_analysis": self._load_opponent_analysis_template(),
            "interactive_chat": self._load_interactive_chat_template()
        }
    
    def _load_hand_analysis_template(self):
        """Load the hand analysis prompt template."""
        return """
        Please analyze this poker hand:
        
        Player cards: {hole_cards}
        Community cards: {community_cards}
        
        Hand action:
        {hand_action}
        
        Player stack: {player_stack}
        Pot size: {pot_size}
        
        Provide a comprehensive analysis including:
        1. Pre-flop decisions
        2. Flop play
        3. Turn decisions
        4. River play
        5. Overall hand strategy
        6. Alternative approaches
        7. Key mistakes or missed opportunities
        """
    
    def _load_strategy_advice_template(self):
        """Load the strategy advice prompt template."""
        return """
        Please provide strategic advice for a {skill_level} player on:
        
        Topic: {topic}
        
        Context:
        {context}
        
        Tailor your advice to be:
        - Practical and actionable
        - Appropriate for the player's skill level
        - Focused on long-term skill development
        - Illustrated with concrete examples
        """
    
    def _load_opponent_analysis_template(self):
        """Load the opponent analysis prompt template."""
        return """
        Analyze this opponent based on their play history:
        
        Opponent: {opponent_name}
        
        Recent hands:
        {recent_hands}
        
        Statistics:
        - VPIP: {vpip}
        - PFR: {pfr}
        - AF: {af}
        - 3-bet: {three_bet}
        - Fold to 3-bet: {fold_to_three_bet}
        - WTSD: {wtsd}
        
        Provide an analysis of:
        1. Player's likely archetype
        2. Hand range estimation
        3. Exploitable tendencies
        4. Recommended counter-strategies
        """
    
    def _load_interactive_chat_template(self):
        """Load the interactive chat prompt template."""
        return """
        Player question: {question}
        
        Current game context:
        {game_context}
        
        Conversation history:
        {conversation_history}
        
        Provide a helpful, educational response addressing the player's question.
        If relevant, include strategic advice and explanations of poker concepts.
        """
    
    async def analyze_hand(self, hand_history, player_id):
        """
        Analyze a completed poker hand.
        
        Args:
            hand_history: Complete history of the hand
            player_id: ID of the player to analyze for
            
        Returns:
            Comprehensive hand analysis
        """
        player = next((p for p in hand_history["players"] if p["player_id"] == player_id), None)
        if not player:
            raise ValueError(f"Player {player_id} not found in hand history")
            
        # Format the hand analysis prompt
        analysis_prompt = self.prompt_templates["hand_analysis"].format(
            hole_cards=", ".join([str(card) for card in player["hole_cards"]]),
            community_cards=", ".join([str(card) for card in hand_history["community_cards"]]),
            hand_action=self._format_hand_action(hand_history),
            player_stack=player["starting_stack"],
            pot_size=hand_history["pot"]["main"]
        )
        
        # Get analysis from LLM
        analysis = await self.llm_service.complete(
            system_prompt=self.prompt_templates["system"],
            user_prompt=analysis_prompt,
            temperature=0.5,
            max_tokens=1500
        )
        
        # Store analysis in conversation history
        self._update_conversation_history("system", "hand_analysis", analysis_prompt, analysis)
        
        return analysis
    
    def _format_hand_action(self, hand_history):
        """Format the action sequence of a hand for analysis."""
        streets = ["preflop", "flop", "turn", "river"]
        formatted_action = []
        
        for street in streets:
            if street in hand_history["actions"]:
                street_actions = hand_history["actions"][street]
                formatted_action.append(f"*** {street.upper()} ***")
                if street == "flop":
                    formatted_action.append(f"Board: {', '.join(str(c) for c in hand_history['community_cards'][:3])}")
                elif street == "turn":
                    formatted_action.append(f"Board: {', '.join(str(c) for c in hand_history['community_cards'][:4])}")
                elif street == "river":
                    formatted_action.append(f"Board: {', '.join(str(c) for c in hand_history['community_cards'])}")
                
                for action in street_actions:
                    player_name = next((p["name"] for p in hand_history["players"] 
                                     if p["player_id"] == action["player_id"]), "Unknown")
                    act_str = f"{player_name}: {action['action']}"
                    if action['action'] in ["bet", "raise"]:
                        act_str += f" {action['amount']}"
                    formatted_action.append(act_str)
        
        return "\n".join(formatted_action)
    
    async def get_strategy_advice(self, topic, skill_level, context=""):
        """
        Get strategic advice on a poker topic.
        
        Args:
            topic: The poker topic to get advice on
            skill_level: Player's skill level (beginner, intermediate, advanced)
            context: Additional context for the advice
            
        Returns:
            Strategic advice on the requested topic
        """
        advice_prompt = self.prompt_templates["strategy_advice"].format(
            topic=topic,
            skill_level=skill_level,
            context=context
        )
        
        advice = await self.llm_service.complete(
            system_prompt=self.prompt_templates["system"],
            user_prompt=advice_prompt,
            temperature=0.5,
            max_tokens=1200
        )
        
        self._update_conversation_history("user", "strategy_advice", advice_prompt, advice)
        
        return advice
    
    async def analyze_opponent(self, opponent_data, recent_hands):
        """
        Analyze an opponent based on their play history.
        
        Args:
            opponent_data: Statistics and information about the opponent
            recent_hands: Recent hands played by the opponent
            
        Returns:
            Analysis of the opponent's playing style and tendencies
        """
        # Format recent hands
        formatted_hands = self._format_recent_hands(recent_hands, opponent_data["player_id"])
        
        analysis_prompt = self.prompt_templates["opponent_analysis"].format(
            opponent_name=opponent_data["name"],
            recent_hands=formatted_hands,
            vpip=opponent_data["stats"].get("vpip", "Unknown"),
            pfr=opponent_data["stats"].get("pfr", "Unknown"),
            af=opponent_data["stats"].get("af", "Unknown"),
            three_bet=opponent_data["stats"].get("three_bet", "Unknown"),
            fold_to_three_bet=opponent_data["stats"].get("fold_to_three_bet", "Unknown"),
            wtsd=opponent_data["stats"].get("wtsd", "Unknown")
        )
        
        analysis = await self.llm_service.complete(
            system_prompt=self.prompt_templates["system"],
            user_prompt=analysis_prompt,
            temperature=0.5,
            max_tokens=1000
        )
        
        self._update_conversation_history("system", "opponent_analysis", analysis_prompt, analysis)
        
        return analysis
    
    def _format_recent_hands(self, recent_hands, opponent_id):
        """Format recent hands for opponent analysis."""
        formatted_hands = []
        
        for i, hand in enumerate(recent_hands):
            opponent = next((p for p in hand["players"] if p["player_id"] == opponent_id), None)
            if not opponent:
                continue
                
            formatted_hands.append(f"Hand #{i+1}:")
            formatted_hands.append(f"Opponent cards: {', '.join(str(c) for c in opponent['hole_cards'])}")
            formatted_hands.append(f"Community cards: {', '.join(str(c) for c in hand['community_cards'])}")
            
            # Add actions
            for street in ["preflop", "flop", "turn", "river"]:
                if street in hand["actions"]:
                    street_actions = [a for a in hand["actions"][street] if a["player_id"] == opponent_id]
                    if street_actions:
                        formatted_hands.append(f"{street.capitalize()}: {', '.join(a['action'] for a in street_actions)}")
            
            # Add result
            result = "won" if opponent["player_id"] in hand.get("winners", []) else "lost"
            formatted_hands.append(f"Result: {result}\n")
        
        return "\n".join(formatted_hands)
    
    async def chat(self, question, game_context=None):
        """
        Handle an interactive chat question from the player.
        
        Args:
            question: The player's question
            game_context: Current game context (optional)
            
        Returns:
            Coach's response to the question
        """
        # Format conversation history
        formatted_history = self._format_conversation_history()
        
        # Format game context
        formatted_context = self._format_game_context(game_context) if game_context else "No game in progress."
        
        chat_prompt = self.prompt_templates["interactive_chat"].format(
            question=question,
            game_context=formatted_context,
            conversation_history=formatted_history
        )
        
        response = await self.llm_service.complete(
            system_prompt=self.prompt_templates["system"],
            user_prompt=chat_prompt,
            temperature=0.7,
            max_tokens=800
        )
        
        self._update_conversation_history("user", "chat", question, response)
        
        return response
    
    def _format_conversation_history(self):
        """Format the conversation history for context."""
        if not self.conversation_history:
            return "No previous conversation."
            
        # Format only the last 10 exchanges to avoid context overload
        recent_history = self.conversation_history[-10:]
        formatted_history = []
        
        for entry in recent_history:
            if entry["role"] == "user":
                formatted_history.append(f"Player: {entry['content']}")
            else:
                formatted_history.append(f"Coach: {entry['content']}")
                
        return "\n".join(formatted_history)
    
    def _format_game_context(self, game_context):
        """Format the current game context for the coach."""
        formatted_context = []
        
        if "phase" in game_context:
            phase_names = {
                0: "Waiting", 1: "Preflop", 2: "Flop", 
                3: "Turn", 4: "River", 5: "Showdown"
            }
            formatted_context.append(f"Phase: {phase_names.get(game_context['phase'], 'Unknown')}")
            
        if "player" in game_context:
            player = game_context["player"]
            formatted_context.append(f"Your cards: {', '.join(str(c) for c in player['hole_cards'])}")
            formatted_context.append(f"Your stack: {player['stack']}")
            formatted_context.append(f"Your position: {player.get('position', 'Unknown')}")
            
        if "community_cards" in game_context:
            cards = game_context["community_cards"]
            if cards:
                formatted_context.append(f"Community cards: {', '.join(str(c) for c in cards)}")
                
        if "pot" in game_context:
            formatted_context.append(f"Current pot: {game_context['pot']}")
            
        if "current_bet" in game_context:
            formatted_context.append(f"Current bet: {game_context['current_bet']}")
            
        if "players" in game_context:
            formatted_context.append("Other players:")
            for p in game_context["players"]:
                if p.get("player_id") != game_context.get("player", {}).get("player_id"):
                    status = "active"
                    if p.get("folded"):
                        status = "folded"
                    elif p.get("all_in"):
                        status = "all-in"
                    formatted_context.append(f"- {p['name']}: {status}, Stack: {p['stack']}")
                    
        return "\n".join(formatted_context)
    
    def _update_conversation_history(self, role, type, prompt, response):
        """Update the conversation history with a new exchange."""
        self.conversation_history.append({
            "role": role,
            "type": type,
            "content": prompt if role == "user" else response,
            "timestamp": time.time()
        })
        
        # Keep history manageable
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
```

## Integration with Game Engine

The AI integration in this project involves multiple components working together to create a seamless experience where AI players can participate in poker games alongside human players. The integration follows a modular approach, where the core poker engine can interact with the AI agents through well-defined interfaces.

### Updated Backend-AI Integration Flow

The integration between the backend game engine and AI agents follows this workflow:

1. **Player Setup**: During game setup, players are created with `is_human` and `archetype` parameters.
2. **Turn Management**: When a player's turn is detected, the system checks if they are human or AI.
3. **AI Decision Process**:
   - If AI, the backend calls `_request_and_process_ai_action` asynchronously
   - The game state is converted to a format suitable for AI consumption
   - The AI agent is queried via `MemoryIntegration.get_agent_decision`
   - The agent's decision is validated and processed in the game state
   - The result is broadcast to all players
4. **Chain of AI Actions**: If multiple AI players act in sequence, each action triggers the next
5. **Human Notification**: When an AI action results in a human player's turn, the system sends an action request to the human player

### Key Components

#### Memory Integration Layer

The `MemoryIntegration` class serves as a bridge between the backend and AI agents:

```python
class MemoryIntegration:
    """Integration class for AI memory and decision systems."""
    
    # Class-level references for easy access
    _memory_service = None
    _memory_enabled = False
    
    @classmethod
    async def get_agent_decision(cls, archetype, game_state, context, player_id, 
                               use_memory=True, intelligence_level="expert"):
        """
        Get a decision from an agent using the memory system.
        
        Args:
            archetype: The type of agent to use (e.g., "TAG", "LAG")
            game_state: The current state of the game
            context: Additional context information
            player_id: The ID of the player making the decision
            use_memory: Whether to use memory for this decision
            intelligence_level: The agent's intelligence level
            
        Returns:
            A dictionary containing the agent's decision
        """
        # Create an agent with specified parameters
        agent = AgentFactory.create_agent(
            archetype=archetype,
            use_memory=use_memory,
            intelligence_level=intelligence_level
        )
        
        # Add player_id to game state if not already there
        if isinstance(game_state, dict) and "player_id" not in game_state:
            game_state["player_id"] = player_id
        
        # Make decision
        return await agent.make_decision(game_state, context)
    
    @classmethod
    def get_all_profiles(cls):
        """Get all player profiles from memory."""
        if not cls._memory_service:
            return []
        
        return [
            profile.to_dict() 
            for player_id, profile in cls._memory_service.active_profiles.items()
        ]
    
    @classmethod
    def get_player_profile(cls, player_id):
        """Get a specific player's profile."""
        if not cls._memory_service:
            return None
            
        profile = cls._memory_service.get_profile(player_id)
        if profile:
            return profile.to_dict()
        return None
    
    @classmethod
    def is_memory_enabled(cls):
        """Check if memory system is enabled."""
        return cls._memory_enabled
    
    @classmethod
    def enable_memory(cls):
        """Enable the memory system."""
        connector = MemoryConnector.get_instance()
        connector.enable()
        cls._memory_enabled = True
```

#### Backend AI Processing in GameService

The `GameService` class has been enhanced with a new asynchronous method for processing AI actions:

```python
async def _request_and_process_ai_action(self, game_id: str, player_id: str):
    """
    Request a decision from an AI player and process it in the game.
    
    This method will:
    1. Get the game and player information
    2. Prepare the game state for the AI
    3. Request a decision from the appropriate AI agent
    4. Process the resulting action in the game
    5. Notify clients of the action and state changes
    """
    # Import AI memory integration
    from ai.memory_integration import MemoryIntegration
    from ai.agents.response_parser import AgentResponseParser
    
    # Retrieve the game and poker game
    game = self.game_repo.get(game_id)
    poker_game = self.poker_games.get(game_id)
    
    # Find the player in the domain model
    domain_player = next((p for p in game.players if p.id == player_id), None)
    
    # Verify this is an AI player
    if domain_player.is_human:
        return
        
    # Find the player in the poker game
    poker_player = next((p for p in poker_game.players if p.player_id == player_id), None)
    
    # Get archetype and intelligence level (with defaults)
    archetype = domain_player.archetype or "TAG"
    intelligence_level = "expert"
    
    # Prepare game state for AI consumption
    game_state = game_to_model(game_id, poker_game)
    
    # Filter sensitive information - only show this player's cards
    game_state_dict = game_state.dict()
    for player_model in game_state_dict["players"]:
        if player_model["player_id"] != player_id:
            player_model["cards"] = None
    
    try:
        # Request decision from AI
        ai_decision = await MemoryIntegration.get_agent_decision(
            archetype=archetype,
            game_state=game_state_dict,
            context=context,
            player_id=player_id,
            use_memory=True,
            intelligence_level=intelligence_level
        )
        
        # Parse and validate the response
        action, amount, metadata = AgentResponseParser.parse_response(ai_decision)
        
        # Process the action in the poker game
        await poker_game.process_action(poker_player, poker_action, action_amount)
        
        # Notify clients
        await game_notifier.notify_player_action(game_id, player_id, action_type, action_amount)
        await game_notifier.notify_game_update(game_id, poker_game)
        
        # Check if hand is complete or if it's next player's turn
        if poker_game.current_round == BettingRound.SHOWDOWN:
            await game_notifier.notify_hand_result(game_id, poker_game)
            self._start_new_hand(game)
        else:
            # If next player is AI, trigger their action
            next_player = active_players[poker_game.current_player_idx]
            next_player_domain = next((p for p in game.players if p.id == next_player.player_id), None)
            
            if next_player_domain and not next_player_domain.is_human:
                # Trigger next AI player action asynchronously
                asyncio.create_task(self._request_and_process_ai_action(
                    game_id, next_player.player_id
                ))
            else:
                # If human, send action request
                await game_notifier.notify_action_request(game_id, poker_game)
        
    except Exception as e:
        # Default to fold on error
        await poker_game.process_action(poker_player, PokerPlayerAction.FOLD, None)
```

#### WebSocket Game Flow Updates

The WebSocket handler has been updated to check for AI players and trigger their actions:

```python
async def process_action_message(websocket, game_id, message, player_id, service):
    """Process a player action WebSocket message."""
    # Process the human player's action
    success = await poker_game.process_action(player, action_type, action_amount)
    
    # Notify about updated game state
    await game_notifier.notify_game_update(game_id, poker_game)
    
    # Check if next player is AI
    active_players = [p for p in poker_game.players 
                     if p.status in {PlayerStatus.ACTIVE, PlayerStatus.ALL_IN}]
    
    if active_players and poker_game.current_player_idx < len(active_players):
        next_player = active_players[poker_game.current_player_idx]
        game = service.get_game(game_id)
        
        if game:
            next_player_domain = next((p for p in game.players 
                                     if p.id == next_player.player_id), None)
            
            if next_player_domain and not next_player_domain.is_human:
                # AI player's turn - trigger AI action asynchronously
                asyncio.create_task(service._request_and_process_ai_action(
                    game_id, next_player.player_id
                ))
                return  # AI will handle the turn
    
    # If hand is complete, notify about results
    if poker_game.current_round == BettingRound.SHOWDOWN:
        await game_notifier.notify_hand_result(game_id, poker_game)
    else:
        # Send action request to next player (if human)
        await game_notifier.notify_action_request(game_id, poker_game)
```

#### GameStateNotifier Updates

The `GameStateNotifier` has been enhanced to only send action requests to human players:

```python
async def notify_action_request(self, game_id: str, game: PokerGame):
    """
    Notify the current player that it's their turn to act.
    Only sends action requests to human players.
    """
    active_players = [p for p in game.players 
                     if p.status in {PlayerStatus.ACTIVE, PlayerStatus.ALL_IN}]
    if not active_players or game.current_player_idx >= len(active_players):
        return
        
    current_player = active_players[game.current_player_idx]
    
    # Check if player is human before sending action request
    try:
        service = GameService.get_instance()
        game_obj = service.get_game(game_id)
        
        if game_obj:
            player = next((p for p in game_obj.players 
                         if p.id == current_player.player_id), None)
            
            # If player is not human, we don't send an action request
            if player and not player.is_human:
                return
    except Exception as e:
        logging.error(f"Error checking if player is human: {str(e)}")
    
    # Continue with regular action request for human players
    valid_actions = game.get_valid_actions(current_player)
    
    # Create action options
    options = []
    for action, params in valid_actions:
        options.append(action.name)
    
    message = {
        "type": "action_request",
        "data": {
            "handId": game.current_hand_id,
            "player_id": current_player.player_id,
            "options": options,
            # Other data...
        }
    }
    
    await self.connection_manager.send_to_player(game_id, current_player.player_id, message)
```

### AI Connector API Endpoints

The enhanced `ai_connector.py` provides these API endpoints:

```python
@router.get("/status")
async def get_ai_status():
    """Get the status of the AI and memory systems."""
    # Returns memory availability, enabled status, and profiles count
    
@router.post("/decision")
async def get_ai_decision(request: AIDecisionRequest):
    """Get a decision from an AI agent."""
    # Takes archetype, game_state, context, player_id
    # Returns an action, amount, and reasoning
    
@router.get("/profiles")
async def get_player_profiles():
    """Get all available player profiles."""
    # Returns all player profiles from memory
    
@router.get("/profiles/{player_id}")
async def get_player_profile(player_id: str):
    """Get a player's profile."""
    # Returns a specific player profile
    
@router.post("/memory/enable")
async def enable_memory():
    """Enable the memory system."""
    
@router.post("/memory/disable")
async def disable_memory():
    """Disable the memory system."""
    
@router.delete("/memory/clear")
async def clear_memory():
    """Clear all memory data."""

@router.post("/process-hand-history")
async def process_hand_history(hand_data: Dict[str, Any]):
    """Process a hand history to update player profiles."""
    
@router.get("/archetypes")
async def get_available_archetypes():
    """Get a list of available AI archetypes."""
    # Returns all supported agent archetypes
```

### WebSocket Handler for Coaching

The coaching WebSocket handler remains as previously implemented:

```python
@router.websocket("/ws/coach/{user_id}")
async def websocket_coach(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time coaching interactions."""
    # Handles coaching queries and strategy questions
    # Provides real-time advice during gameplay
```

### WebSocket Handler for Coaching

```python
@router.websocket("/ws/coach/{user_id}")
async def websocket_coach(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time coaching interactions."""
    await websocket.accept()
    
    try:
        # Authentication check
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return
            
        # Validate token
        if not await auth_service.validate_token(token, user_id):
            await websocket.close(code=1008, reason="Invalid authentication token")
            return
            
        # Process coaching messages
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "coach_query":
                query = data["data"]["query"]
                game_id = data["data"].get("context", {}).get("gameId")
                
                # Get game context if available
                game_context = None
                if game_id:
                    game_state = await db.get_game_state(game_id)
                    game_context = await game_service.create_visible_state(game_state, user_id)
                
                # Get coaching response
                response = await ai_service.get_coaching_advice(query, game_context)
                
                # Send response back to client
                await websocket.send_json({
                    "type": "coach_response",
                    "data": {
                        "text": response,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                
            elif data["type"] == "strategy_question":
                topic = data["data"]["topic"]
                question = data["data"]["question"]
                skill_level = data["data"].get("skill_level", "intermediate")
                
                # Get strategy advice
                advice = await ai_service.get_strategy_advice(
                    topic, 
                    skill_level, 
                    context=question
                )
                
                # Send advice back to client
                await websocket.send_json({
                    "type": "coach_response",
                    "data": {
                        "category": "strategy",
                        "text": advice,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                
            else:
                # Unknown message type
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "message": f"Unknown message type: {data['type']}"
                    }
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnect: user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
```

## Prompt Engineering

### Prompts for Player Agents

#### Base System Prompt Template

```
You are an expert poker player AI with the following playing style:

{archetype_description}

Your goal is to make realistic poker decisions based on your assigned playing style, responding as if you were a real player with this particular strategy and temperament. You will be given information about your cards, the board, pot size, stack sizes, positions, and player actions.

When making decisions, consider:
1. Your assigned playing style and its characteristic tendencies
2. The strength of your hand relative to the board
3. Pot odds and implied odds
4. Position at the table
5. Previous actions of other players
6. Your stack size and the effective stacks
7. The stage of the hand (preflop, flop, turn, river)

Always respond with valid poker actions (fold, check, call, bet, raise) and valid betting amounts when applicable. Your response must be in valid JSON format as specified in the prompt.
```

#### Archetype-Specific Descriptions

**TAG (Tight Aggressive)**:
```
You are a Tight Aggressive (TAG) player who carefully selects premium hands to play but plays them aggressively. You understand poker math and hand selection. You typically play only 15-20% of hands, focusing on strong starting cards, but when you enter a pot, you're usually raising or re-raising rather than calling. You make disciplined folds with marginal hands but extract maximum value with strong hands. You bluff selectively at opportune moments, particularly when your position and the board texture support it.
```

**LAG (Loose Aggressive)**:
```
You are a Loose Aggressive (LAG) player who plays a wide range of starting hands and plays them aggressively. You're involved in 30-40% of hands, frequently raising and re-raising. You put consistent pressure on opponents, forcing them to make difficult decisions. You're comfortable playing in many different board situations and frequently bluff or semi-bluff. You recognize that aggression wins pots even with mediocre hands. You understand that your high-variance style requires skill to balance aggression with appropriate caution.
```

**Tight Passive**:
```
You are a Tight Passive player who plays a narrow range of strong hands but plays them cautiously. You typically enter only 12-15% of pots but rarely raise, preferring to call. You're risk-averse and avoid confrontation, typically only raising with premium hands like AA, KK, or QQ. You rarely bluff and tend to fold to aggression unless you have a very strong hand. You prioritize safety over maximizing value and prefer straightforward play over complex strategies.
```

**Calling Station**:
```
You are a Calling Station who calls too frequently with a wide range of hands but rarely raises. You hate folding once you've invested in a pot and will call with draws, weak pairs, or even just overcards. You'll call all streets with marginal hands due to curiosity and the "need to see" what your opponent has. You rarely bluff, but when you raise, it's almost always with a very strong hand. You frequently chase draws regardless of pot odds and have difficulty folding even when facing obvious strength.
```

**Maniac**:
```
You are a Maniac player characterized by extreme aggression and unpredictability. You play a vast range of hands (50%+) and are constantly raising, re-raising, and bluffing. You're erratic and apply maximum pressure on opponents. You believe aggression is always better than passivity and make seemingly irrational plays, sometimes raising with complete trash or making massive overbets. Your style is high-variance but creates significant discomfort for opponents who struggle to put you on a range.
```

**Beginner (Noob)**:
```
You are a Beginner player who lacks understanding of poker strategy fundamentals. You play too many hands (40%+) based on how they "look" rather than their mathematical value. You call too often but bet/raise too rarely. You make basic strategic errors like calling with weak draws regardless of odds, overvaluing hands like top pair with weak kicker, playing too passively with strong hands, and folding too quickly to aggression. Your decisions are inconsistent and often driven by emotion rather than strategy. You don't consider position, pot odds, or implied odds in your decision-making.
```

### Prompts for Poker Coach

#### System Prompt

```
You are an expert poker coach with decades of experience playing and teaching Texas Hold'em. Your goal is to provide thoughtful, educational coaching to poker players seeking to improve their game.

As a coach, you should:
1. Provide honest and constructive feedback on hand play
2. Explain poker concepts clearly, relating them to specific situations
3. Tailor your advice to the player's skill level when indicated
4. Focus on actionable advice that can improve decision-making
5. Explain the "why" behind recommendations, not just what to do
6. Use proper poker terminology while ensuring explanations remain accessible
7. When analyzing hands, consider GTO principles but also exploitative adjustments
8. Be supportive and encouraging while still being honest about mistakes

Your coaching should cover key poker concepts such as:
- Hand ranges and reading opponents
- Pot odds and equity calculations
- Position and its impact on strategy
- Bet sizing and its implications
- Bankroll management
- Tournament vs. cash game adjustments
- Mental game and emotional control
- Advanced concepts like balance, polarization, and protection

When asked about specific opponents, provide insights on how to exploit their tendencies based on the data provided. Always maintain a professional, educational tone and avoid gambling encouragement. Focus on the strategic elements of poker as a skill game.
```

## Performance Considerations

1. **Parallelized AI Requests**: The system processes multiple AI player decisions concurrently to minimize game delays.

2. **Caching for Common Scenarios**: Frequently encountered scenarios have their responses cached to reduce API calls.

3. **Context Management**: The system carefully manages prompt context size to optimize token usage and response times.

4. **Asynchronous Processing**: All AI operations use asynchronous processing to prevent blocking the game flow.

5. **Response Validation**: All LLM responses are validated for correctness before being applied to the game state.

## Enhanced Memory and Adaptation Systems

The Chip Swinger Championship Poker Trainer implements sophisticated memory and adaptation components that enhance agent decision-making capabilities.

### Memory System

The Enhanced Archetype Memory System allows agents to build and maintain opponent profiles across sessions. Key components include:

#### OpponentProfile
- Detailed representation of opponent behaviors and tendencies
- Statistical tracking (VPIP, PFR, etc.)
- Action tendencies in specific situations
- Hand range assessment
- Qualitative notes and observations
- Archetype detection
- Exploitability analysis

#### MemoryService
- Persistent memory service that manages opponent profiles
- Stores and retrieves player data across sessions
- Tracks statistical trends over time
- Identifies exploitation opportunities
- Provides formatted opponent data for LLM prompts

#### MemoryConnector
- Integration layer connecting memory system to game backend
- Processes hand histories
- Updates profiles from observed actions
- Simplifies integration with minimal dependencies
- Provides backend-friendly data format

### Advanced Adaptation Components

The adaptation system allows agents to adjust their strategies based on game conditions:

#### 1. Game State Tracking

The `GameStateTracker` component monitors and analyzes game dynamics over time:
- Maintains a sliding window of hand histories
- Tracks table aggression, position effectiveness, and stack trends
- Detects significant changes in game dynamics
- Uses exponential weighting to prioritize recent information
- Generates strategic recommendations based on observed patterns

#### 2. Tournament Stage Awareness

The `TournamentStageAnalyzer` component provides tournament-specific strategic adaptations:
- Identifies tournament stages (early, middle, bubble, final table, late)
- Calculates ICM implications and bubble pressure factors
- Determines M-Zone awareness (Harrington's M)
- Provides stage-specific strategic recommendations
- Generates player-specific advice based on stack size

Tournament stages and their strategic implications:

**Early Stage**
- Deep stacks and lower blind pressure
- Focus on chip accumulation without excessive risk
- Standard ranges with some speculative play

**Middle Stage**
- Moderate stack depths and increasing blind pressure
- Increased aggression with position leverage
- Tighter ranges, more steal attempts

**Bubble Stage**
- High ICM pressure near the money
- ICM-aware cautious play with selective aggression
- Tighter calling ranges, maintained aggression with strong hands

**Final Table**
- Significant payout implications
- Dynamic play with payout ladder awareness
- Adjust strategy based on payout structure and stack sizes

**Late Stage**
- In-the-money play with ladder-up considerations
- Target medium stacks afraid to bust
- Looser aggression, tighter calling

M-Zone awareness (Harrington's concept):

**Red Zone (M < 5)**
- Critical push/fold territory
- Look for any push opportunity with decent equity
- Greatly expanded shoving range

**Orange Zone (5 <= M < 10)**
- High pressure zone
- Selective aggression with strong holdings
- Avoid calling all-ins without premium hands

**Yellow Zone (10 <= M < 20)**
- Caution zone
- Prioritize maintaining stack above 10 BBs
- Controlled aggression

**Green Zone (M >= 20)**
- Comfortable stack
- Standard play with ICM awareness
- Full strategic flexibility

#### 3. Exploit-Aware Behaviors

The advanced agents can identify and capitalize on opponent weaknesses:
- Detects patterns like excessive passivity or aggression
- Identifies specific exploitable tendencies
- Recommends counter-strategies based on observed behaviors
- Adjusts strategy intensity based on confidence levels
- Balances exploitation with balanced play

#### 4. Dynamic Strategy Adjustment

The `AdaptableAgent` can change its strategy based on game conditions:
- Shifts from tight to loose or passive to aggressive as needed
- Adapts to changing table dynamics
- Responds to tournament stage considerations
- Utilizes a weighted approach to strategy selection
- Maintains archetype identity while adapting

#### Integration

The `AdaptationManager` class provides a unified interface for using all adaptation components together. It can be integrated with any poker agent using the `enhance_agent_with_adaptation` function, which adds adaptation capabilities to the agent's decision-making process:

```python
from ai.agents.adaptation.integration import enhance_agent_with_adaptation

# Create a poker agent
agent = AdaptableAgent(llm_service)

# Enhance the agent with advanced adaptation
enhance_agent_with_adaptation(agent)

# The agent will now have access to all adaptation components
# and will include adaptation information in its decisions
```

## Future Enhancements

1. **Fine-tuned Models**: Custom fine-tuned models for each player archetype to improve decision quality and reduce cost.

2. **Hybrid Approaches**: Combining rule-based systems with LLMs for faster and more consistent behavior in routine scenarios.

3. **Multi-agent Reasoning**: Enhancing agent reasoning about other agents' perceptions and strategies.

4. **Personalized Coaching**: Tailoring coaching to individual player weaknesses based on historical play data.

5. **Adaptive Difficulty**: Dynamically adjusting AI player skill levels based on the human player's performance and learning progress.