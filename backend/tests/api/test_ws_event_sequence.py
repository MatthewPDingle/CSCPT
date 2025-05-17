# mypy: ignore-errors
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

import pytest

from app.main import app
from app.core.websocket import ConnectionManager, GameStateNotifier


class DummyService:
    def __init__(self):
        self.poker_games = {
            "game1": MagicMock(players=[], current_round=None, to_act=set())
        }

    def get_game(self, game_id: str):
        return MagicMock(id=game_id, players=[])


def setup_ws_test(monkeypatch):
    """Patch WebSocket dependencies for test."""
    cm = ConnectionManager()
    notifier = GameStateNotifier(cm)
    monkeypatch.setattr("app.api.game_ws.connection_manager", cm)
    monkeypatch.setattr("app.api.game_ws.game_notifier", notifier)
    dummy_service = DummyService()
    monkeypatch.setattr("app.api.game_ws.get_game_service", lambda: dummy_service)
    return cm


@pytest.mark.asyncio
async def test_event_sequence(monkeypatch):
    cm = setup_ws_test(monkeypatch)

    async def fake_process_action_message(
        websocket, game_id, message, player_id, service
    ):
        await cm.broadcast_to_game(game_id, {"type": "round_bets_finalized"})
        await cm.broadcast_to_game(game_id, {"type": "street_dealt"})
        await cm.broadcast_to_game(game_id, {"type": "showdown_hands_revealed"})
        await cm.broadcast_to_game(game_id, {"type": "pot_winners_determined"})
        await cm.broadcast_to_game(game_id, {"type": "chips_distributed"})

    monkeypatch.setattr(
        "app.api.game_ws.process_action_message", fake_process_action_message
    )

    client = TestClient(app)
    events = [
        "round_bets_finalized",
        "street_dealt",
        "showdown_hands_revealed",
        "pot_winners_determined",
        "chips_distributed",
    ]
    with client.websocket_connect("/ws/game/game1") as ws:
        ws.send_json({"type": "action", "data": {}})
        received = [ws.receive_json()["type"] for _ in events]
    assert received == events
