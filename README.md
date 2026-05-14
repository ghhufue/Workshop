# 简易五子棋 AI 联机对战系统

这是一个面向 AI Bot 对战和本地模型/逻辑引擎对战的五子棋系统。项目的核心目标不是统一不同落子实现的内部结构，而是统一平台与落子能力之间的边界：平台维护棋盘、回合、校验和 UI；本地落子能力只需要根据棋盘返回下一步坐标。

当前命名上区分 `Bot` 和 `MoveEngine`：`Bot` 特指规则/启发式机器人对手，主要用于人机和模型 vs Bot；`MoveEngine` 泛指能根据棋盘输出落子的本地引擎，可以是规则逻辑、C++ 程序、搜索程序或神经网络推理进程。

## 总体架构

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
Local Inference Service
        |
        | stdin / stdout JSON Lines
        v
MoveEngine Process
```

当前实现已经包含一条最小可运行的 Godot 在线 model-vs-model 链路：两个 Godot 客户端通过 Match Server 同步房间和棋盘，各自收到 `your_turn` 后复用本地 HTTP 连接请求 Local Inference Service 计算落子。

## 模块说明

### Match Server

`match_server` 是远程比赛服务器，也是整局游戏的权威裁判。

它负责：

- 创建和管理房间
- 接收玩家加入房间
- 分配黑棋和白棋
- 维护权威棋盘状态
- 控制当前回合
- 校验落子是否合法
- 判断五连胜负
- 向双方广播落子结果和游戏结束消息

即使本地服务已经校验过 Bot 的输出，服务器仍然必须再次校验。棋盘状态、回合顺序和胜负结果都以 Match Server 为准。

当前 Match Server 使用 Python + FastAPI 实现：

```text
GET /health
WS  /ws
```

WebSocket 支持：

- `create_room`：创建 6 位数字房间号
- `join_room`：加入已有房间
- `game_start`：房间满员后广播开始
- `your_turn`：只发给当前应落子的一方
- `move`：客户端提交落子
- `move_result`：向双方广播合法落子
- `game_over`：向双方广播胜负结果
- `error`：返回协议或落子错误

### Local Inference Service

`local_inference_service` 是本地 MoveEngine 托管服务，对应架构文档中的 Local Bot Runner，但新的命名中它不再只服务 Bot。

它负责：

- 读取本地配置
- 启动并管理 MoveEngine 子进程
- 提供本地 HTTP `/bot_move` 接口，供 Godot 复用现有本地请求链路
- 把 Godot 或服务器同步得到的棋盘转换为 MoveEngine 视角
- 把棋盘请求写入 MoveEngine 的 stdin
- 从 MoveEngine 的 stdout 读取落子响应
- 校验 MoveEngine 输出格式和基本合法性
- 处理 MoveEngine 超时、崩溃或非法输出

Local Inference Service 不关心 MoveEngine 内部如何决策，只要求它遵守约定的 stdin/stdout JSON Lines 协议。

当前本地 HTTP 接口：

```text
GET  /health
GET  /engines
POST /bot_move
```

`POST /bot_move` 兼容 Godot 当前请求：

```json
{
  "board": [[0]],
  "current_player": 1,
  "bot_name": "trained"
}
```

返回：

```json
{
  "row": 7,
  "col": 7,
  "x": 7,
  "y": 7,
  "engine_name": "center_first",
  "debug": {}
}
```

### MoveEngine Process

MoveEngine 是用户自行实现的独立程序或脚本。

MoveEngine 只需要遵守两条核心规则：

- 从 stdin 读取一行只包含棋盘的 JSON 请求
- 向 stdout 输出一行能提取出 `x` 和 `y` 的 JSON 落子结果

调试日志必须写入 stderr，不能写入 stdout。stdout 会被本地服务当作协议数据解析，如果混入日志，会导致 JSON 解析失败。

### Bot

Bot 是玩法语义中的机器人对手，不是底层协议名。

Bot 通常是规则、启发式、随机或搜索逻辑，用于：

- Human vs Bot
- Model vs Bot
- Bot vs Bot

Bot 的落子可以由 MoveEngine 驱动，但 Bot 不等同于 MoveEngine。神经网络模型推理、外部 C++ 逻辑进程、训练策略评估等通用落子能力应称为 MoveEngine。

### Godot Client

`godot_client` 是图形客户端。

当前已具备：

- 在线创建房间
- 在线加入房间
- 显示棋盘
- 展示双方模型名称
- 接收服务器 `move_result` 并同步渲染
- 收到服务器 `your_turn` 后调用已有 `LocalHttpMoveProvider`
- 将本地 HTTP 返回的落子再提交给 Match Server

联机模式当前只面向 model-vs-model。这里的 model 是广义概念，可以是神经网络，也可以是非神经网络的逻辑实现。人类落子不参与联机回合；如果下一步是本地模型/逻辑进程，Godot 才会发本地 HTTP 请求。

## 棋盘约定

棋盘使用二维数组表示：

```text
board[y][x]
```

棋子值约定：

```text
0  = 空位
1  = 黑棋
-1 = 白棋
```

默认棋盘大小：

```text
15 x 15
```

坐标从 `0` 开始：

```text
x = 横坐标，范围 0 到 14
y = 纵坐标，范围 0 到 14
```

## 通信协议概览

系统内部有两层通信协议。

第一层是 Godot Client 与 Match Server 之间的 WebSocket 协议，主要消息包括：

- `create_room`
- `room_created`
- `join_room`
- `room_joined`
- `game_start`
- `your_turn`
- `move`
- `move_result`
- `game_over`
- `error`

第二层是 Godot Client 与 Local Inference Service 之间的本地 HTTP 协议，当前核心接口是 `POST /bot_move`。

第三层是 Local Inference Service 与 MoveEngine Process 之间的 stdin/stdout JSON Lines 协议。

当轮到某个本地引擎落子时，本地服务会向 MoveEngine stdin 写入一行极简 JSON。MoveEngine 只接收当前棋盘，不需要维护平台棋盘状态、房间、回合、历史或 request_id。

MoveEngine 输入：

```json
{
  "board": [
    [0, 0, 0],
    [0, 1, 0],
    [0, -1, 0]
  ]
}
```

棋盘值从引擎视角解释：

```text
0  = 空位
1  = 我方棋子
-1 = 敌方棋子
```

MoveEngine 输出可以很宽松，最小格式是：

```json
{
  "x": 7,
  "y": 8
}
```

如果输出包含 `debug`，本地服务会保留并在后续链路中上传或展示。

### 本地 HTTP 接口分层

Godot 可以通过本地 HTTP 请求接入不同落子能力。

Bot 专用桥接层位于 `gomoku_ai/bots`，负责把 Godot 的 Bot 落子请求转给现有 `gomoku_ai.bots` 实现：

```text
Godot
  -> POST /bot_move
  -> gomoku_ai.bots local HTTP bridge
  -> Bot.next_action()
  -> row/col
```

这个接口只处理 Bot 角色，不处理神经网络模型或通用外部进程。

模型、独立逻辑程序、C++ 可执行文件、神经网络推理等通用落子能力由 `local_inference_service` 的 MoveEngine 层处理：

```text
Godot / Match Server
  -> Local Inference Service
  -> MoveEngine stdin/stdout
  -> x/y
```

因此：

```text
Bot 是一种玩法角色。
MoveEngine 是一种落子执行能力。
Bot 的落子可以走 MoveEngine，也可以直接使用 gomoku_ai.bots 中的 Bot.next_action()。
模型和通用逻辑进程必须走 MoveEngine。
```

## 当前运行方式

启动 Match Server：

```bash
python -m match_server.main
```

默认地址：

```text
ws://127.0.0.1:9000/ws
```

启动 Local Inference Service：

```bash
python -m local_inference_service.main
```

默认地址：

```text
http://127.0.0.1:8000/bot_move
```

Godot 在线模式流程：

1. 打开 Online Mode Select
2. 输入 Match Server 地址、玩家名、模型名
3. 一端点击 Create Room
4. 另一端输入 6 位房间号并点击 Join Room
5. 房间满员后服务器广播 `game_start`
6. 当前回合一方收到 `your_turn`
7. Godot 调用 Local Inference Service 的 `/bot_move`
8. Godot 将返回的 `row/col` 作为 `move` 发给 Match Server
9. Match Server 校验并广播 `move_result`

当前暂不实现：

- 数据库
- 账号系统
- 排行榜
- 观战系统
- 复杂断线重连
- 禁手规则
- Docker 沙箱
- Web 页面

## 设计原则

### 统一协议，而不是统一 Bot

系统不要求所有 Bot 使用相同算法或模型结构。Bot 内部可以完全不同，只要输入输出协议一致，就能接入平台。

核心抽象是：

```text
MoveEngine 输入：board
输出：x + y
```

平台层负责维护 `player`、`move_index`、`time_limit`、历史、校验和胜负判断。MoveEngine 不需要维护这些平台状态。

### 服务器是最终裁判

Match Server 必须维护权威状态。任何客户端或本地服务提交的落子都需要由服务器重新验证。

这样可以避免：

- 本地服务存在 bug
- 本地服务被修改
- 双方棋盘状态不一致
- 非法落子污染比赛结果

### MoveEngine 进程应常驻

MoveEngine 不建议每一步重新启动。推荐在本地服务启动时创建 MoveEngine 子进程，并在整局游戏中复用。

这样可以减少进程启动开销，也方便神经网络模型、搜索程序或推理服务保留内部状态。

## 后续扩展方向

项目跑通第一阶段后，可以继续扩展：

- Godot 图形客户端
- 观战模式
- Bot 调试信息展示
- 多局比赛和胜率统计
- 不同版本模型评估
- MCTS Bot、规则 Bot、神经网络 Bot
- Docker 沙箱隔离
- CPU、内存和运行时间限制

## 当前仓库命名说明

本地目录命名与架构文档略有不同：

- `match_server`：比赛服务器
- `local_inference_service`：本地 MoveEngine 托管服务，对应旧文档中的 Local Bot Runner
- `godot_client`：后续 Godot 客户端
- `gomoku_ai`：AI 训练与规则 Bot 项目，其中 `gomoku_ai/bots` 提供 Bot 专用本地 HTTP 桥接层
