# Match Server WebSocket 协议

> 本页是实现细节附录。普通 Workshop 参与者不需要掌握 WebSocket 消息格式；它只服务于客户端联机对局。

Match Server 通过 WebSocket `/ws` 与客户端通信。

## create_room

创建普通玩家房间。

```json
{
  "type": "create_room",
  "player_name": "black_client",
  "model_name": "model_a"
}
```

服务端返回：

```json
{
  "type": "room_created",
  "room_id": "123456",
  "player_id": "p1_xxxxxxxx",
  "color": 1
}
```

## host_game

创建主持房间。主持人是 spectator，不执黑白，但可以控制进入模型选择和开始对局。

```json
{
  "type": "host_game",
  "player_name": "host"
}
```

服务端返回：

```json
{
  "type": "room_hosted",
  "room_id": "123456",
  "spectator_id": "s1_xxxxxxxx"
}
```

## join_room

加入已有房间。

```json
{
  "type": "join_room",
  "room_id": "123456",
  "player_name": "white_client",
  "model_name": "model_b"
}
```

## room_state

房间状态广播，包含玩家数量、黑白双方、模型 ready 状态和是否已满员。

关键字段：

```text
is_full
black_player
white_player
black_model_ready
white_model_ready
all_models_ready
model_select_started
game_started
```

## start_game

`start_game` 有两个阶段：

1. 房间满员后第一次调用，进入模型选择阶段。
2. 两个玩家都 ready 后再次调用，正式开始棋局。

允许调用者：

- 黑棋房间创建者。
- `host_game` 创建的主持人。

## select_model

玩家提交本地模型名称。

```json
{
  "type": "select_model",
  "room_id": "123456",
  "model_name": "trained"
}
```

## game_start

正式开始对局后广播：

```json
{
  "type": "game_start",
  "room_id": "123456",
  "black_player": "black_client",
  "white_player": "white_client",
  "current_turn": 1,
  "move_index": 0,
  "board": []
}
```

## your_turn

只发给当前需要落子的一方。

```json
{
  "type": "your_turn",
  "room_id": "123456",
  "request_id": "123456_000_1",
  "player": 1,
  "move_index": 0,
  "board": []
}
```

## move

客户端提交落子：

```json
{
  "type": "move",
  "room_id": "123456",
  "request_id": "123456_000_1",
  "x": 7,
  "y": 7
}
```

## move_result 与 game_over

合法落子会广播 `move_result`。出现五连或终局时广播 `game_over`。

服务端始终是最终裁判，客户端和本地推理服务的结果都需要服务端重新校验。
