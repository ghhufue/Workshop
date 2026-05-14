import pytest

from match_server.core.errors import InvalidMoveError, RoomFullError
from match_server.core.room import Room
from shared.constants import BLACK, EMPTY, WHITE


def test_add_players_assigns_black_then_white() -> None:
    room = Room(room_id="ABC")

    first = room.add_player("player_a", "random_bot")
    second = room.add_player("player_b", "center_first_bot")

    assert first.color == BLACK
    assert second.color == WHITE


def test_room_rejects_third_player() -> None:
    room = Room(room_id="ABC")
    room.add_player("player_a", "random_bot")
    room.add_player("player_b", "center_first_bot")

    with pytest.raises(RoomFullError):
        room.add_player("player_c", "random_bot")


def test_apply_move_updates_board_and_turn() -> None:
    room = Room(room_id="ABC")
    black = room.add_player("player_a", "random_bot")
    white = room.add_player("player_b", "center_first_bot")

    result = room.apply_move(black.player_id, 7, 7)

    assert result["accepted"] is True
    assert room.board[7][7] == BLACK
    assert room.current_turn == WHITE
    assert room.winner == EMPTY
    assert room.history[-1].player == BLACK
    assert white.color == WHITE


def test_apply_move_rejects_wrong_turn() -> None:
    room = Room(room_id="ABC")
    room.add_player("player_a", "random_bot")
    white = room.add_player("player_b", "center_first_bot")

    with pytest.raises(InvalidMoveError):
        room.apply_move(white.player_id, 7, 7)


def test_apply_move_sets_winner() -> None:
    room = Room(room_id="ABC")
    black = room.add_player("player_a", "random_bot")
    room.add_player("player_b", "center_first_bot")
    for x in range(4):
        room.board[0][x] = BLACK

    result = room.apply_move(black.player_id, 4, 0)

    assert result["winner"] == BLACK
    assert room.winner == BLACK

