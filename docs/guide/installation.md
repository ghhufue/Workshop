# 安装项目

本页说明如何从零开始安装本项目。命令以 Windows PowerShell 为主；如果你使用 macOS 或 Linux，命令思路相同，但虚拟环境激活方式和 Godot 下载包不同。

## 1. 安装基础工具

先准备这些工具：

| 工具 | 用途 |
|---|---|
| Git | 克隆仓库和子模块 |
| Python 3.10 或更新版本 | 运行服务端、训练脚本和本地推理 |
| pip | 安装 Python 依赖 |
| Godot 4.6 | 打开图形客户端 |
| NVIDIA 驱动 | 如果要用 GPU 训练 PyTorch 模型 |

本项目的 `gomoku_ai` 要求 Python `>=3.10`。建议使用 Python 3.10、3.11 或 3.12。

检查 Python：

```powershell
python --version
pip --version
```

## 2. 克隆仓库

本仓库地址：

```text
https://github.com/ghhufue/Workshop.git
```

因为项目包含子模块，推荐直接用：

```powershell
git clone --recurse-submodules https://github.com/ghhufue/Workshop.git
cd Workshop
```

如果你已经普通克隆过仓库，再补子模块：

```powershell
git submodule update --init --recursive
```

确认子模块存在：

```powershell
git submodule status
```

应该能看到 `gomoku_ai` 和 `godot_client`。

## 3. 创建虚拟环境

在仓库根目录创建 `.venv`：

```powershell
python -m venv .venv
```

激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 拒绝执行脚本，可以在当前终端临时放开执行策略：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 4. 安装项目依赖

本项目只需要仓库根目录下这一个虚拟环境。确认当前目录是 `Workshop`，并且虚拟环境已经激活后，运行一次：

```powershell
pip install -r requirements.txt
```

根目录的 `requirements.txt` 已经包含主服务依赖、`gomoku_ai` 训练依赖，并会以 editable 方式安装 `gomoku_ai` 子模块，不需要再进入 `gomoku_ai` 目录创建或安装第二套环境。

`gomoku_ai` 当前默认依赖 GPU 版 PyTorch：

```text
torch==2.12.0+cu130
```

如果你有 NVIDIA 显卡并且驱动足够新，通常可以直接安装成功。如果安装失败，按下一节重新选择适合自己机器的 PyTorch 版本。

## 5. 安装 GPU 版 PyTorch

PyTorch 的官方安装入口是：

[https://pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/)

官方页面可以按系统、包管理器、语言和计算平台生成安装命令。PyTorch 官网的稳定版和 CUDA 选项会更新，不要照抄旧命令；以你打开页面时显示的选项为准。

例如当前官网页面可能显示：

```text
Stable (2.12.0)
Windows / Pip / Python
CUDA 12.6 / CUDA 13.0 / CUDA 13.2 / CPU
```

### 先确认显卡类型

在 PowerShell 里查看显卡：

```powershell
Get-CimInstance Win32_VideoController | Select-Object Name
```

如果是 NVIDIA 显卡，再查看驱动和 CUDA 支持：

```powershell
nvidia-smi
```

重点看两项：

| 字段 | 含义 |
|---|---|
| GPU 型号 | 例如 RTX 3060、RTX 4070、RTX 5090 |
| CUDA Version | 当前驱动能支持的最高 CUDA 运行时版本 |

### 怎么选择 CUDA 版本

先记住三件事：

1. PyTorch 官网里的 `cu126`、`cu130`、`cu132` 这类后缀，指的是 PyTorch wheel 自带的 CUDA 运行时版本。
2. 普通安装 PyTorch 时通常不需要单独安装 CUDA Toolkit；你主要需要安装合适的 NVIDIA 显卡驱动。
3. `nvidia-smi` 右上角的 `CUDA Version` 可以理解为“当前驱动最高支持到哪个 CUDA 运行时版本”，不是你电脑上已经安装了哪个 CUDA Toolkit。

选择流程：

```text
有 NVIDIA 显卡
  -> 运行 nvidia-smi
  -> 看 CUDA Version
  -> 在 PyTorch 官网选择不高于该版本的最高 CUDA wheel

没有 NVIDIA 显卡
  -> 选择 CPU
```

常见情况：

| `nvidia-smi` 显示 | PyTorch 官网建议选择 |
|---|---|
| CUDA Version >= 13.2 | CUDA 13.2 |
| CUDA Version >= 13.0，但 < 13.2 | CUDA 13.0 |
| CUDA Version >= 12.6，但 < 13.0 | CUDA 12.6 |
| 低于官网最低 CUDA 选项 | 更新 NVIDIA 驱动，或安装 CPU 版本 |
| 没有 NVIDIA 显卡 | CPU 版本 |

显卡型号只作为辅助判断：

| 机器情况 | 建议 |
|---|---|
| RTX 50 系列 | 优先更新到最新 NVIDIA 驱动，再选官网提供的最高 CUDA 版本 |
| RTX 20/30/40 系列 | 驱动足够新时选官网提供的最高 CUDA 版本；否则按 `nvidia-smi` 显示选择不超过驱动支持范围的版本 |
| 较老 NVIDIA 显卡 | 先确认驱动是否还能更新到支持官网当前提供的 CUDA 版本 |
| AMD 显卡 Windows | 通常选择 CPU；ROCm 主要面向 Linux |

实际安装时，最稳妥的做法是更新到较新的 NVIDIA Game Ready 或 Studio Driver，然后在 PyTorch 官网选择当前显示的最高 CUDA 版本。官网命令会自动带上正确的 `--index-url`，例如 CUDA 12.6 会生成类似：

```powershell
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

如果安装后 `torch.cuda.is_available()` 是 `False`，不要先去装 CUDA Toolkit。先检查：

```powershell
nvidia-smi
pip show torch
```

确认你安装的是来自 `download.pytorch.org/whl/cuXXX` 的 PyTorch，而不是 CPU 版。

### 本项目推荐命令

如果你只想按项目当前依赖复现，优先使用仓库根目录的 `requirements.txt`：

```powershell
pip install -r requirements.txt
```

这个文件已经合并了 `gomoku_ai` 的依赖，并默认使用 CUDA 13.0 的 PyTorch wheel。如果你的机器不适合 CUDA 13.0，请先按 PyTorch 官网选择合适版本，再把根目录 `requirements.txt` 里的 `--index-url` 和 `torch==...` 改成官网生成命令对应的版本。

例如 CUDA 12.6 通常需要类似：

```powershell
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

如果你是在开发独立的 `gomoku_ai` 子模块，可以使用它自己的 `gomoku_ai/requirements.txt`。但下载和运行完整 Workshop 仓库时，统一使用根目录虚拟环境和根目录 `requirements.txt`，不需要为子模块再建一套环境。

如果没有 NVIDIA 显卡，安装 CPU 版本：

```powershell
pip install torch torchvision torchaudio
```

安装后验证：

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU only')"
```

输出 `True` 表示 PyTorch 可以访问 GPU。

## 6. 安装 Godot

Godot 官方下载页：

[https://godotengine.org/download/windows/](https://godotengine.org/download/windows/)

当前 `godot_client/project.godot` 使用 Godot 4.6 项目格式。建议下载 Godot 4.6.x 标准版。官方 Windows 页面提供 Godot Engine 4.6.3，并说明 Godot 是自包含程序，下载后解压运行即可。

下载建议：

| 需求 | 下载项 |
|---|---|
| 只运行本项目客户端 | Godot Engine 4.6.x |
| 需要 C#/.NET 项目 | Godot Engine - .NET 4.6.x |

本项目 Godot 客户端不需要 .NET 版本，普通 Godot Engine 即可。

打开客户端：

```text
Godot -> Import -> 选择 Workshop/godot_client/project.godot
```

导入后点击运行按钮即可打开图形客户端。

## 7. 验证安装

验证当前 Python 环境、pip 依赖、本地推理服务、MoveEngine 协议、`gomoku_ai` C++ 后端和 C++ 编译器：

```powershell
python tools\verify_environment.py
```

验证通过时，所有检查项都应显示 `[OK]`：

```text
[OK  ] Python version                   CPython 3.13.10 at .venv\Scripts\python.exe
[OK  ] Virtual environment              active at .venv
[OK  ] pip                              pip 25.3 ...
[OK  ] setuptools                       80.10.2; satisfies <81
[OK  ] PyTorch                          torch 2.12.0+cu130; cuda_available=True; device=NVIDIA GeForce RTX 5070
[OK  ] Package fastapi                  0.136.1
[OK  ] Package uvicorn                  0.46.0
[OK  ] Package websockets               16.0
[OK  ] Package pydantic                 2.13.4
[OK  ] Package PyYAML                   6.0.3
[OK  ] Package numpy                    2.4.6
[OK  ] Package pybind11                 3.0.4
[OK  ] Package torch                    2.12.0+cu130
[OK  ] Package tqdm                     4.67.3
[OK  ] Package tensorboard              2.20.0
[OK  ] Local Inference Service imports  app and core modules import successfully
[OK  ] Local Inference Service request  {"row": 7, "col": 7, ...}
[OK  ] Dynamic Python MoveEngine        stdin/stdout JSON Lines path works
[OK  ] gomoku_ai imports                gomoku_ai, bots, and env import successfully
[OK  ] C++ precompute table             gomoku_ai\cpp\precompute\direction_delta_table.bin
[OK  ] gomoku_ai C++ backend            available; scored 1 candidate(s)
[OK  ] pip dependency consistency       No broken requirements found.

Environment verification passed.
```

> 如果没有安装 MSVC 编译器，可以加 `--skip-compiler` 跳过 C++ 编译器检查：
> ```powershell
> python tools\verify_environment.py --skip-compiler
> ```

验证 `gomoku_ai` 最小训练流程：

```powershell
python gomoku_ai/scripts/demo_v0_env.py
python gomoku_ai/scripts/train_v1_terminal.py --n-envs 1 --n-steps 4 --updates 1 --batch-size 4 --epochs 1 --no-progress
```

如果这些命令能跑通，说明 Python 环境、子模块和基础训练依赖已经可用。

如果你是在修改项目代码，可以额外运行开发者测试：

```powershell
pytest -q
```

## 常见问题

### 克隆后没有 `gomoku_ai` 或 `godot_client`

说明子模块没有拉下来，运行：

```powershell
git submodule update --init --recursive
```

### `torch.cuda.is_available()` 是 `False`

常见原因：

- 安装了 CPU 版 PyTorch。
- NVIDIA 驱动太旧。
- 当前机器不是 NVIDIA 显卡。
- 虚拟环境里装了多个冲突的 torch 版本。

先运行：

```powershell
nvidia-smi
pip show torch
```

确认驱动和 torch 版本后，再按 PyTorch 官方安装页面重新安装。

### Godot 打开项目后提示版本不一致

本项目使用 Godot 4.6 项目格式。优先下载 Godot 4.6.x。不要使用 Godot 3.x 打开这个项目。
