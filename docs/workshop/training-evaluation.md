# 训练与评估

## 训练对手

项目可以先使用多个规则 Bot 作为训练对手，而不是一开始就做纯 self-play。

| Bot 类型 | 行为特点 | 训练作用 |
|---|---|---|
| Random Bot | 随机合法落子 | 提供基础训练环境 |
| Attack Bot | 优先形成己方棋形 | 训练防守能力 |
| Defense Bot | 优先阻挡对方威胁 | 训练进攻能力 |
| Pattern Bot | 根据棋形评分选点 | 提供更强规则对手 |
| Mixed Bot | 多种规则随机混合 | 提高泛化能力 |

推荐训练路线：

```text
简单 Bot -> 攻防 Bot -> Pattern Bot -> 混合对手
```

## 网络结构

典型结构是共享主干 + Actor-Critic 双头：

```text
棋盘状态输入
     ↓
共享主干网络
     ↓
 ┌───────────────┬───────────────┐
 │ Policy Head   │ Value Head    │
 │ 输出落子概率  │ 输出局面价值  │
 └───────────────┴───────────────┘
```

Policy Head 输出 225 个动作 logits。Value Head 输出当前局面的状态价值。

## 训练记录

PPO 训练时需要记录：

| 数据 | 作用 |
|---|---|
| state | 当前棋盘局面 |
| action | Agent 实际选择的动作 |
| reward | 落子后得到的奖励 |
| log_prob | 旧策略选择该动作的 log 概率 |
| value | Critic 对当前状态的估计 |
| done | 当前 episode 是否结束 |

这些数据用于计算 return、advantage 和 PPO loss。

## 评估指标

强化学习不能只看 loss，更要看实际对战表现。

| 指标 | 含义 |
|---|---|
| Win Rate | 对不同 Bot 的胜率 |
| Average Reward | 平均每局回报 |
| Invalid Action Rate | 非法动作比例 |
| Average Game Length | 平均对局长度 |
| Offensive Pattern Count | 主动形成威胁次数 |
| Defensive Success Rate | 成功阻挡威胁次数 |

## 常见问题

| 问题 | 表现 | 处理方向 |
|---|---|---|
| 奖励设计不合理 | AI 只刷棋形分 | 增大终局奖励，做 reward ablation |
| 非法动作频繁 | 模型下已有棋子 | 检查训练和推理 mask 是否一致 |
| 对单一 Bot 过拟合 | 只能赢某种 Bot | 使用多个规则 Bot 或混合对手 |
| Value 预测不准 | loss 波动大 | 标准化 advantage，调整学习率 |
| 胜率不稳定 | 训练后反而变弱 | 降低学习率，调小 clip range |

## 后续改进

- 更强规则 Bot。
- 混合对手池。
- Curriculum Learning。
- Supervised Warm Start。
- Self-Play。
- MCTS。
- Reward Ablation。
