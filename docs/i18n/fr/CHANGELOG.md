[Deutsch](../../../CHANGELOG.md) · [English](../en/CHANGELOG.md) · [Español](../es/CHANGELOG.md) · **Français** · [Українська](../uk/CHANGELOG.md) · [简体中文](../zh/CHANGELOG.md)

# Changelog

Toutes les modifications notables de BgRemover sont
documentées dans ce fichier. Le format s'inspire de
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/) ; le projet
suit le [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Ajouté

- **Snapshot reproductible des dépendances**
  (`requirements/constraints.txt`). Le Makefile, le workflow de licences
  et le build de l'app macOS utilisent le même jeu de constraints commité
  pour les installations de tests, CI, licences et App Bundle.
- **Doctor local de l'environnement de tests** (`make doctor`,
  `scripts/check_test_env.py`). Vérifie la version de Python, les
  dépendances `[test]`, l'installation non éditable du paquet, le script
  console `bgremover` et Qt `offscreen` avant qu'un échec local
  n'apparaisse tard dans pytest.
- **Test de smoke CI pour le démarrage de l'app**
  (`tests/test_app_smoke.py`). Les tests d'UI existants sont exclus de
  la CI via `-m 'not ui'` ; la CI ne vérifiait donc jamais si
  l'application démarre tout court – exactement la faille par laquelle
  les échecs de démarrage macOS sont passés. Nouveau, sans le marqueur
  `ui` (donc exécuté en CI) : `python -m bgremover` et le script de
  console `bgremover` démarrent entièrement depuis un répertoire de
  travail neutre (le nouveau hook d'autotest `BGREMOVER_SMOKE_TEST`
  quitte après le premier tour de boucle d'événements avec le code 0) ;
  on vérifie que la configuration des plugins Qt produit un chemin
  valide ; la syntaxe shell des scripts de démarrage
  (`create_BgRemover_app.sh`, `BgRemover.command`, `diagnose_mac.sh`)
  et du lanceur intégré au paquet d'app est contrôlée. `zsh` est
  installé dans le job CI Linux à cet effet.

### Modifié

- **MainWindow est encore modularisé.** La persistance et la sémantique
  du menu « Ouvrir récent » vivent maintenant dans
  `bgremover/recent_files.py`; `MainWindow` ne délègue plus que le
  chargement, les messages d'état et l'intégration au menu Fichier.
- **Construction des menus/actions extraite de `MainWindow`.**
  `bgremover/menu_actions.py` construit la barre de menus, les `QAction`,
  les raccourcis et le sous-menu des fichiers récents ; `MainWindow`
  ne fournit plus que les callbacks métier.
- **Panneau d'onglets droit extrait de `MainWindow`.**
  `bgremover/right_panel.py` construit les onglets Sélection, Arrière-plan,
  Transformation et Forme, y compris sliders, spinboxes et boutons de
  panneau ; `MainWindow` ne fournit plus que les callbacks du canevas.
- **Orchestration des workers encapsulée hors de `MainWindow`.**
  `bgremover/worker_controller.py` possède maintenant les threads de
  chargement, d'IA et de warmup, y compris les références fortes aux
  workers, le câblage `deleteLater` et le shutdown partagé.

### Corrigé

- **Liens de release/changelog corrigés vers des refs réelles.**
  `[Unreleased]` compare maintenant depuis `v2.1.0` ; `[2.1.0]`
  utilise comme base le commit de release 2.0.0 documenté, car le dépôt
  n'a pas de tag historique `v2.0.0`.
- **Paquet d'app : la détection de `bgremover` au setup ne dépend plus
  du répertoire de travail.** `create_BgRemover_app.sh` considérait la
  venv comme « prête » alors que `bgremover` n'y était pas installé :
  la vérification `has_deps` s'exécutait avec `cwd` dans le dossier du
  projet, et Python ajoute automatiquement le répertoire courant à
  `sys.path[0]` – donc `import bgremover` trouvait le **répertoire
  source** `bgremover/` du dépôt au lieu d'une vraie installation dans
  la venv. Le lanceur de l'app démarre avec un autre `cwd`, ne voit
  pas le répertoire source et signalait donc « Le paquet bgremover
  manque dans la venv ». `has_deps` et la vérification finale
  s'exécutent maintenant depuis `$HOME` (sous-shell `cd "$HOME"`), et
  vérifient ainsi la même réalité que le lanceur ; si le paquet
  manque, le chemin rapide pip install s'enclenche. `diagnose_mac.sh`
  teste aussi depuis `$HOME` et affiche en plus `pip show bgremover`
  de la venv de l'app (preuve indépendante du cwd indiquant si/où le
  paquet est installé).
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

- **Opérations d'image pures extraites de `ImageCanvas`.**
  `bgremover/image_ops.py` contient désormais suppression/remplacement
  d'arrière-plan, enregistrement, rotation, miroir, coins arrondis et
  masquage de crop sous forme de fonctions PIL/NumPy sans Qt.
  `ImageCanvas` conserve l'état UI, undo/redo, signaux et overlays ;
  `tests/test_image_ops.py` vérifie directement les opérations de pixels
  sans `QApplication`.
- **Documentation des recommandations mise à l'état actuel.**
  `RECOMMENDATIONS.md` et les versions i18n contiennent maintenant un
  bloc d'état du tour 6 pour la série récente de PRs (#70, #72–#78) et
  signalent explicitement les anciens constats du monolithe comme
  contexte historique. `tests/test_recommendations_docs.py` protège ce
  bloc.
- **Documentation des ressources synchronisée.** `RESOURCES.md` et les
  versions i18n reflètent maintenant le layout de paquet (`bgremover/`
  au lieu de `BgRemover.py`), les package-data sous `bgremover/icons/`,
  le snapshot reproductible de constraints ainsi que les workflows PR,
  full et licences. Un test statique protège ces références contre un
  nouveau vieillissement.
- **`make pr-check` rend la vérification locale de PR plus robuste.** La
  cible réinstalle le paquet avec `[test]`, lance le doctor puis démarre
  `ruff`, `mypy` et `pytest`. Le Makefile trouve automatiquement
  `.venv/bin/python` et, sinon, retombe sur `python`/`python3` ; GitHub
  PR CI et Full CI utilisent la même cible. La configuration partagée
  des plugins Qt copie les plugins de plateforme dans le répertoire
  temporaire système si nécessaire, afin que les exécutions headless
  locales sur macOS n'échouent pas sur le listing des plugins dans le
  chemin du projet.
- **CI légère pour PR ajoutée et documentation de tests synchronisée.**
  Les pull requests disposent maintenant d'un workflow peu coûteux
  Ubuntu/Python 3.12 avec `make pr-check` ; la matrice complète Linux/macOS
  reste réservée aux releases et aux exécutions manuelles. Les workflows
  de test installent le paquet en mode non éditable afin que les smoke
  tests de l'app vérifient la réalité installée depuis un `cwd` externe.
  `README`, READMEs i18n, `TESTING.md` et `Makefile` décrivent
  désormais le même flux.
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

Premier état de release 2.0.0 documenté. Le dépôt n'a pas de tag Git
historique `v2.0.0`.

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

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/NikolayDA/picture_helper/compare/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1...v2.1.0
[2.0.0]: https://github.com/NikolayDA/picture_helper/tree/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1
