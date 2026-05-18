from __future__ import annotations

import argparse
import asyncio
import json
from urllib.error import URLError
from urllib.request import urlopen

import websockets


def health_url_from_ws(ws_url: str) -> str:
    if ws_url.startswith("ws://"):
        return "http://" + ws_url[len("ws://") :].removesuffix("/ws") + "/health"
    if ws_url.startswith("wss://"):
        return "https://" + ws_url[len("wss://") :].removesuffix("/ws") + "/health"
    raise ValueError("WebSocket URL must start with ws:// or wss://")


def check_health(ws_url: str, timeout: float) -> None:
    health_url = health_url_from_ws(ws_url)
    print(f"[health] GET {health_url}")
    try:
        with urlopen(health_url, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(f"[health] HTTP {response.status}: {body}")
            payload = json.loads(body)
            if response.status != 200 or payload.get("service") != "match_server":
                raise RuntimeError(f"unexpected health response: {response.status} {payload}")
    except URLError as exc:
        raise RuntimeError(f"health request failed: {exc}") from exc


async def recv_type(ws, expected_type: str, timeout: float) -> dict:
    raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
    payload = json.loads(raw)
    print(f"[ws] recv {payload}")
    if payload.get("type") != expected_type:
        raise RuntimeError(f"expected {expected_type}, got {payload.get('type')}")
    return payload


async def check_websocket(ws_url: str, timeout: float) -> None:
    print(f"[ws] connect {ws_url}")
    async with websockets.connect(ws_url, open_timeout=timeout) as black_ws:
        await black_ws.send(json.dumps({"type": "create_room", "player_name": "smoke_black", "model_name": "smoke_a"}))
        created = await recv_type(black_ws, "room_created", timeout)
        room_id = created["room_id"]
        print(f"[ws] room id {room_id}")

        async with websockets.connect(ws_url, open_timeout=timeout) as white_ws:
            await white_ws.send(
                json.dumps(
                    {
                        "type": "join_room",
                        "room_id": room_id,
                        "player_name": "smoke_white",
                        "model_name": "smoke_b",
                    }
                )
            )
            await recv_type(white_ws, "room_joined", timeout)
            await recv_type(black_ws, "room_state", timeout)
            await recv_type(white_ws, "room_state", timeout)
            await black_ws.send(json.dumps({"type": "start_game", "room_id": room_id}))
            await recv_type(black_ws, "model_select", timeout)
            await recv_type(white_ws, "model_select", timeout)
            await recv_type(black_ws, "room_state", timeout)
            await recv_type(white_ws, "room_state", timeout)
            await black_ws.send(json.dumps({"type": "select_model", "room_id": room_id, "model_name": "smoke_a"}))
            await recv_type(black_ws, "room_state", timeout)
            await recv_type(white_ws, "room_state", timeout)
            await white_ws.send(json.dumps({"type": "select_model", "room_id": room_id, "model_name": "smoke_b"}))
            await recv_type(black_ws, "room_state", timeout)
            await recv_type(white_ws, "room_state", timeout)
            await black_ws.send(json.dumps({"type": "start_game", "room_id": room_id}))
            await recv_type(black_ws, "game_start", timeout)
            await recv_type(white_ws, "game_start", timeout)
            turn = await recv_type(black_ws, "your_turn", timeout)
            await black_ws.send(
                json.dumps(
                    {
                        "type": "move",
                        "room_id": room_id,
                        "request_id": turn["request_id"],
                        "x": 7,
                        "y": 7,
                    }
                )
            )
            await recv_type(black_ws, "move_result", timeout)
            await recv_type(white_ws, "move_result", timeout)
            await recv_type(white_ws, "your_turn", timeout)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test the online Gomoku match server.")
    parser.add_argument("--ws-url", default="ws://frp-cup.com:57190/ws")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--skip-health", action="store_true")
    args = parser.parse_args()

    if not args.skip_health:
        check_health(args.ws_url, args.timeout)
    await check_websocket(args.ws_url, args.timeout)
    print("[ok] online match smoke test passed")


if __name__ == "__main__":
    asyncio.run(main())
