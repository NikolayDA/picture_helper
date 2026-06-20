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

## 开放的 GitHub Issues — 优先级评估（2026-06-20）

截至 2026-06-20，共有 **14** 个开放 issue。自 2026-06-19 的评估以来，**#311**
（release 正文）已 **关闭**。新增的有 epic **#329**（项目/图层数据模型——高度图、
光泽与 EufyMake 导出的基础）及其六个子 issue **#330–#335**，外加测试覆盖发现
**#326**（GIF 被声明为输入格式但未测试）。图层 epic 是优先级路线图的第 1 名：
**#330**（无 Qt 的领域模型）是无依赖的基石，可立即着手，而其余子 issue 沿依赖链
受阻（#330 → #331 → #332/#333 → #334 → #335）。上一轮仍开放的有：**#318**（权限
guard）、**#245**（CI quota，外部受阻）、三个 **#245** 加固后续 **#322–#324**，
以及低优先级测试卫生项 **#299**。所有开放 issue 均已对照当前代码重新核实。

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#329](https://github.com/NikolayDA/picture_helper/issues/329) | [Epic] 项目/图层数据模型（高度图/光泽/EufyMake 的基础） | 🟠 高 | 🟠 高 | **Epic / 跟踪** — 路线图第 1 名；通过六个子 issue 推进，本身不出 PR |
| [#330](https://github.com/NikolayDA/picture_helper/issues/330) | 领域模型 `Project` + `Layer`（无 Qt） | 🟠 高 | 🟡 中 | **可做 PR** — 无依赖的基石；无 Qt、严格类型、合成/角色、`tests/test_project_model.py`。epic 的起点 |
| [#331](https://github.com/NikolayDA/picture_helper/issues/331) | 项目级 undo/redo（图层感知历史） | 🟠 高 | 🟠 高 | **受阻于 #330** — 图层感知历史，可在接入 canvas 前独立测试 |
| [#332](https://github.com/NikolayDA/picture_helper/issues/332) | Canvas：合成渲染 + 活动图层 | 🟠 高 | 🟠 高 | **受阻于 #330/#331** — 最大的一块；行为切换为基于图层，单图层等价 |
| [#333](https://github.com/NikolayDA/picture_helper/issues/333) | 项目文件格式：保存/加载（版本化、原子、校验） | 🟠 高 | 🟠 高 | **受阻于 #330**（与 #332 并行）— `.bgrproj` ZIP 容器，原子/校验/版本化 |
| [#334](https://github.com/NikolayDA/picture_helper/issues/334) | UI：图层面板 + 项目菜单 + i18n | 🟠 高 | 🟠 高 | **受阻于 #330/#332/#333** — 面板 + 菜单动作，i18n de/en 对等 |
| [#335](https://github.com/NikolayDA/picture_helper/issues/335) | 迁移与集成（图像→项目、recent、设置、导出） | 🟠 高 | 🟡 中 | **受阻于 #330/#332/#333/#334** — epic 的收尾 issue；现有流程不得回归 |
| [#326](https://github.com/NikolayDA/picture_helper/issues/326) | 测试：GIF 输入格式已声明但未测试 | 🟡 中 | 🟢 低 | **可做 PR，可立即做** — 经 `ImageLoadWorker` 的加载测试覆盖 `_ALLOWED_IMAGE_FORMATS` 对 GIF 的 gate；不含保存/导出 |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | 测试：尊重可复用 WF 中的 job 级权限覆盖 | 🟡 中 | 🟡 中 | **需打磨** — 先确认 GitHub 的 startup-validation 语义（top-level 与 effective-per-job）；目前是纯理论上的误报（`ci.yml` 中没有 job 级覆盖），且 OIDC guard #303 不得被削弱 |
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI：为计划的 Codex Security Scan 增加维护/跳过路径 | 🟡 中 | 🟡 中 | **#245 后续** — 范围决策：手动开关 vs. 可见的 auto-graceful-skip（或两者）；在 `cadence` job 加 gate，“disabled → skipped，而非 failed”，保持最小权限（scan job 不得有 `issues: write`），静态测试 |
| [#323](https://github.com/NikolayDA/picture_helper/issues/323) | 测试：覆盖安全 issue 同步的 severity 过滤与空 findings | 🟢 低 | 🟢 低 | **#245 后续，可立即做** — 针对 `reportable: false`、severity 阈值与“No reportable findings”的回归测试；经 `--dry-run`/直接调用，无需网络 |
| [#324](https://github.com/NikolayDA/picture_helper/issues/324) | Security：针对仓库范围的 Codex 扫描 prompt 文档治理测试 | 🟢 低 | 🟢 低 | **#245 后续，可立即做** — 静态测试：prompt 仍列出当前顶层安全面；补充现有 prompt 断言 |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | 测试卫生：弱断言/冗余 | 🟢 低 | 🟢 低 | 非正确性缺陷；先做最有价值的（endpoint 移动、合并 `set_brush_size`），其余按需 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI：Codex Security Scan 因 “Quota exceeded” 失败 | 🟡 中 | 🟢 低 | **受阻（外部）：** 在账户侧恢复 quota。仓库侧加固现于 **#322–#324** 跟踪；优雅跳过对应 #322 的变体 B |

### 可合并 Issues

- 图层 epic **#329** 按规定顺序通过其子 issue 推进；**#332** 与 **#333** 可在 #330 之后并行。
- **#323/#324**（均为 #245 后续、无需网络的静态安全扫描测试）可合并到一个 PR。
- **#318** 保持独立——在触及 `_required_permissions` 之前，需先有 GitHub 语义的文档依据。
- **#299** 是机会型测试卫生，只应在本来就触及相关测试时顺手处理。

### 推荐 PR 顺序

1. **#330** — 图层 epic 中无依赖的基石；解阻 #331/#332/#333。
2. **#326** — 快速、范围明确的收益（GIF 加载测试），填补一处覆盖缺口。
3. **#323 / #324** — 无需网络的安全扫描加固，随时可做。
4. **#331 → #332 / #333 → #334 → #335** — 图层 epic 沿其依赖链推进。
5. **#322** — 在审慎的 auto/manual 决策后做维护/跳过路径（#245 后续）。
6. **#318** — 在 GitHub 语义有文档依据后打磨权限 guard，且不削弱 OIDC 回归用例。
7. **#245** — 在账户侧恢复 quota（外部受阻）。
8. **#299** — 测试卫生按需处理。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
