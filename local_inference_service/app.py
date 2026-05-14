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
        )
    except (KeyError, ValueError, EngineProcessError, MoveValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result.to_response()

