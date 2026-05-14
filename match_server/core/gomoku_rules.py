from shared.constants import EMPTY


DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))


def create_board(board_size: int) -> list[list[int]]:
    return [[EMPTY for _ in range(board_size)] for _ in range(board_size)]


def is_in_bounds(x: int, y: int, board_size: int) -> bool:
    return 0 <= x < board_size and 0 <= y < board_size


def is_valid_cell_value(value: int) -> bool:
    return value in (-1, 0, 1)


def has_five_in_a_row(board: list[list[int]], x: int, y: int) -> bool:
    player = board[y][x]
    if player == EMPTY:
        return False

    board_size = len(board)
    for dx, dy in DIRECTIONS:
        count = 1
        count += _count_direction(board, x, y, dx, dy, player, board_size)
        count += _count_direction(board, x, y, -dx, -dy, player, board_size)
        if count >= 5:
            return True
    return False


def _count_direction(
    board: list[list[int]],
    x: int,
    y: int,
    dx: int,
    dy: int,
    player: int,
    board_size: int,
) -> int:
    count = 0
    cx = x + dx
    cy = y + dy
    while is_in_bounds(cx, cy, board_size) and board[cy][cx] == player:
        count += 1
        cx += dx
        cy += dy
    return count

