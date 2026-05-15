from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from local_inference_service.core.errors import EngineProcessError, MoveValidationError
from local_inference_service.core.local_move_service import LocalMoveService


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await move_service.shutdown()


class LocalMoveRequest(BaseModel):
    board: list[list[int]]
    current_player: int
    bot_name: str | None = None
    engine_name: str | None = None
    engine_kind: str | None = None
    engine_path: str | None = None
    engine_command: str | None = None
    engine_args: list[str] | None = None
    engine_working_dir: str | None = None
    engine_timeout_ms: int | None = None
    model_path: str | None = None


move_service = LocalMoveService()
app = FastAPI(title="Local Inference Service", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "local_inference_service"}


@app.get("/engines")
def engines() -> dict[str, list[str]]:
    return {"engines": move_service.list_engines()}


@app.post("/bot_move")
async def bot_move(request: LocalMoveRequest) -> dict[str, Any]:
    engine_name = request.engine_name or request.bot_name
    try:
        result = await move_service.request_move(
            board=request.board,
            current_player=request.current_player,
            engine_name=engine_name,
            engine_kind=request.engine_kind,
            engine_path=request.engine_path or request.model_path,
            engine_command=request.engine_command,
            engine_args=request.engine_args,
            engine_working_dir=request.engine_working_dir,
            engine_timeout_ms=request.engine_timeout_ms,
        )
    except (KeyError, ValueError, EngineProcessError, MoveValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result.to_response()
