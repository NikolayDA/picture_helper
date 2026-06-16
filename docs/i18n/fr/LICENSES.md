[Deutsch](../../../LICENSES.md) · [English](../en/LICENSES.md) · [Español](../es/LICENSES.md) · **Français** · [Українська](../uk/LICENSES.md) · [简体中文](../zh/LICENSES.md)

# Aperçu des licences et aspects juridiques – bgremover 2.4.0

> Généré automatiquement – **une évaluation purement technique des conditions de licence, pas un conseil juridique.**
> Au : 2026-06-16 · Licence propre du projet : `GPL-3.0-or-later` · 45 dépendances analysées.

## Évaluation globale – utilisabilité commerciale

Licence pertinente la plus forte dans l'œuvre combinée : **Copyleft fort**.

- **Utilisation commerciale :** Autorisée – la GPL n'interdit pas la vente. De l'argent peut être demandé pour la distribution, le support ou les services.
- **Conditions :** L'œuvre combinée distribuée est régie par `GPL-3.0-or-later`. À chaque redistribution (vente comprise), le **code source** complet et correspondant doit être fourni ou proposé par écrit sous licence GPL ; le texte de la licence GPL et toutes les mentions de copyright doivent être joints ; aucune restriction d'utilisation supplémentaire ne peut être ajoutée.
- **Obligations en cas de publication/vente :** Divulgation du code source de l'œuvre combinée sous GPL, inclusion du texte GPL et des mentions de copyright/licence de toutes les dépendances (même permissives), et avis d'exclusion de garantie. Une livraison **propriétaire/code fermé** n'est **pas** possible.
- **Particularité LGPL/Qt :** Qt (PyQt6-Qt6) est en LGPL-v3 ; PyQt6 est utilisé ici sous GPL-3.0. Comme l'œuvre combinée est de toute façon en GPL, les obligations de remplacement de la LGPL sont couvertes par la divulgation du code source.

## Remarques sur d'éventuels conflits de licence

- Aucun conflit de licence détecté : toutes les licences des dépendances (permissives, MPL-2.0, LGPL-v3) sont compatibles avec GPL-3.0 et peuvent être redistribuées sous GPL-3.0.
- PyQt6 est `GPL-3.0-only`. Compatible avec la licence du projet `GPL-3.0-or-later` – l'œuvre combinée doit effectivement être distribuée sous GPL-3.0.
- PyQt6/Qt sont sous double licence (GPL **ou** une licence commerciale Riverbank/Qt). Tant que le projet reste en GPL, la variante GPL s'applique ; un produit propriétaire nécessiterait des licences PyQt6/Qt payantes.

## Répartition des licences

| Catégorie | Nombre | Paquets |
|---|---|---|
| Copyleft fort | 1 | PyQt6 |
| Copyleft faible (bibliothèque) | 1 | PyQt6-Qt6 |
| Copyleft faible (fichier) | 3 | certifi, pathspec, tqdm |
| Permissive | 40 | ImageIO, PyMatting, PyQt6_sip, Pygments, ast_serialize, attrs, charset-normalizer, coverage, flatbuffers, idna, iniconfig, jsonschema, jsonschema-specifications, lazy-loader, librt, llvmlite, mypy, mypy_extensions, networkx, numba, numpy, onnxruntime, packaging, pillow, platformdirs, pluggy, pooch, protobuf, pytest, pytest-qt, referencing, rembg, requests, rpds-py, ruff, scikit-image, scipy, tifffile, typing_extensions, urllib3 |

## Dépendances en détail

| Paquet | Version | Licence | Catégorie | Évaluation |
|---|---|---|---|---|
| ast_serialize | 0.5.0 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| attrs | 26.1.0 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| certifi | 2026.2.25 | `Mozilla Public License 2.0 (MPL 2.0)` | Copyleft faible (fichier) | Copyleft faible, au niveau du fichier. Utilisation commerciale autorisée ; seules les modifications des fichiers sous licence MPL eux-mêmes doivent être à nouveau divulguées sous MPL. Compatible avec GPL-3.0. |
| charset-normalizer | 3.4.6 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| coverage | 7.14.0 | `Apache-2.0` | Permissive | Licence permissive avec octroi de brevet explicite. Utilisation commerciale et propriétaire autorisée ; la mention de licence/copyright et les notes de modification (NOTICE) doivent être conservées. |
| flatbuffers | 25.12.19 | `Apache Software License` | Permissive | Licence permissive avec octroi de brevet explicite. Utilisation commerciale et propriétaire autorisée ; la mention de licence/copyright et les notes de modification (NOTICE) doivent être conservées. |
| idna | 3.15 | `BSD-3-Clause` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| ImageIO | 2.37.3 | `BSD-2-Clause` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| iniconfig | 2.3.0 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| jsonschema | 4.26.0 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| jsonschema-specifications | 2025.9.1 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| lazy-loader | 0.5 | `BSD-3-Clause` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| librt | 0.11.0 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| llvmlite | 0.47.0 | `BSD-2-Clause AND Apache-2.0 WITH LLVM-exception` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| mypy | 2.1.0 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| mypy_extensions | 1.1.0 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| networkx | 3.6.1 | `BSD-3-Clause` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| numba | 0.65.1 | `BSD License` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| numpy | 2.4.5 | `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| onnxruntime | 1.26.0 | `MIT License` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| packaging | 24.0 | `Apache Software License; BSD License` | Permissive | Licence permissive avec octroi de brevet explicite. Utilisation commerciale et propriétaire autorisée ; la mention de licence/copyright et les notes de modification (NOTICE) doivent être conservées. |
| pathspec | 1.1.1 | `Mozilla Public License 2.0 (MPL 2.0)` | Copyleft faible (fichier) | Copyleft faible, au niveau du fichier. Utilisation commerciale autorisée ; seules les modifications des fichiers sous licence MPL eux-mêmes doivent être à nouveau divulguées sous MPL. Compatible avec GPL-3.0. |
| pillow | 12.2.0 | `MIT-CMU` | Permissive | Licence permissive HPND/MIT-CMU (Pillow). Utilisation commerciale et propriétaire autorisée ; conserver la mention de copyright et de licence. |
| platformdirs | 4.9.6 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| pluggy | 1.6.0 | `MIT License` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| pooch | 1.9.0 | `BSD-3-Clause` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| protobuf | 7.34.1 | `3-Clause BSD License` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| Pygments | 2.20.0 | `BSD-2-Clause` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| PyMatting | 1.1.15 | `MIT License` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| PyQt6 | 6.11.0 | `GPL-3.0-only` | Copyleft fort | Copyleft fort. Toute redistribution de l'œuvre combinée doit être effectuée sous forme de code source complet sous licence GPL ; une redistribution propriétaire (code fermé) est exclue. |
| PyQt6-Qt6 | 6.11.1 | `LGPL v3` | Copyleft faible (bibliothèque) | Copyleft faible pour les bibliothèques. Utilisation commerciale autorisée ; l'utilisateur final doit pouvoir remplacer la bibliothèque (liaison dynamique ou possibilité de réédition de liens). Compatible avec GPL-3.0. |
| PyQt6_sip | 13.11.1 | `BSD-2-Clause` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| pytest | 9.0.3 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| pytest-qt | 4.5.0 | `MIT License` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| referencing | 0.37.0 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| rembg | 2.0.75 | `MIT License` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| requests | 2.33.1 | `Apache Software License` | Permissive | Licence permissive avec octroi de brevet explicite. Utilisation commerciale et propriétaire autorisée ; la mention de licence/copyright et les notes de modification (NOTICE) doivent être conservées. |
| rpds-py | 0.30.0 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| ruff | 0.15.13 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |
| scikit-image | 0.26.0 | `BSD License` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| scipy | 1.17.1 | `BSD License` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| tifffile | 2026.3.3 | `BSD-3-Clause` | Permissive | Licence permissive (famille BSD). Utilisation commerciale et propriétaire autorisée ; la mention de copyright/licence doit être fournie et le nom des auteurs ne peut pas être utilisé à des fins publicitaires sans accord. |
| tqdm | 4.67.3 | `MPL-2.0 AND MIT` | Copyleft faible (fichier) | Copyleft faible, au niveau du fichier. Utilisation commerciale autorisée ; seules les modifications des fichiers sous licence MPL eux-mêmes doivent être à nouveau divulguées sous MPL. Compatible avec GPL-3.0. |
| typing_extensions | 4.15.0 | `PSF-2.0` | Permissive | Licence permissive de la Python Software Foundation. Utilisation commerciale et propriétaire autorisée ; conserver la mention de licence et de copyright. |
| urllib3 | 2.7.0 | `MIT` | Permissive | Licence permissive. L'utilisation, la modification et la redistribution – y compris à des fins commerciales et dans des produits propriétaires – sont autorisées tant que les mentions de copyright et de licence sont conservées. |

## Sources / pages du projet

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
_Généré par `scripts/generate_license_report.py`. Les modifications de l'ensemble des dépendances mettent à jour ce rapport automatiquement dans le workflow CI._
