[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · **简体中文**

# 代码分析与评级建议：BgRemover

## 评级标准

| 符号 | 优先级 | 含义 |
|------|--------|------|
| 🔴 | 严重 | 必须修复：会导致错误、崩溃或不一致 |
| 🟠 | 高 | 应尽快修复：明显影响可靠性或可维护性 |
| 🟡 | 中 | 建议处理：提升代码质量、可读性或可测试性 |
| 🟢 | 低 | 可选：打磨和补充改进 |

---

## 当前状态（2026-06-02，"adoring-johnson" 评审）

在 "modest-shannon" 之后的针对性跟进评审，聚焦保存、加载与 CI 路径。**共 8 项（N1–N8）：** 7 项已修复并带回归测试，通过 **PR #142**（N1）、**#143**（N6、N8）、**#144**（N4、N5）与 **#148**（N2、N7）合并；1 项已覆盖（N3）。基线仍为绿色：ruff/mypy 干净、测试套件通过。

### 完成状态

| 状态 | 条目 |
|------|------|
| ✅ 已完成 | N1, N2, N4, N5, N6, N7, N8 |
| ⏳ 待办 | – |

### 发现的问题

- **N1 🟠 — 在错误路径上释放魔棒闸门**（PR #142）。承接 "modest-shannon" B：换图时 `_load_image_async` 取消 flood fill，而后者既不发 `finished` 也不发 `error`。闸门重置只走成功路径（`apply_loaded_image`）——若加载失败，`_wand_busy` 仍置位，魔棒被旧图阻塞。新增静默的 `reset_pending_wand()`，紧挨 `cancel_flood_fill()`。
- **N2 🟡 — 旋转尺寸限制**（PR #148）。`rotate_image`（`image_ops.py`）以 `expand=True` 旋转；兆像素保护此前只在加载时生效（`Image.MAX_IMAGE_PIXELS`），不作用于结果——一张刚好不超限的图在 ~45° 时可膨胀到约 2×。现在 `rotated_size()` 预先估算扩展后的边界框；`apply_rotate` 以状态消息拒绝超过上限的结果。
- **N3 ➖ — 历史内存预算**（已覆盖）。`CanvasHistory`（`canvas_history.py`）早已通过 `_trim()`/`_UNDO_MEMORY_LIMIT` 强制撤销预算，重做由 `_REDO_MAX_ENTRIES` 封顶。无需处理。
- **N4 🟢 — 保存时的扩展名诚实**（PR #144）。`save_image_file` 曾对未知扩展名静默写入 PNG 字节；现以 `ValueError` 明确拒绝，而空扩展名仍默认 PNG。
- **N5 🟡 — 原子保存**（PR #144）。直接写入目标会在中断时损坏既有文件。现改为在目标目录中 `mkstemp` → `os.replace`（即 `qt_plugins._copy_if_needed` 的模式），保留权限并清理临时文件。
- **N6 🟡 — 完整 CI 矩阵中的 `libgl1` + 漂移测试**（PR #143）。完整矩阵未安装 `libgl1`（与其他 Qt 包来源不同）→ `import PyQt6` 可能触发 `libGL.so.1`。已补上；新的 `test_ci_qt_packages.py` 让四份包清单保持一致。
- **N7 🟢 — 急切导入**（PR #148）。`workers.py` 此前在模块层导入 `rembg`（会拖入 onnxruntime）；由于 `main_window` 加载 `workers`，导入开销在启动时即产生——即便不使用 AI。现在改用 `find_spec` 探测 `REMBG_AVAILABLE`，并仅在 worker 线程（warmup/首次 AI 点击）惰性导入 `rembg`。
- **N8 🟢 — 过时的 `load_image` docstring**（PR #143）。它把拖放路径称作同步调用方，而拖放早已异步运行。已更正。

---

## 待办建议

第二次分析中提出、尚未实现的改进（产品/流程）：

- **O1 🟠 — 应用本地化。** 已实现运行时 i18n：`bgremover.i18n` 提供集中字符串表与稳定的德语 fallback；**德语与英语**可在运行时切换（设置对话框中的语言选择，附带重启提示）。整个可见界面——包括画布状态消息、历史条目与对话框——均通过 `tr()`，并由 AST 检查防止新增未翻译字面量。待办：将其他现有文档语言（es/fr/uk/zh）作为运行时 locale（**PR 4c**）。
- **O2 🟡 — Linux 应用 / 打包。** 没有 Linux 的应用包；仅能通过 venv 中的 `python -m bgremover` 启动。为 **Raspberry Pi OS** 和主流发行版（Debian/Ubuntu/Fedora）提供可安装包（AppImage/Flatpak/`.deb`），可降低非开发者的上手门槛——类似 macOS 的 `.app` 包。
**✅ 已完成：** O4/O6 — 单键切换工具（`W`/`B`/`E`/`L`）与按平台显示的 `Cmd`/`Ctrl` 提示（PR #146，`test_tool_shortcuts.py`）；O3 — 完整矩阵额外每周通过 cron 运行（PR #149）；O5 — `ui_smoke` 子集在 PR/Full CI 中运行，完整 qtbot 套件保留在 nightly（PR #149）。

## 按 PR 包实施计划（自 2026-06-02 起）

- **PR 0 — 代码加固（N2 + N7）。** ✅ 已完成（PR #148）。N2 — 将兆像素闸门也应用于旋转结果（`rotated_size()` 预先估算目标尺寸，`apply_rotate` 以状态消息拒绝超过上限的结果）；N7 — 惰性导入 `rembg` 并用 `find_spec` 探测 `REMBG_AVAILABLE`（现有的 warmup 失败处理可覆盖损坏的后端）。
- **PR 1 — 工具快捷键与提示。** ✅ 已完成（PR #146）。O4 + O6：单键切换（`W`/`B`/`E`/`L`）、同步 toolbar 选中状态、更新 tooltips/README/手册，并加入快捷键 wiring 回归测试。
- **PR 2 — 更早加强 CI。** ✅ 已完成（PR #149）。O3 — 完整矩阵额外每周（cron）运行；O5 — `ui_smoke` 子集进入 PR/Full CI，Nightly UI 保留完整套件。
- **PR 3 — i18n 基础。** ✅ 已完成。O1 已准备：新增带 runtime locale/fallback 的 `bgremover.i18n`，德语保持稳定默认值，首个集中字符串表覆盖状态消息、菜单、toolbar、tabs、历史和裁剪栏；加入 locale 规范化、fallback 与 UI wiring 回归测试。
- **PR 4 — i18n 推出。** ✅ 已完成。已让 O1 可用：**4a** — 将 `tr()` 覆盖扩展到右侧面板、设置对话框和所有对话框（德语逐字节一致，经 golden diff 验证）；**4b** — 完整英语表 + 语言选择（持久化、重启提示）；**4b.1** — 画布状态消息、历史描述与 `main_window` 对话框（打开/保存/颜色/未保存）通过 `tr()`，并新增 AST guard 防止用户可见位置出现新的未翻译字面量。已测试键/占位符对等性与按 locale 的 UI smoke。
- **PR 4c — i18n 更多语言（可选，已搁置）。** 如有需要，将 es/fr/uk/zh 添加为运行时 locale（按键逐一镜像表——对等性/smoke/guard 随后自动生效）。目前未计划。
- **PR 5 — Linux 打包基础。** 启动 O2：选择目标产物（AppImage/`.deb`/Flatpak）、desktop 文件/图标/AppStream 元数据和 Linux build smoke。
- **PR 6 — Linux 打包扩展。** 完成 O2：Raspberry Pi OS 变体、可选第二种包格式，以及 Linux 产物 release workflow。

---

## 往轮

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成（PR #135/#136）；其中包括解压缩炸弹处理，以及 N1 现已在错误路径上补全的魔棒生命周期。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，#1–#15 完成，#4 放弃（误报）。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
