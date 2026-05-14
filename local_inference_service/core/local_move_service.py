from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from local_inference_service.core.engine_process import EngineProcess
from local_inference_service.core.engine_registry import EngineRegistry, EngineSpec
from local_inference_service.core.move_validator import validate_engine_move
from local_inference_service.core.perspective import to_engine_board


@dataclass
class LocalMoveResult:
    row: int
    col: int
    x: int
    y: int
    engine_name: str
    debug: dict[str, Any] = field(default_factory=dict)

    def to_response(self) -> dict[str, Any]:
        return {
            "row": self.row,
            "col": self.col,
            "x": self.x,
            "y": self.y,
            "engine_name": self.engine_name,
            "debug": self.debug,
        }


class LocalMoveService:
    def __init__(self, registry: EngineRegistry | None = None) -> None:
        self.registry = registry or EngineRegistry()
        self._processes: dict[str, EngineProcess] = {}

    def list_engines(self) -> list[str]:
        return self.registry.list_engines()

    async def request_move(
        self,
        board: list[list[int]],
        current_player: int,
        engine_name: str | None,
    ) -> LocalMoveResult:
        spec = self.registry.resolve(engine_name)
        process = self._get_or_create_process(spec)
        engine_board = to_engine_board(board, current_player)
        move = await process.request_move(engine_board)
        validate_engine_move(move.x, move.y, board)

        return LocalMoveResult(
            row=move.y,
            col=move.x,
            x=move.x,
            y=move.y,
            engine_name=spec.name,
            debug=move.debug,
        )

    async def shutdown(self) -> None:
        for process in self._processes.values():
            await process.stop()
        self._processes.clear()

    def _get_or_create_process(self, spec: EngineSpec) -> EngineProcess:
        process = self._processes.get(spec.name)
        if process is None:
            process = EngineProcess(
                command=spec.command,
                args=spec.args,
                working_dir=spec.working_dir,
                timeout_ms=spec.timeout_ms,
            )
            self._processes[spec.name] = process
        return process
