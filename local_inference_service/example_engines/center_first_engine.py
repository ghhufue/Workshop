import json
import random
import sys


def choose_move(board: list[list[int]]) -> tuple[int, int]:
    center = len(board) // 2
    if board[center][center] == 0:
        return center, center

    empty_cells = [
        (x, y)
        for y, row in enumerate(board)
        for x, value in enumerate(row)
        if value == 0
    ]
    if not empty_cells:
        raise RuntimeError("No legal moves")
    return random.choice(empty_cells)


def main() -> None:
    for line in sys.stdin:
        request = json.loads(line)
        x, y = choose_move(request["board"])
        print(json.dumps({"x": x, "y": y, "debug": {"engine": "center_first"}}), flush=True)


if __name__ == "__main__":
    main()
