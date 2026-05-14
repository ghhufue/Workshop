# 简易五子棋 AI 联机对战系统

这是一个面向 AI Bot 对战的五子棋联机系统。项目的核心目标不是统一 Bot 的内部实现，而是统一 Bot 与平台之间的通信协议。只要 Bot 能通过标准输入和标准输出读写 JSON Lines 消息，它就可以接入系统参与对战。

Bot 可以是规则程序、随机程序、MCTS、神经网络模型推理程序，也可以是 Python、C++、Java、Rust 或其他语言实现的独立进程。

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
Bot Process
```

第一阶段优先实现命令行可运行版本，不包含 Godot 前端。目标是让两个本地 Bot 通过服务器完成一局自动五子棋对战。

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

### Local Inference Service

`local_inference_service` 是本地 Bot 托管服务，对应架构文档中的 Local Bot Runner。

它负责：

- 读取本地配置
- 启动并管理 Bot 子进程
- 连接远程 Match Server
- 收到 `your_turn` 后把棋盘请求写入 Bot 的 stdin
- 从 Bot 的 stdout 读取落子响应
- 校验 Bot 输出格式和基本合法性
- 将合法落子上传给 Match Server
- 处理 Bot 超时、崩溃或非法输出

Local Inference Service 不关心 Bot 内部如何决策，只要求 Bot 遵守约定的 stdin/stdout JSON Lines 协议。

### Bot Process

Bot 是用户自行实现的独立程序。

Bot 只需要遵守两条核心规则：

- 从 stdin 读取一行 JSON 请求
- 向 stdout 输出一行 JSON 落子结果

调试日志必须写入 stderr，不能写入 stdout。stdout 会被本地服务当作协议数据解析，如果混入日志，会导致 JSON 解析失败。

### Godot Client

`godot_client` 是后续可扩展的图形客户端方向。第一阶段暂不实现。

未来它可以用于：

- 创建房间
- 加入房间
- 显示棋盘
- 展示双方 Bot 名称
- 实时显示落子
- 支持观战模式

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

第一层是 Match Server 与 Local Inference Service 之间的 WebSocket 协议，主要消息包括：

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

第二层是 Local Inference Service 与 Bot Process 之间的 stdin/stdout JSON Lines 协议。

当轮到某个 Bot 落子时，本地服务会向 Bot stdin 写入一行 `request_move` JSON。Bot 需要在时间限制内向 stdout 输出一行 `move` JSON。

## 第一阶段目标

第一阶段只需要跑通命令行自动对战：

1. 启动 Match Server
2. 启动 Player A 的 Local Inference Service
3. 启动 Player B 的 Local Inference Service
4. 两个 Bot 自动完成一局五子棋
5. 终端输出每一步落子和最终胜负

第一阶段暂不实现：

- Godot 前端
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
输入：board + player + move_index + time_limit
输出：x + y
```

### 服务器是最终裁判

Match Server 必须维护权威状态。任何客户端或本地服务提交的落子都需要由服务器重新验证。

这样可以避免：

- 本地服务存在 bug
- 本地服务被修改
- 双方棋盘状态不一致
- 非法落子污染比赛结果

### Bot 进程应常驻

Bot 不建议每一步重新启动。推荐在本地服务启动时创建 Bot 子进程，并在整局游戏中复用。

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
- `local_inference_service`：本地 Bot 托管服务，对应文档中的 Local Bot Runner
- `godot_client`：后续 Godot 客户端
- `gomoku_ai`：另一个独立项目，本项目不在其中放置内容

