**Deutsch** · [English](docs/i18n/en/LICENSES.md) · [Español](docs/i18n/es/LICENSES.md) · [Français](docs/i18n/fr/LICENSES.md) · [Українська](docs/i18n/uk/LICENSES.md) · [简体中文](docs/i18n/zh/LICENSES.md)

# Lizenz- & Rechtsuebersicht – bgremover 2.2.0

> Automatisch generiert – **rein technische Einschaetzung der Lizenzbedingungen, keine Rechtsberatung.**
> Stand: 2026-05-26 · Eigenlizenz des Projekts: `GPL-3.0-or-later` · 45 Dependencies analysiert.

## Gesamtbewertung – kommerzielle Nutzbarkeit

Staerkste relevante Lizenz im Gesamtwerk: **Starkes Copyleft**.

- **Kommerzielle Nutzung:** Erlaubt – die GPL untersagt keinen Verkauf. Es darf Geld fuer Vertrieb, Support oder Dienste verlangt werden.
- **Bedingungen:** Das verteilte Gesamtwerk steht unter `GPL-3.0-or-later`. Bei jeder Weitergabe (auch Verkauf) muss der vollstaendige, korrespondierende **Quelltext** unter GPL mitgeliefert oder schriftlich angeboten werden; der GPL-Lizenztext und alle Copyright-Hinweise muessen beiliegen; es duerfen keine zusaetzlichen Nutzungsbeschraenkungen ergaenzt werden.
- **Pflichten bei Veroeffentlichung/Verkauf:** Quelloffenlegung des Gesamtwerks unter GPL, Beilegen von GPL-Text und Copyright-/Lizenzhinweisen aller (auch permissiver) Dependencies, Hinweis auf Gewaehrleistungsausschluss. Eine **proprietaere/closed-source** Auslieferung ist **nicht** moeglich.
- **LGPL/Qt-Besonderheit:** Qt (PyQt6-Qt6) ist LGPL-v3; PyQt6 wird hier unter GPL-3.0 genutzt. Da das Gesamtwerk ohnehin GPL ist, sind die LGPL-Austauschpflichten durch die Quelloffenlegung abgedeckt.

## Hinweise auf potenzielle Lizenz-Konflikte

- Kein Lizenzkonflikt erkannt: Alle Dependency-Lizenzen (permissive, MPL-2.0, LGPL-v3) sind mit GPL-3.0 vereinbar und koennen unter GPL-3.0 weitergegeben werden.
- PyQt6 ist `GPL-3.0-only`. Mit der Projektlizenz `GPL-3.0-or-later` vertraeglich – das Gesamtwerk ist effektiv unter GPL-3.0 zu verteilen.
- PyQt6/Qt sind dual lizenziert (GPL **oder** kommerzielle Riverbank/Qt-Lizenz). Solange das Projekt GPL bleibt, ist die GPL-Variante einschlaegig; fuer ein proprietaeres Produkt waeren kostenpflichtige PyQt6-/Qt-Lizenzen noetig.

## Lizenzverteilung

| Kategorie | Anzahl | Pakete |
|---|---|---|
| Starkes Copyleft | 1 | PyQt6 |
| Schwaches Copyleft (Bibliothek) | 1 | PyQt6-Qt6 |
| Schwaches Copyleft (Datei) | 3 | certifi, pathspec, tqdm |
| Permissiv | 40 | ImageIO, PyMatting, PyQt6_sip, Pygments, ast_serialize, attrs, charset-normalizer, coverage, flatbuffers, idna, iniconfig, jsonschema, jsonschema-specifications, lazy-loader, librt, llvmlite, mypy, mypy_extensions, networkx, numba, numpy, onnxruntime, packaging, pillow, platformdirs, pluggy, pooch, protobuf, pytest, pytest-qt, referencing, rembg, requests, rpds-py, ruff, scikit-image, scipy, tifffile, typing_extensions, urllib3 |

## Dependencies im Detail

| Paket | Version | Lizenz | Kategorie | Einschaetzung |
|---|---|---|---|---|
| ast_serialize | 0.5.0 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| attrs | 26.1.0 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| certifi | 2026.2.25 | `Mozilla Public License 2.0 (MPL 2.0)` | Schwaches Copyleft (Datei) | Schwaches, dateibezogenes Copyleft. Kommerzielle Nutzung erlaubt; nur Aenderungen an den MPL-lizenzierten Dateien selbst muessen wieder unter MPL offengelegt werden. Mit GPL-3.0 vereinbar. |
| charset-normalizer | 3.4.6 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| coverage | 7.14.0 | `Apache-2.0` | Permissiv | Permissive Lizenz mit ausdruecklicher Patentlizenz. Kommerzielle und proprietaere Nutzung erlaubt; Lizenz-/Copyright-Hinweis und Aenderungsvermerke (NOTICE) muessen erhalten bleiben. |
| flatbuffers | 25.12.19 | `Apache Software License` | Permissiv | Permissive Lizenz mit ausdruecklicher Patentlizenz. Kommerzielle und proprietaere Nutzung erlaubt; Lizenz-/Copyright-Hinweis und Aenderungsvermerke (NOTICE) muessen erhalten bleiben. |
| idna | 3.11 | `BSD-3-Clause` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| ImageIO | 2.37.3 | `BSD-2-Clause` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| iniconfig | 2.3.0 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| jsonschema | 4.26.0 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| jsonschema-specifications | 2025.9.1 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| lazy-loader | 0.5 | `BSD-3-Clause` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| librt | 0.11.0 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| llvmlite | 0.47.0 | `BSD-2-Clause AND Apache-2.0 WITH LLVM-exception` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| mypy | 2.1.0 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| mypy_extensions | 1.1.0 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| networkx | 3.6.1 | `BSD-3-Clause` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| numba | 0.65.1 | `BSD License` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| numpy | 2.4.5 | `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| onnxruntime | 1.26.0 | `MIT License` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| packaging | 24.0 | `Apache Software License; BSD License` | Permissiv | Permissive Lizenz mit ausdruecklicher Patentlizenz. Kommerzielle und proprietaere Nutzung erlaubt; Lizenz-/Copyright-Hinweis und Aenderungsvermerke (NOTICE) muessen erhalten bleiben. |
| pathspec | 1.1.1 | `Mozilla Public License 2.0 (MPL 2.0)` | Schwaches Copyleft (Datei) | Schwaches, dateibezogenes Copyleft. Kommerzielle Nutzung erlaubt; nur Aenderungen an den MPL-lizenzierten Dateien selbst muessen wieder unter MPL offengelegt werden. Mit GPL-3.0 vereinbar. |
| pillow | 12.2.0 | `MIT-CMU` | Permissiv | Permissive HPND/MIT-CMU-Lizenz (Pillow). Kommerzielle und proprietaere Nutzung erlaubt; Copyright- und Lizenzhinweis beibehalten. |
| platformdirs | 4.9.6 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| pluggy | 1.6.0 | `MIT License` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| pooch | 1.9.0 | `BSD-3-Clause` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| protobuf | 7.34.1 | `3-Clause BSD License` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| Pygments | 2.20.0 | `BSD-2-Clause` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| PyMatting | 1.1.15 | `MIT License` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| PyQt6 | 6.11.0 | `GPL-3.0-only` | Starkes Copyleft | Starkes Copyleft. Jede Weitergabe des Gesamtwerks muss als vollstaendiger Quelltext unter GPL erfolgen; eine proprietaere (closed-source) Weitergabe ist ausgeschlossen. |
| PyQt6-Qt6 | 6.11.1 | `LGPL v3` | Schwaches Copyleft (Bibliothek) | Schwaches Copyleft fuer Bibliotheken. Kommerzielle Nutzung erlaubt; Endnutzer muss die Bibliothek austauschen koennen (dynamisches Linking bzw. Re-Link-Moeglichkeit). Mit GPL-3.0 vereinbar. |
| PyQt6_sip | 13.11.1 | `BSD-2-Clause` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| pytest | 9.0.3 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| pytest-qt | 4.5.0 | `MIT License` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| referencing | 0.37.0 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| rembg | 2.0.75 | `MIT License` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| requests | 2.33.1 | `Apache Software License` | Permissiv | Permissive Lizenz mit ausdruecklicher Patentlizenz. Kommerzielle und proprietaere Nutzung erlaubt; Lizenz-/Copyright-Hinweis und Aenderungsvermerke (NOTICE) muessen erhalten bleiben. |
| rpds-py | 0.30.0 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| ruff | 0.15.13 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |
| scikit-image | 0.26.0 | `BSD License` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| scipy | 1.17.1 | `BSD License` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| tifffile | 2026.3.3 | `BSD-3-Clause` | Permissiv | Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, keine Werbung mit den Autorennamen ohne Zustimmung. |
| tqdm | 4.67.3 | `MPL-2.0 AND MIT` | Schwaches Copyleft (Datei) | Schwaches, dateibezogenes Copyleft. Kommerzielle Nutzung erlaubt; nur Aenderungen an den MPL-lizenzierten Dateien selbst muessen wieder unter MPL offengelegt werden. Mit GPL-3.0 vereinbar. |
| typing_extensions | 4.15.0 | `PSF-2.0` | Permissiv | Permissive Python-Software-Foundation-Lizenz. Kommerzielle und proprietaere Nutzung erlaubt; Lizenz- und Copyright-Hinweis beibehalten. |
| urllib3 | 2.6.3 | `MIT` | Permissiv | Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch kommerziell und in proprietaeren Produkten – sind erlaubt, solange Copyright- und Lizenzhinweis erhalten bleiben. |

## Quellen / Projektseiten

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
_Erzeugt durch `scripts/generate_license_report.py`. Aenderungen am Dependency-Satz aktualisieren diesen Report automatisch im CI-Workflow._
