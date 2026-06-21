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

## 打开的 GitHub Issues — Triage 状态 (2026-06-21)

截至 2026-06-21，GitHub 仍显示 **5** 个打开的 issues：**#245**、**#299**、
**#318**、**#322** 和 **#339**。此前列出的项目/图层与安全测试 issues
**#323**、**#324**、**#326** 和 **#329–#335** 已在 merge commits **#337**、
**#338** 与 **#340** 中完成。**#322** 现在也有 **#342**，应在验证 merge 后
补充评论并关闭。

| # | 标题 | Label/status 建议 | 评论/status 建议 |
|---|------|-------------------|------------------|
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan 因 "Quota exceeded" 失败 | `security`; **保持打开 / blocked external** | 评论说明 repo 侧加固已由 #323/#324 和 #322/#342 覆盖；剩余 blocker 是 OpenAI/billing quota。恢复 quota 后手动触发一次 scheduled scan，然后关闭。 |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | `quality`, `testing`; **open / low priority** | 评论说明它不是产品或 CI blocker；等相关 tests 被修改时作为 opportunistic cleanup 合并处理。无需更改 status。 |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | `enhancement`, `testing`; **needs refinement** | 评论说明改代码前需记录 called workflow 中 top-level vs. job-level permissions 的 GitHub semantics；不得削弱 #303 OIDC guard。 |
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI: scheduled Codex Security Scan 的 maintenance/skip path | `security`; **#342 后关闭** | 评论说明 #342 实现了保守的手动维护开关 (`CODEX_SECURITY_SCAN_ENABLED=false`)，包含 skip output 和 regression tests；验证 merge 后关闭。 |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF 不支持作为输入格式 | **添加 labels:** `enhancement`, `documentation`（或可用时 `question`）；**needs decision** | 评论要求产品决策：明确文档说明 HEIC 不支持，或规划 optional `pillow-heif`/`HEIF` allowlist 加 load test。决策前保持打开。 |

### 推荐 Issue 操作

1. 在确认 #342 merge 到 `main` 后评论并关闭 **#322**。
2. 为 **#339** 添加 label 并作出明确产品决策（文档澄清 vs. HEIC feature）。
3. 保持 **#245** 打开但标记为 externally blocked；链接 #322/#342 作为已完成
   的 repo-side 部分。
4. 不立即实现 **#318**；先记录 GitHub permission semantics。
5. 保持 **#299** 为低优先级 test cleanup。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
