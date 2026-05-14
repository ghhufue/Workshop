from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from local_inference_service.core.errors import EngineOutputError


@dataclass(frozen=True)
class EngineMove:
    x: int
    y: int
    debug: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


def parse_engine_output(raw_line: str) -> EngineMove:
    """Parse a loose MoveEngine response and extract x/y.

    Accepted shapes include:
    {"x": 7, "y": 8}
    {"row": 8, "col": 7}
    {"move": {"x": 7, "y": 8}, "debug": {...}}
    """
    try:
        payload = json.loads(raw_line)
    except json.JSONDecodeError as exc:
        raise EngineOutputError("MoveEngine output is not valid JSON") from exc

    if not isinstance(payload, dict):
        raise EngineOutputError("MoveEngine output must be a JSON object")

    x, y = _extract_coordinates(payload)
    debug = _extract_debug(payload)
    return EngineMove(x=x, y=y, debug=debug, raw=payload)


def _extract_coordinates(payload: dict[str, Any]) -> tuple[int, int]:
    if _has_int_coordinates(payload, "x", "y"):
        return int(payload["x"]), int(payload["y"])

    if _has_int_coordinates(payload, "col", "row"):
        return int(payload["col"]), int(payload["row"])

    move = payload.get("move")
    if isinstance(move, dict):
        if _has_int_coordinates(move, "x", "y"):
            return int(move["x"]), int(move["y"])
        if _has_int_coordinates(move, "col", "row"):
            return int(move["col"]), int(move["row"])

    raise EngineOutputError("MoveEngine output does not contain integer x/y")


def _has_int_coordinates(payload: dict[str, Any], x_key: str, y_key: str) -> bool:
    return isinstance(payload.get(x_key), int) and isinstance(payload.get(y_key), int)


def _extract_debug(payload: dict[str, Any]) -> dict[str, Any]:
    debug = payload.get("debug")
    if isinstance(debug, dict):
        return dict(debug)

    return {
        key: value
        for key, value in payload.items()
        if key not in {"x", "y", "row", "col", "move"}
    }
