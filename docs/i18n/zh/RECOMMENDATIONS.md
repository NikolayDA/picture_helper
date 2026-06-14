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

### 仍然开放

- **O1 🟠 — 更多 runtime 语言。** 应用内可切换德语和英语。现有文档语言
  es/fr/uk/zh 尚不是 runtime locales；如需要，请在 `bgremover.i18n`
  中逐 key 添加并用测试保护。
- **O7 🟠 — rembg/ONNX 子进程（#231 的后续，跟踪于 #270）。** PR #267
  限制了关闭回退，但不可中断的 AI 工作仍在线程中运行，以 `terminate()`
  作为应急出口。完整方案将 rembg/ONNX 移入子进程。

## 开放的 GitHub Issues — 优先级评估（2026-06-14，收尾 triage）

PR **#263–#269** 合并并关闭 **#261**（由 PR #268 解决）后，仍有 **5** 个
开放 issue。先前开放的九个 issue——**#231、#234、#248、#249、#257、#258、
#259、#260** 和 **#261**——已通过合并的 PR 关闭。从 #231 推迟的架构后续
（rembg/ONNX 子进程，路线图 **O7**）已登记为 **#270**。所有开放 issue
均已对照当前代码重新核实。

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#270](https://github.com/NikolayDA/picture_helper/issues/270) | 将 rembg/ONNX 推理移入子进程（#231 的后续） | 🟠 高 | 🟡 中 | 独立架构 PR：PR #267 仅限制了关闭。将 rembg/ONNX 移入子进程，使 `terminate()` 不再是 AI 应急出口；为关闭/取消/阻塞调用编写测试 |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` 加载完整 PyQt6 GUI | 🟡 中 | 🟡 中 | 可提 PR：用 PEP 562 惰性导出保持公共 API，并增加 import 回归测试。代码未变：`__init__.py:15-43` 仍在 re-export GUI |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI：Codex Security Scan 因 “Quota exceeded” 失败 | 🟡 中 | 🟢 低 | 账户侧恢复 quota；仓库只改进错误处理并可选升级到 Node 24，不强制改 `setup-node` |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo 内存限制未包含 redo 栈 | 🟢 低 | 🟡 中 | 共享 undo/redo 预算；原图/Qt 内存仅测量。代码未变：`canvas_history.py` 仅计 `_undo_bytes`，redo 仅由 `maxlen` 限制 |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README：匿名用户访问 clone URL 返回 404 | 🟢 低 | 🟢 低 | “Runde 5” 已修复；先决定公开或私有/邀请制，再更新 clone 指引或关闭 |

### 推荐 PR 顺序

1. **#232** — 使用 PEP 562 惰性导出实现轻量导入。
2. **#245** — 在外部恢复 quota；可选的 workflow 加固（Node 24）单独处理。
3. **#235** — 实现共享 undo/redo 历史预算。
4. **#161** — 决定发布模式，再更新文档或关闭。
5. **#270** — 将 rembg/ONNX 子进程规划为独立架构 PR（#231 的后续）。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
