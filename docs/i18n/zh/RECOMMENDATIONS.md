[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · **简体中文**

# 代码分析与优先级建议：BgRemover

## 评级标准

| 符号 | 优先级 | 含义 |
|------|--------|------|
| 🔴 | 严重 | 缺陷、崩溃或数据丢失 |
| 🟠 | 高 | 对可靠性或可维护性有明显影响 |
| 🟡 | 中 | 对质量、可读性或可测试性有用的改进 |
| 🟢 | 低 | 可选的打磨或流程改进 |

## 当前状态（2026-09-09，v2.9.0 已发布，未结议题已全部审计）

**2026-09-09 每日审计（状态 `dd6c572`）：** 已复核全部 56 个未结议题；十五个新议题（#1031–#1045）已进入分诊表。实质性的新内容是含十一个工作包的流程史诗 #1032：在窗口 `85eeea4^..dd6c572` 中有 156 个主线提交，其中 28 个（18 %）纯粹只做分诊维护——也就是本条目此刻正在更新的这张表（#1032 记为 27；差异是一个同时改动归档的提交）。#1040 计划连同实时核对工作流一并废除它；在此之前它仍是有效契约，而该核对正因如此自 2026-09-08 起一直报红（运行 34282863300），期间代码毫无变化。唯一影响证据基础的新发现是 #1031（优先级 0）：过时的非可编辑 `bgremover` 会让按文件路径启动的子进程测试测量外来代码——危险方向是测试因此变**绿**。#1044（#1004/#1005 的测试缺口，覆盖率 93 %）与 #1045（CHANGELOG 中缺少 `#1023` 引用）是两个可以立刻着手的小 PR。没有新的产品缺陷，也没有 🔴 级发现。

**发布评估：建议发布 v2.10.0。** 自 `v2.9.0`（2026-08-29）以来共有 83 个第一父提交，其中十二个改动产品代码。因此 `[Unreleased]` 已具备完整的次版本范围：EufyMake 目标配置 v2 及 Studio 4.3.3 预检（#681/#691）、已确认的平板尺寸 335 × 420 mm（#971）、以 PNG `pHYs` 写入的项目 DPI（#996）、Qt 升级至 6.11（#994，约十项安全公告，其中包括 CVE-2025-10728 与 CVE-2025-10729），以及四项 3D 修复（#1002、#1004、#1023、#1024），其中 #1024 修复了一次段错误。有两点理由不宜再等：Qt 升级的安全收益只有随产物才能到达用户手中；而提高后的 glibc 下限（aarch64 2.39、x86_64 2.34）是一次平台变更，理应发布并公告。COLOR 色调引擎（#693 及后续）**不是**等待的理由——那是下一个版本的范围。构建候选之前（#1045 第 1 点，即 CHANGELOG 中的 `#1023` 引用，已完成）：通过 `scripts/prepare_release.py 2.10.0` 走 runbook 第 1/2 步，包括其中的编辑性 `TODO(release)` 空缺（`NOTES-01`）。同一次运行也会补上 #914 与 #918 仍缺的端到端证据。

**EufyMake #681/#687–#691：** 可复现集合包含 42 个独立 fixture 和七个未变的
真实导出包（Schema 5）。29 个必需的无打印导入测试格在历史 Studio 4.2.2 基线和
完整 4.3.3 回归中均已完成；I-09 (`.empf`) 仍不阻塞。13/13 个准备好的原生项目
均可加载，十二个活动项目可进入预览。这证明 GUI 与项目准备完成，但不证明 HEIGHT、
尺寸、光泽或套准的实体效果。#688–#690 的 E1 测量及 #687 收尾评审仍未完成。

保持不变并已关闭：**N1/N2/N4/N5/N6/N7/N8**、**O1–O8**、自 **2026-06-25** 起完成的全部事项、v2.7.0 至 v2.9.0 各版本，以及史诗 #741（含其十一个子议题）、史诗 #805（含 #806–#811）、#817 与 #821；自上次同步以来新关闭：#943（PR #944）、#692（PR #947），以及 ANLEITUNG 评审 #963 及其 #964–#966、#968、#969（PR #972）与 #967（PR #973），以及测试套件审计 #949（PR #977）与 PDF 守卫 #974（PR #979），以及 Heartbeat 分级升级 #958（PR #981），以及文档同步 #982（PR #984），以及标注载体补录 #975（PR #986），以及分诊表补录 #995（PR #997），以及死代码清理 #992/#993（PR #998），以及 Qt 升级 #994（详见以往轮次）。

未结事项：下方分诊表中每个议题一行。自 #821 起，数量与表行都不再人工维护——`scripts/recommendations_live_check.py --write` 依据 GitHub 实时状态更新全部六个版本，评估列仍是编辑工作。

## GitHub 未结议题 — 分诊状态

| # | 标题 | 相关性 | 复杂度 | 建议模型（投入） | 下一步 |
|---|------|--------|--------|--------------------|--------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Epic] EufyMake 目标配置文件 —— 验证 Height/Gloss/mm-DPI | 🟠 高（关系到最重要导出目标的正确性） | 🔴 高（5 个子议题，需要物理硬件） | –（Epic） | 集成及全部 29 个必需无打印测试格已完成；I-09 不阻塞。仍需 #688–#690 与收尾评审 |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | 假设清单、厂商资料来源、测试矩阵 | 🟠 高（#688–#691 的约束性基础） | 🔴 高（仓库材料已齐；剩余部分需要真实硬件） | –（无需 Agent；需要真实的 EufyMake 硬件） | 阻塞（外部）—— 已完成 17/18 项及全部 29 个必需导入测试格。仅余 #688–#690 后的收尾评审 |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | 在真实硬件上验证 HEIGHT 位深/语义 | 🟠 高（直接影响浮雕高度） | 🔴 高（需物理打印机、测试样件、测量记录） | –（无需 Agent；需要真实 EufyMake 硬件） | 受阻（外部）—— 包括直接生成的 I-14 滤波/归一化对在内，全部预检已完成；仍需物理精度、滤波、浮雕和毫米测量 |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | 验证 mm/DPI、目标尺寸、定位契约 | 🟠 高（打印尺寸/对位） | 🔴 高（物理测量、对照图案） | –（无需 Agent；需要真实硬件） | 受阻（外部）—— 包含裁剪和 HEIGHT 宽高比处理的 Studio 契约已证实；仅余物理对位、测量和公差 |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | 验证 gloss/亮光漆语义 | 🟡 中（代码中 gloss 已标记为“experimental”） | 🔴 高（需物理打印、消耗材料） | –（无需 Agent；需要真实硬件） | 阻塞（外部）—— 原生 `Gloss Varnish` 已预检；仍需逐单元对位及物理极性、强度和材料效果 |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | 将带版本号的目标配置文件整合进 validator/writer/对话框/文档 | 🟠 高（强化生产环境导出路径） | 🟢 发布关键余项较低；🔴 收尾需硬件 | Sonnet，中 + 后续硬件 | 实现已具备发布条件：v2 是 Studio 4.3.3/固件 4.0.9 的默认配置，v1 保持冻结且可选。#688–#690 后仅复核证据状态；新语义需创建后续配置版本 |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Epic] COLOR 色调/灰度引擎 | 🟡 中高（激光路线图基础，非当前缺陷） | 🔴 高（剩余 4 个子议题：核心→UI→集成→验收） | – （史诗） | 进行中：ADR #692 已批准；接下来是核心 #693 |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | 无 Qt 依赖核心：直方图/灰度/色阶/伽马 | 🟡 中高 | 🟡 中（扩展 `color_ops.py`，隔离良好且易测） | Sonnet，高 | 可以开始：ADR #692（PR #947）给出数据契约；据其公式实现并测试核心 |
| [#694](https://github.com/NikolayDA/picture_helper/issues/694) | 直方图/色阶/伽马的实时预览 + 操作界面 | 🟡 中 | 🟡 中高（Qt UI，需类似高度预览的防抖/世代保护） | Sonnet，高 | 阻塞 —— 等待核心 #693 |
| [#695](https://github.com/NikolayDA/picture_helper/issues/695) | 图层/选区/历史/项目集成 | 🟡 中 | 🟠 高（大量状态转换：撤销/重做、选区、脏状态） | Opus，高 | 阻塞 —— 等待 #693/#694 |
| [#696](https://github.com/NikolayDA/picture_helper/issues/696) | 性能/E2E/文档/激光接口验收 | 🟡 中（收尾关卡，非新功能） | 🟠 高（基准测试套件、E2E、文档、适配器契约） | Opus，高 | 阻塞 —— #695 完成后的收尾议题 |
| [#882](https://github.com/NikolayDA/picture_helper/issues/882) | [Epic] BgRemover 上架 Mac App Store | 🟡 中高（新分发渠道，非当前产品缺陷） | 🔴 高（许可、沙箱、打包、商店和发布治理） | –（Epic） | 阻塞 —— 先决定 #883，并分别处理 Qt/代码许可与模型产物未决的来源/权利 |
| [#883](https://github.com/NikolayDA/picture_helper/issues/883) | [MAS] 许可策略：PySide6、Riverbank 与代码重新许可 | 🟠 高（所有 MAS 技术工作的硬性阻塞项） | 🔴 高（许可/负责人决策、可能的 Qt 移植、残余风险） | Opus，高 + 负责人/法律审核 | 可启动 —— ADR/负责人决策，并证明确切 `u2net.onnx` 的来源、许可和再分发权，或选择替代模型 |
| [#884](https://github.com/NikolayDA/picture_helper/issues/884) | [MAS] 加入 Apple Developer Program | 🟠 高（阻塞证书和商店访问） | 🟢 低（手动账户/付款步骤） | –（无需 Agent；Account Holder） | 阻塞 —— 明确账户、注册/2FA 和续费；免费应用无需 Paid Apps Agreement，但 trader 仍可能需要付款账户资料（#904） |
| [#885](https://github.com/NikolayDA/picture_helper/issues/885) | [MAS] 签名身份、App ID 与 Provisioning Profile | 🟠 高（签名商店构建的前提） | 🟡 中（负责人密钥与 bundle-ID/打包契约） | –（无需 Agent；Account Holder/Admin） | 阻塞 —— 等待 #884；创建证书、显式 App ID/配置文件并冻结 bundle ID |
| [#886](https://github.com/NikolayDA/picture_helper/issues/886) | [MAS] 定义并应用 App Sandbox 权限 | 🟠 高（商店和运行时强制要求） | 🟠 高（全部 Mach-O、打包与硬件证据） | Opus，高 | 阻塞 —— 等待 #883；实现最小权限并加入产物/硬件测试 |
| [#887](https://github.com/NikolayDA/picture_helper/issues/887) | [MAS] 兼容沙箱的推理子进程 | 🟠 高（核心 AI 必须在商店构建中运行） | 🔴 高（spawn/helper 签名、双键规则、真实沙箱） | Opus，高 | 阻塞 —— 等待 #886；决定 re-exec/helper，并在硬件上证明 AI 自检 |
| [#888](https://github.com/NikolayDA/picture_helper/issues/888) | [MAS] 文件和目录的 Security-scoped Bookmarks | 🟠 高（最近文件/快速保存否则在重启后失效） | 🟠 高（持久授权、图像/项目/目录、渠道 gating） | Opus，高 | 阻塞 —— 等待 #886；实现 bookmark 契约并测试沙箱重启场景 |
| [#889](https://github.com/NikolayDA/picture_helper/issues/889) | [MAS] 沙箱安全写入与 EufyMake 导出 | 🟠 高（保存/导出路径及数据完整性） | 🔴 高（多路径原子性和 Powerbox 授权） | Opus，高 | 阻塞 —— 等待 #886；设计授权内的原子写入/扩展名/目标选择并在硬件验证 |
| [#890](https://github.com/NikolayDA/picture_helper/issues/890) | [MAS] 沙箱容器中的 AI 模型缓存 | 🟡 中（商店渠道中的确定性模型路径） | 🟡 中（隔离路径契约与迁移决策） | Sonnet，高 | 阻塞 —— 等待 #886，并与 #893 联动；显式设置 `U2NET_HOME` 并决定迁移策略 |
| [#891](https://github.com/NikolayDA/picture_helper/issues/891) | [MAS] 分发渠道标志与更新检查 gating | 🟠 高（App Store 2.4.5，禁止自行更新） | 🟠 中高（菜单、设置、worker、hook 的中心标志） | Sonnet，高 | 阻塞 —— 等待 #883；建立渠道契约并对 MAS 网络/UI 路径做负向测试 |
| [#892](https://github.com/NikolayDA/picture_helper/issues/892) | [MAS] 移除 AiInstallDialog 并内置 AI 后端 | 🟠 高（商店中不得安装可执行代码） | 🟡 中（渠道 gating 与强制打包测试） | Sonnet，高 | 阻塞 —— 等待 #891；隐藏对话框/菜单并证明已内置 rembg/onnxruntime |
| [#893](https://github.com/NikolayDA/picture_helper/issues/893) | [MAS] 内置 u2net 或在首次启动时下载 | 🟠 高（审核风险与 AI 功能） | 🟠 高（产品/审核决策、打包或新 i18n 流程） | Opus，高 | 阻塞 —— 选择方案前由 #883 证明模型来源/许可/再分发权或更换模型；之后再做 #890/#891 与沙箱验证 |
| [#894](https://github.com/NikolayDA/picture_helper/issues/894) | [MAS] 选择 Briefcase 或 py2app 打包 | 🟠 高（决定技术可行性） | 🟠 高（开放式沙箱/签名/上传 spike） | Opus，高 | 阻塞 —— 等待 #883；测试 Briefcase 与 py2app 后备并记录 ADR |
| [#895](https://github.com/NikolayDA/picture_helper/issues/895) | [MAS] onedir App、inside-out 签名与 Qt 清理 | 🟠 高（核心可执行商店构建） | 🔴 高（全部二进制、Qt、配置、上传验证） | Opus，高 | 阻塞 —— #885/#886/#894 后实现，选择 fail-closed `AppTransaction` 或 receipt，并确保无 ITMS 错误 |
| [#896](https://github.com/NikolayDA/picture_helper/issues/896) | [MAS] 完整 Info.plist 与图标集 | 🟡 中高（商店元数据与平台契约） | 🟡 中（字段、架构、确定性资源） | Sonnet，高 | 阻塞 —— 等待 #895；决定系统/架构/文档类型并加入测试 |
| [#897](https://github.com/NikolayDA/picture_helper/issues/897) | [MAS] 签名 productbuild PKG 与 Transporter 上传 | 🟠 高（可提交产物） | 🟠 高（二次签名、自动化、首次手动上传） | Opus，高 + Account Holder | 阻塞 —— 等待 #885/#895/#896；构建可复现 PKG 并记录 delivery |
| [#898](https://github.com/NikolayDA/picture_helper/issues/898) | [MAS] CI、六产物契约与 PKG 扫描 | 🟠 高（fail-closed 发布完整性） | 🔴 高（密钥、契约、解包、恶意软件/路径扫描） | Opus，高 | 阻塞 —— 等待 #895/#897；扩展 leg、契约、payload 扫描与测试 |
| [#899](https://github.com/NikolayDA/picture_helper/issues/899) | [MAS] 真实硬件沙箱验收 smoke | 🟠 高（核心路径的约束性运行证据） | 🔴 高（PKG、AI spawn、Powerbox、3D、证据 schema） | Opus，高 + macOS 硬件 | 阻塞 —— #898 后在 ARM64 执行，并纳入有效及在可复现时无效的应用下载证据 |
| [#900](https://github.com/NikolayDA/picture_helper/issues/900) | [MAS] macOS TestFlight Beta | 🟠 高（早期审核与外部设备证据） | 🟡 中（手动 ASC/测试者协调） | –（无需 Agent；Holder/测试者） | 阻塞 —— 等待 #897/#901；在另一设备验证 AI、文件和 3D |
| [#901](https://github.com/NikolayDA/picture_helper/issues/901) | [MAS] ASC 记录与六语言元数据 | 🟠 高（名称、商店页面、提交前提） | 🟠 中高（负责人步骤与六套本地化文本） | Sonnet，高 + Holder | 阻塞 —— 等待 #884/#885；保留名称、版本化/填写文本、评级/店面 |
| [#902](https://github.com/NikolayDA/picture_helper/issues/902) | [MAS] 16:10 商店截图 | 🟡 中高（必需上架材料） | 🟡 中（格式、Alpha、语言决策） | Sonnet，高 | 阻塞 —— 等待构建 #895；扩展自动化并验证截图集 |
| [#903](https://github.com/NikolayDA/picture_helper/issues/903) | [MAS] 隐私政策与 App Privacy | 🟠 高（商店和 App 强制要求） | 🟡 中（政策、托管、i18n 链接、问卷） | Sonnet，高 + 负责人 | 阻塞 —— 等待 #891/#893；发布/链接并证明“Data Not Collected” |
| [#904](https://github.com/NikolayDA/picture_helper/issues/904) | [MAS] 欧盟 DSA 状态、法律声明与 GPSR | 🟠 高（欧盟店面与公开法律义务） | 🟠 中高（分类、验证、法律风险） | –（无需 Agent；负责人/法律审核） | 阻塞 —— #884 后记录 trader、公开联系方式、必要的付款账户资料及 DDG/GPSR 责任/复查 |
| [#905](https://github.com/NikolayDA/picture_helper/issues/905) | [MAS] 扩展发布治理 | 🟠 高（防止渠道绕过 fail-closed 契约） | 🟠 高（runbook、checklist、契约、policy、六份 changelog） | Opus，高 | 阻塞 —— 与 #898/#899 同步；提交前将契约/测试提升到六产物 |
| [#906](https://github.com/NikolayDA/picture_helper/issues/906) | [MAS] 首次提交与审核 | 🟠 高（人工发布关卡） | 🔴 高（多项依赖、残余风险、Apple 沟通） | –（无需 Agent；Release Owner） | 阻塞 —— #896/#897/#899/#901–#905 后预检（含下载验证）、提交并记录结果/后续议题 |
| [#907](https://github.com/NikolayDA/picture_helper/issues/907) | [MAS] 续费、更新与渠道运营方案 | 🟡 中高（长期可用性与渠道分离） | 🟡 中（runbook、责任人、提醒、矩阵） | Opus，高 + 负责人 | 阻塞 —— 可提前起草，#906 后定稿；固化续费/更新/网站维护流程 |
| [#914](https://github.com/NikolayDA/picture_helper/issues/914) | [Epic] 发布流程：runner、自动化证据、解除 main 冻结 | 🟠 高（发布运维；实现基本完成） | 🟢 低（一项按事件产生的证据） | – （史诗） | 接近完成：2026-09-03 首次定时 dry-run 已成功运行（run 33737226157）；仅剩下一次真实发布中包含 #918 的端到端证据 |
| [#918](https://github.com/NikolayDA/picture_helper/issues/918) | 用发布 ref 取代 main 冻结（ADR + fail-closed 保障） | 🟠 高（发布期间 `main` 保持可合并） | 🟢 低（代码、文档与 ruleset 均已就位） | – （无代理；下一次发布运行） | 受阻（外部）：2026-08-31 收尾检查后重新开启；PR #936 与生效的 ruleset 21941216 均有记录，仅差一次发布后验收可证明从 `release/vX.Y.Z` 启动的运行 |
| [#939](https://github.com/NikolayDA/picture_helper/issues/939) | 运维：自托管 runner（heartbeat 告警通道） | 🟡 中（运维通道，非产品代码） | 🟢 低（仅观察） | – （无代理；仓库 owner） | 长期开启：请勿关闭（`RUNNER_HEARTBEAT_ISSUE`）；2026-08-31 的 FAIL 是计划中的告警通道测试，清理步骤已完成（计划运行 33496675995 通过，x86_64 跳过，Mac 与 Pi 均合格） |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | 为手动 Codex 安全检查恢复 OpenAI 配额 | 🟢 低（仅阻塞一次可选的手动扫描） | 🟢 低（纯运维性质，无代码） | –（无需 Agent；由仓库所有者处理账单） | 阻塞（外部）—— 最近一次运行（29233060507，2026-07-13）并未证明扫描成功；账单/配额仍未解决 |
| [#1053](https://github.com/NikolayDA/picture_helper/issues/1053) | `make doctor` 与 SessionStart 钩子的 editable 契约（#1031）相矛盾：每个 Web 会话都 FAIL | 🟡 中（诊断命令在 Web 会话中指向错误方向；`make install-test` 会破坏钩子状态） | 🟡 中（`check_test_env.py` 中的模式开关、复用 `check_install_provenance.py` 的链接规则、新测试、三处文档） | Sonnet，中 | Ready for PR：独立；模式开关的形式由所有者决定 |
| [#1043](https://github.com/NikolayDA/picture_helper/issues/1043) | 将 `docs/PROZESSE_UML.md` 精简为主干流程 | 🟡 中（773 行、30 个菱形；重复了 runbook 的重启矩阵） | 🟡 中（四张图，外加指向 runbook 与 ADR 的引用） | Sonnet，高 | 阻塞：最后一个工作包；等待 #1040、#1035、#1036、#1037 和 #1041 |
| [#1042](https://github.com/NikolayDA/picture_helper/issues/1042) | 将分析命令（`.claude/commands/analyze-*`）改为写入 GitHub 议题 | 🟡 中（分析结果落到记录未结事项的地方） | 🟢 低（五个命令文件） | Sonnet，中 | 阻塞：等待 #1040；建议放在同一个 PR 中 |
| [#1041](https://github.com/NikolayDA/picture_helper/issues/1041) | `make pr-ready`：从 diff 识别漂移义务 | 🟡 中（用一条命令取代六个人工判定菱形） | 🟠 中高（新的严格类型脚本、NUL 分隔路径、重命名、Python 3.10 矩阵） | Opus，高 | 阻塞：等待 #1040；宜在 #1036 与 #1037 之后，因为那时两项义务会彻底消失 |
| [#1040](https://github.com/NikolayDA/picture_helper/issues/1040) | 移除推荐清单的实时分诊（表格、状态、工作流、守卫） | 🟠 高（史诗中最大的杠杆：2123 行机制，且议题状态变化不再产生红色运行） | 🟡 中（六种语言版本、脚本、工作流、三个文件中的 42 个测试函数，以及 `TESTING.md` 与 `docs/PROZESSE_UML.md` 中的残留引用） | Opus，高 | 阻塞：等待 #1033；建议与 #1042 原子性地一并处理 |
| [#1039](https://github.com/NikolayDA/picture_helper/issues/1039) | 用所有者脚本替代手工复制 run-ID 的发布 dispatch | 🟡 中（发布流程中的手工操作，无产品风险） | 🟡 中（通过 API 解析 run-ID/产物，严格类型，测试依赖网络） | Sonnet，高 | 推迟：史诗有意将其安排在下一次真实发布之后；在此之前手工路径是 #914/#918 的参照 |
| [#1038](https://github.com/NikolayDA/picture_helper/issues/1038) | 为 CodeQL、依赖审计与许可证检查在 PR 上加路径过滤 | 🟢 低（节省 CI 时间，无质量或风险收益） | 🟢 低（三个 `paths-ignore` 块） | Sonnet，中 | Ready for PR：风险很低，因为这三个运行都不是必需检查（唯一必需检查是 `Lightweight PR checks`） |
| [#1037](https://github.com/NikolayDA/picture_helper/issues/1037) | 路径策略：未知路径改为告警而非阻塞 | 🟠 高（该门禁在每个 PR 上运行；测量窗口内策略改动 22 次） | 🟡 中（策略版本 17→18、ADR 补记、`prepare_release.py`、冻结文档、测试） | Opus，高 | Ready for PR：发布门禁不受影响——分类不变，仅取消阻塞。证据取自下一次 dry-run |
| [#1035](https://github.com/NikolayDA/picture_helper/issues/1035) | 仓库设置：仅 squash、自动删除分支、恰好一个自动审阅者 | 🟡 中（减少合并与审阅噪声，对产品无影响） | 🟢 低（设置与连接器配置，无代码） | –（无代理；仓库所有者） | 可以开始（所有者）：2026-09-09 的实时比对确认了全部四个当前值；`chatgpt-codex-connector` 的自动审阅设置只能在连接器配置中查看 |
| [#1034](https://github.com/NikolayDA/picture_helper/issues/1034) | 为桌面应用启用 Issue Forms，替代 GitHub 默认模板 | 🟡 中（报告质量；浏览器/智能手机字段不适用于 PyQt6 应用） | 🟢 低（两个 YAML 表单加 `config.yml`） | Sonnet，中 | Ready for PR：独立于 #1033/#1040，可随时插入 |
| [#1033](https://github.com/NikolayDA/picture_helper/issues/1033) | 将分诊内容迁入议题并引入优先级/阻塞标签 | 🟠 高（#1040 的硬性前提；否则精心整理的文本会丢失） | 🟡 中（无需改代码，但要为所有未结议题打标签并写 41 条移交评论） | Sonnet，高 | 可以开始：通过 API 做议题整理，不是 PR；2026-09-09 的切换基线是 56 个未结议题，而非议题中记的 54 个 |
| [#1032](https://github.com/NikolayDA/picture_helper/issues/1032) | [史诗] 流程瘦身：分诊迁至 GitHub，减少漂移义务 | 🟠 高（测量窗口内 156 个主线提交中有 28 个纯属分诊维护） | 🔴 高（十一个工作包 #1033–#1043，含顺序与依赖） | –（史诗） | 进行中：顺序为 #1033 → #1040（+#1042）→ #1041/#1043；#1031 以优先级 0 排在最前 |

### 接下来推荐

1. **#1031**（优先级 0）：SessionStart 钩子中的来源校验；没有它，一个变绿的子进程测试可能检查的是旧代码。
2. **#1044** 与 **#1045**：已完成——`tests/test_preview3d_controller.py` 中 #1004/#1005 的测试缺口，
   以及六个 CHANGELOG 版本中缺失的 `#1023` 引用。
3. **启动 v2.10.0**：范围已在 `[Unreleased]` 中；通过
   `scripts/prepare_release.py 2.10.0` 走 runbook 第 1/2 步。该次运行同时补齐 #914 与 #918
   尚缺的端到端证据。
4. **#1033 → #1040（+#1042）**：启动流程瘦身；#1034、#1035、#1037 和 #1038 相互独立，可随时插入（#1036 已完成）。
5. **#693**（无 Qt 核心）：ADR #692 已批准；随后依次进行 #694、#695、#696。
6. **#883**：决定 Qt/代码许可，并证明具体 `u2net.onnx` 的权利与来源，或选择许可明确的替代模型。
7. 在设备/材料获批后，与 #687 的剩余部分、#688 和 #690 一并完成 **#689** 的物理测量；之后复核配置 v2
   的证据状态。v1 保持冻结，新增或矛盾语义应使用后续配置版本。

## 以往轮次

自 v2.2 以来的详细记录：[RECOMMENDATIONS-2026-v2.2-v2.9.zh.md](../../history/RECOMMENDATIONS-2026-v2.2-v2.9.zh.md)。

历史发现和工作记录（第 1–5 轮）：[RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
