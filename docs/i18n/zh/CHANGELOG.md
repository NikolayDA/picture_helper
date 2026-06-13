[Deutsch](../../../CHANGELOG.md) · [English](../en/CHANGELOG.md) · [Español](../es/CHANGELOG.md) · [Français](../fr/CHANGELOG.md) · [Українська](../uk/CHANGELOG.md) · **简体中文**

# Changelog

BgRemover 的所有值得注意的变更都记录在本文件中。
其格式参照
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/)；本项目
遵循[语义化版本](https://semver.org/lang/de/)。

## [Unreleased]

### 新增

- **图像处理流水线性能基准测试。** `scripts/benchmark.py` 通过真实的
  `image_ops` 路径测量每种输出格式（PNG/JPEG/WebP/TIFF）的处理时间，将带日期的
  结果保存到 `benchmarks/results/`，并比较相邻的运行；退化超过 10% 的格式会被标记，
  并可选地作为 GitHub issue 上报（`make bench` / `make bench-compare`）。
  每周一次的 CI 工作流（`.github/workflows/benchmark.yml`）在固定硬件上运行并比较，
  并将结果提交回仓库作为下一次的基线。

### 变更

- **更新依赖。** `idna` 升级到 3.15，`urllib3` 升级到 2.7.0；
  `LICENSES.md` 已与新的依赖快照同步。
- **固定构建后端以防范供应链 CVE。** `setuptools` 在 `pyproject.toml`
  （`[build-system]`）和 `requirements/constraints.txt` 中升级到 `>=78.1.1`
  （CVE-2024-6345 RCE、CVE-2025-47273 路径遍历），`wheel` 在 `constraints.txt`
  中升级到 `==0.46.2`（CVE-2026-24049）。这样隔离的 wheel 构建就不会再拉取存在
  漏洞的构建工具（#200、#201）。
- **在 CI/开发环境中将 pip 升级到已修复版本。** 使用 pip 安装的 CI 工作流
  （`ci.yml`、`pr-ci.yml`、`ui-nightly.yml`、`benchmark.yml`、`license-check.yml`）
  和 Web SessionStart 钩子在安装前将 `pip` 升级到 `>=26.1.2`，开发安装文档
  （`README.md`/`INSTALL_MAC.md`/`INSTALL_LINUX.md`）同样如此。修复了
  `pip-audit` 报告的路径遍历、符号链接和模块劫持 CVE 批次；pip 本身就是安装
  工具，因此无法通过 `constraints.txt` 固定（#202）。
- **macOS 诊断脚本默认遮蔽敏感路径。** `diagnose_mac.sh` 现在默认将 `$HOME`
  替换为 `~`，缩短其余 `/Users/<name>` 路径，并以路径经过遮蔽的错误摘要取代
  原先输出的日志原文最后 40 行——因此输出可以放心附加到错误报告中。新的
  `--include-raw-logs` 选项提供完整诊断（含原始日志）；新增的 shell 测试
  （`tests/test_diagnose_mac.py`）确保主目录和图片路径不会出现在默认输出
  中（#185）。

### 修复

- **读入前限制输入文件大小。** `open_validated_image` 现在在将文件内容完整读入
  内存**之前**，先通过 `os.fstat()` 对照一个有文档说明的字节上限
  （`_MAX_INPUT_FILE_BYTES`，512 MB）检查输入文件；额外的有界 `read()` 可防范
  异常的文件对象，以及 `fstat()` 与 `read()` 之间的大小变化（TOCTOU）。提示信息
  会区分文件大小（MB）与百万像素上限（MP）。同步和异步加载路径共用同一检查；
  原有的百万像素上限与 TOCTOU 保护均保持不变（#230）。
- **复用 rembg 推理 session。** warmup 现在通过 `new_session()` 恰好创建一个
  rembg/ONNX session 并在模块级缓存；之后每次 `AIWorker` 都将其传给
  `remove(..., session=...)`，而不是重新初始化模型。该创建通过 double-checked
  locking 保证线程安全，并在多次 AI 调用中最多执行一次；初始化失败仍会通过
  worker 错误信号上报，且不会留下被误判为「就绪」的状态。误导性的注释（声称
  dummy `remove()` 会缓存 session）也一并修正（#229）。
- **`recent_files` 对损坏的设置具有健壮性。** `RecentFiles.paths()` 现在防御性地
  处理任意存储的原始类型：单个字符串仍作为一个条目，列表/元组按元素过滤为非空
  字符串，而其他任何值（如整数、`None`）都会得到空列表而非 `TypeError`。新增的
  `sanitize()` 在启动时将真正损坏的值清理后回写一次（并记录一条警告）；QSettings
  无害的单元素字符串保持不变。因此手动编辑或过时的 `recent_files` 值不再中断菜单
  或应用构建（#233）。

### 移除

## [2.3.0] – 2026-06-04


### 新增

- **测试覆盖率提高到 88%（第二轮，之前为 82%）。** 新增
  `tests/test_canvas_events.py`，覆盖 `canvas.py` 中此前未测的事件处理和控制
  逻辑：鼠标、键盘、滚轮、拖拽、魔棒结果流、工具设置、活动裁剪中的
  undo/redo/undo-to，以及未加载图片时的 guard 路径。`canvas.py` 从 64% 提升到
  99%，`fail_under` 从 80 提升到 86。
- **测试覆盖率提高到 82%（之前为 74%）。** 新的行为测试覆盖
  `tests/test_lasso.py`、`tests/test_canvas_crop.py`、`tests/test_viewport.py`、
  `tests/test_crop_overlay.py`、`tests/test_settings_schema.py` 和
  `tests/test_settings_dialog.py`。多个模块达到 100%，`canvas_crop.py` 达到
  98%，`fail_under` 从 68 提升到 80。
- **ANLEITUNG.md i18n。** 为德语用户指南新增五种译文：
  `docs/i18n/{en,es,fr,uk,zh}/ANLEITUNG.md`；`tests/test_i18n_docs.py` 的
  `DOC_NAMES` 现在包含 `"ANLEITUNG.md"`，每个 i18n 头部也说明
  `ANLEITUNG.pdf` 只从德语原文生成。
- **Soft-drift 测试 `tests/test_i18n_sync.py`。** 将 `CHANGELOG.md`、
  `INSTALL_MAC.md` 和 `INSTALL_LINUX.md` 的标题层级与代码块数量同德语原文
  对比；差异会生成可读警告，而不是让 CI 硬失败。
- **`bgremover/status_messages.py` – 集中 status 消息。** 将 `canvas.py`、
  `canvas_crop.py` 和 `main_window.py` 中用户可见的 status 字符串移入
  `StatusMessages`，作为未来本地化的准备。
- **支持英语的 runtime i18n。** 德语和英语可在运行时切换；设置对话框包含
  持久化语言选择器和重启提示，canvas、对话框和右侧面板的 UI 字符串通过
  集中翻译层处理。
- **工具键盘快捷键。** 编辑工具现在可以通过键盘切换；toolbar tooltip 和文档会列出
  各平台对应的快捷键。
- **Linux AppImage 打包。** release build 现在会生成 AppImage，作为 Linux
  最终用户的推荐路径，并包含打包脚本、CI 覆盖和安装说明。
- **Linux `.deb`、aarch64/Raspberry Pi 与 release workflow。** Linux 打包扩展了
  Debian 包、aarch64/Pi 支持以及对应的 release workflow。
- **引入 QSettings schema version。** 新增 `bgremover/settings_schema.py`，包含
  `SCHEMA_VERSION = 1` 和 `migrate(settings)`；`MainWindow.__init__` 在创建
  `QSettings` 后立即执行迁移。覆盖 downgrade 保护、损坏值和
  `tests/test_settings_schema.py` 中的相关测试。
- **`RembgWarmupWorker` runtime 测试。** `tests/test_workers.py` 与
  `tests/test_worker_controller.py` 新增测试，验证 warmup 总会发出 `finished`，
  且即使 `rembg_remove` 首次启动失败，thread lifecycle 也能完成。

### 变更

- 清理了文档和代码注释：从活文档中移除过时的 PR/轮次标记，更新
  macOS 安装说明，并将建议文档压缩为当前 review/roadmap 状态。
- 项目版本在包元数据、AppStream、许可证概览和 changelog 链接中提升
  到 2.3.0。

- **统一 docstring 语言。** `bgremover/image_ops.py`、
  `bgremover/recent_files.py` 和 `bgremover/worker_controller.py` 的 docstring
  从英文改为德文，与项目其他部分保持一致。
- **更新 Linux 包和语言设置的用户文档。** README、`INSTALL_LINUX.md` 和
  `ANLEITUNG.md` 现在将 AppImage/`.deb` 作为 Linux 最终用户的推荐路径，
  并记录持久化语言设置及重启提示；i18n 副本同步更新。
- **代码卫生汇总轮。** version fallback 读取 `pyproject.toml`，
  `_paint_brush` 显式接收 `additive`，`apply_remove`/`apply_replace` 只捕获
  预期错误，补充全局副作用与 QSettings 特例说明，`make clean` 清理更多
  构建产物，项目描述反映 macOS/Linux 支持。
- **魔棒选区不再冻结 UI。** Flood-fill 移入短生命周期 `QThread` 上的
  `FloodFillWorker`，并通过 `content_revision` 做 stale 检查；pan/zoom 保持
  响应，只有并行魔棒点击会用 status 消息阻止。
- **扩展 CI 测试矩阵。** Full CI 现在在 Ubuntu 和 macOS 上检查 Python 3.10、
  3.11、3.12 和 3.13。
- **`RembgWarmupWorker` 继承 `_Worker`。** 公共 boilerplate 移入基类并加入
  `_always_finished()` hook，保留 `finished` 合约，同时统一 logging、错误语义和
  `WorkerController` 类型注解。
- **Canvas 子模块使用公共 edit API。** `CanvasCrop` 和 `CanvasTransform` 使用
  `apply_edit(...)` 与 `ImageCanvas.current_tool`；多项 selection 操作改用
  `_requires_image`，空状态会一致地提示未加载图片。
- **精简包的公共 API。** 私有符号不再从 `bgremover` 顶层 re-export；需要这些
  符号的代码应从子模块导入。`logger`、`LOG_FILENAME`、`REMBG_AVAILABLE` 和
  `current_log_file` 保持公共；测试边缘 `MainWindow._recent_paths()` 被移除。

### 修复

- **`apply_remove`/`apply_replace` 不再吞掉真实 bug。** 窄过滤器会让
  `AttributeError`、`AssertionError` 等继续向上传播，同时仍把预期的 image/IO
  错误转为 status 消息。
- **同步加载路径使用与 worker 相同的保护。** `ImageCanvas.load_image` 现在调用
  `open_validated_image`，因此 drag & drop 中的恶意文件和不支持格式也会以干净的
  status 消息结束。
- **稳定 License Check。** `coverage` 固定在 `requirements/constraints.txt`
  (`==7.14.0`)，避免上游 release 造成 `LICENSES.md` drift 比较失败。
- **License Check 加强 timezone drift 防护。** `actions/checkout` 使用
  `fetch-depth: 0`，日期计算使用 `TZ=UTC` 和 `--date=short-local`，从而找到真实
  edit commit 并确定性地格式化日期。

### 移除

- **移除 Canvas、Lasso 和 MainWindow 中的死代码。** 删除 `ImageCanvas._version`、
  `CanvasLasso.close_to_mask` 和 `MainWindow._btn_grp`。

## [2.2.0] – 2026-05-25

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
- **从 `MainWindow` 中封装 worker 编排。**
  `bgremover/worker_controller.py` 现在负责加载、AI 和 warmup 线程，
  包括强 worker 引用、`deleteLater` 连接和统一 shutdown。

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

### 移除

- 删除了未再使用的 stylesheet 常量 `BTN_STYLE` 和 `GRP_STYLE`。

### 修复

- `save_image()` 现在会将 I/O 失败报告为状态消息，而不是让其未处理地
  继续传播。

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

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/5fa8025dbabd997484e4739b1f547e9c59aed319...HEAD
[2.3.0]: https://github.com/NikolayDA/picture_helper/compare/da7186869e63cf9612897b31d80a84c1cc409062...5fa8025dbabd997484e4739b1f547e9c59aed319
[2.2.0]: https://github.com/NikolayDA/picture_helper/compare/4f4bfc2a3adf154d86d4aa2f46b0149bb863bc66...da7186869e63cf9612897b31d80a84c1cc409062
[2.1.0]: https://github.com/NikolayDA/picture_helper/compare/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1...4f4bfc2a3adf154d86d4aa2f46b0149bb863bc66
[2.0.0]: https://github.com/NikolayDA/picture_helper/tree/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1
