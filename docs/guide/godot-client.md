# 演示界面说明

Godot 客户端是展示 AI 对局的图形界面。对于 Workshop 参与者来说，它的作用是帮助观察模型如何落子、如何与对手博弈，以及最终胜负结果如何呈现。

客户端实现细节不是本项目需要重点掌握的内容。

## 主菜单

主菜单有两个主要入口：

- `OFFLINE PLAY`：线下模式。
- `ONLINE MATCH`：线上联机模式。

`Simple pieces` 开关用于切换棋子显示方式。开启后使用简单黑白半球；关闭后使用项目内的 3D 棋子模型。

## 对局模式

- `Human vs Model`：人类观察或参与一方，模型作为另一方落子。
- `Model vs Bot`：模型和规则 Bot 对局，适合观察训练效果。
- `ONLINE MATCH`：两个模型通过房间进行联机对局。

## 模型选择

模型选择页可以选择本地脚本、可执行文件或 checkpoint。你可以把它理解成“选择本局由哪个 AI 下棋”。

支持的文件类型：

- `.py`：Python 落子脚本。
- `.exe`、`.bat`、`.cmd`：可执行落子程序。
- `.pt`：gomoku_ai checkpoint。

调试时可以使用项目内置随机引擎：

```text
godot_client/Scripts/debug/random_move_engine.py
godot_client/Scripts/debug/random_move_engine.exe
```

## 对局结束

线上对局结束后，客户端进入结果页，显示黑白双方、模型名称、胜负结果和本机玩家总结。点击 `HOME` 返回主菜单。
