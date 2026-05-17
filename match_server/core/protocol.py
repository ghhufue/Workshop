from __future__ import annotations

from typing import Any

from match_server.core.room import Player, Room


def expected_request_id(room: Room) -> str:
    return f"{room.room_id}_{room.move_index:03d}_{room.current_turn}"


def room_created(room: Room, player: Player) -> dict[str, Any]:
    return {
        "type": "room_created",
        "room_id": room.room_id,
        "player_id": player.player_id,
        "color": player.color,
        "player_name": player.player_name,
        "avatar_index": player.avatar_index,
        "board_size": room.board_size,
    }


def room_joined(room: Room, player: Player) -> dict[str, Any]:
    return {
        "type": "room_joined",
        "room_id": room.room_id,
        "player_id": player.player_id,
        "color": player.color,
        "player_name": player.player_name,
        "avatar_index": player.avatar_index,
        "board_size": room.board_size,
    }


def room_hosted(room: Room, spectator_id: str) -> dict[str, Any]:
    return {
        "type": "room_hosted",
        "room_id": room.room_id,
        "spectator_id": spectator_id,
        "board_size": room.board_size,
    }


def room_state(room: Room) -> dict[str, Any]:
    players = _players_by_color(room)
    black = players.get(1)
    white = players.get(-1)
    return {
        "type": "room_state",
        "room_id": room.room_id,
        "board_size": room.board_size,
        "player_count": len(room.players),
        "black_player": black.player_name if black else "",
        "black_model": black.bot_name if black else "",
        "black_avatar_index": black.avatar_index if black else 0,
        "white_player": white.player_name if white else "",
        "white_model": white.bot_name if white else "",
        "white_avatar_index": white.avatar_index if white else 0,
        "is_full": room.is_full,
    }


def game_start(room: Room) -> dict[str, Any]:
    players = _players_by_color(room)
    return {
        "type": "game_start",
        "room_id": room.room_id,
        "board_size": room.board_size,
        "black_player": players[1].player_name,
        "white_player": players[-1].player_name,
        "black_avatar_index": players[1].avatar_index,
        "white_avatar_index": players[-1].avatar_index,
        "black_model": players[1].bot_name,
        "white_model": players[-1].bot_name,
        "current_turn": room.current_turn,
        "move_index": room.move_index,
        "board": room.board,
    }


def your_turn(room: Room) -> dict[str, Any]:
    return {
        "type": "your_turn",
        "room_id": room.room_id,
        "request_id": expected_request_id(room),
        "board_size": room.board_size,
        "player": room.current_turn,
        "move_index": room.move_index,
        "board": room.board,
    }


def move_result(room: Room, x: int, y: int, player: int, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "move_result",
        "room_id": room.room_id,
        "accepted": bool(result["accepted"]),
        "x": x,
        "y": y,
        "row": y,
        "col": x,
        "player": player,
        "next_turn": int(result["next_turn"]),
        "winner": int(result["winner"]),
        "move_index": int(result["move_index"]),
        "board": room.board,
    }


def game_over(room: Room, reason: str = "five_in_a_row") -> dict[str, Any]:
    return {
        "type": "game_over",
        "room_id": room.room_id,
        "winner": room.winner,
        "reason": reason,
        "final_board": room.board,
    }


def error(code: str, message: str) -> dict[str, str]:
    return {
        "type": "error",
        "code": code,
        "message": message,
    }


def _players_by_color(room: Room) -> dict[int, Player]:
    return {player.color: player for player in room.players.values()}
