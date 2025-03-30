"""
Game state tracking and analysis for poker agents.

This component tracks game dynamics over time and detects changes
that may warrant strategic adjustments.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)

class GameStateTracker:
    """
    Tracks and analyzes game dynamics over time.
    
    This class maintains a history of game states and outcomes to identify
    patterns and changes in game dynamics that may warrant strategic adjustments.
    """
    
    def __init__(self, window_size: int = 20):
        """
        Initialize the game state tracker.
        
        Args:
            window_size: Maximum number of hands to track in history
        """
        self.window_size = window_size
        
        # Tracking data structures
        self.aggression_history = deque(maxlen=window_size)  # Track table aggression
        self.position_effectiveness = {}  # Position → win rate mapping
        self.strategy_results = {}  # Strategy → result mapping
        self.player_stats = {}  # Player → stats mapping
        self.stack_trend = {}  # Player → stack history mapping
        
        # Calculated metrics
        self.current_dynamics = {
            "table_aggression": 0.0,  # 0.0-1.0 scale
            "table_tightness": 0.0,   # 0.0-1.0 scale (higher = tighter)
            "positional_advantage": {},  # Position → advantage score
            "stack_pressure": 0.0      # 0.0-1.0 scale (higher = more pressure)
        }
        
        # Record of detected changes
        self.detected_changes = []
        
        # Hand counter
        self.hands_processed = 0
    
    def update(self, game_state: Dict[str, Any], outcome: Optional[Dict[str, Any]] = None) -> None:
        """
        Update tracking based on a new hand.
        
        Args:
            game_state: Current game state data
            outcome: Optional outcome of the hand
        """
        self.hands_processed += 1
        
        # Extract key information
        action_history = game_state.get("action_history", [])
        players = game_state.get("players", [])
        position = game_state.get("position", "")
        
        # Calculate aggression ratio for this hand
        aggressive_actions = sum(1 for a in action_history 
                             if a.get("action", "").lower() in ["raise", "bet"])
        passive_actions = sum(1 for a in action_history 
                           if a.get("action", "").lower() in ["call", "check"])
        
        aggression_ratio = 0.5  # Default balanced
        if aggressive_actions + passive_actions > 0:
            aggression_ratio = aggressive_actions / (aggressive_actions + passive_actions)
        
        self.aggression_history.append(aggression_ratio)
        
        # Update player stats
        for player in players:
            player_id = player.get("player_id")
            if not player_id:
                continue
                
            if player_id not in self.player_stats:
                self.player_stats[player_id] = {
                    "aggression": [],
                    "vpip": [],
                    "hands": 0
                }
            
            self.player_stats[player_id]["hands"] += 1
            
            # Track stack sizes
            if "stack" in player:
                if player_id not in self.stack_trend:
                    self.stack_trend[player_id] = deque(maxlen=self.window_size)
                self.stack_trend[player_id].append(player["stack"])
        
        # Update position effectiveness if outcome provided
        if outcome and position:
            if position not in self.position_effectiveness:
                self.position_effectiveness[position] = {
                    "wins": 0,
                    "hands": 0
                }
            
            self.position_effectiveness[position]["hands"] += 1
            if outcome.get("result", "") == "win":
                self.position_effectiveness[position]["wins"] += 1
        
        # Update strategy results if provided
        if outcome and "strategy" in outcome:
            strategy = outcome["strategy"]
            if strategy not in self.strategy_results:
                self.strategy_results[strategy] = {
                    "success": 0,
                    "attempts": 0,
                    "profit": 0
                }
            
            self.strategy_results[strategy]["attempts"] += 1
            if outcome.get("success", False):
                self.strategy_results[strategy]["success"] += 1
            
            self.strategy_results[strategy]["profit"] += outcome.get("profit", 0)
        
        # Update current dynamics
        self._update_current_dynamics()
        
        # Detect significant changes
        self._detect_changes()
    
    def _update_current_dynamics(self) -> None:
        """Update the current game dynamics metrics."""
        # Calculate table aggression
        if self.aggression_history:
            # Focus more on recent hands with exponential weighting
            weights = [0.8 ** i for i in range(len(self.aggression_history))]
            total_weight = sum(weights)
            
            if total_weight > 0:
                weighted_aggression = sum(a * w for a, w in zip(self.aggression_history, weights)) / total_weight
                self.current_dynamics["table_aggression"] = weighted_aggression
        
        # Calculate positional advantage
        for position, stats in self.position_effectiveness.items():
            if stats["hands"] > 0:
                self.current_dynamics["positional_advantage"][position] = stats["wins"] / stats["hands"]
        
        # Calculate stack pressure (based on stack trend volatility)
        total_volatility = 0
        stack_count = 0
        
        for player_id, stack_history in self.stack_trend.items():
            if len(stack_history) >= 2:
                diffs = [abs(stack_history[i] - stack_history[i-1]) for i in range(1, len(stack_history))]
                avg_diff = sum(diffs) / len(diffs)
                
                # Normalize by average stack size
                avg_stack = sum(stack_history) / len(stack_history)
                if avg_stack > 0:
                    volatility = avg_diff / avg_stack
                    total_volatility += volatility
                    stack_count += 1
        
        if stack_count > 0:
            self.current_dynamics["stack_pressure"] = min(1.0, total_volatility / stack_count)
    
    def _detect_changes(self) -> None:
        """Detect significant changes in game dynamics."""
        # Need at least 5 hands to detect changes
        if self.hands_processed < 5:
            return
            
        # Check for significant aggression shift
        if len(self.aggression_history) >= 5:
            recent = list(self.aggression_history)[-5:]
            earlier = list(self.aggression_history)[:-5] or [0.5]  # Default if not enough history
            
            recent_avg = sum(recent) / len(recent)
            earlier_avg = sum(earlier) / len(earlier)
            
            if abs(recent_avg - earlier_avg) > 0.2:  # 20% change threshold
                self.detected_changes.append({
                    "type": "aggression_shift",
                    "from": earlier_avg,
                    "to": recent_avg,
                    "hand": self.hands_processed,
                    "timestamp": datetime.now()
                })
                logger.info(f"Detected aggression shift: {earlier_avg:.2f} → {recent_avg:.2f}")
    
    def get_dynamics_assessment(self) -> Dict[str, Any]:
        """
        Get an assessment of current game dynamics.
        
        Returns:
            Dictionary with game dynamics assessment
        """
        # Aggression level characterization
        aggression_level = "balanced"
        if self.current_dynamics["table_aggression"] > 0.7:
            aggression_level = "very aggressive"
        elif self.current_dynamics["table_aggression"] > 0.6:
            aggression_level = "aggressive"
        elif self.current_dynamics["table_aggression"] < 0.3:
            aggression_level = "very passive"
        elif self.current_dynamics["table_aggression"] < 0.4:
            aggression_level = "passive"
        
        # Stack pressure characterization
        pressure_level = "moderate"
        if self.current_dynamics["stack_pressure"] > 0.7:
            pressure_level = "high"
        elif self.current_dynamics["stack_pressure"] < 0.3:
            pressure_level = "low"
        
        # Recent changes
        recent_changes = [c for c in self.detected_changes 
                         if self.hands_processed - c["hand"] <= 10]
        
        # Strategy effectiveness
        effective_strategies = []
        for strategy, results in self.strategy_results.items():
            if results["attempts"] >= 3:
                win_rate = results["success"] / results["attempts"]
                if win_rate > 0.5:
                    effective_strategies.append({
                        "name": strategy,
                        "win_rate": win_rate,
                        "profit": results["profit"]
                    })
        
        return {
            "aggression": {
                "value": self.current_dynamics["table_aggression"],
                "description": aggression_level
            },
            "stack_pressure": {
                "value": self.current_dynamics["stack_pressure"],
                "description": pressure_level
            },
            "positional_advantage": {
                pos: {"value": adv} for pos, adv in 
                self.current_dynamics["positional_advantage"].items()
            },
            "changes": [
                {
                    "type": c["type"],
                    "description": f"{c['type'].replace('_', ' ').title()} from {c['from']:.2f} to {c['to']:.2f}",
                    "hands_ago": self.hands_processed - c["hand"]
                }
                for c in recent_changes
            ],
            "effective_strategies": effective_strategies,
            "data_confidence": min(1.0, self.hands_processed / 20)  # Up to 100% with 20+ hands
        }
    
    def get_recommended_adjustments(self) -> Dict[str, Any]:
        """
        Get recommended strategy adjustments based on game dynamics.
        
        Returns:
            Dictionary with recommended adjustments
        """
        assessment = self.get_dynamics_assessment()
        adjustments = {}
        
        # Adjust to aggression level
        if assessment["aggression"]["description"] == "very aggressive":
            adjustments["aggression_response"] = {
                "type": "tighten",
                "description": "Tighten range and capitalize on strong holdings",
                "intensity": 0.8
            }
        elif assessment["aggression"]["description"] == "aggressive":
            adjustments["aggression_response"] = {
                "type": "selective_aggression",
                "description": "Be selective with aggression, look for trapping opportunities",
                "intensity": 0.6
            }
        elif assessment["aggression"]["description"] == "very passive":
            adjustments["aggression_response"] = {
                "type": "increase_aggression",
                "description": "Increase aggression and steal opportunities",
                "intensity": 0.8
            }
        elif assessment["aggression"]["description"] == "passive":
            adjustments["aggression_response"] = {
                "type": "moderate_aggression",
                "description": "Moderately increase aggression, particularly in position",
                "intensity": 0.6
            }
        
        # Adjust to positional advantage
        if assessment["positional_advantage"]:
            strong_positions = [pos for pos, adv in assessment["positional_advantage"].items() 
                             if adv.get("value", 0) > 0.6]
            if strong_positions:
                adjustments["position_focus"] = {
                    "type": "leverage_positions",
                    "positions": strong_positions,
                    "description": f"Leverage advantage in {', '.join(strong_positions)}",
                    "intensity": 0.7
                }
        
        # Consider recent changes
        if assessment["changes"]:
            # Just take the most recent change for simplicity
            latest_change = assessment["changes"][0]
            if "aggression" in latest_change["type"]:
                adjustments["change_response"] = {
                    "type": "adapt_to_aggression_change",
                    "description": f"Adapt to recent {latest_change['description']}",
                    "intensity": 0.5
                }
        
        # Consider effective strategies
        if assessment["effective_strategies"]:
            # Take the most profitable strategy
            best_strategy = max(assessment["effective_strategies"], 
                              key=lambda s: s["profit"])
            adjustments["continue_strategy"] = {
                "type": "reinforce_strategy",
                "strategy": best_strategy["name"],
                "description": f"Continue successful {best_strategy['name']} strategy",
                "intensity": min(0.9, best_strategy["win_rate"])
            }
        
        # Apply confidence factor
        for key in adjustments:
            adjustments[key]["confidence"] = assessment["data_confidence"]
        
        return adjustments