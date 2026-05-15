from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
GOMOKU_AI_ROOT = ROOT / "gomoku_ai"
if str(GOMOKU_AI_ROOT) not in sys.path:
    sys.path.insert(0, str(GOMOKU_AI_ROOT))


BOARD_SIZE = 15
BOARD_AREA = BOARD_SIZE * BOARD_SIZE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MoveEngine adapter for gomoku_ai PPO checkpoints.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def load_model(checkpoint_path: Path, device: str):
    import torch
    from gomoku_ai.model import ActorCriticNet, model_config_from_checkpoint_payload

    payload = torch.load(checkpoint_path, map_location=device)
    if not isinstance(payload, dict) or "model_state_dict" not in payload:
        raise ValueError(f"checkpoint does not contain model_state_dict: {checkpoint_path}")

    model_config = model_config_from_checkpoint_payload(payload)
    model = ActorCriticNet(model_config).to(device)
    model.load_state_dict(payload["model_state_dict"])
    model.eval()
    return model, torch


def build_observation(board: list[list[int]], torch_module):
    obs = torch_module.zeros((1, 3, BOARD_SIZE, BOARD_SIZE), dtype=torch_module.float32)
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            value = int(board[row][col])
            if value == 1:
                obs[0, 0, row, col] = 1.0
            elif value == -1:
                obs[0, 1, row, col] = 1.0
            else:
                obs[0, 2, row, col] = 1.0
    return obs


def build_action_mask(board: list[list[int]], torch_module):
    mask = torch_module.zeros((1, BOARD_AREA), dtype=torch_module.bool)
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if int(board[row][col]) == 0:
                mask[0, row * BOARD_SIZE + col] = True
    return mask


def validate_board(payload: dict[str, Any]) -> list[list[int]]:
    board = payload.get("board")
    if not isinstance(board, list) or len(board) != BOARD_SIZE:
        raise ValueError(f"board must be {BOARD_SIZE}x{BOARD_SIZE}")

    normalized: list[list[int]] = []
    for row in board:
        if not isinstance(row, list) or len(row) != BOARD_SIZE:
            raise ValueError(f"board must be {BOARD_SIZE}x{BOARD_SIZE}")
        normalized.append([int(value) for value in row])
    return normalized


def choose_move(model, torch_module, board: list[list[int]], device: str) -> tuple[int, int, float]:
    obs = build_observation(board, torch_module).to(device)
    mask = build_action_mask(board, torch_module).to(device)
    if not bool(mask.any().item()):
        raise ValueError("board has no legal moves")

    with torch_module.no_grad():
        logits, _value = model(obs)
        masked_logits = logits.masked_fill(~mask, torch_module.finfo(logits.dtype).min)
        action = int(torch_module.argmax(masked_logits, dim=1).item())
        confidence = float(torch_module.softmax(masked_logits, dim=1)[0, action].item())

    return action // BOARD_SIZE, action % BOARD_SIZE, confidence


def main() -> None:
    args = parse_args()
    try:
        model, torch_module = load_model(args.checkpoint, args.device)
    except Exception as exc:
        print(f"failed to load checkpoint: {exc}", file=sys.stderr, flush=True)
        raise

    for line in sys.stdin:
        try:
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError("request must be a JSON object")
            board = validate_board(payload)
            row, col, confidence = choose_move(model, torch_module, board, args.device)
            print(
                json.dumps(
                    {
                        "row": row,
                        "col": col,
                        "x": col,
                        "y": row,
                        "debug": {
                            "adapter": "gomoku_ai_checkpoint",
                            "checkpoint": str(args.checkpoint),
                            "confidence": confidence,
                        },
                    },
                    separators=(",", ":"),
                ),
                flush=True,
            )
        except Exception as exc:
            print(f"checkpoint adapter request failed: {exc}", file=sys.stderr, flush=True)
            print(json.dumps({"error": str(exc)}), flush=True)


if __name__ == "__main__":
    main()
