"""
Utility functions for the poker application.
"""

from typing import List

from app.core.poker_game import PokerGame
from app.models.game_models import CardModel, PlayerModel, GameStateModel, PotModel


def game_to_model(game_id: str, game: PokerGame) -> GameStateModel:
    """
    Convert a PokerGame to a GameStateModel for API responses.

    Args:
        game_id: The ID of the game
        game: The PokerGame instance

    Returns:
        A GameStateModel representing the game state
    """
    # Convert community cards
    community_cards = [
        CardModel(rank=str(card.rank), suit=card.suit.name[0])
        for card in game.community_cards
    ]

    # Convert players
    players = []
    for player in game.players:
        # Only include player's cards if they have been dealt
        cards = None
        if player.hand and len(player.hand.cards) > 0:
            cards = [
                CardModel(rank=str(card.rank), suit=card.suit.name[0])
                for card in player.hand.cards
            ]

        players.append(
            PlayerModel(
                player_id=player.player_id,
                name=player.name,
                chips=player.chips,
                position=player.position,
                status=player.status.name,
                current_bet=player.current_bet,
                total_bet=player.total_bet,
                cards=cards,
            )
        )

    # Convert pots
    pots = []
    for pot in game.pots:
        pots.append(
            PotModel(
                name=pot.name or "Pot",
                amount=pot.amount,
                eligible_player_ids=list(pot.eligible_players),
            )
        )

    # If no pots, create a default main pot
    if not pots:
        pots = [PotModel(name="Main Pot", amount=0, eligible_player_ids=[])]

    # Calculate total pot amount
    total_pot = sum(pot.amount for pot in game.pots)

    # Create the game state model with base fields
    game_state = GameStateModel(
        game_id=game_id,
        players=players,
        community_cards=community_cards,
        pots=pots,
        total_pot=total_pot,
        current_round=game.current_round.name,
        button_position=game.button_position,
        current_player_idx=game.current_player_idx,
        current_bet=game.current_bet,
        small_blind=game.small_blind,
        big_blind=game.big_blind,
    )
    
    # Add cash game specific fields if available
    from app.services.game_service import GameService
    service = GameService.get_instance()
    domain_game = service.get_game(game_id)
    
    if domain_game and domain_game.type.name == 'CASH':
        # Cash game - add min/max buy-in
        game_state.min_buy_in = getattr(domain_game, 'min_buy_in', None)
        game_state.max_buy_in = getattr(domain_game, 'max_buy_in', None)
    
    return game_state


def format_winners(game: PokerGame) -> str:
    """Format the winners for the response message."""
    if not game.hand_winners:
        return "No winners yet"

    result = []
    for pot_id, winners in game.hand_winners.items():
        winner_names = [p.name for p in winners]

        # Find the pot amount by pot name
        pot_amount = 0
        for pot in game.pots:
            if pot.name == pot_id or f"pot_{pot_id}" == pot_id:
                pot_amount = pot.amount
                break

        pot_display = f"{pot_id} (${pot_amount})"

        if len(winner_names) == 1:
            result.append(f"{winner_names[0]} wins {pot_display}")
        else:
            result.append(f"{', '.join(winner_names)} split {pot_display}")

    return "; ".join(result)
