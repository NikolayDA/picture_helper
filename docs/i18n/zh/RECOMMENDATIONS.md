[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · **简体中文**

# 代码分析与优先级建议：BgRemover

## 评级标准

| 符号 | 优先级 | 含义 |
|------|--------|------|
| 🔴 | 严重 | 缺陷、崩溃或数据丢失 |
| 🟠 | 高 | 对可靠性或可维护性有明显影响 |
| 🟡 | 中 | 对质量、可读性或可测试性有用的改进 |
| 🟢 | 低 | 可选的打磨或流程改进 |

## 当前状态（2026-08-29，v2.9.0 已发布，未结议题已全部审计）

**2026-08-29 补记（未结议题全面审计）：** 全部 40 个未结议题均已对照 `main`
（HEAD `411d47c`）检查，并对结论做了对抗性复核。#878 已由 PR #908 全部完成，
仅待关闭；#681、#882、#905 与 #906 的描述均已补正。最重要的发现是：EufyMake
真实测试 #688–#690 **并非**只在等待硬件——Alpha/覆盖度既无 fixture 也无测试
单元格，缺少一对像素尺寸相同的 COLOR/HEIGHT，gloss 只有一个测试单元格
（I-10），而单元格 I-06 引用的是 fixture 清单而非真实的导出清单。相应的四行
已更正。没有新的 🔴 级发现。

**2026-08-29 补记：** v2.9.0 已发布。硬件验收在 macOS arm64 与 Linux arm64
上以真实 GPU 渲染器通过，标签与发布已按字节比对批准清单，`PUBLIC-DOWNLOAD-01`
与 `UPDATE-01` 均已达成。#881 因此关闭；刻意暂停的 Linux x86_64 标准仍显式
保持 `PENDING`。

**2026-08-28 例行检查：** GitHub 实时核对补上此前缺失的未结议题
**#878**、**#881**、**#882** 以及新建的 MAS 子议题 **#883–#907**。
#878 修复标准/专家界面与用户指南之间的差距，
包括最新截图和 PDF。#881 是 2.9.0 的约束性验收与发布记录；候选构建和预检
均为绿色，但硬件验收和人工批准尚未完成。#882 将 Mac App Store 路径作为受阻
Epic 统一管理；#883–#907 将许可、账户、沙箱、打包、商店和运营阶段具体化。任何技术
工作之前必须先决定许可策略。没有新的 🔴 级发现。

**2026-08-26 例行检查：** 实时状态现为 16 个未结议题（此前为 15 个）。新收录并评估了 **#869**（自动化测试套件审计：`test_workers.py` 中的一处重复用例、若干私有字段/控件访问、六处薄弱断言——无生产环境缺陷，`make coverage` 仍保持 93% 绿色通过）。**#828**（评审自动化）此后已通过 PR #876 关闭；测量序列为 10/10（见下方补记）。没有未决的 🔴 级发现。 **2026-08-26 补记：** 本轮有两处更正。其一，本轮仍将 **#866**（Apple Silicon 上的 Rosetta/x86_64）列为未结，而 [PR #870](https://github.com/NikolayDA/picture_helper/pull/870) 早在 07:56 UTC 就已将其关闭——本轮是针对本地拼装的快照工作的（实时 API 访问在代理沙箱中被阻断，参见 #752 的历史），到 13:05 UTC 合并时该快照已经过时。其二，**#869** 已通过 [PR #873](https://github.com/NikolayDA/picture_helper/pull/873) 全部完成。两行均已移除，实时状态因此曾为 **14** 个；在 #828 通过 PR #876 关闭后为 **13** 个。因 #866 之故，`recommendations-live-check.yml` 自第 #67 次运行（2026-08-25 21:56 UTC）起连续四次为红：先是缺行，后是已关闭却仍在列。**2026-08-26 补记（#828）：** 随着 PR #870 的评审运行，被动的十次运行样本已满——**10/10**，其中 6 绿 4 红。十次运行的拒绝计数均为 0（最初中断的那些运行各有 6–10 次），每次运行都发布了摘要与行内发现；四次红色运行全部仅因 25 回合上限而失败（26–30 回合）。owner 已于同日将上限上调至 40（超时 20 分钟）。

**2026-08-26 发布范围检查：** 自 v2.8.0（2026-08-17）以来，`main` 上已合并 37 个提交。与此前几轮的判断不同，自 2026-08-24 的补记以来，落地的已不只是治理/文档工作：`CHANGELOG.md` 中的 `[Unreleased]` 部分已经包含一项真正的功能（#863，缩放胶囊控件现在也出现在 3D 浮雕预览中）以及四项修复/UX 变更（#839/#846 在切换到标准模式时丢弃高度实时预览；#864/#865 修复 macOS 上应用切换器/Stage Manager 侧边栏中错误的进程图标；#867 将标准/专家模式提示从常驻文字改为工具提示；#868 将“从图像生成高度图”主按钮移到步骤 5 顶部）。下一个版本的冻结文档尚不存在（`docs/history/RELEASE-*-scope-freeze.md` 仍止步于 2.8.0）。由于 3D 缩放胶囊是一项新功能，按 SemVer 应发布**次要版本 v2.9.0**，目前已到期但尚未启动准备工作。#866 与 #869 此后均已关闭，本就不会阻塞该发布。 **补记（本次切分）：** 准备工作已完成——`pyproject.toml` 为 2.9.0，[冻结文档](../../history/RELEASE-2.9.0-scope-freeze.md)已就位（基线 v2.8.0，路径策略 6），CHANGELOG 与 AppStream 均标注 2026-08-26。上文所述的 37 个提交是检查时点的计数；决定性的提交集合由 freeze-gate 从 first-parent 历史动态推导，此处刻意不予固定。

**2026-08-22 例行检查：** `scripts/recommendations_live_check.py --write` 已将六种语言的分诊表与 GitHub 同步：#837 通过 PR #838 关闭并移除；新增 #839 与 #841。v2.8.0 之后，PR #840 更新了文档，PR #842 更新了流程文档、依赖审计工作流的一项小细节和防漂移测试，没有发布产品功能。目前无需新版本，也没有未决的 🔴 级发现。**2026-08-23 补记：** #836 与 #839 已完成；关闭它们的 PR 见下方列表。仅修改文档的 PR #843 提前关闭了 #841；之后三个 PR 运行再次失败，因此该议题已重新打开。只有在完成 allowlist/prompt 修复并取得连续三次绿色 review 运行后，才能视为完成。因此分诊表当时重新收录了 #841：修复 PR #850 已合并，但**并不**关闭该议题——它只是解锁了测量序列。上一版本提前移除了该行；#849 报告的红色 live check 正源于此，本轮予以关闭。后续议题 #847 已加入并完成评估。**2026-08-24 补记：** owner 已于 2026-08-23 在未进行测量序列的情况下关闭 #841，#847 亦经 PR #852 完成——两行均已再次移出分诊表；#841 的判据存放于 [../../history/ISSUE-841-VERIFIKATION.md](../../history/ISSUE-841-VERIFIKATION.md)，其余事项在 #828 中跟进。原先在该文件中记录的“三次运行”规则已于 2026-08-24 随评审循环降级替换为不重置的十次运行被动测量（见判据文件第 1 条）。

**完整审计（例行检查时的快照，早于两条补记；#836/#839 已完成，#841 其后已关闭）：** 每项描述、验收标准、评论和标签都已对照 `main` 检查。#839 记录了切换到标准模式时高度预览与保存/导出模型之间范围很窄但真实存在的不一致。#841 将 #828 的测量结果具体化为工作流缺陷。#836 现在涵盖六种语言的指南和 PDF 重新生成；#694 涵盖标准/专家模式与活动中的 COLOR 预览。

**#828/#841 与 PR #842：** #828 的 3/3 样本已完成，原始假设已被推翻。PR #842 的最终评审运行（[32572985972](https://github.com/NikolayDA/picture_helper/actions/runs/32572985972)）增加了另一条基线：`error_max_turns`、31 回合、9 次拒绝。它把 #841 的修复进一步明确为：将 `git show-ref` 作为有用的只读工具，并在提示中明确禁止 `git fetch`、本地测试和通用 `gh api` 绕行；该运行不计入修复后的三次验证。修复本身此后已通过 PR #850 合并；#828 曾保留上层事项，现已通过 PR #876 关闭。

**EufyMake #681/#687–#691：** 现有 31 个 fixture、协议模板和已批准的测试治理均已正确反映在议题中。#687 已完成 16/18 项标准；仅剩 I-06（文件夹/清单）以及真实测试后的收尾评审。对于独立的 Spot UV 路径，有厂商资料支持的假设为：黑色 = gloss，白色 = 无 gloss。完整 16 位利用、`pHYs` 优先级、灰度到毫米映射以及 gloss 强度仍是 #688–#690 的硬件问题。

保持不变并已关闭：**N1/N2/N4/N5/N6/N7/N8**、**O1–O8**、自 **2026-06-25** 起完成的全部事项、v2.7.0 至 v2.8.0 各版本，以及史诗 #741（含其十一个子议题）、史诗 #805（含 #806–#811）、#817 与 #821；自上次同步以来新关闭：#836（PR #844）、#837（PR #838）、#839（PR #846）、#849（PR #851）、#841（由 owner 关闭）、#847（PR #852）、#866（PR #870/#871）与 #869（PR #873）（详见以往轮次）。

未结事项：下方分诊表中每个议题一行。自 #821 起，数量与表行都不再人工维护——`scripts/recommendations_live_check.py --write` 依据 GitHub 实时状态更新全部六个版本，评估列仍是编辑工作。

## GitHub 未结议题 — 分诊状态

| # | 标题 | 相关性 | 复杂度 | 建议模型（投入） | 下一步 |
|---|------|--------|--------|--------------------|--------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Epic] EufyMake 目标配置文件 —— 验证 Height/Gloss/mm-DPI | 🟠 高（关系到最重要导出目标的正确性） | 🔴 高（5 个子议题，需要物理硬件） | –（Epic） | #687 的准备工作已完成 16/18 项；仍有 I-06 和收尾评审，#691 则等待 #688–#690 的真实测试 |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | 假设清单、厂商资料来源、测试矩阵 | 🟠 高（#688–#691 的约束性基础） | 🔴 高（准备工作已完成；剩余部分需要真实硬件） | –（无需 Agent；需要真实的 EufyMake 硬件） | 阻塞（外部）—— 已完成 16/18 项；待完成文件夹/清单 I-06，以及 #688–#690 真实测试后的收尾评审 |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | 在真实硬件上验证 HEIGHT 位深/语义 | 🟠 高（直接影响浮雕高度） | 🔴 高（需物理打印机、测试样件、测量记录） | –（无需 Agent；需要真实 EufyMake 硬件） | 阻塞（外部）+ 前期工作未完成 —— #687 提供的 fixture/协议模板已就绪，但 Alpha/覆盖度既无 fixture 也无测试单元格（所有 COLOR fixture 均为不透明），并且缺少一对像素尺寸相同的 COLOR/HEIGHT（I-02/I-08 存在混杂）；须在测试日之前补齐 |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | 验证 mm/DPI、目标尺寸、定位契约 | 🟠 高（打印尺寸/对位） | 🔴 高（物理测量、对照图案） | –（无需 Agent；需要真实硬件） | 阻塞（外部）+ 前期工作未完成 —— Studio 导入对话框是否依据 `pHYs`/DPI 推导起始尺寸尚未证实（N10, EM-F04）；此外单元格 I-06 引用的是 fixture 清单而非真实的导出清单，非正方形 DPI 也既未测试、也没有给出排除理由 |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | 验证 gloss/亮光漆语义 | 🟡 中（代码中 gloss 已标记为“experimental”） | 🔴 高（需物理打印、消耗材料） | –（无需 Agent；需要真实硬件） | 阻塞（外部）+ 前期工作未完成 —— #687 的前期工作只完成了一部分：gloss 测试单元格仅有一个（I-10），没有 Alpha/覆盖度 fixture，没有尺寸不一致的 gloss 用例，gloss × HEIGHT 也未交叉覆盖 |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | 将带版本号的目标配置文件整合进 validator/writer/对话框/文档 | 🟠 高（强化生产环境导出路径） | 🟠 高（横跨 eufymake_export/_validate/_writer + UI） | Opus，高 | 阻塞 —— 等待 #688–#690 |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Epic] COLOR 色调/灰度引擎 | 🟡 中高（激光路线图的基础，非当前活跃缺陷） | 🔴 高（5 个子议题，ADR→核心→UI→集成→验收） | –（Epic） | 进行中 —— 优先启动 #692 |
| [#692](https://github.com/NikolayDA/picture_helper/issues/692) | 色调/直方图/灰度操作的 ADR + 数据契约 | 🟠 高（为整个 Epic 确立契约） | 🟡 中（架构决策，无需实现） | Opus，高 | 可立即启动 |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | 无 Qt 依赖核心：直方图/灰度/色阶/伽马 | 🟡 中高 | 🟡 中（扩展 `color_ops.py`，隔离良好、易于测试） | Sonnet，高 | 阻塞 —— 等待 ADR #692 |
| [#694](https://github.com/NikolayDA/picture_helper/issues/694) | 直方图/色阶/伽马的实时预览 + 操作界面 | 🟡 中 | 🟡 中高（Qt UI，需类似高度预览的防抖/世代保护） | Sonnet，高 | 阻塞 —— 等待核心 #693 |
| [#695](https://github.com/NikolayDA/picture_helper/issues/695) | 图层/选区/历史/项目集成 | 🟡 中 | 🟠 高（大量状态转换：撤销/重做、选区、脏状态） | Opus，高 | 阻塞 —— 等待 #693/#694 |
| [#696](https://github.com/NikolayDA/picture_helper/issues/696) | 性能/E2E/文档/激光接口验收 | 🟡 中（收尾关卡，非新功能） | 🟠 高（基准测试套件、E2E、文档、适配器契约） | Opus，高 | 阻塞 —— #695 完成后的收尾议题 |
| [#878](https://github.com/NikolayDA/picture_helper/issues/878) | 在用户指南中补充标准/专家模式与 3D 缩放胶囊 | 🟡 中（标准模式用户否则看不到已记录的控件） | 🟡 中（六种语言、新截图、PDF 和漂移测试） | Sonnet，高 | 已完成（PR #908）—— 用户指南、六种语言版本、PDF 和截图集均已完备；仅待 owner 关闭，之后移除本行 |
| [#882](https://github.com/NikolayDA/picture_helper/issues/882) | [Epic] BgRemover 上架 Mac App Store | 🟡 中高（新分发渠道，非当前产品缺陷） | 🔴 高（许可、沙箱、打包、商店和发布治理） | –（Epic） | 阻塞 —— 先将许可策略创建为具体的阶段 0 子任务并作出决定 |
| [#883](https://github.com/NikolayDA/picture_helper/issues/883) | [MAS] 许可策略：PySide6、Riverbank 与代码重新许可 | 🟠 高（所有 MAS 技术工作的硬性阻塞项） | 🔴 高（许可/负责人决策、可能的 Qt 移植、残余风险） | Opus，高 + 负责人/法律审核 | 可启动 —— 编写 ADR 并记录负责人决定；若选 PySide6，另建移植议题 |
| [#884](https://github.com/NikolayDA/picture_helper/issues/884) | [MAS] 加入 Apple Developer Program | 🟠 高（阻塞证书和商店访问） | 🟢 低（手动账户/付款步骤） | –（无需 Agent；Account Holder） | 阻塞（外部）—— 选择账户类型，完成注册/2FA，并明确续费责任 |
| [#885](https://github.com/NikolayDA/picture_helper/issues/885) | [MAS] 签名身份、App ID 与 Provisioning Profile | 🟠 高（签名商店构建的前提） | 🟡 中（负责人密钥与 bundle-ID/打包契约） | –（无需 Agent；Account Holder/Admin） | 阻塞 —— 等待 #884；创建证书、显式 App ID/配置文件并冻结 bundle ID |
| [#886](https://github.com/NikolayDA/picture_helper/issues/886) | [MAS] 定义并应用 App Sandbox 权限 | 🟠 高（商店和运行时强制要求） | 🟠 高（全部 Mach-O、打包与硬件证据） | Opus，高 | 阻塞 —— 等待 #883；实现最小权限并加入产物/硬件测试 |
| [#887](https://github.com/NikolayDA/picture_helper/issues/887) | [MAS] 兼容沙箱的推理子进程 | 🟠 高（核心 AI 必须在商店构建中运行） | 🔴 高（spawn/helper 签名、双键规则、真实沙箱） | Opus，高 | 阻塞 —— 等待 #886；决定 re-exec/helper，并在硬件上证明 AI 自检 |
| [#888](https://github.com/NikolayDA/picture_helper/issues/888) | [MAS] 文件和目录的 Security-scoped Bookmarks | 🟠 高（最近文件/快速保存否则在重启后失效） | 🟠 高（持久授权、图像/项目/目录、渠道 gating） | Opus，高 | 阻塞 —— 等待 #886；实现 bookmark 契约并测试沙箱重启场景 |
| [#889](https://github.com/NikolayDA/picture_helper/issues/889) | [MAS] 沙箱安全写入与 EufyMake 导出 | 🟠 高（保存/导出路径及数据完整性） | 🔴 高（多路径原子性和 Powerbox 授权） | Opus，高 | 阻塞 —— 等待 #886；设计授权内的原子写入/扩展名/目标选择并在硬件验证 |
| [#890](https://github.com/NikolayDA/picture_helper/issues/890) | [MAS] 沙箱容器中的 AI 模型缓存 | 🟡 中（商店渠道中的确定性模型路径） | 🟡 中（隔离路径契约与迁移决策） | Sonnet，高 | 阻塞 —— 等待 #886，并与 #893 联动；显式设置 `U2NET_HOME` 并决定迁移策略 |
| [#891](https://github.com/NikolayDA/picture_helper/issues/891) | [MAS] 分发渠道标志与更新检查 gating | 🟠 高（App Store 2.4.5，禁止自行更新） | 🟠 中高（菜单、设置、worker、hook 的中心标志） | Sonnet，高 | 阻塞 —— 等待 #883；建立渠道契约并对 MAS 网络/UI 路径做负向测试 |
| [#892](https://github.com/NikolayDA/picture_helper/issues/892) | [MAS] 移除 AiInstallDialog 并内置 AI 后端 | 🟠 高（商店中不得安装可执行代码） | 🟡 中（渠道 gating 与强制打包测试） | Sonnet，高 | 阻塞 —— 等待 #891；隐藏对话框/菜单并证明已内置 rembg/onnxruntime |
| [#893](https://github.com/NikolayDA/picture_helper/issues/893) | [MAS] 内置 u2net 或在首次启动时下载 | 🟠 高（审核风险与 AI 功能） | 🟠 高（产品/审核决策、打包或新 i18n 流程） | Opus，高 | 阻塞 —— 等待 #890/#891 和 #883；记录、实现并在沙箱验证所选方案 |
| [#894](https://github.com/NikolayDA/picture_helper/issues/894) | [MAS] 选择 Briefcase 或 py2app 打包 | 🟠 高（决定技术可行性） | 🟠 高（开放式沙箱/签名/上传 spike） | Opus，高 | 阻塞 —— 等待 #883；测试 Briefcase 与 py2app 后备并记录 ADR |
| [#895](https://github.com/NikolayDA/picture_helper/issues/895) | [MAS] onedir App、inside-out 签名与 Qt 清理 | 🟠 高（核心可执行商店构建） | 🔴 高（全部二进制、Qt、配置、上传验证） | Opus，高 | 阻塞 —— 等待 #885/#886/#894；实现并确保无 ITMS 错误 |
| [#896](https://github.com/NikolayDA/picture_helper/issues/896) | [MAS] 完整 Info.plist 与图标集 | 🟡 中高（商店元数据与平台契约） | 🟡 中（字段、架构、确定性资源） | Sonnet，高 | 阻塞 —— 等待 #895；决定系统/架构/文档类型并加入测试 |
| [#897](https://github.com/NikolayDA/picture_helper/issues/897) | [MAS] 签名 productbuild PKG 与 Transporter 上传 | 🟠 高（可提交产物） | 🟠 高（二次签名、自动化、首次手动上传） | Opus，高 + Account Holder | 阻塞 —— 等待 #885/#895/#896；构建可复现 PKG 并记录 delivery |
| [#898](https://github.com/NikolayDA/picture_helper/issues/898) | [MAS] CI、六产物契约与 PKG 扫描 | 🟠 高（fail-closed 发布完整性） | 🔴 高（密钥、契约、解包、恶意软件/路径扫描） | Opus，高 | 阻塞 —— 等待 #895/#897；扩展 leg、契约、payload 扫描与测试 |
| [#899](https://github.com/NikolayDA/picture_helper/issues/899) | [MAS] 真实硬件沙箱验收 smoke | 🟠 高（核心路径的约束性运行证据） | 🔴 高（PKG、AI spawn、Powerbox、3D、证据 schema） | Opus，高 + macOS 硬件 | 阻塞（外部）—— 等待 #898；在 self-hosted ARM64 实现并执行 |
| [#900](https://github.com/NikolayDA/picture_helper/issues/900) | [MAS] macOS TestFlight Beta | 🟠 高（早期审核与外部设备证据） | 🟡 中（手动 ASC/测试者协调） | –（无需 Agent；Holder/测试者） | 阻塞 —— 等待 #897/#901；在另一设备验证 AI、文件和 3D |
| [#901](https://github.com/NikolayDA/picture_helper/issues/901) | [MAS] ASC 记录与六语言元数据 | 🟠 高（名称、商店页面、提交前提） | 🟠 中高（负责人步骤与六套本地化文本） | Sonnet，高 + Holder | 阻塞 —— 等待 #884/#885；保留名称、版本化/填写文本、评级/店面 |
| [#902](https://github.com/NikolayDA/picture_helper/issues/902) | [MAS] 16:10 商店截图 | 🟡 中高（必需上架材料） | 🟡 中（格式、Alpha、语言决策） | Sonnet，高 | 阻塞 —— 等待构建 #895；扩展自动化并验证截图集 |
| [#903](https://github.com/NikolayDA/picture_helper/issues/903) | [MAS] 隐私政策与 App Privacy | 🟠 高（商店和 App 强制要求） | 🟡 中（政策、托管、i18n 链接、问卷） | Sonnet，高 + 负责人 | 阻塞 —— 等待 #891/#893；发布/链接并证明“Data Not Collected” |
| [#904](https://github.com/NikolayDA/picture_helper/issues/904) | [MAS] 欧盟 DSA 状态、法律声明与 GPSR | 🟠 高（欧盟店面与公开法律义务） | 🟠 中高（分类、验证、法律风险） | –（无需 Agent；负责人/法律审核） | 阻塞 —— 等待 #884；申报 trader 并记录 DDG/GPSR 负责人/复查 |
| [#905](https://github.com/NikolayDA/picture_helper/issues/905) | [MAS] 扩展发布治理 | 🟠 高（防止渠道绕过 fail-closed 契约） | 🟠 高（runbook、checklist、契约、policy、六份 changelog） | Opus，高 | 阻塞 —— 与 #898/#899 同步；提交前将契约/测试提升到六产物 |
| [#906](https://github.com/NikolayDA/picture_helper/issues/906) | [MAS] 首次提交与审核 | 🟠 高（人工发布关卡） | 🔴 高（多项依赖、残余风险、Apple 沟通） | –（无需 Agent；Release Owner） | 阻塞 —— #896/#897/#899/#901–#905 后预检、提交并记录结果/后续议题 |
| [#907](https://github.com/NikolayDA/picture_helper/issues/907) | [MAS] 续费、更新与渠道运营方案 | 🟡 中高（长期可用性与渠道分离） | 🟡 中（runbook、责任人、提醒、矩阵） | Opus，高 + 负责人 | 阻塞 —— 可提前起草，#906 后定稿；固化续费/更新/网站维护流程 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | 为手动 Codex 安全检查恢复 OpenAI 配额 | 🟢 低（仅阻塞一次可选的手动扫描） | 🟢 低（纯运维性质，无代码） | –（无需 Agent；由仓库所有者处理账单） | 阻塞（外部）—— 最近一次运行（29233060507，2026-07-13）并未证明扫描成功；账单/配额仍未解决 |

### 接下来推荐

1. **#692**（ADR）开启 COLOR 史诗 #682。
2. 一旦有 Studio/打印机硬件：将 #687（剩余，尤其 I-06）、#688、#689、#690 已准备好的真实测试
   在一次打包会话中执行——fixture、协议模板和已批准的中止标准均已齐备。
3. **#883**（MAS 许可策略）决定 Mac App Store 路径 #882——没有该 owner 决策，
   #884–#907 整条链条将持续受阻。

## 以往轮次

自 v2.2 以来的详细记录：[RECOMMENDATIONS-2026-v2.2-v2.9.zh.md](../../history/RECOMMENDATIONS-2026-v2.2-v2.9.zh.md)。

历史发现和工作记录（第 1–5 轮）：[RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
