# 总体架构

> 本页是实现细节附录。普通 Workshop 参与者可以跳过。理解五子棋 AI 训练与评估，不依赖本页内容。

系统由三层核心组件组成：

```text
Godot Client / CLI Client
        |
        | WebSocket
        v
Match Server
        ^
        | WebSocket
        |
Local Inference Service
        |
        | stdin / stdout JSON Lines
        v
MoveEngine Process
```

## 核心思想

项目不要求所有 AI 使用同一种算法或模型结构，只统一“对局平台”和“落子能力”之间的边界。

平台负责：

- 棋盘状态。
- 回合顺序。
- 落子合法性。
- 胜负判断。
- 房间和 UI。

MoveEngine 负责：

- 接收当前棋盘。
- 返回下一步坐标。

这种设计只是为了方便演示和扩展。项目重点仍然是训练五子棋 AI，并观察它在对局中的表现。

## 数据流

轮到某个本地模型落子时：

```text
Match Server -> Godot Client -> Local Inference Service -> MoveEngine
MoveEngine -> Local Inference Service -> Godot Client -> Match Server
```

Match Server 会重新校验客户端提交的坐标，因此本地服务返回的结果不能直接污染权威棋盘。
