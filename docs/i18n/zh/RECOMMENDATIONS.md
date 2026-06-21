[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · **简体中文**

# 代码分析与优先级建议：BgRemover

## 优先级说明

| 符号 | 优先级 | 含义 |
|------|--------|------|
| 🔴 | 严重 | 错误、崩溃或数据丢失 |
| 🟠 | 高 | 明显影响可靠性或可维护性 |
| 🟡 | 中 | 有助于质量、可读性或可测试性的改进 |
| 🟢 | 低 | 可选的打磨或流程改进 |

## 当前状态（2026-06-04）

当前代码分析清单为空。Ruff、mypy 和本地测试套件仍是新 PR 前的基线。

### 自上次 Review 以来已完成

- **N1/N2/N4/N5/N6/N7/N8** 已完成：错误路径、大小限制、文件扩展名、
  原子保存、CI Qt 包、惰性导入和 docstring。
- **O2/O3/O4/O5/O6** 已实现：Linux 包、release workflow、完整矩阵、
  `ui_smoke` 和适配平台的工具快捷键。
- **#163–#206** 已在记录的 PR 中关闭，并由回归测试或 CI 检查保护。
- PR **#263–#269** 关闭了 **#257、#258、#234 + #259、#248 + #260、#231**
  和 **#249**；**#261** 已通过 PR #268 解决并关闭。
- PR **#274** 关闭了 **#232**：借助 PEP 562 惰性导出，`import bgremover`
  不再加载 Qt 栈；一个子进程回归测试对此进行了覆盖。
- PR 浪潮 **#280–#284** 落地了每周 benchmark，实现了三项发现——**#235**
  （共享 undo/redo 预算，PR #281）、**#275**（已本地化的百万像素提示，PR #282）
  和 **#270**（经 `ai_process.py` 的 rembg/ONNX 子进程，PR #283）——并刷新了
  路线图（PR #284）。**#235、#270 和 #275 现已关闭。**
- 来自 #283 与 #264 的两项合并后 Codex 后续发现同样已修复**并关闭**：**#285**
  （rembg 子进程的健壮性/内存，PR #289）和 **#286**（受限文件读取中的内存峰值，
  PR #290）。

- **N9 ✅ — 项目/图层数据模型（史诗 #329）已交付。** 无 Qt 领域模型（#330）、
  图层感知历史（#331）、合成画布（#332）、`.bgrproj` 格式（#333）、图层面板/项目
  菜单（#334）与迁移/集成（#335）——保持单图对等，`make check`/`make ui` 通过。

### 仍然开放

- **O1 🟠 — 更多 runtime 语言。** 应用内可切换德语和英语。现有文档语言
  es/fr/uk/zh 尚不是 runtime locales；如需要，请在 `bgremover.i18n`
  中逐 key 添加并用测试保护。
- **O7 ✅ — rembg/ONNX 子进程已完成（PR #283，issue #270 已关闭）。** 不可中断的
  AI 推理现已在经 `spawn` 启动的进程（`ai_process.py`）中运行；作为 AI 应急
  出口的 `QThread.terminate()` 已移除。健壮性/内存方面的后续发现已在 **#285**（PR #289）修复并关闭。

## 开放的 GitHub Issues — 优先级评估（2026-06-21）

As of 2026-06-21, only **4** roadmap/follow-up issues remain open after
reviewing yesterday's and today's PRs. Merge commits **#337**, **#338**, and
**#340** cleanly complete the items that were still open yesterday: **#326**,
**#329–#335**, **#323**, and **#324**. The GIF load path is regression-tested,
the project/layer epic is implemented end-to-end from the domain model through
UI/integration, and the security-scan tests cover severity filtering, empty
findings, and prompt scope. The remaining open items are **#322**
(maintenance/skip path for the scheduled Codex Security Scan), **#318**
(permission-guard semantics), **#245** (externally blocked quota), and **#299**
(test hygiene).

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI: add a maintenance/skip path for the scheduled Codex Security Scan | 🟡 Medium | 🟡 Medium | **Next repo-side step for #245** — choose manual switch, visible auto graceful-skip, or both; gate in the `cadence` job, "disabled → skipped, not failed", keep least privilege and add a static test |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟡 Medium | 🟡 Medium | **Needs refinement** — first document GitHub's startup-validation semantics (top-level vs. effective-per-job); no observed repo failure right now, and OIDC guard #303 must not be weakened |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | **Externally blocked** — restore quota account-side; #323/#324 are complete repo-side, #322 remains open as maintenance/skip hardening |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | No correctness bug; improve opportunistically when related tests are touched (highest value: endpoint move, consolidate `set_brush_size`) |

### 可合并处理的 Issues

- **#322** can be implemented as a standalone CI-hardening PR and complements
  the already completed #323/#324.
- **#318** stays separate because GitHub's semantics must be documented before
  changing code.
- **#299** should only ride along when an affected test is already being edited.

### 推荐 PR 顺序

1. **#322** — final repo-side #245 follow-up with direct operational value.
2. **#318** — refine the permission guard once semantics are documented, without
   weakening the OIDC regression case.
3. **#245** — restore quota account-side (externally blocked).
4. **#299** — test hygiene as needed.

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
