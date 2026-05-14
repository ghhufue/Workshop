import random

from shared.constants import BOARD_SIZE
from match_server.core.errors import RoomNotFoundError
from match_server.core.room import Player, Room


class RoomManager:
    def __init__(self, board_size: int = BOARD_SIZE) -> None:
        self.board_size = board_size
        self.rooms: dict[str, Room] = {}

    def create_room(self, player_name: str, bot_name: str) -> tuple[Room, Player]:
        room_id = self._generate_room_id()
        room = Room(room_id=room_id, board_size=self.board_size)
        player = room.add_player(player_name, bot_name)
        self.rooms[room_id] = room
        return room, player

    def join_room(self, room_id: str, player_name: str, bot_name: str) -> tuple[Room, Player]:
        room = self.get_room(room_id)
        player = room.add_player(player_name, bot_name)
        return room, player

    def get_room(self, room_id: str) -> Room:
        try:
            return self.rooms[room_id]
        except KeyError as exc:
            raise RoomNotFoundError(f"Room not found: {room_id}") from exc

    def _generate_room_id(self) -> str:
        for _attempt in range(100):
            room_id = f"{random.randint(0, 999999):06d}"
            if room_id not in self.rooms:
                return room_id
        raise RuntimeError("Unable to allocate a unique room id")
