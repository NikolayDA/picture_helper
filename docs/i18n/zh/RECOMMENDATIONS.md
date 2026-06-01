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

## 当前状态（2026，"admiring-mayer" 评审）

针对实际代码库，对一份外部提交的建议清单（15 项）进行了评审。结论：**14 项确认，1 项误报**（#4）。已确认的项目在下面归为**六个实施包**；包的顺序同时也是建议的处理顺序。每条都保留原始问题、证据（`文件:行`）以及修复方向；当前实施状态以下表为准。编号（#1–#15）对应原始评审清单。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。

### 完成状态（核对日期：2026-06-01）

| 状态 | 条目 |
|------|------|
| ✅ 已完成 | #1, #2, #3, #5, #6, #7, #8, #10, #11, #13, #14, #15 |
| ⬜ 待处理 | #12 |
| ➖ 已放弃 | #4 – 误报 |

---

## 建议包

**包 1 — 立即处理** 🔴

- **#1 取消 AI 必须结束线程。** `AIWorker._work`（`bgremover/workers.py:74`）在取消时直接返回而不发出信号；`quit_on=(finished, error)`（`bgremover/worker_controller.py:152`）于是永远不触发 → QThread 持续运行，`ai_thread`/`ai_worker` 一直被保留，AI 按钮在本次会话剩余时间内保持禁用（触发条件：「AI 正在计算时加载图片」）。修复：在 `finally` 分支（`_always_finished`）发出一个无参 `done` 信号并加入 `quit_on`——相关基础设施已存在（预热 worker）。**已在本 PR 中实现，并附取消生命周期测试。**

**包 2 — 快速且安全的改进（已完成）** 🟠 🟡

- **#2 集中重置画布的瞬时状态。** `apply_loaded_image`（`canvas.py:234`）调用 `cancel_overlay_only()` 却不发 `cropModeChanged(False)`，也不取消套索 → 裁剪信号序列停留在 `[True]`，旧套索点残留。引入 `_reset_transient_state()` 方法。
- **#11 让日志独立于外部 handler 配置。** `logging.basicConfig()`（`logging_config.py:61`）在根 logger 已有 handler 时是 no-op → 显示的日志路径 ≠ 实际写入的路径。显式配置具名的 `BgRemover` logger（比 `force=True` 更干净）。
- **#10 让诊断脚本指向当前日志路径。** `diagnose_mac.sh:178` 仍读取 `~/.bgremover.log`；logger 实际写入 `~/Library/Application Support/BgRemover/bgremover.log`（QStandardPaths）。对齐该路径。
- **#8 稳健地规范导出格式。** `_save_as`（`main_window.py:304`）丢弃了对话框所选的过滤器；`save_image_file`（`image_ops.py:46`）在缺少扩展名时静默保存为 PNG。建立带默认后缀的中央格式模型；合并重复的格式字典（对话框 vs. MainWindow）。*(所报告的 EXR `KeyError` 仅在被篡改的设置/字典漂移下可达；缺扩展名才是用户可见的核心。)*
- **#14 同步 CI 与文档检查。** `RESOURCES.md:102` 和 `TESTING.md:10` 仍写「3.10/3.12」（实际为 3.10–3.13）；`ui-nightly.yml` 未出现在 workflow 列表和 `test_resource_docs.py:35` 中。也应检查 workflow 列表和 Python 矩阵。
- **#15 让 release CI 成为真正的关卡。** `ci.yml` 仅在 `release: published` 时跑完整矩阵（作为关卡太晚）；`ui-nightly.yml:18` 的 `continue-on-error: true` 掩盖了失败。增加 tag/预发布候选运行，并让 nightly 失败可见地升级。

**包 3 — 需测量的实质改进（已完成）** 🟠

- **#5 不要在每次画笔移动时重建 overlay。** `_refresh_overlay`（`canvas.py:263`）→ `mask_to_overlay` 构建完整 RGBA overlay（40 MP ≈ 160 MiB）——即使掩码为空、即使每次鼠标移动。改为惰性构建、更新脏区域或合并事件。
- **#6 限制魔棒、使其可取消、做基准测试。** `flood_fill`（`image_utils.py:48`）在 Python 层扩张区域；实测 2.25 MP 约 3.3 秒（→ 40 MP 为两位数秒）。引入扫描线/原生实现（如 `scipy.ndimage.label`）并加上取消路径。
- **#7 串行化 rembg 预热与 AI 调用。** `_on_warmup_done`（`main_window.py:270`）即便预热出错也显示「AI 就绪」；预热期间 AI 按钮仍可用 → 并行的模型初始化。区分成功/失败，并在预热结束前禁用按钮。
- **#3 强制执行历史的内存预算。** `restore`（`canvas_history.py:81`）和 `redo`（`:47`）向 undo 栈追加却绕过了 `push` 的逐出 → 反复恢复会无限增长。使用共享的裁剪辅助函数并测试总预算。

**包 4 — 安全** 🟡

- **#12 加固临时 Qt 插件暂存。** `qt_plugins.py`（第 26/29/48 行）在 macOS 上使用 `/private/tmp` 下的可预测路径、固定的 `.tmp` 文件，且仅比较大小。由于从那里加载的是可执行的 Qt 插件，预先投放是一个本地代码注入向量。改用用户专属的 `0700` 目录、唯一的临时文件以及内容/哈希校验。

**包 5 — 测试与方法** 🟡

- **#13 让测试面向行为，而非源代码文本。** `test_static_checks.py` 中的 AST 检查只检查字符串出现，捕获不到取消 AI 的缺陷（#1）。补充动态测试：取消生命周期、裁剪/套索期间加载、预热错误、未知导出格式、已有 handler 时的日志，以及恢复后的内存预算。

**包 6 — 放弃 / 改作他用** 🟢

- **#4 macOS 上的 Cmd 相减——误报。** 在未设置 `AA_MacDontSwapCtrlAndMeta`（任何地方都没设）时，Qt 在 macOS 上将 Cmd→`ControlModifier`；因此 `canvas.py:80` 的检查已经能响应 Cmd+点击，UI 文案也正确。额外接受 `MetaModifier` 反而会把物理 Control 键错误地绑定到「相减」。**放弃该代码改动**；至多添加一个平台测试以锁定 Qt 的映射。
