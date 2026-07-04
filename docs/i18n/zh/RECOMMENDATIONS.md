[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · **简体中文**

# 代码分析与优先级建议：BgRemover

## 评级标准

| 符号 | 优先级 | 含义 |
|------|--------|------|
| 🔴 | 严重 | 缺陷、崩溃或数据丢失 |
| 🟠 | 高 | 对可靠性或可维护性有明显影响 |
| 🟡 | 中 | 对质量、可读性或可测试性有价值的改进 |
| 🟢 | 低 | 可选的润色或流程改进 |

## 当前状态（2026-07-05）

活跃的代码分析清单为空。Ruff、mypy 与本地测试套件仍是新 PR 前的基线。
自 2026-07-04 快照后，Dark Mode/原型对齐组 **#474–#480**（PR #482）以及
rail 图标/状态颜色波次 **#483–#488**（PR #489）已关闭。本 follow-up 前，
GitHub 显示 **12** 个开放议题（含 **#490**）；合并/关闭这个 snapshot fix 后，
仍剩 **11** 个路线图/Backlog 议题。

### 自上次评审以来已完成

- **旧基线稳定：** **N1/N2/N4/N5/N6/N7/N8** 与 **O2–O7** 仍已完成；史诗
  **#329/#344/#358/#384**（N9–N12）及导出修复 **#363** 已合并、由测试/CI 覆盖并归档。
- **自 2026-06-25 评审以来已关闭：** **#404**、**#406** 与 **#408**（PR #412）——
  此前列出的预览/死代码/审计发现均已完成；`_derive_physical_size` 已不复存在，
  且渲染路径在尺寸不匹配时会降级到 COLOR。
- **重构核心已交付：** 步骤条/`stepper.py`、卡片检查器、引导式导航、上下文工具以及
  设计令牌（`ACCENT`/`CARD_STYLE`）已通过 PR #412/#423 落地（DE/EN 字符串，
  `tests/test_workflow.py`）。
- **Rail/zoom 波次已完成：** **#455/#456/#457/#458/#463/#464** 已通过 PR #466
  落地，**#465** 有意标记为 `not_planned`；PR #467 关闭三个 #466 P2 并刷新了分诊快照。
- **卡片检查器已完成：** **#414** 已通过 PR #473 落地（集中 `CARD_*` 令牌、
  明/暗卡片样式、强调色 hex 防回归 guard）。这也完成了史诗 **#413**。
- **Dark Mode 与 rail 图标已完成：** PR #482 关闭 **#474–#480**（暗色表面、
  hairline、强调色、checkerboard、缺失令牌、REDESIGN_SPEC drift test）；
  PR #489 关闭 **#483–#488**（矢量图标、状态/主题颜色、移除 PNG fallback、
  文档/测试/评审修复）。
- **#490 处理中：** 本 PR 修复 PR #482/#489 后 Recommendations 快照漂移，并保持六个
  语言镜像同步。

### 仍待处理

- **O1 🟠 — 更多运行时语言。** 德语与英语可切换；es/fr/uk/zh 尚不是运行时语言环境。
  这与重构议题 **#430** 相符——在 `bgremover.i18n` 中逐键补齐并以测试覆盖。
- **O8 🟢 — 原型误差：生成后高度工具仍被锁定。** 在
  `design/Prototyp A - Geführter Workflow.dc.html` 中，「从图像生成高度图」只
  设置了 `heightGen`，并未把当前图层切换为 `Höhe` 角色——`heightDisabled` 仍
  依赖旧角色（PR #460 的评审发现）。仅影响原型模拟；实际应用已会自动激活新的
  HEIGHT 图层（#347）。

## GitHub 开放议题 — 分诊状态（2026-07-05）

截至 2026-07-05，GitHub 在本 PR 前显示 **12** 个开放议题（含 **#490**）。
本 follow-up 合并/关闭后，仍剩 **11** 个路线图/Backlog 议题：i18n/文档
（**#425/#430/#431/#432**）、rollout/发布（**#426/#435/#392/#389**），以及
Backlog/外部事项（**#299/#318/#245**）。

### 合理的组合

- **#490：** 本 PR 关闭 PR #482/#489 后的快照漂移；不会留下后续实现票。
- **i18n/文档（#425）：** #430（ES/FR/UK/ZH）可解锁一致性测试；#431（文档）与
  #432（截图）在 UI 视觉定稿后跟进。
- **Rollout/发布：** #426 只因 #435 仍开放；将 #435 与 #392 协调，然后关闭
  #426/#389。
- **Backlog：** #299 放在发布后；#318 先细化语义；#245 仍因 OpenAI 计费/配额
  外部受阻。

评估：**相关性** = 对路线图/用户的重要性，**复杂度** = 预估实现工作量。

| # | 标题 | 相关性 | 复杂度 | 建议的下一步 |
|---|------|--------|--------|--------------|
| [#490](https://github.com/NikolayDA/picture_helper/issues/490) | Dark Mode 与 rail 图标波次后刷新 triage snapshot | 🟡 中 | 🟢 低 | **本 PR** – 合并后关闭。 |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC：国际化与文档 | 🟠 高 | 🟡 中 | **进行中** – #430/#431/#432 开放。 |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | 新增 UI 字符串（步骤/卡片/导航） | 🟠 高 | 🟡 中 | **可提 PR** – ES/FR/UK/ZH；DE/EN 见 PR #423。 |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | 将 ANLEITUNG 与 README 更新为引导式流程 | 🟡 中 | 🟡 中 | **UI 冻结后** – 6 语镜像，链接测试。 |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | 为重构重制应用截图 | 🟢 低 | 🟢 低 | **受阻** – 仅当 UI 视觉定稿后。 |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC：重构的质量保障与发布 | 🟠 高 | 🟢 低 | **接近完成** – 仅剩 #435 开放。 |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | 重构的 CHANGELOG 与版本提升 | 🟡 中 | 🟢 低 | **与 #392 对齐** – 厘清发布顺序。 |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | 切出 v2.5.0 版本 | 🟠 高 | 🟡 中 | **就绪** – 决定与重构的顺序。 |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC：更新用户文档并切出发布 | 🟠 高 | 🟢 低 | **在 #392 后关闭** – 仅剩发布。 |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | 测试卫生：弱断言/冗余 | 🟢 低 | 🟢 低 | **发布之后** – 高影响优先。 |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | 可复用 WF 中 job 级权限覆盖 | 🟢 低 | 🟡 中 | **需细化** – 先验证 GitHub 语义。 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan「Quota exceeded」 | 🟡 中 | 🟢 低 | **受阻（外部）** – OpenAI 计费/配额。 |

### 接下来推荐（PR 顺序）

1. 优先推进 **#430**（ES/FR/UK/ZH 字符串）——解锁 i18n 一致性；随后在 UI 定稿后处理
   **#431**/**#432**。
2. **发布：** 协调推进 **#435** + **#392**，随后关闭史诗 **#426** 与 **#389**。
3. **#299** 在发布后处理；**#318** 仅做调研（需细化）；**#245** 保持外部受阻。

## 往轮记录

- **2026-06-29 分诊** — #404/#406/#408 完成（PR #412），开启重构浪潮。
- **v2.2，「admiring-mayer」（#1–#15）** — 外部清单，已完成或在误报时舍弃。

完整的历史发现与工作日志（第 1–5 轮）：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md).
