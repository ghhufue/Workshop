import json
import sys


def main() -> None:
    for line in sys.stdin:
        request = json.loads(line)
        print("received board", file=sys.stderr)
        board = request["board"]
        for y, row in enumerate(board):
            for x, value in enumerate(row):
                if value == 0:
                    print(json.dumps({"move": {"x": x, "y": y}, "debug": {"source": "debug_engine"}}), flush=True)
                    break
            else:
                continue
            break


if __name__ == "__main__":
    main()
