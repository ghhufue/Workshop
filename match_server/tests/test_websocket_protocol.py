from fastapi.testclient import TestClient

from match_server.app import app


def test_websocket_create_join_and_move_flow() -> None:
    client = TestClient(app)

    with client.websocket_connect("/ws") as black_ws:
        black_ws.send_json(
            {
                "type": "create_room",
                "player_name": "black_client",
                "model_name": "model_a",
                "avatar_index": 2,
            }
        )
        created = black_ws.receive_json()
        assert created["type"] == "room_created"
        assert created["color"] == 1
        assert len(created["room_id"]) == 6
        assert created["room_id"].isdigit()

        with client.websocket_connect("/ws") as white_ws:
            white_ws.send_json(
                {
                    "type": "join_room",
                    "room_id": created["room_id"],
                    "player_name": "white_client",
                    "model_name": "model_b",
                    "avatar_index": 1,
                }
            )
            joined = white_ws.receive_json()
            assert joined["type"] == "room_joined"
            assert joined["color"] == -1

            state = black_ws.receive_json()
            assert state["type"] == "room_state"
            assert state["is_full"] is True

            white_state = white_ws.receive_json()
            assert white_state["type"] == "room_state"
            assert white_state["is_full"] is True

            black_ws.send_json(
                {
                    "type": "start_game",
                    "room_id": created["room_id"],
                }
            )

            black_model_select = black_ws.receive_json()
            white_model_select = white_ws.receive_json()
            assert black_model_select["type"] == "model_select"
            assert white_model_select["type"] == "model_select"

            black_model_state = black_ws.receive_json()
            white_model_state = white_ws.receive_json()
            assert black_model_state["type"] == "room_state"
            assert white_model_state["type"] == "room_state"
            assert black_model_state["all_models_ready"] is False

            black_ws.send_json(
                {
                    "type": "select_model",
                    "room_id": created["room_id"],
                    "model_name": "model_a_selected",
                }
            )
            black_ready_state = black_ws.receive_json()
            white_observed_black_ready = white_ws.receive_json()
            assert black_ready_state["black_model_ready"] is True
            assert white_observed_black_ready["black_model_ready"] is True

            white_ws.send_json(
                {
                    "type": "select_model",
                    "room_id": created["room_id"],
                    "model_name": "model_b_selected",
                }
            )
            black_all_ready = black_ws.receive_json()
            white_all_ready = white_ws.receive_json()
            assert black_all_ready["all_models_ready"] is True
            assert white_all_ready["all_models_ready"] is True

            black_ws.send_json(
                {
                    "type": "start_game",
                    "room_id": created["room_id"],
                }
            )

            black_start = black_ws.receive_json()
            white_start = white_ws.receive_json()
            assert black_start["type"] == "game_start"
            assert white_start["type"] == "game_start"
            assert black_start["black_model"] == "model_a_selected"
            assert black_start["white_model"] == "model_b_selected"
            assert black_start["black_avatar_index"] == 2
            assert black_start["white_avatar_index"] == 1

            turn = black_ws.receive_json()
            assert turn["type"] == "your_turn"
            assert turn["player"] == 1

            black_ws.send_json(
                {
                    "type": "move",
                    "room_id": created["room_id"],
                    "request_id": turn["request_id"],
                    "x": 7,
                    "y": 7,
                }
            )

            black_result = black_ws.receive_json()
            white_result = white_ws.receive_json()
            assert black_result["type"] == "move_result"
            assert white_result["type"] == "move_result"
            assert black_result["row"] == 7
            assert black_result["col"] == 7
            assert black_result["next_turn"] == -1

            white_turn = white_ws.receive_json()
            assert white_turn["type"] == "your_turn"
            assert white_turn["player"] == -1
