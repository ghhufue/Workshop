from __future__ import annotations

from local_inference_service.core.errors import MoveValidationError
from match_server.core.gomoku_rules import is_in_bounds
from shared.constants import EMPTY


def validate_engine_move(x: int, y: int, board: list[list[int]]) -> None:
    """Validate x/y against the platform board."""
    if not isinstance(x, int) or not isinstance(y, int):
        raise MoveValidationError("Move x/y must be integers")

    board_size = len(board)
    if not is_in_bounds(x, y, board_size):
        raise MoveValidationError("Move is out of bounds")

    if board[y][x] != EMPTY:
        raise MoveValidationError("Move targets an occupied cell")
