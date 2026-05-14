from __future__ import annotations

from shared.constants import EMPTY


def to_engine_board(board: list[list[int]], current_player: int) -> list[list[int]]:
    """Convert a platform board into the engine perspective.

    Engine board values:
    0 = empty
    1 = current engine side
    -1 = opponent side
    """
    return [
        [_to_engine_cell(value, current_player) for value in row]
        for row in board
    ]


def _to_engine_cell(value: int, current_player: int) -> int:
    if value == EMPTY:
        return EMPTY
    if value == current_player:
        return 1
    if value == -current_player:
        return -1
    raise ValueError(f"unexpected board cell value: {value}")
