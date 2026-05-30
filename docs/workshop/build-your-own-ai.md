# 现场实现五子棋 AI

本环节的目标不是训练一个神经网络，而是在现场实现一个能参与对弈的五子棋 AI。你的程序可以很简单：随机落子、优先下中心、阻挡对手、寻找连五，都可以。系统不关心你内部怎样决策，只要求你的程序能接收棋盘并输出一个合法落子。

## 接入方式

对局时，Godot 客户端不会直接调用你的代码。调用链是：

```text
Godot Client
  -> Local Inference Service /bot_move
  -> 你的 MoveEngine 进程
```

你的 AI 是一个独立进程，称为 MoveEngine。它可以是：

| 类型 | 说明 |
|---|---|
| `.py` | Python 脚本，最适合现场实现 |
| `.exe` | C++、Rust、Go 等语言编译出的可执行文件 |
| `.bat` / `.cmd` | Windows 命令脚本 |

课堂现场推荐先写 Python 脚本，因为不需要额外编译。

## 必须实现什么

你的程序至少要实现三件事：

1. 从 `stdin` 持续读取一行 JSON。
2. 从 JSON 里取出 `board`，计算一个空位坐标。
3. 向 `stdout` 输出一行 JSON，包含本次落子的坐标。

注意：程序应该持续运行，不能只处理一步就退出。Local Inference Service 会复用同一个进程，每轮轮到你时再写入一行新的棋盘。

## 输入格式

服务会向你的程序写入一行 JSON：

```json
{"board":[[0,0,0],[0,1,0],[0,-1,0]]}
```

实际棋盘是 `15 x 15`。访问方式是：

```text
board[y][x]
```

坐标含义：

| 名称 | 含义 |
|---|---|
| `x` | 列，从左到右，范围 `0..14` |
| `y` | 行，从上到下，范围 `0..14` |

棋盘数值从你的 AI 视角解释：

| 值 | 含义 |
|---:|---|
| `0` | 空位 |
| `1` | 你的棋子 |
| `-1` | 对手棋子 |

Local Inference Service 已经根据当前执棋方做过视角转换。你的程序不需要判断自己是黑棋还是白棋，只需要把 `1` 当成自己，把 `-1` 当成对手。

## 输出格式

最小输出是一行 JSON：

```json
{"x":7,"y":7}
```

也可以输出 `row` / `col`：

```json
{"row":7,"col":7}
```

推荐使用 `x` / `y`，因为它和输入里的 `board[y][x]` 对应更直接。

如果想带调试信息，可以加 `debug`：

```json
{"x":7,"y":7,"debug":{"reason":"center first"}}
```

每次输出后必须刷新 stdout。Python 里可以这样写：

```python
print(json.dumps({"x": x, "y": y}), flush=True)
```

## 日志只能写 stderr

`stdout` 只能输出协议 JSON。不要在 stdout 里打印：

```text
thinking...
my score is 123
```

这些内容会被服务当成 JSON 解析，导致落子失败。

调试日志请写到 `stderr`：

```python
print("thinking...", file=sys.stderr)
```

## 最小可运行版本

新建一个文件，例如：

```text
my_engine.py
```

写入：

```python
import json
import random
import sys


def choose_move(board):
    center = len(board) // 2
    if board[center][center] == 0:
        return center, center

    empty = [
        (x, y)
        for y, row in enumerate(board)
        for x, value in enumerate(row)
        if value == 0
    ]
    if not empty:
        raise RuntimeError("no legal moves")
    return random.choice(empty)


for line in sys.stdin:
    request = json.loads(line)
    board = request["board"]
    x, y = choose_move(board)
    print(json.dumps({"x": x, "y": y}), flush=True)
```

这个版本的策略是：如果中心点空着就下中心，否则随机选择一个空位。它不强，但已经能合法对弈。

## 本地快速测试

可以先不用打开 Godot，只测试脚本能否读写协议：

```powershell
'{"board":[[0,0,0],[0,0,0],[0,0,0]]}' | python my_engine.py
```

应该输出类似：

```json
{"x": 1, "y": 1}
```

真实对局棋盘是 15 路，这个小棋盘只用于确认输入输出通路。

## 通过本地服务测试

先启动 Local Inference Service：

```powershell
python -m local_inference_service.main
```

然后在另一个终端向 `/bot_move` 发送请求：

```powershell
$body = @{
  board = @(
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
    @(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
  )
  current_player = 1
  engine_kind = "python_script"
  engine_path = "D:\path\to\my_engine.py"
} | ConvertTo-Json -Depth 20

Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/bot_move `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

如果成功，会返回：

```json
{
  "row": 7,
  "col": 7,
  "x": 7,
  "y": 7,
  "engine_name": "python_script:...",
  "debug": {}
}
```

`row` / `col` 是给 Godot 和平台使用的坐标，和 `y` / `x` 等价。

## 在 Godot 里选择你的 AI

启动 Local Inference Service 后，在 Godot 的模型选择界面选择你的 `.py` 文件。服务会按扩展名推断：

| 扩展名 | engine kind |
|---|---|
| `.py` | `python_script` |
| `.exe` / `.bat` / `.cmd` | `executable` |

选中后开始对局，Godot 每到你的回合都会通过本地服务请求你的脚本落子。

## 合法落子要求

Local Inference Service 会校验你的输出：

| 要求 | 说明 |
|---|---|
| 必须是 JSON 对象 | 不能输出普通文本 |
| 坐标必须是整数 | `7` 可以，`7.5` 不可以 |
| 坐标必须在棋盘内 | 15 路棋盘范围是 `0..14` |
| 目标位置必须为空 | 不能下到已有棋子的地方 |
| 必须在超时前输出 | 默认超时约 3 秒 |

如果输出非法，本地服务会返回错误，本局对弈就无法正常继续。

## 可以怎样改进策略

最小版本能跑通后，可以逐步加入策略：

1. 如果自己有一步成五，直接下。
2. 如果对手下一步能成五，先阻挡。
3. 优先选择已有棋子附近的空位。
4. 给每个候选点打分，例如连二、连三、连四得不同分数。
5. 加入一层或多层搜索，模拟自己和对手的下一步。

无论内部策略多复杂，对外协议都不变：读一行 `{"board": ...}`，输出一行 `{"x": ..., "y": ...}`。

## 常见错误

| 现象 | 原因 | 处理 |
|---|---|---|
| 服务提示 JSON 解析失败 | stdout 打印了日志 | 日志改写到 stderr |
| 服务提示 out of bounds | 坐标越界 | 检查 `0 <= x,y < len(board)` |
| 服务提示 occupied cell | 下到了非空位置 | 只从 `board[y][x] == 0` 的位置里选 |
| 脚本第一步能下，第二步失败 | 程序处理一行后退出 | 使用 `for line in sys.stdin` 持续处理 |
| 行列反了 | 混淆 `x/y` 和 `row/col` | 记住 `board[y][x]`，输出 `x=列`、`y=行` |
