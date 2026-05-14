from match_server.core.gomoku_rules import create_board, has_five_in_a_row
from shared.constants import BLACK


def test_horizontal_five_in_a_row() -> None:
    board = create_board(15)
    for x in range(3, 8):
        board[4][x] = BLACK

    assert has_five_in_a_row(board, 5, 4)


def test_vertical_five_in_a_row() -> None:
    board = create_board(15)
    for y in range(2, 7):
        board[y][6] = BLACK

    assert has_five_in_a_row(board, 6, 4)


def test_main_diagonal_five_in_a_row() -> None:
    board = create_board(15)
    for offset in range(5):
        board[2 + offset][3 + offset] = BLACK

    assert has_five_in_a_row(board, 5, 4)


def test_anti_diagonal_five_in_a_row() -> None:
    board = create_board(15)
    for offset in range(5):
        board[6 - offset][3 + offset] = BLACK

    assert has_five_in_a_row(board, 5, 4)


def test_no_five_in_a_row() -> None:
    board = create_board(15)
    for x in range(4):
        board[0][x] = BLACK

    assert not has_five_in_a_row(board, 3, 0)

