# 五子棋 AI 强化学习 Workshop

一个围绕五子棋 AI 从零训练到对局博弈的教学项目。通过分阶段的训练实验，逐步理解强化学习如何在棋盘上生效；最后动手实现自己的落子 AI，并在图形界面中观看对局。

## 这个项目做什么

1. **把五子棋变成强化学习问题**——定义状态、动作、奖励和训练环境。
2. **用 PPO 逐步训练落子策略**——从最朴素的终局奖励开始，逐步加入 action mask、棋形奖励、奖励退火和混合对手。
3. **评估模型是否真的变强**——通过胜率、非法动作、熵值等指标观察训练效果。
4. **在图形界面里看 AI 对局**——用 Godot 客户端观看模型与 Bot、模型与模型的对弈。
5. **自己动手写一个 AI**——按统一协议实现落子程序，接入对局平台参与博弈。

## 你会经历什么

强化学习基础 → PPO 算法 → 五子棋环境建模 → 终局奖励与稀疏反馈 → Action Mask → 人工棋形奖励 → 奖励退火 → 混合对手与历史模型对手 → 评估与可视化

对应训练阶段：

| 阶段 | 要解决的问题 |
|---|---|
| V0 | 怎样把五子棋变成强化学习环境 |
| V1 | 只靠输赢奖励能不能学 |
| V2 | 为什么需要 action mask |
| V3 | 人工棋形奖励怎样缓解稀疏奖励 |
| V4 | 为什么人工奖励不能一直很强 |
| V5 | 为什么不能只和一种 Bot 训练 |
| V6 | 历史 checkpoint 对手有什么作用 |

## 现场实现五子棋 AI

训练阶段之后，现场对弈环节会实现一个能接入平台的五子棋 AI。这个环节不训练神经网络，而是按统一协议写一个落子程序，让它进入 Godot 对局平台参与博弈。

## 参考思路

- 可以直接使用 V1 到 V5 的训练脚本训练自己的模型，再把训练出的 checkpoint 接入对局平台。
- 也可以完全不训练模型，直接写纯逻辑 AI，例如棋形打分、规则搜索、Minimax 或 Alpha-Beta 剪枝搜索。
- 训练时可修改训练轮数、并行环境数、学习率、batch size、模型规模、对手池、奖励模式、棋形 reward、action mask、历史 checkpoint 对手等配置。

详细说明见 [docs/workshop/build-your-own-ai.md](docs/workshop/build-your-own-ai.md)。

## 快速开始

### 你需要什么

- Python 3.10+
- Git
- Godot 4.6（用于打开图形客户端观看对局）
- NVIDIA 显卡（可选，用于 GPU 训练）

### 安装

```powershell
# 克隆仓库（含子模块）
git clone --recurse-submodules https://github.com/ghhufue/Workshop.git
cd Workshop

# 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### 验证

```powershell
python tools\verify_environment.py
```

所有检查项显示 `[OK]` 即表示环境就绪。

### 打开图形客户端

用 Godot 导入 `godot_client/project.godot`，点击运行即可启动图形客户端。

详细安装指引请查看 [docs/guide/installation.md](docs/guide/installation.md)。

## 项目结构

| 目录 | 作用 |
|---|---|
| `gomoku_ai/` | 五子棋 AI 训练项目：环境、PPO、训练脚本、对手池、评估工具 |
| `godot_client/` | Godot 图形客户端：线下/线上对局展示 |
| `match_server/` | 对战服务器：房间管理、回合控制、胜负裁判 |
| `local_inference_service/` | 本地引擎托管：让自定义 AI 程序接入对局 |
| `docs/` | 完整项目文档（讲义、安装指南、协议附录） |
| `tools/` | 环境验证、冒烟测试等辅助工具 |

## 运行演示

演示联机对局前，需要先启动两个后台服务：

```powershell
# 终端 1：启动对战服务器
python -m match_server.main

# 终端 2：启动本地引擎服务
python -m local_inference_service.main
```

然后打开 Godot 客户端，选择 `ONLINE MATCH` 即可创建或加入房间开始对局。

线下模式（Human vs Bot / Model vs Bot）不需要启动 Match Server。

## 自己写一个 AI

训练模型不是参与博弈的唯一方式。你也可以直接写一个落子程序接入平台。核心协议非常简单：

1. 从 **stdin** 读一行 `{"board": [[...]]}`（15×15 棋盘，`1` 是你，`-1` 是对手）
2. 向 **stdout** 输出一行 `{"x": 7, "y": 7}`

最小可运行示例：

```python
import json, random, sys

for line in sys.stdin:
    board = json.loads(line)["board"]
    empty = [(x, y) for y in range(15) for x in range(15) if board[y][x] == 0]
    x, y = random.choice(empty)
    print(json.dumps({"x": x, "y": y}), flush=True)
```

保存为 `my_engine.py`，在 Godot 里选择这个文件就能让你的 AI 参与对局。

更多策略改进思路和接入细节，见 [docs/workshop/build-your-own-ai.md](docs/workshop/build-your-own-ai.md)。

## 文档导航

完整文档请查看 [`docs/`](docs/) 目录（可部署为静态网页）：

- **如何阅读与体验**：[docs/guide/quick-start.md](docs/guide/quick-start.md)
- **安装说明**：[docs/guide/installation.md](docs/guide/installation.md)
- **强化学习基础**：[docs/workshop/rl-intro.md](docs/workshop/rl-intro.md)
- **PPO 算法**：[docs/workshop/ppo.md](docs/workshop/ppo.md)
- **五子棋训练阶段**：[docs/workshop/gomoku-rl.md](docs/workshop/gomoku-rl.md)
- **训练后期与评估**：[docs/workshop/training-evaluation.md](docs/workshop/training-evaluation.md)
- **现场实现五子棋 AI**：[docs/workshop/build-your-own-ai.md](docs/workshop/build-your-own-ai.md)
- **演示界面说明**：[docs/guide/godot-client.md](docs/guide/godot-client.md)

## 可以跳过什么

如果你主要是来体验 Workshop 和阅读讲义的，以下内容可以跳过：

- Match Server 协议细节
- MoveEngine JSON Lines 协议细节
- Godot 客户端内部实现
- 本地推理服务内部流程

这些是供后续维护者或想深度接入自己模型的同学参考的附录内容。
