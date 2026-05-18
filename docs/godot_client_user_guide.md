# Godot Client 使用指南

本文说明 Godot 客户端的线下模式、线上模式、模型选择和本地推理服务的基本使用流程。

## 启动前准备

Godot 客户端本身只负责界面、棋盘显示、房间流程和把落子请求转发给本地或远程服务。

线下的人类对战 Bot、模型对战 Bot、线上模型对战，都可能需要本地推理服务。推荐先在项目根目录启动：

```powershell
python -m local_inference_service.main
```

如果使用线下 Bot 列表，也可以启动 Bot bridge：

```powershell
cd gomoku_ai
python -m bots.local_http_api
```

线上模式还需要 Match Server 正在运行：

```powershell
python -m match_server.main
```

客户端默认连接地址在 `Global.match_server_url` 中配置。

## 主菜单

进入客户端后，主菜单有两个主要入口：

- `OFFLINE PLAY`：线下模式
- `ONLINE MATCH`：线上联机模式

`Simple pieces` 开关会影响棋子显示方式。开启后使用简单黑白半球；关闭后使用项目里的 3D 模型棋子。

## 线下模式

点击顺序：

1. 在主菜单点击 `OFFLINE PLAY`
2. 进入 `SELECT OFFLINE MODE`
3. 选择一种模式
4. 点击 `START`
5. 在配置页选择需要的 Bot 或模型文件
6. 点击 `START` 进入棋盘

### Human vs Model

黑方是人类，白方是本地模型。

你需要在配置页选择一个模型或 MoveEngine 文件。支持：

- Python 脚本：`.py`
- 可执行程序：`.exe`、`.bat`、`.cmd`
- gomoku_ai checkpoint：`.pt`

### Model vs BOT

黑方是本地模型，白方是 Bot。

你需要选择黑方模型文件，也可以选择白方 Bot 类型。这个模式通常用于观察模型和规则 Bot 的对局。

### Human vs Bot

黑方是人类，白方是 Bot。

只需要选择 Bot 类型，不需要选择模型文件。

## 线上模式

点击顺序：

1. 在主菜单点击 `ONLINE MATCH`
2. 进入 `ONLINE MATCH`
3. 一方点击 `CREATE ROOM`
4. 创建者输入昵称，点击 `START`
5. 创建者把右上角房间号告诉另一方
6. 另一方点击 `JOIN ROOM`
7. 加入者输入昵称和房间号，点击 `JOIN`
8. 双方进入同一个房间等待页
9. 创建者点击 `START`
10. 双方进入模型选择页
11. 双方各自选择或填写自己的本地模型，点击 `START` 提交 ready
12. 双方都 ready 后，创建者再次点击 `START`
13. 进入棋盘，对局开始
14. 对局结束后进入结果页，点击 `HOME` 返回主页

### CREATE ROOM

`CREATE ROOM` 是普通创建房间流程。创建者会作为房间中的一名玩家。

创建成功后，界面右上角显示房间号，例如：

```text
ROOM 123456
```

对方加入前，`START` 不会真正进入游戏。对方加入后，创建者点击 `START` 只是进入模型选择阶段，不会立即开始棋局。

### JOIN ROOM

加入者需要输入：

- 昵称
- 6 位房间号

加入成功后，客户端会切换到和创建者一样的房间等待页，并同步双方昵称、黑白位置和头像状态。

### HOST GAME

`HOST GAME` 用于创建旁观/主持房间。当前主要联机对局流程推荐使用 `CREATE ROOM` 和 `JOIN ROOM`。

## 在线模型选择

双方进入 `SELECT MODEL` 页面后，每一方只选择自己的本地模型。

可以直接使用模型名，例如：

```text
trained
```

也可以点击：

```text
SELECT PY / EXE / PT
```

选择本地 MoveEngine 文件。支持：

- `.py`
- `.exe`
- `.bat`
- `.cmd`
- `.pt`

点击 `START` 后，当前玩家状态变成 ready。双方都 ready 后，只有创建房间的一方可以再次点击 `START` 进入棋局。

## 本地推理服务的作用

线上模式中，Match Server 只负责房间、棋盘状态、轮到谁下、落子是否合法、胜负判断和消息转发。

真正“怎么想、下哪里”的逻辑在玩家自己的电脑上完成。Godot 客户端收到服务器的“轮到你”消息后，会把当前棋盘发给本地推理服务：

```text
Godot Client -> Local Inference Service -> MoveEngine
```

本地推理服务再调用你选择的 Python、exe 或 checkpoint，得到一个落子坐标，然后 Godot 把这个坐标发回 Match Server。

这样设计的意义是：

- 每个玩家可以使用自己的本地模型
- 模型文件不需要上传到服务器
- 服务器只做裁判，不承担推理计算
- 双方通过服务器同步棋盘，保证对局状态一致

## MoveEngine 输入输出约定

本地推理服务会给 MoveEngine 发送一行 JSON：

```json
{"board":[[0,0,0],[0,1,0],[0,-1,0]]}
```

棋盘数值含义：

```text
0  = 空位
1  = 当前引擎自己一方
-1 = 对手一方
```

MoveEngine 需要输出一行 JSON。最小格式是：

```json
{"x":7,"y":8}
```

其中：

```text
x = 列
y = 行
```

也可以输出：

```json
{"row":8,"col":7}
```

调试日志不要写到 stdout，应该写到 stderr。stdout 应只输出协议 JSON。

## 调试用随机引擎

项目里提供了两个随机落子的调试引擎：

```text
godot_client/Scripts/debug/random_move_engine.py
godot_client/Scripts/debug/random_move_engine.exe
```

它们会随机选择一个空位，不会下在已有棋子的位置上。在线模型选择页可以直接选择它们测试流程。

## 对局结束

线上对局结束后，客户端会进入结果页。

结果页显示：

- 哪方赢了
- 黑方昵称和模型
- 白方昵称和模型
- 本机玩家执黑还是执白
- 本机玩家赢了、输了或平局

点击 `HOME` 返回主菜单。

## 常见问题

### 创建房间后没有房间号

先看底部状态信息。如果一直显示连接失败，通常是 Match Server 或网络地址不可用。可以先测试：

```powershell
python tools\online_match_smoke.py --ws-url ws://frp-cup.com:57190/ws --timeout 8
```

### 加入后马上开始游戏

这通常表示你连接的 Match Server 还是旧版本。重启服务器：

```powershell
python -m match_server.main
```

### 进入棋盘后没有落子

确认本地推理服务已启动，并且模型选择页中选择的文件可以被本地推理服务执行。

### 两个 Godot 客户端能否在一台电脑上运行

可以。两个客户端会各自连接 Match Server，但默认共用本机的 Local Inference Service。多个客户端同时请求同一个模型时，本地推理服务会串行处理同一个 MoveEngine 的请求。
