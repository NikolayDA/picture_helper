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

当前代码分析清单为空。最近一次 follow-up review 已实现并由测试覆盖；
ruff、mypy 和本地 suite 仍是新 PR 前的 baseline。

### 自上次 Review 以来已完成

- **N1/N2/N4/N5/N6/N7/N8** 已完成：魔棒错误路径、旋转尺寸限制、真实文件
  扩展名、原子保存、CI Qt 包、`rembg` 惰性导入以及 `load_image` docstring。
- **O2/O3/O4/O5/O6** 已实现：Linux AppImage/`.deb`、release workflow、
  每周完整矩阵、PR/Full CI 中的 `ui_smoke`，以及带平台提示的工具快捷键。
- **#164** 已完成并合并（PR #172）：安装指南中的 Python 3.11 AI 提示、
  Releases 链接与本地化 UI 字符串。

### 仍然开放

- **O1 🟠 — 更多 runtime 语言。** 应用内可切换德语和英语。现有文档语言
  （es/fr/uk/zh）尚未作为 runtime locales；如需要，请在 `bgremover.i18n`
  中逐 key 添加，并用 parity/smoke tests 保护。

## 开放的 GitHub Issues — 优先级评估（2026-06-04）

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#168](https://github.com/NikolayDA/picture_helper/issues/168) | 测试套件审计：过期测试、缺失 assertion、私有耦合、覆盖率缺口 | 🔴 高 | 🔴 高 | 🔴 发现已完成（PR #173）；🟠/🟡 仍开放 — 拆分并细化 |
| [#167](https://github.com/NikolayDA/picture_helper/issues/167) | 代码审查：质量、可维护性与小问题 | 🔴 高 | 🟡 中 | Medium 发现（竞态、TOCTOU）→ 已在 PR #174；Low 发现：合并处理 |
| [#163](https://github.com/NikolayDA/picture_helper/issues/163) | CHANGELOG.md：版本链接损坏 + 缺少 2.3.0 条目 | 🔴 高 | 🟡 中 | 内容更新 → 可提 PR；git tag 需要细化 |
| [#165](https://github.com/NikolayDA/picture_helper/issues/165) | TESTING.md：与当前代码相比存在三处不准确 | 🟡 中 | 🟢 低 | 可提 PR |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README 审计：一个外部链接失效，一处内部术语 | 🟡 中 | 🟢 低 | "Runde 5" 修复 → 可提 PR；clone URL → 已阻塞（需决定仓库可见性） |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | 注释审计：语言不一致与小措辞不准确 | 🟢 低 | 🟢 低 | 可提 PR |

### 推荐 PR 顺序

1. **#167 Medium** — `_ensure_rembg_remove()` 中的双重检查锁 + `open_validated_image` 中的 TOCTOU 窗口：已在 **PR #174** 中实现（待合并；Low 发现另行处理）。
2. **#165** — TESTING.md 修正：风险低，范围明确。
3. **#163 内容** — 在 CHANGELOG 中补充缺失的 2.3.0 特性及 `[Unreleased]` 条目；git tag 单独处理。
4. **#161 部分** — 从 README 架构说明中移除"Runde 5"术语（clone URL 修复需要关于仓库可见性的决策）。
5. **#166** — docstring 语言清理，作为小型维护 PR。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
