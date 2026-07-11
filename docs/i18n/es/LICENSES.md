[Deutsch](../../../LICENSES.md) · [English](../en/LICENSES.md) · **Español** · [Français](../fr/LICENSES.md) · [Українська](../uk/LICENSES.md) · [简体中文](../zh/LICENSES.md)

# Resumen de Licencias y Aspectos Legales – bgremover 2.5.0
> Generado automáticamente – **una evaluación puramente técnica de los términos de licencia, no asesoramiento jurídico.**
> A fecha de: 2026-06-17 · Licencia propia del proyecto: `GPL-3.0-or-later` · 45 dependencias analizadas.

## Evaluación general – usabilidad comercial

Licencia relevante más fuerte en la obra combinada: **Copyleft fuerte**.

- **Uso comercial:** Permitido – la GPL no prohíbe la venta. Se puede cobrar dinero por la distribución, el soporte o los servicios.
- **Condiciones:** La obra combinada distribuida se rige por `GPL-3.0-or-later`. En cada redistribución (incluida la venta) debe entregarse u ofrecerse por escrito el **código fuente** completo y correspondiente bajo la GPL; deben adjuntarse el texto de la licencia GPL y todos los avisos de copyright; no se pueden añadir restricciones de uso adicionales.
- **Obligaciones al publicar/vender:** Divulgación del código fuente de la obra combinada bajo la GPL, inclusión del texto GPL y de los avisos de copyright/licencia de todas las dependencias (incluso las permisivas), y aviso de exención de garantía. No es posible una entrega **propietaria/código cerrado**.
- **Particularidad LGPL/Qt:** Qt (PyQt6-Qt6) es LGPL-v3; aquí PyQt6 se usa bajo GPL-3.0. Como la obra combinada ya es GPL, las obligaciones de reemplazo de la LGPL quedan cubiertas por la divulgación del código fuente.

## Notas sobre posibles conflictos de licencia

- No se detecta ningún conflicto de licencias: todas las licencias de las dependencias (permisivas, MPL-2.0, LGPL-v3) son compatibles con GPL-3.0 y pueden redistribuirse bajo GPL-3.0.
- PyQt6 es `GPL-3.0-only`. Compatible con la licencia del proyecto `GPL-3.0-or-later` – la obra combinada debe distribuirse efectivamente bajo GPL-3.0.
- PyQt6/Qt tienen licencia dual (GPL **o** una licencia comercial de Riverbank/Qt). Mientras el proyecto siga siendo GPL, se aplica la variante GPL; un producto propietario requeriría licencias de pago de PyQt6/Qt.

## Distribución de licencias

| Categoría | Cantidad | Paquetes |
|---|---|---|
| Copyleft fuerte | 1 | PyQt6 |
| Copyleft débil (biblioteca) | 1 | PyQt6-Qt6 |
| Copyleft débil (archivo) | 3 | certifi, pathspec, tqdm |
| Permisiva | 40 | ImageIO, PyMatting, PyQt6_sip, Pygments, ast_serialize, attrs, charset-normalizer, coverage, flatbuffers, idna, iniconfig, jsonschema, jsonschema-specifications, lazy-loader, librt, llvmlite, mypy, mypy_extensions, networkx, numba, numpy, onnxruntime, packaging, pillow, platformdirs, pluggy, pooch, protobuf, pytest, pytest-qt, referencing, rembg, requests, rpds-py, ruff, scikit-image, scipy, tifffile, typing_extensions, urllib3 |

## Dependencias en detalle

| Paquete | Versión | Licencia | Categoría | Evaluación |
|---|---|---|---|---|
| ast_serialize | 0.5.0 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| attrs | 26.1.0 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| certifi | 2026.2.25 | `Mozilla Public License 2.0 (MPL 2.0)` | Copyleft débil (archivo) | Copyleft débil, a nivel de archivo. Se permite el uso comercial; solo los cambios en los propios archivos con licencia MPL deben divulgarse de nuevo bajo MPL. Compatible con GPL-3.0. |
| charset-normalizer | 3.4.6 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| coverage | 7.14.0 | `Apache-2.0` | Permisiva | Licencia permisiva con concesión de patente explícita. Se permite el uso comercial y propietario; deben conservarse el aviso de licencia/copyright y las notas de cambios (NOTICE). |
| flatbuffers | 25.12.19 | `Apache Software License` | Permisiva | Licencia permisiva con concesión de patente explícita. Se permite el uso comercial y propietario; deben conservarse el aviso de licencia/copyright y las notas de cambios (NOTICE). |
| idna | 3.15 | `BSD-3-Clause` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| ImageIO | 2.37.3 | `BSD-2-Clause` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| iniconfig | 2.3.0 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| jsonschema | 4.26.0 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| jsonschema-specifications | 2025.9.1 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| lazy-loader | 0.5 | `BSD-3-Clause` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| librt | 0.11.0 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| llvmlite | 0.47.0 | `BSD-2-Clause AND Apache-2.0 WITH LLVM-exception` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| mypy | 2.1.0 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| mypy_extensions | 1.1.0 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| networkx | 3.6.1 | `BSD-3-Clause` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| numba | 0.65.1 | `BSD License` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| numpy | 2.4.5 | `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| onnxruntime | 1.26.0 | `MIT License` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| packaging | 24.0 | `Apache Software License; BSD License` | Permisiva | Licencia permisiva con concesión de patente explícita. Se permite el uso comercial y propietario; deben conservarse el aviso de licencia/copyright y las notas de cambios (NOTICE). |
| pathspec | 1.1.1 | `Mozilla Public License 2.0 (MPL 2.0)` | Copyleft débil (archivo) | Copyleft débil, a nivel de archivo. Se permite el uso comercial; solo los cambios en los propios archivos con licencia MPL deben divulgarse de nuevo bajo MPL. Compatible con GPL-3.0. |
| pillow | 12.2.0 | `MIT-CMU` | Permisiva | Licencia permisiva HPND/MIT-CMU (Pillow). Se permite el uso comercial y propietario; conservar el aviso de copyright y de licencia. |
| platformdirs | 4.9.6 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| pluggy | 1.6.0 | `MIT License` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| pooch | 1.9.0 | `BSD-3-Clause` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| protobuf | 7.34.1 | `3-Clause BSD License` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| Pygments | 2.20.0 | `BSD-2-Clause` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| PyMatting | 1.1.15 | `MIT License` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| PyQt6 | 6.11.0 | `GPL-3.0-only` | Copyleft fuerte | Copyleft fuerte. Toda redistribución de la obra combinada debe realizarse como código fuente completo bajo la GPL; queda excluida una redistribución propietaria (código cerrado). |
| PyQt6-Qt6 | 6.11.1 | `LGPL v3` | Copyleft débil (biblioteca) | Copyleft débil para bibliotecas. Se permite el uso comercial; el usuario final debe poder reemplazar la biblioteca (enlazado dinámico o posibilidad de reenlazado). Compatible con GPL-3.0. |
| PyQt6_sip | 13.11.1 | `BSD-2-Clause` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| pytest | 9.0.3 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| pytest-qt | 4.5.0 | `MIT License` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| referencing | 0.37.0 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| rembg | 2.0.75 | `MIT License` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| requests | 2.33.1 | `Apache Software License` | Permisiva | Licencia permisiva con concesión de patente explícita. Se permite el uso comercial y propietario; deben conservarse el aviso de licencia/copyright y las notas de cambios (NOTICE). |
| rpds-py | 0.30.0 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| ruff | 0.15.13 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |
| scikit-image | 0.26.0 | `BSD License` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| scipy | 1.17.1 | `BSD License` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| tifffile | 2026.3.3 | `BSD-3-Clause` | Permisiva | Licencia permisiva (familia BSD). Se permite el uso comercial y propietario; debe incluirse el aviso de copyright/licencia y no se puede usar el nombre de los autores con fines publicitarios sin consentimiento. |
| tqdm | 4.67.3 | `MPL-2.0 AND MIT` | Copyleft débil (archivo) | Copyleft débil, a nivel de archivo. Se permite el uso comercial; solo los cambios en los propios archivos con licencia MPL deben divulgarse de nuevo bajo MPL. Compatible con GPL-3.0. |
| typing_extensions | 4.15.0 | `PSF-2.0` | Permisiva | Licencia permisiva de la Python Software Foundation. Se permite el uso comercial y propietario; conservar el aviso de licencia y de copyright. |
| urllib3 | 2.7.0 | `MIT` | Permisiva | Licencia permisiva. El uso, la modificación y la redistribución – incluido el uso comercial y en productos propietarios – están permitidos siempre que se conserven el aviso de copyright y de licencia. |

## Fuentes / páginas del proyecto

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
_Generado por `scripts/generate_license_report.py`. Los cambios en el conjunto de dependencias actualizan este informe automáticamente en el flujo de trabajo de CI._
