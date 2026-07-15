[Deutsch](../../../INSTALL_MAC.md) · [English](../en/INSTALL_MAC.md) · [Español](../es/INSTALL_MAC.md) · [Français](../fr/INSTALL_MAC.md) · [Українська](../uk/INSTALL_MAC.md) · **简体中文**

# BgRemover – 在 Mac 上安装

从 GitHub 安装并启动 BgRemover 的简要说明——
既可以从 `main` 分支，也可以从某个功能分支（例如
为了在合并前测试一个开放的 Pull Request）。

## 下载预构建应用（`.dmg`）

最简单的方式——**无需 Python、git 或终端**：从
[GitHub releases](https://github.com/NikolayDA/picture_helper/releases)
下载预构建的应用程序包。Apple Silicon（arm64）对应
`BgRemover-<version>-macos-arm64-ai.dmg`(文件名标明了平台和架构)；AI 抠图已经
内置——从 `-ai` 后缀即可看出，与 Linux 构件一致。

1. 打开 `.dmg`，将 `BgRemover.app` 拖入**应用程序**文件夹。
2. **首次**启动时通过**右键点击 →“打开”**确认——该程序包尚未经过 Apple
   签名/公证，否则 Gatekeeper 会警告“来自身份不明的开发者”。

也可以预先在终端中移除隔离属性：

```bash
xattr -dr com.apple.quarantine /Applications/BgRemover.app
```

若你更愿意从源码构建（例如 Intel Mac 或自定义修改），请参考下方章节。

## 前提条件

- **macOS**
- **Python 3.10 或更新版本**——用以下命令检查：
  ```bash
  python3 --version
  ```
- **git**

> **AI 说明：** 核心应用可在 Python 3.10+ 上运行。AI 背景移除
> （`.[ai]`）需要 **Python 3.11 或更新版本**（当前的 `onnxruntime` 和
> `rembg` 构建面向 Python 3.11+）。

如果缺少 Python 或 git，最简单的方式是通过 [Homebrew](https://brew.sh)：
```bash
brew install python git
```

## 从 `main` 快速开始

**推荐**使用应用程序包脚本——它会使用专用的应用程序 venv，
以非 editable 方式安装当前 checkout（包括工具栏图标），正确处理
Apple Silicon，并尝试安装 AI 依赖项：

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

如果创建新的应用程序 venv，出现提示时按 **Enter** 确认；之后
双击位于 `~/Applications` 的 `BgRemover.app` 即可启动。

**直接在终端中启动**——在现代 macOS 上需在 venv 中进行，
因为系统 Python 会根据 PEP 668 阻止 `pip install`：

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

- `.[ai]` 会安装 `rembg[cpu]`，含 `onnxruntime`（AI 背景移除）。
- 不需要 AI 功能时：`python3 -m pip install -c requirements/constraints.txt -e .` 即可

## 启动方式

安装之后，有三种方式启动程序：

| 方式 | 命令 / 操作 | 结果 |
|----------|-----------------|----------|
| **A – macOS 应用程序（推荐）** | `bash create_BgRemover_app.sh` | 维护一个专用的应用程序 venv，以非 editable 方式安装当前 checkout，尝试安装 AI 依赖项，复制图标，并在 `~/Applications` 下生成一个独立的 `BgRemover.app`。隔离属性会被自动移除；项目可以保留在 `~/Documents` 中。 |
| **B – 双击** | 在 Finder 中双击 `BgRemover.command` | 在终端窗口中启动；自动使用脚本创建的应用程序 venv（文件已具有可执行权限）。 |
| **C – 终端** | 在 venv 中：`python3 -m bgremover` | 直接启动（venv 设置见上面的快速开始）。 |

## 从某个分支安装（测试开放的 PR）

PR 分支名称见 GitHub 上对应的 Pull Request
（“… wants to merge … from **`<branch>`**”）。

**方式 1 – 在已有的克隆目录中：**
```bash
cd picture_helper
git fetch origin
git branch -r                       # 显示可用的分支
git checkout <branch>
# 在 venv 中（见快速开始）；仅在依赖项发生变化时才需要：
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

或者在某个分支上直接执行 `bash create_BgRemover_app.sh`
——它会把当前 checkout 重新安装到应用程序 venv 中，并自动处理
依赖项。

**方式 2 – 直接克隆某个分支：**
```bash
git clone --branch <branch-name> \
  https://github.com/NikolayDA/picture_helper.git
```

## 更新 / 切换分支

```bash
git checkout main && git pull          # 最新主版本
git checkout <branch> && git pull      # 更新某个特定分支
```

在 `git pull` 之后**无需**再次执行 editable 安装
（`pip install -e`）——除非 `pyproject.toml` 或
`requirements/constraints.txt` 中的依赖项发生了变化。

如果使用 `BgRemover.app`，请在更新或切换分支后再次执行
`bash create_BgRemover_app.sh`。脚本会自动更新专用应用程序 venv
中的软件包副本。

## 故障排除

- **应用程序无法启动 / 双击没有反应** → 自 v3 起，
  应用程序会显示一个带“打开日志”的错误对话框。最常见的原因：
  应用程序所使用的 Python 中没有安装 `PyQt6`
  （例如因为 `pip install` 装到了某个 venv 或另一个 Python，
  或者 Homebrew Python 根据 PEP 668 阻止了 `pip install`）。解决办法：
  再次执行 `bash create_BgRemover_app.sh` 并让它创建
  venv（按 Enter 确认提议）——脚本随后会把
  依赖项安装到位于
  `~/Library/Application Support/BgRemover/venv` 的 venv，并把这个 Python
  打包进应用程序中。
- **访问项目时出现 `[Errno 1] Operation not permitted`**
  → macOS 隐私保护（TCC）。如果项目位于 `~/Documents`、
  `~/Desktop`、`~/Downloads` 或 iCloud Drive，那么从
  Finder 启动的 `.app` 就无法在那里读取。当前包布局已解决这一点：
  `create_BgRemover_app.sh` 以**非 editable**
  方式将 `bgremover` 包安装到位于
  `~/Library/Application Support/BgRemover/venv` 的 venv 中（包含
  代码自身的副本以及作为 package-data 的 `icons/`），因此应用
  独立于项目目录。修复：重新执行一次
  `bash create_BgRemover_app.sh`。（或者将项目移动到例如
  `~/picture_helper`，然后在那里重新执行脚本。）
- **`numpy ... incompatible architecture (have 'arm64', need 'x86_64')`**
  → Apple Silicon：在 `~/Library/Python/...` 中存在一个架构不匹配的
  软件包，它“渗透”到了一个不匹配的 Python 中。启动器设置了
  `PYTHONNOUSERSITE=1`（忽略 user-site），
  强制使用原生 CPU 架构，并且会强制使用
  一个隔离的 venv。解决办法：最好先安装一个原生
  Python，然后重新构建：
  ```bash
  brew install python
  bash create_BgRemover_app.sh   # venv 询问按 Enter 确认
  ```
- **直接查看错误（手动诊断）** → 在终端中启动
  启动器，这样就会出现真实的错误消息：
  ```bash
  ~/Applications/BgRemover.app/Contents/MacOS/BgRemover
  ```
  缺少软件包时可预期出现：`ModuleNotFoundError: No module named 'PyQt6'`。
  更方便的方式：在项目目录中运行 `bash diagnose_mac.sh` 会自动收集这份启动
  诊断信息（包括应用 venv 的 `pip show bgremover`）；输出默认已脱敏，可附加到
  错误报告中。
- **“python3: command not found”** → `brew install python`
- **安装时出现 pip 错误** → 先升级 pip：
  ```bash
  python3 -m pip install --upgrade "pip>=26.1.2"
  ```
  然后重新执行安装命令。
- **启动后 AI 按钮短暂保持禁用** → 这不是安装错误：只要安装了
  `rembg`，应用就会在**应用启动**时（而不是首次点击 AI 时）自动
  一次性下载模型，几百 MB，缓存在 `~/.u2net`。期间状态栏会显示
  ”AI 模型加载中…”，然后显示”AI 就绪”；AI 按钮在此之前
  （以及未加载图片时）保持禁用。若下载在离线状态下失败，可随时通过
  `工具 → 管理 AI 模型…` 查看状态并手动触发下载/重试。
- **Gatekeeper：“未验证的开发者”** → 右键点击
  `BgRemover.app` → **打开**。构建脚本已经通过 `xattr`
  移除了隔离属性，不过保险起见，右键打开
  仍然足够。
- **应用程序以“No onnxruntime backend found”崩溃** → 较新的
  `rembg` 版本不再附带该后端。当前已修复
  （`ai` extra 会引入 `rembg[cpu]`/`onnxruntime`；即便仍然缺少，
  应用程序也会在没有 AI 的情况下启动，而不是崩溃）。解决办法：重新
  执行一次 `bash create_BgRemover_app.sh` 构建——或者向 venv 中补装：
  `"~/Library/Application Support/BgRemover/venv/bin/python3" -m pip install "rembg[cpu]"`。
- **`.app` 看起来与 `BgRemover.command` 不同** → 较旧的应用程序包
  没有工具栏图标（应用程序使用了绘制的替代图标）。图标是
  `bgremover/icons/` 中的 `package-data`，因此在 `pip install` 时
  自动进入 venv，并通过 `importlib.resources` 加载；重新执行一次
  `bash create_BgRemover_app.sh` 构建。
- **出错时的诊断** → 应用程序包启动器会将启动诊断信息写入
  `~/Library/Application Support/BgRemover/bgremover.log`。内部运行时
  日志可能位于子目录中；其确切路径显示在
  `工具 → 设置… → 日志文件` 中。
