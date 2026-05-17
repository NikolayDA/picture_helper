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
