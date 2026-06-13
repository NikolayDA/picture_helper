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

### 仍然开放

- **O1 🟠 — 更多 runtime 语言。** 应用内可切换德语和英语。现有文档语言
  es/fr/uk/zh 尚不是 runtime locales；如需要，请在 `bgremover.i18n`
  中逐 key 添加并用测试保护。

## 开放的 GitHub Issues — 优先级评估（2026-06-14）

目前有 **8** 个开放 issue。对描述、代码、测试和文档的复核确认了五个
可执行问题。另三个 issue（#161/#203/#204）在没有更多证据时不能构成
本仓库的任务，应关闭或补充可复现的发布/依赖路径。

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README：匿名用户访问 clone URL 返回 404 | 🟢 低 | 🟢 低 | HTTPS URL 本身正确；仓库保持私有时以 `not planned` 关闭，否则明确发布方式 |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — CVE 集合 | 🟢 低 | 🟢 低 | 不在项目 snapshot 中；没有可复现依赖路径时以 `not planned` 关闭，且不要保留错误的严重性数据 |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | PyJWT 2.7.0 — CVE 集合 | 🟢 低 | 🟢 低 | 不在项目 snapshot 中；没有可复现路径时以 `not planned` 关闭，并修正严重性和失效的 GHSA 链接 |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | INSTALL 审查：releases、Raspberry Pi 和 macOS 诊断 | 🟡 中 | 🟢 低 | 三项发现仍有效；同时更新根文档和五份翻译，并如实说明 release 工件的可用性 |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` 可能不安全地终止 worker | 🟡 中 | 🟠 高 | 有效的安全/稳定性问题；阻塞的 native 调用需要架构决策，而当前测试明确保留了缺陷行为 |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` 加载完整 PyQt6 GUI | 🟡 中 | 🟡 中 | 正确、文档充分且可直接提 PR；使用 PEP 562 惰性导出保持公共 API |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | 缺失迁移仍会提升 `schema_version` | 🟡 中 | 🟢 低 | Bug 已确认；反转现有测试，并在加入真实迁移前明确版本 0 的语义 |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo 内存限制未包含 redo 栈 | 🟢 低 | 🟡 中 | 将范围缩小为共享 undo/redo 预算；原始图像和 Qt 分配仅在测量后纳入 |

### 推荐 PR 顺序

1. **#226** — 六种语言中均已确认的小型文档修复；必须决定或明确限制 release 可用性。
2. **#232** — PEP 562 惰性导出并增加 import 回归测试；无需更多澄清。
3. **#234** — 缺少迁移时不得提升版本，并修正当前期待相反行为的测试。
4. **#231** — 先确定取消模型；对于永久阻塞的 native 调用，子进程是可靠方案。
5. **#235** — 明确范围后，可选实现共享 undo/redo 内存预算。
6. **#161/#203/#204** — 除非补充具体发布或依赖路径，否则以 `not planned` 关闭。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
