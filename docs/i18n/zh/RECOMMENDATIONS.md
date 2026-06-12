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
- **#164/#167/#168** 已完成（PR #172/#174/#173）；其余发现此后也已通过
  #176/#178 完成。
- **2026-06-06 已验证为干净关闭**（PR #188–#193，每个都带回归测试，
  `make check` 通过 — 504 passed）：**#163**（CHANGELOG 链接改为 GitHub 可
  解析的真实 commit SHA；补齐四个缺失的 2.3.0 特性 + idna/urllib3 条目；
  有意未创建真实 git tag）、**#165/#180**（TESTING.md：`addopts` 过滤器、
  `ui_smoke`、每周 schedule、shellcheck、`make coverage`）、**#184**（load
  generation + `content_revision` 复检以抵御迟到的 async 加载）、**#182**
  （`PIP_CONSTRAINT` 接入 AppImage 构建）、**#183**（license-check 只读 +
  独立评论 job）、**#177**（行为断言 + 新增 `tests/test_history_popup.py`）。
- **2026-06-07 安全批次已完成**（#200/#201/#202/#205/#206，经 PR
  #209/#211/#222）：setuptools/wheel/pip/urllib3/idna 已固定或强制，
  每项都有与 CVE 绑定的回归测试保护。

### 仍然开放

- **O1 🟠 — 更多 runtime 语言。** 应用内可切换德语和英语。现有文档语言
  （es/fr/uk/zh）尚未作为 runtime locales；如需要，请在 `bgremover.i18n`
  中逐 key 添加，并用 parity/smoke tests 保护。

## 开放的 GitHub Issues — 优先级评估（2026-06-12）

现有 **14** 个开放 issue：观察项 #203/#204、暂缓的 #161、文档/审计发现
#218/#226/#227/#236，以及来自 2026-06-11 审计的代码质量批次 #229–#235。
#203/#204 不是项目依赖（纯传递/系统层）→ 仅作参考，无需改动
`constraints.txt`。

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README 审计：clone URL 无法访问 | 🟡 中 | 🟢 低 | 受阻（需所有者就仓库可见性决定） |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — 6 个 CVE | 🟢 低 | 🟢 低 | 观察项，无需项目操作 |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — 5 个 CVE | 🟢 低 | 🟢 低 | 观察项，无需项目操作 |
| [#218](https://github.com/NikolayDA/picture_helper/issues/218) | CHANGELOG：`[Unreleased]` 缺少条目 | 🟡 中 | 🟢 低 | 可提 PR（按现有风格补充七条条目） |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | INSTALL 审查：指向空的 Releases + 两处小问题 | 🟡 中 | 🟢 低 | 可提 PR（文档修复）；工件提示取决于打标签决定 |
| [#227](https://github.com/NikolayDA/picture_helper/issues/227) | RECOMMENDATIONS 审计：issue 概览过期 | 🟡 中 | 🟢 低 | 已由本次更新解决 → 可关闭该 issue |
| [#229](https://github.com/NikolayDA/picture_helper/issues/229) | rembg 预热未创建可复用的推理会话 | 🟠 高 | 🟡 中 | 可提 PR（经 `new_session` 缓存会话） |
| [#230](https://github.com/NikolayDA/picture_helper/issues/230) | 文件在尺寸检查前被完整读入内存 | 🟠 高 | 🟢 低 | 可提 PR（在 `read()` 前加字节上限） |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` 可能不安全地中止 worker | 🟡 中 | 🟠 高 | 需细化（在方案 A/B/C 中决策；短期采用方案 C） |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` 加载完整 PyQt6 GUI | 🟡 中 | 🟡 中 | 可提 PR（经 PEP 562 惰性导出） |
| [#233](https://github.com/NikolayDA/picture_helper/issues/233) | 损坏的 recent_files 设置会破坏菜单构建 | 🟡 中 | 🟢 低 | 可提 PR（防御性 `paths()` + 参数化测试） |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | 缺失的迁移仍会抬升 `schema_version` | 🟢 低 | 🟢 低 | 可提 PR（在首次真实迁移之前） |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo 限制未计入 redo/原始图像 | 🟢 低 | 🟡 中 | 需细化（决定仅改文档 vs. 共享预算） |
| [#236](https://github.com/NikolayDA/picture_helper/issues/236) | session-start.sh 注释：缺少 `benchmark.yml` | 🟢 低 | 🟢 低 | 可提 PR（单行注释修复） |

### 推荐 PR 顺序

1. **#230** — 相关性最高且复杂度低：在读取前加文件大小上限，同时集中覆盖同步和异步路径。
2. **#229** — 复用预热会话；对 AI 流水线收益最大，顺带修正错误的注释。
3. **#233** — 防御性 `paths()` 加参数化测试；契合设置 schema 的健壮性目标。
4. **#236 + #218** — 小型注释/文档修复，宜合并提交；**#227** 已由本次更新解决，可关闭。
5. **#232** — 经 PEP 562 的惰性导出；因测试/导入迁移而属中等规模。
6. **#234** — 小修复；最迟应在首次真实 schema 迁移之前安排。
7. **#226** — 文档修复现在就做；Release 工件提示取决于所有者的打标签决定。
8. **#235** — 先决定语义（仅改文档 vs. 共享预算），再实现。
9. **#231** — 短期采用方案 C（有界等待 + 日志），长期评估方案 B（子进程）。
10. **#203/#204** 继续作为观察项；**#161** 继续受阻（需所有者决定）。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
