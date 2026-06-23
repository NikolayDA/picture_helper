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
- **N10 ✅ — Height Map 工作区（史诗 #344）已交付。** 无 Qt 高度表示与 2D
  视图（#345）、生成/导入（#346）、编辑（#347）、带实时预览的 `height_ops`
  优化（#348）以及上下文感知的高度标签页（#349）。
- **N11 ✅ — 阶段 0 打磨（史诗 #358）已交付。** 项目目标尺寸缩放（#359）、
  保留 alpha 的亮度/对比度/饱和度调整（#360）与选区限定的 alpha 边缘羽化
  （#361），均支持 undo/redo 并无损保存在 `.bgrproj` 中。
- **#363 ✅ — 导出回归已修复（PR #367）。** 无论激活哪个图层，保存图像
  都会再次写入 COLOR 合成；显示渲染与导出渲染已分离，并由一个像素回归
  测试覆盖。

### 仍然开放

- **O1 🟠 — 更多 runtime 语言。** 应用内可切换德语和英语。现有文档语言
  es/fr/uk/zh 尚不是 runtime locales；如需要，请在 `bgremover.i18n`
  中逐 key 添加并用测试保护。
- **O7 ✅ — rembg/ONNX 子进程已完成（PR #283，issue #270 已关闭）。** 不可中断的
  AI 推理现已在经 `spawn` 启动的进程（`ai_process.py`）中运行；作为 AI 应急
  出口的 `QThread.terminate()` 已移除。健壮性/内存方面的后续发现已在 **#285**（PR #289）修复并关闭。

## 打开的 GitHub Issues — Triage 状态 (2026-06-23，已更新)

截至 2026-06-23，GitHub 显示 **11** 个打开的 issues。EufyMake epic
**#351** 已在 PR **#372–#374** 后关闭：#352–#355 覆盖 ADR/模型、渲染与
原子 writer、验证以及 UI/settings。#374 还修复了 `optional_roles` 生成器
耗尽，并阻止目录替换已有文件。新的 roadmap epic **#375** 与 #376–#380
现涵盖精确 mm/DPI 输出和通用导出检查。**#357**、**#339**、**#318**、
**#299** 与 **#245** 仍待处理；EufyMake 复核本身无需新增后续 issue。

评估：**相关性** = 对 roadmap/用户的重要性，**复杂度** = 预计实现工作量。

| # | 标题 | 相关性 | 复杂度 | 推荐下一步 |
|---|------|--------|--------|------------|
| [#375](https://github.com/NikolayDA/picture_helper/issues/375) | [Epic] 精确输出（mm/DPI）+ 通用导出检查 | 🟠 高 | 🔴 高（epic） | **Ready for PR — 基础优先：** #376（无 Qt 几何 + 项目元数据），随后 #377/#378/#379 可并行；#380 完成 UI 与 epic。 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan 因 "Quota exceeded" 失败 | 🟡 中 | 🟢 低 | **Blocked（外部）** – repo 侧加固经 #322/#342（已关闭）完成；剩余 blocker 是 OpenAI/billing quota。恢复 quota 后手动触发一次 scheduled scan，然后关闭。 |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟢 低 | 🟡 中 | **Needs refinement** – 先记录 GitHub semantics（top-level vs. 有效的 per-job）；不得削弱 #303 OIDC guard。 |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF 不支持作为输入格式 | 🟢 低 | 🟢 低 | **Ready for PR（docs）** – maintainer 已**有意排除 HEIC**（评论 2026-06-21）。仅需澄清 README/ANLEITUNG，然后关闭。 |
| [#357](https://github.com/NikolayDA/picture_helper/issues/357) | Docs：ANLEITUNG §4 缺少启动路径/Finder 打开方式 | 🟢 低 | 🟢 低 | **Ready for PR（docs）。** 同步主指南和五份 i18n；明确最近文件包含图像与 `.bgrproj` 项目。 |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 低 | 🟢 低 | **Ready for PR（opportunistic）** – 非产品或 CI blocker；优先做最有价值的（断言 lasso endpoint、`test_helpers` 行、合并 `set_brush_size` 测试）。 |

### 2026-06-23 已关闭 PR/Issues 复核

已复核今日关闭的 PR **#372–#374** 与 issues **#351–#355**。ADR、无 Qt
模块、UI、持久化及 #373 后续修复均已存在并有测试覆盖。没有需要新建 issue
或评论的未解决发现。

### 推荐下一步（PR 顺序）

1. 先实现基础 **#376**；随后并行 **#377**、**#378**、**#379**，最后
   完成 **#380**。
2. 将 **#357** 与 **#339** 作为独立的小型 docs PR 穿插处理。
3. 适时清理 **#299**；暂缓 **#318**，并保持 **#245** externally blocked。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
