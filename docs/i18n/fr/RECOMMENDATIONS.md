[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse du code et recommandations évaluées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | À corriger impérativement : provoque erreurs, plantages ou incohérences |
| 🟠 | Haute | À corriger rapidement : nuit fortement à la fiabilité ou à la maintenabilité |
| 🟡 | Moyenne | Recommandé : améliore la qualité du code, la lisibilité ou les tests |
| 🟢 | Basse | Optionnel : polissage et améliorations complémentaires |

---

## État actuel (2026-06-02, revue « adoring-johnson »)

Revue de suivi après « modest-shannon », axée sur les chemins de sauvegarde, de chargement et de CI. **8 points (N1–N8) :** 5 corrigés avec tests de régression, fusionnés via **PR #142** (N1), **#143** (N6, N8) et **#144** (N4, N5) ; 2 ouverts (N2, N7) ; 1 déjà couvert (N3). Base toujours verte : ruff/mypy propres, suite verte.

### État d'avancement

| Statut | Points |
|--------|--------|
| ✅ Terminé | N1, N4, N5, N6, N8 |
| ⏳ Ouvert | N2, N7 |

### Constats

- **N1 🟠 — Libérer le verrou de la baguette magique sur le chemin d'erreur** (PR #142). Suite de « modest-shannon » B : au changement d'image, `_load_image_async` annule le flood fill, qui n'émet alors ni `finished` ni `error`. La réinitialisation du verrou ne passait que par le chemin de succès (`apply_loaded_image`) : si le chargement échouait, `_wand_busy` restait actif et la baguette bloquée sur l'ancienne image. Nouvelle `reset_pending_wand()` silencieuse juste à côté de `cancel_flood_fill()`.
- **N2 🟡 — Limite de taille à la rotation** (ouvert). `rotate_image` (`image_ops.py`) tourne avec `expand=True` ; la protection mégapixels ne s'applique qu'au chargement (`Image.MAX_IMAGE_PIXELS`), pas au résultat. Une image juste sous la limite peut gonfler à ~2× à ~45° : un pic mémoire sans garde-fou.
- **N3 ➖ — Budget mémoire de l'historique** (déjà couvert). `CanvasHistory` (`canvas_history.py`) impose depuis longtemps le budget d'annulation via `_trim()`/`_UNDO_MEMORY_LIMIT`, le rétablissement étant plafonné par `_REDO_MAX_ENTRIES`. Aucune action requise.
- **N4 🟢 — Honnêteté de l'extension à l'enregistrement** (PR #144). `save_image_file` écrivait silencieusement des octets PNG pour les extensions inconnues ; désormais un rejet clair par `ValueError`, tandis qu'une extension vide reste le PNG par défaut.
- **N5 🟡 — Enregistrement atomique** (PR #144). Écrire directement à la cible détruisait le fichier existant en cas d'interruption. Désormais `mkstemp` → `os.replace` dans le répertoire cible (le motif de `qt_plugins._copy_if_needed`), avec conservation des permissions et nettoyage du temporaire.
- **N6 🟡 — `libgl1` dans la matrice CI complète + test de dérive** (PR #143). La matrice complète n'installait pas `libgl1` (contrairement aux autres sources de paquets Qt) → `import PyQt6` risquait `libGL.so.1`. Ajouté ; le nouveau `test_ci_qt_packages.py` garde les quatre listes de paquets cohérentes.
- **N7 🟢 — Imports précoces** (ouvert). `workers.py` importe `rembg` (qui entraîne onnxruntime) au niveau du module ; comme `main_window` charge `workers`, le coût d'import est payé au démarrage, même sans utiliser l'IA. Import paresseux + sonde `find_spec` pour `REMBG_AVAILABLE`.
- **N8 🟢 — Docstring obsolète de `load_image`** (PR #143). Elle nommait le chemin de drop comme appelant synchrone, alors que le glisser-déposer est asynchrone depuis longtemps. Corrigé.

---

## Recommandations ouvertes

Améliorations issues de la deuxième analyse, pas encore implémentées (produit/processus) :

- **O1 🟠 — Localisation de l'app.** L'UI est codée en dur en allemand ; pas d'i18n à l'exécution (pas de `QTranslator`/`tr()`), bien que la doc existe en cinq langues. Les messages d'état sont déjà centralisés (`status_messages.py`). De façon incrémentale via Qt Linguist (`.ts`) ou une table de chaînes légère selon `QLocale`.
- **O2 🟡 — App Linux / empaquetage.** Pas de bundle pour Linux ; lancement seulement via `python -m bgremover` depuis une venv. Un paquet installable (AppImage/Flatpak/`.deb`) pour **Raspberry Pi OS** et les grandes distributions (Debian/Ubuntu/Fedora) abaisse la barrière d'entrée pour les non-développeurs — analogue au bundle `.app` de macOS.
- **O3 🟡 — Matrice CI complète plus tôt.** La matrice complète (Linux/macOS × 3.10–3.13) ne tourne qu'aux tags/release ; les régressions sous macOS ou Python 3.10/3.13 apparaissent tard. La lancer aussi au push sur `main` ou via un cron hebdomadaire.
- **O4 🟢 — Raccourcis clavier pour les outils.** Baguette/pinceau/gomme/lasso ne sont accessibles qu'à la souris ; ajouter un changement par touche unique (p. ex. `B`/`E`).
- **O5 🟡 — Smoke UI plus tôt dans la CI.** Les tests `ui` complets tournent nightly/manuellement ; PR CI et Full CI n'exécutent que `make pr-check`. Ajouter un petit smoke UI stable à PR/Full CI, tout en gardant la suite complète nightly.
- **O6 🟢 — Indications de raccourcis correctes selon la plateforme.** Certains tooltips/docs citent `Cmd` alors que Linux utilise `Ctrl`. Générer les textes de raccourcis de façon centralisée ou dépendante de la plateforme.

## Plan d'implémentation par paquets de PR (à partir du 2026-06-02)

- **PR 1 — Raccourcis d'outils et indications.** O4 + O6 : changement par touche unique (`W`/`B`/`E`/`L`), état coché de la toolbar synchronisé, tooltips/README/manuel mis à jour, test de régression du câblage des raccourcis.
- **PR 2 — CI sécurisée plus tôt.** O3 + O5 : matrice complète aussi chaque semaine ou sur `main`, petit smoke UI en PR/Full CI, Nightly UI reste la suite complète.
- **PR 3 — Socle i18n.** Préparer O1 : locale/fallback à l'exécution, centralisation progressive des chaînes visibles, allemand conservé comme défaut stable.
- **PR 4 — Déploiement i18n.** Rendre O1 utilisable : au moins l'anglais comme langue runtime, puis les autres langues de documentation existantes, avec smoke checks par locale.
- **PR 5 — Base du packaging Linux.** Démarrer O2 : choisir l'artefact cible (AppImage/`.deb`/Flatpak), fichier desktop/icône/métadonnées AppStream et smoke de build Linux.
- **PR 6 — Extension du packaging Linux.** Finaliser O2 : variante Raspberry Pi OS, deuxième format de paquet optionnel et workflow de release pour les artefacts Linux.

---

## Séries précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés (PR #135/#136) ; dont la gestion des bombes de décompression et le cycle de vie de la baguette que N1 complète désormais sur le chemin d'erreur.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, #1–#15 terminés, #4 abandonné (faux positif).

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
