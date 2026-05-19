[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations évaluées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|--------|-----------|-----------|
| 🔴 | Critique | Doit être corrigé – entraîne des erreurs, des plantages ou des incohérences |
| 🟠 | Élevée | Devrait être corrigé bientôt – nuit considérablement à la fiabilité ou à la maintenabilité |
| 🟡 | Moyenne | Recommandé – améliore la qualité du code, la lisibilité ou la testabilité |
| 🟢 | Faible | Facultatif – peaufinage, améliorations complémentaires |

---

## Résumé priorisé

| # | Recommandation | Priorité | Effort |
|---|-----------|-----------|---------|
| 1 | ~~Conflit de version Python avec les annotations de type~~ | ✅ Corrigé | – |
| 2 | ~~Capture d'exception trop large lors de l'import de rembg~~ | ✅ Corrigé | – |
| 3 | ~~Conditions de course dans les threads de worker~~ | ✅ Corrigé | – |
| 4 | ~~Validation de la taille d'image au chargement~~ | ✅ Corrigé | – |
| 5 | ~~Consommation de mémoire de la pile d'annulation~~ | ✅ Corrigé | – |
| 6 | ~~Découper les classes God~~ | ✅ Corrigé | – |
| 7 | ~~Refactoriser les méthodes trop longues~~ | ✅ Corrigé | – |
| 8 | ~~Remplacer les nombres magiques~~ | ✅ Corrigé | – |
| 9 | ~~Tests pour les scénarios de thread~~ | ✅ Corrigé | – |
| 10 | ~~Compléter les annotations de type de retour~~ | ✅ Corrigé | – |
| 11 | ~~Compléter les docstrings~~ | ✅ Corrigé | – |
| 12 | ~~Chemin du fichier journal indépendant de la plateforme~~ | ✅ Corrigé | – |
| 13 | ~~Dédupliquer le boilerplate de thread~~ | ✅ Corrigé | – |

---

## Recommandations en détail

### ✅ 1. Conflit de version Python avec les annotations de type *(corrigé)*

**Fichier** : `pyproject.toml`

`requires-python` relevé à `>=3.10`, `ruff target-version` mis à jour vers `py310`. La syntaxe `X | Y` (PEP 604) utilisée dans le code est ainsi couverte par les exigences minimales déclarées.

---

### ✅ 2. Capture d'exception trop large lors de l'import de rembg *(corrigé)*

**Fichier** : `BgRemover.py` (ligne 41)

`except BaseException:` remplacé par `except (ImportError, RuntimeError, OSError, SystemExit):`. `KeyboardInterrupt` et d'autres signaux critiques ne sont plus interceptés. `SystemExit` reste explicitement inclus, car des versions connues de rembg/onnxruntime peuvent le déclencher lors de l'import.

---

### ✅ 3. Conditions de course dans les threads de worker *(corrigé)*

**Fichier** : `BgRemover.py`

- Un nouvel assistant `_launch_worker()` dans `MainWindow` encapsule le boilerplate de thread identique (auparavant dupliqué trois fois). Les trois flux (chargement d'image, IA, préchauffage) l'utilisent désormais.
- La vérification d'obsolescence dans `_on_ai_done()` utilise désormais `_canvas._version` (compteur entier monotone, incrémenté à chaque changement d'image dans `apply_loaded_image()`) au lieu de la fragile comparaison d'identité d'objet `is`. `_ai_input_version` dans `MainWindow` stocke la valeur au démarrage de l'IA.

---

### ✅ 4. Validation manquante de la taille d'image au chargement *(corrigé)*

**Fichier** : `BgRemover.py`

Constante `_MAX_MEGAPIXELS = 100` introduite. Vérification après le `Image.open()` paresseux à deux endroits :
- `ImageLoadWorker.run()` : émet le signal `error` avec un message d'erreur (chemin de la boîte de dialogue de fichier)
- `ImageCanvas.load_image()` : émet `statusMsg` et interrompt (chemin du glisser-déposer)

---

### ✅ 5. Consommation de mémoire élevée de la pile d'annulation *(corrigé)*

**Fichier** : `BgRemover.py`

Constante `_UNDO_MEMORY_LIMIT = 256 MB` introduite. La pile d'annulation n'a plus de `maxlen` strict – à la place, après chaque push, la taille totale (estimée à `width × height × 4` octets par image RGBA) est calculée et les entrées les plus anciennes sont supprimées tant que la limite est dépassée.

---

### ✅ 6. Découper les classes God *(corrigé)*

**Fichier** : `BgRemover.py`

Les 6 fonctions d'assistance imbriquées de `_build_right_panel()` (`sec`, `lbl`, `hdivider`, `scroll_tab`, `btn`, `slider_row`) ont été extraites en tant que méthodes de classe `@staticmethod` de `MainWindow` : `_make_section`, `_make_label`, `_make_hdivider`, `_make_scroll_tab`, `_make_panel_btn`, `_make_slider`. `_TAB_STYLE` a été externalisé en tant qu'attribut de classe.

---

### ✅ 7. Refactoriser les méthodes trop longues *(corrigé)*

**Fichier** : `BgRemover.py`

Les 8 branches de dessin d'icône de `make_tool_icon()` (175 lignes, cascade if-elif) ont été extraites en tant que fonctions de module distinctes : `_draw_wand_icon`, `_draw_brush_icon`, `_draw_eraser_icon`, `_draw_ai_icon`, `_draw_open_icon`, `_draw_save_icon`, `_draw_undo_icon`, `_draw_restore_icon`. `make_tool_icon()` est désormais un répartiteur léger via un `dict`.

---

### ✅ 8. Remplacer les nombres magiques par des constantes nommées *(corrigé)*

**Fichier** : `BgRemover.py`

Nouveau bloc de constantes en tête de module :
- Mise en page de l'interface : `_TOOLBAR_WIDTH`, `_TOOLBAR_BTN_SIZE`, `_TOOLBAR_ICON_SIZE`, `_RIGHT_PANEL_WIDTH`, `_CROP_BAR_HEIGHT`, `_HISTORY_LIST_H`, `_COLOR_BTN_SIZE`, `_TAB_ICON_PX`, `_WINDOW_MIN_W/H`
- Valeurs par défaut du canevas : `_DEFAULT_TOLERANCE`, `_DEFAULT_BRUSH_RADIUS`, `_ZOOM_FACTOR`
- Couleur de superposition : `_OVERLAY_COLOR`

Tous les points d'utilisation dans le code ont été basculés sur les constantes.

---

### ✅ 9. Tests pour les chemins d'erreur des workers *(corrigé)*

**Fichier** : `tests/test_workers.py` (nouveau, 9 tests)

Nouveaux tests :
- `ImageLoadWorker` : fichier manquant, fichier corrompu, image surdimensionnée (via Mock)
- `ImageLoadWorker` : cas normal (aucune erreur attendue)
- `ImageCanvas.load_image()` : image surdimensionnée (chemin du glisser-déposer)
- `AIWorker` : signal d'erreur lors d'une exception `rembg_remove`, cas de succès (via Mock)
- Compteur `_version` du canevas : incrémenté lors d'`apply_loaded_image`, inchangé lors d'une annulation

---

### ✅ 10. Annotations de type de retour complétées *(corrigé)*

**Fichier** : `BgRemover.py`

77 fonctions et méthodes sans annotation de retour ont été dotées de `-> None` (ou d'un type spécifique). En outre, `QFont` a été ajouté à l'import PyQt6 (requis pour `_text_font() -> QFont`).

---

### ✅ 11. Docstrings manquantes dans les méthodes auxiliaires *(corrigé)*

**Fichier** : `BgRemover.py`

Docstrings d'une ligne ajoutées à `_make_label`, `_make_hdivider`, `_make_panel_btn` et `_make_slider`. Les générateurs de curseur (`make_wand_cursor`, `make_brush_cursor`, `make_eraser_cursor`) avaient déjà des docstrings.

---

### ✅ 12. Rendre le chemin du fichier journal indépendant de la plateforme *(corrigé)*

**Fichier** : `BgRemover.py`

`QStandardPaths` ajouté aux imports PyQt6. Chemin de journal basculé de `Path.home() / ".bgremover.log"` vers `QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) / "bgremover.log"` (Linux : `~/.local/share/BgRemover/`, macOS : `~/Library/Application Support/BgRemover/`).

---

### ✅ 13. Dédupliquer le boilerplate de thread dupliqué *(corrigé)*

**Fichier** : `BgRemover.py`

L'assistant `_launch_worker()` a déjà été introduit dans le cadre du correctif #3 (conditions de course). Les trois flux de worker (chargement d'image, IA, préchauffage) l'utilisent depuis lors.

---

## Tour 2 – revue de suivi (code, tests, documentation, licence)

> Correction par rapport au tour 1 : les points **#6 (classes God)** et **#8 (nombres
> magiques)** étaient marqués ✅, mais ne s'appliquaient que _partiellement_
> (`MainWindow`/`_build_right_panel` est resté à ~300 lignes ; de nombreux
> nombres de feuille de style/mise en page sont restés en ligne). Le tour 2 traite les
> points restants.

| # | Recommandation | Priorité | Statut |
|---|-----------|-----------|--------|
| R1 | Configuration du logging : appel avant `QApplication`, répertoire non créé | 🔴 | ✅ Corrigé |
| R2 | Le flood-fill bloque l'interface ; limite de 100 MP trop élevée | 🟠 | ✅ Corrigé |
| R3 | Glisser-déposer / « Récemment ouverts » contournaient le worker asynchrone | 🟠 | ✅ Corrigé |
| R4 | Violation d'encapsulation (`_pil`/`_version`/`_img_item`/`_cx…`) | 🟡 | ✅ Corrigé |
| R5 | `undo_to` incohérent (non rétablissable) | 🟡 | ✅ Corrigé |
| R6 | `MainWindow` God-Object / `_build_right_panel` | 🟡 | ✅ Corrigé |
| R7 | Pas de contrôle de typage dans la CI | 🟡 | ✅ Corrigé |
| R8 | `pyproject` ignorait `F401` globalement | 🟢 | ✅ Corrigé |
| R9 | `make_tool_icon` : import dans la boucle, `except` silencieux | 🟢 | ✅ Corrigé |
| R10 | `_apply_pil` sommait la pile d'annulation en O(n) par action | 🟢 | ✅ Corrigé |
| R11 | Pas de protection contre les bombes de décompression | 🟡 | ✅ Corrigé |
| R12 | Lacunes de tests (éviction d'annulation, géométrie, lasso, dépôt) | 🔴/🟠 | ✅ Corrigé |
| R13 | Documentation : mauvaise version de Python, licence manquante | 🟠 | ✅ Corrigé |

**R1** — Logging externalisé dans `_setup_logging()` ; il est appelé dans `__main__`
**après** `QApplication` + `setApplicationName/​setOrganizationName`.
Le répertoire cible est créé via `mkdir(parents=True, exist_ok=True)`
(fallback `~/.bgremover`).

**R2** — `flood_fill` est vectorisé (masque de similarité en quelques
opérations NumPy, puis croissance de région) ; `_MAX_MEGAPIXELS` de 100 → 40.

**R3** — Nouveau signal `ImageCanvas.loadRequested` ; `dropEvent` et
`_open_recent` passent désormais par `_load_image_async` (chemin du worker).
`load_image` reste un chemin synchrone pour les tests/le fallback de dépôt.

**R4** — Accesseurs publics : `ImageCanvas.image/has_image/version/
fit_to_view()` et `CropOverlayItem.top_left/size`. `MainWindow` et
`ImageCanvas` n'accèdent plus aux membres privés de façon inter-classes.

**R5** — `undo_to()` se comporte comme plusieurs `undo()` (chaque étape
sur la pile de rétablissement) et est ainsi rétablissable via `redo()` ; en outre,
garde-fou de recadrage comme pour `undo()`.

**R6** — `_build_right_panel()` est un répartiteur léger ; quatre
constructeurs `_build_tab_selection/background/transform/shape` ajoutent chacun un
onglet (index d'onglet issu d'`addTab()`).

**R7** — `mypy` configuré dans `pyproject.toml` (de manière pragmatique : le bruit des overrides Qt
et des lambdas de tuple mis sous silence via `disable_error_code`) et
ajouté comme étape de CI.

**R8/R9/R10/R11** — Ignore `F401` supprimé, deux imports inutilisés
supprimés ; `make_tool_icon` utilise l'import `Image` du module et journalise
les échecs avec `logger.debug` ; somme courante d'octets d'annulation `_undo_bytes`
(O(1)) ; `Image.MAX_IMAGE_PIXELS` couplé à `_MAX_MEGAPIXELS`.

**R12** — Nouveaux tests (81 → 108) : éviction de la limite de mémoire d'annulation +
suivi des octets, `tests/test_geometry.py` (rotation/miroir/coins/recadrage),
lasso + `_paint_brush` + cas de succès `apply_remove/replace`,
`tests/test_drop_and_history.py` (dépôt asynchrone, rétablissement `undo_to`),
création du répertoire `_setup_logging`.

**R13** — README/INSTALL_MAC : Python **3.10+** ; README enrichi de l'architecture,
des limitations connues, du chemin de journal correct et d'une **section Licence** ;
`LICENSE` (GPL-3.0) ajouté ; `pyproject.toml` avec
`license`/`authors`/`urls`/`classifiers`. Recommandation de licence :
**GPL-3.0-or-later** (correspond à l'obligation GPL de PyQt6 ; permissif uniquement avec
un passage à PySide6).

---

## Tour 3 – Avant l'extension de fonctionnalités

> Deux tours d'optimisation sont terminés ; le tour 3 regroupe les
> nettoyages à faible risque qu'il vaut la peine de faire avant une
> extension de fonctionnalités prévue. La recommandation **#1
> (monolithe → paquet)** est délibérément reportée : priorité élevée,
> mais aussi effort/risque élevés et en conflit avec la décision de
> conception en fichier unique documentée — une décision distincte. La
> colonne d'état référence la PR qui l'implémente.

| # | Recommandation | Priorité | Effort | État |
|---|-----------|-----------|---------|--------|
| 1 | Monolithe → paquet (`bgremover/` avec modules) | 🟠 Élevée | Élevé | ✅ résolu (tour 5) |
| 2 | ~~`save_image()` sans gestion d'erreurs~~ | 🟡 Moyenne | Faible | ✅ #48 |
| 3 | ~~Duplication d'état dans `undo/redo/undo_to/restore_original/_apply_pil`~~ | 🟡 Moyenne | Faible | ✅ #52 |
| 4 | ~~Feuilles de style en ligne éparpillées, pas de module de thème~~ | 🟡 Moyenne | Moyen | ✅ #53 |
| 5 | ~~Pas de hook SessionStart pour Claude Code on the web~~ | 🟡 Moyenne | Faible | ✅ #51 |
| 6 | Gardes « aucune image chargée » répétées (~8×) | 🟢 Faible | Faible | Ouvert |
| 7 | Code répétitif des workers (try/except/log/emit) → classe de base | 🟢 Faible | Faible | Ouvert |
| 8 | ~~Maintenir `CHANGELOG [Unreleased]`~~ | 🟢 Faible | Faible | ✅ continu |
| 9 | `mypy` très permissif (7 codes désactivés) | 🟢 Faible | Moyen | Ouvert |

**#1** — `BgRemover.py` reste un fichier unique (~3000 lignes :
utilitaires, worker, canevas, IU, dialogues, journalisation, main). Le
plus grand levier pour la croissance des fonctionnalités, mais le risque
le plus élevé (risque : élevé) et en conflit avec la décision de fichier
unique documentée. **Ouvert — délibérément reporté**, nécessite une
décision de conception distincte.

→ **Résolu au tour 5** (décision de conception : rupture nette vers un paquet – voir ci-dessous).

**#2** — Corrigé dans la **PR #48** : `save_image()` renvoie un `bool`
et encapsule les opérations d'écriture dans `try/except`
(journalisation + message d'état), cohérent avec `apply_remove/replace`
; « Enregistrer sous… » ne retient plus un chemin échoué comme cible
d'enregistrement rapide (`BgRemover.py:1080–1113`).

**#3** — Corrigé dans la **PR #52** (initialement #49, recréée
proprement après un conflit de fusion) : le bloc d'état d'image
identique a été fusionné dans les utilitaires `_set_image_state()` /
`_emit_history()` ; comportement inchangé (`BgRemover.py:877`, `:891`).

**#4** — Corrigé dans la **PR #53** (initialement #50) : une palette de
couleurs `_Theme` centrale que les modèles réutilisés référencent
(vérifié octet par octet, 218 feuilles de style, aucune différence
visuelle). Constantes mortes `BTN_STYLE`/`GRP_STYLE` supprimées
(`BgRemover.py:1547`).

**#5** — Corrigé dans la **PR #51** : un hook `SessionStart` synchrone
(`.claude/hooks/session-start.sh`, mode git 100755) installe les
bibliothèques système Qt + le projet et définit
`QT_QPA_PLATFORM=offscreen` de manière persistante ; enregistré dans
`.claude/settings.json`.

**#6** — **Ouvert.** Le retour anticipé « aucune image chargée » se
répète dans ~8 méthodes ; un petit utilitaire de garde le
regrouperait.

**#7** — **Ouvert.** Les trois flux de workers partagent du code
répétitif `try/except/log/emit` ; une classe de base optionnelle
réduirait la répétition.

**#8** — Respecté : les PR du tour 3 #48/#52/#53 maintiennent chacune
la section `CHANGELOG [Unreleased]` ; cette entrée documente en outre
le tour 3 lui-même. Une pratique continue plutôt qu'une PR unique.

**#9** — **Ouvert.** `mypy` est pragmatiquement assoupli dans
`pyproject.toml` (7 `disable_error_code`) ; le durcir progressivement
améliore la sûreté de typage (effort/risque : moyen).

---

## Tour 4 – État des lieux & prochaine étape

> État de l'analyse : `ruff` propre, `mypy` propre, **140 tests au
> vert** (16 tests d'UI désélectionnés volontairement). La qualité du
> code est élevée – le tour 4 priorise donc **ce qu'il faut aborder
> ensuite concrètement**, plutôt que de chercher de nouveaux défauts.

| # | Recommandation | Priorité | Effort | Statut |
|---|----------------|----------|--------|--------|
| 1 | ~~Coupe de version 2.1.0 + tag git~~ | 🟠 Haute | Faible | ✅ Fait (tag après merge) |
| 2 | ~~Utilitaire de garde « aucune image » (tour 3 #6)~~ | 🟢 Basse | Faible | ✅ Fait |
| 3 | ~~Classe de base de worker (tour 3 #7)~~ | 🟢 Basse | Faible | ✅ Fait |
| 4 | Durcir `mypy` progressivement (tour 3 #9) | 🟢 Basse | Moyen | 🟢 Étape 1 faite |
| 5 | Monolithe → paquet (tour 3 #1) | 🟠 Haute | Élevé | ✅ résolu (tour 5) |

### ✅ 1. Coupe de version 2.1.0 + tag git *(fait)*

**Fait dans cette PR :** `pyproject.toml` et le repli `__version__`
(`BgRemover.py`) passés à `2.1.0` ; le bloc `[Unreleased]` dans
`CHANGELOG.md` (+ i18n en/es/fr/uk/zh) daté en `[2.1.0] – 2026-05-19`
et un nouveau bloc `[Unreleased]` vide ajouté. Le `git tag v2.1.0`
n'est **délibérément pas** posé sur la branche de fonctionnalité ; il
revient au commit de merge dans `main` après le merge (voir la
description de la PR).

**Constat (pour mémoire) :** il **n'existait pas un seul tag git**
(`git tag -l` vide), bien que le CHANGELOG affirme une « première
version publiquement taguée 2.0.0 ». Depuis 2.0.0, le bloc
`[Unreleased]` avait accumulé des changements substantiels (PR #48
gestion d'erreur de sauvegarde, #52 déduplication d'état, #53
`_Theme`, doc INSTALL_LINUX, #55 lanceur de tests local), tandis que
`pyproject.toml` et le repli `__version__` restaient à `2.0.0`.

### ✅ 2. Utilitaire de garde « aucune image chargée » *(fait, tour 3 #6)*

Le retour anticipé octet-identique `if self._pil is None:
self.statusMsg.emit("Kein Bild geladen"); return` des cinq méthodes de
`ImageCanvas` `apply_round_corners`, `apply_rotate`, `apply_flip`,
`start_crop_circle`, `start_crop_ratio` est regroupé dans le décorateur
`@_requires_image`. Comportement inchangé (140 tests unitaires + 16 UI
au vert). Les trois gardes `has_image` de `MainWindow` restent
délibérément en ligne : messages différents et vérifications
secondaires dépendantes de l'ordre – les regrouper là ajouterait plus
de risque que de valeur.

### ✅ 3. Classe de base de worker *(fait, tour 3 #7)*

`AIWorker` et `ImageLoadWorker` héritent désormais de la classe de
base `_Worker`, qui encapsule le flux identique
`try/except → logger.exception → error.emit` ; les sous-classes
n'implémentent plus que `_work()`. `RembgWarmupWorker` reste
délibérément autonome (pas de signal `error`, `finished` toujours dans
`finally` – contrat différent).

### 🟢 4. Durcir `mypy` progressivement *(tour 3 #9 – étape 1 faite)*

`disable_error_code` réduit de **8 à 6** : `index` et `operator` sont
déjà propres (**0 erreur** chacun, mesuré) et donc réactivés dans
`pyproject.toml` – sans changement de code, sans risque. Feuille de
route mesurée pour les codes restants (une étape par PR, comme
recommandé) :

| Code | Erreurs ouvertes | Nature |
|------|------------------|--------|
| `arg-type` | 2 | rétrécissement None via gardes/décorateur |
| `attr-defined` | 2 | `QThread._worker`/`QObject.run` dynamiques |
| `func-returns-value` | 4 | retour void dans des tuples lambda d'UI |
| `assignment` | 4 | types d'affectation mixtes |
| `override` | 7 | signatures d'override Qt |
| `union-attr` | 67 | très large – à traiter en dernier |

Prochaine étape sensée : `arg-type` ou `attr-defined` (2 chacun,
petites améliorations réelles). Effort/risque des étapes restantes :
moyen.

### 🟠 5. Monolithe → paquet *(tour 3 #1, reporté volontairement)*

`BgRemover.py` reste un fichier unique de **3003 lignes**. Le plus
grand levier pour la croissance des fonctionnalités, mais le risque le
plus élevé et en conflit avec la décision de conception en fichier
unique documentée. Reste une décision architecturale délibérée et
distincte – à réexaminer au plus tard avant la prochaine expansion
majeure de fonctionnalités. Les quick wins #2/#3 réduisent déjà
légèrement le fichier et préparent une scission ultérieure.

→ **Résolu au tour 5** (décision de conception : rupture nette vers un paquet – voir ci-dessous).

---

## Tour 5 – Décision de conception : monolithe → paquet (résolue)

> La « décision de conception distincte » explicitement exigée au tour 3
> #1 et au tour 4 #5 est prise ici et donc résolue. La décision de
> conception en fichier unique documentée est **délibérément annulée**.

**Décision.** `BgRemover.py` (3026 lignes) est scindé en un paquet
Python `bgremover/`. Modules : `constants`, `image_utils`, `icons`,
`theme`, `workers`, `crop`, `canvas`, `widgets`, `settings_dialog`,
`logging_config`, `main_window`, `app`, `__main__`, `__init__`.

**Rupture nette vers un paquet (sans shim de compatibilité).**
`BgRemover.py` est supprimé purement et simplement. L'application est
lancée via le script de console `bgremover` **et** `python -m bgremover`.
Le mode précédent `python -m bgremover` est **délibérément abandonné** ;
les scripts de construction (`create_BgRemover_app.sh`,
`BgRemover.command`), `pyproject.toml`, Makefile/CI, tests et
documentation (i18n incluse) sont migrés dans la même coupe.

**Justification.** Selon le tour 3 #1 / tour 4 #5, le fichier unique
était le plus grand levier pour la croissance des fonctionnalités ; le
seul bloqueur était la décision de fichier unique documentée – qui est
ici explicitement annulée. Le risque reste élevé mais il est maîtrisé
par la méthode.

**Méthode.** Par phases avec une barrière stricte : **Phase A**
(préparation – cet ADR + disposition/conception, aucun code déplacé) →
**Barrière** (référence verte capturée : `ruff`/`mypy` propres,
**140 tests unitaires + 16 tests d'IU au vert**) → **Phase B** (scission
purement mécanique et identique au bit près ; code déplacé tel quel,
seuls les imports ajustés ; les tests restent au vert). Le seul
changement de code intentionnel : la résolution des ressources dans
`make_tool_icon` (`importlib.resources` au lieu de
`__file__`/`argv`/`cwd`), sans changement de comportement.

**Ordre / travail préparatoire.** Précondition remplie : `git tag
v2.1.0` est posé (au merge de la PR #60) et publié comme préversion
GitHub – le dernier état pur en fichier unique est ainsi marqué (tour 4
#1). Que le tag soit quelques commits derrière `main` HEAD est une
décision de release optionnelle du mainteneur, sans incidence sur la
coupe.

**Délibérément après, pas avant.** Le durcissement progressif de mypy
(tour 4 #4, 6 `disable_error_code` restants) se fait **après** la
scission – un grand déplacement invalide la progression de typage par
fichier. Les nettoyages internes (consolidation guard/worker) restent
également hors de cette coupe.

**Impact sur le statut.** Le tour 3 #1 et le tour 4 #5 sont **résolus**
par cette décision ; les colonnes de statut des tableaux respectifs sont
mises à jour en conséquence.

**Phase B terminée.** La coupe mécanique a atterri (13 étapes, chacune
verrouillée par l'oracle vert : `make test` 140, `make ui` 16,
`make type`, `make lint` ; les deux points d'entrée
`python -m bgremover` et `bgremover` démarrent stablement).
`BgRemover.py` est supprimé. Le paquet contient 14 modules sous
`bgremover/` ; les icônes sont expédiées comme `package-data`
(`bgremover/icons/`). Le seul changement de code intentionnel est resté
celui promis : résolution des ressources via `importlib.resources` dans
`make_tool_icon` (contrat inchangé). Script de build, Makefile/CI et
documentation (i18n incluse) ont suivi.

**Prochaine étape recommandée.** Avec la disposition par fichier, le
tour 4 #4 (durcissement progressif de mypy) prend tout son sens :
retirer un `disable_error_code` par module, corriger, recommencer. Les
nettoyages internes marqués optionnels aux tours 3/4 (unification
garde/worker) sont également moins risqués par fichier.
