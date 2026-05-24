# MoveEngine JSON Lines 协议

> 本页是实现细节附录。只有在你想接入自己的落子脚本、可执行程序或模型时，才需要阅读本协议。理解 PPO 训练和五子棋 AI 博弈不依赖本页。

MoveEngine 是一个通用落子进程：接收一个棋盘，返回一个落子。它可以是规则程序、搜索程序、C++ 可执行文件、Python 脚本或神经网络推理进程。

`Bot` 是玩法角色，通常指规则或启发式机器对手。Bot 可以由 MoveEngine 实现，但并不是所有 MoveEngine 都应该叫 Bot。

## 进程边界

```text
Local Inference Service
        |
        | stdin/stdout JSON Lines
        v
MoveEngine Process
```

Local Inference Service 维护平台状态：玩家颜色、回合、request_id、超时策略、落子校验、Godot row/col 转换和 Match Server 集成。

MoveEngine 只接收自己视角下的棋盘，并返回坐标。

## 输入

服务端向 MoveEngine stdin 写入一行 JSON：

```json
{
  "board": [
    [0, 0, 0],
    [0, 1, 0],
    [0, -1, 0]
  ]
}
```

棋盘数值从 MoveEngine 视角解释：

```text
0  = 空位
1  = 当前引擎自己一方
-1 = 对手一方
```

Local Inference Service 会在发送请求前完成平台棋盘到引擎视角的转换。

## 输出

MoveEngine 向 stdout 写入一行 JSON。最小响应是：

```json
{
  "x": 7,
  "y": 8
}
```

解析器也接受：

```json
{
  "move": {"x": 7, "y": 8},
  "debug": {"thinking_ms": 25}
}
```

也接受：

```json
{
  "row": 8,
  "col": 7
}
```

坐标会统一归一化为：

```text
x = 列
y = 行
```

Godot 侧可以继续使用：

```text
row = y
col = x
```

## debug 字段

如果输出包含 `debug` 对象，本地推理服务会保留它，后续可用于展示或上传。若没有显式 `debug` 对象，额外顶层字段会被当作调试元数据处理。

## stdout 与 stderr

`stdout` 只能输出协议 JSON。调试日志必须写到 `stderr`。

如果日志混入 stdout，本地推理服务会把日志当作 JSON 解析，导致落子失败。
