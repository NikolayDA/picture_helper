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
- PR 浪潮 **#280–#283** 落地了每周 benchmark 并实现了三项发现：**#235**
  （共享 undo/redo 预算，PR #281，已关闭）、**#275**（已本地化的百万像素提示，
  PR #282）和 **#270**（经 `ai_process.py` 的 rembg/ONNX 子进程，PR #283）。
  #275 与 #270 已在代码中完成，仅需关闭其 issue。

### 仍然开放

- **O1 🟠 — 更多 runtime 语言。** 应用内可切换德语和英语。现有文档语言
  es/fr/uk/zh 尚不是 runtime locales；如需要，请在 `bgremover.i18n`
  中逐 key 添加并用测试保护。
- **O7 ✅ — rembg/ONNX 子进程已完成（PR #283，issue #270）。** 不可中断的
  AI 推理现已在经 `spawn` 启动的进程（`ai_process.py`）中运行；作为 AI 应急
  出口的 `QThread.terminate()` 已移除。issue #270 仅需关闭。

## 开放的 GitHub Issues — 优先级评估（2026-06-15）

PR 浪潮 **#280–#283** 之后，仍有 **7** 个开放 issue。**#235** 已通过 PR #281
关闭。**#270**（PR #283）和 **#275**（PR #282）已在代码中实现，仅需关闭其
issue。新增三项性能发现——**#277/#278/#279**——来自每周 benchmark 运行
（#280）；按 owner 的 triage，它们**尚未**被确认为代码回归，因为 2026-06-08
的基线没有环境指纹。所有开放 issue 均已对照当前代码重新核实。

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#270](https://github.com/NikolayDA/picture_helper/issues/270) | 将 rembg/ONNX 推理移入子进程（#231 的后续） | 🟠 高 | 🟡 中 | **代码已完成（PR #283，`ai_process.py`）。** 核实并关闭 issue；路线图 O7 已完成 |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | 性能回归：JPEG（+38.4%） | 🟡 中 | 🟡 中 | 待细化：尚未确认为代码回归。为 benchmark 增加环境指纹 + 确认运行（中位数），然后才与兼容基线比较。与 #278/#279 合并处理 |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | 性能回归：TIFF（+21.8%） | 🟡 中 | 🟡 中 | 同 #277：共享的 benchmark 加固；只有在兼容的确认运行之后才调查 encode 路径（`save_image_file`） |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | 性能回归：WebP（+13.7%） | 🟡 中 | 🟡 中 | 同 #277/#278：一个共享 PR 处理指纹 + 中位数确认；只报告已确认的回归 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI：Codex Security Scan 因 “Quota exceeded” 失败 | 🟡 中 | 🟢 低 | 受阻（外部）：在账户侧恢复 quota。仓库内只能做更清晰的失败处理（优雅跳过）+ 可选升级到 Node 24，不强制改 `setup-node` |
| [#275](https://github.com/NikolayDA/picture_helper/issues/275) | 百万像素“图像过大”提示未本地化 | 🟢 低 | 🟢 低 | **代码已完成（PR #282）。** `_too_large_message` 现走 `tr("status.image_too_large[_mp]", …)`（de/en）；核实并关闭 issue |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README：匿名用户访问 clone URL 返回 404 | 🟢 低 | 🟢 低 | 需要决策：公开或私有/邀请制，再更新 clone 指引或关闭（“Runde 5” 已修复） |

### 推荐 PR 顺序

1. **#270 + #275** — 二者均已在代码中完成（PR #283 / #282）：核实并关闭 issue。
2. **#277/#278/#279** — 一个共享 PR：为 benchmark 增加环境指纹与确认运行（中位数）；仅在兼容基线下报告回归。范围清晰，可直接做 PR。
3. **#245** — 在外部恢复 quota；可选的 workflow 加固（优雅跳过 + Node 24）作为单独的小型 PR。
4. **#161** — 决定发布模式，再更新文档或关闭。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
