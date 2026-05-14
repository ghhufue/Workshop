import json
import random
import sys


def choose_move(board: list[list[int]]) -> tuple[int, int]:
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
        print(json.dumps({"type": "move", "request_id": request["request_id"], "x": x, "y": y}), flush=True)


if __name__ == "__main__":
    main()

