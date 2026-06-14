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

Triage 后仍有 **13** 个开放 issue。**#203/#204** 因并非项目依赖而以
`not planned` 关闭；**#226/#244** 已由 PR #246 和 #256 完成。11 个 issue
具有可执行的仓库范围。#161 需要先决定发布模式，#245 主要需要账户侧修复
quota/billing。

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README：匿名用户访问 clone URL 返回 404 | 🟢 低 | 🟢 低 | “Runde 5” 已修复；先决定公开或私有/邀请制，再修改 clone 指引 |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` 可能不安全地终止 worker | 🟠 高 | 🟡 中 | 首个 PR：限制第二次 wait，记录并测试失败；子进程架构另行处理 |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` 加载完整 PyQt6 GUI | 🟡 中 | 🟡 中 | 可提 PR：使用 PEP 562 惰性导出保持公共 API，并增加 import 回归测试 |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | 缺失迁移仍会提升 `schema_version` | 🟡 中 | 🟢 低 | 与 #259 合并：缺失迁移不得标记或修改 settings |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo 内存限制未包含 redo 栈 | 🟢 低 | 🟡 中 | 共享 undo/redo 预算；原图与 Qt 内存仅测量和记录 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI：Codex Security Scan 因 “Quota exceeded” 失败 | 🟡 中 | 🟢 低 | 账户侧恢复 quota；仓库只改进错误处理，不改 `setup-node` |
| [#248](https://github.com/NikolayDA/picture_helper/issues/248) | Escape 清除选区而非取消多边形套索 | 🟡 中 | 🟡 中 | 与 #260 合并：集中实现 crop → 套索 → 取消选区 |
| [#249](https://github.com/NikolayDA/picture_helper/issues/249) | 文件关联传入图像路径但应用不打开 | 🟡 中 | 🟡 中 | 可提 PR：将启动路径和 macOS `QFileOpenEvent` 通过已校验的加载路径打开 |
| [#257](https://github.com/NikolayDA/picture_helper/issues/257) | Release follow-up：publish 上下文、tag gate 与重跑工件 | 🟠 高 | 🟡 中 | 下个 tag 前的独立首要 PR；workflow、文档和测试一起改 |
| [#258](https://github.com/NikolayDA/picture_helper/issues/258) | 图像加载限制可能预分配 512 MiB | 🟠 高 | 🟡 中 | 独立 PR：分块读取、本地化错误和精确边界显示 |
| [#259](https://github.com/NikolayDA/picture_helper/issues/259) | Recent Files 会修改未来 schema | 🟠 高 | 🟡 中 | 与 #234 合并：未来 schema 全程只读 |
| [#260](https://github.com/NikolayDA/picture_helper/issues/260) | 自动丢弃 crop 后工具光标错误 | 🟡 中 | 🟢 低 | 与 #248 合并并测试集中取消和光标恢复 |
| [#261](https://github.com/NikolayDA/picture_helper/issues/261) | 画笔 overlay 每次移动都扫描完整掩码 | 🟡 中 | 🟡 中 | 独立性能 PR，加入选中像素计数器和 spy test |

### 推荐 PR 顺序

1. **#257** — 在下个 tag 前让 release workflow 可靠。
2. **#258** — 移除预分配并修正大小错误。
3. **#234 + #259** — QSettings 迁移与未来 schema 保护。
4. **#248 + #260** — 集中 Escape/crop 取消与正确光标。
5. **#231** — 先交付有界 shutdown fallback；子进程另做。
6. **#261** — 从常用画笔路径移除 O(图像大小) 扫描。
7. **#249** — 实际处理文件关联和 macOS open events。
8. **#232** — 使用 PEP 562 惰性导出实现轻量导入。
9. **#235** — 实现共享 undo/redo 历史预算。
10. **#245** — 外部恢复 quota；workflow 加固单独处理。
11. **#161** — 决定发布模式，再更新文档或关闭。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
