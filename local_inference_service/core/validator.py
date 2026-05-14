import json
from typing import Any

from local_inference_service.core.errors import BotValidationError
from match_server.core.gomoku_rules import is_in_bounds
from shared.constants import EMPTY


def validate_bot_move(raw_line: str, request_id: str, board: list[list[int]]) -> dict[str, Any]:
    try:
        payload = json.loads(raw_line)
    except json.JSONDecodeError as exc:
        raise BotValidationError("Bot output is not valid JSON") from exc

    if payload.get("type") != "move":
        raise BotValidationError("Bot output type must be move")
    if payload.get("request_id") != request_id:
        raise BotValidationError("Bot request_id does not match")

    x = payload.get("x")
    y = payload.get("y")
    if not isinstance(x, int) or not isinstance(y, int):
        raise BotValidationError("Bot move x/y must be integers")

    board_size = len(board)
    if not is_in_bounds(x, y, board_size):
        raise BotValidationError("Bot move is out of bounds")
    if board[y][x] != EMPTY:
        raise BotValidationError("Bot move targets an occupied cell")

    return payload

