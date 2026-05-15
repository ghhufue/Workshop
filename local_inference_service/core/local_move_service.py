from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from local_inference_service.core.engine_process import EngineProcess
from local_inference_service.core.engine_registry import ROOT, EngineRegistry, EngineSpec
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
        engine_kind: str | None = None,
        engine_path: str | None = None,
        engine_command: str | None = None,
        engine_args: list[str] | None = None,
        engine_working_dir: str | None = None,
        engine_timeout_ms: int | None = None,
    ) -> LocalMoveResult:
        spec = self._resolve_spec(
            engine_name=engine_name,
            engine_kind=engine_kind,
            engine_path=engine_path,
            engine_command=engine_command,
            engine_args=engine_args,
            engine_working_dir=engine_working_dir,
            engine_timeout_ms=engine_timeout_ms,
        )
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

    def _resolve_spec(
        self,
        engine_name: str | None,
        engine_kind: str | None,
        engine_path: str | None,
        engine_command: str | None,
        engine_args: list[str] | None,
        engine_working_dir: str | None,
        engine_timeout_ms: int | None,
    ) -> EngineSpec:
        if engine_path:
            return self._spec_from_path(
                engine_name=engine_name,
                engine_kind=engine_kind,
                engine_path=engine_path,
                engine_args=engine_args,
                engine_working_dir=engine_working_dir,
                engine_timeout_ms=engine_timeout_ms,
            )

        if engine_command:
            name = self._dynamic_name(engine_name, "command", engine_command, engine_args or [])
            return EngineSpec(
                name=name,
                command=engine_command,
                args=engine_args or [],
                working_dir=Path(engine_working_dir).resolve() if engine_working_dir else ROOT,
                timeout_ms=engine_timeout_ms or 3000,
            )

        return self.registry.resolve(engine_name)

    def _spec_from_path(
        self,
        engine_name: str | None,
        engine_kind: str | None,
        engine_path: str,
        engine_args: list[str] | None,
        engine_working_dir: str | None,
        engine_timeout_ms: int | None,
    ) -> EngineSpec:
        path = Path(engine_path).expanduser().resolve()
        if not path.exists():
            raise ValueError(f"engine path does not exist: {path}")
        if not path.is_file():
            raise ValueError(f"engine path must be a file: {path}")

        kind = self._infer_kind(engine_kind, path)
        args = engine_args or []
        timeout_ms = engine_timeout_ms or 3000
        name = self._dynamic_name(engine_name, kind, str(path), args)
        working_dir = Path(engine_working_dir).resolve() if engine_working_dir else path.parent

        if kind == "python_script":
            import sys

            return EngineSpec(
                name=name,
                command=sys.executable,
                args=[str(path), *args],
                working_dir=working_dir,
                timeout_ms=timeout_ms,
            )

        if kind == "executable":
            return EngineSpec(
                name=name,
                command=str(path),
                args=args,
                working_dir=working_dir,
                timeout_ms=timeout_ms,
            )

        if kind == "gomoku_ai_checkpoint":
            import sys

            return EngineSpec(
                name=name,
                command=sys.executable,
                args=[
                    str(ROOT / "local_inference_service" / "adapters" / "gomoku_ai_checkpoint_engine.py"),
                    "--checkpoint",
                    str(path),
                ],
                working_dir=ROOT,
                timeout_ms=timeout_ms,
            )

        raise ValueError(f"unsupported engine kind: {kind}")

    def _infer_kind(self, engine_kind: str | None, path: Path) -> str:
        if engine_kind and engine_kind.strip():
            return engine_kind.strip().lower()

        suffix = path.suffix.lower()
        if suffix == ".py":
            return "python_script"
        if suffix == ".pt":
            return "gomoku_ai_checkpoint"
        if suffix in {".exe", ".bat", ".cmd"}:
            return "executable"
        return "executable"

    def _dynamic_name(self, engine_name: str | None, kind: str, identifier: str, args: list[str]) -> str:
        import hashlib

        digest = hashlib.sha1("|".join([kind, identifier, *args]).encode("utf-8")).hexdigest()[:12]
        if engine_name and engine_name.strip():
            return f"{engine_name.strip()}:{digest}"
        return f"{kind}:{digest}"

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
