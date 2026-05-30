# 运行与排错

> 本页是维护者和助教用的附录。普通 Workshop 参与者不需要掌握这些命令。

## 文档网页如何提供给别人

参与者不需要安装文档工具链。把 `docs/` 目录作为静态站点发布后，别人只需要打开网页链接。

适合的发布方式包括：

- GitHub Pages。
- Nginx 或 Caddy 静态目录。
- 学校或活动平台提供的静态网页托管。

本仓库中的文档预览配置只用于维护者本地检查页面，不是参与者运行项目的要求。

## 运行项目演示

如果要现场演示完整对局，通常需要提前启动：

```powershell
python -m match_server.main
python -m local_inference_service.main
```

如果演示线下 Bot 列表，还可以启动：

```powershell
python -m bots.local_http_api
```

## 常见问题

| 现象 | 可能原因 | 处理方式 |
|---|---|---|
| 创建房间没有房间号 | Match Server 未启动或地址不对 | 检查服务器地址 |
| 进入棋盘后没有自动落子 | 本地推理服务未启动 | 启动 Local Inference Service |
| 选择脚本后无法落子 | 脚本不符合 MoveEngine 协议 | 检查 stdin/stdout JSON |
| 对局流程和文档不一致 | 客户端和服务器版本不一致 | 确认使用同一份代码 |

## 检查服务

Match Server 健康检查：

```text
http://127.0.0.1:9000/health
```

本地推理服务健康检查：

```text
http://127.0.0.1:8000/health
```

联机冒烟测试：

```powershell
python tools\online_match_smoke.py --ws-url ws://127.0.0.1:9000/ws --timeout 8
```
