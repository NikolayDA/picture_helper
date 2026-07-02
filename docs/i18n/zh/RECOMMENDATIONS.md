[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · **简体中文**

# 代码分析与优先级建议：BgRemover

## 评级标准

| 符号 | 优先级 | 含义 |
|------|--------|------|
| 🔴 | 严重 | 缺陷、崩溃或数据丢失 |
| 🟠 | 高 | 对可靠性或可维护性有明显影响 |
| 🟡 | 中 | 对质量、可读性或可测试性有价值的改进 |
| 🟢 | 低 | 可选的润色或流程改进 |

## 当前状态（2026-07-02）

活跃的代码分析清单为空。Ruff、mypy 与本地测试套件仍是新 PR 之前的基线。本轮新增：
开放议题的分诊已更新至真实状态（18 个开放议题）。

### 自上次评审以来已完成

- **旧基线稳定：** **N1/N2/N4/N5/N6/N7/N8** 与 **O2–O7** 仍已完成；史诗
  **#329/#344/#358/#384**（N9–N12）及导出修复 **#363** 已合并、由测试/CI 覆盖并归档。
- **自 2026-06-25 评审以来已关闭：** **#404**、**#406** 与 **#408**（PR #412）——
  此前列出的预览/死代码/审计发现均已完成；`_derive_physical_size` 已不复存在，
  且渲染路径在尺寸不匹配时会降级到 COLOR。
- **重构核心已交付：** 步骤条/`stepper.py`、卡片检查器、引导式导航、上下文工具以及
  设计令牌（`ACCENT`/`CARD_STYLE`）已通过 PR #412/#423 落地（DE/EN 字符串，
  `tests/test_workflow.py`）；仅剩润色（见分诊）。

### 仍待处理

- **O1 🟠 — 更多运行时语言。** 德语与英语可切换；es/fr/uk/zh 尚不是运行时语言环境。
  这与重构议题 **#430** 相符——在 `bgremover.i18n` 中逐键补齐并以测试覆盖。

## GitHub 开放议题 — 分诊状态（2026-07-02）

截至 2026-07-02，GitHub 显示 **18** 个开放议题。2026-06-29 的快照已过时：
#404/#406/#408 已关闭（PR #412），而**重构浪潮（引导式工作流）**是当前的活跃路线图。
其核心已交付；剩余为润色（**#414**）、i18n/文档（史诗 **#425**：#430/#431/#432）、
质量保障/发布（史诗 **#426**：#433/#434/#435）、待定发布 **#392** 以及独立事项
**#299/#318/#245**。**#442** 正是跟踪本次文档刷新。

**评论巡查：** 无新的外部评论。#245/#299/#392 上的所有者备注与当前状态一致；
#442（2026-07-02）记录了本次审计——无需更新议题。

### 合理的组合

- **接近完成的史诗：** #418 与 #424 的**全部**子议题均已关闭 → 核实并关闭。
  #413 仅剩 #414 开放；其令牌已在 `theme.py` 中——补上浅色卡片样式后即可关闭。
- **i18n/文档（#425）：** #430（ES/FR/UK/ZH）可解锁一致性测试；#431（文档）与
  #432（截图）在 UI 视觉定稿后跟进。
- **QA/发布（#426）：** #433 已大体被 PR #423 覆盖（核对缺口后关闭）；#434 可提 PR；
  将 #435（CHANGELOG/版本）与 #392 对齐。
- **发布：** 决定重构是随 **v2.5.0**（#392/#435 一起）发布，还是在后续版本提升中发布。

评估：**相关性** = 对路线图/用户的重要性，**复杂度** = 预估实现工作量。

| # | 标题 | 相关性 | 复杂度 | 建议的下一步 |
|---|------|--------|--------|--------------|
| [#418](https://github.com/NikolayDA/picture_helper/issues/418) | EPIC：引导式工作流 – 步骤条与导航 | 🟠 高 | 🟢 低 | **核实并关闭** – 子议题已关闭（PR #423）。 |
| [#413](https://github.com/NikolayDA/picture_helper/issues/413) | EPIC：卡片检查器 – 右栏改为卡片 | 🟠 高 | 🟢 低 | **接近完成** – 仅 #414 开放。 |
| [#414](https://github.com/NikolayDA/picture_helper/issues/414) | 集中卡片容器与强调色令牌 | 🟡 中 | 🟢 低 | **可提 PR** – 令牌已有；补浅色卡片样式。 |
| [#424](https://github.com/NikolayDA/picture_helper/issues/424) | EPIC：统一设计系统与主题化 | 🟠 高 | 🟢 低 | **核实并关闭** – 子议题已关闭。 |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC：国际化与文档 | 🟠 高 | 🟡 中 | **进行中** – #430/#431/#432 开放。 |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | 新增 UI 字符串（步骤/卡片/导航） | 🟠 高 | 🟡 中 | **可提 PR** – ES/FR/UK/ZH；DE/EN 见 PR #423。 |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | 将 ANLEITUNG 与 README 更新为引导式流程 | 🟡 中 | 🟡 中 | **UI 冻结后** – 6 语镜像，链接测试。 |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | 为重构重制应用截图 | 🟢 低 | 🟢 低 | **受阻** – 仅当 UI 视觉定稿后。 |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC：重构的质量保障与发布 | 🟠 高 | 🟢 低 | **进行中** – #433/#434/#435 开放。 |
| [#433](https://github.com/NikolayDA/picture_helper/issues/433) | 步骤条/卡片/导航冒烟测试 | 🟡 中 | 🟢 低 | **核对缺口** – 已大体被 PR #423 覆盖。 |
| [#434](https://github.com/NikolayDA/picture_helper/issues/434) | 可见性与动作接线回归 | 🟡 中 | 🟢 低 | **可提 PR** – 每步的动作回调。 |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | 重构的 CHANGELOG 与版本提升 | 🟡 中 | 🟢 低 | **与 #392 对齐** – 厘清发布顺序。 |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | 切出 v2.5.0 版本 | 🟠 高 | 🟡 中 | **就绪** – 决定与重构的顺序。 |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC：更新用户文档并切出发布 | 🟠 高 | 🟢 低 | **在 #392 后关闭** – 仅剩发布。 |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | 测试卫生：弱断言/冗余 | 🟢 低 | 🟢 低 | **发布之后** – 高影响优先。 |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | 可复用 WF 中 job 级权限覆盖 | 🟢 低 | 🟡 中 | **需细化** – 先验证 GitHub 语义。 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan「Quota exceeded」 | 🟡 中 | 🟢 低 | **受阻（外部）** – OpenAI 计费/配额。 |
| [#442](https://github.com/NikolayDA/picture_helper/issues/442) | RECOMMENDATIONS.md 已过时 | 🟡 中 | 🟢 低 | **本次更新已解决** – 可关闭。 |

### 接下来推荐（PR 顺序）

1. **收尾维护：** 核实子议题并关闭接近完成的史诗 **#418** 与 **#424**；完成 **#414**
   （浅色卡片样式），随后关闭 **#413**。
2. 优先推进 **#430**（ES/FR/UK/ZH 字符串）——解锁 i18n 一致性；随后在 UI 定稿后处理
   **#431**/**#432**。
3. 实现 **#434**（回归）；确认 **#433** 在 PR #423 中的覆盖并将其关闭。
4. **发布：** 协调推进 **#435** + **#392**，随后关闭史诗 **#426** 与 **#389**。
5. **#299** 在发布后处理；**#318** 仅做调研（需细化）；**#245** 保持外部受阻；
   本次刷新落地后关闭 **#442**。

## 往轮记录

- **2026-06-29 分诊** — #404/#406/#408 完成（PR #412），开启重构浪潮。
- **v2.2，「admiring-mayer」（#1–#15）** — 外部清单，已完成或在误报时舍弃。

完整的历史发现与工作日志（第 1–5 轮）：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md).
