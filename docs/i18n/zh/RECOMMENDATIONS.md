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

### 仍然开放

- **O1 🟠 — 更多 runtime 语言。** 应用内可切换德语和英语。现有文档语言
  （es/fr/uk/zh）尚未作为 runtime locales；如需要，请在 `bgremover.i18n`
  中逐 key 添加，并用 parity/smoke tests 保护。

## 开放的 GitHub Issues — 优先级评估（2026-06-11）

现有 **五** 个开放 issue：观察项 #203/#204、暂缓的 #161，以及文档审计发现
#218（CHANGELOG 缺漏）和 #226（INSTALL 审查）。**#176 已完成**（代码质量批次见 PR #198/#214，
issue 已关闭）；此前 #166/#178/#185（PR #219–#221）、#205/#206（PR #222）与
#199/#200/#201/#202（PR #215/#209/#211）已完成。`pip-audit`
安全批次（2026-06-07，#200–#206）仅剩观察项 #203/#204 开放；#195 已关闭并验证。

针对项目实际状态（`requirements/constraints.txt` + `pyproject.toml`）对安全批次
进行分诊：

- **#200/#201 已完成（PR #209）** — `setuptools` 现已在 `pyproject.toml`
  （`[build-system]`）和 `constraints.txt` 中固定为 `>=78.1.1`，`wheel` 固定为
  `==0.46.2`；与 CVE 绑定的回归测试加以保护。
- **#202（pip）已完成（PR #211）** — 已在 CI setup 步骤（`ci.yml`/`pr-ci.yml`/
  `ui-nightly.yml`/`benchmark.yml`/`license-check.yml`）、Web SessionStart 钩子和
  dev 安装文档中强制 `pip>=26.1.2`；一个与 CVE 绑定的回归测试加以保护。
- **#203（cryptography）/#204（pyjwt）** **不是**项目依赖（纯传递/系统层）→
  仅作参考，无需改动 `constraints.txt`。
- **#205（urllib3）/#206（idna）已完成（PR #222）** — 项目固定了已修补的版本
  （`urllib3==2.7.0`、`idna==3.15`）；与 CVE 绑定的回归测试将其冻结，
  SessionStart 钩子现在使用 constraints 安装。

| # | 标题 | 相关性 | 复杂度 | 建议 |
|---|------|--------|--------|------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README 审计：一个外部链接失效，一处内部术语 | 🟡 中 | 🟢 低 | 受阻："Runde 5" 术语已移除；仅剩 clone URL（需所有者就仓库可见性决定） |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — HIGH/MEDIUM：6 个 CVE | 🟢 低 | 🟢 低 | 非项目依赖（传递/系统）→ 仅作参考，无需改动 `constraints.txt` |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — HIGH/MEDIUM：5 个 CVE | 🟢 低 | 🟢 低 | 非项目依赖 → 仅作参考，无需项目操作 |
| [#218](https://github.com/NikolayDA/picture_helper/issues/218) | CHANGELOG：`[Unreleased]` 缺少多条条目（PR #174、#190–#215） | 🟡 中 | 🟢 低 | 通过文档 PR 按现有风格补充七条缺失条目 |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | INSTALL 审查：Release 工件章节指向空的 Releases + 两处小问题 | 🟡 中 | 🟢 低 | 补充"工件自 v2.3.0 起提供"提示（或打 v2.3.0 标签，由所有者决定）；"Bookworm 或更新" + 链接 `diagnose_mac.sh`，经文档 PR 落实 |

### 推荐 PR 顺序

1. **#200 已完成（PR #209）** — 已在 `pyproject.toml`（`[build-system]`）**和** `constraints.txt` 中固定 `setuptools>=78.1.1`；CRITICAL RCE 已关闭。
2. **#201 已完成（PR #209）** — 已在 `constraints.txt` 中固定 `wheel==0.46.2`；与 #200 合并为单个供应链固定 PR。
3. **#202 已完成（PR #211）** — 已在 CI setup 步骤、SessionStart 钩子 + dev 安装文档中强制 `pip>=26.1.2`；CVE 批次（路径遍历/符号链接/模块劫持）已关闭。
4. **#176 已完成（PR #198/#214）** — 移除全局 `E741` ignore，`check_untyped_defs` 已对 `canvas`/`main_window`/`worker_controller` 启用，cancel_ai 的等待通过状态栏消息可见，`shutdown_all` 清空线程引用；为 `app.py`/`main_window.py` 新增专门测试。已于 2026-06-10 对照 `main` 验证（`make check` 通过）。
5. **#199 已完成（PR #215）** — 已从 `canvas_history.py` 删除只写的 `_redo_max`；回归测试 `test_redo_stack_capped_by_maxlen`，`make check` 通过。
6. **#166 已完成（PR #219）** — 包内英文 docstring/注释已全部德语化；"无自有副本"注释已修正。
7. **#185 已完成（PR #220）** — 诊断脚本脱敏 `$HOME`/路径并只输出过滤后的日志摘要；`--include-raw-logs` 标志 + shell 测试。
8. **#178 已完成（PR #221）** — 测试改用公共访问器，AST 检查替换为行为测试，重复测试已删除（来自 #168）。
9. **#205/#206 已完成（PR #222）** — 干净固定由 CVE 回归测试冻结，SessionStart 钩子使用 constraints 安装；issue 已关闭。
10. **#203/#204 作为观察项** — 非项目依赖；仅当未来功能直接引入时再固定。
11. **#161 暂缓** — "Runde 5" 已完成；仅剩 clone URL（需所有者就仓库可见性决定）。
12. **#218 作为下一个文档 PR** — 在 CHANGELOG 中补充七条缺失的 `[Unreleased]` 条目。
13. **#226 随后** — 更新 INSTALL 指南；Release 工件提示取决于所有者的打标签决定。

## 先前轮次

- **2026-06-01，"modest-shannon"（A–E）** — 5 项发现，全部完成。
- **v2.2，"admiring-mayer"（#1–#15）** — 外部清单，已完成或在误报处放弃。

第 1–5 轮的完整历史发现与工作日志：[../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
