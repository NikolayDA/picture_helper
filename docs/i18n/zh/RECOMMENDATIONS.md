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
  和 **#249**；**#261** 已通过 PR #268 解决。

### 仍然开放

- **O1 🟠 — 更多 runtime 语言。** 应用内可切换德语和英语。现有文档语言
  es/fr/uk/zh 尚不是 runtime locales；如需要，请在 `bgremover.i18n`
  中逐 key 添加并用测试保护。
- **O7 🟠 — rembg/ONNX 子进程（#231 的后续）。** PR #267 限制了关闭回退，
  但不可中断的 AI 工作仍在线程中运行，以 `terminate()` 作为应急出口。
  完整方案将 rembg/ONNX 移入子进程——独立的架构 PR，尚无 issue。

## 开放的 GitHub Issues — 优先级评估（2026-06-14，收尾 triage）

PR **#263–#269** 合并后，仅剩 **5** 个开放 issue。先前列出的八个 issue
（**#231、#234、#248、#249、#257、#258、#259、#260**）已合并并自动关闭。
**#261** 已由 PR **#268** 修复，但因缺少 `Closes` 关键字而在管理上仍开放，
应予关闭。剩下四个可执行 issue；均已对照当前代码重新核实。

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` 加载完整 PyQt6 GUI | 🟡 中 | 🟡 中 | 可提 PR：用 PEP 562 惰性导出保持公共 API，并增加 import 回归测试。代码未变：`__init__.py:15-43` 仍在 re-export GUI |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo 内存限制未包含 redo 栈 | 🟢 低 | 🟡 中 | 共享 undo/redo 预算；原图/Qt 内存仅测量。代码未变：`canvas_history.py` 仅计 `_undo_bytes`，redo 仅由 `maxlen` 限制 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI：Codex Security Scan 因 “Quota exceeded” 失败 | 🟡 中 | 🟢 低 | 账户侧恢复 quota；仓库只改进错误处理并可选升级到 Node 24，不强制改 `setup-node` |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README：匿名用户访问 clone URL 返回 404 | 🟢 低 | 🟢 低 | “Runde 5” 已修复；先决定公开或私有/邀请制，再更新 clone 指引或关闭 |
| [#261](https://github.com/NikolayDA/picture_helper/issues/261) | 画笔 overlay 每次移动都扫描完整掩码 | ✅ 已完成 | — | 已由 PR **#268**（已合并）修复；issue 因缺少 `Closes` 关键字仍开放——应在管理上关闭 |

### 推荐 PR 顺序

1. **#232** — 使用 PEP 562 惰性导出实现轻量导入。
2. **#235** — 实现共享 undo/redo 历史预算。
3. **#245** — 在外部恢复 quota；可选的 workflow 加固（Node 24、错误处理）单独处理。
4. **#161** — 决定发布模式，再更新文档或关闭。
5. **O7** — 将 rembg/ONNX 子进程规划为独立架构 PR（#231 的后续）。
6. **Admin** — 关闭 **#261**（已通过 PR #268 完成）。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
