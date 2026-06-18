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

## 开放的 GitHub Issues — 优先级评估（2026-06-18）

截至 2026-06-18，共有 **12** 个开放 issue。自上次评估（2026-06-15）以来，
**#161**（README 的 clone URL）已于 2026-06-17 **关闭**；与此同时，v2.4.x 发布
周期带来了一批测试/发布加固类 issue（**#299、#307–#312**）；**#313** 跟踪
recommendations snapshot 本身。仍开放的是三项性能发现 **#277/#278/#279**（每周
benchmark #280，按 owner 的 triage **尚未**确认为代码回归）以及 **#245**（CI
quota，外部受阻）。所有开放 issue 均已对照当前代码重新核实。

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#313](https://github.com/NikolayDA/picture_helper/issues/313) | Docs：更新 RECOMMENDATIONS issue snapshot | 🟡 中 | 🟢 低 | Snapshot 的 meta issue：用本次更新对齐后关闭；否则它会把自己算作第 12 个开放 issue |
| [#312](https://github.com/NikolayDA/picture_helper/issues/312) | CI：将 node20 actions 升级到 Node 24 | 🟠 高 | 🟢 低 | GitHub 已带警告强制使用 Node 24；将受影响的 actions（`github-script`、`upload/download-artifact`）统一升级到 node24 大版本，可选 guard 测试 |
| [#311](https://github.com/NikolayDA/picture_helper/issues/311) | 发布：从 CHANGELOG 填充 release 正文 | 🟡 中 | 🟡 中 | 手动补全 v2.4.1 正文；让 `release-linux.yml` 从 `## [X.Y.Z]` 推导 notes 而非硬编码文本——复用时亦然 |
| [#310](https://github.com/NikolayDA/picture_helper/issues/310) | 测试：LICENSES.md 版本 == pyproject | 🟡 中 | 🟢 低 | 快速 pytest，将标题版本与 `[project].version` 比较——在繁重的 License Check 之前捕获 bump 漂移 |
| [#309](https://github.com/NikolayDA/picture_helper/issues/309) | 测试：caller 覆盖可复用 WF 的权限 | 🟡 中 | 🟢 低 | 推广 `test_release_gate.py`：caller job 必须授予被调用 workflow 声明的每项权限（OIDC `id-token: write`） |
| [#308](https://github.com/NikolayDA/picture_helper/issues/308) | 测试：`--ai` 制品中 AI 链可导入 | 🟠 高 | 🟡 中 | 在 `--ai` 构建中做无网络的 spawn 自检，加载 `rembg`+`pymatting` 元数据（回归 #306） |
| [#307](https://github.com/NikolayDA/picture_helper/issues/307) | 测试：以 headless 启动已构建制品 | 🟠 高 | 🟡 中 | 在 build job 中 headless 启动 bundle（捕获启动崩溃 #304 / fork bomb #305）；`publish` 仍由 `needs: build` 把关 |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | 测试卫生：弱断言/冗余 | 🟢 低 | 🟢 低 | 非正确性缺陷；先做最有价值的（endpoint 移动、合并 `set_brush_size`），其余按需 |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | 性能回归：JPEG（+38.4%） | 🟡 中 | 🟡 中 | 尚未确认为代码回归。为 benchmark 增加环境指纹 + 确认运行（中位数）；与 #278/#279 合并处理 |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | 性能回归：TIFF（+21.8%） | 🟡 中 | 🟡 中 | 同 #277：共享的 benchmark 加固；只有在兼容的确认运行之后才调查 encode 路径（`save_image_file`） |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | 性能回归：WebP（+13.7%） | 🟡 中 | 🟡 中 | 同 #277/#278：一个共享 PR 处理指纹 + 中位数确认；只报告已确认的回归 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI：Codex Security Scan 因 “Quota exceeded” 失败 | 🟡 中 | 🟢 低 | 受阻（外部）：在账户侧恢复 quota。仓库内只能做更清晰的失败处理（优雅跳过）+ 可选升级到 Node 24 |

### 可合并 Issues

- **#307/#308** 应放在一起：一个 release artifact verification PR 可 headless 启动 GUI 和 `--ai` bundle，并加入 AI spawn self-check。
- **#309/#310** 都是小型 guard tests，可合并为一个测试加固 PR；**#311** 最好单独做，因为它涉及 release workflow、CHANGELOG 提取和现有 release notes。
- **#277/#278/#279** 应作为 benchmark 可靠性 PR 一起处理；之后再做按格式的 encode 分析才有意义。
- **#312** 是跨所有 workflows 的独立 CI 现代化 PR；**#245** 的 Node 24 部分可以放进去，但 OpenAI quota 仍是外部事项。
- **#299** 是机会型测试卫生，只应在本来就触及相关测试时顺手处理。

### 推荐 PR 顺序

1. **#313** — 更新此 snapshot 并关闭 meta issue，避免计数长期自引用。
2. **#307/#308** — 对 release bundle 做 headless 冒烟测试（GUI + `--ai`）；避免再次发布启动崩溃/fork bomb。
3. **#312** — 在 GitHub 移除 fallback 之前，将 node20 actions 升级到 Node 24。
4. **#309/#310** — 通用 workflow permissions 和 LICENSES 版本，作为快速测试加固 PR。
5. **#311** — 从 CHANGELOG 生成 release body，并补回 v2.4.1 notes。
6. **#277/#278/#279** — 共享 benchmark 指纹 + 中位数确认；仅在兼容基线下报告回归。
7. **#245** — 在外部恢复 quota；仓库侧之后只需更清晰的失败处理。
8. **#299** — 测试卫生按需处理。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
