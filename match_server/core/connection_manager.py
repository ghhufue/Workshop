from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket


@dataclass
class PlayerConnection:
    websocket: WebSocket
    room_id: str
    player_id: str


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, PlayerConnection] = {}

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()

    def register(self, websocket: WebSocket, room_id: str, player_id: str) -> None:
        self._connections[player_id] = PlayerConnection(
            websocket=websocket,
            room_id=room_id,
            player_id=player_id,
        )

    def disconnect(self, websocket: WebSocket) -> None:
        for player_id, connection in list(self._connections.items()):
            if connection.websocket is websocket:
                del self._connections[player_id]

    async def send_to_player(self, player_id: str, payload: dict[str, Any]) -> None:
        connection = self._connections.get(player_id)
        if connection is None:
            return
        await connection.websocket.send_json(payload)

    async def broadcast_room(self, room_id: str, payload: dict[str, Any]) -> None:
        for connection in list(self._connections.values()):
            if connection.room_id == room_id:
                await connection.websocket.send_json(payload)
