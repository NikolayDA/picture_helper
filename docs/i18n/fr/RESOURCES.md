[Deutsch](../../../RESOURCES.md) · [English](../en/RESOURCES.md) · [Español](../es/RESOURCES.md) · **Français** · [Українська](../uk/RESOURCES.md) · [简体中文](../zh/RESOURCES.md)

# Ressources utilisées

Ce document liste **toutes les ressources externes** que BgRemover
utilise ou nécessite : bibliothèques (paquets Python), autres logiciels
et outils, code tiers ainsi que les assets propres au projet — chacun
avec son objet, sa licence et sa source.

> Indications de version : « Min. » provient de `pyproject.toml` (exigence
> minimale contraignante), « vérifié » est la base Python 3.12 figée dans
> `requirements/constraints.txt` pour les contrôles locaux/CI actuels. Le
> texte de licence fourni avec chaque paquet fait toujours foi.

---

## 1. Dépendances d'exécution (paquets Python)

Déclarées dans `pyproject.toml` sous `[project] dependencies`.

| Paquet | Objet dans le programme | Min. | Vérifié | Licence |
|-------|-------------------|------|---------|--------|
| **PyQt6** | Interface graphique complète (fenêtre, canevas, widgets, événements, QSettings, QThread) | `>=6.5` | 6.11.0 | **GPL v3** ou licence commerciale Riverbank |
| **Pillow** (PIL) | E/S d'image, EXIF-transpose, rotation/miroir, masques/alpha, enregistrement (PNG/JPEG/WebP/TIFF) | `>=10` | 12.2.0 | HPND (aussi « MIT-CMU » ; licence open source PIL) |
| **NumPy** | Tableaux de pixels, flood-fill, opérations sur les masques | `>=1.24` | 2.4.5 | BSD-3-Clause |

Via PyQt6, le framework **Qt 6** (The Qt Company) est également lié.
Qt lui-même est sous LGPL v3 / GPL / licence commerciale ; le
**binding PyQt6** est sous GPL v3 — voir la section 8.

## 2. Dépendance d'IA facultative

Déclarée sous `[project.optional-dependencies] ai` — nécessaire uniquement pour la
suppression automatique d'arrière-plan (outil `rembg`) :

| Ressource | Objet | Min. | Vérifié | Licence | Source |
|-----------|-------|------|---------|--------|-------|
| **rembg[cpu]** | Suppression d'arrière-plan assistée par IA (`rembg.remove`) | `>=2.0` | 2.0.75 | MIT | PyPI |
| **onnxruntime** | Backend d'inférence ONNX (dépendance transitive de `rembg[cpu]`) | (transitif) | 1.26.0 | MIT (Microsoft) | PyPI |
| **Modèle U²-Net** (`u2net.onnx`) | Modèle de segmentation par défaut, que rembg **télécharge à l'exécution** (non inclus dans le dépôt) | – | – | Apache-2.0 (projet *U-2-Net*) | Téléchargement par rembg dans le répertoire de cache utilisateur |

Sans les extras `ai`, le programme démarre normalement ; le bouton d'IA est alors
désactivé (`REMBG_AVAILABLE = False`).

## 3. Bibliothèque standard Python

Partie de CPython, **aucune installation supplémentaire** nécessaire
(licence : PSF License Agreement) :

`sys`, `os`, `io`, `logging`, `collections.deque`, `pathlib.Path`,
`importlib.metadata`, `importlib.resources`, `contextlib`, `tempfile`.

## 4. Outils de développement et de test

Déclarés sous `[project.optional-dependencies] test` :

| Outil | Objet | Min. | Vérifié | Licence |
|----------|-------|------|---------|--------|
| **pytest** | Exécuteur de tests | `>=8` | 9.0.3 | MIT |
| **pytest-qt** | Fixtures Qt (headless `offscreen`) | `>=4.4` | 4.5.0 | MIT |
| **ruff** | Linting / vérification de style | `>=0.6` | 0.15.13 | MIT |
| **mypy** | Contrôle de typage statique (étape de CI) | `>=1.10` | 2.1.0 | MIT |
| **packaging** | Analyse des constraints de dépendances dans les tests | `>=24` | 24.0 | Apache-2.0 ou BSD-2-Clause |

Les outils optionnels de documentation/PDF sont déclarés sous
`[project.optional-dependencies] docs` :

| Outil | Objet | Min. | Licence |
|----------|-------|------|--------|
| **Markdown** | Markdown → HTML pour `ANLEITUNG.pdf` | `>=3.5` | BSD |
| **WeasyPrint** | Rendu PDF depuis HTML/CSS | `>=61` | BSD-3-Clause |
| **fonttools** | Inspection des polices pour la génération PDF | `>=4.0` | MIT |

Sous Linux, la génération PDF nécessite également les polices DejaVu et
Pango/Cairo/GDK-Pixbuf (paquets de distribution). Sous macOS, le
générateur utilise les polices système Arial/Courier New ; installer
Pango avec `brew install pango`.

## 5. Outils de construction et de distribution (macOS)

Requis par le script de bundle d'application `create_BgRemover_app.sh`. Il n'empaquette
**aucun** de ces programmes, mais les appelle via le système :

| Outil | Objet | Origine |
|----------|-------|----------|
| `python3` + `venv` + `pip` | Créer un venv isolé, installer les dépendances avec `requirements/constraints.txt` | Python / PyPA |
| `setuptools` (backend de build) | Empaquetage selon `[build-system]` (`>=61`) | MIT |
| `/usr/bin/arch`, `uname` | Forcer l'architecture CPU native (Apple Silicon) | macOS |
| `iconutil` | Générer l'icône d'application `.icns` depuis un iconset (fallback : PNG) | macOS |
| `osascript` | Afficher les messages d'erreur du lanceur d'application | macOS |
| Outils shell standard | `mkdir`, `cp`, `cat`, `command`, entre autres | POSIX/macOS |

`BgRemover.command` est le lanceur par double-clic fourni (code
propre du projet).

## 6. Intégration continue

Définie dans `.github/workflows/pr-ci.yml`, `.github/workflows/ci.yml`,
`.github/workflows/ui-nightly.yml` et `.github/workflows/license-check.yml`.
Les pull requests exécutent un job léger sur Ubuntu/Python 3.12 ; la
matrice complète s'exécute sur Ubuntu + macOS avec Python 3.10–3.13 comme
gate de release (le workflow de release l'appelle sur un tag de version
avant la publication), chaque semaine via cron ou manuellement ;
`ui-nightly.yml` exécute les tests d'interaction UI chaque nuit ; le
workflow de licences génère le rapport dépendances/licences.

| Ressource | Objet | Licence |
|-----------|-------|--------|
| `actions/checkout@v5` | Récupérer le dépôt | MIT |
| `actions/setup-python@v6` | Configurer Python + cache pip | MIT |
| `actions/upload-artifact@v4` | Téléverser les artefacts du rapport de licences | MIT |
| `actions/download-artifact@v4` | Télécharger le résumé des licences dans le job de commentaire séparé | MIT |
| `actions/github-script@v7` | Commenter le résumé des licences sur les pull requests | MIT |
| `pip-licenses` | Dump brut des licences des paquets installés | MIT |
| `requirements/constraints.txt` | Snapshot reproductible des dépendances pour checks locaux, CI, rapport de licences et App Bundle | Fichier du projet |
| Bibliothèques système Qt via `apt` (Linux) | Exécution Qt headless : `libegl1`, `libfontconfig1`, `libxkbcommon0`, `libdbus-1-3`, `libxcb-*` | empaquetées par la distribution, diverses licences permissives/copyleft (Mesa, fontconfig, libxkbcommon, libxcb, dbus …) |

## 7. Ressources propres au projet

Œuvre propre du projet, couverte par la licence du projet
(GPL-3.0-or-later, voir `LICENSE`) :

- **Code source** : le paquet installable `bgremover/`, la suite de
  tests sous `tests/` et les scripts du projet sous `scripts/`.
- **Icônes de barre d'outils/d'onglets** : `bgremover/icons/*.png` (`ai`, `bg`, `brush`,
  `clear_sel`, `close`, `eraser`, `form`, `open`, `redo`, `restore`,
  `save`, `transparency`, `undo`, `wand`). Chargées par `make_tool_icon()`
  via `importlib.resources` comme données du paquet.
- **Icônes vectorielles dessinées** : si un PNG manque, `make_tool_icon()`
  dessine l'icône de façon programmatique avec `QPainter`
  (fonctions `_draw_*_icon`) — aucun asset externe.
- **Icône d'application** : `BgRemover_icon.png` (source du `.icns` macOS).
- **Curseurs** : dessinés à l'exécution (`make_wand_cursor`,
  `make_brush_cursor`, `make_eraser_cursor`) — aucun fichier externe.

**Aucun code source tiers** n'est intégré au dépôt
(pas de `vendor/` ni de `third_party/`) ; les fonctionnalités externes sont
exclusivement obtenues via les paquets listés ci-dessus.

## 8. Compatibilité de licence (remarque)

BgRemover est sous **GPL-3.0-or-later** (`LICENSE`). Ce choix est
conditionné par **PyQt6** : le binding est sous licence GPL v3 (ou
commerciale), c'est pourquoi l'application distribuée dans son ensemble —
en particulier le `BgRemover.app` empaqueté — doit être
conforme à la GPL. Les autres dépendances d'exécution/d'IA
(Pillow HPND, NumPy BSD, rembg MIT, onnxruntime MIT, U²-Net Apache-2.0)
sont compatibles avec la GPL v3.

Un modèle de licence **permissif** (MIT/Apache-2.0) ne serait possible que si
PyQt6 était remplacé par **PySide6** sous licence LGPL v3.

---

*Note de maintenance :* en cas de modifications de `pyproject.toml`,
`requirements/constraints.txt`, `.github/workflows/pr-ci.yml`,
`.github/workflows/ci.yml`, `.github/workflows/ui-nightly.yml`, `.github/workflows/license-check.yml`,
`create_BgRemover_app.sh` ou des données du paquet sous `bgremover/icons/`,
merci de mettre également à jour ce document.
