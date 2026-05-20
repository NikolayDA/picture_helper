[Deutsch](../../../CHANGELOG.md) · [English](../en/CHANGELOG.md) · [Español](../es/CHANGELOG.md) · **Français** · [Українська](../uk/CHANGELOG.md) · [简体中文](../zh/CHANGELOG.md)

# Changelog

Toutes les modifications notables de BgRemover sont
documentées dans ce fichier. Le format s'inspire de
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/) ; le projet
suit le [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Corrigé

- **Chemins de lancement macOS de nouveau fonctionnels.** Après la
  coupe en paquet (tour 5), `BgRemover.command` cherchait encore le
  fichier `BgRemover.py` qui n'existe plus et s'arrêtait sur « non
  trouvé » ; le `INSTALL_MAC.md` allemand ainsi que les versions i18n
  de `INSTALL_LINUX.md` et `README.md` conservaient aussi quelques
  anciennes commandes (l'étape 15 du tour 5 avait raté le
  `INSTALL_MAC.md` allemand et la documentation d'installation i18n
  dans le glob, ainsi que `Exec=python3 /CHEMIN/.../BgRemover.py`
  dans les extraits `.desktop` i18n). Conséquence : sur macOS aucune
  des trois voies de lancement documentées (paquet app, double-clic
  sur `.command`, terminal) n'était utilisable de façon fiable.
  `BgRemover.command` démarre maintenant via `python3 -m bgremover`
  et vérifie au préalable `import bgremover` (sinon affiche une
  indication claire vers `create_BgRemover_app.sh`). INSTALL_MAC +
  tous les documents i18n reflètent le modèle de paquet actuel (y
  compris l'installation non éditable du paquet dans la venv de
  l'app et la résolution des ressources via `importlib.resources`).
- **`create_BgRemover_app.sh` : venv existante migrée proprement.**
  Une venv de l'ère monolithique (avec PyQt6/Pillow/numpy installés,
  mais bien sûr pas encore `bgremover`) était considérée à tort comme
  « ready » parce que la vérification de setup `has_deps` ne testait
  pas `bgremover`. Lors du re-run, l'installation du paquet était
  donc ignorée — et le lanceur de l'app signalait ensuite à l'exécution
  « Le paquet bgremover manque dans la venv ». La vérification inclut
  désormais aussi `import bgremover` ; en outre, il y a un chemin
  rapide : si la venv de l'app a déjà PyQt6/Pillow/numpy, on ajoute
  seulement `pip install ".[ai]"` (secondes) au lieu de reconstruire
  la venv avec toutes les dépendances (minutes).

### Modifié

- **Monolithe → paquet (tour 5).** Le fichier unique `BgRemover.py`
  (3026 lignes) a été scindé dans le paquet installable `bgremover/`
  (14 modules : `constants`, `image_utils`, `icons`, `theme`,
  `workers`, `crop`, `canvas`, `widgets`, `settings_dialog`,
  `logging_config`, `main_window`, `app`, `__main__`, `__init__`).
  Lancement désormais via `python -m bgremover` ou le script de
  console `bgremover` ; l'ancienne forme `python BgRemover.py` est
  supprimée sans remplacement. `BgRemover.py` est supprimé. Réalisé
  en **13 étapes mécaniques**, chacune verrouillée par l'oracle vert
  (140 tests unitaires + 16 tests UI, ruff, mypy). Le seul changement
  de code intentionnel, neutre en comportement : `make_tool_icon`
  résout désormais les icônes via `importlib.resources` depuis les
  données du paquet (`bgremover/icons/`) au lieu de `__file__`/
  `sys.argv`/`cwd` — contrat inchangé. `pyproject.toml`, `Makefile`,
  workflow CI et le script de build macOS (`create_BgRemover_app.sh`)
  ont suivi dans la même coupe ; la venv installe le paquet en mode
  non éditable (avec package-data), rendant l'application indépendante
  du dossier du projet.
- Les re-exports transitoires dans `BgRemover.py` (phase B) et toutes
  les importations `BgRemover` des tests ont été basculés vers le
  paquet dans l'étape finale.

## [2.1.0] – 2026-05-19

### Modifié

- Garde de retour anticipé « aucune image chargée » des cinq méthodes
  de `ImageCanvas` (`apply_round_corners`, `apply_rotate`,
  `apply_flip`, `start_crop_circle`, `start_crop_ratio`) regroupée dans
  le décorateur `@_requires_image` – le bloc auparavant octet-identique
  disparaît ; comportement inchangé (défendu par la suite de tests
  existante).
- Les workers d'arrière-plan `AIWorker` et `ImageLoadWorker` partagent
  désormais la classe de base commune `_Worker`, qui encapsule le flux
  identique `try/except → logger.exception → error.emit` ; les
  sous-classes n'implémentent plus que `_work()`. `RembgWarmupWorker`
  reste délibérément autonome (pas de signal `error`, `finished`
  toujours dans `finally`).
- Coupe de version **2.1.0** : `pyproject.toml` et le repli
  `__version__` dans `BgRemover.py` passés à `2.1.0` ; les changements
  auparavant regroupés sous `[Unreleased]` (#48/#52/#53, INSTALL_LINUX,
  tours 3/4) sont désormais datés comme 2.1.0.

### Documentation

- Ajout d'un guide d'installation pour Linux (`INSTALL_LINUX.md`) :
  paquets système par distribution (apt/dnf/pacman), configuration du venv,
  script de lancement ou entrée `.desktop` et dépannage ; lié depuis le README.
  Y compris une voie particulièrement simple pour Raspberry Pi OS (Desktop)
  sans venv/pip (PyQt6/Pillow/numpy en tant que paquets système via `apt`), avec
  une étape facultative d'ajout de l'IA.

## [2.0.0] – 2026-05-17

Première publication taguée publiquement.

### Fonctionnalités

- Suppression d'arrière-plan par IA via `rembg` (extra `ai` facultatif) y compris
  préchauffage en arrière-plan, pour que le premier clic ne bloque pas.
- Outils de sélection : baguette magique (flood-fill vectorisé avec
  curseur de tolérance), pinceau, gomme et lasso polygonal ; Maj/Ctrl
  pour une sélection additive ou soustractive.
- Rendre l'arrière-plan transparent ou le remplacer par une couleur.
- Transformations : rotation (par pas de 90° et angle libre), miroir,
  arrondi des coins, recadrage dans plusieurs formats avec grille des tiers.
- Historique avec annulation/rétablissement (boutons de la barre d'outils) et retour à n'importe quelle
  étape antérieure via une fenêtre flottante d'historique.
- Glisser-déposer ainsi que « Récemment ouverts » (10 entrées), tous deux via le
  worker de chargement asynchrone – pas de gel de l'interface.
- Enregistrement en PNG, JPEG, WebP ou TIFF.
- Paramètres persistants (répertoires par défaut, format de fichier
  préféré) via `QSettings`.
- Construction d'un bundle d'application macOS (`create_BgRemover_app.sh`) y compris venv
  isolé, gestion d'Apple Silicon et définition de l'icône ; prend en charge Python
  3.10–3.15.

### Stabilité et qualité

- Threads de worker sécurisés (pas de GC prématuré du worker,
  arrêt propre du thread dans `closeEvent`, course de l'IA via un compteur de version
  monotone du canevas).
- Limite de taille d'image (40 MP) et protection contre les bombes de décompression au chargement.
- Pile d'annulation limitée en mémoire (256 Mo) avec suivi des octets en O(1).
- Chemin de journal indépendant de la plateforme (`bgremover.log` dans le répertoire de données d'application).
- 108 tests ; `ruff` et `mypy` comme étapes de CI ; CI sur Ubuntu et macOS
  sous Python 3.10 et 3.12.
- `__version__` est lu depuis les métadonnées du paquet (source unique) ;
  la version apparaît dans le titre de la fenêtre.

### Documentation et licence

- Licence **GPL-3.0-or-later** (`LICENSE`) ; conditionnée par le
  binding PyQt6 sous licence GPL.
- `RESOURCES.md` (toutes les bibliothèques/outils/assets ainsi que leurs licences),
  `LICENSES.md` et un workflow automatisé de licence/conformité.
- README avec architecture, limitations connues et guide
  d'installation ; `INSTALL_MAC.md` détaillé.

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/NikolayDA/picture_helper/releases/tag/v2.0.0
