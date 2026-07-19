[Deutsch](../../../CHANGELOG.md) · [English](../en/CHANGELOG.md) · [Español](../es/CHANGELOG.md) · [Français](../fr/CHANGELOG.md) · [Українська](../uk/CHANGELOG.md) · **简体中文**

# Changelog

BgRemover 的所有值得注意的变更都记录在本文件中。
其格式参照
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/)；本项目
遵循[语义化版本](https://semver.org/lang/de/)。

## [Unreleased]

### 新增

- **真正的 3D 浮雕预览——交互、高性能且稳健降级（Epic #582、#592–#595）。**
  规范的 HEIGHT 图层变成可旋转、平移和缩放的 3D 表面（工作流“浮雕”步骤、
  “高度”标签页中的 **显示 [2D|3D]** 分段，或“视图 → 显示 3D 浮雕”）。一个
  与 Qt 无关的确定性几何内核（`relief_mesh.py`）将 16 位高度场转换为
  **硬性受限**的网格（按覆盖加权且按行带处理的块抽稀；按质量分级的顶点/
  三角形预算——40 MP 图像永不生成全分辨率网格），而 Qt 原生的
  `QOpenGLWidget` 查看器（`viewer_3d.py`）通过 GL 2.1 着色器路径以 Lambert
  光照进行渲染。高度夸张、光照和质量都是纯粹且受限的显示参数（高度夸张与
  光照无需重建网格）；异步、去抖动的网格构建使用世代 ID 和单网格缓存
  （在高度/角色/尺寸变化时精确失效）。若无 OpenGL 2.1 上下文或初始化失败，
  应用保持稳定并继续提供现有的 2D 浮雕预览及清晰提示（能力探测 + 保证的
  2D 回退）。“保存图像”、EufyMake 导出和项目导出均保持不变——3D 视图仅用于
  显示，不写入模型。架构/UX 固定于
  [`docs/history/ADR-2026-3d-reliefvorschau-renderer.md`](../../history/ADR-2026-3d-reliefvorschau-renderer.md)
  和 [`docs/UX_3D_PREVIEW.md`](../../UX_3D_PREVIEW.md)；用法/回退见
  [`ANLEITUNG.md`](../../../ANLEITUNG.md)。运行时 i18n（de/en）覆盖所有 3D 状态。

### 变更

- **3D 后续审计：延迟能力探测、一致的 UI 状态与稳健的上下文恢复（#582/#595）。**
  OpenGL 探测仅在首次使用 3D 时运行；高度夸张、光照与质量通过 QSettings 和
  重建面板保持同步；重置会恢复所有参数；GL 上下文丢失后会重新上传 CPU 网格。

- **Linux AppImage 恢复启动；修复 aarch64 兼容性问题（#595）。** 在真实的
  Raspberry Pi 5 硬件上手动测试发现两个打包缺陷：AppImage 缺少自己的
  `AppRun` 入口点，在无参数情况下调用捆绑的 Python 解释器，导致进入交互式
  控制台而非图形界面（现通过专用的 `entrypoint.sh` 配方修复）；此外，固定
  的 PyQt6/PyQt6-Qt6 版本在 aarch64 上需要比当前 Raspberry Pi OS/Debian 12
  「bookworm」（2.36）更新的 glibc（2.39），导致出现 `GLIBC` 加载错误。
  PyQt6/PyQt6-Qt6 已回退到最后一个支持 aarch64 的可移植版本
  （6.7.1/6.7.3）。

- **混合安全扫描模型：CodeQL 自动化，Codex 仅手动触发（#551）。** CodeQL
  现在以已版本化的高级配置形式运行（`.github/workflows/codeql.yml`），在
  推送/PR 到 `main` 时以及每周自动分析 Python，提供确定性的、GitHub 原生
  的 SAST 基础覆盖，不依赖外部 API 配额。现有的 Codex Security Scan 现在
  仅通过手动 `workflow_dispatch` 运行；此前的 14 天节奏路径（锚定日期、
  `cadence` 任务）及其启用/禁用开关因对纯手动触发而言冗余而被移除。提示
  词、JSON 模式、产物上传、发现结果校验、去重的 issue 同步以及权限分离
  （`issues: write` 仅存在于下游同步任务中）均保持不变。`SECURITY.md`
  现在描述了当前实际生效的完整安全检查体系；架构决策已记录为 ADR
  （`docs/history/ADR-2026-codeql-codex-sicherheitsmodell.md`）。

- **16 位高度管线收官：预览、导出警告与端到端验收（#590，史诗 #581 收
  尾）。** 浮雕预览现在直接基于规范的 16 位 payload 计算晕渲——低于一个
  8 位台阶的细腻渐变变得可见（瞬态实时预览仍是文档化的显示例外）。当
  8 位导出目标会量化真实的 16 位高度时，EufyMake 导出会给出需确认的警
  告，且"空"检查基于 payload。高度导入会在状态栏注明来源位深，高度面
  板显示内部 16 位表示。新的端到端测试证明导入 → 编辑 → 项目往返 →
  导出 → 重新读取全程无意外的 8 位降级（含旧版迁移与像素级精确的 8 位
  参考量化）；每周基准测试现在也把高度管线（1/16/40 MP 的导入、操作、
  往返、预览）纳入基线测量。

- **16 位高度：导入、生成与操作均无 8 位量化（#589，史诗 #581 的一部分）。**
  高度图导入现在原生读取 16 位灰度（PNG/TIFF）的全部 65536 级（字节序受
  控）；不支持的模式（如浮点图像）会以明确提示被拒绝，不会产生部分图层。
  8 位与彩色来源按文档化的亮度规则精确进入 16 位契约（等价于 ×257）；
  Alpha 仅作为覆盖度。高度图生成直接缩放到 0…65535，新高度图层直接由规范
  payload 创建，外部尺寸按保精度方式缩放。每个高度操作都被明确归类为
  16 位安全或有意量化（恒等参数是按位精确的空操作）；0–255 控件保持原有
  刻度，并通过工具提示说明到 16 位范围的映射。

- **16 位高度管线：领域模型与历史记录无损化（#587，史诗 #581 的一部分）。**
  HEIGHT 图层现按 ADR #586 以 16 位 payload 的规范形式保存高度
  （`Layer.height_data`：`uint16` 值 0…65535，外加单独管理的覆盖度）；
  `Layer.image` 在该图层上仅是派生的 8 位视图，绝不会被回读。撤销/重做
  按位精确地快照 payload（在 256 MiB 预算内按 3 B/px 计费，而非 4 B/px
  的视图），复制/重排/删除保留低位比特，缩放在 `float32` 中插值高度而非
  8 位通道，现有 8 位数据通过一个有意设为过渡期、带日志的兼容适配器
  确定性地迁移（`×257`）。本步骤不改变项目文件格式（v1）与导出
  （#588/#590 随后跟进）；COLOR/GLOSS 图层无回归。
- **项目格式 v2：`.bgrproj` 文件中按位精确的 16 位高度（#588，史诗 #581
  的一部分）。** 高度图层现在还会把规范的 `uint16` 高度值以 16 位灰度
  PNG 的形式存入项目容器（字节序受控、以 sha256 完整性校验防止载荷被截
  断或调换、并有独立的条目上限）——保存/打开往返按位精确地保留低位比
  特。现有 v1 项目可原样打开（确定性的 ×257 迁移），并在下次保存时受控
  地写为 v2；旧版 BgRemover（2.6.0 及更早）无法打开 v2 项目，会给出明确
  的错误提示——文件本身保持原样。格式参考：`docs/PROJECT_FORMAT.md`。
- **严格拒绝未来版本的项目格式（#588）。** v3 及更高版本会在处理未知字段
  或载荷之前停止，并显示已翻译的应用更新提示。当前项目和文件均保持不变，
  从而防止旧版本将未来数据静默重写为 v2。
- **16 位管线审查加固（#610）。** 高度工具、旋转和裁剪现在直接读写规范
  payload；现有的 0…255 UI 值会在明确的边界转换为 16 位。16 位 EufyMake
  导出会保留来源中真实的低位比特，不再把 8 位视图用 `×257` 扩展；8 位
  导出则只进行一次受控量化。外部 NumPy 视图会在共享前复制，确保其基础
  缓冲区不会改变副本或历史快照。

## [2.6.0] – 2026-07-15

### 新增

- **更新检查核心逻辑（#564，Epic #563 的一部分）。** 新增无 Qt 依赖模块
  `app_update.py`：`check_for_update(current_version)` 查询 GitHub Releases
  API（仅使用标准库 `urllib.request`，不下载任何资源文件），返回结构化的
  `UpdateCheckResult`（`UP_TO_DATE` / `UPDATE_AVAILABLE` /
  `CHECK_FAILED`）；任何网络/解析错误都以带可读错误信息的 `CHECK_FAILED`
  返回，绝不向外抛出异常。
- **AI 模型状态检测（#568，Epic #563 的一部分）。** 新增无 Qt 依赖模块
  `ai_model_status.py`：`get_model_status()` 检测 rembg 默认模型
  (`u2net.onnx`) 是否已存在于缓存目录（`U2NET_HOME` 或 `~/.u2net`）中——
  不导入 `rembg`，也不会触发下载。
- **"检查更新…" 菜单项（#565，Epic #563 的一部分）。** 工具菜单中的手动更新
  检查在独立的工作线程中非阻塞运行（`UpdateCheckWorker`，类似现有的 rembg
  预热机制），并根据结果显示相应的翻译对话框：当前版本、带"打开发布页面"
  按钮的新版本，或不含技术堆栈信息的错误提示。重入保护可防止第二次并行
  检查。
- **"管理 AI 模型…" 菜单项（#569，Epic #563 的一部分）。** 新增对话框
  `ai_model_dialog.py` 显示 rembg 模型的缓存状态（已下载/尚未下载/AI 功能
  不可用），提供下载/重试和取消按钮及忙碌指示器；未安装 rembg 时菜单项被
  禁用（并带有说明性提示）。
- **启动时自动检查更新（#566，Epic #563 的一部分）。** 设置对话框中新增
  "启动时自动检查更新"选项（默认**关闭**——需要显式启用）。启用后，会在
  启动后不久进行一次静默检查；`CHECK_FAILED` 完全保持静默，只有
  `UPDATE_AVAILABLE` 会在状态栏显示一个低调、可点击的提示，点击后打开与
  手动检查相同的结果对话框——无需再次发起网络请求。
- **AI 模型下载：与预热机制的真正联动（#570，Epic #563 的一部分）。** AI
  模型对话框中的下载按钮现在会附加到已在运行的启动预热，而不是启动第二个
  进程/线程（`WorkerController.start_warmup` 现在支持多个观察者）；状态栏
  与对话框因此不会再显示相互矛盾的状态。取消按钮使用新的协作式取消机制
  （`RembgWarmupWorker.cancel()`，类似于 `AIWorker`/`FloodFillWorker`）：
  推理子进程会被干净地终止，且不会将取消误报为成功或失败。
- **菜单项「安装 AI 背景移除…」。** 新的 `ai_install_dialog.py` 对话框会向未安装
  rembg 后端的用户（例如在 Raspberry Pi 最小化安装之后）显示相应的安装命令，
  并带有复制到剪贴板按钮——按平台区分（Linux：venv/pip 方案；macOS：
  `create_BgRemover_app.sh`，因为那里维护着专属的应用包 venv），并在当前
  Python 版本低于 rembg/onnxruntime 所需的 3.11 时给出警告。应用内故意不做
  自动安装尝试：PEP 668 无论如何都会阻止向系统 Python 执行 pip 安装，而且
  刚安装的包在当前进程中也要重启后才能生效。

### 变更

- **针对新 CVE 提升了 setuptools 的版本锁定。** `pyproject.toml`
  （`[build-system]`）和 `requirements/constraints.txt` 中的 `setuptools`
  已从 `78.1.1` 提升到 `>=83.0.0`（`constraints.txt` 中为 `==83.0.0`）——
  修复了 `PYSEC-2026-3447`（`MANIFEST.in` 排除模式中的 Unicode 规范化绕过，
  macOS APFS/HFS+），并在此前已锁定的 CVE-2024-6345/CVE-2025-47273 之外。
- **发行版构件名称现在按平台/设备明确区分（#584）。** 五个发行版下载文件
  （Linux x86_64 和 Linux/树莓派 aarch64 的 AppImage/`.deb`，macOS arm64 的
  `.dmg`）现在命名为
  `BgRemover-X.Y.Z-<平台标签>[-ai].<扩展名>`，而不再是裸架构名——例如
  `BgRemover-2.6.0-linux-raspberrypi-arm64-ai.AppImage`。此前 Linux/树莓派的
  `.deb` 和 macOS 的 `.dmg` 都使用相同的 `arm64` 标签，只能靠扩展名区分；
  `-ai` 后缀还能清楚显示每个构件——包括树莓派构建——都内置了与 macOS
  构建相同的 AI 背景移除功能。

### 修复

- **AI 模型对话框中可见的预热错误（#575）。** 如果自动启动预热因推理子
  进程中的具体错误而失败（例如因 venv/解释器不匹配导致的
  `ModuleNotFoundError`，或连接中断/`EOFError`），「管理 AI 模型…」现在会
  在下次打开时立即显示具体的技术原因，而不是仅显示中性的「尚未下载」
  提示且毫无问题线索——此前该错误只会记录到日志中。
- **「管理 AI 模型…」在缺少 rembg 时不再毫无反应（#575）。** 未安装 rembg
  时，该菜单项会被静默禁用——而 Qt 默认不在菜单中显示工具提示，点击看起来
  就像一个 bug（「没有任何反应」），也没有任何解释。该菜单项现在始终可用：
  对话框自身会显示「AI 功能不可用」状态，并额外注明当前 Python 环境
  （`sys.executable`）——这样一来，用错误的解释器启动（例如用系统 Python
  而不是包含 rembg 的 venv）就能立即被识别。

## [2.5.0] – 2026-07-11

### 新增

- **运行时界面支持六种语言（重构 i18n，#430）。** 完整的运行时字符串表现在还维护
  西班牙语、法语、乌克兰语和简体中文版本——包括重构新增的工作流字符串（步骤标签、
  步骤标题与描述、卡片标题、导航）。这些语言会自动出现在设置对话框的语言选择中；
  德语仍是有保证的回退语言，i18n 对等测试（键与占位符一致性、每种语言的界面冒烟
  测试）覆盖全部六种语言（史诗 #425 的一部分）。
- **浅色主题与设计令牌（界面重构，史诗 #424）。** 一套集中的、基于令牌的主题系统
  （包含浅色与深色两种方案的 `Palette`）通过 `QPalette` 和应用级样式表为整个界面着色。
  通过“视图 → 浅色主题”可在运行时于浅色与深色之间切换；该选择会记入设置并在启动时应用。
  无障碍性：每个交互元素都显示可见的焦点环（切换主题后依然保留），步骤栏可用键盘操作
  （Tab + 回车/空格），所有控件满足最小点击目标尺寸，并由 WCAG AA 对比度矩阵
  持续守护两种配色方案（#427–#429、#441）。
- **带卡片式检查器的引导式工作流（界面重构，史诗 #413/#418）。** 右侧栏现在以六个清晰的
  步骤引导编辑（打开 · 抠图 · 调整 · 形状与尺寸 · 浮雕与图层 · 导出）：顶部为步骤条，
  检查器带有步骤标题和固定的“上一步/下一步”导航，并提供上下文相关的工具栏（选择工具
  仅在抠图步骤显示）。在加载图像之前，步骤 2–6 处于锁定状态；加载后会自动切换到抠图
  步骤。现有的操作连线保持不变（#419–#422、#415–#417）。

- **用户可选的组合式 2D 预览（阶段 1 收尾）。** 画布现在提供明确且不依赖激活图层的
  颜色、颜色上的浮雕、高度（灰度）、光泽和组合模式。仅保留一个图像的缓存会按内容修订、
  模式和显示参数失效；“视图”菜单与新的“预览”标签页保持同步，浮雕强度和光泽可见性实时
  生效。清晰提示与“模式×图层”测试矩阵守住 #363 契约：“保存图像”仍只导出 COLOR 合成
  （#387、#388；完成史诗 #384）。
- **用于组合 2D 预览的无 Qt 浮雕与光泽渲染器。** 新增严格类型化模块
  `bgremover/relief_preview.py` 与 `bgremover/gloss_preview.py`：前者从
  `HeightField` 生成确定性的定向 hillshade（8/16 位数据结果等价），后者生成清晰可见的
  光泽高光。二者都会在尺寸校验后将效果叠加到 RGBA 彩色图案上，逐位保留其 Alpha 通道，
  并提供真正的中性空操作；纯像素与边界测试覆盖光照方向、覆盖度、强度和 Alpha（#385、
  #386）。
- **常规保存时的导出前检查。** “保存”/“另存为…”现在会在写入前对项目运行通用检查（#379），
  并像 EufyMake 流程一样显示结论：**错误会阻止**保存并给出清晰提示（不触发写入），
  **警告**需要用户明确确认。取消没有副作用（不写入、不产生临时文件）。部分透明被有意
  **不**标记——它是抠图工具的正常输出。所有文本均为 de/en；结论显示复用与 EufyMake 显示
  相同的 `format_finding` 渲染逻辑（#380）。至此，epic #375（尺寸精确输出 + 导出检查）完成。
- **“调整大小…”对话框新增毫米/DPI 模式 + 打印区域检查。** 调整大小对话框现在提供两种单位：
  像素（与此前一致）与**毫米 + DPI**。在毫米模式下输入以毫米为单位的宽/高及 DPI，所得的
  **像素尺寸**通过共享几何（#376）实时显示，并可选择锁定宽高比。**打印区域检查**会将图案与
  可选目标介质（A3/A4/A5/Letter）比较，超出时给出清晰警告。应用时，物理目标尺寸（毫米）通过
  `project_model` 的 setter 固化到项目中（权威来源；DPI 由毫米 + 像素尺寸推导），并在
  `.bgrproj` 往返后保留；重采样本身仍为纯像素（`Project.resize`）。所有文本均为 de/en（#377）。
- **通用的、无 Qt 的导出前检查（共享框架）。** 新增严格类型化模块
  `bgremover/export_checks.py`，将 `eufymake_validate`（#354）的结论框架提升为共享基础：
  通用的 `Finding`/`CheckCode`/`Severity` 契约，具备稳定代码、i18n 键
  （`export.checks.*`，de/en）与确定性排序。实现了与格式无关的检查：尺寸（px > 0、
  百万像素上限）、分辨率合理性（DPI 来自 #376）、色彩空间（期望 RGBA）、透明度
  （完全透明／意外的部分 alpha）、空输出，以及打印区域/边距检查（物理尺寸对比目标介质）。
  `eufymake_validate` 现在基于该共享基础（重新导出 `Severity`/`has_blocking_errors`/
  `split_findings`）；EufyMake 专有代码仍保留在其中，且所有既有 EufyMake 测试保持不变并通过
  （#379）。
- **在输出中锚定 DPI/分辨率。** 保存栅格图像时，`image_ops.save_image_file`
  现在可选地将项目 DPI（#376）作为纯元数据嵌入——PNG（`pHYs`）、JPEG（JFIF 密度）
  与 TIFF（`Resolution`/`ResolutionUnit`）；WebP 不携带 DPI。画布保存路径会传入
  由物理尺寸 + 像素尺寸推导出的分辨率；未设置项目 DPI 时行为保持不变，且像素/透明度
  绝不会被改动（保留逐位精确的单 COLOR 图层导出）。EufyMake 导出现在从模型的
  毫米/DPI getter 提供其 `ExportTarget`，而非导出本地的推导（#378）。
- **毫米/DPI 作为项目属性 + 共享的无 Qt 几何运算。** 新增严格类型化模块
  `bgremover/units.py`，将全部 px↔毫米↔DPI 运算集中到一处：从任意两个已知量确定性地推导
  第三个量（`MM_PER_INCH = 25.4`），校验输入，并将无效值（≤ 0、非数值、形状错误）报告为
  结构化的 `UnitsError` 错误，而非静默修正。`Project` 新增针对物理目标尺寸（毫米）与分辨率
  （DPI）的受校验 setter/getter：物理尺寸为权威来源，DPI 由它与像素尺寸推导得出（不会漂移），
  并在 `.bgrproj` 往返保存/加载后保持数值相等。EufyMake 导出现在使用同一套几何运算
  （`_derive_physical_size`/`_derive_dpi`/`MM_PER_INCH`），行为保持不变（#376）。
- **EufyMake Studio 导入：菜单、对话框、检查显示与设置。** 新增菜单操作
  “导出 EufyMake Studio 资源…”（项目菜单，Ctrl+Alt+E）打开一个 Qt 对话框
  （`eufymake_export_dialog.py`）：彩色图案为必选，高度图/光泽蒙版仅在项目支持时可选
  （光泽明确标注为实验性），位深 8/16（16 标注为未确认），推导出的目标/物理尺寸，以及
  来自检查（#354）的**实时检查结果显示**：错误会阻止导出，警告需要明确确认。写入通过
  `write_export` 原子完成；取消/出错既不改动项目也不改动目标，覆盖确认可保护已有文件夹。
  成功对话框显示目标路径及 Studio 后续步骤（导入、定位、分配墨水模式/图层、另存为
  `.empf`）。导出文件夹与通用选项保存在带版本的 QSettings 中（架构 v2，附加键带迁移）。
  `build_export_plan`/`write_export` 新增 `optional_roles`/`bit_depth` 供界面选择。
  所有字符串均为 de/en；界面始终称其为导入资源，绝不声称生成完整的 `.empf` 项目（#355）。
- **EufyMake 导出：渲染、原子写入与一致性检查（无 Qt）。** 两个新的严格类型化模块
  基于 #352 的计划构建：`bgremover/eufymake_validate.py`（`validate_export`）以确定性
  顺序收集结构化检查结果（稳定代码、`error`/`warning`、角色、i18n 键）；硬错误（缺少
  彩色图案、缺少所选角色、尺寸不匹配、目标参数无效）会阻止导出，而警告（高度/光泽数据
  为空或恒定、16 位未确认、光泽仅为墨水模式辅助资源、物理尺寸无厂商约定）仅在确认后才
  允许导出，所有消息均为 de/en（#354）。`bgremover/eufymake_writer.py`
  （`render_export`/`write_export`）将彩色图案（= 合成，RGBA 保留 Alpha）、高度图
  （灰度浅色 = 高位，8/16 位）和可选光泽蒙版按目标尺寸渲染，并附带 `manifest.json`，
  以**原子方式**写入（渲染到临时目录，通过单个 `os.replace` 步骤发布；失败时保留现有
  目标，清理临时数据；通过 `overwrite` 控制冲突行为）。不生成原生 `.empf`（#353）。
- **EufyMake 导出：数据模型与规划（无 Qt）。** 新增严格类型化模块
  `bgremover/eufymake_export.py`：`build_export_plan(project)` 将图层角色确定性地
  映射为由 `ExportAsset` 组成的 `ExportPlan`——彩色图案（RGBA PNG）为**必需**
  （显式 `COLOR_MOTIF` 角色或 COLOR 合成），高度图与光泽蒙版为**可选**的灰度 PNG
  （光泽为实验性）。文件名、配置版本与默认值均为有据可查的 **BgRemover 约定**
  （而非官方 EufyMake 规范）；高度语义**浅色 = 高位**在类型契约中固定，而位深/光泽
  的待确认问题以及刻意不生成原生 `.empf` 均被显式标注。物理尺寸、DPI 与位深可从
  项目元数据或默认值可复现地推导；非法取值会产生结构化错误。这是纯数据模型，不
  渲染/写入/界面（后续见 #353–#355）（#352）。
- **EufyMake 导出包 ADR。** 新的架构决策记录了 #352/#351 面向导入的包约定：
  彩色图案采用 RGBA PNG，高度图采用浅色 = 高位的灰度 PNG，可选光泽蒙版；同时将
  16 位数据、光泽语义和原生 `.empf` 格式列为待确认事项。
- **抠图精修：边缘平滑 / 羽化。** 在 `image_ops.py` 中新增无 Qt、严格类型化的
  `feather_alpha(img, radius, *, mask=None)`：**仅对 Alpha 通道**进行高斯模糊
  （RGB 逐位保留；`radius = 0` 为空操作；完全不透明的图层在边界不产生伪影）。画布
  将其接入为作用于活动图层的 `feather_active_edges(radius)`，**受选区限制**（若存在
  选区），并通过现有应用路径支持**撤销/重做**。界面：背景选项卡中新增半径滑块与
  “平滑边缘”按钮（紧邻抠图）。所有新增字符串 de/en 对齐（#361）。
- **活动颜色图层的色彩校正（亮度/对比度/饱和度）。** 新增无 Qt、严格类型化模块
  `bgremover/color_ops.py`，提供 `adjust_color`（Pillow `ImageEnhance`，**精确保留
  Alpha 通道**，中性值为逐位一致的空操作）——作为可复用的色调原语，供后续共享引擎
  （第 #6 级）使用。画布为此提供通用的**实时预览**
  （`preview_color_op`/`cancel_color_preview`，瞬态、不改动模型；预览在
  `_refresh_image` 中优先），以及对活动 **COLOR** 图层可撤销/重做的提交
  （`apply_color_op`，对非 COLOR 图层无效）。右侧面板新增“调整”选项卡，含
  亮度/对比度/饱和度滑块以及**重置**与**应用**。所有新增字符串 de/en 对齐（#360）。
- **调整尺寸 / 缩放到目标尺寸（重采样）。** 在 `image_ops.py` 中新增无 Qt、
  严格类型化的图像操作 `resize_image`/`resized_size`（尺寸相同时为空操作；
  纵横比/百万像素门限辅助函数），并在 `project_model.py` 中新增 `Project.resize`，
  可一致地对**所有图层**与画布尺寸进行重采样（COLOR 采用所选方法，HEIGHT 通过
  高度表示无损处理；颜色合成保持对齐）。画布将其接入并支持撤销/重做，带百万像素
  门限（超限时给出清晰的本地化拒绝提示，不分配超大缓冲区）；新增“调整尺寸…”对话框
  （以像素为单位的宽/高、**锁定纵横比**、重采样方法），可通过“编辑”菜单（Ctrl+R）
  与变换选项卡打开。保留的物理尺寸（`META_PHYSICAL_SIZE_MM`）保持不变（毫米/DPI
  留待后续阶段）。所有新增字符串 de/en 对齐（#359）。
- **高度表示与 2D 可视化（高度图基础）。** 新增无 Qt、严格类型化模块
  `bgremover/height_map.py`：高度 ↔ 灰度数组的无损转换（`HeightField`，约定
  `R==G==B==高度`、`A==覆盖`）、将任意值归一化到高度范围以及画布尺寸校验；内部
  以 `uint16` 存储，因而可扩展到 16 位（`max_value`）。画布现在以灰度显示**活动的
  HEIGHT 图层**；颜色合成保持不变（一致性）（#345、#344）。
- **生成与导入高度图（无 AI）。** `bgremover/height_map.py` 新增
  `generate_from_image`：从彩色图像**确定性地**构建高度图（通道加权/亮度 →
  色阶曲线 → 伽马 → 反相）。画布将其接入为可撤销/重做的新活动 HEIGHT 图层并赋予
  `HEIGHT_MAP` 角色：`generate_height_map` 取自活动 COLOR 图层或合成，
  `import_height_map` 通过 `open_validated_image` 校验加载灰度文件（格式/文件
  大小/百万像素防护，清晰的本地化错误消息）并缩放到画布尺寸（#346、#344）。
- **高度图编辑器（提亮/压暗/设定/反相）。** `bgremover/height_map.py` 新增
  感知选区、无损的高度操作（`adjust_height`、`set_height`、`invert_height`；
  带钳制，输入不变）。画布将其接入**活动 HEIGHT 图层**
  （`lighten_/darken_/set_/invert_active_height`）：它们尊重已有选区（否则全局），
  可撤销/重做，并对 COLOR 图层刻意不起作用（颜色编辑无回归）。最大程度复用现有的
  画笔/选区/历史路径（#347、#344）。
- **高度图优化（`height_ops`）。** 新增无 Qt、严格类型化、兼容 16 位的模块
  `bgremover/height_ops.py`，提供对高度场的纯粹、确定性操作：色调
  （`levels`/`gamma`）、平滑（`gaussian_blur` 可分离、`median_blur` 保边——纯
  numpy，无新依赖）、`threshold`、级数缩减（`quantize`）与高度范围钳制
  （`clamp_range`）——与后续等级共享的同一套色调/灰度原语。画布为此提供通用的
  **实时预览**（`preview_height_op`/`cancel_height_preview`，瞬态、不改动模型）
  以及可撤销/重做的提交（`apply_height_op`），作用于活动 HEIGHT 图层（#348、#344）。
- **高度图工作区可用（UI）——史诗完成。** 右侧面板新增“高度”标签页
  （`height_map_panel.py`）：从图像**生成**高度图或**导入**灰度图，使用
  提亮/压暗/设定/反相进行**编辑**，并通过色阶/伽马/平滑（高斯、中值）/阈值/级数/
  范围配合实时预览进行**优化**。编辑与优化是**模式上下文相关**的——仅当活动图层为
  HEIGHT 图层或带有 `HEIGHT_MAP` 角色时才启用；颜色编辑保持不变。于是完整流程
  （生成 → 绘制 → 优化 → 反相 → 在 `.bgrproj` 中无损保存/重载）现可通过 UI 操作。
  所有新字符串通过 `i18n.py`（de/en 一致）；完成高度图史诗（#349、#344）。
- **无 Qt 的项目/图层数据模型。** 新增严格类型化模块
  `bgremover/project_model.py`，包含 `Project` 与 `Layer`（`LayerKind`
  颜色/高度/光泽/通用，角色在整个项目内唯一），作为图层史诗的基础：有序图层、
  恰好一个活动图层、纯操作（添加/删除/重排/复制/重命名，
  可见性/不透明度/锁定/角色），以及对可见颜色图层的 Alpha 合成——不涉及任何
  Qt、渲染、持久化或历史记录的接线（#330、#329）。
- **图层感知、无 Qt 的撤销/重做历史。** 新增严格类型化模块
  `bgremover/project_history.py`（`ProjectHistory`），将撤销/重做从单张图像提升到
  项目模型：涵盖结构性变更（添加/删除/重排/复制图层、活动图层、
  可见性/不透明度/锁定/角色）以及每个图层的像素变更。内存策略：轻量的结构快照加上
  一个去重像素池，在共享的撤销/重做预算中对未改动的图层只计一次（原始状态与当前
  状态不计入预算）；保留 `descriptions()`/`undo_to()`/“恢复原始”。尚未接入画布
  （#331、#329；将在 #332 中接入）。
- **`.bgrproj` 项目文件格式（无损保存/加载）。** 新增无 Qt 模块
  `bgremover/project_io.py` 与 `bgremover/project_schema.py`，将完整的多图层项目
  写入/读取为 ZIP 容器（`manifest.json` 含格式版本、画布尺寸、有序图层列表及
  角色/元数据，外加每图层一个 RGBA PNG）。保存是原子的（`mkstemp`+`os.replace`）；
  加载进行防御性校验（文件大小上限、每图层百万像素上限、对 zip-slip/意外条目的
  防护、清晰的本地化错误消息）。模式带迁移钩子做版本管理：旧版本迁移，新版本保持
  不变（仅警告）。尚未接入菜单/对话框（#333、#329；将在 #334/#335 中接入）。
- **图层面板与项目菜单。** 右侧面板新增“图层”标签页：创建图层、选择（活动编辑
  图层）、显示/隐藏、调整不透明度、上/下重排、复制、删除、重命名，以及分配角色
  （颜色主题/高度图/光泽）——所有更改都作用于画布合成（#332），并可撤销/重做
  （#331）。新增“项目”菜单：“新建项目”（`Ctrl+N`）、“打开项目…”（`Ctrl+Shift+O`）、
  “保存项目”（`Ctrl+Alt+S`）和“项目另存为…”（`Ctrl+Alt+Shift+S`），接入 `.bgrproj`
  格式（#333）；`Ctrl+O`/`Ctrl+S` 仍保留给图像工作流。加载/保存错误以清晰的本地化
  消息显示。所有新字符串均经由 `i18n.py`（de/en 对等）
  （#334、#329；图像→项目迁移将在 #335 中加入）。

### 变更

- **图像→项目集成，以及“最近打开”支持项目。** “打开图像”和拖放现在会创建一个
  单图层项目（经由 `image_loading` 的校验加载保持不变）；“最近打开”同时列出图像
  **与** `.bgrproj` 项目，并按扩展名正确打开每种类型。会记住最近使用的项目目录
  （新增设置键；无需模式迁移——未来版本保护已被测试覆盖）。单图导出仍写出合成
  （单图层项目逐位一致），“恢复原始”返回加载时状态的文档。收尾图层史诗
  （#335、#329）。
- **编辑器现在基于图层工作（合成渲染 + 活动图层）。** 画布持有 `Project`（#330）
  而非单张图像，并显示/保存可见图层的**合成**（顺序/可见性/不透明度）；所有工具
  （魔棒/选区、画笔/橡皮、套索、AI 抠图、替换背景、翻转、圆角）都作用于**活动图层**，
  选区蒙版也以其为准。改变尺寸的几何操作（旋转、裁剪）会一致地应用到所有图层，以保持
  模型不变量。撤销/重做与“恢复原始”都经由图层感知的 `ProjectHistory`（#331）。仅含
  一个 COLOR 图层的项目与此前逐位一致（对等，包括保存时保留透明像素下的 RGB 值）；
  AI 取消路径仍无 `QThread.terminate()` 回归（#332、#329；图层面板 UI 将在 #334 中加入）。
- **GitHub 发布说明现在来自 CHANGELOG。** 发布工作流（`release-linux.yml`）会
  从 `CHANGELOG.md` 的 `## [X.Y.Z]` 小节中提取 `vX.Y.Z` 标签的发布正文，并通过
  `--notes-file` 传给 `gh release`——包括复用已存在的发布时（`gh release edit`），
  而不仅是首次创建。写死的“Automated build…”文本被移除；若缺少对应小节，
  publish 作业会明确失败（不再静默回退）（#311）。
- **每周基准测试不再把环境差异误报为性能退化。** 每个结果
  （`benchmarks/results/`）现在都带有环境指纹（Python/Pillow/NumPy 版本、架构、
  CPU 数量、runner）；比较会跳过不可比较的基线（缺少指纹、版本或基准参数不同），
  并在同一次运行中通过多次重复（中位数）确认可疑数值后才创建 issue
  （#277、#278、#279）。

### 修复

- **深色主题背景色与原型对齐。** 深色模式的背景区域(`theme.DARK`:检查器面板、
  步骤条、工具栏、导航底栏、状态栏、控件与卡片)现在采用已确认原型
  (`design/Prototyp A - Geführter Workflow.dc.html`)中偏冷的蓝灰色调,而不是
  接近纯黑的中性色。`card_bg` 现在同样使用原型数值 `#2e353f`;
  `docs/REDESIGN_SPEC.md` §2 记录了采用的数值以及剩余的刻意 token 偏差
  (#475、#496)。
- **深色主题边框改为柔和叠加效果,而非生硬的灰色调。** `border` 与 `hairline`
  现在是半透明白色叠加效果,与原型一致(会随所在表面呈现不同效果,而不是在任何
  位置都同样生硬);新增的 `border_2` 用于中性次要按钮(裁剪格式、保存格式等,
  `panel_btn_style`)的次级边框色调。菜单栏现在与工具栏共用 `toolbar` 色调,
  而不再使用状态栏的色调,与原型中菜单栏和工具栏颜色一致的做法保持一致(#476)。
- **深色主题的强调蓝色与原型对齐。** `accent`/`accent2`(以及由此派生的
  `accent_soft`/`accent_line`/`accent_shadow` 表面)现在采用原型中更明亮、
  偏薰衣草色的蓝色,而不是较暗淡的色调——在主按钮渐变、"下一步"按钮、活动工具、
  活动步骤圆圈以及滑块手柄上都能看到。`accent_text` 此前已与原型数值完全一致;
  `accent_shadow` 仍只是一个颜色值,没有发光效果(Qt QSS 不支持
  `box-shadow`,#477)。
- **右侧栏滑块现在复刻原型。** Qt 滑块现在与原型中的 `input[type=range]`
  一致:8 px 轨道、`accent` 填充段、浅灰色剩余轨道、白色轨道边框、白色 16 px 手柄,
  以及 `9px 0 2px` 的垂直间距;图层面板中的不透明度滑块也同样适用(#496)。
- **预览分段控件(步骤 6)现在使用正确的原型表面。**"颜色/浮雕/高度/光泽"容器
  (`_ModeSegments`)之前错误地使用了 `tabbar` 色调;核对原型实际的 CSS 规则
  (而不仅是 `:root` 变量)后发现,正确的值应为内凹的 `--inset` 表面——已新增
  为 `inset` 令牌并接入。另外两个在原型中已声明但未使用的令牌(`label`、
  `good_line`)也已为完整性添加到 `Palette` 中,目前尚无使用方;原型中不存在
  对应的 `bad_line`,因此未凭空创建(#479)。
- **画布透明棋盘格现在跟随当前主题。** 透明图像区域背后的棋盘格图案此前固定为
  浅灰色(`QColor(170,170,170)`/`(210,210,210)`),在深色模式下看起来像画布
  中间的一块亮斑。`checker_a`/`checker_b` 通过调色板解决了这个问题(深色:
  `#2c313a`/`#353b45`;浅色:`#dde2ea`/`#eef1f5`);`make_checker_brush`
  现在接收当前调色板,`ImageCanvas.apply_palette` 会在切换主题时实时刷新该
  图案——无需重启应用(#478)。
- **修正 REDESIGN_SPEC.md 颜色表并新增偏差回归测试。** 该文档声称是从原型
  1:1 复制而来,但根据其自身的来源说明,从未真正与实际颜色数值核对过——逐行
  比对后发现文档本身也存在独立于 `theme.py` 的偏差(缺少
  `checker_a`/`checker_b`、`inset`、`label`、`good_line`、`border_2`;浅色
  方案此前只是一段文字摘要而非表格)。§2/§3 现在是与 `theme.DARK`/
  `theme.LIGHT` 完全一致的完整表格;浅色方案与原型之间仍存在的、刻意排除在
  本史诗任务范围之外的偏差,现在也已明确记录而非略而不提。
  `tests/test_theme.py` 中的两个新测试永久性地守护这一点:一个将规范表格与
  调色板进行比对,另一个进一步将 `theme.DARK` 直接与原型包中嵌入的 CSS
  变量核对——只要代码与文档再次出现偏差,两者都会失败(#480,完成史诗
  任务 #474)。
- **数据图层尺寸不匹配时实时预览降级为 COLOR。** 当 HEIGHT/GLOSS 图层的像素尺寸
  （异常或外来项目状态）不再与基底一致时，`_render_preview_uncached` 现在会在**每一种**
  预览模式下把该图层视为缺失角色并回退到 COLOR 合成，而不是显示尺寸错误的视图或用异常
  中断渲染路径——与既有的“角色缺失/不可见 = 降级”规则一致。渲染/像素回归测试将尺寸
  不一致的 HEIGHT/GLOSS 图层送入 `HEIGHT`/`RELIEF`/`GLOSS`/`COMBINED`，并验证得到
  COLOR 结果（#404）。
- **移除 EufyMake 导出中的死几何路径。** 自切换到项目模型 getter（#377/#378）后已成
  孤儿的私有函数 `_derive_physical_size`，以及仅在此处使用的 `parse_size_mm` 导入已
  一并删除；`_derive_target` 仍从 `project.physical_size_mm`/`project.dpi` 推导物理
  尺寸与 DPI。行为不变；CLAUDE.md 的几何说明现在指向实际使用的路径（#406）。
- **Phase 1 完成后的画布预览保持一致。** 颜色和高度实时预览现在作为临时图层内容
  通过所选模式管线，因此模式、浮雕强度和 Gloss 开关会立即生效，同时不改变模型或
  导出。隐藏的 Height/Gloss 角色图层不再参与渲染，浮雕强度为 0 时会完全跳过昂贵的
  hillshade（#397，#396 的后续修复）。
- **活动高度图层下的图像导出。** “保存图像”现在会再次忽略当前编辑图层并写入
  COLOR 合成。灰度 HEIGHT 视图仅保留为画布显示，不再会被静默导出为普通图像；
  单一 COLOR 图层的逐位导出仍保持不变，包括透明像素下的 RGB 值（#363）。
- **Height Map 中值滤波受内存限制。** `height_ops.median_blur` 不再materialize
  完整的 `(2r+1)² × H × W` 窗口栈（在 40 MP/半径 10 时约为 33 GiB），而是按
  **行带**处理图像，每个带的栈通过 `_MEDIAN_MAX_TEMP_BYTES` 硬性上限。因此额外内存
  与图像尺寸无关，也不再随半径增长，而结果保持**逐位**一致（相同的边缘处理、
  `coverage`、`max_value`、16 位）。`gaussian_blur` 作为可分离卷积本就是
  `O(H × W)` 且与半径无关——已在 docstring 中评估。回归测试覆盖所有 UI 半径下与
  完整栈的等价性以及 40 MP 情况的内存预算（#365）。
- **高度上下文：模型、界面与画布遵循同一约定。** 现在，当且仅当
  `kind == LayerKind.HEIGHT` 时图层才支持高度；`HEIGHT_MAP` 角色只能位于 HEIGHT
  图层上。新的中心化、无 Qt 规则（`role_allowed_for_kind`）是唯一的事实来源：
  模型 API（`Layer`、`assign_role`）会以 `IncompatibleRoleError` 拒绝在
  COLOR/GLOSS/GENERIC 上设置 `HEIGHT_MAP`，图层面板仅为 HEIGHT 图层提供该角色，
  高度图标签仅在活动 HEIGHT 图层时启用其工具——因此界面不再承诺画布随后会拒绝的
  操作。加载历史上不兼容的项目时，仅无损移除无效角色（类型、名称、像素、顺序与
  元数据保持一致），并显示翻译后的警告（#364）。

## [2.4.1] – 2026-06-17

### 修复

- **macOS 下载版应用（`.dmg`）启动后不断打开新窗口。** 在冻结的程序包中，AI
  推理通过 multiprocessing “spawn” 启动其子进程，而这会重新启动应用自身的二进制
  文件；由于程序包入口未调用 `multiprocessing.freeze_support()`，每个子进程都会
  再次运行 GUI——形成 100 多个窗口的“fork 炸弹”，只能重启才能停止。PyInstaller
  入口现在会首先调用 `freeze_support()`，使推理子进程正确启动，而不是打开 GUI。

- **macOS 下载版应用（`.dmg`）无法启动。** 冻结后的程序包在 `import bgremover`
  阶段即以 `PackageNotFoundError` 以及随后的 `FileNotFoundError` 中止，因为
  PyInstaller 未打包该软件包的元数据，而程序包内也没有可作后备的
  `pyproject.toml`——图标只是短暂闪烁，随后便毫无反应。PyInstaller spec 现在会
  打包 `*.dist-info` 元数据（`copy_metadata`），并且版本探测不再可能中断启动
  （以防御性后备取代未处理的异常）。

- **`.dmg` 中的 AI 抠图无法加载。** 推理子进程在 `import rembg` 时以
  `PackageNotFoundError`（“No package metadata was found for pymatting”）退出：
  PyInstaller 打包了 rembg 各依赖的代码，却未打包它们的 `*.dist-info` 元数据，而
  `pymatting` 在导入时会读取自身版本。spec 现在会打包整条 rembg 依赖链的元数据
  （`copy_metadata(…, recursive=True)`）。

## [2.4.0] – 2026-06-15

### 新增

- **macOS 应用提供下载（`.dmg`）。** 通过 PyInstaller 构建自包含的
  `BgRemover.app`（Apple Silicon/arm64）并打包为 `.dmg`，附加到 GitHub 发布中
  ——与 Linux AppImage 类似，且无需本地安装 Python。该程序包目前**未签名**：
  首次启动时请右键点击 →“打开”确认一次。通过 `packaging/mac/build_macos.sh`
  构建。
- **下载产物现已包含 AI 抠图。** Linux AppImage 与 macOS `.dmg` 均内置
  `rembg`/`onnxruntime`，因此一键 AI 无需额外安装即可使用（产物体积相应增大）。
- **发布工作流跨平台构建。** `release-linux.yml` 现在除 Linux 的 AppImage 与
  `.deb`（x86_64 + aarch64/树莓派 OS）外，还会为 `vX.Y.Z` 标签生成 macOS
  arm64 `.dmg`，并一起发布所有产物。
- **通过文件关联和命令行打开图像。** `bgremover image.png` 和
  `python -m bgremover image.png` 会在窗口构建完成后，经由与文件对话框、最近文件
  和拖放相同的、经过校验的异步加载路径打开该路径；Linux 桌面条目（`%F`）和 macOS
  `QFileOpenEvent`（Finder「打开方式」、双击）同样会被处理。多个路径时：打开第一个，
  其余在状态栏标注数量后忽略；缺失、不支持或非本地的路径会被受控地拒绝而不是中断
  启动，且在替换已编辑图像前会触发未保存更改的询问。此外，应用退出时正在运行的工作
  线程也会被干净地结束（#249）。
- **图像处理流水线性能基准测试。** `scripts/benchmark.py` 通过真实的
  `image_ops` 路径测量每种输出格式（PNG/JPEG/WebP/TIFF）的处理时间，将带日期的
  结果保存到 `benchmarks/results/`，并比较相邻的运行；退化超过 10% 的格式会被标记，
  并可选地作为 GitHub issue 上报（`make bench` / `make bench-compare`）。
  每周一次的 CI 工作流（`.github/workflows/benchmark.yml`）在固定硬件上运行并比较，
  并将结果提交回仓库作为下一次的基线。
- **强化行为测试。** 扩展了此前覆盖不全路径的行为测试覆盖率（#177、#192）。
- **为 `app.py` 和 `main_window.py` 新增专门的单元测试。** `app.py` 覆盖率
  0% → 100%，`main_window.py` 68% → 100%；整体覆盖率提升至 94%（#214）。

### 变更

- **更新依赖。** `idna` 升级到 3.15，`urllib3` 升级到 2.7.0；
  `LICENSES.md` 已与新的依赖快照同步。
- **固定构建后端以防范供应链 CVE。** `setuptools` 在 `pyproject.toml`
  （`[build-system]`）和 `requirements/constraints.txt` 中升级到 `>=78.1.1`
  （CVE-2024-6345 RCE、CVE-2025-47273 路径遍历），`wheel` 在 `constraints.txt`
  中升级到 `==0.46.2`（CVE-2026-24049）。这样隔离的 wheel 构建就不会再拉取存在
  漏洞的构建工具（#200、#201）。
- **在 CI/开发环境中将 pip 升级到已修复版本。** 使用 pip 安装的 CI 工作流
  （`ci.yml`、`pr-ci.yml`、`ui-nightly.yml`、`benchmark.yml`、`license-check.yml`）
  和 Web SessionStart 钩子在安装前将 `pip` 升级到 `>=26.1.2`，开发安装文档
  （`README.md`/`INSTALL_MAC.md`/`INSTALL_LINUX.md`）同样如此。修复了
  `pip-audit` 报告的路径遍历、符号链接和模块劫持 CVE 批次；pip 本身就是安装
  工具，因此无法通过 `constraints.txt` 固定（#202）。
- **macOS 诊断脚本默认遮蔽敏感路径。** `diagnose_mac.sh` 现在默认将 `$HOME`
  替换为 `~`，缩短其余 `/Users/<name>` 路径，并以路径经过遮蔽的错误摘要取代
  原先输出的日志原文最后 40 行——因此输出可以放心附加到错误报告中。新的
  `--include-raw-logs` 选项提供完整诊断（含原始日志）；新增的 shell 测试
  （`tests/test_diagnose_mac.py`）确保主目录和图片路径不会出现在默认输出
  中（#185）。
- **固定 AppImage 发布依赖。** 一份 `requirements/constraints.txt` 快照为
  AppImage 构建工作流固定了版本（#182、#191）。
- **强化 license 工作流权限。** 该工作流现在以最小权限运行（#183、#193）。
- **移除 `CanvasHistory._redo_max`。** 该只写属性从未被读取；redo 上限仅通过
  `deque(maxlen=…)` 实施（#199、#215）。
- **`import bgremover` 不再加载 Qt 栈。** 包入口（`bgremover/__init__.py`）现在
  仅直接导出轻量元数据（`__version__`、`get_version`）；既有的 GUI/Qt
  re-export（`ImageCanvas`、`MainWindow`、workers …）保持兼容，但通过 PEP 562
  的 `__getattr__` 在首次属性访问时才惰性加载。版本与元数据查询现可在无
  PyQt6 的 headless 环境下工作；一个子进程回归测试确保轻量导入不会把
  `bgremover.canvas`/`main_window` 或 PyQt6 拉入 `sys.modules`（#232）。

### 修复

- **加固 rembg 子进程（健壮性与内存）。** 来自 #283 的 Codex 复审在
  `bgremover/ai_process.py` 中遗留的四项后续问题：在 `new_session()` 发生瞬时
  失败后，rembg 会话会在下一次请求时重新且仅重建一次，而不再退回到
  `remove(..., session=None)` 并在每次调用时重新加载模型（#229 的保证得以保留）；
  空闲的子进程会立即释放最后一个输入 PNG，而不再长期持有；输入和结果 PNG 以原始
  字节帧（`send_bytes`/`recv_bytes`）传输，而非通过管道经 pickle 序列化，从而消除
  大图（最高 40 MP）时的内存峰值与 OOM 风险；并且恰好在进程启动期间到达的
  `request_stop()` 会通过 `_proc_lock`/`_stop_pending` 这一对机制转交给新进程。
  回归测试覆盖了全部四条路径（#285）。
- **缓解受限文件读取中的内存峰值。** 来自 #264 的 Codex 复审在
  `bgremover/image_loading._read_capped` 中遗留的两项后续问题：内容不再用
  `b"".join(chunks)`（它会同时持有各 chunk **和**结果，在接近 512 MiB 上限时约
  1 GiB）拼接，而是组装进一个一次性预分配大小的 `bytearray` 并直接传出——不再有约
  2× 的峰值。此外，第一次 read 受 `os.fstat()` 已知大小的限制，因此小文件不再申请
  约 8 MiB 的余量；一个小的后续 read 仍能检测 `fstat()` 与读取之间的增长（TOCTOU）
  或不可靠的 `st_size`（管道/套接字）。上限/超限检测（`None`）保持不变；回归测试
  覆盖了两条路径（#286）。
- **读入前限制输入文件大小。** `open_validated_image` 现在在将文件内容完整读入
  内存**之前**，先通过 `os.fstat()` 对照一个有文档说明的字节上限
  （`_MAX_INPUT_FILE_BYTES`，512 MB）检查输入文件；额外的有界 `read()` 可防范
  异常的文件对象，以及 `fstat()` 与 `read()` 之间的大小变化（TOCTOU）。提示信息
  会区分文件大小（MB）与百万像素上限（MP）。同步和异步加载路径共用同一检查；
  原有的百万像素上限与 TOCTOU 保护均保持不变（#230）。
- **复用 rembg 推理 session。** warmup 现在通过 `new_session()` 恰好创建一个
  rembg/ONNX session 并在模块级缓存；之后每次 `AIWorker` 都将其传给
  `remove(..., session=...)`，而不是重新初始化模型。该创建通过 double-checked
  locking 保证线程安全，并在多次 AI 调用中最多执行一次；初始化失败仍会通过
  worker 错误信号上报，且不会留下被误判为「就绪」的状态。误导性的注释（声称
  dummy `remove()` 会缓存 session）也一并修正（#229）。
- **`recent_files` 对损坏的设置具有健壮性。** `RecentFiles.paths()` 现在防御性地
  处理任意存储的原始类型：单个字符串仍作为一个条目，列表/元组按元素过滤为非空
  字符串，而其他任何值（如整数、`None`）都会得到空列表而非 `TypeError`。新增的
  `sanitize()` 在启动时将真正损坏的值清理后回写一次（并记录一条警告）；QSettings
  无害的单元素字符串保持不变。因此手动编辑或过时的 `recent_files` 值不再中断菜单
  或应用构建；更新的（未来）schema 同样保持不变，以避免降级时的数据丢失（#233、#240）。
- **rembg 惰性导入的双重检查锁，以及 `open_validated_image` 中的 TOCTOU 防护。**
  两个线程可能同时进入导入（竞态），且文件被打开两次（TOCTOU 窗口）；两者均有
  回归测试覆盖（#174）。
- **丢弃过时的异步图像加载结果。** `MainWindow` 中的单调 `_load_generation`
  计数器可防止迟到的加载回调覆盖更新的图像（类似 AI 过时检查）（#190）。
- **修正 canvas 选区掩码类型标注。** 错误的类型在完整 CI 运行中导致 mypy
  错误（#196、#197）。
- **修复 CI 工作流 YAML。** pip 升级步骤的名称未加引号，导致工作流解析失败
  （#213）。
- **激活的裁剪不再残留于图像状态变更之后。** 现在每次可见的图像变更（旋转、翻转、
  AI 结果、撤销/重做、恢复原图、确认裁剪）都会在 `_set_image_state` 中集中丢弃激活
  的裁剪叠加层与进行中的套索，并恰好发出一次 `cropModeChanged(False)`。因此过时的
  裁剪矩形不再会被应用到新图像，也不会再产生透明的填充像素（#247）。
- **发布工作流仅在 Full CI 门禁通过后才发布。** `release-linux.yml` 现在将权威的
  Full CI 矩阵（`ci.yml`）作为可复用工作流调用，并通过 `needs` 将构建与发布绑定其
  上；独立的 `verify-tag` 作业会在标签不符合 `vX.Y.Z` 或与 `project.version` 不一致
  时失败。AppImage/`.deb` 在上传前会校验文件名、架构、可执行性与 Debian 元数据，且
  `gh release create` 的错误不再被 `|| true` 吞掉（已存在的 release 会被显式复用）。
  这样，来自测试失败或版本不匹配提交的产物不再会进入 release（#250）。
- **空选区会立即释放叠加层 pixmap。** `_refresh_overlay` 现在会**先**检查掩码是否
  为空，再走增量 dirty 路径。当橡皮擦抹除最后一个选中像素时，`_overlay_pixmap` 与
  `QGraphicsPixmapItem` 会立刻清空，而不是把一张整图大小的透明 QPixmap（40 MP 时约
  160 MiB）一直保留到下一次完整重建。部分擦除仍只更新脏矩形（#251）。
- **强化 release 工作流的后续修复。** publish 作业现在设置 `GH_REPO`，使 `gh
  release` 无需 checkout 即可定位到正确的仓库；可复用的 test 作业依赖
  `verify-tag`，因此无效或与版本不匹配的标签不会再启动整个矩阵；并且
  `download-artifact` 通过 `run-id`/`github-token`（配合 `actions: read`）从整个
  run 拉取产物，使「Re-run failed jobs」不再丢失先前尝试的产物。README/RESOURCES
  （含翻译）不再描述已移除的 `release: published` 触发器（#257）。
- **图像加载限制不再预分配 512 MiB，且已本地化。** `open_validated_image` 现在按
  8 MiB 分块读取文件内容（而非 `read(limit + 1)`——在 CPython 的带缓冲读取器上会
  立即预留约 512 MiB，可能使小文件在内存紧张时以 `MemoryError` 失败）；`fstat()`
  与读取之间的增长仍通过 `limit + 1` 检测。大小提示改用翻译键
  `status.file_too_large`（de/en 完整本地化，而非中英/德英混合提示），并将实际值
  向上取整、限值向下取整，使其在「限值 + 1 字节」时明显大于限值（例如「513 MB」
  而最大为「512 MB」，而不是用 `.0f` 把两者都显示为「512 MB」）（#258）。
- **QSettings 模式迁移对降级安全。** 缺失的迁移不再未经检查就把
  `schema_version` 提升到当前值，构建最近文件菜单时也不再回写更高的未来模式
  ——意外降级因此不会丢失任何设置（#234、#259）。
- **Escape 先取消进行中的套索；裁剪后恢复工具光标。** 进行中的多边形套索现在
  会被 Escape 先取消，然后才清除选区（顺序为 裁剪 > 套索 > 选区）。当活动裁剪
  被自动放弃时，`_finish_mode` 会恢复活动工具的光标，而不是保留裁剪光标
  （#248、#260）。
- **Worker 关闭有时间上限。** 应用关闭时，`WorkerController` 现在只在
  `quit()`/`wait()` 上短暂等待，然后回退到 `terminate()` 并再次进行有上限的
  `wait()`；无响应的 worker 不再无限期阻塞关闭，错误路径也会记录日志。原生
  ONNX 工作中 `terminate()` 的实际风险随后已解决：将 rembg/ONNX 推理移入通过
  `spawn` 启动的独立进程（`ai_process`）——AI worker 仅轮询结果且可协作式停止，
  取消和关闭会强制终止推理进程，`terminate()` 不再是 AI 工作的紧急出口（#270，
  #231 的后续）。
- **画笔 overlay 避免每次鼠标移动全量扫描掩码。** `canvas_selection` 增量维护
  选区计数，并使用变更的 bounding box，而不是在每次画笔/橡皮移动时扫描整张
  掩码；`has_selection` 因此为 O(1)。这让大图在快速绘制时保持流畅（#261）。

### 移除

- **移除死代码（#244）。** 删除了从未被调用的 `ImageCanvas._zoom` 方法以及生产中
  未使用的 `WorkerController.launch_worker` 包装器；线程生命周期测试现在走真正使用
  的 `_build_thread` 路径。

## [2.3.0] – 2026-06-04


### 新增

- **测试覆盖率提高到 88%（第二轮，之前为 82%）。** 新增
  `tests/test_canvas_events.py`，覆盖 `canvas.py` 中此前未测的事件处理和控制
  逻辑：鼠标、键盘、滚轮、拖拽、魔棒结果流、工具设置、活动裁剪中的
  undo/redo/undo-to，以及未加载图片时的 guard 路径。`canvas.py` 从 64% 提升到
  99%，`fail_under` 从 80 提升到 86。
- **测试覆盖率提高到 82%（之前为 74%）。** 新的行为测试覆盖
  `tests/test_lasso.py`、`tests/test_canvas_crop.py`、`tests/test_viewport.py`、
  `tests/test_crop_overlay.py`、`tests/test_settings_schema.py` 和
  `tests/test_settings_dialog.py`。多个模块达到 100%，`canvas_crop.py` 达到
  98%，`fail_under` 从 68 提升到 80。
- **ANLEITUNG.md i18n。** 为德语用户指南新增五种译文：
  `docs/i18n/{en,es,fr,uk,zh}/ANLEITUNG.md`；`tests/test_i18n_docs.py` 的
  `DOC_NAMES` 现在包含 `"ANLEITUNG.md"`，每个 i18n 头部也说明
  `ANLEITUNG.pdf` 只从德语原文生成。
- **Soft-drift 测试 `tests/test_i18n_sync.py`。** 将 `CHANGELOG.md`、
  `INSTALL_MAC.md` 和 `INSTALL_LINUX.md` 的标题层级与代码块数量同德语原文
  对比；差异会生成可读警告，而不是让 CI 硬失败。
- **`bgremover/status_messages.py` – 集中 status 消息。** 将 `canvas.py`、
  `canvas_crop.py` 和 `main_window.py` 中用户可见的 status 字符串移入
  `StatusMessages`，作为未来本地化的准备。
- **支持英语的 runtime i18n。** 德语和英语可在运行时切换；设置对话框包含
  持久化语言选择器和重启提示，canvas、对话框和右侧面板的 UI 字符串通过
  集中翻译层处理。
- **工具键盘快捷键。** 编辑工具现在可以通过键盘切换；toolbar tooltip 和文档会列出
  各平台对应的快捷键。
- **Linux AppImage 打包。** release build 现在会生成 AppImage，作为 Linux
  最终用户的推荐路径，并包含打包脚本、CI 覆盖和安装说明。
- **Linux `.deb`、aarch64/Raspberry Pi 与 release workflow。** Linux 打包扩展了
  Debian 包、aarch64/Pi 支持以及对应的 release workflow。
- **引入 QSettings schema version。** 新增 `bgremover/settings_schema.py`，包含
  `SCHEMA_VERSION = 1` 和 `migrate(settings)`；`MainWindow.__init__` 在创建
  `QSettings` 后立即执行迁移。覆盖 downgrade 保护、损坏值和
  `tests/test_settings_schema.py` 中的相关测试。
- **`RembgWarmupWorker` runtime 测试。** `tests/test_workers.py` 与
  `tests/test_worker_controller.py` 新增测试，验证 warmup 总会发出 `finished`，
  且即使 `rembg_remove` 首次启动失败，thread lifecycle 也能完成。

### 变更

- 清理了文档和代码注释：从活文档中移除过时的 PR/轮次标记，更新
  macOS 安装说明，并将建议文档压缩为当前 review/roadmap 状态。
- 项目版本在包元数据、AppStream、许可证概览和 changelog 链接中提升
  到 2.3.0。

- **统一 docstring 语言。** `bgremover/image_ops.py`、
  `bgremover/recent_files.py` 和 `bgremover/worker_controller.py` 的 docstring
  从英文改为德文，与项目其他部分保持一致。
- **更新 Linux 包和语言设置的用户文档。** README、`INSTALL_LINUX.md` 和
  `ANLEITUNG.md` 现在将 AppImage/`.deb` 作为 Linux 最终用户的推荐路径，
  并记录持久化语言设置及重启提示；i18n 副本同步更新。
- **代码卫生汇总轮。** version fallback 读取 `pyproject.toml`，
  `_paint_brush` 显式接收 `additive`，`apply_remove`/`apply_replace` 只捕获
  预期错误，补充全局副作用与 QSettings 特例说明，`make clean` 清理更多
  构建产物，项目描述反映 macOS/Linux 支持。
- **魔棒选区不再冻结 UI。** Flood-fill 移入短生命周期 `QThread` 上的
  `FloodFillWorker`，并通过 `content_revision` 做 stale 检查；pan/zoom 保持
  响应，只有并行魔棒点击会用 status 消息阻止。
- **扩展 CI 测试矩阵。** Full CI 现在在 Ubuntu 和 macOS 上检查 Python 3.10、
  3.11、3.12 和 3.13。
- **`RembgWarmupWorker` 继承 `_Worker`。** 公共 boilerplate 移入基类并加入
  `_always_finished()` hook，保留 `finished` 合约，同时统一 logging、错误语义和
  `WorkerController` 类型注解。
- **Canvas 子模块使用公共 edit API。** `CanvasCrop` 和 `CanvasTransform` 使用
  `apply_edit(...)` 与 `ImageCanvas.current_tool`；多项 selection 操作改用
  `_requires_image`，空状态会一致地提示未加载图片。
- **精简包的公共 API。** 私有符号不再从 `bgremover` 顶层 re-export；需要这些
  符号的代码应从子模块导入。`logger`、`LOG_FILENAME`、`REMBG_AVAILABLE` 和
  `current_log_file` 保持公共；测试边缘 `MainWindow._recent_paths()` 被移除。

### 修复

- **`apply_remove`/`apply_replace` 不再吞掉真实 bug。** 窄过滤器会让
  `AttributeError`、`AssertionError` 等继续向上传播，同时仍把预期的 image/IO
  错误转为 status 消息。
- **同步加载路径使用与 worker 相同的保护。** `ImageCanvas.load_image` 现在调用
  `open_validated_image`，因此 drag & drop 中的恶意文件和不支持格式也会以干净的
  status 消息结束。
- **稳定 License Check。** `coverage` 固定在 `requirements/constraints.txt`
  (`==7.14.0`)，避免上游 release 造成 `LICENSES.md` drift 比较失败。
- **License Check 加强 timezone drift 防护。** `actions/checkout` 使用
  `fetch-depth: 0`，日期计算使用 `TZ=UTC` 和 `--date=short-local`，从而找到真实
  edit commit 并确定性地格式化日期。

### 移除

- **移除 Canvas、Lasso 和 MainWindow 中的死代码。** 删除 `ImageCanvas._version`、
  `CanvasLasso.close_to_mask` 和 `MainWindow._btn_grp`。

## [2.2.0] – 2026-05-25

### 新增

- **可复现的依赖 snapshot**（`requirements/constraints.txt`）。
  Makefile、license workflow 和 macOS App 构建会使用同一份已提交的
  constraints，用于测试、CI、license 和 App Bundle 安装。
- **本地测试环境 doctor**（`make doctor`、
  `scripts/check_test_env.py`）。在本地运行深入 pytest 后才失败之前，
  先检查 Python 版本、`[test]` 依赖、非 editable 包安装、
  `bgremover` console script 以及 Qt `offscreen`。
- **应用启动的 CI 冒烟测试**（`tests/test_app_smoke.py`）。现有的 UI
  测试通过 `-m 'not ui'` 被排除在 CI 之外，因此 CI 从未检查应用是否
  能够完整启动——正是这个缺口让 macOS 启动故障溜了过去。新增测试不带
  `ui` 标记（因此会在 CI 中运行）：`python -m bgremover` 和
  console-script `bgremover` 从一个中性的工作目录完整启动（新的自检
  钩子 `BGREMOVER_SMOKE_TEST` 在第一个事件循环周期后以退出码 0
  结束）；检查 Qt 插件配置产出有效路径；
  对启动脚本（`create_BgRemover_app.sh`、`BgRemover.command`、
  `diagnose_mac.sh`）以及打包进 App 包的启动器进行 shell 语法检查。
  为此在 Linux CI job 中安装 `zsh`。

### 变更

- **继续模块化 MainWindow。** “最近打开”的持久化和菜单语义现在位于
  `bgremover/recent_files.py`；`MainWindow` 只负责委托加载、状态消息和
  文件菜单集成。
- **从 `MainWindow` 中抽出菜单/action 构建。**
  `bgremover/menu_actions.py` 负责菜单栏、`QAction`、快捷键和最近文件
  子菜单；`MainWindow` 只传入领域回调。
- **从 `MainWindow` 中抽出右侧标签面板。**
  `bgremover/right_panel.py` 负责选择、背景、变换和形状标签页，
  包括滑块、spinbox 和面板按钮；`MainWindow` 只传入画布回调。
- **从 `MainWindow` 中封装 worker 编排。**
  `bgremover/worker_controller.py` 现在负责加载、AI 和 warmup 线程，
  包括强 worker 引用、`deleteLater` 连接和统一 shutdown。

### 修复

- **将 release/changelog 链接修正为真实存在的 ref。** `[Unreleased]`
  现在从 `v2.1.0` 开始比较；由于仓库中没有历史 `v2.0.0` 标签，
  `[2.1.0]` 使用已记录的 2.0.0 release commit 作为比较基点。
- **App 包：setup 中的 `bgremover` 检测不再依赖工作目录。**
  `create_BgRemover_app.sh` 把 venv 判定为「就绪」，尽管 `bgremover`
  并未安装在其中：`has_deps` 检查在项目目录下以该 `cwd` 运行，而
  Python 会自动把当前目录加到 `sys.path[0]` —— 于是
  `import bgremover` 找到的是仓库的 `bgremover/` **源码目录**，而非
  venv 中的真正安装。App 启动器以不同的 `cwd` 启动，看不到该源码
  目录，因此报告「venv 中缺少 bgremover 包」。`has_deps` 与最终
  完整性检查现在都从 `$HOME` 运行（子 shell `cd "$HOME"`），因而与
  启动器检查的是同一现实；若包缺失，则触发 pip 安装快速路径。
  `diagnose_mac.sh` 同样从 `$HOME` 测试，并额外显示 App venv 的
  `pip show bgremover`（与 cwd 无关地证明包是否/安装到何处）。
- **macOS 启动路径恢复可用。** 在包切分（第 5 轮）之后，
  `BgRemover.command` 仍在寻找已不存在的 `BgRemover.py` 并以「未
  找到」中止；德语版 `INSTALL_MAC.md` 以及 `INSTALL_LINUX.md` 和
  `README.md` 的 i18n 版本也仍保留了部分旧命令（第 5 轮的步骤
  15 在 glob 中漏掉了德语 `INSTALL_MAC.md` 以及 i18n 安装文档，
  并且 i18n 的 `.desktop` 片段里还遗留有
  `Exec=python3 /路径/.../BgRemover.py`）。后果：在 macOS 上三条
  已记录的启动路径（App 包、双击 `.command`、终端）没有一条能
  可靠使用。`BgRemover.command` 现在通过 `python3 -m bgremover`
  启动，并预先检查 `import bgremover`（否则会输出指向
  `create_BgRemover_app.sh` 的明确提示）。INSTALL_MAC 及所有
  i18n 文档反映当前的包模型（包括把包以非 editable 方式安装到
  App venv，以及通过 `importlib.resources` 解析资源）。
- **`create_BgRemover_app.sh`：现有 venv 可被干净迁移。** 来自单体
  时代的 venv（已安装 PyQt6/Pillow/numpy，但显然还没有 `bgremover`）
  会被错误地视为「ready」，因为 setup 检查 `has_deps` 没有测试
  `bgremover`。重新运行时，包安装因此被跳过——随后应用启动器在运行
  时报告「venv 中缺少 bgremover 包」。该检查现在也包括
  `import bgremover`；此外还有快速路径：若 App venv 已具备
  PyQt6/Pillow/numpy，则仅追加 `pip install ".[ai]"`（数秒），而
  不必带着所有依赖重新构建 venv（数分钟）。

### 更改

- **从 `ImageCanvas` 中提取纯图像操作。** `bgremover/image_ops.py`
  现在以不依赖 Qt 的 PIL/NumPy 函数承载背景移除/替换、保存、旋转、
  翻转、圆角和 crop mask。`ImageCanvas` 继续负责 UI 状态、undo/redo、
  signals 与 overlays；`tests/test_image_ops.py` 会在没有
  `QApplication` 的情况下直接检查像素操作。
- **Recommendations 文档更新到当前状态。** `RECOMMENDATIONS.md` 及其
  i18n 版本现在包含第 6 轮状态块，记录最近的 PR 系列（#70、#72–#78），
  并明确说明旧的单体分析属于历史上下文。
  `tests/test_recommendations_docs.py` 会保护该状态块。
- **同步资源文档。** `RESOURCES.md` 及其 i18n 版本现在反映包布局
  （`bgremover/` 而非 `BgRemover.py`）、`bgremover/icons/` 下的
  package data、可复现 constraints snapshot，以及 PR/full/license
  workflows。新增静态测试防止这些引用再次过期。
- **`make pr-check` 让本地 PR 检查更稳健。** 该 target 会重新安装带
  `[test]` 的包，运行 doctor，然后启动 `ruff`、`mypy` 和 `pytest`。
  Makefile 会自动找到 `.venv/bin/python`，否则回退到
  `python`/`python3`；GitHub PR CI 和 Full CI 使用同一个 target。
  共享的 Qt 插件配置会在需要时把 platform plugins 暂存到系统临时目录，
  避免 macOS 本地 headless 运行因项目路径中的 Qt 插件列表问题而失败。
- **新增轻量级 PR CI，并同步测试文档。** Pull Request 现在会运行低成本的
  Ubuntu/Python 3.12 workflow（`make pr-check`）；完整的 Linux/macOS
  矩阵保留给 release 和手动运行。测试 workflow 使用非 editable 安装，
  让 app smoke test 从外部 `cwd` 检查真实安装后的包。`README`、
  i18n README、`TESTING.md` 和 `Makefile` 现在描述同一套流程。
- **单体 → 包（第 5 轮）。** 单文件 `BgRemover.py`（3026 行）已拆分为
  可安装包 `bgremover/`（14 个模块：`constants`、`image_utils`、
  `icons`、`theme`、`workers`、`crop`、`canvas`、`widgets`、
  `settings_dialog`、`logging_config`、`main_window`、`app`、
  `__main__`、`__init__`）。通过 `python -m bgremover` 或
  console-script `bgremover` 启动；旧的 `python BgRemover.py` 形式被
  无替代地移除。`BgRemover.py` 已删除。以 **13 个机械步骤**完成，每一
  步都以绿色测试 oracle 为闸门（140 unit + 16 UI 测试、ruff、mypy）。
  唯一有意的、行为中立的代码变更：`make_tool_icon` 现在通过
  `importlib.resources` 从包数据（`bgremover/icons/`）解析图标，取代
  `__file__`/`sys.argv`/`cwd` —— 契约不变。`pyproject.toml`、
  `Makefile`、CI workflow 与 macOS 构建脚本
  （`create_BgRemover_app.sh`）在同一次切分中同步跟进；venv 以非
  editable 模式安装本包（含 package-data），因而应用不依赖项目目录。
- `BgRemover.py` 中的过渡再导出（B 阶段）与测试中所有的 `BgRemover`
  导入在最后一步被切换到包上。

## [2.1.0] – 2026-05-19

### 已更改

- 将五个 `ImageCanvas` 方法（`apply_round_corners`、`apply_rotate`、
  `apply_flip`、`start_crop_circle`、`start_crop_ratio`）的“未加载
  图像”提前返回守卫合并到装饰器 `@_requires_image` 中——此前逐字节
  相同的代码块消失；行为不变（由现有测试套件保护）。
- 后台 worker `AIWorker` 和 `ImageLoadWorker` 现共用基类 `_Worker`，
  封装相同的 `try/except → logger.exception → error.emit` 流程；
  子类仅实现 `_work()`。`RembgWarmupWorker` 有意保持独立（无 `error`
  信号，`finished` 始终在 `finally` 中）。
- 版本切割 **2.1.0**：`pyproject.toml` 和 `BgRemover.py` 中的
  `__version__` 回退提升至 `2.1.0`；此前归集在 `[Unreleased]` 下的
  更改（#48/#52/#53、INSTALL_LINUX、第 3/4 轮）由此标注为 2.1.0。

### 移除

- 删除了未再使用的 stylesheet 常量 `BTN_STYLE` 和 `GRP_STYLE`。

### 修复

- `save_image()` 现在会将 I/O 失败报告为状态消息，而不是让其未处理地
  继续传播。

### 文档

- 补充了 Linux 安装说明（`INSTALL_LINUX.md`）：
  各发行版的系统软件包（apt/dnf/pacman）、venv 设置、
  启动脚本或 `.desktop` 条目以及故障排除；并在 README 中
  链接。包括针对 Raspberry Pi OS（桌面版）的尤其简单的方式，
  无需 venv/pip（PyQt6/Pillow/numpy 作为系统软件包通过 `apt` 安装），并附带
  可选的 AI 加装步骤。

## [2.0.0] – 2026-05-17

首个已记录的 2.0.0 release 状态。仓库中没有历史 `v2.0.0` Git 标签。

### 功能

- 通过 `rembg` 实现 AI 背景移除（可选的 `ai` extra），含
  后台预热，使首次点击不被阻塞。
- 选区工具：魔棒（带容差滑块的向量化 Flood-Fill）、
  画笔、橡皮擦和多边形套索；Shift/Ctrl
  用于加选或减选。
- 将背景设为透明或用颜色替换。
- 变换：旋转（90° 步长和任意角度）、镜像翻转、
  圆角处理、带三分法网格的多种比例裁剪。
- 带撤销/重做的历史记录（工具栏按钮），并可通过
  浮动历史弹窗跳转到任意此前的步骤。
- 拖放以及“最近打开”（10 个条目），两者均通过
  异步加载 Worker——不会冻结 UI。
- 保存为 PNG、JPEG、WebP 或 TIFF。
- 通过 `QSettings` 持久化设置（默认目录、首选
  文件格式）。
- macOS 应用程序包构建（`create_BgRemover_app.sh`），含隔离的
  venv、Apple Silicon 处理和图标设置；支持 Python
  3.10–3.15。

### 稳定性与质量

- 加固了 Worker 线程（Worker 不会过早被 GC，
  在 `closeEvent` 中干净地关闭线程，AI 竞态通过单调的
  画布版本计数器处理）。
- 加载时的图像尺寸限制（40 MP）和解压缩炸弹防护。
- 内存受限的撤销栈（256 MB），带 O(1) 字节跟踪。
- 与平台无关的日志路径（应用数据目录中的 `bgremover.log`）。
- 108 项测试；`ruff` 和 `mypy` 作为 CI 步骤；CI 在 Ubuntu 和 macOS 上
  以 Python 3.10 和 3.12 运行。
- `__version__` 从包元数据中读取（单一来源）；
  版本号显示在窗口标题中。

### 文档与许可证

- 许可证 **GPL-3.0-or-later**（`LICENSE`）；这是由
  采用 GPL 许可的 PyQt6 绑定决定的。
- `RESOURCES.md`（所有库/工具/资源及许可证）、
  `LICENSES.md` 以及自动化的许可证/合规工作流。
- 带有架构、已知限制和安装
  说明的 README；详细的 `INSTALL_MAC.md`。

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/v2.6.0...HEAD
[2.6.0]: https://github.com/NikolayDA/picture_helper/compare/v2.5.0...v2.6.0
[2.5.0]: https://github.com/NikolayDA/picture_helper/compare/v2.4.1...v2.5.0
[2.4.1]: https://github.com/NikolayDA/picture_helper/compare/v2.4.0...v2.4.1
[2.4.0]: https://github.com/NikolayDA/picture_helper/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/NikolayDA/picture_helper/compare/79f61c5514f283fae31ce9d21f31786a3acfbe16...v2.3.0
[2.2.0]: https://github.com/NikolayDA/picture_helper/compare/666d4a3932f70eabaafde8de4bfc2a0574be5d16...79f61c5514f283fae31ce9d21f31786a3acfbe16
[2.1.0]: https://github.com/NikolayDA/picture_helper/compare/d80067dbc064a8eab5774457eaaffab733c4cab6...666d4a3932f70eabaafde8de4bfc2a0574be5d16
[2.0.0]: https://github.com/NikolayDA/picture_helper/tree/d80067dbc064a8eab5774457eaaffab733c4cab6
