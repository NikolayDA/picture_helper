[Deutsch](../../../CHANGELOG.md) · [English](../en/CHANGELOG.md) · [Español](../es/CHANGELOG.md) · [Français](../fr/CHANGELOG.md) · [Українська](../uk/CHANGELOG.md) · **简体中文**

# Changelog

BgRemover 的所有值得注意的变更都记录在本文件中。
其格式参照
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/)；本项目
遵循[语义化版本](https://semver.org/lang/de/)。

## [Unreleased]（未发布）

### 新增

- **可复现的依赖 snapshot**（`requirements/constraints.txt`）。
  Makefile、license workflow 和 macOS App 构建会使用同一份已提交的
  constraints，用于测试、CI、license 和 App Bundle 安装。
- **本地测试环境 doctor**（`make doctor`、
  `scripts/check_test_env.py`）。在本地运行深入 pytest 后才失败之前，
  先检查 Python 版本、`[test]` 依赖、非 editable 包安装、
  `bgremover` console script 以及 Qt `offscreen`。
- **应用启动的 CI 冒烟测试**（`tests/test_app_smoke.py`）。现有的 UI
  测试通过 `-m 'not ui'` 被排除在 CI 之外，因此 CI 从未检查应用是否
  能够完整启动——正是这个缺口让 macOS 启动故障溜了过去。新增测试不带
  `ui` 标记（因此会在 CI 中运行）：`python -m bgremover` 和
  console-script `bgremover` 从一个中性的工作目录完整启动（新的自检
  钩子 `BGREMOVER_SMOKE_TEST` 在第一个事件循环周期后以退出码 0
  结束）；检查 Qt 插件配置产出有效路径；
  对启动脚本（`create_BgRemover_app.sh`、`BgRemover.command`、
  `diagnose_mac.sh`）以及打包进 App 包的启动器进行 shell 语法检查。
  为此在 Linux CI job 中安装 `zsh`。

### 变更

- **继续模块化 MainWindow。** “最近打开”的持久化和菜单语义现在位于
  `bgremover/recent_files.py`；`MainWindow` 只负责委托加载、状态消息和
  文件菜单集成。
- **从 `MainWindow` 中抽出菜单/action 构建。**
  `bgremover/menu_actions.py` 负责菜单栏、`QAction`、快捷键和最近文件
  子菜单；`MainWindow` 只传入领域回调。
- **从 `MainWindow` 中抽出右侧标签面板。**
  `bgremover/right_panel.py` 负责选择、背景、变换和形状标签页，
  包括滑块、spinbox 和面板按钮；`MainWindow` 只传入画布回调。

### 修复

- **将 release/changelog 链接修正为真实存在的 ref。** `[Unreleased]`
  现在从 `v2.1.0` 开始比较；由于仓库中没有历史 `v2.0.0` 标签，
  `[2.1.0]` 使用已记录的 2.0.0 release commit 作为比较基点。
- **App 包：setup 中的 `bgremover` 检测不再依赖工作目录。**
  `create_BgRemover_app.sh` 把 venv 判定为「就绪」，尽管 `bgremover`
  并未安装在其中：`has_deps` 检查在项目目录下以该 `cwd` 运行，而
  Python 会自动把当前目录加到 `sys.path[0]` —— 于是
  `import bgremover` 找到的是仓库的 `bgremover/` **源码目录**，而非
  venv 中的真正安装。App 启动器以不同的 `cwd` 启动，看不到该源码
  目录，因此报告「venv 中缺少 bgremover 包」。`has_deps` 与最终
  完整性检查现在都从 `$HOME` 运行（子 shell `cd "$HOME"`），因而与
  启动器检查的是同一现实；若包缺失，则触发 pip 安装快速路径。
  `diagnose_mac.sh` 同样从 `$HOME` 测试，并额外显示 App venv 的
  `pip show bgremover`（与 cwd 无关地证明包是否/安装到何处）。
- **macOS 启动路径恢复可用。** 在包切分（第 5 轮）之后，
  `BgRemover.command` 仍在寻找已不存在的 `BgRemover.py` 并以「未
  找到」中止；德语版 `INSTALL_MAC.md` 以及 `INSTALL_LINUX.md` 和
  `README.md` 的 i18n 版本也仍保留了部分旧命令（第 5 轮的步骤
  15 在 glob 中漏掉了德语 `INSTALL_MAC.md` 以及 i18n 安装文档，
  并且 i18n 的 `.desktop` 片段里还遗留有
  `Exec=python3 /路径/.../BgRemover.py`）。后果：在 macOS 上三条
  已记录的启动路径（App 包、双击 `.command`、终端）没有一条能
  可靠使用。`BgRemover.command` 现在通过 `python3 -m bgremover`
  启动，并预先检查 `import bgremover`（否则会输出指向
  `create_BgRemover_app.sh` 的明确提示）。INSTALL_MAC 及所有
  i18n 文档反映当前的包模型（包括把包以非 editable 方式安装到
  App venv，以及通过 `importlib.resources` 解析资源）。
- **`create_BgRemover_app.sh`：现有 venv 可被干净迁移。** 来自单体
  时代的 venv（已安装 PyQt6/Pillow/numpy，但显然还没有 `bgremover`）
  会被错误地视为「ready」，因为 setup 检查 `has_deps` 没有测试
  `bgremover`。重新运行时，包安装因此被跳过——随后应用启动器在运行
  时报告「venv 中缺少 bgremover 包」。该检查现在也包括
  `import bgremover`；此外还有快速路径：若 App venv 已具备
  PyQt6/Pillow/numpy，则仅追加 `pip install ".[ai]"`（数秒），而
  不必带着所有依赖重新构建 venv（数分钟）。

### 更改

- **从 `ImageCanvas` 中提取纯图像操作。** `bgremover/image_ops.py`
  现在以不依赖 Qt 的 PIL/NumPy 函数承载背景移除/替换、保存、旋转、
  翻转、圆角和 crop mask。`ImageCanvas` 继续负责 UI 状态、undo/redo、
  signals 与 overlays；`tests/test_image_ops.py` 会在没有
  `QApplication` 的情况下直接检查像素操作。
- **Recommendations 文档更新到当前状态。** `RECOMMENDATIONS.md` 及其
  i18n 版本现在包含第 6 轮状态块，记录最近的 PR 系列（#70、#72–#78），
  并明确说明旧的单体分析属于历史上下文。
  `tests/test_recommendations_docs.py` 会保护该状态块。
- **同步资源文档。** `RESOURCES.md` 及其 i18n 版本现在反映包布局
  （`bgremover/` 而非 `BgRemover.py`）、`bgremover/icons/` 下的
  package data、可复现 constraints snapshot，以及 PR/full/license
  workflows。新增静态测试防止这些引用再次过期。
- **`make pr-check` 让本地 PR 检查更稳健。** 该 target 会重新安装带
  `[test]` 的包，运行 doctor，然后启动 `ruff`、`mypy` 和 `pytest`。
  Makefile 会自动找到 `.venv/bin/python`，否则回退到
  `python`/`python3`；GitHub PR CI 和 Full CI 使用同一个 target。
  共享的 Qt 插件配置会在需要时把 platform plugins 暂存到系统临时目录，
  避免 macOS 本地 headless 运行因项目路径中的 Qt 插件列表问题而失败。
- **新增轻量级 PR CI，并同步测试文档。** Pull Request 现在会运行低成本的
  Ubuntu/Python 3.12 workflow（`make pr-check`）；完整的 Linux/macOS
  矩阵保留给 release 和手动运行。测试 workflow 使用非 editable 安装，
  让 app smoke test 从外部 `cwd` 检查真实安装后的包。`README`、
  i18n README、`TESTING.md` 和 `Makefile` 现在描述同一套流程。
- **单体 → 包（第 5 轮）。** 单文件 `BgRemover.py`（3026 行）已拆分为
  可安装包 `bgremover/`（14 个模块：`constants`、`image_utils`、
  `icons`、`theme`、`workers`、`crop`、`canvas`、`widgets`、
  `settings_dialog`、`logging_config`、`main_window`、`app`、
  `__main__`、`__init__`）。通过 `python -m bgremover` 或
  console-script `bgremover` 启动；旧的 `python BgRemover.py` 形式被
  无替代地移除。`BgRemover.py` 已删除。以 **13 个机械步骤**完成，每一
  步都以绿色测试 oracle 为闸门（140 unit + 16 UI 测试、ruff、mypy）。
  唯一有意的、行为中立的代码变更：`make_tool_icon` 现在通过
  `importlib.resources` 从包数据（`bgremover/icons/`）解析图标，取代
  `__file__`/`sys.argv`/`cwd` —— 契约不变。`pyproject.toml`、
  `Makefile`、CI workflow 与 macOS 构建脚本
  （`create_BgRemover_app.sh`）在同一次切分中同步跟进；venv 以非
  editable 模式安装本包（含 package-data），因而应用不依赖项目目录。
- `BgRemover.py` 中的过渡再导出（B 阶段）与测试中所有的 `BgRemover`
  导入在最后一步被切换到包上。

## [2.1.0] – 2026-05-19

### 已更改

- 将五个 `ImageCanvas` 方法（`apply_round_corners`、`apply_rotate`、
  `apply_flip`、`start_crop_circle`、`start_crop_ratio`）的“未加载
  图像”提前返回守卫合并到装饰器 `@_requires_image` 中——此前逐字节
  相同的代码块消失；行为不变（由现有测试套件保护）。
- 后台 worker `AIWorker` 和 `ImageLoadWorker` 现共用基类 `_Worker`，
  封装相同的 `try/except → logger.exception → error.emit` 流程；
  子类仅实现 `_work()`。`RembgWarmupWorker` 有意保持独立（无 `error`
  信号，`finished` 始终在 `finally` 中）。
- 版本切割 **2.1.0**：`pyproject.toml` 和 `BgRemover.py` 中的
  `__version__` 回退提升至 `2.1.0`；此前归集在 `[Unreleased]` 下的
  更改（#48/#52/#53、INSTALL_LINUX、第 3/4 轮）由此标注为 2.1.0。

### 文档

- 补充了 Linux 安装说明（`INSTALL_LINUX.md`）：
  各发行版的系统软件包（apt/dnf/pacman）、venv 设置、
  启动脚本或 `.desktop` 条目以及故障排除；并在 README 中
  链接。包括针对 Raspberry Pi OS（桌面版）的尤其简单的方式，
  无需 venv/pip（PyQt6/Pillow/numpy 作为系统软件包通过 `apt` 安装），并附带
  可选的 AI 加装步骤。

## [2.0.0] – 2026-05-17

首个已记录的 2.0.0 release 状态。仓库中没有历史 `v2.0.0` Git 标签。

### 功能

- 通过 `rembg` 实现 AI 背景移除（可选的 `ai` extra），含
  后台预热，使首次点击不被阻塞。
- 选区工具：魔棒（带容差滑块的向量化 Flood-Fill）、
  画笔、橡皮擦和多边形套索；Shift/Ctrl
  用于加选或减选。
- 将背景设为透明或用颜色替换。
- 变换：旋转（90° 步长和任意角度）、镜像翻转、
  圆角处理、带三分法网格的多种比例裁剪。
- 带撤销/重做的历史记录（工具栏按钮），并可通过
  浮动历史弹窗跳转到任意此前的步骤。
- 拖放以及“最近打开”（10 个条目），两者均通过
  异步加载 Worker——不会冻结 UI。
- 保存为 PNG、JPEG、WebP 或 TIFF。
- 通过 `QSettings` 持久化设置（默认目录、首选
  文件格式）。
- macOS 应用程序包构建（`create_BgRemover_app.sh`），含隔离的
  venv、Apple Silicon 处理和图标设置；支持 Python
  3.10–3.15。

### 稳定性与质量

- 加固了 Worker 线程（Worker 不会过早被 GC，
  在 `closeEvent` 中干净地关闭线程，AI 竞态通过单调的
  画布版本计数器处理）。
- 加载时的图像尺寸限制（40 MP）和解压缩炸弹防护。
- 内存受限的撤销栈（256 MB），带 O(1) 字节跟踪。
- 与平台无关的日志路径（应用数据目录中的 `bgremover.log`）。
- 108 项测试；`ruff` 和 `mypy` 作为 CI 步骤；CI 在 Ubuntu 和 macOS 上
  以 Python 3.10 和 3.12 运行。
- `__version__` 从包元数据中读取（单一来源）；
  版本号显示在窗口标题中。

### 文档与许可证

- 许可证 **GPL-3.0-or-later**（`LICENSE`）；这是由
  采用 GPL 许可的 PyQt6 绑定决定的。
- `RESOURCES.md`（所有库/工具/资源及许可证）、
  `LICENSES.md` 以及自动化的许可证/合规工作流。
- 带有架构、已知限制和安装
  说明的 README；详细的 `INSTALL_MAC.md`。

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/NikolayDA/picture_helper/compare/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1...v2.1.0
[2.0.0]: https://github.com/NikolayDA/picture_helper/tree/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1
