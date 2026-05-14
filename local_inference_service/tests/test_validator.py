import json

import pytest

from local_inference_service.core.errors import BotValidationError
from local_inference_service.core.validator import validate_bot_move
from match_server.core.gomoku_rules import create_board
from shared.constants import BLACK


def test_validate_legal_move() -> None:
    board = create_board(15)
    raw_line = json.dumps({"type": "move", "request_id": "r1", "x": 7, "y": 8})

    payload = validate_bot_move(raw_line, "r1", board)

    assert payload["x"] == 7
    assert payload["y"] == 8


def test_rejects_invalid_json() -> None:
    with pytest.raises(BotValidationError):
        validate_bot_move("{", "r1", create_board(15))


def test_rejects_request_id_mismatch() -> None:
    raw_line = json.dumps({"type": "move", "request_id": "other", "x": 7, "y": 8})

    with pytest.raises(BotValidationError):
        validate_bot_move(raw_line, "r1", create_board(15))


def test_rejects_out_of_bounds_move() -> None:
    raw_line = json.dumps({"type": "move", "request_id": "r1", "x": 15, "y": 0})

    with pytest.raises(BotValidationError):
        validate_bot_move(raw_line, "r1", create_board(15))


def test_rejects_occupied_cell() -> None:
    board = create_board(15)
    board[8][7] = BLACK
    raw_line = json.dumps({"type": "move", "request_id": "r1", "x": 7, "y": 8})

    with pytest.raises(BotValidationError):
        validate_bot_move(raw_line, "r1", board)


def test_rejects_non_integer_coordinates() -> None:
    raw_line = json.dumps({"type": "move", "request_id": "r1", "x": 7.5, "y": 8})

    with pytest.raises(BotValidationError):
        validate_bot_move(raw_line, "r1", create_board(15))

