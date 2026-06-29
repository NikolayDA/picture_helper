[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · **简体中文**

# 代码分析与优先级建议：BgRemover

## 优先级说明

| 符号 | 优先级 | 含义 |
|------|--------|------|
| 🔴 | 严重 | 错误、崩溃或数据丢失 |
| 🟠 | 高 | 明显影响可靠性或可维护性 |
| 🟡 | 中 | 有助于质量、可读性或可测试性的改进 |
| 🟢 | 低 | 可选的打磨或流程改进 |

## 当前状态（2026-06-29）

当前代码分析清单为空。Ruff、mypy 和本地测试套件仍是新 PR 前的基线。

### 自上次 Review 以来已完成

- **N1/N2/N4/N5/N6/N7/N8** 已完成：错误路径、大小限制、文件扩展名、
  原子保存、CI Qt 包、惰性导入和 docstring。
- **O2/O3/O4/O5/O6** 已实现：Linux 包、release workflow、完整矩阵、
  `ui_smoke` 和适配平台的工具快捷键。
- 较早已关闭的发现（含 EufyMake 史诗 **#351**/**#352–#355** 与 rembg/ONNX
  子进程 **#270**/**#285**/**#286**）均已在记录的 PR 中完成，由测试/CI 覆盖并归档。

- **N9 ✅ — 项目/图层数据模型（史诗 #329）已交付。** 无 Qt 领域模型（#330）、
  图层感知历史（#331）、合成画布（#332）、`.bgrproj` 格式（#333）、图层面板/项目
  菜单（#334）与迁移/集成（#335）——保持单图对等，`make check`/`make ui` 通过。
- **N10 ✅ — Height Map 工作区（史诗 #344）已交付。** 无 Qt 高度表示与 2D
  视图（#345）、生成/导入（#346）、编辑（#347）、带实时预览的 `height_ops`
  优化（#348）以及上下文感知的高度标签页（#349）。
- **N11 ✅ — 阶段 0 打磨（史诗 #358）已交付。** 项目目标尺寸缩放（#359）、
  保留 alpha 的亮度/对比度/饱和度调整（#360）与选区限定的 alpha 边缘羽化
  （#361），均支持 undo/redo 并无损保存在 `.bgrproj` 中。
- **N12 ✅ — 组合式 2D 预览（史诗 #384）已交付。** 无 Qt 浮雕/光泽渲染器
  （#385/#386）、不依赖激活图层且带有限缓存的明确模式（#387），以及同步的
  “视图”菜单/“预览”面板与实时强度和光泽开关（#388）；“模式×图层”矩阵逐位守住
  #363 导出契约。后续 #397（PR #398）让临时颜色/高度预览通过同一管线，遵守隐藏
  数据图层，并高效跳过强度为 0 的浮雕。
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

## 打开的 GitHub Issues — Triage 状态 (2026-06-29，已更新)

截至 2026-06-29，GitHub 显示 **8** 个打开的 issues：**#245**、**#299**、
**#318**、**#389**、**#392**、**#404**、**#406** 与 **#408**。同日新增文档/代码
审计 **#408**（API/CLI 文档对照当前函数签名 — 无 drift）。此前新增的质量/健壮性
issue（自 2026-06-25 复核以来），即死代码审计 **#406** 与预览降级缺口
**#404**，仍为打开。文档包
**#390/#391**、打开方式说明 **#357** 以及已记录的 HEIC 排除项 **#339** 仍为关闭；
roadmap 史诗 **#389** 只剩 release 步骤 **#392**。

**评论复核：** 无新的外部评论。#392/#299/#245 上的现有评论是 owner 的 triage
记录，与当前状态一致；#408 为新建且无评论 — 无需更新 issue。

**新发现已对照代码核实：** #406 已确认 —`_derive_physical_size`
（`eufymake_export.py:217`）无任何调用者，且 `parse_size_mm` 仅为该死函数在此
导入（`project_model.py` 仍在使用，故符号保留）。#404 已确认 —
`compose_relief`/`compose_gloss`（`canvas.py:555/564`）在渲染路径中未被捕获，
尽管 docstring（第 513 行）承诺降级到 COLOR 合成。#408 已确认 — 审计无发现：
`CLAUDE.md`/`README.md` 中所列签名与 `bgremover image.png` CLI 路径均与代码一致，
无需修复。

### 建议分组

- **发布包：** **#392** 现已可开始；验证 tag、release body 与 macOS/Linux
  产物后关闭史诗 **#389**。
- **质量速赢：** **#406** 与 **#404** 体量小、自包含且 ready-for-PR — 适合作为
  发布路径之外的短小质量 PR，但与发布路径分开（不同模块，无共享 diff）。
- 不把 **#299/#318/#245** 混入发布路径；它们分别属于质量、研究和外部阻塞工作。

评估：**相关性** = 对 roadmap/用户的重要性，**复杂度** = 预计实现工作量。

| # | 标题 | 相关性 | 复杂度 | 推荐下一步 |
|---|------|--------|--------|------------|
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | 发布 v2.5.0（CHANGELOG/版本号/tag/产物） | 🟠 高 | 🟡 中 | **可开始** – #390、#391 与 #384 已关闭。 |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | [Epic] 更新用户文档并发布 release | 🟠 高 | 🟢 低（剩余） | **接近完成** – 只剩 #392。 |
| [#404](https://github.com/NikolayDA/picture_helper/issues/404) | 预览渲染：尺寸不匹配未降级到 COLOR | 🟡 中 | 🟢 低 | **Ready for PR** – 防御性包裹 `compose_relief`/`compose_gloss`，尺寸不匹配时回退到 `base`，并加 render/pixel 回归测试。潜在但范围清晰。 |
| [#406](https://github.com/NikolayDA/picture_helper/issues/406) | 死代码：`eufymake_export.py` 中未使用的 `_derive_physical_size` | 🟢 低 | 🟢 低 | **Ready for PR** – 删除该函数、清理 `parse_size_mm` 导入，并把 CLAUDE.md 的几何说明更新为 `_derive_target`/项目模型路径。简单，验收标准完整。 |
| [#408](https://github.com/NikolayDA/picture_helper/issues/408) | 文档/代码审计：API/CLI 文档与函数签名一致（无 drift） | 🟢 低 | 🟢 低 | **信息性 / 可关闭** – 审计无发现，无需代码/文档修复。可选后续：通过 autodoc 生成真正的 `docs/api.md`，以便自动捕获未来 drift。 |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 低 | 🟢 低 | **v2.5.0 后** – 优先 lasso、可写 NumPy、完整 wand mask 与 brush 参数化。 |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟢 低 | 🟡 中 | **需细化** – 先证明语义；仅为已证实的误报改代码并保留 #303。 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan 因 "Quota exceeded" 失败 | 🟡 中 | 🟢 低 | **Blocked（外部）** – repo 侧加固经 #322/#342（已关闭）完成；剩余 blocker 是 OpenAI/billing quota。恢复 quota 后手动触发一次 scheduled scan，然后关闭。 |

### 推荐下一步（PR 顺序）

1. 把 **#406** 与 **#404** 作为短小质量 PR 提前处理 — 两者均已核实、自包含且
   ready-for-PR（不同模块，低风险）。
2. 随后执行 **#392**；验证 tag、release body 与两个产物后关闭史诗 **#389**。
3. v2.5.0 后处理 **#299**；**#318** 仅作研究（需细化）；把 **#408** 作为无需操作
   的信息性审计关闭；保持 **#245** 阻塞直到外部 quota 恢复。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
