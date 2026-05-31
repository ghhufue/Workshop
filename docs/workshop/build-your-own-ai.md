# 现场实现五子棋 AI

本环节的目标不是训练一个神经网络，而是在现场实现一个能参与对弈的五子棋 AI。你的程序可以很简单：随机落子、优先下中心、阻挡对手、寻找连五，都可以。系统不关心你内部怎样决策，只要求你的程序能接收棋盘并输出一个合法落子。

## 参考思路

实现现场 AI 有两条路线：一种是使用已有的 V1 到 V5 训练框架训练模型，再把 checkpoint 接入平台；另一种是不训练神经网络，直接写纯逻辑落子程序。

### 路线一：使用 V1 到 V5 训练框架

V1 到 V5 都可以作为学生自己的训练起点：

| 阶段 | 训练脚本 | 适合修改的方向 |
|---|---|---|
| V1 | `python gomoku_ai/scripts/train_v1_terminal.py` | 只使用终局输赢奖励，适合观察最基础 PPO 是否能学到东西 |
| V2 | `python gomoku_ai/scripts/train_v2_masked.py` | 加入 action mask，避免模型选择已落子位置 |
| V3 | `python gomoku_ai/scripts/train_v3_shaped.py` | 加入棋形奖励，鼓励连二、连三、连四等局面 |
| V4 | `python gomoku_ai/scripts/train_v4_anneal.py` | 对棋形奖励做退火，让目标逐步回到赢棋本身 |
| V5 | `python gomoku_ai/scripts/train_v5_mixed.py` | 使用混合对手池，降低模型只会打固定对手的风险 |

常用启动示例：

```powershell
python gomoku_ai/scripts/train_v5_mixed.py `
  --updates 300 `
  --n-envs 16 `
  --n-steps 128 `
  --batch-size 512 `
  --epochs 4 `
  --lr 3e-4 `
  --model-preset base
```

训练完成后，模型通常保存在：

```text
gomoku_ai/runs/<stage>/<timestamp>/final_model.pt
```

在 Godot 里可以选择这个 checkpoint，让它作为你的 AI 参与对局。

### 命令行可修改的训练参数

这些参数不需要改代码，运行训练脚本时直接传入：

| 参数 | 默认值 | 作用 |
|---|---:|---|
| `--device` | `auto` | 训练设备，`auto` 会优先使用 CUDA，否则用 CPU |
| `--seed` | `2026` | 随机种子，影响初始化、环境和对局采样 |
| `--run-dir` | 自动生成 | 指定训练输出目录 |
| `--n-envs` | `8` | 并行环境数量，越大采样越快但更占资源 |
| `--n-steps` | `128` | 每个环境每轮采样步数 |
| `--updates` | `100` | PPO 更新轮数，主要决定训练时长 |
| `--batch-size` | `256` | 每次 PPO 小批量更新的数据量 |
| `--epochs` | `4` | 每轮采样数据重复训练的次数 |
| `--lr` | `3e-4` | 学习率 |
| `--model-preset` | `small` | 模型规模，可选 `small`、`base`、`large` |
| `--save-every` | `25` | 每隔多少个 update 保存一次中间 checkpoint，设为 `0` 可关闭 |
| `--opponent-checkpoint` | 无 | 加入历史模型作为对手，可重复传入多个 |
| `--checkpoint-weight` | 阶段默认值 | 历史 checkpoint 对手被采样到的权重 |
| `--no-progress` | 关闭 | 不显示进度条，适合脚本化运行 |

### 训练阶段配置项

如果要改每个阶段本身的训练逻辑，修改 `gomoku_ai/scripts/train_v*.py` 里的 `StageConfig`：

| 配置项 | 作用 |
|---|---|
| `stage_name` | 输出目录中的阶段名 |
| `description` | 命令行帮助描述 |
| `reward_mode` | 奖励模式，`terminal` 表示只看输赢，`shaped` 表示加入棋形奖励 |
| `shape_alpha` | 棋形奖励权重，越大越依赖人工棋形分 |
| `use_action_mask` | 是否屏蔽非法落子 |
| `bot_pool` | 训练对手池，可用 `random`、`classic_rule`、`reward_driven_medium`、`reward_driven_hard` |
| `bot_weights` | 对手采样权重，长度要和 `bot_pool` 一致 |
| `checkpoint_paths` | 默认加入的历史 checkpoint 对手路径 |
| `checkpoint_weight` | 历史 checkpoint 对手的采样权重 |
| `alpha_schedule` | 棋形奖励退火配置 |

`alpha_schedule` 可继续修改：

| 配置项 | 作用 |
|---|---|
| `start` | 初始棋形奖励权重 |
| `end` | 训练后期棋形奖励权重 |
| `warmup_fraction` | 前多少比例的训练保持 `start` |
| `decay_fraction` | 用多少比例的训练从 `start` 下降到 `end` |

### 棋形 Reward 配置

V3、V4、V5 使用 `reward_mode = "shaped"`，总奖励由终局奖励和棋形 reward 组成：

```text
total_reward = terminal_reward + shape_alpha * raw_shape_reward
```

其中 `shape_alpha` 在 `StageConfig` 或 `AlphaSchedule` 里控制权重，`raw_shape_reward` 的具体棋形分数来自 `gomoku_ai/configs/reward.toml`。

普通棋形分：

| 配置项 | 默认值 | 含义 |
|---|---:|---|
| `live_one` | `0.5` | 活一 |
| `sleep_one` | `0.2` | 眠一 |
| `dead_one` | `0.0` | 死一 |
| `live_two` | `5.0` | 活二 |
| `live_two_gap1` | `2.5` | 带一个空点的活二 |
| `sleep_two` | `2.0` | 眠二 |
| `sleep_two_gap1` | `1.0` | 带一个空点的眠二 |
| `dead_two` | `0.0` | 死二 |
| `dead_two_gap1` | `0.0` | 带一个空点的死二 |
| `live_three` | `20.0` | 活三 |
| `live_three_gap1` | `14.0` | 带一个空点的活三 |
| `live_three_gap2` | `6.0` | 带两个空点的活三 |
| `sleep_three` | `8.0` | 眠三 |
| `sleep_three_gap1` | `5.6` | 带一个空点的眠三 |
| `sleep_three_gap2` | `2.4` | 带两个空点的眠三 |
| `dead_three` | `0.0` | 死三 |
| `dead_three_gap1` | `0.0` | 带一个空点的死三 |
| `dead_three_gap2` | `0.0` | 带两个空点的死三 |
| `live_four` | `120.0` | 活四 |
| `live_four_gap1` | `50.0` | 带一个空点的活四 |
| `sleep_four` | `50.0` | 眠四 |
| `sleep_four_gap1` | `25.0` | 带一个空点的眠四 |
| `dead_four` | `0.0` | 死四 |
| `dead_four_gap1` | `0.0` | 带一个空点的死四 |
| `five` | `1000.0` | 五连 |

特殊奖励和惩罚：

| 配置项 | 默认值 | 含义 |
|---|---:|---|
| `step_penalty` | `-1.0` | 每步基础惩罚，鼓励更快形成有效局面 |
| `double_live_three_bonus` | `40.0` | 双活三奖励 |
| `block_winning_bonus` | `200.0` | 阻挡对手直接成五奖励 |
| `block_live_four_bonus` | `120.0` | 阻挡对手活四奖励 |
| `block_live_three_bonus` | `40.0` | 阻挡对手活三奖励 |
| `unresolved_winning_threat_penalty` | `300.0` | 未处理对手成五威胁惩罚 |
| `unresolved_four_threat_penalty` | `300.0` | 未处理对手四连威胁惩罚 |
| `unresolved_live_three_fatal_penalty` | `200.0` | 未处理危险活三惩罚 |
| `missed_immediate_win_penalty` | `150.0` | 有一步成五却没有下的惩罚 |

学生可以直接修改这些数值，观察模型会更偏进攻、防守、快速结束，还是更容易刷局部棋形分。修改棋形 reward 后，建议同时观察 `history.json` 和 TensorBoard 里的 `reward/terminal_reward`、`reward/shape_reward`、`reward/total_reward`，不要只看总 reward。

### PPO 超参数

大部分 PPO 超参数在 `gomoku_ai/gomoku_ai/ppo.py` 的 `PPOConfig` 中。当前训练脚本已经暴露了 `n_envs`、`n_steps`、`total_updates`、`batch_size`、`epochs`、`learning_rate`、`device`、`show_progress`；如果要继续实验，可以在 `train_common.py` 构造 `PPOConfig` 时手动加入这些项：

| 参数 | 默认值 | 作用 |
|---|---:|---|
| `gamma` | `0.99` | 折扣因子，越接近 1 越重视长期收益 |
| `gae_lambda` | `0.95` | GAE 优势估计平滑系数 |
| `clip_range` | `0.2` | PPO policy clip 范围 |
| `value_coef` | `0.5` | value loss 权重 |
| `entropy_coef` | `0.03` | 熵奖励权重，越大越鼓励探索 |
| `max_grad_norm` | `0.5` | 梯度裁剪上限 |

### 环境和模型配置

环境配置在 `gomoku_ai/gomoku_ai/env.py` 的 `EnvConfig`：

| 配置项 | 默认值 | 作用 |
|---|---:|---|
| `reward_mode` | `terminal` | 奖励模式 |
| `terminal_reward` | `1.0` | 胜负终局奖励幅度 |
| `shape_alpha` | `0.0` | 棋形奖励权重 |
| `use_action_mask` | `True` | 是否启用 action mask |
| `candidate_radius` | `2` | 有棋子后，候选落子距离已有棋子的搜索半径 |
| `opening_radius` | `1` | 开局附近候选点半径 |

模型预设在 `gomoku_ai/gomoku_ai/model/presets.toml`：

| 配置项 | 作用 |
|---|---|
| `channels` | 主干卷积通道数 |
| `blocks` | 残差块数量 |
| `policy_channels` | policy head 通道数 |
| `value_channels` | value head 通道数 |
| `value_hidden_dim` | value head 隐藏层维度 |

当前预设值：

| 预设 | `channels` | `blocks` | `policy_channels` | `value_channels` | `value_hidden_dim` |
|---|---:|---:|---:|---:|---:|
| `small` | 48 | 3 | 2 | 1 | 96 |
| `base` | 64 | 4 | 2 | 1 | 128 |
| `large` | 128 | 10 | 4 | 2 | 256 |

对手配置在 `gomoku_ai/configs/bots.toml`，可改 `candidate_radius`、`top_k` 等对手行为参数；也可以调整 `difficulty`、`aliases`、`capabilities` 这类展示信息。

### 路线二：纯逻辑 AI

也可以完全不训练模型，直接实现规则或搜索：

1. 先检查自己是否能一步连五，能就直接下。
2. 再检查对手是否能一步连五，必须先挡。
3. 对所有候选空位做棋形打分，例如活二、冲三、活三、冲四、活四。
4. 只搜索已有棋子附近的候选点，避免遍历全部 225 个格子。
5. 在棋形打分基础上加入 Minimax 或 Alpha-Beta 剪枝，模拟自己和对手接下来几步。

纯逻辑 AI 的优势是现场可解释、调试快、对硬件要求低；缺点是强度取决于棋形评估函数和搜索深度。无论使用训练模型还是 Alpha-Beta 搜索，对外协议都一样：读入 `{"board": ...}`，输出 `{"x": ..., "y": ...}`。

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
