from __future__ import annotations

import json
from typing import Any


def build_engine_request(engine_board: list[list[int]]) -> dict[str, Any]:
    """Build the minimal MoveEngine request payload."""
    return {"board": engine_board}


def encode_engine_request(engine_board: list[list[int]]) -> str:
    """Encode a MoveEngine request as one JSON Lines payload."""
    return json.dumps(build_engine_request(engine_board), separators=(",", ":")) + "\n"
