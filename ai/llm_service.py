"""
LLM service implementation for testing.

This is a mock implementation that returns predetermined responses
for testing purposes.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for interacting with LLM providers.
    This is a mock implementation for testing.
    """
    
    def __init__(self):
        """Initialize the LLM service."""
        logger.info("Initializing mock LLM service")
    
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        provider: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Complete a prompt with an LLM.
        
        Args:
            system_prompt: System instructions for the LLM
            user_prompt: User prompt
            temperature: Temperature for sampling (0.0 to 1.0)
            provider: Provider to use (None for default)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated completion
        """
        # Mock implementation that returns a fixed response
        return "This is a mock response from the LLM service."
    
    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Dict[str, Any],
        temperature: float = 0.7,
        provider: Optional[str] = None,
        extended_thinking: bool = False
    ) -> Dict[str, Any]:
        """
        Complete a prompt and return structured JSON.
        
        Args:
            system_prompt: System instructions for the LLM
            user_prompt: User prompt
            json_schema: JSON schema for validation
            temperature: Temperature for sampling
            provider: Provider to use
            extended_thinking: Whether to use extended thinking
            
        Returns:
            JSON response
        """
        # Extract archetype from the system prompt to customize the response
        archetype = "TAG"  # Default
        if "TAG player" in system_prompt:
            archetype = "TAG"
        elif "LAG player" in system_prompt:
            archetype = "LAG"
        elif "TightPassive player" in system_prompt:
            archetype = "TightPassive"
        elif "CallingStation player" in system_prompt:
            archetype = "CallingStation"
        elif "Adaptable player" in system_prompt:
            archetype = "Adaptable"
        
        # Check if hand and community cards are mentioned in user prompt
        hand = ["Ah", "Kh"]
        community_cards = []
        position = "BTN"
        
        if "Your Hand: " in user_prompt:
            hand_text = user_prompt.split("Your Hand: ")[1].split("\n")[0].strip()
            if hand_text and hand_text != "None":
                hand = hand_text.split()
        
        if "Community Cards: " in user_prompt:
            cards_text = user_prompt.split("Community Cards: ")[1].split("\n")[0].strip()
            if cards_text and cards_text != "None":
                community_cards = cards_text.split()
        
        # Generate appropriate mock response based on archetype and cards
        if archetype == "TAG":
            if "A" in hand[0] or "A" in hand[1] or "K" in hand[0] or "K" in hand[1]:
                # Strong hand for TAG
                action = "raise"
                amount = 100
                thinking = "I have a strong hand and I'm in position. This is a clear value betting spot."
            else:
                # Weak hand for TAG
                action = "fold"
                amount = None
                thinking = "My hand is weak and I should fold here as a TAG player."
        elif archetype == "LAG":
            # LAG is more aggressive
            action = "raise"
            amount = 150
            thinking = "As a LAG player, I can put pressure with a wide range here."
        elif archetype == "CallingStation":
            action = "call"
            amount = None
            thinking = "I'll call to see another card and hope to improve my hand."
        elif archetype == "Adaptable":
            # Check if adaptation strategy is mentioned
            if "adaptation_strategy" in user_prompt:
                if "counter-aggressive" in user_prompt:
                    action = "call"
                    amount = None
                    thinking = "Using counter-aggressive strategy, I'll call here to trap aggressive players."
                elif "exploit-passive" in user_prompt:
                    action = "raise"
                    amount = 120
                    thinking = "Using exploit-passive strategy, I'll raise to take advantage of passive opponents."
                else:
                    action = "bet"
                    amount = 80
                    thinking = "Using balanced strategy, I'll make a standard bet."
            else:
                action = "bet"
                amount = 80
                thinking = "I'll make a standard bet based on my hand strength and position."
        else:
            # Default response
            action = "check"
            amount = None
            thinking = "I'm not sure what to do here, so I'll check."
        
        # Build complete response
        response = {
            "thinking": thinking,
            "action": action,
            "amount": amount,
            "reasoning": {
                "hand_assessment": f"{'Strong' if action in ['raise', 'bet'] else 'Medium' if action == 'call' else 'Weak'} hand",
                "positional_considerations": f"I'm in {position} which is {'good' if position in ['BTN', 'CO'] else 'okay' if position in ['MP', 'HJ'] else 'challenging'}",
                "opponent_reads": "Limited information about opponents",
                "archetype_alignment": f"This action aligns with my {archetype} playing style"
            }
        }
        
        # If it's an adaptive agent, add adaptation strategy
        if archetype == "Adaptable" and "adaptation_strategy" in user_prompt:
            if "counter-aggressive" in user_prompt:
                response["reasoning"]["adaptation_strategy"] = "Using counter-aggressive strategy based on table dynamics"
            elif "exploit-passive" in user_prompt:
                response["reasoning"]["adaptation_strategy"] = "Using exploit-passive strategy to take advantage of passive tendencies"
            else:
                response["reasoning"]["adaptation_strategy"] = "Using balanced strategy for mixed table dynamics"
        
        # Add calculations field if schema requires it
        if "calculations" in json_schema.get("properties", {}):
            response["calculations"] = {
                "pot_odds": "3:1",
                "estimated_equity": "65%"
            }
        
        return response