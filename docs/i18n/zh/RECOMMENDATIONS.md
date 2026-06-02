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

在 "modest-shannon" 之后的针对性跟进评审，聚焦保存、加载与 CI 路径。**共 8 项（N1–N8）：** 5 项已修复并带回归测试，通过 **PR #142**（N1）、**#143**（N6、N8）与 **#144**（N4、N5）合并；2 项待办（N2、N7）；1 项已覆盖（N3）。基线仍为绿色：ruff/mypy 干净、测试套件通过。

### 完成状态

| 状态 | 条目 |
|------|------|
| ✅ 已完成 | N1, N4, N5, N6, N8 |
| ⏳ 待办 | N2, N7 |

### 发现的问题

- **N1 🟠 — 在错误路径上释放魔棒闸门**（PR #142）。承接 "modest-shannon" B：换图时 `_load_image_async` 取消 flood fill，而后者既不发 `finished` 也不发 `error`。闸门重置只走成功路径（`apply_loaded_image`）——若加载失败，`_wand_busy` 仍置位，魔棒被旧图阻塞。新增静默的 `reset_pending_wand()`，紧挨 `cancel_flood_fill()`。
- **N2 🟡 — 旋转尺寸限制**（待办）。`rotate_image`（`image_ops.py`）以 `expand=True` 旋转；兆像素保护只在加载时生效（`Image.MAX_IMAGE_PIXELS`），不作用于结果。一张刚好不超限的图在 ~45° 时可膨胀到约 2×——没有闸门的内存峰值。
- **N3 ➖ — 历史内存预算**（已覆盖）。`CanvasHistory`（`canvas_history.py`）早已通过 `_trim()`/`_UNDO_MEMORY_LIMIT` 强制撤销预算，重做由 `_REDO_MAX_ENTRIES` 封顶。无需处理。
- **N4 🟢 — 保存时的扩展名诚实**（PR #144）。`save_image_file` 曾对未知扩展名静默写入 PNG 字节；现以 `ValueError` 明确拒绝，而空扩展名仍默认 PNG。
- **N5 🟡 — 原子保存**（PR #144）。直接写入目标会在中断时损坏既有文件。现改为在目标目录中 `mkstemp` → `os.replace`（即 `qt_plugins._copy_if_needed` 的模式），保留权限并清理临时文件。
- **N6 🟡 — 完整 CI 矩阵中的 `libgl1` + 漂移测试**（PR #143）。完整矩阵未安装 `libgl1`（与其他 Qt 包来源不同）→ `import PyQt6` 可能触发 `libGL.so.1`。已补上；新的 `test_ci_qt_packages.py` 让四份包清单保持一致。
- **N7 🟢 — 急切导入**（待办）。`workers.py` 在模块层导入 `rembg`（会拖入 onnxruntime）；由于 `main_window` 加载 `workers`，导入开销在启动时即产生——即便不使用 AI。应改为惰性导入，并用 `find_spec` 探测 `REMBG_AVAILABLE`。
- **N8 🟢 — 过时的 `load_image` docstring**（PR #143）。它把拖放路径称作同步调用方，而拖放早已异步运行。已更正。

---

## 待办建议

第二次分析中提出、尚未实现的改进（产品/流程）：

- **O1 🟠 — 应用本地化。** UI 硬编码为德语；没有运行时 i18n（无 `QTranslator`/`tr()`），尽管文档已有五种语言。状态消息已集中（`status_messages.py`）。可逐步通过 Qt Linguist（`.ts`）或轻量的 `QLocale` 字符串表实现。
- **O2 🟡 — Linux 应用 / 打包。** 没有 Linux 的应用包；仅能通过 venv 中的 `python -m bgremover` 启动。为 **Raspberry Pi OS** 和主流发行版（Debian/Ubuntu/Fedora）提供可安装包（AppImage/Flatpak/`.deb`），可降低非开发者的上手门槛——类似 macOS 的 `.app` 包。
- **O3 🟡 — 更早运行完整 CI 矩阵。** 完整矩阵（Linux/macOS × 3.10–3.13）仅在 tag/release 时运行；macOS 或 Python 3.10/3.13 的回归发现得太晚。应同时在推送到 `main` 时或每周 cron 运行。
- **O5 🟡 — 更早在 CI 中运行 UI smoke。** 完整 `ui` 测试只在 nightly/手动运行；PR CI 和 Full CI 只执行 `make pr-check`。在 PR/Full CI 中加入小而稳定的 UI smoke，完整 UI 套件继续 nightly。

**✅ 本轮起已完成（PR #146）：** O4 — 单键切换工具（`W`/`B`/`E`/`L`）并同步 toolbar 状态；O6 — tooltips 通过 `_shortcut_label()` 按平台显示 `Cmd`/`Ctrl`。回归测试 `test_tool_shortcuts.py`。

## 按 PR 包实施计划（自 2026-06-02 起）

- **PR 0 — 代码加固（N2 + N7）。** 归并 "adoring-johnson" 的两个待办发现：N2 — 将兆像素闸门也应用于旋转结果（依据角度/对角线预先计算目标尺寸，用状态消息代替无上限的内存峰值）；N7 — 惰性导入 `rembg` 并用 `find_spec` 探测 `REMBG_AVAILABLE`，把 AI 按钮的门控移到 warmup 失败处。小而低风险、不破坏 UX——置于大型包之前。
- **PR 1 — 工具快捷键与提示。** ✅ 已完成（PR #146）。O4 + O6：单键切换（`W`/`B`/`E`/`L`）、同步 toolbar 选中状态、更新 tooltips/README/手册，并加入快捷键 wiring 回归测试。
- **PR 2 — 更早加强 CI。** O3 + O5：完整矩阵也每周或在 `main` 上运行，PR/Full CI 加入小型 UI smoke，Nightly UI 保留完整套件。
- **PR 3 — i18n 基础。** 准备 O1：加入 runtime locale/fallback，逐步集中可见字符串，德语保持稳定默认值。
- **PR 4 — i18n 推出。** 让 O1 可用：至少英语作为运行时语言，然后覆盖现有其他文档语言，并为每个 locale 做 smoke check。
- **PR 5 — Linux 打包基础。** 启动 O2：选择目标产物（AppImage/`.deb`/Flatpak）、desktop 文件/图标/AppStream 元数据和 Linux build smoke。
- **PR 6 — Linux 打包扩展。** 完成 O2：Raspberry Pi OS 变体、可选第二种包格式，以及 Linux 产物 release workflow。

---

## 往轮

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成（PR #135/#136）；其中包括解压缩炸弹处理，以及 N1 现已在错误路径上补全的魔棒生命周期。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，#1–#15 完成，#4 放弃（误报）。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
