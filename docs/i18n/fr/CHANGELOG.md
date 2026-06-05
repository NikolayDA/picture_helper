[Deutsch](../../../CHANGELOG.md) · [English](../en/CHANGELOG.md) · [Español](../es/CHANGELOG.md) · **Français** · [Українська](../uk/CHANGELOG.md) · [简体中文](../zh/CHANGELOG.md)

# Changelog

Toutes les modifications notables de BgRemover sont
documentées dans ce fichier. Le format s'inspire de
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/) ; le projet
suit le [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Ajouté

### Modifié

- **Dépendances mises à jour.** `idna` passe à 3.15 et `urllib3` à 2.7.0 ;
  `LICENSES.md` est synchronisé avec le nouveau snapshot de dépendances.

### Corrigé

### Supprimé

## [2.3.0] – 2026-06-04


### Ajouté

- **Couverture de tests portée à 88 % (deuxième ronde, auparavant 82 %).** Le
  nouveau fichier `tests/test_canvas_events.py` couvre les gestionnaires
  d'événements et la logique de `canvas.py` : souris, clavier, molette,
  glisser-déposer, flux de résultat de la baguette, réglages d'outils,
  undo/redo/undo-to pendant un crop actif et guards sans image chargée.
  `canvas.py` passe de 64 % à 99 % et `fail_under` de 80 à 86.
- **Couverture de tests portée à 82 % (auparavant 74 %).** De nouveaux tests de
  comportement couvrent `tests/test_lasso.py`, `tests/test_canvas_crop.py`,
  `tests/test_viewport.py`, `tests/test_crop_overlay.py`,
  `tests/test_settings_schema.py` et `tests/test_settings_dialog.py`. Plusieurs
  modules atteignent 100 %, `canvas_crop.py` 98 %, et `fail_under` passe de 68 à
  80.
- **i18n de ANLEITUNG.md.** Cinq traductions du guide allemand ont été ajoutées
  dans `docs/i18n/{en,es,fr,uk,zh}/ANLEITUNG.md`; `tests/test_i18n_docs.py`
  inclut désormais `"ANLEITUNG.md"` et chaque traduction précise que
  `ANLEITUNG.pdf` n'est généré que pour l'original allemand.
- **Test soft-drift `tests/test_i18n_sync.py`.** Compare la hiérarchie des
  titres et le nombre de blocs de code de `CHANGELOG.md`, `INSTALL_MAC.md` et
  `INSTALL_LINUX.md` avec les originaux allemands ; les écarts produisent des
  avertissements lisibles plutôt que des échecs bloquants.
- **`bgremover/status_messages.py` – messages d'état centralisés.** Les textes
  d'état visibles depuis `canvas.py`, `canvas_crop.py` et `main_window.py` sont
  regroupés dans `StatusMessages`, en préparation d'une future localisation.
- **i18n runtime avec support anglais.** L'allemand et l'anglais peuvent être
  changés à l'exécution ; le dialogue de réglages inclut un sélecteur de langue
  persistant avec indication de redémarrage, et les textes UI du canvas, des
  dialogues et du panneau droit utilisent la couche centrale de traduction.
- **Raccourcis clavier pour les outils.** Les outils d'édition peuvent être
  changés au clavier ; les tooltips de la barre d'outils et la documentation
  listent les raccourcis adaptés à chaque plateforme.
- **Paquet Linux AppImage.** Le build de release produit désormais un AppImage
  comme voie recommandée pour les utilisateurs Linux, avec scripts de packaging,
  couverture CI et notes d'installation.
- **Linux `.deb`, aarch64/Raspberry Pi et workflow de release.** Le packaging
  Linux ajoute les paquets Debian, le support aarch64/Pi et le workflow de
  release associé.
- **Version de schéma QSettings.** Nouveau `bgremover/settings_schema.py` avec
  `SCHEMA_VERSION = 1` et `migrate(settings)` ; `MainWindow.__init__` lance la
  migration à la création de `QSettings`. Protection downgrade, valeurs
  corrompues et tests dans `tests/test_settings_schema.py` sont couverts.
- **Test runtime pour `RembgWarmupWorker`.** De nouveaux tests dans
  `tests/test_workers.py` et `tests/test_worker_controller.py` vérifient que le
  warmup émet toujours `finished` et que le cycle de vie du thread se termine
  même si `rembg_remove` échoue au premier démarrage.

### Modifié

- Documentation et commentaires de code nettoyés : les marqueurs PR/séries
  obsolètes ont été retirés des docs vivantes, les notes d'installation macOS
  ont été actualisées et les recommandations résumées à l'état review/roadmap
  courant.
- La version du projet passe à 2.3.0 dans les métadonnées du paquet,
  AppStream, les aperçus de licences et les liens du changelog.

- **Langue des docstrings unifiée.** `bgremover/image_ops.py`,
  `bgremover/recent_files.py` et `bgremover/worker_controller.py` passent de
  docstrings anglaises à l'allemand, conformément au reste du projet.
- **Documentation utilisateur des paquets Linux et du réglage de langue mise à
  jour.** README, `INSTALL_LINUX.md` et `ANLEITUNG.md` mentionnent AppImage/`.deb`
  comme voie recommandée pour les utilisateurs Linux et documentent la langue
  persistante avec l'indication de redémarrage ; les copies i18n sont
  synchronisées.
- **Ronde d'hygiène de code.** Le fallback de version lit `pyproject.toml`,
  `_paint_brush` reçoit `additive` explicitement, `apply_remove`/`apply_replace`
  ne capturent que les erreurs attendues, les effets globaux et cas QSettings
  sont documentés, `make clean` nettoie plus d'artefacts et la description du
  projet reflète le support macOS/Linux.
- **La sélection par baguette ne bloque plus l'UI.** Le flood-fill passe dans
  `FloodFillWorker` sur un `QThread` court avec vérification stale par
  `content_revision`; pan/zoom restent réactifs et seul un clic parallèle de
  baguette est bloqué avec un message d'état.
- **Matrice CI étendue.** Full CI vérifie Python 3.10, 3.11, 3.12 et 3.13 sur
  Ubuntu et macOS.
- **`RembgWarmupWorker` hérite de `_Worker`.** Le boilerplate commun passe dans
  la base avec le hook `_always_finished()`, tout en conservant le contrat
  `finished` et en unifiant logging, erreurs et annotations de `WorkerController`.
- **Les sous-modules Canvas utilisent l'API publique d'édition.** `CanvasCrop` et
  `CanvasTransform` utilisent `apply_edit(...)` et `ImageCanvas.current_tool` ;
  plusieurs opérations de sélection utilisent `_requires_image` et l'état vide
  signale désormais clairement l'absence d'image.
- **API publique du paquet allégée.** Les symboles privés ne sont plus
  réexportés depuis `bgremover`; les consommateurs doivent importer depuis les
  sous-modules. `logger`, `LOG_FILENAME`, `REMBG_AVAILABLE` et
  `current_log_file` restent publics ; la façade de test `MainWindow._recent_paths()`
  est supprimée.

### Corrigé

- **`apply_remove`/`apply_replace` ne masquent plus les vrais bugs.** Le filtre
  étroit laisse remonter `AttributeError`, `AssertionError` et similaires tout en
  convertissant les erreurs image/IO attendues en messages d'état.
- **Le chemin de chargement synchrone utilise les mêmes protections que le
  worker.** `ImageCanvas.load_image` appelle désormais `open_validated_image`,
  donc les fichiers manipulés et formats non pris en charge se terminent aussi
  proprement via message d'état lors du drag & drop.
- **License check stabilisé.** `coverage` est épinglé dans
  `requirements/constraints.txt` (`==7.14.0`) pour éviter un drift de
  `LICENSES.md` dû aux releases upstream.
- **License check renforcé contre le drift de fuseau horaire.**
  `actions/checkout` utilise `fetch-depth: 0` et la date est calculée avec
  `TZ=UTC` et `--date=short-local`, afin de trouver le vrai commit et de
  formater la date de manière déterministe.

### Supprimé

- **Code mort supprimé de Canvas, Lasso et MainWindow.** `ImageCanvas._version`,
  `CanvasLasso.close_to_mask` et `MainWindow._btn_grp` sont supprimés.

## [2.2.0] – 2026-05-25

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

### Supprimé

- Suppression des constantes de stylesheet mortes `BTN_STYLE` et
  `GRP_STYLE`.

### Corrigé

- `save_image()` signale désormais les erreurs d'E/S comme message de
  statut au lieu de les propager sans gestion.

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

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/5fa8025dbabd997484e4739b1f547e9c59aed319...HEAD
[2.3.0]: https://github.com/NikolayDA/picture_helper/compare/da7186869e63cf9612897b31d80a84c1cc409062...5fa8025dbabd997484e4739b1f547e9c59aed319
[2.2.0]: https://github.com/NikolayDA/picture_helper/compare/4f4bfc2a3adf154d86d4aa2f46b0149bb863bc66...da7186869e63cf9612897b31d80a84c1cc409062
[2.1.0]: https://github.com/NikolayDA/picture_helper/compare/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1...4f4bfc2a3adf154d86d4aa2f46b0149bb863bc66
[2.0.0]: https://github.com/NikolayDA/picture_helper/tree/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1
