[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · **简体中文**

# 代码分析与优先级建议：BgRemover

## 评级标准

| 符号 | 优先级 | 含义 |
|------|--------|------|
| 🔴 | 严重 | 缺陷、崩溃或数据丢失 |
| 🟠 | 高 | 对可靠性或可维护性有明显影响 |
| 🟡 | 中 | 对质量、可读性或可测试性有用的改进 |
| 🟢 | 低 | 可选的打磨或流程改进 |

## 当前状态（2026-09-02，v2.9.0 已发布，未结议题已全部审计）

**每日审计 2026-09-02（状态 `1ec9d96`）：** 已将 42 个未结议题与 GitHub 实时状态比对。自 2026-08-30 起，六个语言版本的分诊表均有误——`recommendations-live-check` 自此持续飘红：缺少 **#914**、**#918**、**#939** 和 **#949**，而 **#692** 仍被列为未结（已于 2026-09-01 通过 PR #947 关闭）。2026-08-31 的审计还把 #918 记为已关闭；它当天在收尾检查后被重新开启，如今只等下一次真实的发布运行。本轮修正了这两点。新评估：#949（测试套件审计，四项可执行的测试改动，无生产缺陷）、#939（常设 heartbeat 告警通道，不要关闭）以及史诗 #914。无新的 🔴 发现。

**发布评估：尚未启动候选版本。** 自 `v2.9.0`（2026-08-29）以来共有 30 个主线提交。随着 PR #953（版本化 EufyMake 目标配置文件、16 位 HEIGHT 默认值、对话框中的配置文件与 X/Y DPI 显示、清单溯源），`[Unreleased]` 首次包含用户可见的条目；其余均为发布自动化、文档与治理。**v2.10.0** 是仅含 #953 发布，还是与 COLOR 色调引擎（史诗 #682 的 #693/#694，ADR #692）一起发布，由负责人决定；冻结门禁在 `ac64c3b` 状态下为绿色。

**EufyMake #681/#687–#691：** PR #948、#951 与 #952 已合并；可复现测试集包含 41 个独立 fixture 和七个真实导出包（模式 4）。Alpha/覆盖、裁剪对位、独立 X/Y DPI、清单/`pHYs` 冲突、Gloss 0/128/255、64…192 归一化、尺寸不匹配、Alpha×Gloss 与 HEIGHT×Gloss 均有自动化验证。Studio 4.2.2 确认了 #689 的无 `pHYs` 72 dpi 回退、按轴的 `pHYs` 优先级、图像导入中不生效的 `manifest.json`、手动尺寸优先、旋转和单图裁剪；对于 #690，所有 PNG 仍是相互独立的“Flat”图层，没有 GLOSS 角色分配。PR #953 集成了**暂定**目标配置文件 v1（#691）；#688–#690 的 E1 物理测量以及由此决定的配置文件升级仍未完成。#687 已完成 17/18 项，等待真实测试后的收尾评审。

保持不变并已关闭：**N1/N2/N4/N5/N6/N7/N8**、**O1–O8**、自 **2026-06-25** 起完成的全部事项、v2.7.0 至 v2.9.0 各版本，以及史诗 #741（含其十一个子议题）、史诗 #805（含 #806–#811）、#817 与 #821；自上次同步以来新关闭：#943（PR #944）与 #692（PR #947）（详见以往轮次）。

未结事项：下方分诊表中每个议题一行。自 #821 起，数量与表行都不再人工维护——`scripts/recommendations_live_check.py --write` 依据 GitHub 实时状态更新全部六个版本，评估列仍是编辑工作。

## GitHub 未结议题 — 分诊状态

| # | 标题 | 相关性 | 复杂度 | 建议模型（投入） | 下一步 |
|---|------|--------|--------|--------------------|--------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Epic] EufyMake 目标配置文件 —— 验证 Height/Gloss/mm-DPI | 🟠 高（关系到最重要导出目标的正确性） | 🔴 高（5 个子议题，需要物理硬件） | –（Epic） | #687 已完成 17/18 项；仅剩真实测试后的收尾评审，#691 已暂定实现（PR #953），仅等待 #688–#690 之后的升级 |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | 假设清单、厂商资料来源、测试矩阵 | 🟠 高（#688–#691 的约束性基础） | 🔴 高（自身交付物已完成；#688–#690 的 fixture/测试单元格缺口未补齐，剩余部分需要真实硬件） | –（无需 Agent；需要真实的 EufyMake 硬件） | 阻塞（外部）—— 已完成 17/18 项；I-06 已在 Studio 中观察，仅剩 #688–#690 真实测试后的收尾评审 |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | 在真实硬件上验证 HEIGHT 位深/语义 | 🟠 高（直接影响浮雕高度） | 🔴 高（需物理打印机、测试样件、测量记录） | –（无需 Agent；需要真实 EufyMake 硬件） | 受阻（外部）：PR #948 已合并，仓库准备完成；其余导入矩阵及安全的 E1 实体打印、浮雕与毫米测量仍待完成 |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | 验证 mm/DPI、目标尺寸、定位契约 | 🟠 高（打印尺寸/对位） | 🔴 高（物理测量、对照图案） | –（无需 Agent；需要真实硬件） | 进行中：仓库测试集和 Studio 子契约已记录，包括 72-DPI 回退、X/Y `pHYs`、清单边界、手动尺寸、旋转和单图裁剪。跨角色裁剪/对位、物理测量和打印公差仍待完成 |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | 验证 gloss/亮光漆语义 | 🟡 中（代码中 gloss 已标记为“experimental”） | 🔴 高（需物理打印、消耗材料） | –（无需 Agent；需要真实硬件） | 阻塞（外部）+ 数字/导入部分已完成——模式 4 与 Studio 4.2.2 已确认 fixture、导出包、72 dpi 几何，以及无 GLOSS 分配的独立“Flat”图层；仍缺实体 gloss 证据 |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | 将带版本号的目标配置文件整合进 validator/writer/对话框/文档 | 🟠 高（强化生产环境导出路径） | 🟠 高（横跨 eufymake_export/_validate/_writer + UI） | Opus，高 | 进行中 —— 暂定配置文件 v1 已通过 PR #953 集成（注册表、对话框、写入器、验证器、文档）；剩余工作是在 #688–#690 的物理测量后将其升级为 `validated`，然后关闭 |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Epic] COLOR 色调/灰度引擎 | 🟡 中高（激光路线图基础，非当前缺陷） | 🔴 高（剩余 4 个子议题：核心→UI→集成→验收） | – （史诗） | 进行中：ADR #692 已批准；接下来是核心 #693 |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | 无 Qt 依赖核心：直方图/灰度/色阶/伽马 | 🟡 中高 | 🟡 中（扩展 `color_ops.py`，隔离良好且易测） | Sonnet，高 | 可以开始：ADR #692（PR #947）给出数据契约；据其公式实现并测试核心 |
| [#694](https://github.com/NikolayDA/picture_helper/issues/694) | 直方图/色阶/伽马的实时预览 + 操作界面 | 🟡 中 | 🟡 中高（Qt UI，需类似高度预览的防抖/世代保护） | Sonnet，高 | 阻塞 —— 等待核心 #693 |
| [#695](https://github.com/NikolayDA/picture_helper/issues/695) | 图层/选区/历史/项目集成 | 🟡 中 | 🟠 高（大量状态转换：撤销/重做、选区、脏状态） | Opus，高 | 阻塞 —— 等待 #693/#694 |
| [#696](https://github.com/NikolayDA/picture_helper/issues/696) | 性能/E2E/文档/激光接口验收 | 🟡 中（收尾关卡，非新功能） | 🟠 高（基准测试套件、E2E、文档、适配器契约） | Opus，高 | 阻塞 —— #695 完成后的收尾议题 |
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
| [#914](https://github.com/NikolayDA/picture_helper/issues/914) | [Epic] 发布流程：runner、自动化证据、解除 main 冻结 | 🟠 高（发布运维；9 个工作包已完成 8 个） | 🟡 中（仅剩 #918 的余项） | – （史诗） | 接近完成：只差“`main` 在发布期间保持可合并”这一成功判据，由下一次真实发布运行经 #918 证明 |
| [#918](https://github.com/NikolayDA/picture_helper/issues/918) | 用发布 ref 取代 main 冻结（ADR + fail-closed 保障） | 🟠 高（发布期间 `main` 保持可合并） | 🟢 低（代码、文档与 ruleset 均已就位） | – （无代理；下一次发布运行） | 受阻（外部）：2026-08-31 收尾检查后重新开启；PR #936 与生效的 ruleset 21941216 均有记录，仅差一次发布后验收可证明从 `release/vX.Y.Z` 启动的运行 |
| [#939](https://github.com/NikolayDA/picture_helper/issues/939) | 运维：自托管 runner（heartbeat 告警通道） | 🟡 中（运维通道，非产品代码） | 🟢 低（仅观察） | – （无代理；仓库 owner） | 长期开启：请勿关闭（`RUNNER_HEARTBEAT_ISSUE`）；2026-08-31 的 FAIL 是计划中的告警通道测试，清理步骤已完成（计划运行 33496675995 通过，x86_64 跳过，Mac 与 Pi 均合格） |
| [#949](https://github.com/NikolayDA/picture_helper/issues/949) | 测试套件审计 2026-09-02（RESOURCES 漂移、CropOverlay、覆盖率缺口） | 🟡 中（测试质量与防漂移，无生产缺陷） | 🟢 中低（四项范围明确的测试改动，不涉及生产代码） | Sonnet，中 | 可以开始：从真实的 `uses:` 行推导 `RESOURCES.md` 的期望值，将 `test_crop_overlay.py` 改用 `set_position()`/`crop_rect()`，并覆盖 `crop_image()` 的矩形分支与 `adjust_color()` 的非 RGBA 分支 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | 为手动 Codex 安全检查恢复 OpenAI 配额 | 🟢 低（仅阻塞一次可选的手动扫描） | 🟢 低（纯运维性质，无代码） | –（无需 Agent；由仓库所有者处理账单） | 阻塞（外部）—— 最近一次运行（29233060507，2026-07-13）并未证明扫描成功；账单/配额仍未解决 |

### 接下来推荐

1. **#693**（无 Qt 依赖核心）：ADR #692 已批准，COLOR 史诗 #682 因此可以开工；
   随后依次进行 #694、#695、#696。
2. **#949**：四项小而明确、无生产风险的测试改动；适合与史诗并行的 PR。
3. 在设备/材料获批后，与 #687 的剩余部分、#688 和 #690 一并完成 **#689** 的物理
   测量；#689 和 #690 的 Studio 导入部分已记录。 之后收尾 #691：升级配置文件 v1，或在结果矛盾时创建 v2。
4. **#883**（MAS 许可策略）决定 Mac App Store 路径 #882——没有该 owner 决策，
   #884–#907 整条链条将持续受阻。

## 以往轮次

自 v2.2 以来的详细记录：[RECOMMENDATIONS-2026-v2.2-v2.9.zh.md](../../history/RECOMMENDATIONS-2026-v2.2-v2.9.zh.md)。

历史发现和工作记录（第 1–5 轮）：[RECOMMENDATIONS-2026-pre-v2.2.zh.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md)。
