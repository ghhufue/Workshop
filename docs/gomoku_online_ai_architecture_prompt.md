# 简易五子棋 AI 联机对战系统：项目架构与代码生成 Prompt

## 1. 项目目标

本项目目标是实现一个简易的五子棋 AI 联机对战系统。

核心设计思想：

> Bot 程序可以是任意实现：神经网络模型、MCTS、规则程序、随机程序、C++ 程序、Python 脚本等。  
> 系统不关心 Bot 内部如何决策，只要求 Bot 遵守统一的 stdin/stdout JSON Lines 协议。

系统由三个主要部分组成：

```text
Godot Client / CLI Client
        |
        | WebSocket
        v
Match Server
        ^
        | WebSocket
        |
Local Bot Runner
        |
        | stdin / stdout JSON Lines
        v
Bot Process
```

第一阶段可以先不实现 Godot，只实现：

1. Match Server
2. Local Bot Runner
3. Example Bots
4. 命令行自动对战 Demo

---

## 2. 总体架构

```text
gomoku-online-ai/
├── local_bot_runner/              # 本地 Bot 托管服务
│   ├── app.py                     # 可选 FastAPI 本地 API 入口
│   ├── main.py                    # Local Bot Runner 主入口
│   ├── config.py                  # 配置读取
│   ├── config.yaml                # 默认配置
│   │
│   ├── core/
│   │   ├── bot_process.py         # 启动和管理 Bot 子进程
│   │   ├── bot_runner.py          # BotRunner 抽象逻辑
│   │   ├── match_client.py        # 连接 Match Server 的 WebSocket 客户端
│   │   ├── protocol.py            # 本地协议处理
│   │   ├── validator.py           # Bot 输出校验
│   │   ├── game_state.py          # 本地棋盘缓存
│   │   └── errors.py              # 自定义错误类型
│   │
│   ├── schemas/
│   │   ├── bot_protocol.py        # Bot stdin/stdout 协议 schema
│   │   ├── server_protocol.py     # Match Server WebSocket 协议 schema
│   │   └── local_api.py           # 本地 HTTP API schema，可选
│   │
│   ├── example_bots/
│   │   ├── random_bot.py          # 随机 Bot
│   │   ├── center_first_bot.py    # 第一手优先中心点的 Bot
│   │   ├── invalid_bot.py         # 故意输出非法落子，用于测试
│   │   └── timeout_bot.py         # 故意超时，用于测试
│   │
│   └── tests/
│       ├── test_bot_process.py
│       ├── test_validator.py
│       └── test_protocol.py
│
├── match_server/                  # 远程游戏服务器
│   ├── app.py                     # FastAPI WebSocket 服务入口
│   ├── main.py                    # Match Server 启动入口
│   │
│   ├── core/
│   │   ├── room.py                # 单个房间状态
│   │   ├── room_manager.py        # 房间管理
│   │   ├── gomoku_rules.py        # 五子棋规则和胜负判断
│   │   ├── connection_manager.py  # WebSocket 连接管理
│   │   ├── protocol.py            # 服务器协议处理
│   │   └── errors.py              # 自定义错误类型
│   │
│   ├── schemas/
│   │   └── messages.py            # 服务器消息 schema
│   │
│   └── tests/
│       ├── test_gomoku_rules.py
│       ├── test_room.py
│       └── test_room_manager.py
│
├── shared/
│   ├── constants.py               # 通用常量
│   ├── protocol.md                # 协议文档
│   └── message_examples.json      # 消息示例
│
├── scripts/
│   ├── run_match_server.py
│   ├── run_local_bot_runner.py
│   └── demo_two_bots.py
│
├── configs/
│   ├── player_a.yaml
│   └── player_b.yaml
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 3. 模块职责

### 3.1 Match Server

Match Server 是远程权威服务器，负责：

| 功能 | 说明 |
|---|---|
| 创建房间 | 生成 room_id |
| 加入房间 | 允许第二个玩家加入 |
| 分配黑白 | 创建者默认黑棋，加入者默认白棋 |
| 维护棋盘 | 服务器保存权威棋盘 |
| 回合管理 | 控制谁当前可以落子 |
| 校验落子 | 检查越界、重复落子、是否轮到该玩家 |
| 判断胜负 | 检查横、竖、两条对角线是否五连 |
| 广播状态 | 向双方发送 move_result 和 game_over |
| 发送 your_turn | 通知当前玩家调用本地 Bot |

第一版不需要：

- 账号系统
- 数据库
- 排行榜
- 观战系统
- 断线重连
- 禁手规则

---

### 3.2 Local Bot Runner

Local Bot Runner 是本地托管服务，负责：

| 功能 | 说明 |
|---|---|
| 读取配置 | 从 YAML 读取 Bot 启动命令和服务器地址 |
| 启动 Bot | 用 asyncio 启动 Bot 子进程 |
| 管理 stdin/stdout | 向 Bot stdin 写入请求，从 stdout 读取响应 |
| 超时控制 | Bot 超过 time_limit_ms 未响应则判定失败 |
| 输出校验 | 校验 Bot 输出 JSON、request_id、坐标合法性 |
| 连接服务器 | 使用 WebSocket 连接 Match Server |
| 上传落子 | 将 Bot 返回的 x/y 上传给 Match Server |
| 日志管理 | Bot stderr 用于调试日志，避免污染 stdout |

关键点：

> Local Bot Runner 不关心 Bot 内部是模型、规则、MCTS 还是随机逻辑。  
> 它只要求 Bot 遵守 stdin/stdout JSON Lines 协议。

---

### 3.3 Bot Process

Bot 是用户自己写的程序。

它只需要做到：

1. 从 stdin 读取一行 JSON。
2. 根据棋盘选择一个合法落子。
3. 向 stdout 输出一行 JSON。
4. 所有调试日志必须输出到 stderr。

Bot 可以是：

```text
Python 脚本
C++ 可执行文件
Java 程序
Rust 程序
PyTorch 推理程序
ONNX 推理程序
MCTS 搜索程序
纯规则 Bot
随机 Bot
```

---

## 4. 棋盘与坐标约定

棋盘格式：

```text
board[y][x]
```

棋盘值：

```text
0  = 空位
1  = 黑棋
-1 = 白棋
```

坐标：

```text
x = 横坐标，从 0 到 14
y = 纵坐标，从 0 到 14
```

默认棋盘大小：

```text
board_size = 15
```

动作编号，如需使用：

```text
action = y * board_size + x
x = action % board_size
y = action // board_size
```

---

## 5. Bot stdin/stdout 协议

### 5.1 Local Bot Runner 发送给 Bot

Local Bot Runner 每次要求 Bot 下棋时，向 Bot stdin 写入一行 JSON，末尾带换行符。

```json
{
  "type": "request_move",
  "request_id": "room_ABC_move_12",
  "room_id": "ABC",
  "board_size": 15,
  "player": 1,
  "move_index": 12,
  "time_limit_ms": 3000,
  "board": [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
  ],
  "history": [
    {"x": 7, "y": 7, "player": 1},
    {"x": 7, "y": 8, "player": -1}
  ]
}
```

注意：

实际 `board` 必须是完整的 `15 x 15` 二维数组。

---

### 5.2 Bot 输出给 Local Bot Runner

Bot 必须向 stdout 输出一行 JSON，末尾带换行符。

```json
{
  "type": "move",
  "request_id": "room_ABC_move_12",
  "x": 7,
  "y": 8
}
```

可选字段：

```json
{
  "type": "move",
  "request_id": "room_ABC_move_12",
  "x": 7,
  "y": 8,
  "value": 0.42,
  "debug": {
    "thinking_ms": 25,
    "model": "ppo_resnet_v3"
  }
}
```

---

### 5.3 stdout 和 stderr 规则

必须规定：

```text
stdout：只能输出协议 JSON
stderr：输出调试日志
```

Python Bot 的调试日志应该这样写：

```python
import sys

print("model loaded", file=sys.stderr)
```

不能这样写：

```python
print("model loaded")
```

因为 stdout 会被 Local Bot Runner 当作协议数据解析。

---

## 6. Match Server WebSocket 协议

### 6.1 create_room

Local Bot Runner 发送：

```json
{
  "type": "create_room",
  "player_name": "player_a",
  "bot_name": "random_bot"
}
```

服务器返回：

```json
{
  "type": "room_created",
  "room_id": "ABC",
  "player_id": "p1",
  "color": 1
}
```

---

### 6.2 join_room

Local Bot Runner 发送：

```json
{
  "type": "join_room",
  "room_id": "ABC",
  "player_name": "player_b",
  "bot_name": "center_first_bot"
}
```

服务器返回：

```json
{
  "type": "room_joined",
  "room_id": "ABC",
  "player_id": "p2",
  "color": -1
}
```

---

### 6.3 game_start

服务器向双方广播：

```json
{
  "type": "game_start",
  "room_id": "ABC",
  "board_size": 15,
  "black_player": "player_a",
  "white_player": "player_b",
  "current_turn": 1,
  "board": [[0]]
}
```

实际 `board` 是完整的 `15 x 15` 二维数组。

---

### 6.4 your_turn

服务器发送给当前回合玩家：

```json
{
  "type": "your_turn",
  "room_id": "ABC",
  "request_id": "room_ABC_move_0",
  "board_size": 15,
  "player": 1,
  "move_index": 0,
  "time_limit_ms": 3000,
  "board": [[0]],
  "history": []
}
```

Local Bot Runner 收到后：

```text
your_turn
→ 构造 Bot request_move
→ 写入 Bot stdin
→ 等待 Bot stdout
→ 校验 Bot 输出
→ 上传 move 给服务器
```

---

### 6.5 move

Local Bot Runner 上传：

```json
{
  "type": "move",
  "room_id": "ABC",
  "request_id": "room_ABC_move_0",
  "x": 7,
  "y": 7
}
```

---

### 6.6 move_result

服务器广播：

```json
{
  "type": "move_result",
  "room_id": "ABC",
  "accepted": true,
  "x": 7,
  "y": 7,
  "player": 1,
  "next_turn": -1,
  "winner": 0,
  "move_index": 1,
  "board": [[0]]
}
```

实际 `board` 是完整的 `15 x 15` 二维数组。

---

### 6.7 game_over

服务器广播：

```json
{
  "type": "game_over",
  "room_id": "ABC",
  "winner": 1,
  "reason": "five_in_a_row",
  "final_board": [[0]]
}
```

---

### 6.8 error

服务器返回错误：

```json
{
  "type": "error",
  "code": "INVALID_MOVE",
  "message": "Cell is already occupied"
}
```

---

## 7. Local Bot Runner 内部流程

```text
启动 Local Bot Runner
→ 读取 config.yaml
→ 启动 Bot 子进程
→ 连接远程 Match Server
→ 创建房间或加入房间
→ 等待服务器消息

收到 your_turn:
    1. 构造 BotRequest
    2. 写入 Bot stdin
    3. 等待 stdout 一行 JSON
    4. 做超时检测
    5. 做 JSON 格式检测
    6. 做 request_id 匹配检测
    7. 做坐标合法性检测
    8. 做目标位置为空检测
    9. 上传 move 给 Match Server

收到 move_result:
    1. 更新本地棋盘缓存
    2. 记录日志

收到 game_over:
    1. 打印最终结果
    2. 正常退出或等待下一局
```

---

## 8. Match Server 内部流程

```text
启动 Match Server
→ 等待 WebSocket 连接

收到 create_room:
    1. 创建 Room
    2. 分配 player_id
    3. 分配黑棋
    4. 返回 room_created

收到 join_room:
    1. 检查房间是否存在
    2. 检查房间是否未满
    3. 分配白棋
    4. 广播 game_start
    5. 向黑棋发送 your_turn

收到 move:
    1. 检查 room_id 是否存在
    2. 检查 request_id 是否匹配当前回合
    3. 检查是否轮到该玩家
    4. 检查 x/y 是否越界
    5. 检查目标位置是否为空
    6. 更新权威棋盘
    7. 判断是否五连
    8. 广播 move_result
    9. 如果胜利，广播 game_over
    10. 如果未胜利，切换 current_turn，并向下一方发送 your_turn
```

---

## 9. 配置文件示例

### 9.1 player_a.yaml

```yaml
player:
  name: "player_a"

server:
  url: "ws://127.0.0.1:9000/ws"
  mode: "create_room"

bot:
  name: "random_bot"
  command: "python"
  args: ["local_bot_runner/example_bots/random_bot.py"]
  working_dir: "."
  timeout_ms: 3000

game:
  board_size: 15
```

---

### 9.2 player_b.yaml

```yaml
player:
  name: "player_b"

server:
  url: "ws://127.0.0.1:9000/ws"
  mode: "join_room"
  room_id: "ABC"

bot:
  name: "center_first_bot"
  command: "python"
  args: ["local_bot_runner/example_bots/center_first_bot.py"]
  working_dir: "."
  timeout_ms: 3000

game:
  board_size: 15
```

---

## 10. 推荐启动方式

### 10.1 启动 Match Server

```bash
python scripts/run_match_server.py
```

---

### 10.2 启动 Player A

```bash
python scripts/run_local_bot_runner.py --config configs/player_a.yaml
```

---

### 10.3 启动 Player B

```bash
python scripts/run_local_bot_runner.py --config configs/player_b.yaml
```

---

### 10.4 可选：一键 Demo

```bash
python scripts/demo_two_bots.py
```

---

## 11. Example Bots 要求

### 11.1 random_bot.py

功能：

- 从 stdin 读取 `request_move`
- 找到所有空位
- 随机选择一个合法空位
- 向 stdout 输出 `move`

---

### 11.2 center_first_bot.py

功能：

- 如果中心点为空，优先下中心点
- 否则随机选择合法空位

---

### 11.3 invalid_bot.py

功能：

- 故意输出非法坐标
- 用于测试 Local Bot Runner 的校验逻辑

---

### 11.4 timeout_bot.py

功能：

- 故意 sleep 超过 `time_limit_ms`
- 用于测试超时逻辑

---

## 12. 单元测试要求

### 12.1 test_gomoku_rules.py

需要测试：

- 横向五连
- 纵向五连
- 主对角线五连
- 副对角线五连
- 没有五连的情况

---

### 12.2 test_validator.py

需要测试：

- 合法 move
- 非法 JSON
- `request_id` 不匹配
- 坐标越界
- 落在已有棋子上
- `x/y` 不是整数

---

### 12.3 test_bot_process.py

需要测试：

- `random_bot.py` 能返回合法步
- `invalid_bot.py` 会被识别为非法
- `timeout_bot.py` 会触发超时

---

## 13. 关键设计原则

### 13.1 服务器是最终裁判

即使 Local Bot Runner 已经校验了 Bot 输出，Match Server 仍然必须再次校验。

原因：

- 本地服务可能有 bug。
- 本地服务可能被修改。
- 服务器需要维护权威状态。
- 双方棋盘状态必须以服务器为准。

---

### 13.2 Bot 子进程应常驻

不推荐每一步重新启动 Bot。

推荐：

```text
Local Bot Runner 启动时启动 Bot
整局游戏复用同一个 Bot 进程
```

好处：

- 神经网络模型只加载一次。
- MCTS 或搜索程序可以保留内部状态。
- 减少进程启动开销。

---

### 13.3 stdout 不允许打印日志

这是整个系统最容易出错的地方。

错误示例：

```python
print("thinking...")
print(json.dumps(move))
```

正确示例：

```python
import sys
import json

print("thinking...", file=sys.stderr)
print(json.dumps(move), flush=True)
```

---

### 13.4 第一版失败策略

第一版建议：

```text
Bot 超时 / 崩溃 / 输出非法
→ Local Bot Runner 向 Match Server 发送 resign
→ Match Server 判对方获胜
```

不建议第一版自动随机补步，因为这样会掩盖 Bot 的错误。

---

## 14. 可直接给代码生成 AI 的 Prompt

下面这份 Prompt 可以直接交给 Codex、Cursor、Claude Code 或其他代码生成工具。

```text
你需要帮我实现一个“简易五子棋 AI 联机对战系统”。这个项目不要求一开始实现 Godot 前端，先实现后端和本地 Bot Runner 的最小可运行版本。

项目目标：
1. 有一个远程 Match Server，负责五子棋房间、棋盘、回合、胜负判断和 WebSocket 通信。
2. 有一个 Local Bot Runner，本地服务负责启动一个 Bot 子进程，通过 stdin/stdout 与 Bot 通信。
3. Bot 可以是任何程序，比如 Python、C++、神经网络推理程序、规则程序。Local Bot Runner 不关心 Bot 内部实现，只要求它遵守 stdin/stdout JSON Lines 协议。
4. Local Bot Runner 收到远程服务器发来的 your_turn 消息后，把当前棋盘写入 Bot 的 stdin，等待 Bot 从 stdout 输出落子，然后校验并上传给 Match Server。
5. Match Server 是最终裁判，负责校验落子是否合法，并广播最新棋盘状态。
6. 先不实现 Godot 客户端，但协议要设计得方便以后 Godot 接入。

技术要求：
- 使用 Python 实现。
- 使用 FastAPI + WebSocket 实现 Match Server。
- Local Bot Runner 使用 asyncio 管理 Bot 子进程。
- 使用 Pydantic 定义所有协议消息 schema。
- 使用 JSON Lines 协议与 Bot 子进程通信。
- 使用 pytest 编写关键单元测试。
- 所有代码注释使用英文。
- README 使用中文，解释如何启动服务器、启动两个本地 Bot Runner，并跑通一局随机 Bot 对战。

项目目录结构要求：

gomoku-online-ai/
├── local_bot_runner/
│   ├── app.py
│   ├── main.py
│   ├── config.py
│   ├── config.yaml
│   ├── core/
│   │   ├── bot_process.py
│   │   ├── bot_runner.py
│   │   ├── match_client.py
│   │   ├── protocol.py
│   │   ├── validator.py
│   │   ├── game_state.py
│   │   └── errors.py
│   ├── schemas/
│   │   ├── bot_protocol.py
│   │   ├── server_protocol.py
│   │   └── local_api.py
│   ├── example_bots/
│   │   ├── random_bot.py
│   │   ├── center_first_bot.py
│   │   ├── invalid_bot.py
│   │   └── timeout_bot.py
│   └── tests/
│       ├── test_bot_process.py
│       ├── test_validator.py
│       └── test_protocol.py
│
├── match_server/
│   ├── app.py
│   ├── main.py
│   ├── core/
│   │   ├── room.py
│   │   ├── room_manager.py
│   │   ├── gomoku_rules.py
│   │   ├── connection_manager.py
│   │   ├── protocol.py
│   │   └── errors.py
│   ├── schemas/
│   │   └── messages.py
│   └── tests/
│       ├── test_gomoku_rules.py
│       ├── test_room.py
│       └── test_room_manager.py
│
├── shared/
│   ├── constants.py
│   ├── protocol.md
│   └── message_examples.json
│
├── scripts/
│   ├── run_match_server.py
│   ├── run_local_bot_runner.py
│   └── demo_two_bots.py
│
├── configs/
│   ├── player_a.yaml
│   └── player_b.yaml
│
├── requirements.txt
├── README.md
└── .gitignore

核心协议设计：

一、棋盘表示：
- board 是二维 list，格式是 board[y][x]
- 0 表示空位
- 1 表示黑棋
- -1 表示白棋
- board_size 默认是 15
- action 坐标使用 x, y，均从 0 开始

二、Bot stdin 输入协议：
Local Bot Runner 每次要求 Bot 下棋时，向 Bot stdin 写入一行 JSON，末尾带换行符。

示例：
{
  "type": "request_move",
  "request_id": "room_ABC_move_12",
  "room_id": "ABC",
  "board_size": 15,
  "player": 1,
  "move_index": 12,
  "time_limit_ms": 3000,
  "board": [[0, 0, 0]],
  "history": [
    {"x": 7, "y": 7, "player": 1}
  ]
}

注意实际 board 必须是完整的 15x15 二维数组。

三、Bot stdout 输出协议：
Bot 必须向 stdout 输出一行 JSON，末尾带换行符。

示例：
{
  "type": "move",
  "request_id": "room_ABC_move_12",
  "x": 7,
  "y": 8
}

可选字段：
{
  "type": "move",
  "request_id": "room_ABC_move_12",
  "x": 7,
  "y": 8,
  "value": 0.42,
  "debug": {
    "thinking_ms": 25,
    "model": "random_bot"
  }
}

四、stdout/stderr 规则：
- stdout 只能输出协议 JSON。
- stderr 用于调试日志。
- example_bots 中必须遵守这个规则。

五、Match Server WebSocket 协议：

create_room:
客户端发送：
{
  "type": "create_room",
  "player_name": "player_a",
  "bot_name": "random_bot"
}

服务器返回：
{
  "type": "room_created",
  "room_id": "ABC",
  "player_id": "p1",
  "color": 1
}

join_room:
客户端发送：
{
  "type": "join_room",
  "room_id": "ABC",
  "player_name": "player_b",
  "bot_name": "center_first_bot"
}

服务器返回：
{
  "type": "room_joined",
  "room_id": "ABC",
  "player_id": "p2",
  "color": -1
}

game_start:
服务器广播：
{
  "type": "game_start",
  "room_id": "ABC",
  "board_size": 15,
  "black_player": "player_a",
  "white_player": "player_b",
  "current_turn": 1,
  "board": [[...]]
}

your_turn:
服务器发送给当前回合玩家：
{
  "type": "your_turn",
  "room_id": "ABC",
  "request_id": "room_ABC_move_0",
  "board_size": 15,
  "player": 1,
  "move_index": 0,
  "time_limit_ms": 3000,
  "board": [[...]],
  "history": []
}

move:
Local Bot Runner 上传：
{
  "type": "move",
  "room_id": "ABC",
  "request_id": "room_ABC_move_0",
  "x": 7,
  "y": 7
}

move_result:
服务器广播：
{
  "type": "move_result",
  "room_id": "ABC",
  "accepted": true,
  "x": 7,
  "y": 7,
  "player": 1,
  "next_turn": -1,
  "winner": 0,
  "move_index": 1,
  "board": [[...]]
}

game_over:
服务器广播：
{
  "type": "game_over",
  "room_id": "ABC",
  "winner": 1,
  "reason": "five_in_a_row",
  "final_board": [[...]]
}

错误消息：
{
  "type": "error",
  "code": "INVALID_MOVE",
  "message": "Cell is already occupied"
}

Local Bot Runner 行为要求：
1. 启动时读取 YAML 配置。
2. 根据配置启动 Bot 子进程。
3. 使用 asyncio.create_subprocess_exec 启动进程。
4. Bot 进程应该常驻，不要每一步重启。
5. 向 Bot stdin 写入 JSON Lines。
6. 从 Bot stdout 读取一行 JSON。
7. 对 Bot 输出做严格校验：
   - 必须是合法 JSON
   - type 必须是 move
   - request_id 必须匹配
   - x/y 必须是整数
   - x/y 必须在棋盘范围内
   - board[y][x] 必须为空
8. 如果 Bot 超时、崩溃、输出非法，则向服务器发送 bot_error 或 resign。第一版可以直接发送 resign。
9. Bot 的 stderr 要异步读取并写入本地日志，避免 stderr 堵塞导致子进程卡死。
10. 收到服务器 move_result 后更新本地 GameState。
11. 收到 game_over 后打印结果并正常退出。

Match Server 行为要求：
1. 使用 WebSocket 接收 Local Bot Runner 连接。
2. 支持 create_room 和 join_room。
3. 每个房间最多两个玩家。
4. 创建者默认是黑棋 1，加入者是白棋 -1。
5. 房间满员后广播 game_start。
6. game_start 后立即向黑棋发送 your_turn。
7. 收到 move 后，服务器必须校验：
   - room_id 是否存在
   - player 是否属于该房间
   - request_id 是否匹配当前回合
   - 是否轮到该玩家
   - x/y 是否越界
   - 目标位置是否为空
8. 服务器维护权威棋盘。
9. 落子成功后判断胜负。
10. 如果无人胜利，切换 current_turn，并向下一方发送 your_turn。
11. 如果胜利，广播 game_over。
12. 实现五子棋五连判断，横、竖、两条对角线都要检测。
13. 第一版不需要禁手规则。

Example Bots 要求：
1. random_bot.py：
   - 从 stdin 读取 request_move
   - 随机选择一个合法空位
   - stdout 输出 move JSON
2. center_first_bot.py：
   - 第一手优先下中心点
   - 之后随机合法落子
3. invalid_bot.py：
   - 故意输出非法位置，用于测试
4. timeout_bot.py：
   - 故意 sleep 超过 time_limit_ms，用于测试

测试要求：
1. test_gomoku_rules.py：
   - 测试横向五连
   - 测试纵向五连
   - 测试主对角线五连
   - 测试副对角线五连
   - 测试没有五连的情况
2. test_validator.py：
   - 测试合法 move
   - 测试非法 JSON
   - 测试 request_id 不匹配
   - 测试坐标越界
   - 测试落在已有棋子上
3. test_bot_process.py：
   - 测试 random_bot 能返回合法步
   - 测试 invalid_bot 被识别为非法
   - 测试 timeout_bot 会触发超时

README 要求：
README 用中文写，包含：
1. 项目简介
2. 架构图
3. 安装依赖
4. 启动 Match Server
5. 启动 Player A 的 Local Bot Runner
6. 启动 Player B 的 Local Bot Runner
7. 如何运行 demo_two_bots.py
8. 如何编写自己的 Bot
9. Bot stdin/stdout 协议说明
10. 常见错误说明，比如 stdout 打印日志导致 JSON 解析失败

实现优先级：
第一阶段只需要命令行跑通：
- 启动 match_server
- 启动 player_a local_bot_runner
- 启动 player_b local_bot_runner
- 两个 Bot 自动完成一局五子棋
- 终端打印每一步落子和最终胜负

暂时不要实现：
- Godot 客户端
- 数据库
- 账号系统
- 排行榜
- 观战系统
- 复杂断线重连
- 禁手规则
- Docker
- Web 页面

请直接生成完整项目代码。代码要尽量清晰、模块化，保证可以运行。所有 Python 代码注释使用英文。
```

---

## 15. 后续可以扩展的方向

第一版跑通后，可以继续扩展：

1. **Godot 前端**
   - 创建房间
   - 加入房间
   - 棋盘显示
   - 显示双方 Bot 名称
   - 显示实时落子

2. **观战模式**
   - 观众只接收棋盘广播，不发送 move

3. **Bot 信息展示**
   - 显示 value
   - 显示 thinking_ms
   - 显示模型名称
   - 显示 policy 热力图

4. **比赛模式**
   - 多局对战
   - 交换先后手
   - 统计胜率

5. **模型评估**
   - 随机 Bot
   - 规则 Bot
   - MCTS Bot
   - 不同版本神经网络模型

6. **安全隔离**
   - Docker 沙盒
   - 限制 CPU / 内存
   - 限制运行时间

---

## 16. 最终总结

这个系统的核心不是“统一所有模型结构”，而是：

```text
统一输入输出协议
```

也就是：

```text
输入：board + player + move_index + time_limit
输出：x + y
```

只要 Bot 能遵守这个协议，不管它内部是神经网络、搜索算法、规则分支还是随机逻辑，都可以接入你的五子棋联机对战系统。
