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
- **#164/#167/#168** 已完成（PR #172/#174/#173）；其余发现在 #176/#178 中
  聚焦推进。
- **2026-06-06 已验证为干净关闭**（PR #188–#193，每个都带回归测试，
  `make check` 通过 — 504 passed）：**#163**（CHANGELOG 链接改为 GitHub 可
  解析的真实 commit SHA；补齐四个缺失的 2.3.0 特性 + idna/urllib3 条目；
  有意未创建真实 git tag）、**#165/#180**（TESTING.md：`addopts` 过滤器、
  `ui_smoke`、每周 schedule、shellcheck、`make coverage`）、**#184**（load
  generation + `content_revision` 复检以抵御迟到的 async 加载）、**#182**
  （`PIP_CONSTRAINT` 接入 AppImage 构建）、**#183**（license-check 只读 +
  独立评论 job）、**#177**（行为断言 + 新增 `tests/test_history_popup.py`）。

### 仍然开放

- **O1 🟠 — 更多 runtime 语言。** 应用内可切换德语和英语。现有文档语言
  （es/fr/uk/zh）尚未作为 runtime locales；如需要，请在 `bgremover.i18n`
  中逐 key 添加，并用 parity/smoke tests 保护。

## 开放的 GitHub Issues — 优先级评估（2026-06-09）

现有 **十一** 个开放 issue。**#200/#201 已在 PR #209 中完成**（构建后端已固定）。
`pip-audit` 安全批次（2026-06-07，#200–#206）以及一处死代码发现（#199）仍在分诊中；
#195 已关闭并验证。

针对项目实际状态（`requirements/constraints.txt` + `pyproject.toml`）对安全批次
进行分诊：

- **#200/#201 已完成（PR #209）** — `setuptools` 现已在 `pyproject.toml`
  （`[build-system]`）和 `constraints.txt` 中固定为 `>=78.1.1`，`wheel` 固定为
  `==0.46.2`；与 CVE 绑定的回归测试加以保护。
- **#202（pip）** 仍具可操作性：`pip` 在 CI/dev 中不受控地随附。
- **#203（cryptography）/#204（pyjwt）** **不是**项目依赖（纯传递/系统层）→
  仅作参考，无需改动 `constraints.txt`。
- **#205（urllib3）/#206（idna）** 在项目中**已干净固定**（`urllib3==2.7.0`、
  `idna==3.15`）；仅系统层发现 → 可关闭。

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#202](https://github.com/NikolayDA/picture_helper/issues/202) | pip 24.0 — HIGH/MEDIUM：5 个 CVE（路径遍历、符号链接） | 🟡 中 | 🟢 低 | 可提 PR；在 CI setup 步骤 + dev 文档中要求 `pip>=26.1.2` |
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | 代码审查后续（Low）：E741、check_untyped_defs、cancel_ai 体验、shutdown_all | 🟡 中 | 🟢 低 | 可提 PR（来自 #167）；`E741`/`check_untyped_defs` 在 `pyproject.toml` 中仍未改 |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README 审计：一个外部链接失效，一处内部术语 | 🟡 中 | 🟢 低 | 受阻："Runde 5" 术语已移除；仅剩 clone URL（需所有者就仓库可见性决定） |
| [#199](https://github.com/NikolayDA/picture_helper/issues/199) | 死代码（Low）：`canvas_history.py` 中只写的 `_redo_max` | 🟢 低 | 🟢 低 | 可提 PR；删除一行（该模块严格类型化 — `make check`） |
| [#185](https://github.com/NikolayDA/picture_helper/issues/185) | 安全：macOS 诊断泄露本地路径 + 原始日志尾部（隐私） | 🟢 低 | 🟡 中 | 可提 PR；脱敏 `$HOME`/路径 + `--include-raw-logs` 标志 + shell 测试 |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | 测试审计后续（Low）：与私有内部解耦 + 去重 | 🟢 低 | 🟡 中 | 可提 PR（来自 #168） |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | 注释审计：语言不一致与小措辞不准确 | 🟢 低 | 🟢 低 | 可提 PR；`right_panel.py`/`main_window.py` 中存在英文 docstring |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — HIGH/MEDIUM：6 个 CVE | 🟢 低 | 🟢 低 | 非项目依赖（传递/系统）→ 仅作参考，无需改动 `constraints.txt` |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — HIGH/MEDIUM：5 个 CVE | 🟢 低 | 🟢 低 | 非项目依赖 → 仅作参考，无需项目操作 |
| [#205](https://github.com/NikolayDA/picture_helper/issues/205) | urllib3 2.6.3 — MEDIUM：2 个 CVE | 🟢 低 | 🟢 低 | 无需操作；项目已固定 `urllib3==2.7.0`（干净）→ 可关闭 |
| [#206](https://github.com/NikolayDA/picture_helper/issues/206) | idna 3.11 — MEDIUM：经 `idna.encode()` 的 DoS | 🟢 低 | 🟢 低 | 无需操作；项目已固定 `idna==3.15`（干净）→ 可关闭 |

### 推荐 PR 顺序

1. **#200 已完成（PR #209）** — 已在 `pyproject.toml`（`[build-system]`）**和** `constraints.txt` 中固定 `setuptools>=78.1.1`；CRITICAL RCE 已关闭。
2. **#201 已完成（PR #209）** — 已在 `constraints.txt` 中固定 `wheel==0.46.2`；与 #200 合并为单个供应链固定 PR。
3. **#202** — 在 CI setup 步骤 + dev 安装文档中要求 `pip>=26.1.2`。
4. **#176** — 来自 #167 的代码质量批次：收窄 `E741`、逐步启用 `check_untyped_defs`、cancel_ai 体验、清空 `shutdown_all` 的线程引用。
5. **#199** — 从 `canvas_history.py` 删除只写的 `_redo_max`（琐碎修复，`make check` 覆盖回归）。
6. **#166** — docstring 语言清理，作为小型维护 PR。
7. **#185** — 脱敏 macOS 诊断（`$HOME`/路径）+ `--include-raw-logs` 标志 + shell 测试。
8. **#178** — 让测试与私有内部解耦 + 减少重复测试（来自 #168）。
9. **#205/#206 可关闭** — 项目固定已正确（`urllib3==2.7.0`、`idna==3.15`）；仅系统层发现。
10. **#203/#204 作为观察项** — 非项目依赖；仅当未来功能直接引入时再固定。
11. **#161 暂缓** — "Runde 5" 已完成；仅剩 clone URL（需所有者就仓库可见性决定）。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
