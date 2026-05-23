[Deutsch](../../../RESOURCES.md) · [English](../en/RESOURCES.md) · [Español](../es/RESOURCES.md) · [Français](../fr/RESOURCES.md) · [Українська](../uk/RESOURCES.md) · **简体中文**

# 使用的资源

本文档列出了 BgRemover 使用或依赖的**所有外部资源**：库（Python
软件包）、其他软件和工具、第三方代码以及项目自有资源 —— 每项均
附带用途、许可证和获取来源。

> 版本说明：“最低”来自 `pyproject.toml`（强制性最低要求），“已验证”
> 是 `requirements/constraints.txt` 为当前本地/CI 检查固定的
> Python 3.12 baseline。始终以软件包随附的许可证文本为准。

---

## 1. 运行时依赖（Python 软件包）

在 `pyproject.toml` 的 `[project] dependencies` 下声明。

| 软件包 | 在程序中的用途 | 最低 | 已验证 | 许可证 |
|-------|-------------------|------|---------|--------|
| **PyQt6** | 完整 GUI（窗口、画布、控件、事件、QSettings、QThread） | `>=6.5` | 6.11.0 | **GPL v3** 或 Riverbank 商业许可证 |
| **Pillow** (PIL) | 图像 IO、EXIF 转置、旋转/翻转、蒙版/Alpha、保存（PNG/JPEG/WebP/TIFF） | `>=10` | 12.2.0 | HPND（亦称“MIT-CMU”；开源 PIL 许可证） |
| **NumPy** | 像素数组、flood-fill、蒙版运算 | `>=1.24` | 2.4.5 | BSD-3-Clause |

通过 PyQt6 还绑定了 **Qt 6** 框架（The Qt Company）。Qt 本身采用
LGPL v3 / GPL / 商业许可证；而 **PyQt6 绑定**为 GPL v3 —— 参见
第 8 节。

## 2. 可选的 AI 依赖

在 `[project.optional-dependencies] ai` 下声明 —— 仅自动背景移除
（`rembg` 工具）需要：

| 资源 | 用途 | 最低 | 已验证 | 许可证 | 获取 |
|-----------|-------|------|---------|--------|-------|
| **rembg[cpu]** | 基于 AI 的背景移除（`rembg.remove`） | `>=2.0` | 2.0.75 | MIT | PyPI |
| **onnxruntime** | ONNX 推理后端（`rembg[cpu]` 的传递依赖） | （传递） | 1.26.0 | MIT (Microsoft) | PyPI |
| **U²-Net 模型** (`u2net.onnx`) | 默认分割模型，由 rembg 在**运行时下载**（不包含在仓库中） | – | – | Apache-2.0（项目 *U-2-Net*） | 由 rembg 下载至用户缓存目录 |

没有 `ai` extras 程序也能正常启动；此时 AI 按钮会被禁用
（`REMBG_AVAILABLE = False`）。

## 3. Python 标准库

属于 CPython 的一部分，**无需额外安装**
（许可证：PSF License Agreement）：

`sys`、`os`、`io`、`logging`、`collections.deque`、`pathlib.Path`、
`importlib.metadata`、`importlib.resources`、`contextlib`、`tempfile`。

## 4. 开发与测试工具

在 `[project.optional-dependencies] test` 下声明：

| 工具 | 用途 | 最低 | 已验证 | 许可证 |
|----------|-------|------|---------|--------|
| **pytest** | 测试运行器 | `>=8` | 9.0.3 | MIT |
| **pytest-qt** | Qt fixtures（无头 `offscreen`） | `>=4.4` | 4.5.0 | MIT |
| **ruff** | Linting / 风格检查 | `>=0.6` | 0.15.13 | MIT |
| **mypy** | 静态类型检查（CI 步骤） | `>=1.10` | 2.1.0 | MIT |
| **packaging** | 在测试中解析 dependency constraints | `>=24` | 24.0 | Apache-2.0 或 BSD-2-Clause |

可选文档/PDF 工具在 `[project.optional-dependencies] docs` 下声明：

| 工具 | 用途 | 最低 | 许可证 |
|----------|-------|------|--------|
| **Markdown** | 为 `ANLEITUNG.pdf` 将 Markdown 转为 HTML | `>=3.5` | BSD |
| **WeasyPrint** | 从 HTML/CSS 渲染 PDF | `>=61` | BSD-3-Clause |
| **fonttools** | PDF 生成时检查字体 | `>=4.0` | MIT |

PDF 生成还需要 DejaVu 字体以及 Pango/Cairo/GDK-Pixbuf 等系统资源
（由发行版打包）。

## 5. 构建与分发工具（macOS）

由应用程序包脚本 `create_BgRemover_app.sh` 所需。它**不会**捆绑
这些程序，而是通过系统调用它们：

| 工具 | 用途 | 来源 |
|----------|-------|----------|
| `python3` + `venv` + `pip` | 创建隔离的 venv，并使用 `requirements/constraints.txt` 安装依赖 | Python / PyPA |
| `setuptools`（构建后端） | 按 `[build-system]` 进行打包（`>=61`） | MIT |
| `/usr/bin/arch`、`uname` | 强制使用原生 CPU 架构（Apple Silicon） | macOS |
| `iconutil` | 从 iconset 生成 `.icns` 应用图标（回退：PNG） | macOS |
| `osascript` | 显示应用启动器的错误消息 | macOS |
| 标准 shell 工具 | `mkdir`、`cp`、`cat`、`command` 等 | POSIX/macOS |

`BgRemover.command` 是随附的双击启动器（项目自有代码）。

## 6. 持续集成

在 `.github/workflows/pr-ci.yml`、`.github/workflows/ci.yml` 和
`.github/workflows/license-check.yml` 中定义。Pull request 运行轻量级
Ubuntu/Python 3.12 job；完整矩阵在 release 或手动触发时运行
Ubuntu + macOS、Python 3.10/3.12；license workflow 生成依赖/license
报告。

| 资源 | 用途 | 许可证 |
|-----------|-------|--------|
| `actions/checkout@v5` | 检出仓库 | MIT |
| `actions/setup-python@v6` | 设置 Python + Pip 缓存 | MIT |
| `actions/upload-artifact@v4` | 上传 license report artifacts | MIT |
| `actions/github-script@v7` | 在 pull request 上评论 license 摘要 | MIT |
| `pip-licenses` | 已安装软件包许可证的原始 dump | MIT |
| `requirements/constraints.txt` | 用于本地检查、CI、license report 和 App Bundle 的可复现依赖 snapshot | 项目文件 |
| 通过 `apt` 安装的 Qt 系统库（Linux） | 无头 Qt 运行时：`libegl1`、`libfontconfig1`、`libxkbcommon0`、`libdbus-1-3`、`libxcb-*` | 发行版打包，多种宽松/copyleft 许可证（Mesa、fontconfig、libxkbcommon、libxcb、dbus …） |

## 7. 项目自有资源

项目自有作品，受项目许可证保护
（GPL-3.0-or-later，参见 `LICENSE`）：

- **源代码**：可安装软件包 `bgremover/`、`tests/` 下的测试套件以及
  `scripts/` 下的项目脚本。
- **工具栏/标签页图标**：`bgremover/icons/*.png`（`ai`、`bg`、`brush`、
  `clear_sel`、`close`、`eraser`、`form`、`open`、`redo`、`restore`、
  `save`、`transparency`、`undo`、`wand`）。由 `make_tool_icon()`
  通过 `importlib.resources` 作为 package data 加载。
- **绘制的矢量图标**：当某个 PNG 缺失时，`make_tool_icon()` 用
  `QPainter` 以编程方式绘制图标（`_draw_*_icon` 函数）—— 无外部
  资源。
- **应用图标**：`BgRemover_icon.png`（macOS `.icns` 的来源）。
- **光标**：在运行时绘制（`make_wand_cursor`、`make_brush_cursor`、
  `make_eraser_cursor`）—— 无外部文件。

仓库中**未嵌入任何第三方源代码**（无 `vendor/` 或
`third_party/`）；外部功能完全通过上面列出的软件包获取。

## 8. 许可证兼容性（说明）

BgRemover 采用 **GPL-3.0-or-later**（`LICENSE`）。该选择由
**PyQt6** 决定：该绑定采用 GPL-v3 许可（或商业许可），因此作为整体
分发的应用程序 —— 尤其是打包后的 `BgRemover.app` —— 必须符合
GPL。其余运行时/AI 依赖（Pillow HPND、NumPy BSD、rembg MIT、
onnxruntime MIT、U²-Net Apache-2.0）均与 GPL-v3 兼容。

只有当把 PyQt6 替换为采用 LGPL-v3 许可的 **PySide6** 时，才可能采用
**宽松**许可模式（MIT/Apache-2.0）。

---

*维护提示：* 当 `pyproject.toml`、`requirements/constraints.txt`、
`.github/workflows/pr-ci.yml`、
`.github/workflows/ci.yml`、`.github/workflows/license-check.yml`、
`create_BgRemover_app.sh` 或 `bgremover/icons/` 下的 package data
发生变更时，请一并更新本文档。
