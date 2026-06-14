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

目前有 **15** 个开放 issue。对描述、代码、测试和文档的复核表明：**九个**
问题范围清晰、可直接提 PR；两个（#231/#235）需先做架构或范围决策；#245 是
基础设施/计费问题（并非代码缺陷）；另三个（#161/#203/#204）在没有更多证据时
不能构成本仓库的任务。

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README：匿名用户访问 clone URL 返回 404 | 🟢 低 | 🟢 低 | HTTPS URL 本身正确；仓库保持私有时以 `not planned` 关闭，否则明确发布方式 |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — CVE 集合 | 🟢 低 | 🟢 低 | 不在项目 snapshot 中；没有可复现依赖路径时以 `not planned` 关闭，且不要保留错误的严重性数据 |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | PyJWT 2.7.0 — CVE 集合 | 🟢 低 | 🟢 低 | 不在项目 snapshot 中；没有可复现路径时以 `not planned` 关闭，并修正严重性和失效的 GHSA 链接 |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | INSTALL 审查：releases、Raspberry Pi 和 macOS 诊断 | 🟡 中 | 🟢 低 | 可提 PR：三项发现仍有效；同时更新根文档和五份翻译，并如实说明 release 工件的可用性 |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` 可能不安全地终止 worker | 🟡 中 | 🟠 高 | 需细化：阻塞的 native 调用需要架构决策（子进程）；当前测试保留了缺陷行为 |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` 加载完整 PyQt6 GUI | 🟡 中 | 🟡 中 | 可提 PR：使用 PEP 562 惰性导出保持公共 API，并增加 import 回归测试 |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | 缺失迁移仍会提升 `schema_version` | 🟡 中 | 🟢 低 | 可提 PR：阻止版本提升、反转测试，并明确版本 0 的语义 |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo 内存限制未包含 redo 栈 | 🟢 低 | 🟡 中 | 需细化：将范围缩小为共享 undo/redo 预算；原始图像和 Qt 分配仅在测量后纳入 |
| [#244](https://github.com/NikolayDA/picture_helper/issues/244) | 死代码：`ImageCanvas._zoom` 与未用的 `launch_worker` wrapper | 🟢 低 | 🟢 低 | 可提 PR：删除 `_zoom`，对 `launch_worker` 在删除与文档化 API 间抉择；小型清理 PR |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI：Codex Security Scan 因 “Quota exceeded” 失败 | 🟡 中 | 🟢 低 | 基础设施/计费：在账户侧恢复 OpenAI 配额；让 workflow 对配额耗尽更健壮，并将 `setup-node` 升到 Node 24 |
| [#247](https://github.com/NikolayDA/picture_helper/issues/247) | 活动 crop 在图像变换后残留并产生错误像素 | 🟠 高 | 🟡 中 | 可提 PR（首选）：每次图像变更都重置瞬态状态；issue 中已给出回归测试（400×200 + 旋转 90°） |
| [#248](https://github.com/NikolayDA/picture_helper/issues/248) | Escape 清除选区而非取消多边形套索 | 🟡 中 | 🟡 中 | 可提 PR：Escape 优先级 crop → 套索 → 取消选区；与 #247 共享瞬态状态契约 |
| [#249](https://github.com/NikolayDA/picture_helper/issues/249) | 文件关联传入图像路径但应用不打开 | 🟡 中 | 🟡 中 | 可提 PR：将启动路径和 macOS `QFileOpenEvent` 通过已校验的加载路径打开 |
| [#250](https://github.com/NikolayDA/picture_helper/issues/250) | Release workflow 在没有完整 CI gate 时即发布工件 | 🟠 高 | 🟡 中 | 可提 PR（下个 tag 前）：用 `needs` 强制完整 CI、校验 tag/`project.version`、移除 `\|\| true` |
| [#251](https://github.com/NikolayDA/picture_helper/issues/251) | 空选区在擦除后仍保留 overlay-QPixmap | 🟡 中 | 🟢 低 | 可提 PR（快速）：掩码为空时释放 overlay pixmap；issue 中已给出精确补丁 |

### 推荐 PR 顺序

1. **#247** — 高：正确性/数据缺陷（过期的 crop 矩形产生透明填充像素）；范围完整并含回归测试。
2. **#250** — 下个 release tag 前的高优先项：用 `needs` 强制完整 CI gate、对齐 tag/版本、移除 `|| true`。
3. **#251** — 快速内存修复：空掩码释放 overlay pixmap；精确补丁已在 issue 中。
4. **#244** — 死代码清理（删除 `_zoom`，决定 `launch_worker`）；小型低风险清理 PR。
5. **#234** — 缺少迁移时不得提升版本，并修正当前期待相反行为的测试。
6. **#248** — Escape 优先级 crop → 套索 → 取消选区；与 #247 共享瞬态状态契约，可一并处理。
7. **#232** — PEP 562 惰性导出并增加 import 回归测试。
8. **#249** — 将启动路径和 macOS `QFileOpenEvent` 通过已校验的加载路径打开。
9. **#226** — 六种语言的文档修复；如实记录 release 可用性。
10. **#245** — 在账户侧恢复 OpenAI 计费；让 scan workflow 对配额耗尽更健壮，并将 `setup-node` 升到 Node 24。
11. **#231** — 先确定取消模型（对永久阻塞的 native 调用用子进程），再实现。
12. **#235** — 明确范围后再实现共享 undo/redo 内存预算。
13. **#161/#203/#204** — 除非补充具体发布或依赖路径，否则以 `not planned` 关闭。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
