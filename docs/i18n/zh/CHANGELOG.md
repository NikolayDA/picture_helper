[Deutsch](../../../CHANGELOG.md) · [English](../en/CHANGELOG.md) · [Español](../es/CHANGELOG.md) · [Français](../fr/CHANGELOG.md) · [Українська](../uk/CHANGELOG.md) · **简体中文**

# Changelog

BgRemover 的所有值得注意的变更都记录在本文件中。
其格式参照
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/)；本项目
遵循[语义化版本](https://semver.org/lang/de/)。

## [Unreleased]（未发布）

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

### 文档

- 补充了 Linux 安装说明（`INSTALL_LINUX.md`）：
  各发行版的系统软件包（apt/dnf/pacman）、venv 设置、
  启动脚本或 `.desktop` 条目以及故障排除；并在 README 中
  链接。包括针对 Raspberry Pi OS（桌面版）的尤其简单的方式，
  无需 venv/pip（PyQt6/Pillow/numpy 作为系统软件包通过 `apt` 安装），并附带
  可选的 AI 加装步骤。

## [2.0.0] – 2026-05-17

首个公开打标签的版本。

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

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/NikolayDA/picture_helper/releases/tag/v2.0.0
