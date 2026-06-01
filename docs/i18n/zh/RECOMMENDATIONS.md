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

## 当前状态（2026-06-01，"modest-shannon" 评审）

针对 v2.2 之后的代码库（代码、文档、测试）进行了深入审查。基线良好：ruff/mypy 干净、测试套件通过、覆盖率 88%。共发现 **5 项（A–E）**——均已实现并带回归测试，通过 **PR #135**（A、B）与 **PR #136**（C–E）合并。证据以文件/函数引用给出。

### 完成状态

| 状态 | 条目 |
|------|------|
| ✅ 已完成 | A, B, C, D, E |

### 发现的问题

- **A 🟠 — 捕获 `DecompressionBombError`。** `image_loading.py` 未捕获 Pillow 的 `DecompressionBombError`（它不是 `OSError` 的子类）→ 超过 2× `MAX_IMAGE_PIXELS`（80 MP）的图像绕过了友好的"过大"提示，并在同步 `load_image` 路径上未被捕获地抛出。现已在两个打开阶段捕获并映射到标准提示；回归测试触发 Pillow 真实的炸弹防护（不再 mock `Image.open`）。
- **B 🟡 — 换图时的魔棒生命周期。** `_reset_transient_state`（`canvas.py`）未重置 `_wand_busy`，且 `_load_image_async`（`main_window.py`）未取消 flood fill——与 `cancel_ai()` 不对称。结果：换图/还原后魔棒被阻塞，并浪费 CPU。现集中重置标志并在加载时调用 `cancel_flood_fill()`。
- **C 🟡 — 日志隔离。** `_setup_logging`（`logging_config.py`）在根 logger 上使用 `basicConfig(force=True)` → 第三方日志（rembg/onnxruntime/Pillow）混入支持用日志文件，并清除了外部 handler。现改为带自有 handler 的具名 `BgRemover` logger（`propagate=False`）。
- **D 🟢 — 测试遗留物。** `test_static_checks.py` 仍探测已删除的单体 `BgRemover.py`，并带有误导性的 `#N` 标记（历史轮次 ≠ 当前编号）。已移除单体分支，并在 docstring 中澄清来源。
- **E 🟢 — i18n 安全网。** 软漂移检查只覆盖 8 个翻译文档中的 3 个。`WATCHED_DOCS` 已扩展到全部 8 个（目前结构均同步）。

---

## 待办建议

第二次分析中提出、尚未实现的改进（产品/流程）：

- **O1 🟠 — 应用本地化。** UI 硬编码为德语；没有运行时 i18n（无 `QTranslator`/`tr()`），尽管文档已有五种语言。状态消息已集中（`status_messages.py`）。可逐步通过 Qt Linguist（`.ts`）或轻量的 `QLocale` 字符串表实现。
- **O2 🟡 — Linux 应用 / 打包。** 没有 Linux 的应用包；仅能通过 venv 中的 `python -m bgremover` 启动。为 **Raspberry Pi OS** 和主流发行版（Debian/Ubuntu/Fedora）提供可安装包（AppImage/Flatpak/`.deb`），可降低非开发者的上手门槛——类似 macOS 的 `.app` 包。
- **O3 🟡 — 更早运行完整 CI 矩阵。** 完整矩阵（Linux/macOS × 3.10–3.13）仅在 tag/release 时运行；macOS 或 Python 3.10/3.13 的回归发现得太晚。应同时在推送到 `main` 时或每周 cron 运行。
- **O4 🟢 — 工具的键盘快捷键。** 魔棒/画笔/橡皮擦/套索只能用鼠标；增加单键切换（如 `B`/`E`）。

---

## 上一轮（v2.2，"admiring-mayer"）

针对代码库审查了一份外部提交的 15 项清单：**#1–#15 已完成，#4 放弃**（误报）。详情见已合并的 PR 与归档。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
