# 五子棋建模与训练阶段

本章把前两章的强化学习和 PPO 放回五子棋项目中，按 V0 到 V4 的顺序讲：先把五子棋包装成环境，再逐步加入终局奖励、action mask、棋形奖励和奖励退火。

核心实现：

```text
gomoku_ai/env.py
scripts/demo_v0_env.py
scripts/train_v1_terminal.py
scripts/train_v2_masked.py
scripts/train_v3_shaped.py
scripts/train_v4_anneal.py
```

## V0：先把五子棋变成环境

训练模型之前，必须先定义环境。`GomokuEnv` 需要支持：

```text
reset() -> observation, action_mask
step(action) -> observation, action_mask, reward, done, info
```

五子棋的基本定义：

| 项 | 当前实现 |
|---|---|
| 棋盘 | `15 x 15` |
| 连子规则 | 五连获胜 |
| 棋盘值 | 空位 `0`，黑棋 `1`，白棋 `-1` |
| 动作空间 | `0..224` |
| 坐标转换 | `row = action // 15`，`col = action % 15` |

当前 observation 是：

```text
3 x 15 x 15
```

| 通道 | 含义 |
|---|---|
| `obs[0]` | 当前模型方棋子 |
| `obs[1]` | 对手棋子 |
| `obs[2]` | 空位 |

这里用“我方/对手/空位”，而不是“黑棋/白棋/空位”。这样模型无论执黑还是执白，输入语义都是一致的。

### 思考问题

- 为什么模型看到“我方/对手”通常比看到“黑棋/白棋”更容易学？
- 如果 observation 里不放空位通道，模型还能学吗？
- 五子棋规则简单，为什么仍然需要认真设计环境接口？

## V1：只使用终局奖励

V1 脚本：

```powershell
python gomoku_ai/scripts/train_v1_terminal.py
```

V1 是最朴素的训练版本：

| 配置 | 值 |
|---|---|
| reward mode | `terminal` |
| action mask | 关闭 |
| opponent | `random` |

奖励：

```text
赢棋：+1
输棋：-1
平局：0
非法落子：-1
中间步骤：0
```

这一版的好处是目标非常纯粹：模型只为赢棋服务。问题是奖励非常稀疏，一局棋中大多数步骤 reward 都是 0。

稀疏奖励带来的困难：

- 模型很晚才知道结果。
- 很难判断中间某一步对最终胜负的贡献。
- 早期策略接近随机，对局结果噪声很大。
- 无 mask 时，模型还可能把动作浪费在非法落子上。

### 思考问题

- 只在终局给奖励，模型为什么仍然理论上能学？
- 为什么这种学习会很慢？
- 如果模型输了，是不是说明每一步都应该被降低概率？
- 非法落子应该交给模型自己学，还是由环境直接屏蔽？

## V2：加入 Action Mask

V2 脚本：

```powershell
python gomoku_ai/scripts/train_v2_masked.py
```

V2 仍然使用终局奖励，但打开 action mask：

| 配置 | 值 |
|---|---|
| reward mode | `terminal` |
| action mask | 开启 |
| opponent | `random` |

当前 action mask 不只是屏蔽已有棋子，还会缩小候选范围：

```text
无棋子时：只允许中心点
只有一颗棋子时：允许已有棋子周围 opening_radius = 1
之后：允许已有棋子周围 candidate_radius = 2
如果候选为空：退回所有空位
```

Mask 的意义不是“作弊”，而是把规则和搜索空间约束交给环境。神经网络应该学习策略，不应该花大量样本学习“已有棋子的地方不能下”。

### 思考问题

- Action mask 改变了学习问题吗？它是在减少动作空间，还是改变奖励？
- 如果不加 mask，PPO 会把多少样本浪费在无意义动作上？
- 候选范围只取已有棋子附近，会不会漏掉远处的好棋？
- 规则约束应该写进环境，还是让模型自己从失败中学？

## V3：加入棋形奖励

V3 脚本：

```powershell
python gomoku_ai/scripts/train_v3_shaped.py
```

V3 开始使用 C++ 后端提供棋形奖励：

| 配置 | 值 |
|---|---|
| reward mode | `shaped` |
| shape alpha | `0.05` |
| action mask | 开启 |
| opponent | `classic_rule` |

总奖励：

$$
\text{total\_reward} = \text{terminal\_reward} + \text{shape\_alpha} \cdot \text{shape\_reward}
$$

`shape_reward` 来自 `configs/reward.toml`，包括：

- 活一、活二、活三、活四、五连。
- 带 gap 的棋形。
- 阻挡对手成五、活四、活三。
- 漏防关键威胁惩罚。
- 每步惩罚。

人工棋形奖励解决的是稀疏奖励问题：模型不必等到整局结束才得到反馈，每一步都可以获得一些关于局面质量的信号。

但这也引入新问题：人工奖励不等于真实目标。如果权重过大，模型可能学会“刷棋形分”，而不是学会赢棋。

### 思考问题

- 人工奖励为什么能帮助探索？
- 如果棋形奖励和最终胜负冲突，模型会优化哪一个？
- 一个能刷高 `shape_reward` 的模型，是否一定胜率更高？
- 奖励设计是在教模型下棋，还是在改变模型真正追求的目标？

## V4：棋形奖励退火

V4 脚本：

```powershell
python gomoku_ai/scripts/train_v4_anneal.py
```

V4 的重点是降低模型对人工奖励的依赖：

| 配置 | 值 |
|---|---|
| reward mode | `shaped` |
| shape alpha | `0.20 -> 0.02` |
| action mask | 开启 |
| opponent | `classic_rule` |

退火规则由 `AlphaSchedule` 控制：

```text
前 30% 更新：保持 start
中间 40% 更新：从 start 线性下降到 end
后 30% 更新：保持 end
```

直觉是：

```text
早期：人工棋形奖励帮助模型探索
中期：逐渐减少人工引导
后期：让模型更接近优化真实胜负目标
```

这一步引出一个强化学习工程里很常见的问题：辅助目标可以帮助训练，但不能长期压过真实目标。

### 思考问题

- 为什么不一直保留很高的棋形奖励？
- 如果退火太快，模型会遇到什么问题？
- 如果退火太慢，模型又会学偏到哪里？
- 什么时候应该相信人工先验，什么时候应该让胜负结果说话？

## 阶段小结

V0 到 V4 的主线是：

```text
先定义环境
再用终局胜负训练
再用 mask 减少无效探索
再用棋形奖励缓解稀疏反馈
最后降低人工奖励权重
```

这几步对应的是强化学习项目最常见的几个问题：环境建模、稀疏奖励、动作约束、奖励塑形和辅助目标偏差。
