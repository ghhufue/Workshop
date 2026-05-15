from dataclasses import dataclass, field
from uuid import uuid4

from shared.constants import BLACK, BOARD_SIZE, EMPTY, WHITE
from match_server.core.errors import InvalidMoveError, RoomFullError
from match_server.core.gomoku_rules import create_board, has_five_in_a_row, is_in_bounds


@dataclass
class Player:
    player_id: str
    player_name: str
    bot_name: str
    color: int
    avatar_index: int = 0


@dataclass
class Move:
    x: int
    y: int
    player: int


@dataclass
class Spectator:
    spectator_id: str
    spectator_name: str


@dataclass
class Room:
    room_id: str
    board_size: int = BOARD_SIZE
    players: dict[str, Player] = field(default_factory=dict)
    spectators: dict[str, Spectator] = field(default_factory=dict)
    board: list[list[int]] = field(default_factory=lambda: create_board(BOARD_SIZE))
    current_turn: int = BLACK
    move_index: int = 0
    history: list[Move] = field(default_factory=list)
    winner: int = EMPTY

    def __post_init__(self) -> None:
        if len(self.board) != self.board_size:
            self.board = create_board(self.board_size)

    @property
    def is_full(self) -> bool:
        return len(self.players) >= 2

    def add_player(self, player_name: str, bot_name: str, avatar_index: int = 0) -> Player:
        if self.is_full:
            raise RoomFullError("Room is full")

        color = BLACK if not self.players else WHITE
        player = Player(
            player_id=f"p{len(self.players) + 1}_{uuid4().hex[:8]}",
            player_name=player_name,
            bot_name=bot_name,
            color=color,
            avatar_index=avatar_index,
        )
        self.players[player.player_id] = player
        return player

    def add_spectator(self, spectator_name: str) -> Spectator:
        spectator = Spectator(
            spectator_id=f"s{len(self.spectators) + 1}_{uuid4().hex[:8]}",
            spectator_name=spectator_name,
        )
        self.spectators[spectator.spectator_id] = spectator
        return spectator

    def apply_move(self, player_id: str, x: int, y: int) -> dict[str, int | bool]:
        player = self.players.get(player_id)
        if player is None:
            raise InvalidMoveError("Player does not belong to this room")
        if self.winner != EMPTY:
            raise InvalidMoveError("Game is already over")
        if player.color != self.current_turn:
            raise InvalidMoveError("It is not this player's turn")
        if not is_in_bounds(x, y, self.board_size):
            raise InvalidMoveError("Move is out of bounds")
        if self.board[y][x] != EMPTY:
            raise InvalidMoveError("Cell is already occupied")

        self.board[y][x] = player.color
        self.history.append(Move(x=x, y=y, player=player.color))
        self.move_index += 1

        if has_five_in_a_row(self.board, x, y):
            self.winner = player.color
        else:
            self.current_turn = WHITE if self.current_turn == BLACK else BLACK

        return {
            "accepted": True,
            "winner": self.winner,
            "next_turn": self.current_turn,
            "move_index": self.move_index,
        }
