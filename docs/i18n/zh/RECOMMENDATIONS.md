[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · **简体中文**

# 代码分析与优先级建议：BgRemover

## 评级标准

| 符号 | 优先级 | 含义 |
|------|--------|------|
| 🔴 | 严重 | 缺陷、崩溃或数据丢失 |
| 🟠 | 高 | 对可靠性或可维护性有明显影响 |
| 🟡 | 中 | 对质量、可读性或可测试性有价值的改进 |
| 🟢 | 低 | 可选的润色或流程改进 |

## 当前状态（2026-07-04）

活跃的代码分析清单为空。Ruff、mypy 与本地测试套件仍是新 PR 之前的基线。本轮新增：
**#461**、**#414** 与史诗 **#413** 已关闭。PR #473 集中了卡片度量，并移除
`theme.py` 之外最后一个强调色 hex。新开放的 Dark Mode/原型对齐组是 **#474–#480**。
GitHub 现在显示 **18** 个开放的路线图/Backlog 议题。

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
  落地，**#465** 有意标记为 `not_planned`。PR #467 关闭了 #466 后续的三个 P2
  （缩放方向、viewport 锚定、高度 dab 预览），并刷新了分诊快照。
- **#461 已关闭（2026-07-04）：** PR #467 刷新的快照与 GitHub 实际状态一致；
  该议题本身在合并后仍保持开放，现于本轮关闭。
- **卡片检查器已完成：** **#414** 已通过 PR #473 落地（集中 `CARD_*` 令牌、
  明/暗卡片样式、强调色 hex 防回归 guard）。这也完成了史诗 **#413**。

### 仍待处理

- **O1 🟠 — 更多运行时语言。** 德语与英语可切换；es/fr/uk/zh 尚不是运行时语言环境。
  这与重构议题 **#430** 相符——在 `bgremover.i18n` 中逐键补齐并以测试覆盖。
- **O8 🟢 — 原型误差:生成后高度工具仍被锁定。** 在
  `design/Prototyp A - Geführter Workflow.dc.html` 中,「从图像生成高度图」只
  设置了 `heightGen`,并未把当前图层切换为 `Höhe` 角色——`heightDisabled` 仍
  依赖旧角色(PR #460 的评审发现)。仅影响原型模拟;实际应用已会自动激活新的
  HEIGHT 图层(#347)。

## GitHub 开放议题 — 分诊状态（2026-07-04）

截至 2026-07-04，GitHub 显示 **18** 个开放的路线图/Backlog 议题：Dark Mode/原型对齐
（**#474/#475/#476/#477/#478/#479/#480**）、i18n/文档
（**#425/#430/#431/#432**）、rollout/发布（**#426/#435/#392/#389**），以及
独立事项 **#299/#318/#245**。**#461** 是已修正的快照漂移；**#414** 与
**#413** 也已在 PR #473 后关闭。

### 合理的组合

- **Dark Mode 1:1（#474）：** 将 #475/#476/#477/#479 作为令牌波次，#478 作为
  canvas checker 修复，#480 作为 spec/drift-test 收尾。
- **i18n/文档（#425）：** #430（ES/FR/UK/ZH）可解锁一致性测试；#431（文档）与
  #432（截图）在 UI 视觉定稿后跟进。
- **Rollout/发布：** #426 只因 #435 仍开放；将 #435 与 #392 协调，然后关闭
  #426/#389。
- **Backlog：** #299 放在发布后；#318 先细化语义；#245 仍因 OpenAI 计费/配额
  外部受阻。

评估：**相关性** = 对路线图/用户的重要性，**复杂度** = 预估实现工作量。

| # | 标题 | 相关性 | 复杂度 | 建议的下一步 |
|---|------|--------|--------|--------------|
| [#474](https://github.com/NikolayDA/picture_helper/issues/474) | EPIC：Dark Mode 1:1 对齐原型 A | 🟠 高 | 🟡 中 | **新增** – 组合 #475–#480。 |
| [#475](https://github.com/NikolayDA/picture_helper/issues/475) | Dark：对齐背景表面 | 🟠 高 | 🟢 低 | **从这里开始** – 基础表面优先。 |
| [#476](https://github.com/NikolayDA/picture_helper/issues/476) | Dark：透明边框/hairline | 🟡 中 | 🟢 低 | **随 #475** – 边框令牌。 |
| [#477](https://github.com/NikolayDA/picture_helper/issues/477) | Dark：对齐强调/按钮色 | 🟠 高 | 🟢 低 | **随 #475** – 交互色。 |
| [#478](https://github.com/NikolayDA/picture_helper/issues/478) | Canvas checker 忽略当前主题 | 🟡 中 | 🟡 中 | **令牌后** – 调色板 + 主题切换。 |
| [#479](https://github.com/NikolayDA/picture_helper/issues/479) | 补齐原型缺失色彩令牌 | 🟡 中 | 🟡 中 | **随 spec** – 只用已证令牌。 |
| [#480](https://github.com/NikolayDA/picture_helper/issues/480) | REDESIGN_SPEC 色表 + drift 测试 | 🟡 中 | 🟡 中 | **最终收尾** – 在 #475–#479 后。 |
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

1. 组合 **#474**：令牌波次 #475/#476/#477/#479，随后 #478 与 #480。
2. 优先推进 **#430**（ES/FR/UK/ZH 字符串）——解锁 i18n 一致性；随后在 UI 定稿后处理
   **#431**/**#432**。
3. **发布：** 协调推进 **#435** + **#392**，随后关闭史诗 **#426** 与 **#389**。
4. **#299** 在发布后处理；**#318** 仅做调研（需细化）；**#245** 保持外部受阻。

## 往轮记录

- **2026-06-29 分诊** — #404/#406/#408 完成（PR #412），开启重构浪潮。
- **v2.2，「admiring-mayer」（#1–#15）** — 外部清单，已完成或在误报时舍弃。

完整的历史发现与工作日志（第 1–5 轮）：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md).
