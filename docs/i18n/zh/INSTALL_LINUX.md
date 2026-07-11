[Deutsch](../../../INSTALL_LINUX.md) · [English](../en/INSTALL_LINUX.md) · [Español](../es/INSTALL_LINUX.md) · [Français](../fr/INSTALL_LINUX.md) · [Українська](../uk/INSTALL_LINUX.md) · **简体中文**

# BgRemover – 在 Linux 上安装

从 GitHub 安装并启动 BgRemover 的简要说明——
既可以从 `main` 分支，也可以从某个功能分支（例如
为了在合并前测试一个开放的 Pull Request）。

> macOS 应用程序包（`create_BgRemover_app.sh`）是 macOS 专属的。
> 在 Linux 下，AppImage 和 `.deb` 是推荐给最终用户的构件；从 venv
> 直接启动仍作为开发、分支测试和本地修改的方式记录在下文。

## 推荐：使用 release 构件

对于普通 Linux 安装，release 构件是最方便的方式——**无需 venv、无需 pip、也无需
Git checkout**：

> **关于可用性的说明：** 现成的 AppImage/`.deb` 构件（**已内置 AI**）自
> **v2.4.0** 起提供。较旧的 release（v2.1.0/v2.2.0）尚未包含此类
> 资源——只要 Releases 页面上没有可供下载的内容，就请使用
> 下文的 venv/Git 方式。

- **AppImage：** 便携式单文件；赋予执行权限后即可启动。
- **`.deb`：** 面向 Debian/Ubuntu/Raspberry Pi OS 的可安装软件包，带菜单项，
  可通过 apt/dpkg 干净移除。

从 [GitHub Releases 页面](https://github.com/NikolayDA/picture_helper/releases) 下载匹配的构件：

```bash
# AppImage（x86_64 示例）
chmod +x BgRemover-*-x86_64.AppImage
./BgRemover-*-x86_64.AppImage

# .deb（amd64 示例；apt 会安装 FUSE 依赖）
sudo apt install ./BgRemover-*-amd64.deb
```

提供 **x86_64** 和 **aarch64/Raspberry Pi OS 64-bit** 构建。下面的 venv/Git
说明仍适用于从 `main`、功能分支或本地修改进行测试。

## 前提条件

> **使用 Raspberry Pi OS（桌面版）？** 那就采用下文中
> [更简单的方式](#raspberry-pi-os桌面版-简单方式)——
> 完全无需 venv 和 pip。下面这一节适用于通用
> Linux。

- **带桌面环境的 Linux 发行版**（X11 或 Wayland）
- **Python 3.10 或更新版本**——用以下命令检查：
  ```bash
  python3 --version
  ```
- **git** 和 **venv** 模块（`python3-venv`）
- 用于 PyQt6 的 **Qt 系统库**——PyQt6 wheel 自身包含 Qt
  本体，但需要一些 X11/XCB 系统库。缺少它们时，
  GUI 会以错误启动失败：*“qt.qpa.plugin: Could not load the Qt
  platform plugin xcb”*。

> **AI 说明：** 核心应用可在 Python 3.10+ 上运行。AI 背景移除
> （`.[ai]`）需要 **Python 3.11 或更新版本**（当前的 `onnxruntime` 和
> `rembg` 构建面向 Python 3.11+）。

### 安装系统软件包

**Debian / Ubuntu / Linux Mint**（`apt`）：
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git \
  libegl1 libgl1 libfontconfig1 libxkbcommon0 libxkbcommon-x11-0 \
  libdbus-1-3 libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
  libxcb-xinerama0 libxcb-xkb1
```
（`libxcb-cursor0` 是 Qt 6.5+ 在 Ubuntu 24.04 等系统上
`xcb` 插件所需要的。）

**Fedora / RHEL**（`dnf`）：
```bash
sudo dnf install -y python3 python3-pip git \
  libxcb xcb-util-cursor xcb-util-image xcb-util-keysyms \
  xcb-util-renderutil xcb-util-wm libxkbcommon-x11 \
  fontconfig mesa-libGL mesa-libEGL dbus-libs
```

**Arch / Manjaro**（`pacman`）：
```bash
sudo pacman -S --needed python python-pip git \
  libxcb xcb-util-cursor xcb-util-image xcb-util-keysyms \
  xcb-util-renderutil xcb-util-wm libxkbcommon-x11 \
  fontconfig mesa
```

## Raspberry Pi OS（桌面版）— 简单方式

在 **Raspberry Pi OS “Bookworm” 桌面版**（Debian 12）或更新版本
（例如 “Trixie”/Debian 13，推荐 64 位）上，安装要简单得多：PyQt6、Pillow 和
numpy 都有现成的系统软件包，可通过 `apt` 获取。**无需
venv、无需 `pip`、也无需 editable 安装**——BgRemover 可
直接从克隆的目录运行。软件包 `python3-pyqt6` 会
自动把所需的 Qt6/XCB 库作为依赖一并引入（上面
那个长长的 XCB 列表就不需要了）。

```bash
sudo apt update
sudo apt install -y git python3-pyqt6 python3-numpy python3-pil
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m bgremover
```

就这样——主窗口会打开。手动工具
（魔棒、画笔/橡皮擦、裁剪、旋转、镜像翻转、圆角
处理）完全可用。**在这个最小安装中 AI 背景移除是
禁用的**（AI 按钮呈灰色）——如有需要可选择
加装（见下文）。

之后只需在项目目录中执行 `git pull` 即可更新；
无需再次执行安装步骤。

### 可选：从应用程序菜单启动

创建一个文件 `~/.local/share/applications/bgremover.desktop`，并将
`/PFAD/ZU/picture_helper` 替换为绝对项目路径：
```ini
[Desktop Entry]
Type=Application
Name=BgRemover
Comment=移除背景并编辑图片
Exec=python3 -m bgremover
Path=/PFAD/ZU/picture_helper
Icon=/PFAD/ZU/picture_helper/BgRemover_icon.png
Categories=Graphics;Photography;
Terminal=false
```
之后 BgRemover 会出现在应用程序菜单中，点击即可启动——
无需 venv 或包装脚本。

### 可选：加装 AI 背景移除

> **说明：** 在 Raspberry Pi 上，AI（`rembg` +
> `onnxruntime`）**明显更慢且更耗内存**。建议
> 仅在 **64 位 Raspberry Pi OS**（`uname -m` → `aarch64`）以及
> 内存充足（≥ 4 GB）的 Pi 4/5 上使用。在 32 位（`armv7l`/armhf）上
> 通常没有合适的 `onnxruntime` wheel——在那种情况下最好
> 不要使用 AI。

由于 `rembg` 是通过 pip 加装的，因此为此使用一个**可访问
系统 Qt 软件包**的 venv：
```bash
cd picture_helper
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install "rembg[cpu]"
python3 -m bgremover
```
`--system-site-packages` 会让通过 `apt` 安装的
PyQt6/Pillow/numpy 在 venv 中可见，这样就只需加载 `rembg` 和
`onnxruntime`。安装 `rembg` 后首次启动应用时，应用会自动一次性
下载模型（几百 MB，缓存在 `~/.u2net`）。状态栏会显示“AI 模型加载中…”，
随后显示“AI 就绪”。在此之前，AI 按钮会保持禁用；这是预期行为，
并不表示安装失败。
之后从 venv 启动：`source .venv/bin/activate` 然后
`python3 -m bgremover`。

## 从 `main` 快速开始

在现代 Linux 上，系统 Python 安装会根据 PEP 668
（“externally-managed-environment”）阻止 `pip install`。
因此要在一个隔离的 venv 中安装：

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

- `.[ai]` 会安装 `rembg[cpu]`，含 `onnxruntime`
  （AI 背景移除）。
- 不需要 AI 功能时：`python3 -m pip install -c requirements/constraints.txt -e .` 即可

在新的 shell 中启动前要重新激活 venv：
```bash
cd picture_helper
source .venv/bin/activate
python3 -m bgremover
```

## 启动方式

| 方式 | 命令 / 操作 | 结果 |
|----------|-----------------|----------|
| **A – 终端（推荐）** | 激活 venv，然后 `python3 -m bgremover` | 从项目目录直接启动。 |
| **B – 启动脚本** | `./bgremover.sh`（见下文） | 自动激活 venv 并启动应用程序。 |
| **C – 应用程序菜单** | `.desktop` 条目（见下文） | 通过双击 / 从应用程序菜单启动。 |

### B – 启动脚本

在项目目录中创建一个文件 `bgremover.sh`：
```bash
#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
source .venv/bin/activate
exec python3 -m bgremover "$@"
```
赋予可执行权限并启动：
```bash
chmod +x bgremover.sh
./bgremover.sh
```

### C – 桌面条目（应用程序菜单）

创建一个文件 `~/.local/share/applications/bgremover.desktop`，并将
`/PFAD/ZU/picture_helper` 替换为绝对项目路径：
```ini
[Desktop Entry]
Type=Application
Name=BgRemover
Comment=移除背景并编辑图片
Exec=/PFAD/ZU/picture_helper/bgremover.sh
Icon=/PFAD/ZU/picture_helper/BgRemover_icon.png
Categories=Graphics;Photography;
Terminal=false
```
之后更新桌面数据库（可选）：
```bash
update-desktop-database ~/.local/share/applications 2>/dev/null || true
```
BgRemover 现在会出现在应用程序菜单中。

## 从某个分支安装（测试开放的 PR）

PR 分支名称见 GitHub 上对应的 Pull Request
（“… wants to merge … from **`<branch>`**”）。

**方式 1 – 在已有的克隆目录中：**
```bash
cd picture_helper
git fetch origin
git branch -r                       # 显示可用的分支
git checkout <branch>
source .venv/bin/activate
# 仅在依赖项发生变化时才需要：
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

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

## 故障排除

- **`qt.qpa.plugin: Could not load the Qt platform plugin "xcb"`** →
  缺少 Qt 系统库。请补装*“安装系统软件包”*
  一节中的软件包（尤其是 Ubuntu 24.04 上的
  `libxcb-cursor0`）。具体缺少哪个库，
  可用以下命令查看：
  ```bash
  QT_DEBUG_PLUGINS=1 python3 -m bgremover 2>&1 | grep -i "cannot\|not found"
  ```
- **执行 `pip install` 时出现 `error: externally-managed-environment`** → PEP
  668：不要安装到系统 Python 中，而是装到一个 venv（见
  快速开始）。缺少 venv 模块？→ `sudo apt install python3-venv`。
- **“python3: command not found” 或版本 < 3.10** → 通过
  发行版的包管理器安装一个较新的
  Python（代码使用了像 `QThread | None` 这样的 PEP-604 类型注解；Python 3.9 会
  失败）。
- **Wayland：窗口/缩放显示异常** → 试着切换到
  X11 插件（XWayland）：
  ```bash
  QT_QPA_PLATFORM=xcb python3 -m bgremover
  ```
- **安装时出现 pip 错误** → 在已激活的 venv 中先升级
  pip，然后重复安装命令：
  ```bash
  python3 -m pip install --upgrade "pip>=26.1.2"
  ```
- **首次启动带 AI 的应用较慢** → 安装 `rembg` 后首次启动应用时，
  应用会自动下载模型（几百 MB，一次性，缓存在 `~/.u2net`）。
  状态栏会显示“AI 模型加载中…”，随后显示“AI 就绪”。
  在此之前，AI 按钮会保持禁用；这是预期行为，并不表示安装失败。
- **应用程序在没有 AI 的情况下启动 / “No onnxruntime backend found”** →
  没有安装 `ai` extra。在 venv 中补装：
  ```bash
  python3 -m pip install "rembg[cpu]"
  ```
- **Raspberry Pi：`Unable to locate package python3-pyqt6`** → 较旧的
  Raspberry Pi OS 版本（Bullseye）只提供 PyQt5。请
  升级到 “Bookworm”（或更新版本）——或者按照上面
  通用的 venv/pip 方式操作。
- **Raspberry Pi OS “Bookworm”（Pi 4/5）使用 Wayland** → 出现窗口
  或缩放问题时，试着切换到 X11 插件：
  `QT_QPA_PLATFORM=xcb python3 -m bgremover`（参见上面的 Wayland
  说明）。
- **出错时的诊断** → 内部运行时日志的确切路径显示在
  `工具 → 设置… → 日志文件` 中；在 Linux 上，该文件位于 Qt
  确定的 `~/.local/share/` 下的目录中。从终端启动时，错误消息
  还会直接出现在控制台上。
