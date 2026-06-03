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

Revue de suivi après « modest-shannon », axée sur les chemins de sauvegarde, de chargement et de CI. **8 points (N1–N8) :** 7 corrigés avec tests de régression, fusionnés via **PR #142** (N1), **#143** (N6, N8), **#144** (N4, N5) et **#148** (N2, N7) ; 1 déjà couvert (N3). Base toujours verte : ruff/mypy propres, suite verte.

### État d'avancement

| Statut | Points |
|--------|--------|
| ✅ Terminé | N1, N2, N4, N5, N6, N7, N8 |
| ⏳ Ouvert | – |

### Constats

- **N1 🟠 — Libérer le verrou de la baguette magique sur le chemin d'erreur** (PR #142). Suite de « modest-shannon » B : au changement d'image, `_load_image_async` annule le flood fill, qui n'émet alors ni `finished` ni `error`. La réinitialisation du verrou ne passait que par le chemin de succès (`apply_loaded_image`) : si le chargement échouait, `_wand_busy` restait actif et la baguette bloquée sur l'ancienne image. Nouvelle `reset_pending_wand()` silencieuse juste à côté de `cancel_flood_fill()`.
- **N2 🟡 — Limite de taille à la rotation** (PR #148). `rotate_image` (`image_ops.py`) tourne avec `expand=True` ; la protection mégapixels ne s'appliquait qu'au chargement (`Image.MAX_IMAGE_PIXELS`), pas au résultat : une image juste sous la limite pouvait gonfler à ~2× à ~45°. Désormais `rotated_size()` estime la bounding box étendue en amont ; `apply_rotate` rejette les résultats au-dessus de la limite avec un message d'état.
- **N3 ➖ — Budget mémoire de l'historique** (déjà couvert). `CanvasHistory` (`canvas_history.py`) impose depuis longtemps le budget d'annulation via `_trim()`/`_UNDO_MEMORY_LIMIT`, le rétablissement étant plafonné par `_REDO_MAX_ENTRIES`. Aucune action requise.
- **N4 🟢 — Honnêteté de l'extension à l'enregistrement** (PR #144). `save_image_file` écrivait silencieusement des octets PNG pour les extensions inconnues ; désormais un rejet clair par `ValueError`, tandis qu'une extension vide reste le PNG par défaut.
- **N5 🟡 — Enregistrement atomique** (PR #144). Écrire directement à la cible détruisait le fichier existant en cas d'interruption. Désormais `mkstemp` → `os.replace` dans le répertoire cible (le motif de `qt_plugins._copy_if_needed`), avec conservation des permissions et nettoyage du temporaire.
- **N6 🟡 — `libgl1` dans la matrice CI complète + test de dérive** (PR #143). La matrice complète n'installait pas `libgl1` (contrairement aux autres sources de paquets Qt) → `import PyQt6` risquait `libGL.so.1`. Ajouté ; le nouveau `test_ci_qt_packages.py` garde les quatre listes de paquets cohérentes.
- **N7 🟢 — Imports précoces** (PR #148). `workers.py` importait `rembg` (qui entraîne onnxruntime) au niveau du module ; comme `main_window` charge `workers`, le coût d'import était payé au démarrage, même sans utiliser l'IA. Désormais une sonde `find_spec` pour `REMBG_AVAILABLE` plus un import paresseux de `rembg` uniquement dans le thread worker (warmup/premier clic IA).
- **N8 🟢 — Docstring obsolète de `load_image`** (PR #143). Elle nommait le chemin de drop comme appelant synchrone, alors que le glisser-déposer est asynchrone depuis longtemps. Corrigé.

---

## Recommandations ouvertes

Améliorations issues de la deuxième analyse, pas encore implémentées (produit/processus) :

- **O1 🟠 — Localisation de l'app.** i18n à l'exécution implémentée : `bgremover.i18n` avec une table centrale de chaînes et un fallback stable vers l'allemand ; **allemand et anglais** sont commutables à l'exécution (sélecteur de langue dans le dialogue des réglages avec invite de redémarrage). Toute la surface visible — y compris les messages d'état du canevas, les entrées d'historique et les dialogues — passe par `tr()`, protégée par un contrôle AST contre de nouveaux littéraux non traduits. Ouvert : les autres langues de documentation existantes (es/fr/uk/zh) comme locales d'exécution (**PR 4c**).
- **O2 🟡 — App Linux / empaquetage.** Pas de bundle pour Linux ; lancement seulement via `python -m bgremover` depuis une venv. Un paquet installable (AppImage/Flatpak/`.deb`) pour **Raspberry Pi OS** et les grandes distributions (Debian/Ubuntu/Fedora) abaisse la barrière d'entrée pour les non-développeurs — analogue au bundle `.app` de macOS.
**✅ Terminé :** O4/O6 — changement d'outil par touche unique (`W`/`B`/`E`/`L`) & indications `Cmd`/`Ctrl` selon la plateforme (PR #146, `test_tool_shortcuts.py`) ; O3 — matrice complète en plus chaque semaine via cron (PR #149) ; O5 — le sous-ensemble `ui_smoke` tourne en PR/Full CI, la suite qtbot complète reste nightly (PR #149).

## Plan d'implémentation par paquets de PR (à partir du 2026-06-02)

- **PR 0 — Durcissement du code (N2 + N7).** ✅ Terminé (PR #148). N2 — appliquer le garde-fou mégapixels aussi au résultat de la rotation (`rotated_size()` estime la taille cible en amont, `apply_rotate` rejette les résultats au-dessus de la limite avec un message d'état) ; N7 — importer `rembg` de façon paresseuse et sonder `REMBG_AVAILABLE` via `find_spec` (la gestion d'échec du warmup existante couvre un backend défectueux).
- **PR 1 — Raccourcis d'outils et indications.** ✅ Terminé (PR #146). O4 + O6 : changement par touche unique (`W`/`B`/`E`/`L`), état coché de la toolbar synchronisé, tooltips/README/manuel mis à jour, test de régression du câblage des raccourcis.
- **PR 2 — CI sécurisée plus tôt.** ✅ Terminé (PR #149). O3 — matrice complète en plus chaque semaine (cron) ; O5 — sous-ensemble `ui_smoke` en PR/Full CI, Nightly UI reste la suite complète.
- **PR 3 — Socle i18n.** ✅ Terminé. O1 préparé : `bgremover.i18n` avec locale/fallback à l'exécution, allemand comme défaut stable, première table centrale de chaînes pour messages d'état, menu, toolbar, onglets, historique et barre de recadrage ; tests de régression pour normalisation de locale, fallback et câblage UI.
- **PR 4 — Déploiement i18n.** ✅ Terminé. O1 rendu utilisable : **4a** — couverture `tr()` étendue au panneau droit, au dialogue des réglages et à tous les dialogues (allemand byte-identique, vérifié par golden diff) ; **4b** — table anglaise complète + sélecteur de langue (persistance, invite de redémarrage) ; **4b.1** — messages d'état du canevas, descriptions d'historique et dialogues de `main_window` (ouvrir/enregistrer/couleur/non enregistré) via `tr()`, plus un garde AST contre de nouveaux littéraux non traduits aux points visibles par l'utilisateur. Parité clés/marqueurs et smoke UI par locale testés.
- **PR 4c — i18n autres langues (optionnel, reporté).** Au besoin, ajouter es/fr/uk/zh comme locales d'exécution (refléter les tables clé par clé — parité/smoke/garde s'appliquent alors automatiquement). Non planifié actuellement.
- **PR 5 — Base du packaging Linux.** Démarrer O2 : choisir l'artefact cible (AppImage/`.deb`/Flatpak), fichier desktop/icône/métadonnées AppStream et smoke de build Linux.
- **PR 6 — Extension du packaging Linux.** Finaliser O2 : variante Raspberry Pi OS, deuxième format de paquet optionnel et workflow de release pour les artefacts Linux.

---

## Séries précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés (PR #135/#136) ; dont la gestion des bombes de décompression et le cycle de vie de la baguette que N1 complète désormais sur le chemin d'erreur.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, #1–#15 terminés, #4 abandonné (faux positif).

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
