# PPO 算法

本章解释项目使用的 PPO。重点不是推公式，而是回答一个问题：模型已经通过对局收集到了很多 `state/action/reward`，为什么不能直接根据 reward 正负更新参数？

相关代码：

```text
gomoku_ai/ppo.py
gomoku_ai/model/network.py
```

## 从策略梯度开始

最直觉的想法是：

```text
赢了：提高这局走过的动作概率
输了：降低这局走过的动作概率
```

这个想法方向上没错，但直接这样做会很粗糙。原因是：

- 一局赢了，不代表每一步都好。
- 一局输了，不代表每一步都坏。
- 有些动作只是刚好跟着强局面获胜。
- 有些动作虽然当下 reward 为 0，但对后续胜负很关键。

因此 PPO 不直接看单步 reward 的正负，而是看这个动作相对预期来说有没有更好。

## 为什么需要 Value

`Value` 是 Critic 对当前状态的长期回报估计：

$$
V(s) = \text{从状态 } s \text{ 开始，未来大概能拿到多少回报}
$$

如果当前局面本来就很有利，那么赢棋不一定说明某一步特别优秀。如果当前局面很差，但某一步让局面明显改善，即使最后还是输了，这一步也可能值得提高概率。

所以训练时需要一个基准线：

```text
实际结果比预期更好 -> 鼓励这个动作
实际结果比预期更差 -> 抑制这个动作
```

这个“预期”就是 Value。

## Advantage 是什么

Advantage 衡量某个动作比预期好多少：

$$
\text{Advantage} = \text{Return} - \text{Value}
$$

| Advantage | 含义 | 更新方向 |
|---|---|---|
| 大于 0 | 结果比 Critic 预期好 | 提高动作概率 |
| 小于 0 | 结果比 Critic 预期差 | 降低动作概率 |
| 接近 0 | 和预期差不多 | 不做大幅更新 |

Advantage 的作用不是单纯给训练日志多一个指标，而是直接决定策略更新：

- **方向**：advantage 为正时，提高这个动作的概率；为负时，降低这个动作的概率。
- **强度**：advantage 绝对值越大，说明这个动作越明显地好于或差于预期，更新力度也越大。
- **归因**：它把“局面本来就好”与“这个动作真的有贡献”分开，避免把强局面里的普通动作也全部当成好动作。

因此，Policy Head 真正学习的不是“reward 是正还是负”，而是“在这个状态下，刚才这个动作是否比 Critic 的预期更好”。这回答了前面的问题：不能只根据 reward 正负更新参数，因为 reward 不知道“这个状态本来有多好”，也不知道“这个动作是否超出预期”。

当前实现使用 GAE 计算 advantage：

$$
\delta_t = r_t + \gamma V_{t+1} - V_t
$$

$$
A_t = \delta_t + \gamma \lambda A_{t+1}
$$

训练前还会标准化 advantage，减少不同 rollout 之间尺度差异带来的波动。

## Actor-Critic 网络

本项目使用一个共享卷积主干和两个输出头：

```text
3 x 15 x 15 observation
        ↓
Conv + Residual Blocks
        ↓
 ┌────────────────────┬────────────────────┐
 │ Policy Head        │ Value Head         │
 │ 输出 225 个 logits │ 输出当前局面 value │
 └────────────────────┴────────────────────┘
```

| 部分 | 作用 |
|---|---|
| Actor / Policy Head | 决定下在哪里 |
| Critic / Value Head | 估计当前局面长期价值 |

模型预设：

| Preset | channels | blocks | 适用场景 |
|---|---:|---:|---|
| `small` | 48 | 3 | 默认 workshop 训练 |
| `base` | 64 | 4 | 更稳定但更慢 |
| `large` | 128 | 10 | 更大模型实验 |

## Rollout：先采样再更新

PPO 不会每下一手就更新一次。它会先用当前策略收集一批数据：

```text
n_envs 个环境
每个环境走 n_steps 步
得到 n_envs * n_steps 条训练样本
```

每条样本记录：

```text
observation
action_mask
action
log_prob
reward
done
value
```

这些数据构成 rollout。采样结束后，PPO 会根据 `reward`、`done` 和 `value` 反向计算每一步的 `return` 与 `advantage`，再用同一批样本训练若干轮。

## 为什么需要 PPO Clip

如果策略每次更新太大，模型可能从“偶尔会赢”突然变成“完全乱下”。PPO 的核心是限制新旧策略差距。

它比较同一个动作在新旧策略下的概率：

$$
\text{ratio} = \exp(\text{new\_log\_prob} - \text{old\_log\_prob})
$$

然后把变化限制在一个范围内：

$$
\text{clipped\_ratio} = \operatorname{clamp}(\text{ratio}, 1 - \text{clip\_range}, 1 + \text{clip\_range})
$$

直觉上，PPO 允许策略变好，但不允许一次改得太猛。这里要注意：Clip 不判断动作好坏，动作好坏已经由 advantage 给出；Clip 只负责限制“根据这个 advantage 更新策略”时迈出的步子有多大。

## PPO Loss

当前实现的总损失：

$$
\text{loss} = \text{policy\_loss} + \text{value\_coef} \cdot \text{value\_loss} - \text{entropy\_coef} \cdot \text{entropy}
$$

| 项 | 作用 |
|---|---|
| `policy_loss` | 让高 advantage 动作概率上升 |
| `value_loss` | 让 Critic 更准确 |
| `entropy` | 保持探索，防止过早固定 |

其中 `policy_loss` 会把新旧策略概率比 `ratio` 和 advantage 相乘。这样一来，同样是提高某个动作概率，只有 advantage 明显为正的动作才会被强烈鼓励；advantage 接近 0 的动作即使出现过，也不会推动策略大幅改变。

默认关键参数：

| 参数 | 默认值 |
|---|---:|
| `gamma` | 0.99 |
| `gae_lambda` | 0.95 |
| `clip_range` | 0.2 |
| `entropy_coef` | 0.03 |
| `max_grad_norm` | 0.5 |

## 本章小结

PPO 的核心不是“赢了就全鼓励，输了就全惩罚”，而是：

```text
用 Value 估计预期
用 Advantage 给策略更新定方向和强度
用 Clip 控制更新幅度
用 Entropy 保留探索
```

## 思考问题

- 为什么一局赢了，也不能把这一局所有动作都当成好动作？
- 如果没有 Value，只根据 reward 更新，会在稀疏奖励任务里遇到什么问题？
- PPO 为什么要限制新旧策略差距？如果不限制会怎样？
- Entropy 越高越好吗？什么时候探索会变成噪声？
