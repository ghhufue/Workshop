from __future__ import annotations

from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from match_server.core.connection_manager import ConnectionManager
from match_server.core.errors import InvalidMoveError, MatchServerError
from match_server.core.protocol import (
    error,
    expected_request_id,
    game_over,
    game_start,
    move_result,
    room_created,
    room_joined,
    your_turn,
)
from match_server.core.room import Room
from match_server.core.room_manager import RoomManager
from shared.constants import EMPTY


app = FastAPI(title="Gomoku Match Server")
room_manager = RoomManager()
connections = ConnectionManager()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "match_server"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await connections.connect(websocket)
    player_id = ""
    room: Room | None = None
    try:
        while True:
            payload = await websocket.receive_json()
            message_type = str(payload.get("type", ""))

            if message_type == "create_room":
                room, player_id = await _handle_create_room(websocket, payload)
                continue

            if message_type == "join_room":
                room, player_id = await _handle_join_room(websocket, payload)
                continue

            if message_type == "move":
                if room is None or not player_id:
                    await websocket.send_json(error("NOT_JOINED", "Client is not in a room"))
                    continue
                await _handle_move(websocket, room, player_id, payload)
                continue

            await websocket.send_json(error("UNKNOWN_MESSAGE", f"Unsupported message type: {message_type}"))
    except WebSocketDisconnect:
        connections.disconnect(websocket)
    except MatchServerError as exc:
        await websocket.send_json(error("MATCH_ERROR", str(exc)))
        connections.disconnect(websocket)


async def _handle_create_room(websocket: WebSocket, payload: dict[str, Any]) -> tuple[Room, str]:
    player_name = str(payload.get("player_name") or "player")
    model_name = _model_name_from_payload(payload)
    room, player = room_manager.create_room(player_name, model_name)
    connections.register(websocket, room.room_id, player.player_id)
    await websocket.send_json(room_created(room, player))
    return room, player.player_id


async def _handle_join_room(websocket: WebSocket, payload: dict[str, Any]) -> tuple[Room, str]:
    room_id = str(payload.get("room_id") or "")
    player_name = str(payload.get("player_name") or "player")
    model_name = _model_name_from_payload(payload)
    room, player = room_manager.join_room(room_id, player_name, model_name)
    connections.register(websocket, room.room_id, player.player_id)
    await websocket.send_json(room_joined(room, player))

    if room.is_full:
        await connections.broadcast_room(room.room_id, game_start(room))
        await _send_turn_to_current_player(room)

    return room, player.player_id


async def _handle_move(
    websocket: WebSocket,
    room: Room,
    player_id: str,
    payload: dict[str, Any],
) -> None:
    request_id = str(payload.get("request_id") or "")
    expected_id = expected_request_id(room)
    if request_id != expected_id:
        await websocket.send_json(error("REQUEST_ID_MISMATCH", "Move request_id does not match current turn"))
        return

    x, y = _coordinates_from_payload(payload)
    player_color = room.players[player_id].color
    try:
        result = room.apply_move(player_id, x, y)
    except InvalidMoveError as exc:
        await websocket.send_json(error("INVALID_MOVE", str(exc)))
        return

    await connections.broadcast_room(room.room_id, move_result(room, x, y, player_color, result))

    if room.winner != EMPTY:
        await connections.broadcast_room(room.room_id, game_over(room))
        return

    await _send_turn_to_current_player(room)


async def _send_turn_to_current_player(room: Room) -> None:
    for player in room.players.values():
        if player.color == room.current_turn:
            await connections.send_to_player(player.player_id, your_turn(room))
            return


def _model_name_from_payload(payload: dict[str, Any]) -> str:
    return str(payload.get("model_name") or payload.get("engine_name") or payload.get("bot_name") or "model")


def _coordinates_from_payload(payload: dict[str, Any]) -> tuple[int, int]:
    if "x" in payload and "y" in payload:
        return int(payload["x"]), int(payload["y"])
    if "col" in payload and "row" in payload:
        return int(payload["col"]), int(payload["row"])
    raise InvalidMoveError("Move must contain x/y or row/col")
