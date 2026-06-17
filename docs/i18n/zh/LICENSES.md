[Deutsch](../../../LICENSES.md) · [English](../en/LICENSES.md) · [Español](../es/LICENSES.md) · [Français](../fr/LICENSES.md) · [Українська](../uk/LICENSES.md) · **简体中文**

# 许可证与法律概览 – bgremover 2.4.1

> 自动生成 – **纯粹是对许可条款的技术性评估，并非法律意见。**
> 截至：2026-06-17 · 项目自身许可证：`GPL-3.0-or-later` · 已分析 45 个依赖。

## 总体评估 – 商业可用性

整体作品中最强的相关许可证：**强 copyleft**。

- **商业用途：** 允许 – GPL 并不禁止销售。可以就分发、支持或服务收取费用。
- **条件：** 所分发的整体作品受 `GPL-3.0-or-later` 约束。每次再分发（包括销售）都必须在 GPL 下随附或书面提供完整、对应的**源代码**；必须附上 GPL 许可证文本和所有版权声明；不得附加任何额外的使用限制。
- **发布/销售时的义务：** 在 GPL 下公开整体作品的源代码，随附 GPL 文本以及所有（包括宽松许可）依赖的版权/许可证声明，并附上免责声明。**专有/闭源**交付是**不**可能的。
- **LGPL/Qt 特殊说明：** Qt（PyQt6-Qt6）为 LGPL-v3；此处PyQt6 在 GPL-3.0 下使用。由于整体作品本就是 GPL，LGPL 的可替换义务已由源代码公开所涵盖。

## 关于潜在许可证冲突的说明

- 未检测到许可证冲突：所有依赖许可证（宽松、MPL-2.0、LGPL-v3）均与 GPL-3.0 兼容，可在 GPL-3.0 下再分发。
- PyQt6 为 `GPL-3.0-only`。与项目许可证 `GPL-3.0-or-later` 兼容 – 整体作品实际上应在 GPL-3.0 下分发。
- PyQt6/Qt 采用双重许可（GPL **或** 商业 Riverbank/Qt 许可证）。只要项目保持 GPL，即适用 GPL 变体；专有产品则需要付费的 PyQt6/Qt 许可证。

## 许可证分布

| 类别 | 数量 | 软件包 |
|---|---|---|
| 强 copyleft | 1 | PyQt6 |
| 弱 copyleft（库） | 1 | PyQt6-Qt6 |
| 弱 copyleft（文件） | 3 | certifi, pathspec, tqdm |
| 宽松 | 40 | ImageIO, PyMatting, PyQt6_sip, Pygments, ast_serialize, attrs, charset-normalizer, coverage, flatbuffers, idna, iniconfig, jsonschema, jsonschema-specifications, lazy-loader, librt, llvmlite, mypy, mypy_extensions, networkx, numba, numpy, onnxruntime, packaging, pillow, platformdirs, pluggy, pooch, protobuf, pytest, pytest-qt, referencing, rembg, requests, rpds-py, ruff, scikit-image, scipy, tifffile, typing_extensions, urllib3 |

## 依赖详情

| 软件包 | 版本 | 许可证 | 类别 | 评估 |
|---|---|---|---|---|
| ast_serialize | 0.5.0 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| attrs | 26.1.0 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| certifi | 2026.2.25 | `Mozilla Public License 2.0 (MPL 2.0)` | 弱 copyleft（文件） | 弱的、文件级 copyleft。允许商业用途；仅对 MPL 许可文件本身的修改必须再次以 MPL 公开。与 GPL-3.0 兼容。 |
| charset-normalizer | 3.4.6 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| coverage | 7.14.0 | `Apache-2.0` | 宽松 | 带有明确专利授权的宽松许可证。允许商业和专有用途；必须保留许可证/版权声明和变更说明（NOTICE）。 |
| flatbuffers | 25.12.19 | `Apache Software License` | 宽松 | 带有明确专利授权的宽松许可证。允许商业和专有用途；必须保留许可证/版权声明和变更说明（NOTICE）。 |
| idna | 3.15 | `BSD-3-Clause` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| ImageIO | 2.37.3 | `BSD-2-Clause` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| iniconfig | 2.3.0 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| jsonschema | 4.26.0 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| jsonschema-specifications | 2025.9.1 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| lazy-loader | 0.5 | `BSD-3-Clause` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| librt | 0.11.0 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| llvmlite | 0.47.0 | `BSD-2-Clause AND Apache-2.0 WITH LLVM-exception` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| mypy | 2.1.0 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| mypy_extensions | 1.1.0 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| networkx | 3.6.1 | `BSD-3-Clause` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| numba | 0.65.1 | `BSD License` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| numpy | 2.4.5 | `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| onnxruntime | 1.26.0 | `MIT License` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| packaging | 24.0 | `Apache Software License; BSD License` | 宽松 | 带有明确专利授权的宽松许可证。允许商业和专有用途；必须保留许可证/版权声明和变更说明（NOTICE）。 |
| pathspec | 1.1.1 | `Mozilla Public License 2.0 (MPL 2.0)` | 弱 copyleft（文件） | 弱的、文件级 copyleft。允许商业用途；仅对 MPL 许可文件本身的修改必须再次以 MPL 公开。与 GPL-3.0 兼容。 |
| pillow | 12.2.0 | `MIT-CMU` | 宽松 | 宽松的 HPND/MIT-CMU 许可证（Pillow）。允许商业和专有用途；保留版权和许可证声明。 |
| platformdirs | 4.9.6 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| pluggy | 1.6.0 | `MIT License` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| pooch | 1.9.0 | `BSD-3-Clause` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| protobuf | 7.34.1 | `3-Clause BSD License` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| Pygments | 2.20.0 | `BSD-2-Clause` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| PyMatting | 1.1.15 | `MIT License` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| PyQt6 | 6.11.0 | `GPL-3.0-only` | 强 copyleft | 强 copyleft。整体作品的任何再分发都必须以 GPL 下的完整源代码形式进行；不允许专有（闭源）再分发。 |
| PyQt6-Qt6 | 6.11.1 | `LGPL v3` | 弱 copyleft（库） | 面向库的弱 copyleft。允许商业用途；最终用户必须能够替换该库（动态链接或可重新链接）。与 GPL-3.0 兼容。 |
| PyQt6_sip | 13.11.1 | `BSD-2-Clause` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| pytest | 9.0.3 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| pytest-qt | 4.5.0 | `MIT License` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| referencing | 0.37.0 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| rembg | 2.0.75 | `MIT License` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| requests | 2.33.1 | `Apache Software License` | 宽松 | 带有明确专利授权的宽松许可证。允许商业和专有用途；必须保留许可证/版权声明和变更说明（NOTICE）。 |
| rpds-py | 0.30.0 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| ruff | 0.15.13 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |
| scikit-image | 0.26.0 | `BSD License` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| scipy | 1.17.1 | `BSD License` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| tifffile | 2026.3.3 | `BSD-3-Clause` | 宽松 | 宽松许可证（BSD 系列）。允许商业和专有用途；必须随附版权/许可证声明，未经同意不得使用作者姓名进行宣传。 |
| tqdm | 4.67.3 | `MPL-2.0 AND MIT` | 弱 copyleft（文件） | 弱的、文件级 copyleft。允许商业用途；仅对 MPL 许可文件本身的修改必须再次以 MPL 公开。与 GPL-3.0 兼容。 |
| typing_extensions | 4.15.0 | `PSF-2.0` | 宽松 | 宽松的 Python 软件基金会许可证。允许商业和专有用途；保留许可证和版权声明。 |
| urllib3 | 2.7.0 | `MIT` | 宽松 | 宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和再分发，包括商业用途和在专有产品中使用。 |

## 来源 / 项目页面

- **ast_serialize** – https://github.com/mypyc/ast_serialize
- **certifi** – https://github.com/certifi/python-certifi
- **coverage** – https://github.com/coveragepy/coveragepy
- **flatbuffers** – https://google.github.io/flatbuffers/
- **idna** – https://github.com/kjd/idna
- **ImageIO** – https://github.com/imageio/imageio
- **iniconfig** – https://github.com/pytest-dev/iniconfig
- **jsonschema** – https://github.com/python-jsonschema/jsonschema
- **jsonschema-specifications** – https://github.com/python-jsonschema/jsonschema-specifications
- **lazy-loader** – https://github.com/scientific-python/lazy-loader
- **librt** – https://github.com/mypyc/librt
- **llvmlite** – http://llvmlite.readthedocs.io
- **mypy** – https://www.mypy-lang.org/
- **mypy_extensions** – https://github.com/python/mypy_extensions
- **networkx** – https://networkx.org/
- **numba** – https://numba.pydata.org
- **numpy** – https://numpy.org
- **onnxruntime** – https://onnxruntime.ai
- **packaging** – https://github.com/pypa/packaging
- **pillow** – https://python-pillow.github.io
- **platformdirs** – https://github.com/tox-dev/platformdirs
- **protobuf** – https://developers.google.com/protocol-buffers/
- **Pygments** – https://pygments.org
- **PyMatting** – https://pymatting.github.io
- **PyQt6** – https://www.riverbankcomputing.com/software/pyqt/
- **PyQt6-Qt6** – https://www.riverbankcomputing.com/software/pyqt/
- **PyQt6_sip** – https://github.com/Python-SIP/sip
- **pytest** – https://docs.pytest.org/en/latest/
- **pytest-qt** – http://github.com/pytest-dev/pytest-qt
- **referencing** – https://github.com/python-jsonschema/referencing
- **rembg** – https://github.com/danielgatis/rembg
- **requests** – https://github.com/psf/requests
- **rpds-py** – https://github.com/crate-py/rpds
- **ruff** – https://docs.astral.sh/ruff
- **scikit-image** – https://scikit-image.org
- **scipy** – https://scipy.org/
- **tifffile** – https://www.cgohlke.com
- **tqdm** – https://tqdm.github.io
- **typing_extensions** – https://github.com/python/typing_extensions

---
_由 `scripts/generate_license_report.py` 生成。依赖集合的更改会在 CI 工作流中自动更新此报告。_
