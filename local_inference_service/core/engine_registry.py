from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class EngineSpec:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    working_dir: Path = ROOT
    timeout_ms: int = 3000


class EngineRegistry:
    def __init__(self) -> None:
        self._engines: dict[str, EngineSpec] = {
            "center_first": EngineSpec(
                name="center_first",
                command=sys.executable,
                args=["local_inference_service/example_engines/center_first_engine.py"],
            ),
            "debug": EngineSpec(
                name="debug",
                command=sys.executable,
                args=["local_inference_service/example_engines/debug_engine.py"],
            ),
        }
        self._aliases: dict[str, str] = {
            "trained": "center_first",
            "model": "center_first",
            "default": "center_first",
        }

    def list_engines(self) -> list[str]:
        return sorted(self._engines.keys())

    def resolve(self, name: str | None) -> EngineSpec:
        requested = (name or "default").strip().lower()
        resolved_name = self._aliases.get(requested, requested)
        try:
            return self._engines[resolved_name]
        except KeyError as exc:
            raise KeyError(f"unsupported MoveEngine: {name}") from exc
