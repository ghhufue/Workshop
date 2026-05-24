# 模块职责

> 本页是实现细节附录。普通 Workshop 参与者只需要知道：这些模块让 AI 可以在图形界面里对局，不需要记住每个接口。

## Match Server

`match_server` 是远程比赛服务器，也是整局游戏的权威裁判。

它负责：

- 创建和管理房间。
- 接收玩家加入房间。
- 分配黑棋和白棋。
- 维护权威棋盘状态。
- 控制当前回合。
- 校验落子是否合法。
- 判断五连胜负。
- 广播落子结果和游戏结束消息。

当前服务使用 Python + FastAPI 实现：

```text
GET /health
WS  /ws
```

## Local Inference Service

`local_inference_service` 是本地 MoveEngine 托管服务。

它负责：

- 启动和管理 MoveEngine 子进程。
- 提供本地 HTTP `/bot_move` 接口。
- 将平台棋盘转换为 MoveEngine 视角。
- 向 MoveEngine stdin 写入请求。
- 从 MoveEngine stdout 读取响应。
- 处理超时、崩溃和非法输出。

## MoveEngine Process

MoveEngine 是用户自行实现的独立程序或脚本。它只需要遵守 stdin/stdout JSON Lines 协议。

MoveEngine 不需要知道房间号、玩家 ID、回合编号、历史记录或 request_id。

## Bot

Bot 是玩法语义中的机器对手，通常是规则、启发式、随机或搜索逻辑。Bot 可以由 MoveEngine 驱动，但 Bot 不等同于 MoveEngine。

## Godot Client

`godot_client` 是图形客户端。

它负责：

- 主菜单和模式选择。
- 线下和线上房间流程。
- 棋盘显示和棋子动画。
- 在线模型选择。
- 接收服务器消息并同步棋盘。
- 在轮到本地模型时调用 Local Inference Service。
