import json
import sys


def main() -> None:
    for line in sys.stdin:
        request = json.loads(line)
        print(json.dumps({"type": "move", "request_id": request["request_id"], "x": -1, "y": -1}), flush=True)


if __name__ == "__main__":
    main()

