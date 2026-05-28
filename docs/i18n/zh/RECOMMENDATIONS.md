[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · **简体中文**

# 代码分析与评级建议：BgRemover

## 评级标准

| 符号 | 优先级 | 含义 |
|------|--------|------|
| 🔴 | 严重 | 必须修复：会导致错误、崩溃或不一致 |
| 🟠 | 高 | 应尽快修复：明显影响可靠性或可维护性 |
| 🟡 | 中 | 建议处理：提升代码质量、可读性或可测试性 |
| 🟢 | 低 | 可选：打磨和补充改进 |

---

## 当前状态（2026，Round 5 之后）

单体→包的切分已经完成：`BgRemover.py` 已由 `bgremover/` 包取代。Canvas 状态封装在 `CanvasHistory`、`CanvasLasso` 和 `CanvasSelection` 中；`MainWindow` 已拆分为 toolbar、history popup、worker controller、RightPanel、MenuActions 和 RecentFiles。测试不再耦合 Canvas 私有字段，mypy 也不再依赖过去按错误码关闭的检查。

第 1-5 轮的完整历史发现和工作日志已归档到：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。

---

## 未完成的 polish 项

| 优先级 | 建议 | 工作量 | 状态 |
|--------|------|--------|------|
| 🟢 | 补充 Python 3.11/3.13 classifiers | 小 | 未完成 |
| 🟡 | i18n drift test：保持 `CHANGELOG`/`INSTALL` 结构同步 | 中 | 未完成 |
| 🟢 | 统一模块文档语言，避免 DE/EN 混用 | 中 | 未完成 |
| 🟢 | 为 README 添加截图 | 小 | 未完成 |
