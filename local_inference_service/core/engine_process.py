from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from local_inference_service.core.engine_output_parser import EngineMove, parse_engine_output
from local_inference_service.core.engine_protocol import encode_engine_request
from local_inference_service.core.errors import EngineProcessError


@dataclass
class EngineProcess:
    command: str
    args: Sequence[str] = field(default_factory=list)
    working_dir: str | Path | None = None
    timeout_ms: int = 3000

    _process: asyncio.subprocess.Process | None = field(default=None, init=False)
    _stderr_task: asyncio.Task | None = field(default=None, init=False)
    stderr_lines: list[str] = field(default_factory=list, init=False)

    async def start(self) -> None:
        if self._process is not None and self._process.returncode is None:
            return

        self._process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            cwd=str(self.working_dir) if self.working_dir is not None else None,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._stderr_task = asyncio.create_task(self._drain_stderr())

    async def stop(self) -> None:
        process = self._process
        if process is None:
            return

        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

        if self._stderr_task is not None:
            self._stderr_task.cancel()
            self._stderr_task = None

        self._process = None

    async def request_move(self, engine_board: list[list[int]]) -> EngineMove:
        await self.start()
        process = self._require_process()

        if process.stdin is None or process.stdout is None:
            raise EngineProcessError("MoveEngine process pipes are not available")

        process.stdin.write(encode_engine_request(engine_board).encode("utf-8"))
        await process.stdin.drain()

        try:
            raw_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=max(0.001, self.timeout_ms / 1000),
            )
        except asyncio.TimeoutError as exc:
            raise EngineProcessError("MoveEngine timed out") from exc

        if not raw_line:
            raise EngineProcessError("MoveEngine exited without output")

        return parse_engine_output(raw_line.decode("utf-8"))

    def _require_process(self) -> asyncio.subprocess.Process:
        if self._process is None or self._process.returncode is not None:
            raise EngineProcessError("MoveEngine process is not running")
        return self._process

    async def _drain_stderr(self) -> None:
        process = self._process
        if process is None or process.stderr is None:
            return

        while True:
            line = await process.stderr.readline()
            if not line:
                return
            self.stderr_lines.append(line.decode("utf-8", errors="replace").rstrip())
