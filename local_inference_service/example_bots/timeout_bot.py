import json
import sys
import time


def main() -> None:
    for line in sys.stdin:
        request = json.loads(line)
        time.sleep((request.get("time_limit_ms", 3000) / 1000) + 1)
        print(json.dumps({"type": "move", "request_id": request["request_id"], "x": 0, "y": 0}), flush=True)


if __name__ == "__main__":
    main()

