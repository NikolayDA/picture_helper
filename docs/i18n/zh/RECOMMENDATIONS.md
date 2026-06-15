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

## 开放的 GitHub Issues — 优先级评估（2026-06-15）

PR **#280–#290** 之后，仍有 **5** 个开放 issue。最近的后续 issue **#285**
（PR #289）和 **#286**（PR #290）已实现**并关闭**——**#235**（PR #281）、
**#270**（PR #283）和 **#275**（PR #282）亦然。仍开放的是三项性能发现——
**#277/#278/#279**——来自每周 benchmark 运行（#280）；按 owner 的 triage，
**尚未**被确认为代码回归，因为 2026-06-08 的基线没有环境指纹。此外还有
**#245**（CI quota，外部受阻）和 **#161**（README 的 clone URL，需 owner 决策）。
所有开放 issue 均已对照当前代码重新核实。

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | 性能回归：JPEG（+38.4%） | 🟡 中 | 🟡 中 | 待细化：尚未确认为代码回归。为 benchmark 增加环境指纹 + 确认运行（中位数），然后才与兼容基线比较。与 #278/#279 合并处理 |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | 性能回归：TIFF（+21.8%） | 🟡 中 | 🟡 中 | 同 #277：共享的 benchmark 加固；只有在兼容的确认运行之后才调查 encode 路径（`save_image_file`） |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | 性能回归：WebP（+13.7%） | 🟡 中 | 🟡 中 | 同 #277/#278：一个共享 PR 处理指纹 + 中位数确认；只报告已确认的回归 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI：Codex Security Scan 因 “Quota exceeded” 失败 | 🟡 中 | 🟢 低 | 受阻（外部）：在账户侧恢复 quota。仓库内只能做更清晰的失败处理（优雅跳过）+ 可选升级到 Node 24，不强制改 `setup-node` |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README：匿名用户访问 clone URL 返回 404 | 🟢 低 | 🟢 低 | 需要决策：公开或私有/邀请制，再更新 clone 指引或关闭（“Runde 5” 已修复） |

### 推荐 PR 顺序

1. **#277/#278/#279** — 一个共享 PR：为 benchmark 增加环境指纹与确认运行（中位数）；仅在兼容基线下报告回归。
2. **#245** — 在外部恢复 quota；可选的 workflow 加固（优雅跳过 + Node 24）作为单独的小型 PR。
3. **#161** — 决定发布模式，再更新文档或关闭。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
