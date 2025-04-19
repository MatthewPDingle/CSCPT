"""
Data models for game state representation.
"""
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

from app.core.cards import Suit, Rank
from app.core.poker_game import BettingRound, PlayerStatus, PlayerAction
from datetime import datetime
from typing import Optional


class CardModel(BaseModel):
    """API model representing a card."""
    rank: str
    suit: str
    
    class Config:
        schema_extra = {
            "example": {
                "rank": "A",
                "suit": "H"
            }
        }


class PlayerModel(BaseModel):
    """API model representing a player."""
    player_id: str
    name: str
    chips: int
    position: int
    status: str
    current_bet: int
    total_bet: int
    cards: Optional[List[CardModel]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "player_id": "p1",
                "name": "Player 1",
                "chips": 1000,
                "position": 0,
                "status": "ACTIVE",
                "current_bet": 0,
                "total_bet": 0,
                "cards": [
                    {"rank": "A", "suit": "H"},
                    {"rank": "K", "suit": "H"}
                ]
            }
        }


class ActionHistoryModel(BaseModel):
    """API model representing a single player action in the hand history."""
    player_id: str
    action: str
    amount: Optional[int] = None
    round: str
    # ISO8601 timestamp string of when the action occurred
    timestamp: str


class PotModel(BaseModel):
    """API model representing a pot in the game."""
    name: str
    amount: int
    eligible_player_ids: List[str]
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Main Pot",
                "amount": 200,
                "eligible_player_ids": ["p1", "p2", "p3"]
            }
        }


class GameStateModel(BaseModel):
    """API model representing the current game state."""
    game_id: str
    players: List[PlayerModel]
    community_cards: List[CardModel]
    pots: List[PotModel]
    total_pot: int
    current_round: str
    button_position: int
    current_player_idx: int
    current_bet: int
    small_blind: int
    big_blind: int
    ante: Optional[int] = None
    # Optional fields for cash games
    max_buy_in: Optional[int] = None
    min_buy_in: Optional[int] = None
    # History of all actions taken so far in the current hand
    action_history: List['ActionHistoryModel'] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "game_id": "game1",
                "players": [
                    {
                        "player_id": "p1",
                        "name": "Player 1",
                        "chips": 990,
                        "position": 0,
                        "status": "ACTIVE",
                        "current_bet": 10,
                        "total_bet": 10,
                        "cards": [
                            {"rank": "A", "suit": "H"},
                            {"rank": "K", "suit": "H"}
                        ]
                    },
                    {
                        "player_id": "p2",
                        "name": "Player 2",
                        "chips": 980,
                        "position": 1,
                        "status": "ACTIVE",
                        "current_bet": 20,
                        "total_bet": 20,
                        "cards": None
                    }
                ],
                "community_cards": [
                    {"rank": "10", "suit": "H"},
                    {"rank": "J", "suit": "H"},
                    {"rank": "Q", "suit": "H"}
                ],
                "pots": [
                    {
                        "name": "Main Pot",
                        "amount": 30,
                        "eligible_player_ids": ["p1", "p2"]
                    }
                ],
                "total_pot": 30,
                "current_round": "FLOP",
                "button_position": 0,
                "current_player_idx": 0,
                "current_bet": 20,
                "small_blind": 10,
                "big_blind": 20,
                "ante": 0
            }
        }


class ActionRequest(BaseModel):
    """API model for sending a player action."""
    player_id: str
    action: str
    amount: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "player_id": "p1",
                "action": "RAISE",
                "amount": 40
            }
        }


class ActionResponse(BaseModel):
    """API model for the response to a player action."""
    success: bool
    message: str
    game_state: Optional[GameStateModel] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Action processed successfully",
                "game_state": {
                    "game_id": "game1",
                    "players": [],
                    "community_cards": [],
                    "pot": 30,
                    "current_round": "FLOP",
                    "button_position": 0,
                    "current_player_idx": 1,
                    "current_bet": 40,
                    "small_blind": 10,
                    "big_blind": 20
                }
            }
        }