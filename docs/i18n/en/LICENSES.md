[Deutsch](../../../LICENSES.md) · **English** · [Español](../es/LICENSES.md) · [Français](../fr/LICENSES.md) · [Українська](../uk/LICENSES.md) · [简体中文](../zh/LICENSES.md)

# License & Legal Overview – bgremover 2.4.0

> Automatically generated – **a purely technical assessment of the license terms, not legal advice.**
> As of: 2026-06-16 · Project's own license: `GPL-3.0-or-later` · 45 dependencies analyzed.

## Overall Assessment – Commercial Usability

Strongest relevant license in the combined work: **Strong copyleft**.

- **Commercial use:** Permitted – the GPL does not prohibit selling. Money may be charged for distribution, support or services.
- **Conditions:** The distributed combined work is governed by `GPL-3.0-or-later`. On every redistribution (including sale) the complete, corresponding **source code** must be shipped or offered in writing under the GPL; the GPL license text and all copyright notices must be included; no additional usage restrictions may be added.
- **Obligations on publication/sale:** Disclose the source of the combined work under the GPL, include the GPL text and the copyright/license notices of all (including permissive) dependencies, and the warranty disclaimer. A **proprietary/closed-source** delivery is **not** possible.
- **LGPL/Qt specifics:** Qt (PyQt6-Qt6) is LGPL-v3; PyQt6 is used here under GPL-3.0. Since the combined work is GPL anyway, the LGPL replacement obligations are covered by the source disclosure.

## Notes on Potential License Conflicts

- No license conflict detected: all dependency licenses (permissive, MPL-2.0, LGPL-v3) are compatible with GPL-3.0 and can be redistributed under GPL-3.0.
- PyQt6 is `GPL-3.0-only`. Compatible with the project license `GPL-3.0-or-later` – the combined work is effectively to be distributed under GPL-3.0.
- PyQt6/Qt are dual licensed (GPL **or** a commercial Riverbank/Qt license). As long as the project stays GPL, the GPL variant applies; a proprietary product would require paid PyQt6/Qt licenses.

## License Distribution

| Category | Count | Packages |
|---|---|---|
| Strong copyleft | 1 | PyQt6 |
| Weak copyleft (library) | 1 | PyQt6-Qt6 |
| Weak copyleft (file) | 3 | certifi, pathspec, tqdm |
| Permissive | 40 | ImageIO, PyMatting, PyQt6_sip, Pygments, ast_serialize, attrs, charset-normalizer, coverage, flatbuffers, idna, iniconfig, jsonschema, jsonschema-specifications, lazy-loader, librt, llvmlite, mypy, mypy_extensions, networkx, numba, numpy, onnxruntime, packaging, pillow, platformdirs, pluggy, pooch, protobuf, pytest, pytest-qt, referencing, rembg, requests, rpds-py, ruff, scikit-image, scipy, tifffile, typing_extensions, urllib3 |

## Dependencies in Detail

| Package | Version | License | Category | Assessment |
|---|---|---|---|---|
| ast_serialize | 0.5.0 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| attrs | 26.1.0 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| certifi | 2026.2.25 | `Mozilla Public License 2.0 (MPL 2.0)` | Weak copyleft (file) | Weak, file-level copyleft. Commercial use is allowed; only changes to the MPL-licensed files themselves must be disclosed again under the MPL. Compatible with GPL-3.0. |
| charset-normalizer | 3.4.6 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| coverage | 7.14.0 | `Apache-2.0` | Permissive | Permissive license with an explicit patent grant. Commercial and proprietary use is allowed; the license/copyright notice and change notes (NOTICE) must be retained. |
| flatbuffers | 25.12.19 | `Apache Software License` | Permissive | Permissive license with an explicit patent grant. Commercial and proprietary use is allowed; the license/copyright notice and change notes (NOTICE) must be retained. |
| idna | 3.15 | `BSD-3-Clause` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| ImageIO | 2.37.3 | `BSD-2-Clause` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| iniconfig | 2.3.0 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| jsonschema | 4.26.0 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| jsonschema-specifications | 2025.9.1 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| lazy-loader | 0.5 | `BSD-3-Clause` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| librt | 0.11.0 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| llvmlite | 0.47.0 | `BSD-2-Clause AND Apache-2.0 WITH LLVM-exception` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| mypy | 2.1.0 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| mypy_extensions | 1.1.0 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| networkx | 3.6.1 | `BSD-3-Clause` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| numba | 0.65.1 | `BSD License` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| numpy | 2.4.5 | `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| onnxruntime | 1.26.0 | `MIT License` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| packaging | 24.0 | `Apache Software License; BSD License` | Permissive | Permissive license with an explicit patent grant. Commercial and proprietary use is allowed; the license/copyright notice and change notes (NOTICE) must be retained. |
| pathspec | 1.1.1 | `Mozilla Public License 2.0 (MPL 2.0)` | Weak copyleft (file) | Weak, file-level copyleft. Commercial use is allowed; only changes to the MPL-licensed files themselves must be disclosed again under the MPL. Compatible with GPL-3.0. |
| pillow | 12.2.0 | `MIT-CMU` | Permissive | Permissive HPND/MIT-CMU license (Pillow). Commercial and proprietary use is allowed; keep the copyright and license notice. |
| platformdirs | 4.9.6 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| pluggy | 1.6.0 | `MIT License` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| pooch | 1.9.0 | `BSD-3-Clause` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| protobuf | 7.34.1 | `3-Clause BSD License` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| Pygments | 2.20.0 | `BSD-2-Clause` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| PyMatting | 1.1.15 | `MIT License` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| PyQt6 | 6.11.0 | `GPL-3.0-only` | Strong copyleft | Strong copyleft. Any redistribution of the combined work must be provided as complete source code under the GPL; proprietary (closed-source) redistribution is excluded. |
| PyQt6-Qt6 | 6.11.1 | `LGPL v3` | Weak copyleft (library) | Weak copyleft for libraries. Commercial use is allowed; the end user must be able to replace the library (dynamic linking or a re-link option). Compatible with GPL-3.0. |
| PyQt6_sip | 13.11.1 | `BSD-2-Clause` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| pytest | 9.0.3 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| pytest-qt | 4.5.0 | `MIT License` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| referencing | 0.37.0 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| rembg | 2.0.75 | `MIT License` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| requests | 2.33.1 | `Apache Software License` | Permissive | Permissive license with an explicit patent grant. Commercial and proprietary use is allowed; the license/copyright notice and change notes (NOTICE) must be retained. |
| rpds-py | 0.30.0 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| ruff | 0.15.13 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |
| scikit-image | 0.26.0 | `BSD License` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| scipy | 1.17.1 | `BSD License` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| tifffile | 2026.3.3 | `BSD-3-Clause` | Permissive | Permissive license (BSD family). Commercial and proprietary use is allowed; the copyright/license notice must be shipped along, and the authors' names may not be used for promotion without consent. |
| tqdm | 4.67.3 | `MPL-2.0 AND MIT` | Weak copyleft (file) | Weak, file-level copyleft. Commercial use is allowed; only changes to the MPL-licensed files themselves must be disclosed again under the MPL. Compatible with GPL-3.0. |
| typing_extensions | 4.15.0 | `PSF-2.0` | Permissive | Permissive Python Software Foundation license. Commercial and proprietary use is allowed; keep the license and copyright notice. |
| urllib3 | 2.7.0 | `MIT` | Permissive | Permissive license. Use, modification and redistribution – including commercial use and in proprietary products – are permitted as long as the copyright and license notice are retained. |

## Sources / Project Pages

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
_Generated by `scripts/generate_license_report.py`. Changes to the dependency set update this report automatically in the CI workflow._
