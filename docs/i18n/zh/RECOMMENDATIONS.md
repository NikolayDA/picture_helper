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
- 较早已关闭的发现（**#163–#290**，含 EufyMake 史诗 **#351**/**#352–#355**
  与 rembg/ONNX 子进程 **#270**/**#285**/**#286**）均已在记录的 PR 中完成，
  由测试/CI 覆盖并归档。

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

## 打开的 GitHub Issues — Triage 状态 (2026-06-24，已更新)

截至 2026-06-24，GitHub 显示 **14** 个打开的 issues。史诗 **#375**
（精确 mm/DPI 输出 + 通用导出验证）已经过 **#376–#380**（PR #382/#383）
完成并关闭。自上次 triage 以来，**新增了两个史诗**，用于规划阶段 0/1 的收尾：

- **#384 – 组合式 2D 预览**（relief-core MVP，阶段 1 最后一个待办功能点，
  当前约 ~55%），其子 issue 包括 **#385**（relief-shading 渲染器，无 Qt）、
  **#386**（gloss 可视化，无 Qt）、**#387**（画布预览模式 + 合成管线）与
  **#388**（UI 开关 + i18n）。
- **#389 – 更新用户文档并发布 v2.5.0**，其子 issue 包括 **#390**（ANLEITUNG
  用户指南，6 种语言——同时关闭 **#357**）、**#391**（README + 截图 + i18n）
  与 **#392**（发布 v2.5.0）。

文档缺口 **#357**（现由 #390 覆盖）和 **#339**，以及测试/CI 发现 **#318**、
**#299** 与 **#245** 同样仍待处理。

**评论复核（2026-06-24）：** **#245**、**#299** 与 **#339** 上的评论均来自
maintainer（triage），并确认了已记录的状态：#245 仍因配额/计费在外部受阻，
#299 仍是低优先级的测试卫生，而 #339 确认为有意排除 HEIC。没有评论需要实质性的
issue 更新；也无需新建后续 issue。

评估：**相关性** = 对 roadmap/用户的重要性，**复杂度** = 预计实现工作量。

| # | 标题 | 相关性 | 复杂度 | 推荐下一步 |
|---|------|--------|--------|------------|
| [#384](https://github.com/NikolayDA/picture_helper/issues/384) | [Epic] 组合式 2D 预览（颜色/透明度/relief/gloss） | 🟠 高 | 🔴 高（epic） | **进行中（epic）** – 阶段 1 的最后一个功能点。顺序：#385/#386 并行 → #387 → #388。 |
| [#385](https://github.com/NikolayDA/picture_helper/issues/385) | Relief-shading 渲染器（无 Qt） | 🟠 高 | 🟡 中 | **✅ Ready for PR** – 范围清晰、无依赖、无 Qt 且严格类型化。最佳的下一个 PR；解锁 #387。 |
| [#386](https://github.com/NikolayDA/picture_helper/issues/386) | Gloss 可视化渲染器（无 Qt） | 🟡 中 | 🟢 低–中 | **✅ Ready for PR** – 与 #385 并行、无依赖；无 Qt 的纯图像逻辑。 |
| [#387](https://github.com/NikolayDA/picture_helper/issues/387) | 画布：预览模式 + 合成管线 | 🟠 高 | 🟠 中–高 | **Blocked** – 需要 #385 + #386；用回归测试保留 #363 的导出契约。 |
| [#388](https://github.com/NikolayDA/picture_helper/issues/388) | UI：预览模式选择器 + relief/gloss 开关 + i18n | 🟡 中 | 🟡 中 | **Blocked** – 需要 #387；关闭史诗 #384。 |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | [Epic] 更新用户文档并发布 release | 🟠 高 | 🟡 中（epic） | **进行中（epic）** – 现在并行 #390/#391 →（合并史诗 #384）→ #392。 |
| [#390](https://github.com/NikolayDA/picture_helper/issues/390) | 为新功能更新 ANLEITUNG 用户指南（+ 5 份 i18n） | 🟠 高 | 🔴 高（L，6 种语言） | **Ready for PR** – 范围明确但工作量大；同时关闭 **#357**。 |
| [#391](https://github.com/NikolayDA/picture_helper/issues/391) | 更新 README + 截图 + i18n | 🟡 中–高 | 🟡 中 | **Ready for PR（有保留）** – 文本部分可立即着手；截图需要一次当前版本的应用运行。 |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | 发布 v2.5.0（CHANGELOG/版本号/tag/产物） | 🟠 高 | 🟡 中 | **Blocked** – 需要 #390 + #391，最好在 #384 之后。 |
| [#357](https://github.com/NikolayDA/picture_helper/issues/357) | Docs：ANLEITUNG §4 缺少启动路径/Finder 打开方式 | 🟢 低 | 🟢 低 | **已并入 #390** – 仍可作为独立小 PR 处理，但通常会与 #390 一起关闭。 |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF 不支持作为输入格式 | 🟢 低 | 🟢 低 | **Ready for PR（docs）** – 已**有意排除 HEIC**（评论 2026-06-21）。仅需澄清 README/ANLEITUNG，然后关闭。 |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 低 | 🟢 低 | **Ready for PR（opportunistic）** – 非产品或 CI blocker；优先做最有价值的（断言 lasso endpoint、`test_helpers` 行、合并 `set_brush_size` 测试）。 |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟢 低 | 🟡 中 | **Needs refinement** – 先记录 GitHub semantics（top-level vs. 有效的 per-job）；不得削弱 #303 OIDC guard。 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan 因 "Quota exceeded" 失败 | 🟡 中 | 🟢 低 | **Blocked（外部）** – repo 侧加固经 #322/#342（已关闭）完成；剩余 blocker 是 OpenAI/billing quota。恢复 quota 后手动触发一次 scheduled scan，然后关闭。 |

### 推荐下一步（PR 顺序）

1. 将 **#385** 与 **#386**（无 Qt 的 relief/gloss 渲染器）作为小型、可并行的
   PR 实现——它们是最佳的"就绪且范围清晰"候选；它们解锁 #387。
2. 接着完成 **#387** → **#388** 以收尾史诗 **#384**（组合式 2D 预览）；
   用回归测试保留 #363 的导出契约。
3. 并行落地 **#390** 与 **#391** 作为 docs PR（同时关闭 **#357**）；
   将 **#339** 作为独立小 PR 穿插处理。
4. 仅在 #390/#391 之后、且最好在 #384 之后再发布 **#392**（release v2.5.0）。
5. 适时清理 **#299**；在语义有据可依前暂缓 **#318**，并保持 **#245**
   externally blocked。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
