from fastapi.testclient import TestClient

from local_inference_service.app import app
from match_server.core.gomoku_rules import create_board


def test_local_move_api_returns_row_col() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/bot_move",
            json={
                "board": create_board(15),
                "current_player": 1,
                "engine_name": "center_first",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["row"] == 7
        assert payload["col"] == 7
        assert payload["x"] == 7
        assert payload["y"] == 7
        assert payload["engine_name"] == "center_first"


def test_local_move_api_accepts_existing_godot_bot_name_field() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/bot_move",
            json={
                "board": create_board(15),
                "current_player": -1,
                "bot_name": "trained",
            },
        )

        assert response.status_code == 200
        assert response.json()["engine_name"] == "center_first"
