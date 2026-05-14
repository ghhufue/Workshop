import asyncio
import json
import sys

import pytest

from local_inference_service.core.engine_output_parser import parse_engine_output
from local_inference_service.core.engine_process import EngineProcess
from local_inference_service.core.engine_protocol import build_engine_request, encode_engine_request
from local_inference_service.core.errors import EngineOutputError, MoveValidationError
from local_inference_service.core.move_validator import validate_engine_move
from local_inference_service.core.perspective import to_engine_board
from match_server.core.gomoku_rules import create_board
from shared.constants import BLACK, WHITE


def test_to_engine_board_for_black() -> None:
    board = [
        [0, BLACK, WHITE],
        [WHITE, 0, BLACK],
    ]

    assert to_engine_board(board, BLACK) == [
        [0, 1, -1],
        [-1, 0, 1],
    ]


def test_to_engine_board_for_white() -> None:
    board = [
        [0, BLACK, WHITE],
        [WHITE, 0, BLACK],
    ]

    assert to_engine_board(board, WHITE) == [
        [0, -1, 1],
        [1, 0, -1],
    ]


def test_build_engine_request_contains_only_board() -> None:
    engine_board = [[0, 1], [-1, 0]]

    assert build_engine_request(engine_board) == {"board": engine_board}
    assert json.loads(encode_engine_request(engine_board)) == {"board": engine_board}


def test_parse_direct_xy_output() -> None:
    move = parse_engine_output('{"x": 7, "y": 8, "debug": {"thinking_ms": 25}}')

    assert move.x == 7
    assert move.y == 8
    assert move.debug["thinking_ms"] == 25


def test_parse_nested_move_output() -> None:
    move = parse_engine_output('{"move": {"x": 3, "y": 4}, "value": 0.5}')

    assert move.x == 3
    assert move.y == 4
    assert move.debug["value"] == 0.5


def test_parse_row_col_output() -> None:
    move = parse_engine_output('{"row": 5, "col": 6}')

    assert move.x == 6
    assert move.y == 5


def test_parse_rejects_missing_coordinates() -> None:
    with pytest.raises(EngineOutputError):
        parse_engine_output('{"debug": "no move"}')


def test_validate_engine_move() -> None:
    board = create_board(15)
    validate_engine_move(7, 8, board)

    board[8][7] = BLACK
    with pytest.raises(MoveValidationError):
        validate_engine_move(7, 8, board)

    with pytest.raises(MoveValidationError):
        validate_engine_move(15, 0, board)


def test_engine_process_reads_minimal_board_and_returns_move() -> None:
    move = asyncio.run(_request_center_first_move())

    assert move.x == 7
    assert move.y == 7
    assert move.debug["engine"] == "center_first"


async def _request_center_first_move():
    process = EngineProcess(
        command=sys.executable,
        args=["local_inference_service/example_engines/center_first_engine.py"],
        timeout_ms=1000,
    )

    try:
        move = await process.request_move(create_board(15))
    finally:
        await process.stop()
    return move
