# 训练后期与评估

本章接着 V0 到 V4，讲后期训练为什么要换对手、为什么要引入历史模型，以及如何判断模型是不是真的变强。

核心实现：

```text
scripts/train_v5_mixed.py
scripts/train_v6_selfplay.py
scripts/evaluate.py
tools/policy_viewer.py
gomoku_ai/opponents.py
```

## V5：混合对手训练

V5 脚本：

```powershell
python scripts/train_v5_mixed.py
```

配置：

| 项 | 值 |
|---|---|
| reward mode | `shaped` |
| shape alpha | `0.10 -> 0.02` |
| action mask | 开启 |
| opponent pool | `random` 0.4, `classic_rule` 0.4, `reward_driven_medium` 0.2 |

为什么需要混合对手？

如果模型长期只和 `random` 下，它可能只学会惩罚随机 bot 的低级错误。如果只和固定规则 bot 下，它可能过拟合这个 bot 的风格。

混合对手让训练分布更丰富：

| 对手 | 提供的训练信号 |
|---|---|
| `random` | 基础胜负经验，便于早期学习 |
| `classic_rule` | 快速规则棋形对抗 |
| `reward_driven_medium` | 更接近奖励函数评估的局部策略 |

当前实现会在每局开始时按权重抽取对手，并在这一整局保持不变。

### 思考问题

- 打赢 random bot 是否说明模型真的会下五子棋？
- 如果训练对手太弱，模型会缺少什么能力？
- 如果训练对手太强，早期训练又会遇到什么问题？
- 对手池权重应该固定，还是随训练进度变化？

## V6：加入历史模型对手

V6 脚本：

```powershell
python scripts/train_v6_selfplay.py --opponent-checkpoint runs/v5_mixed/<run>/final_model.pt
```

配置：

| 项 | 值 |
|---|---|
| reward mode | `shaped` |
| shape alpha | `0.05 -> 0.01` |
| action mask | 开启 |
| bot opponents | `classic_rule` 0.5, `reward_driven_medium` 0.3 |
| checkpoint opponents | 默认权重 0.2 |

这里的“selfplay”更准确地说是“历史 checkpoint 对手”。训练中的当前模型不会实时复制自己当对手，而是把过去保存的模型加入对手池。

这样做更稳定：

- 对手不会每一步都跟着当前模型剧烈变化。
- 可以保留旧模型的策略风格。
- 能减少只适应固定规则 bot 的问题。

### 思考问题

- 为什么完全实时的自我对弈可能不稳定？
- 历史 checkpoint 太弱时还有训练价值吗？
- 如果只和过去的自己下，会不会形成封闭的策略生态？
- checkpoint 对手应该怎样筛选和更新？

## 训练命令与输出

进入子模块后安装：

```powershell
cd gomoku_ai
python -m pip install -e .
```

最小 smoke run：

```powershell
python scripts/demo_v0_env.py
python scripts/train_v1_terminal.py --n-envs 1 --n-steps 4 --updates 1 --batch-size 4 --epochs 1 --no-progress
python scripts/evaluate.py --checkpoint runs/v1_terminal/<run>/final_model.pt --games 10 --bots random
```

常用训练参数：

| 参数 | 默认值 | 作用 |
|---|---:|---|
| `--device auto` | auto | 自动选择 CUDA 或 CPU |
| `--seed 2026` | 2026 | 随机种子 |
| `--n-envs 8` | 8 | 并行环境数量 |
| `--n-steps 128` | 128 | 每轮 rollout 步数 |
| `--updates 100` | 100 | PPO 更新轮数 |
| `--batch-size 256` | 256 | mini-batch 大小 |
| `--epochs 4` | 4 | 每批 rollout 优化轮数 |
| `--lr 3e-4` | 0.0003 | 学习率 |
| `--model-preset small` | small | 网络规模 |
| `--save-every 25` | 25 | checkpoint 保存间隔 |

训练输出：

```text
runs/<stage_name>/<timestamp>/
  training_config.json
  history.json
  checkpoints/checkpoint_update_XXXX.pt
  final_model.pt
```

## 为什么不能只看 Loss

监督学习里 loss 下降通常意味着模型更接近标签。强化学习不一样，PPO loss 更多反映“这批 rollout 上的更新过程”，不等于棋力。

训练日志里应同时看：

| 指标 | 含义 |
|---|---|
| `wins/losses/draws` | rollout 中结束对局的结果 |
| `ep_rew_mean` | 已结束 episode 的平均回报 |
| `terminal_reward` | 胜负奖励分量 |
| `shape_reward` | 棋形奖励分量 |
| `entropy` | 策略随机性 |
| `approx_kl` | 新旧策略差异 |
| `clip_fraction` | 被 PPO clip 限制的比例 |
| `explained_variance` | Critic 对 return 的解释能力 |

但最终仍要用独立评估看胜率。

### 思考问题

- 为什么 RL 中 loss 下降不一定代表策略变强？
- 如果 `shape_reward` 上升但胜率下降，应该相信哪个指标？
- 训练时的对手和评估时的对手应该完全一样吗？

## 评估模型

评估脚本：

```powershell
python scripts/evaluate.py `
  --checkpoint runs/v5_mixed/<run>/final_model.pt `
  --games 50 `
  --bots random classic_rule reward_driven_medium `
  --output runs/v5_mixed/<run>/eval.json
```

输出字段：

| 字段 | 含义 |
|---|---|
| `wins` | 胜局数 |
| `losses` | 负局数 |
| `draws` | 平局数 |
| `illegal_moves` | 非法落子次数 |
| `win_rate` | 胜率 |
| `avg_steps` | 平均每局模型行动步数 |
| `workshop_score` | 加权教学评分 |

当前 workshop score：

```text
random: 20
classic_rule: 40
reward_driven_medium: 40
```

这个分数不是正式棋力等级，只是用于比较不同阶段 checkpoint。

## 可视化观察

可以用 policy viewer 看模型实际在想什么：

```powershell
python tools/policy_viewer.py --checkpoint runs/v3_shaped/<run>/final_model.pt --bot classic_rule
```

它会显示策略概率热力图，并让你逐步查看模型和 Bot 的对局。

观察时可以问：

- 高概率是否集中在已有棋子附近。
- 模型是否能识别进攻点。
- 模型是否会防守对手的活三、活四。
- 模型是否被棋形奖励诱导到局部刷分。

## 总结问题

- 一个模型能赢 random，但输给 classic_rule，说明它缺什么？
- 人工棋形奖励、混合对手、历史 checkpoint，分别解决了什么问题？
- 如果只能保留一个评估指标，你会选 win rate、reward 还是 workshop score？
- 怎么设计实验，证明 V3 的 shaped reward 真的比 V2 有帮助？
