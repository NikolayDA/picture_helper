# 历史工作日志：第 1-5 轮建议

冻结时间：2026-05-24，提交 1cf8461。
当前状态：../i18n/zh/RECOMMENDATIONS.md。

---

[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · **简体中文**

# 代码分析与评级建议：BgRemover

## 评级标准

| 符号 | 优先级 | 含义 |
|--------|-----------|-----------|
| 🔴 | 严重 | 必须修复——会导致错误、崩溃或不一致 |
| 🟠 | 高 | 应尽快修复——严重影响可靠性或可维护性 |
| 🟡 | 中 | 建议——提升代码质量、可读性或可测试性 |
| 🟢 | 低 | 可选——打磨、补充性改进 |

---

## 当前状态（第 6 轮）

本文件有意保留单体阶段的历史分析。当前代码库已经是 `bgremover/`
包；`BgRemover.py` 已删除。包拆分之后的最新 PR 系列在这里作为简短
工作日志记录：

| # | 包 | 状态 |
|---|----|------|
| 1 | AI 状态修订：在中间编辑后丢弃迟到的 `rembg` 结果 | ✅ #72 |
| 2 | 轻量级 PR CI + 测试文档同步 | ✅ #73 |
| 3 | CI 应用 smoke test 与启动脚本语法检查 | ✅ #70 |
| 4 | Release/changelog hygiene | ✅ #74/#75 |
| 5 | 更稳健的本地测试环境（`make doctor`、`make pr-check`） | ✅ #76 |
| 6 | 依赖/build 可复现性（`requirements/constraints.txt`） | ✅ #77 |
| 7 | 资源文档与包布局、constraints 和 workflows 同步 | ✅ #78 |
| 8 | Recommendations/roadmap 文档更新到当前状态 | ✅ 本 PR |

静态测试 `tests/test_recommendations_docs.py` 会防止本节再次过期；
资源清单另由 `tests/test_resource_docs.py` 保护。

---

## 按优先级汇总

| # | 建议 | 优先级 | 工作量 |
|---|-----------|-----------|---------|
| 1 | ~~类型提示中的 Python 版本冲突~~ | ✅ 已修复 | – |
| 2 | ~~rembg 导入时过宽的异常捕获~~ | ✅ 已修复 | – |
| 3 | ~~Worker 线程中的竞态条件~~ | ✅ 已修复 | – |
| 4 | ~~加载时的图像尺寸校验~~ | ✅ 已修复 | – |
| 5 | ~~撤销栈的内存占用~~ | ✅ 已修复 | – |
| 6 | ~~拆分上帝类~~ | ✅ 已修复 | – |
| 7 | ~~重构过长的方法~~ | ✅ 已修复 | – |
| 8 | ~~替换魔法数字~~ | ✅ 已修复 | – |
| 9 | ~~针对线程场景的测试~~ | ✅ 已修复 | – |
| 10 | ~~补充返回值类型提示~~ | ✅ 已修复 | – |
| 11 | ~~补充 docstring~~ | ✅ 已修复 | – |
| 12 | ~~日志文件路径与平台无关~~ | ✅ 已修复 | – |
| 13 | ~~去除线程样板代码的重复~~ | ✅ 已修复 | – |

---

## 详细建议

### ✅ 1. 类型提示中的 Python 版本冲突 *(已修复)*

**文件**：`pyproject.toml`

`requires-python` 提升到 `>=3.10`，`ruff target-version` 更新为 `py310`。这样代码中使用的 `X | Y` 语法（PEP 604）就被声明的最低要求所覆盖。

---

### ✅ 2. rembg 导入时过宽的异常捕获 *(已修复)*

**文件**：`BgRemover.py`（第 41 行）

`except BaseException:` 替换为 `except (ImportError, RuntimeError, OSError, SystemExit):`。`KeyboardInterrupt` 和其他关键信号不再被捕获。`SystemExit` 仍被显式包含，因为已知的某些 rembg/onnxruntime 版本在导入时可能会触发它。

---

### ✅ 3. Worker 线程中的竞态条件 *(已修复)*

**文件**：`BgRemover.py`

- `MainWindow` 中新增 `_launch_worker()` 辅助方法，封装了相同的线程样板代码（之前被复制了三遍）。所有三个流程（图像加载、AI、预热）现在都使用它。
- `_on_ai_done()` 中的过期检查现在使用 `_canvas._version`（单调的整数计数器，每次在 `apply_loaded_image()` 中切换图像时递增），取代了脆弱的 `is` 对象身份比较。`MainWindow` 中的 `_ai_input_version` 在 AI 启动时保存该值。

---

### ✅ 4. 加载时缺少图像尺寸校验 *(已修复)*

**文件**：`BgRemover.py`

引入常量 `_MAX_MEGAPIXELS = 100`。在惰性 `Image.open()` 之后于两处进行检查：
- `ImageLoadWorker.run()`：发出带错误消息的 `error` 信号（文件对话框路径）
- `ImageCanvas.load_image()`：发出 `statusMsg` 并中止（拖放路径）

---

### ✅ 5. 撤销栈的内存占用过高 *(已修复)*

**文件**：`BgRemover.py`

引入常量 `_UNDO_MEMORY_LIMIT = 256 MB`。撤销栈不再有硬性的 `maxlen`——而是在每次 push 之后计算总大小（按每个 RGBA 图像 `width × height × 4` 字节估算），只要超出上限就移除最旧的条目。

---

### ✅ 6. 拆分上帝类 *(已修复)*

**文件**：`BgRemover.py`

`_build_right_panel()` 中的 6 个嵌套辅助函数（`sec`、`lbl`、`hdivider`、`scroll_tab`、`btn`、`slider_row`）被提取为 `MainWindow` 的 `@staticmethod` 类方法：`_make_section`、`_make_label`、`_make_hdivider`、`_make_scroll_tab`、`_make_panel_btn`、`_make_slider`。`_TAB_STYLE` 被外移为类属性。

---

### ✅ 7. 重构过长的方法 *(已修复)*

**文件**：`BgRemover.py`

`make_tool_icon()` 中的 8 个图标绘制分支（175 行，if-elif 级联）被提取为独立的模块函数：`_draw_wand_icon`、`_draw_brush_icon`、`_draw_eraser_icon`、`_draw_ai_icon`、`_draw_open_icon`、`_draw_save_icon`、`_draw_undo_icon`、`_draw_restore_icon`。`make_tool_icon()` 现在是一个基于 `dict` 的精简分发器。

---

### ✅ 8. 用具名常量替换魔法数字 *(已修复)*

**文件**：`BgRemover.py`

模块头部新增常量块：
- UI 布局：`_TOOLBAR_WIDTH`、`_TOOLBAR_BTN_SIZE`、`_TOOLBAR_ICON_SIZE`、`_RIGHT_PANEL_WIDTH`、`_CROP_BAR_HEIGHT`、`_HISTORY_LIST_H`、`_COLOR_BTN_SIZE`、`_TAB_ICON_PX`、`_WINDOW_MIN_W/H`
- 画布默认值：`_DEFAULT_TOLERANCE`、`_DEFAULT_BRUSH_RADIUS`、`_ZOOM_FACTOR`
- 叠加层颜色：`_OVERLAY_COLOR`

代码中所有使用处都已改用这些常量。

---

### ✅ 9. 针对 Worker 错误路径的测试 *(已修复)*

**文件**：`tests/test_workers.py`（新增，9 项测试）

新增测试：
- `ImageLoadWorker`：文件缺失、文件损坏、图像过大（通过 Mock）
- `ImageLoadWorker`：正常情况（预期无错误）
- `ImageCanvas.load_image()`：图像过大（拖放路径）
- `AIWorker`：`rembg_remove` 异常时的错误信号、成功情况（通过 Mock）
- 画布 `_version` 计数器：在 `apply_loaded_image` 时递增，在撤销时不变

---

### ✅ 10. 补充返回值类型提示 *(已修复)*

**文件**：`BgRemover.py`

77 个没有返回值注解的函数和方法被加上了 `-> None`（或具体类型）。此外还将 `QFont` 添加到了 PyQt6 导入中（`_text_font() -> QFont` 需要它）。

---

### ✅ 11. 辅助方法缺少 docstring *(已修复)*

**文件**：`BgRemover.py`

为 `_make_label`、`_make_hdivider`、`_make_panel_btn` 和 `_make_slider` 补充了单行 docstring。光标生成器（`make_wand_cursor`、`make_brush_cursor`、`make_eraser_cursor`）已经有 docstring。

---

### ✅ 12. 让日志文件路径与平台无关 *(已修复)*

**文件**：`BgRemover.py`

将 `QStandardPaths` 添加到 PyQt6 导入中。日志路径从 `Path.home() / ".bgremover.log"` 改为 `QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) / "bgremover.log"`（Linux：`~/.local/share/BgRemover/`，macOS：`~/Library/Application Support/BgRemover/`）。

---

### ✅ 13. 去除重复的线程样板代码 *(已修复)*

**文件**：`BgRemover.py`

`_launch_worker()` 辅助方法已作为修复 #3（竞态条件）的一部分引入。从那时起，所有三个 Worker 流程（图像加载、AI、预热）都使用它。

---

## 第 2 轮 – 后续评审（代码、测试、文档、许可证）

> 对第 1 轮的更正：**#6（上帝类）**和 **#8（魔法
> 数字）**两点曾被标记为 ✅，但实际上只_部分_
> 成立（`MainWindow`/`_build_right_panel` 仍约 300 行；不少
> 样式表/布局数字仍内联）。第 2 轮处理了
> 剩余的问题。

| # | 建议 | 优先级 | 状态 |
|---|-----------|-----------|--------|
| R1 | 日志设置：在 `QApplication` 之前调用，目录未创建 | 🔴 | ✅ 已修复 |
| R2 | Flood-Fill 阻塞 UI；100-MP 限制过高 | 🟠 | ✅ 已修复 |
| R3 | 拖放 / “最近打开”绕过了异步 Worker | 🟠 | ✅ 已修复 |
| R4 | 封装被破坏（`_pil`/`_version`/`_img_item`/`_cx…`） | 🟡 | ✅ 已修复 |
| R5 | `undo_to` 不一致（不可重做） | 🟡 | ✅ 已修复 |
| R6 | `MainWindow` 上帝对象 / `_build_right_panel` | 🟡 | ✅ 已修复 |
| R7 | CI 中没有类型检查 | 🟡 | ✅ 已修复 |
| R8 | `pyproject` 全局忽略了 `F401` | 🟢 | ✅ 已修复 |
| R9 | `make_tool_icon`：在循环中导入，静默的 `except` | 🟢 | ✅ 已修复 |
| R10 | `_apply_pil` 每个操作都 O(n) 累加撤销栈 | 🟢 | ✅ 已修复 |
| R11 | 没有解压缩炸弹防护 | 🟡 | ✅ 已修复 |
| R12 | 测试缺口（撤销驱逐、几何、套索、拖放） | 🔴/🟠 | ✅ 已修复 |
| R13 | 文档：错误的 Python 版本、缺少许可证 | 🟠 | ✅ 已修复 |

**R1** — 日志被外移到 `_setup_logging()`；在 `__main__` 中
**在** `QApplication` + `setApplicationName/​setOrganizationName`
**之后**调用。目标目录通过 `mkdir(parents=True, exist_ok=True)`
创建（回退到 `~/.bgremover`）。

**R2** — `flood_fill` 已向量化（用少量
NumPy 操作生成相似度蒙版，随后做区域增长）；`_MAX_MEGAPIXELS` 从 100 → 40。

**R3** — 新增信号 `ImageCanvas.loadRequested`；`dropEvent` 和
`_open_recent` 现在都走 `_load_image_async`（Worker 路径）。
`load_image` 作为用于测试/拖放回退的同步路径保留。

**R4** — 公开访问器：`ImageCanvas.image/has_image/version/
fit_to_view()` 和 `CropOverlayItem.top_left/size`。`MainWindow` 和
`ImageCanvas` 不再跨类访问私有成员。

**R5** — `undo_to()` 的行为如同多次 `undo()`（每一步
都进入重做栈），因此可通过 `redo()` 重做；此外
还有与 `undo()` 相同的裁剪保护。

**R6** — `_build_right_panel()` 是一个精简的分发器；四个
`_build_tab_selection/background/transform/shape` 构建器各添加一个
标签（标签索引来自 `addTab()`）。

**R7** — 在 `pyproject.toml` 中配置了 `mypy`（务实做法：通过
`disable_error_code` 静默 Qt 覆写和 tuple-lambda 噪声）并
作为 CI 步骤补充。

**R8/R9/R10/R11** — 移除了 `F401` 忽略，删除了两个未使用的导入；
`make_tool_icon` 使用模块级 `Image` 导入，并用 `logger.debug`
记录失败；持续累加的撤销字节总和 `_undo_bytes`
（O(1)）；`Image.MAX_IMAGE_PIXELS` 与 `_MAX_MEGAPIXELS` 关联。

**R12** — 新增测试（81 → 108）：撤销内存上限驱逐 +
字节跟踪、`tests/test_geometry.py`（旋转/翻转/圆角/裁剪）、
套索 + `_paint_brush` + `apply_remove/replace` 成功情况、
`tests/test_drop_and_history.py`（异步拖放、`undo_to`-重做）、
`_setup_logging` 目录创建。

**R13** — README/INSTALL_MAC：Python **3.10+**；README 增加了架构、
已知限制、正确的日志路径和**许可证章节**；
补充了 `LICENSE`（GPL-3.0）；`pyproject.toml` 增加了
`license`/`authors`/`urls`/`classifiers`。许可证建议：
**GPL-3.0-or-later**（符合 PyQt6 的 GPL 义务；只有
换用 PySide6 才可能采用宽松许可）。

---

## 第 3 轮 – 功能扩展之前

> 两轮优化已完成；第 3 轮收集在计划中的功能扩展之前值得做的低风险
> 清理。建议 **#1（单体 → 包）** 被有意推迟：优先级高，但工作量/
> 风险也高，且与已记录的“单文件”设计决策相冲突——属于单独的决策。
> 状态列引用实现该项的 PR。

| # | 建议 | 优先级 | 工作量 | 状态 |
|---|-----------|-----------|---------|--------|
| 1 | 单体 → 包（`bgremover/` 含模块） | 🟠 高 | 高 | ✅ 已解决（第 5 轮） |
| 2 | ~~`save_image()` 无错误处理~~ | 🟡 中 | 低 | ✅ #48 |
| 3 | ~~`undo/redo/undo_to/restore_original/_apply_pil` 中的状态重复~~ | 🟡 中 | 低 | ✅ #52 |
| 4 | ~~分散的内联样式表，无主题模块~~ | 🟡 中 | 中 | ✅ #53 |
| 5 | ~~缺少用于 Claude Code on the web 的 SessionStart 钩子~~ | 🟡 中 | 低 | ✅ #51 |
| 6 | ~~重复的“未加载图像”守卫（约 8 处）~~ | 🟢 低 | 低 | ✅ 2.1.0 |
| 7 | ~~Worker 样板代码（try/except/log/emit）→ 基类~~ | 🟢 低 | 低 | ✅ 2.1.0 |
| 8 | ~~维护 `CHANGELOG [Unreleased]`~~ | 🟢 低 | 低 | ✅ 持续 |
| 9 | ~~`mypy` 过于宽松（7 个禁用代码）~~ | 🟢 低 | 中 | ✅ 第 4 轮 #4 |

**#1** — `BgRemover.py` 仍是单个文件（约 3000 行：辅助函数、worker、
画布、界面、对话框、日志、main）。它是功能增长的最大杠杆，但风险
最高（风险：高），且与已记录的单文件决策相冲突。**未完成 — 有意
推迟**，需要单独的设计决策。

→ **已在第 5 轮解决**（设计决策：干净的包拆分 – 见下文）。

**#2** — 已在 **PR #48** 中修复：`save_image()` 返回 `bool` 并将写入
操作包裹在 `try/except` 中（日志 + 状态消息），与
`apply_remove/replace` 一致；“另存为…”不再把失败的路径记为快速
保存目标（`BgRemover.py:1080–1113`）。

**#3** — 已在 **PR #52** 中修复（最初为 #49，在合并冲突后干净地重新
创建）：相同的图像状态代码块合并到辅助方法 `_set_image_state()` /
`_emit_history()`；行为不变（`BgRemover.py:877`、`:891`）。

**#4** — 已在 **PR #53** 中修复（最初为 #50）：集中的 `_Theme` 颜色
调色板，被复用的模板引用（逐字节验证，218 个样式表，无视觉差异）。
移除了无用常量 `BTN_STYLE`/`GRP_STYLE`（`BgRemover.py:1547`）。

**#5** — 已在 **PR #51** 中修复：同步的 `SessionStart` 钩子
（`.claude/hooks/session-start.sh`，git 模式 100755）安装 Qt 系统库
+ 项目，并持久设置 `QT_QPA_PLATFORM=offscreen`；在
`.claude/settings.json` 中注册。

**#6** — **✅ 已完成（2.1.0）。** 五个相关 `ImageCanvas` 方法的
“未加载图像”提前返回已归并到装饰器 `@_requires_image` 中
（`bgremover/canvas.py`）。

**#7** — **✅ 已完成（2.1.0）。** `AIWorker` 和 `ImageLoadWorker`
共用基类 `_Worker`，它封装了
`try/except → logger.exception → error.emit` 流程
（`bgremover/workers.py`）；`RembgWarmupWorker` 有意保持独立。

**#8** — 已遵守：第 3 轮的 PR #48/#52/#53 各自维护
`CHANGELOG [Unreleased]` 章节；本条目还额外记录了第 3 轮本身。这是
持续的实践，而非单个 PR。

**#9** — **✅ 已完成（第 4 轮 #4）。** `disable_error_code` 已从
`pyproject.toml` 中完全移除——此前 8 个被禁用的错误类别现已全部
启用（详情见下方第 4 轮 #4）。

---

## 第 4 轮 – 现状评估与下一步

> 分析状态：`ruff` 干净，`mypy` 干净，**140 个测试通过**（16 个 UI
> 测试有意取消选择）。代码质量很高 – 因此第 4 轮优先确定
> **接下来具体该着手什么**，而非寻找新缺陷。

| # | 建议 | 优先级 | 工作量 | 状态 |
|---|------|--------|--------|------|
| 1 | ~~版本切割 2.1.0 + git 标签~~ | 🟠 高 | 低 | ✅ 已完成（标签于合并后） |
| 2 | ~~“未加载图像”守卫辅助（第 3 轮 #6）~~ | 🟢 低 | 低 | ✅ 已完成 |
| 3 | ~~Worker 基类（第 3 轮 #7）~~ | 🟢 低 | 低 | ✅ 已完成 |
| 4 | ~~逐步收紧 `mypy`（第 3 轮 #9）~~ | 🟢 低 | 中 | ✅ 已完成（全部 8 个 code 已启用） |
| 5 | 单体 → 包（第 3 轮 #1） | 🟠 高 | 高 | ✅ 已解决（第 5 轮） |

### ✅ 1. 版本切割 2.1.0 + git 标签 *(已完成)*

**本 PR 已完成：** `pyproject.toml` 和 `BgRemover.py` 的 `__version__`
回退提升至 `2.1.0`；`CHANGELOG.md`（+ i18n en/es/fr/uk/zh）的
`[Unreleased]` 块注明为 `[2.1.0] – 2026-05-19`，并新增一个空的
`[Unreleased]` 块。`git tag v2.1.0` **有意不**打在功能分支上；它应在
合并后打在 `main` 的合并提交上（见 PR 说明）。

**发现（备查）：** **此前不存在任何 git 标签**（`git tag -l` 为空），
尽管 CHANGELOG 声称有“首个公开打标签的发布 2.0.0”。自 2.0.0 起，
`[Unreleased]` 块已累积实质性变更（PR #48 保存错误处理、#52 状态
去重、#53 `_Theme`、INSTALL_LINUX 文档、#55 本地测试运行器），而
`pyproject.toml` 和 `__version__` 回退仍为 `2.0.0`。

### ✅ 2. “未加载图像”守卫辅助 *(已完成，第 3 轮 #6)*

五个 `ImageCanvas` 方法 `apply_round_corners`、`apply_rotate`、
`apply_flip`、`start_crop_circle`、`start_crop_ratio` 中逐字节相同的
提前返回 `if self._pil is None: self.statusMsg.emit("Kein Bild
geladen"); return` 已合并到装饰器 `@_requires_image`。行为不变
（140 个单元测试 + 16 个 UI 测试通过）。`MainWindow` 的三处
`has_image` 守卫有意保持内联：消息不同且存在依赖顺序的二次检查——
在那里归并弊大于利。

### ✅ 3. Worker 基类 *(已完成，第 3 轮 #7)*

`AIWorker` 和 `ImageLoadWorker` 现继承基类 `_Worker`，封装相同的
`try/except → logger.exception → error.emit` 流程；子类仅实现
`_work()`。`RembgWarmupWorker` 有意保持独立（无 `error` 信号，
`finished` 始终在 `finally` 中——契约不同）。

### ✅ 4. 逐步收紧 `mypy` *(第 3 轮 #9 / 第 4 轮 #4 – 已完成)*

**此前所有被禁用的错误类别现在均已启用。** 在单体 → 包的切分
（第 5 轮）之后，余下的六个 code 得以按文件逐一激活：

| Code | 之前 | 策略 |
|------|------|------|
| `arg-type` | 2 | 通过双重守卫 + 循环 `assert` 表达 `_pil`/`_arr` 不变式 |
| `attr-defined` | 2 | `setattr(thread, "_worker", ...)`；参数 `_Worker \| RembgWarmupWorker` |
| `assignment` | 4 | 明确的首次注解（`Image.Image`、`RankFilter`、`QMenu \| None`） |
| `func-returns-value` | 4 | UI lambda 元组 → 局部 `def` |
| `override` | 7 | 签名与 PyQt6 stubs 对齐（`QPainter \| None` 等） |
| `union-attr` | 67 | 缓存 status/menu bar 与 viewport；定点 assert |

在 `pyproject.toml` 中仅保留 `check_untyped_defs = false` 作为务实
的 Qt 噪声抑制（覆盖 Qt 覆写签名 event/option/widget）。

### 🟠 5. 单体 → 包 *(第 3 轮 #1，有意推迟)*

`BgRemover.py` 仍是 **3003 行** 的单文件。功能增长的最大杠杆，但风险
最高，且与已记录的单文件设计决策冲突。仍是一个深思熟虑的、独立的
架构决策 – 最迟在下一次较大功能扩展前重新评估。快速收益 #2/#3 已
略微缩小文件并为日后的拆分做准备。

→ **已在第 5 轮解决**（设计决策：干净的包拆分 – 见下文）。

---

## 第 5 轮 – 设计决策：单体 → 包（已解决）

> 第 3 轮 #1 与第 4 轮 #5 明确要求的“单独的设计决策”在此作出，
> 由此得到解决。已记录的单文件设计决策被**有意推翻**。

**决策。** `BgRemover.py`（3026 行）拆分为 Python 包 `bgremover/`。
模块：`constants`、`image_utils`、`icons`、`theme`、`workers`、
`crop`、`canvas`、`widgets`、`settings_dialog`、`logging_config`、
`main_window`、`app`、`__main__`、`__init__`。

**干净的包拆分（无兼容垫片）。** `BgRemover.py` 被彻底移除。应用
通过控制台脚本 `bgremover` **以及** `python -m bgremover` 启动。
此前的 `python -m bgremover` 模式被**有意废弃**；构建脚本
（`create_BgRemover_app.sh`、`BgRemover.command`）、`pyproject.toml`、
Makefile/CI、测试与文档（含 i18n）在同一次切分中一并迁移。

**理由。** 据第 3 轮 #1 / 第 4 轮 #5，单文件是功能增长的最大杠杆；
唯一的阻碍是已记录的单文件决策——在此被明确推翻。风险仍然高，但
由方法加以控制。

**方法。** 分阶段并设硬性闸门：**阶段 A**（准备——本 ADR +
布局/设计，不移动代码）→ **闸门**（捕获绿色基线：`ruff`/`mypy`
干净，**140 个单元测试 + 16 个 UI 测试通过**）→ **阶段 B**（纯
机械、逐字节一致的拆分；代码逐字移动，仅调整 import；测试保持
通过）。唯一有意的代码改动：`make_tool_icon` 中的资源解析
（用 `importlib.resources` 取代 `__file__`/`argv`/`cwd`），不改变
行为。

**顺序 / 前置工作。** 前置条件已满足：`git tag v2.1.0` 已设置
（在 PR #60 的合并处）并作为 GitHub 预发布发布——最后的纯单文件
状态由此标记（第 4 轮 #1）。标签落后 `main` HEAD 数个提交是维护者
可选的发布决策，与本次切分无关。

**有意安排在之后，而非之前。** mypy 的逐步收紧（第 4 轮 #4，
剩余 6 个 `disable_error_code`）在拆分**之后**进行——大规模移动
会使按文件的类型进展失效。内部清理（guard/worker 合并）同样不在
本次切分范围内。

**状态影响。** 第 3 轮 #1 与第 4 轮 #5 由此决策**已解决**；相应
表格的状态列已据此更新。

**B 阶段完成。** 机械式拆分已落地（13 个步骤，每一步都以绿色 oracle
为闸门：`make test` 140、`make ui` 16、`make type`、`make lint`；两个
入口 `python -m bgremover` 和 `bgremover` 均稳定启动）。`BgRemover.py`
已删除。包由 `bgremover/` 下的 14 个模块组成；图标作为 `package-data`
（`bgremover/icons/`）随包发布。唯一有意的代码变更仍是承诺的那一项：
在 `make_tool_icon` 中通过 `importlib.resources` 解析资源（契约不变）。
构建脚本、Makefile/CI 与文档（含 i18n）已同步跟进。

**推荐的下一步。** 在基于文件的布局下，第 4 轮 #4（逐步收紧 mypy）此时
是合理的：每个模块移除一个 `disable_error_code`，修复，循环往复。第
3/4 轮中标记为可选的内部清理（守卫/Worker 统一）按文件来做风险也更低。
