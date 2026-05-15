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


def test_local_move_api_accepts_dynamic_python_engine(tmp_path) -> None:
    engine_path = tmp_path / "custom_engine.py"
    engine_path.write_text(
        "\n".join(
            [
                "import json",
                "import sys",
                "for line in sys.stdin:",
                "    request = json.loads(line)",
                "    print(json.dumps({'x': 3, 'y': 4, 'debug': {'source': 'dynamic_python'}}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )

    with TestClient(app) as client:
        response = client.post(
            "/bot_move",
            json={
                "board": create_board(15),
                "current_player": 1,
                "engine_kind": "python_script",
                "engine_path": str(engine_path),
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["row"] == 4
        assert payload["col"] == 3
        assert payload["x"] == 3
        assert payload["y"] == 4
        assert payload["debug"]["source"] == "dynamic_python"
