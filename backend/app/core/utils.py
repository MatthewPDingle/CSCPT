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
    import logging
    import traceback
    
    try:
        # Validate input
        if not game_id:
            raise ValueError("Game ID is required for game_to_model")
        
        if not game:
            raise ValueError(f"PokerGame instance is required for game_id {game_id}")
            
        # Log basic game information for debugging
        logging.debug(f"Converting PokerGame to model: Game ID: {game_id}, " 
                      f"Players: {len(game.players)}, Round: {game.current_round.name if game.current_round else 'None'}")
        
        # Convert community cards with error handling
        try:
            community_cards = []
            for card in game.community_cards:
                try:
                    card_model = CardModel(
                        rank=str(card.rank), 
                        suit=card.suit.name[0] if hasattr(card.suit, 'name') else str(card.suit)[0]
                    )
                    community_cards.append(card_model)
                except Exception as e:
                    logging.error(f"Error converting community card: {str(e)}")
                    logging.error(traceback.format_exc())
                    # Skip this card but continue processing
        except Exception as e:
            logging.error(f"Error processing community cards: {str(e)}")
            logging.error(traceback.format_exc())
            community_cards = []  # Use empty list as fallback

        # Convert players with error handling
        players = []
        try:
            for player in game.players:
                try:
                    # Only include player's cards if they have been dealt
                    cards = None
                    if hasattr(player, 'hand') and player.hand and hasattr(player.hand, 'cards') and len(player.hand.cards) > 0:
                        cards = []
                        for card in player.hand.cards:
                            try:
                                card_model = CardModel(
                                    rank=str(card.rank), 
                                    suit=card.suit.name[0] if hasattr(card.suit, 'name') else str(card.suit)[0]
                                )
                                cards.append(card_model)
                            except Exception as card_error:
                                logging.error(f"Error converting player card: {str(card_error)}")
                                # Skip this card but continue processing

                    # Safely get player attributes with defaults
                    player_id = getattr(player, 'player_id', f"player_{len(players)}")
                    name = getattr(player, 'name', f"Player {len(players)}")
                    chips = getattr(player, 'chips', 0)
                    position = getattr(player, 'position', 0)
                    status = getattr(player, 'status', None)
                    status_name = status.name if status else "UNKNOWN"
                    current_bet = getattr(player, 'current_bet', 0)
                    total_bet = getattr(player, 'total_bet', 0)

                    # Log player chip count for debugging all-in issues
                    if status_name == "ALL_IN" and chips > 0:
                        logging.warning(f"[GAME-STATE] WARNING: Player {name} has status ALL_IN but chips={chips}")
                    
                    players.append(
                        PlayerModel(
                            player_id=player_id,
                            name=name,
                            chips=chips,
                            position=position,
                            status=status_name,
                            current_bet=current_bet,
                            total_bet=total_bet,
                            cards=cards,
                        )
                    )
                except Exception as player_error:
                    logging.error(f"Error converting player: {str(player_error)}")
                    logging.error(traceback.format_exc())
                    # Skip this player but continue processing
        except Exception as e:
            logging.error(f"Error processing players: {str(e)}")
            logging.error(traceback.format_exc())
            # If we couldn't process any players, create at least one dummy player
            # to avoid frontend issues
            if not players:
                players = [PlayerModel(
                    player_id="dummy",
                    name="Player",
                    chips=1000,
                    position=0,
                    status="ACTIVE",
                    current_bet=0,
                    total_bet=0,
                    cards=None,
                )]

        # Convert pots with error handling
        pots = []
        try:
            for pot in game.pots:
                try:
                    name = getattr(pot, 'name', None) or "Pot"
                    amount = getattr(pot, 'amount', 0)
                    eligible_players = getattr(pot, 'eligible_players', set())
                    
                    pots.append(
                        PotModel(
                            name=name,
                            amount=amount,
                            eligible_player_ids=list(eligible_players),
                        )
                    )
                except Exception as pot_error:
                    logging.error(f"Error converting pot: {str(pot_error)}")
                    logging.error(traceback.format_exc())
                    # Skip this pot but continue processing
        except Exception as e:
            logging.error(f"Error processing pots: {str(e)}")
            logging.error(traceback.format_exc())

        # If no pots, create a default main pot
        if not pots:
            pots = [PotModel(name="Main Pot", amount=0, eligible_player_ids=[])]

        # Calculate total pot amount
        total_pot = sum(pot.amount for pot in pots)

        # Safely get game attributes with defaults needed for logging
        current_round = getattr(game, 'current_round', None)
        current_round_name = current_round.name if current_round else "PREFLOP"

        # Debug logging: pot details and total
        try:
            logging.info(f"[game_to_model DEBUG] game_id={game_id}, current_round={current_round_name}")
            # Log each PotModel
            for idx, pmodel in enumerate(pots):
                logging.info(f"[game_to_model DEBUG] PotModel[{idx}]: name={pmodel.name}, amount={pmodel.amount}")
            # Also log raw PokerGame.pots if available
            try:
                raw_sum = sum(p.amount for p in game.pots)
                logging.info(f"[game_to_model DEBUG] Sum of raw PokerGame.pots: {raw_sum}")
            except Exception:
                pass
            logging.info(f"[game_to_model DEBUG] Returning GameStateModel.total_pot={total_pot}")
        except Exception:
            # Ignore logging errors
            pass

        # Safely get game attributes with defaults
        button_position = getattr(game, 'button_position', 0)
        current_player_idx = getattr(game, 'current_player_idx', 0)
        current_bet = getattr(game, 'current_bet', 0)
        small_blind = getattr(game, 'small_blind', 1)
        big_blind = getattr(game, 'big_blind', 2)
        ante = getattr(game, 'ante', 0)

        # Create the game state model with base fields
        game_state = GameStateModel(
            game_id=game_id,
            players=players,
            community_cards=community_cards,
            pots=pots,
            total_pot=total_pot,
            current_round=current_round_name,
            button_position=button_position,
            current_player_idx=current_player_idx,
            current_bet=current_bet,
            small_blind=small_blind,
            big_blind=big_blind,
            ante=ante,
        )
        
        # Add cash game specific fields if available
        try:
            from app.services.game_service import GameService
            service = GameService.get_instance()
            domain_game = service.get_game(game_id)
            
            if domain_game and hasattr(domain_game, 'type') and domain_game.type.name == 'CASH':
                # Cash game - add min/max buy-in
                game_state.min_buy_in = getattr(domain_game, 'min_buy_in', None)
                game_state.max_buy_in = getattr(domain_game, 'max_buy_in', None)
        except Exception as domain_error:
            logging.error(f"Error adding domain-specific fields: {str(domain_error)}")
            logging.error(traceback.format_exc())
            # Continue without domain-specific fields
        
        # Attach action history from domain hand model
        try:
            from app.services.game_service import GameService
            from app.models.game_models import ActionHistoryModel
            svc = GameService.get_instance()
            domain_game = svc.get_game(game_id)
            current_hand = getattr(domain_game, 'current_hand', None)
            if current_hand and hasattr(current_hand, 'actions'):
                game_state.action_history = []
                for ah in current_hand.actions:
                    # Convert timestamp to ISO string to ensure JSON serializability
                    ts = ah.timestamp.isoformat() if hasattr(ah, 'timestamp') else None
                    game_state.action_history.append(
                        ActionHistoryModel(
                            player_id=ah.player_id,
                            action=ah.action.value if hasattr(ah.action, 'value') else str(ah.action),
                            amount=ah.amount,
                            round=ah.round.value if hasattr(ah.round, 'value') else str(ah.round),
                            timestamp=ts
                        )
                    )
        except Exception as history_error:
            logging.error(f"Error attaching action history: {history_error}")
            logging.error(traceback.format_exc())
        
        logging.debug(f"Successfully converted game to model: {game_id}")
        return game_state
        
    except Exception as e:
        logging.error(f"Critical error in game_to_model: {str(e)}")
        logging.error(traceback.format_exc())
        
        # Create a minimal valid game state as fallback
        # This is better than crashing the connection
        emergency_game_state = GameStateModel(
            game_id=game_id,
            players=[
                PlayerModel(
                    player_id="emergency",
                    name="Player",
                    chips=1000,
                    position=0,
                    status="ACTIVE",
                    current_bet=0,
                    total_bet=0,
                    cards=None,
                )
            ],
            community_cards=[],
            pots=[PotModel(name="Main Pot", amount=0, eligible_player_ids=[])],
            total_pot=0,
            current_round="PREFLOP",
            button_position=0,
            current_player_idx=0,
            current_bet=0,
            small_blind=1,
            big_blind=2,
            ante=0,
        )
        
        return emergency_game_state


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
