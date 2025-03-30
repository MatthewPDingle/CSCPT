"""
Opponent profile models for tracking player behavior and statistics.
"""
from typing import Dict, List, Optional, Set, Union, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class StatisticValue(BaseModel):
    """
    A statistical value with optional confidence level and sample size.
    """
    value: Union[float, str]  # The actual statistic (e.g., 25.5 for VPIP %)
    confidence: float = 0.0  # 0.0-1.0, how confident we are in this stat
    sample_size: int = 0  # Number of observations this is based on
    last_updated: datetime = Field(default_factory=datetime.now)


class ActionTendency(BaseModel):
    """
    Records a player's tendencies in specific situations.
    """
    situation: str  # E.g., "facing_3bet", "flop_cbet_opportunity"
    action_taken: str  # E.g., "fold", "call", "raise"
    frequency: float  # 0.0-1.0
    sample_size: int
    last_observed: datetime = Field(default_factory=datetime.now)


class OpponentNote(BaseModel):
    """
    A qualitative observation about an opponent.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    note: str
    category: str  # E.g., "bluffing", "value_betting", "tells"
    hand_id: Optional[str] = None  # Reference to hand where this was observed
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence: float = 0.5  # 0.0-1.0


class HandRange(BaseModel):
    """
    Represents an opponent's observed hand range in a specific situation.
    """
    situation: str  # E.g., "utg_open", "btn_3bet", "river_valuebet" 
    hands: List[str]  # List of hands in the range, e.g. ["AKs", "QQ+"]
    frequency: float = 1.0  # How often they use this range (for mixed strategies)
    sample_size: int = 1
    last_updated: datetime = Field(default_factory=datetime.now)


class OpponentProfile(BaseModel):
    """
    Complete profile of an opponent, tracking their tendencies and statistics.
    """
    player_id: str
    name: str
    archetype: Optional[str] = None  # Detected archetype if identified
    
    # Core statistics (VPIP, PFR, etc.)
    stats: Dict[str, StatisticValue] = Field(default_factory=dict)
    
    # Positional tendencies 
    positional_stats: Dict[str, Dict[str, StatisticValue]] = Field(default_factory=dict)
    
    # Action tendencies in specific situations
    action_tendencies: List[ActionTendency] = Field(default_factory=list)
    
    # Hand ranges in different situations
    hand_ranges: List[HandRange] = Field(default_factory=list)
    
    # Qualitative notes and observations
    notes: List[OpponentNote] = Field(default_factory=list)
    
    # Timestamps
    first_observed: datetime = Field(default_factory=datetime.now)
    last_observed: datetime = Field(default_factory=datetime.now)
    
    # Exploitability assessment
    exploitable_tendencies: List[str] = Field(default_factory=list)
    suggested_exploits: List[str] = Field(default_factory=list)
    
    # Meta information
    confidence_score: float = 0.1  # Overall confidence in profile (0.0-1.0)
    hands_observed: int = 0
    
    def add_note(self, note: str, category: str = "general", hand_id: Optional[str] = None, 
               confidence: float = 0.5) -> None:
        """
        Add a new note to this opponent profile.
        
        Args:
            note: The observation text
            category: Category for organizing notes
            hand_id: Optional reference to specific hand
            confidence: How confident we are in this observation (0.0-1.0)
        """
        new_note = OpponentNote(
            note=note,
            category=category,
            hand_id=hand_id,
            confidence=confidence
        )
        self.notes.append(new_note)
    
    def update_statistic(self, name: str, value: Union[float, str], 
                       sample_size: int = 1, confidence: Optional[float] = None) -> None:
        """
        Update a statistical value with new information.
        
        Args:
            name: Name of the statistic (e.g., "VPIP", "PFR")
            value: New value for the statistic
            sample_size: How many observations this is based on
            confidence: Optional new confidence level (0.0-1.0)
        """
        if name in self.stats:
            existing = self.stats[name]
            # Update based on sample size weighting
            total_samples = existing.sample_size + sample_size
            
            # For numerical values, compute weighted average
            if isinstance(existing.value, (int, float)) and isinstance(value, (int, float)):
                new_value = ((existing.value * existing.sample_size) + 
                           (value * sample_size)) / total_samples
            else:
                # For string values, just use the new one if it has higher confidence
                new_value = value if confidence and confidence > existing.confidence else existing.value
            
            # Update confidence level
            new_confidence = confidence if confidence is not None else existing.confidence
            
            self.stats[name] = StatisticValue(
                value=new_value,
                confidence=new_confidence,
                sample_size=total_samples,
                last_updated=datetime.now()
            )
        else:
            # Create new statistic
            self.stats[name] = StatisticValue(
                value=value,
                confidence=confidence or 0.3,  # Default starting confidence
                sample_size=sample_size,
                last_updated=datetime.now()
            )
    
    def get_formatted_string(self) -> str:
        """
        Get a compact string representation of this profile for LLM prompt inclusion.
        
        Returns:
            Formatted string of the profile data
        """
        # Format core stats
        stats_str = ' '.join([f"[{name}:{stat.value}]" for name, stat in self.stats.items()])
        
        # Format exploitable tendencies
        exploits_str = f"[Exploits:{','.join(self.exploitable_tendencies)}]" if self.exploitable_tendencies else ""
        
        # Format most recent notes (max 3)
        recent_notes = sorted(self.notes, key=lambda x: x.timestamp, reverse=True)[:3]
        notes_str = f"[Notes:{'; '.join([n.note for n in recent_notes])}]" if recent_notes else ""
        
        # Combine components
        return f"Player{self.player_id}: {stats_str} {exploits_str} {notes_str}".strip()
    
    def assess_archetype(self) -> str:
        """
        Determine the most likely archetype based on observed statistics.
        
        Returns:
            Most likely archetype name
        """
        # Simple archetype detection based on common statistics
        if "VPIP" not in self.stats or "PFR" not in self.stats:
            return "Unknown"
            
        vpip = float(self.stats["VPIP"].value) if isinstance(self.stats["VPIP"].value, (int, float)) else 0.0
        pfr = float(self.stats["PFR"].value) if isinstance(self.stats["PFR"].value, (int, float)) else 0.0
        
        if self.hands_observed < 20:
            return "Insufficient Data"
        
        # Simple archetype detection
        if vpip < 20:
            if pfr > 15:
                return "TAG"
            else:
                return "TightPassive"
        elif vpip > 40:
            if pfr > 30:
                return "LAG" if pfr < 45 else "Maniac"
            else:
                return "CallingStation" if vpip > 50 else "LoosePassive"
        else:  # Medium VPIP (20-40)
            if pfr > 25:
                return "LAG"
            elif pfr > 15:
                return "TAG"
            else:
                return "LoosePassive"
                
    def identify_exploits(self) -> List[str]:
        """
        Identify potential exploitable tendencies based on the profile.
        
        Returns:
            List of exploitable tendencies
        """
        exploits = []
        
        # Only try to identify exploits with sufficient data
        if self.hands_observed < 10:
            return ["Insufficient data for exploit analysis"]
            
        # Check for tendencies that can be exploited
        if "VPIP" in self.stats:
            vpip = float(self.stats["VPIP"].value) if isinstance(self.stats["VPIP"].value, (int, float)) else 0.0
            if vpip > 50:
                exploits.append("Over-plays weak hands")
            if vpip < 12:
                exploits.append("Too tight pre-flop")
                
        if "FoldToCbet" in self.stats:
            fold_to_cbet = float(self.stats["FoldToCbet"].value) if isinstance(self.stats["FoldToCbet"].value, (int, float)) else 0.0
            if fold_to_cbet > 70:
                exploits.append("Folds too often to continuation bets")
            if fold_to_cbet < 30:
                exploits.append("Calls continuation bets too loosely")
                
        if "CheckRaiseFreq" in self.stats:
            check_raise = float(self.stats["CheckRaiseFreq"].value) if isinstance(self.stats["CheckRaiseFreq"].value, (int, float)) else 0.0
            if check_raise > 20:
                exploits.append("Check-raises frequently")
            if check_raise < 5 and self.hands_observed > 30:
                exploits.append("Rarely check-raises")
                
        # Look for patterns in notes
        bluff_notes = [n for n in self.notes if "bluff" in n.note.lower()]
        if len(bluff_notes) >= 3:
            exploits.append("Bluffs frequently")
            
        passive_notes = [n for n in self.notes if any(word in n.note.lower() for word in ["passive", "weak", "call", "flat"])]
        if len(passive_notes) >= 3:
            exploits.append("Generally passive")
            
        # Update the exploitable tendencies
        self.exploitable_tendencies = exploits
        return exploits