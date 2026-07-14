[Deutsch](../../../README.md) · [English](../en/README.md) · [Español](../es/README.md) · [Français](../fr/README.md) · [Українська](../uk/README.md) · **简体中文**

# BgRemover

[![CI](https://github.com/NikolayDA/picture_helper/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/NikolayDA/picture_helper/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/NikolayDA/picture_helper/branch/main/graph/badge.svg)](https://codecov.io/gh/NikolayDA/picture_helper)
[![License Check](https://github.com/NikolayDA/picture_helper/actions/workflows/license-check.yml/badge.svg?branch=main)](https://github.com/NikolayDA/picture_helper/actions/workflows/license-check.yml)
[![Latest release](https://img.shields.io/github/v/release/NikolayDA/picture_helper)](https://github.com/NikolayDA/picture_helper/releases/latest)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/github/license/NikolayDA/picture_helper)](https://github.com/NikolayDA/picture_helper/blob/main/LICENSE)
[![Platform: macOS | Linux](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)](https://github.com/NikolayDA/picture_helper)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

一款用于 macOS 和 Linux 的图像处理工具，可**抠图、编辑并将图案准备好用于打印**——从 AI 背景移除，经由图层、项目和高度图，直至**为 UV 打印（EufyMake Studio）导出资源**。具备魔棒、画笔/橡皮擦、多边形套索、多种比例的裁剪、旋转、镜像翻转、圆角处理以及色彩校正功能。

## 功能

- **🤖 AI 背景移除**：通过 [rembg](https://github.com/danielgatis/rembg) 实现——一键完成。
- **🪄 魔棒**：通过 Flood-Fill 选择相连的色块（带容差滑块）。
- **🖌 画笔 / 橡皮擦**：手动绘制或擦除选区。
- **➰ 多边形套索**：通过设置角点精确限定选区。
- **🎨 替换背景**：用任意颜色填充选区，或将其设置为透明。
- **✂ 裁剪**：带三分法网格：圆形、1:1、16:9、4:3、9:16、3:4。
- **⟲ 旋转**：以 90° 为步长或任意角度旋转；**↔ 镜像翻转**水平/垂直。
- **⬤ 圆角**：圆角半径可调。
- **📐 尺寸与物理尺寸**：缩放到目标像素分辨率，**或**通过毫米和 DPI 设定（可锁定纵横比、可选重采样方法）；并对目标介质（如 A4/A3）进行打印区域检查。
- **🎚 色彩校正**：对活动图层调整亮度、对比度与饱和度，带实时预览（保留 Alpha）。
- **🪶 平滑边缘**：抠图边缘柔化（Alpha 羽化），可受选区限制，适用于 AI 或手动抠图之后。
- **🗂 图层与项目**：管理多个图层（颜色、高度、光泽、通用）及其角色，并将整个内容无损保存和打开为 `.bgrproj` 项目。
- **🏔 高度图**：从图像生成、编辑并优化灰度高度图（浅色 = 高）——浮雕与 UV 打印的基础。
- **👁 2D 预览**：在屏幕上检查颜色、颜色上的浮雕、高度和光泽；仅为显示，图像导出仍是彩色图案。
- **↩ 历史记录**：支持撤销以及跳转到任意此前的步骤。
- **📥 拖放**：可将图像直接拖到窗口中。
- **📂 输入格式**：可打开 **PNG、JPEG、WebP、TIFF、BMP 和 GIF**。**目前不支持 HEIC/HEIF。**
- 保存为 **PNG**（带透明度）、**JPEG**（白色背景）、**WebP** 或 **TIFF**。
- **⚙ 持久化设置**：默认目录和首选文件格式将被保留；还可在设置中定位日志文件并打开其目录。
- **🖨 导出到 EufyMake Studio**：写出导入资源（彩色图案为 RGBA PNG，可选高度图浅色 = 高，可选光泽蒙版），并附带预检查与后续 Studio 步骤。BgRemover **不**生成原生 `.empf` 文件——导入、定位与墨水模式分配均在 EufyMake Studio 中完成。

## 截图

![BgRemover – 带图层卡片的“浮雕与图层”步骤](../../screenshot.png)

*引导式“浮雕与图层”步骤：图层卡片（右侧）显示由彩色图案图层和高度图层组成的
项目，并带有角色分配。*

![高度图工作区](../../screenshot_height.png)

*同一步骤的“获取”和“编辑”卡片：从图像生成高度图或导入一张，然后调整——高度
语义为浅色 = 高。*

![2D 预览：颜色上的浮雕与光泽](../../screenshot_preview.png)

*“导出”步骤：组合式 2D 预览将浮雕和光泽叠加在彩色图案之上——仅为显示，导出
不变。*

![EufyMake Studio 导出对话框](../../screenshot_export.png)

*导出对话框生成导入资源（彩色图案、可选高度图与光泽蒙版）并附带预检查——
**而非**原生 `.empf` 文件。*

## 前提条件

- **macOS** 或 **Linux 桌面环境**（可选的应用程序包使用了
  macOS 专属工具，如 `iconutil`）
- **Python 3.10 或更新版本**（代码在函数签名中直接使用了
  PEP-604 类型注解，如 `QThread | None`——Python 3.9 会失败）
- 依赖项（`PyQt6`、`Pillow`、`numpy`，AI 功能可选用 `rembg`）
  通过 `pyproject.toml` 安装。

对于可复现的 AI/app 依赖快照，建议使用 **Python 3.11 或更新版本**：
部分当前的 AI 传递依赖已不再支持 Python 3.10。不带 AI 的基础应用
仍支持 Python 3.10。

## 安装

**最快的方式——开箱即用的下载。** 在
[Releases 页面](https://github.com/NikolayDA/picture_helper/releases/latest)
提供了**已内置 AI** 的即用型构件，无需在本地安装 Python：

- **macOS**（Apple Silicon/arm64）：下载 `.dmg` 并将 `BgRemover.app` 拖入
  *应用程序*。该程序包目前**未签名**——首次启动时通过**右键 →「打开」**确认
  （[INSTALL_MAC.md](INSTALL_MAC.md)）。
- **Linux / Raspberry Pi OS**（x86_64 与 aarch64）：便携式 **AppImage** 或可安装的
  **`.deb`**（[INSTALL_LINUX.md](INSTALL_LINUX.md)）。

如需从源代码构建或用于开发，请继续阅读下文。

**从源代码（macOS）：构建应用程序包。** 该脚本会自动创建隔离的
app venv，尝试安装 AI 依赖项（包括 `onnxruntime`），正确处理
Apple Silicon，并生成一个 `BgRemover.app` 启动器：

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

如果需要新建 app venv，请在提示时按 **Enter** 确认。之后双击
`BgRemover.app`（位于 `~/Applications`）即可启动——其功能与随附的
**`BgRemover.command`** 相同。启动器使用单独安装在
`~/Library/Application Support/BgRemover/venv` 下的 venv，因此项目
可以保留在 `~/Documents` 中。但 app 与 app venv 必须配套使用：
单独的 `.app` 文件并不可移植。如果 AI 依赖项安装失败，脚本会构建
一个不带 AI 但仍可使用的应用程序。

更新或切换分支后，请再次执行 `bash create_BgRemover_app.sh`。脚本会以
非 editable 方式将当前 checkout 覆盖安装到已有 app venv 中，并重新
构建启动器。

**或者直接在终端中运行**——在现代 macOS 上需在 venv 中进行，
因为系统 Python 会根据 PEP 668 阻止 `pip install`：

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

`.[ai]` 会一并引入 AI 依赖项（`rembg[cpu]`，含 `onnxruntime`）；
若不需要 AI 功能，`python3 -m pip install -c requirements/constraints.txt -e .` 即可。

**Linux：** 对最终用户，推荐使用 release 构件：便携式 **AppImage** 和可安装的
**`.deb`**（均提供 x86_64 与 aarch64/Raspberry Pi OS 版本）。安装详情见
**[INSTALL_LINUX.md](INSTALL_LINUX.md)**；构建/打包详情见
**[packaging/linux/README.md](../../../packaging/linux/README.md)**。此类构件自
**v2.4.0** 起提供；**macOS** 还提供 **`.dmg`**（Apple Silicon/arm64）——参见
**[INSTALL_MAC.md](INSTALL_MAC.md)**。

直接从 venv 启动仍然最适合开发、分支测试和本地修改：

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

从 venv 启动前需要一些 Qt 系统库——见 **[INSTALL_LINUX.md](INSTALL_LINUX.md)**。
在 **Raspberry Pi OS（桌面版）** 上也可以完全不使用 venv/pip（PyQt6、Pillow、numpy
通过 `apt` 作为系统包安装）；同样见 **[INSTALL_LINUX.md](INSTALL_LINUX.md)**。

> 详细的说明——包括**从某个分支安装**
> （用于测试开放的 Pull Request）和**故障排除**——见
> **[INSTALL_MAC.md](INSTALL_MAC.md)**（macOS）或
> **[INSTALL_LINUX.md](INSTALL_LINUX.md)**（Linux）。

## 使用方法

**引导式 6 步工作流**（画布上方的步骤条 + 右侧的卡片式检查器）引导整个编辑
过程：

1. **打开** – 将图像拖到放置区，或通过 `文件 → 打开`（⌘O）、将图像拖放到窗口中，或以启动路径（CLI / Finder）加载。
2. **抠图** – 点击卡片检查器中的 **AI** 按钮，或使用魔棒、画笔、橡皮擦或多边形套索；然后设为透明、替换颜色或平滑边缘。
   - `Shift+点击` 添加到选区；`⌘+点击`（macOS）或 `Ctrl+点击`（Linux）从选区中减去。
   - 可用键盘切换工具：`W` 魔棒、`B` 画笔、`E` 橡皮擦、`L` 套索（仅在此步骤中生效）。
3. **调整** – 带实时预览的亮度/对比度/饱和度。
4. **形状与尺寸** – 旋转、镜像翻转、圆角处理，选择裁剪比例（移动/缩放边框，然后点击 ✓ 应用），并调整尺寸。
5. **浮雕与图层** – 管理项目图层，生成/编辑/优化高度图。
6. **导出** – 以颜色/浮雕/高度/光泽/组合方式检查结果，通过 `文件 → 保存`（⌘S）保存为 PNG、JPEG、WebP 或 TIFF——或 `项目 → 导出 EufyMake Studio 资源…` 用于 UV 打印。

### 设置

通过 `工具 → 设置…`（⌘,）可管理以下设置：

| 设置 | 说明 |
|---|---|
| 默认打开目录 | 打开对话框的起始目录；留空 = 上次使用的目录 |
| 默认导出/保存目录 | 保存对话框的起始目录；留空 = 上次使用的目录 |
| 首选图像文件格式 | PNG、JPEG、WebP 或 TIFF——在保存对话框中作为第一个选项出现 |
| 语言 | 德语或英语；更改在重启后生效 |
| 日志文件 | 显示日志文件路径；“打开文件夹”按钮会在文件管理器中打开其目录 |
| 启动时自动检查更新 | 默认关闭；启用后会在启动后不久进行一次静默检查（见下文） |

目录、首选格式、语言以及自动更新检查设置均通过 **QSettings** 持久保存，
并在下次启动程序时自动恢复。

### 应用更新与 AI 模型管理

`工具` 菜单还提供三个选项：

- **“检查更新…”** 会非阻塞地查询最新的 GitHub 版本，并根据结果显示对话
  框：当前版本、带发布页面链接的新版本，或易懂的错误提示。若启用了
  “启动时自动检查更新”，发现新版本时状态栏还会显示一个低调、可点击的
  提示，点击后打开同一个对话框——无需再次发起网络请求。
- **“管理 AI 模型…”** 显示 `rembg` 是否可用、rembg 默认模型是否已缓存
  到本地，并提供显式的下载/重试操作，附带进度指示和取消按钮——作为应用
  启动时自动下载的替代方案（参见安装指南，例如 `INSTALL_MAC.md`）。
- **“安装 AI 背景移除…”** 显示用于补装 rembg 后端的对应命令，并提供复制到
  剪贴板按钮。应用会刻意避免自动安装任何内容；安装后需要重启应用，当前
  进程才能看到新包。

### 键盘快捷键

在 macOS 上修饰键是 **⌘ (Cmd)**，在 Linux 上是 **Ctrl**。工具快捷键
（W/B/E/L）仅在“抠图”步骤处于活动状态时生效。

| 操作 | 快捷键 |
|--------|----------|
| 选择魔棒 | W |
| 选择画笔 | B |
| 选择橡皮擦 | E |
| 选择多边形套索 | L |
| 打开图像 | ⌘O |
| 保存图像 | ⌘S |
| 图像另存为… | ⇧⌘S |
| 新建项目 | ⌘N |
| 打开项目… | ⇧⌘O |
| 保存项目 | ⌥⌘S |
| 调整尺寸… | ⌘R |
| 导出 EufyMake Studio 资源… | ⌥⌘E |
| 撤销 | ⌘Z |
| 重做 | ⇧⌘Z |
| 向左旋转 90° | ⌘← |
| 向右旋转 90° | ⌘→ |
| 取消选区（无活动裁剪/套索时） | Esc |
| 反转选区 | ⌘⇧I |
| Fit to View | ⌘0 |
| 打开设置 | ⌘, |

文件菜单中还有一个**“最近打开”**子菜单，
列出最近加载的 10 张图像——其状态会与
其余设置一起通过 QSettings 持久化保存。

## 开发与测试

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv
source .venv/bin/activate
make pr-check
```

测试套件以无头模式运行（Qt 平台为 `offscreen`），检验
图像操作、裁剪几何和保存逻辑。Pull Request 会运行轻量级
GitHub PR CI（Ubuntu、Python 3.12、`make pr-check`）。完整的
Linux/macOS 矩阵（Python 3.10、3.11、3.12 和 3.13）作为 release 门禁运行：推送版本标签时，
release 工作流会在发布前调用它；此外每周（周日）和手动触发时也会运行。所有本地/CI 测试安装都使用
`requirements/constraints.txt`；需要时可通过
`make PIP_CONSTRAINT=/path/to/file pr-check` 覆盖。完整测试流程见
[TESTING.md](../../../TESTING.md)。

代码风格检查与静态类型检查：

```bash
make lint
make type
```

### 重新生成 UI 截图

用于 review 和文档的完整截图集可以以 headless 方式复现：

```bash
make screenshots
```

生成器会写入 `app_screenshots/bgremover_complete_<timestamp>/`，
使用 Qt `offscreen`，用内存存储替代 QSettings，并模拟 AI 结果视图，
不会真正运行 `rembg` 模型。临时子目录 `_runtime/` 和 `_exports/`
会通过 `.gitignore` 保持为本地文件；可提交的产物是编号 PNG 文件和
`manifest.md`。

### 重新生成指南 PDF

`ANLEITUNG.pdf` 由 `ANLEITUNG.md` 生成（Markdown → HTML → PDF，
通过 WeasyPrint）。修改 Markdown 源文件后，请以可复现方式重新生成
PDF。在 Linux 上，需要 DejaVu 字体和发行版提供的
Pango/Cairo/GDK-Pixbuf 软件包。在 macOS 上，生成器使用系统字体
Arial/Courier New；请用 `brew install pango` 安装 Pango：

```bash
pip install -e ".[docs]"
python scripts/generate_anleitung_pdf.py
```

## 架构（简要概览）

BgRemover 是一个可安装的包（`bgremover/`，通过 `python -m bgremover`
或 console-script `bgremover` 启动）：

- **`ImageCanvas`**（QGraphicsView）保存图像状态、选区蒙版、
  撤销/重做栈以及工具（魔棒、画笔、套索、裁剪）。
- **`MainWindow`** 构建工具栏和状态/裁剪栏，并连接画布、菜单、
  右侧面板和 worker；`_apply_toolbar_for_step` 会根据当前步骤切换
  上下文相关的工具栏。
- **`stepper`** 是无状态的 6 步骤条（打开/抠图/调整/形状与尺寸/浮雕与
  图层/导出）；**`right_panel`** 基于它构建卡片式检查器（标题、每个步骤
  对应一页的 `QStackedWidget`、导航页脚），并为其分配 `right_panel_tabs`
  中现有的八个标签页构建块（预览、选区、背景、调整、旋转/翻转、形状、
  图层、高度）；`project_model`/`height_map` 提供与 Qt 无关的图层与
  高度模型。
- **`menu_actions`** 构建菜单栏、actions 和快捷键；`MainWindow`
  只提供回调。
- **`RecentFiles`** 封装“最近打开”的持久化、去重和菜单适配器，
  因而 `MainWindow` 只需委托加载路径。
- **Worker**（`ImageLoadWorker`、`AIWorker`、`RembgWarmupWorker`、
  `FloodFillWorker`）运行在
  各自的 `QThread` 中；`WorkerController` 封装启动、强 worker 引用、
  `deleteLater` 和 shutdown。
- 画布中的单调**版本计数器**会丢弃过时的 AI 和 flood-fill 结果，
  以防期间加载了另一张图像或图像状态发生变化。
- 撤销和重做共享一个**内存上限**（`_HISTORY_MEMORY_LIMIT`）；持续累加的
  字节总和会清除最旧的历史记录。原始图像和当前画布状态有意不计入此预算。

## 已知限制

- **输入格式：** 支持 **PNG、JPEG、WebP、TIFF、BMP 和 GIF**。**目前不支持
  HEIC/HEIF**（无 `pillow-heif`）；此类文件会作为不受支持的格式被受控地拒绝。
- **最大图像尺寸：40 兆像素。** 更大的图像会以状态消息被拒绝，
  以限制内存占用和处理时间。魔棒选区（Flood-Fill）会在独立的
  `QThread` 中异步运行，因此计算期间界面仍可响应。Pillow 此外还
  针对“解压缩炸弹”图像做了防护。
- **应用程序包构建**是 macOS 专属的；在 Linux 下应用程序通过直接
  `python -m bgremover` 启动来运行。Windows 当前不在官方测试矩阵中。

## 日志文件

应用程序内部 logger 会使用 Qt 确定的应用数据目录中的
`bgremover.log` 文件。具体路径取决于平台和 Qt 配置；在当前 macOS
配置下为
`~/Library/Application Support/BgRemover/BgRemover/bgremover.log`，
在 Linux 下则位于 `~/.local/share/` 之下。该文件包含运行时消息和
已记录错误的堆栈跟踪，并在首次写入日志时创建。

macOS 应用程序包启动器还会将启动诊断信息写入
`~/Library/Application Support/BgRemover/bgremover.log`。

内部日志的准确路径显示在 `工具 → 设置… → 日志文件` 中；
“打开文件夹”按钮可直接在文件管理器中打开其目录。

## 许可证

BgRemover 采用 **GNU General Public License v3.0 或
更高版本**（`GPL-3.0-or-later`）——参见 [LICENSE](../../../LICENSE)。

所有所用库、工具和资源（含许可证）的完整列表
见 **[RESOURCES.md](RESOURCES.md)**。

> **关于 PyQt6 的说明：** GUI 依赖项 PyQt6（Riverbank）
> 本身采用 GPL-v3 许可（或商业许可）。之所以特意选择
> GPL-3.0，是为了使分发的应用程序——尤其是
> 打包的 `BgRemover.app`——符合许可证要求。希望采用宽松
> 模式（MIT/Apache-2.0）的人，需要用采用 LGPL
> 许可的 **PySide6** 替换 PyQt6。
