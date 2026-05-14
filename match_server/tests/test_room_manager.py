import pytest

from match_server.core.errors import RoomNotFoundError
from match_server.core.room_manager import RoomManager
from shared.constants import BLACK, WHITE


def test_create_room_adds_first_player() -> None:
    manager = RoomManager()

    room, player = manager.create_room("player_a", "random_bot")

    assert manager.get_room(room.room_id) is room
    assert player.color == BLACK
    assert len(room.room_id) == 6
    assert room.room_id.isdigit()


def test_join_room_adds_second_player() -> None:
    manager = RoomManager()
    room, _ = manager.create_room("player_a", "random_bot")

    same_room, player = manager.join_room(room.room_id, "player_b", "center_first_bot")

    assert same_room is room
    assert player.color == WHITE
    assert room.is_full


def test_get_missing_room_raises() -> None:
    manager = RoomManager()

    with pytest.raises(RoomNotFoundError):
        manager.get_room("missing")
