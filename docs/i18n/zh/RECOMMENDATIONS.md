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

## 打开的 GitHub Issues — Triage 状态 (2026-06-22)

截至 2026-06-22，GitHub 显示 **9** 个打开的 issues。新增的是 **EufyMake 导出
epic #351** 及其 sub-issues **#352–#355**（roadmap 第 #3 位）。此前列出的
maintenance/skip path **#322** 已通过 **#342** 交付并已**关闭**；项目/图层与
安全测试 issues **#323/#324/#326** 和 **#329–#335** 仍在 **#337/#338/#340** 中
完成。

评估：**相关性** = 对 roadmap/用户的重要性，**复杂度** = 预计实现工作量。

| # | 标题 | 相关性 | 复杂度 | 推荐下一步 |
|---|------|--------|--------|------------|
| [#351](https://github.com/NikolayDA/picture_helper/issues/351) | [Epic] 一致的 EufyMake 导出包 | 🟠 高 | 🔴 高（epic） | **Needs refinement** – 据 deep research（issue 评论），将 scope 收窄为「面向 EufyMake Studio 的稳健 import-assets」；原生 `.empf` 生成**不**作为默认目标。经 #352–#355 推进。 |
| [#352](https://github.com/NikolayDA/picture_helper/issues/352) | 导出数据模型与包定义（无 Qt）+ ADR | 🟠 高 | 🟡 中 | **Ready for PR** – 调研任务已完成，ADR 决策记录在评论中。无 Qt 的 `eufymake_export.py`，含 `ExportPlan`/`ExportAsset`（彩色图案 PNG+alpha、高度灰度图亮=高、gloss mask）；将 16-bit/gloss 语义/原生 `.empf` 标记为「未定」。基础 — 解锁 #353–#355。 |
| [#353](https://github.com/NikolayDA/picture_helper/issues/353) | Asset 渲染与原子写包 | 🟠 高 | 🟡 中 | **Blocked** – 需 #352；之后范围清晰（渲染 + 原子写）。 |
| [#354](https://github.com/NikolayDA/picture_helper/issues/354) | 导出前一致性检查 | 🟠 高 | 🟡 中 | **Blocked** – 需 #352。保持检查模块可复用（与通用导出前错误检查协同）。 |
| [#355](https://github.com/NikolayDA/picture_helper/issues/355) | UI：EufyMake 导出对话框 + 菜单 + i18n + settings | 🟠 高 | 🟡 中 | **Blocked** – 需 #352–#354。据 deep research，UI 文案应为「为 EufyMake Studio 准备 assets」，而非「生成成品项目」。 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan 因 "Quota exceeded" 失败 | 🟡 中 | 🟢 低 | **Blocked（外部）** – repo 侧加固经 #322/#342（已关闭）完成；剩余 blocker 是 OpenAI/billing quota。恢复 quota 后手动触发一次 scheduled scan，然后关闭。 |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟢 低 | 🟡 中 | **Needs refinement** – 先记录 GitHub semantics（top-level vs. 有效的 per-job）；不得削弱 #303 OIDC guard。 |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF 不支持作为输入格式 | 🟢 低 | 🟢 低 | **Ready for PR（docs）** – maintainer 已**有意排除 HEIC**（评论 2026-06-21）。仅需澄清 README/ANLEITUNG，然后关闭。 |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 低 | 🟢 低 | **Ready for PR（opportunistic）** – 非产品或 CI blocker；优先做最有价值的（断言 lasso endpoint、`test_helpers` 行、合并 `set_brush_size` 测试）。 |

### 推荐下一步（PR 顺序）

1. 先做 **#352** — epic 的基础，ADR refinement 后 well-scoped；解锁 #353/#354。
2. #352 合入后并行做 **#353** 与 **#354**。
3. **#355** 收尾该 epic。
4. **#339**（小 docs PR）与 **#299**（test cleanup）作为期间的低优先级填充。
5. 暂缓 **#318**，直至 GitHub permission semantics 记录完成。
6. 保持 **#245** externally blocked（无 repo patch 能恢复 quota）。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
