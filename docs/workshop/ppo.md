# PPO 算法

PPO，全称 Proximal Policy Optimization，是一种常用的 Actor-Critic 强化学习算法。

## Value-Based、Policy-Based 与 Actor-Critic

| 类型 | 学习对象 | 代表算法 | 特点 |
|---|---|---|---|
| Value-Based | 动作价值 Q(s,a) | Q-Learning, DQN | 学习哪个动作更好 |
| Policy-Based | 策略 π(a\|s) | REINFORCE | 直接学习怎么选动作 |
| Actor-Critic | 策略 + 价值 | A2C, A3C, PPO | 同时学习决策和评估 |

PPO 属于 Actor-Critic 方法。

## Actor-Critic

Actor-Critic 的核心分工：

```text
Actor：负责选择动作
Critic：负责评估当前状态好坏
```

Critic 的价值估计可以降低策略梯度更新的方差，让 Actor 更新更稳定。

## Advantage

PPO 更新策略时通常看 Advantage：

```text
Advantage = 实际回报 - Critic 对当前状态的预期价值
```

| Advantage | 含义 | 更新方向 |
|---|---|---|
| 大于 0 | 动作比预期好 | 提高该动作概率 |
| 小于 0 | 动作比预期差 | 降低该动作概率 |
| 接近 0 | 和预期差不多 | 小幅更新 |

## PPO 的核心约束

Policy Gradient 的问题是更新幅度难控制。PPO 的核心思想是：

```text
允许策略进步
但限制一次更新过大
```

它通过新旧策略概率比衡量更新幅度，并用 clip 限制更新范围。

## PPO Loss

PPO 通常包含三类损失：

| Loss | 作用 |
|---|---|
| Policy Loss | 优化 Actor，让好动作概率上升 |
| Value Loss | 优化 Critic，让状态价值预测更准确 |
| Entropy Loss | 保持探索，避免策略过早固定 |

整体训练循环：

```text
初始化 Actor-Critic 网络
        ↓
使用当前策略与环境交互
        ↓
记录 state / action / reward / value / log_prob
        ↓
计算 return 和 advantage
        ↓
使用 PPO loss 更新网络
        ↓
重复采样、训练、评估
```
