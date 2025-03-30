"""
Example demonstrating the tournament stage awareness functionality.

This script shows how the TournamentStageAnalyzer can be used to identify
different tournament stages and provide strategic recommendations.
"""

import os
import sys
from pathlib import Path
import asyncio
from typing import Dict, Any

# Add project root to path
project_root = str(Path(__file__).parents[4])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai.agents.adaptation.tournament_analyzer import TournamentStageAnalyzer, TournamentStage, MZone

def print_tournament_stage(stage_name: str, description: str):
    """Print a tournament stage header."""
    print(f"\n{'='*80}")
    print(f"TOURNAMENT STAGE: {stage_name}")
    print(f"{description}")
    print(f"{'='*80}\n")

def print_recommendations(recommendations: Dict[str, Any]):
    """Print tournament recommendations."""
    print(f"General Strategy: {recommendations.get('general_strategy', 'Unknown')}")
    print(f"Aggression Level: {recommendations.get('aggression_level', 'Unknown')}")
    print(f"Range Adjustment: {recommendations.get('range_adjustment', 'Unknown')}")
    print(f"Stack Management: {recommendations.get('stack_management', 'Unknown')}")
    print("\nKey Considerations:")
    for consideration in recommendations.get("key_considerations", []):
        print(f"- {consideration}")

def demonstrate_early_stage():
    """Demonstrate early tournament stage."""
    analyzer = TournamentStageAnalyzer()
    
    tournament_state = {
        "total_players": 100,
        "players_remaining": 95,
        "level": 2,
        "max_levels": 20,
        "in_the_money": False,
        "final_table": False,
        "paid_positions": 15,
        "blinds": [25, 50],
        "player_stacks": {
            "player1": 10000,
            "player2": 9500,
            "player3": 10500
        }
    }
    
    analyzer.update(tournament_state)
    assessment = analyzer.get_assessment()
    
    print_tournament_stage(
        assessment["stage"],
        assessment["stage_description"]
    )
    
    print_recommendations(assessment["recommendations"])
    
    # Show player-specific advice
    print("\nPlayer-Specific Advice:")
    for player_id in ["player1", "player2", "player3"]:
        player_rec = analyzer.get_recommendations_for_player(player_id)
        print(f"\n{player_id} (M-Zone: {player_rec.get('m_zone', 'Unknown')}):")
        print(f"- {player_rec.get('m_strategy', 'Unknown')}")

def demonstrate_bubble_stage():
    """Demonstrate bubble tournament stage."""
    analyzer = TournamentStageAnalyzer()
    
    tournament_state = {
        "total_players": 100,
        "players_remaining": 16,  # Just outside the money
        "level": 12,
        "max_levels": 20,
        "in_the_money": False,
        "final_table": False,
        "paid_positions": 15,
        "blinds": [500, 1000],
        "player_stacks": {
            "big_stack": 35000,    # Comfortable stack
            "medium_stack": 15000,  # Moderate stack
            "short_stack": 4000    # Danger zone
        }
    }
    
    analyzer.update(tournament_state)
    assessment = analyzer.get_assessment()
    
    print_tournament_stage(
        assessment["stage"],
        assessment["stage_description"]
    )
    
    print_recommendations(assessment["recommendations"])
    
    # Show ICM implications
    if "icm_implications" in assessment:
        print("\nICM Pressure Level:", assessment["icm_implications"]["pressure_level"])
    
    # Show player-specific advice
    print("\nPlayer-Specific Advice:")
    for player_id in ["big_stack", "medium_stack", "short_stack"]:
        player_rec = analyzer.get_recommendations_for_player(player_id)
        print(f"\n{player_id} (M-Zone: {player_rec.get('m_zone', 'Unknown')}):")
        print(f"- {player_rec.get('m_strategy', 'Unknown')}")
        if "icm_pressure" in player_rec:
            print(f"- ICM Pressure: {player_rec['icm_pressure']['level']}")
            print(f"- Implication: {player_rec['icm_pressure']['implications']}")

def demonstrate_final_table():
    """Demonstrate final table stage."""
    analyzer = TournamentStageAnalyzer()
    
    tournament_state = {
        "total_players": 100,
        "players_remaining": 9,
        "level": 18,
        "max_levels": 20,
        "in_the_money": True,
        "final_table": True,
        "paid_positions": 15,
        "blinds": [1000, 2000],
        "player_stacks": {
            "chip_leader": 60000,
            "middle_pack": 25000,
            "short_stack": 8000
        }
    }
    
    analyzer.update(tournament_state)
    assessment = analyzer.get_assessment()
    
    print_tournament_stage(
        assessment["stage"],
        assessment["stage_description"]
    )
    
    print_recommendations(assessment["recommendations"])
    
    # Show player-specific advice
    print("\nPlayer-Specific Advice:")
    for player_id in ["chip_leader", "middle_pack", "short_stack"]:
        player_rec = analyzer.get_recommendations_for_player(player_id)
        print(f"\n{player_id} (M-Zone: {player_rec.get('m_zone', 'Unknown')}):")
        print(f"- {player_rec.get('m_strategy', 'Unknown')}")
        if "stack_strategy" in player_rec:
            print(f"- {player_rec['stack_strategy']['description']}")
            print(f"- Strategy: {player_rec['stack_strategy']['strategy']}")

def main():
    """Run the tournament stage awareness examples."""
    print("TOURNAMENT STAGE AWARENESS EXAMPLE")
    print("==================================")
    print("This example demonstrates how the TournamentStageAnalyzer")
    print("identifies different tournament stages and provides strategic")
    print("recommendations based on tournament context.")
    
    demonstrate_early_stage()
    demonstrate_bubble_stage()
    demonstrate_final_table()

if __name__ == "__main__":
    main()