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

### 仍然开放

- **O1 🟠 — 更多 runtime 语言。** 应用内可切换德语和英语。现有文档语言
  es/fr/uk/zh 尚不是 runtime locales；如需要，请在 `bgremover.i18n`
  中逐 key 添加并用测试保护。
- **O7 ✅ — rembg/ONNX 子进程已完成（PR #283，issue #270 已关闭）。** 不可中断的
  AI 推理现已在经 `spawn` 启动的进程（`ai_process.py`）中运行；作为 AI 应急
  出口的 `QThread.terminate()` 已移除。健壮性/内存方面的后续发现已在 **#285**（PR #289）修复并关闭。

## 开放的 GitHub Issues — 优先级评估（2026-06-19）

截至 2026-06-19，共有 **4** 个开放 issue。自 2026-06-18 的评估以来，测试/发布
加固浪潮大体已合并：**#307、#308、#309、#310** 和 **#312** 现已 **关闭**（snapshot
的 meta issue **#313** 亦然）。三项性能发现 **#277/#278/#279**（每周 benchmark
#280）已通过本 PR 的 benchmark 加固（环境指纹 + 中位数确认；仅对可比较基线报告）
而 **关闭**。PR **#317**（关闭了 #309/#310）从其 Codex review 中衍生出一个新的后续
**#318**（可复用 workflow guard 中的 job 级权限覆盖）。仍开放的是 **#311**
（release 正文）、**#318**（权限 guard）、**#245**（CI quota，外部受阻）以及低
优先级测试卫生项 **#299**。所有开放 issue 均已对照当前代码重新核实。

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#311](https://github.com/NikolayDA/picture_helper/issues/311) | 发布：从 CHANGELOG 填充 release 正文 | 🟡 中 | 🟡 中 | **可做 PR** — 范围明确：手动补全 v2.4.1 正文；让 `release-linux.yml` 从 `## [X.Y.Z]` 推导 notes 而非硬编码文本（复用时亦然），并在 `test_release_gate.py` 中加回归测试 |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | 测试：尊重可复用 WF 中的 job 级权限覆盖 | 🟡 中 | 🟡 中 | **需打磨** — 先确认 GitHub 的 startup-validation 语义（top-level 与 effective-per-job）；目前是纯理论上的误报（`ci.yml` 中没有 job 级覆盖），且 OIDC guard #303 不得被削弱 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI：Codex Security Scan 因 “Quota exceeded” 失败 | 🟡 中 | 🟢 低 | **受阻（外部）：** 在账户侧恢复 quota。仓库内只能做更清晰的失败处理（优雅跳过） |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | 测试卫生：弱断言/冗余 | 🟢 低 | 🟢 低 | 非正确性缺陷；先做最有价值的（endpoint 移动、合并 `set_brush_size`），其余按需 |

### 可合并 Issues

- **#318** 是对已合并的权限 guard（#309/#310）的后续，应保持独立——在触及 `_required_permissions` 之前，需先有 GitHub 语义的文档依据。
- **#311** 保持独立，因为它涉及 release workflow、CHANGELOG 提取和现有 release notes。
- **#299** 是机会型测试卫生，只应在本来就触及相关测试时顺手处理。

### 推荐 PR 顺序

1. **#311** — 从 CHANGELOG 推导 release 正文并补回 v2.4.1 notes；范围明确且用户可见（否则已发布的修复在 release 页面上不可见）。
2. **#318** — 在 GitHub 语义有文档依据后打磨权限 guard，且不削弱 OIDC 回归用例。
3. **#245** — 在外部恢复 quota；仓库侧之后只需更清晰的失败处理。
4. **#299** — 测试卫生按需处理。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
