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

## État actuel (2026-06-01, revue « modest-shannon »)

Revue approfondie du code après la v2.2 (code, docs, tests). Base excellente : ruff/mypy propres, suite verte, couverture 88 %. **5 constats (A–E)** trouvés : tous implémentés, avec tests de régression, et fusionnés via **PR #135** (A, B) et **PR #136** (C–E). Preuve donnée avec une référence fichier/fonction.

### État d'avancement

| Statut | Points |
|--------|--------|
| ✅ Terminé | A, B, C, D, E |

### Constats

- **A 🟠 — Intercepter `DecompressionBombError`.** `image_loading.py` n'interceptait pas le `DecompressionBombError` de Pillow (pas une sous-classe d'`OSError`) → les images au-delà de 2× `MAX_IMAGE_PIXELS` (80 MP) contournaient le message convivial « trop grande » et se propageaient sans être interceptées sur le chemin synchrone `load_image`. Désormais intercepté dans les deux phases d'ouverture et ramené au message standard ; le test de régression déclenche la vraie protection de Pillow (sans mock de `Image.open`).
- **B 🟡 — Cycle de vie de la baguette magique au changement d'image.** `_reset_transient_state` (`canvas.py`) ne réinitialisait pas `_wand_busy`, et `_load_image_async` (`main_window.py`) n'annulait pas le flood fill : asymétrie avec `cancel_ai()`. Conséquence : la baguette restait bloquée après un changement/restauration d'image, plus du CPU gaspillé. Réinitialisation centralisée du drapeau + `cancel_flood_fill()` au chargement.
- **C 🟡 — Isolation du logging.** `_setup_logging` (`logging_config.py`) utilisait `basicConfig(force=True)` sur la racine → des logs tiers (rembg/onnxruntime/Pillow) finissaient dans le fichier de log destiné au support, et les handlers tiers étaient arrachés. Désormais le logger nommé `BgRemover` avec ses propres handlers (`propagate=False`).
- **D 🟢 — Reliquats de tests.** `test_static_checks.py` cherchait le monolithe `BgRemover.py` supprimé et portait des marqueurs `#N` trompeurs (séries historiques ≠ numérotation actuelle). Branche monolithe retirée, origine clarifiée dans la docstring.
- **E 🟢 — Filet de sécurité i18n.** La vérification de dérive douce ne couvrait que 3 des 8 docs traduits. `WATCHED_DOCS` étendu aux 8 (toutes actuellement synchronisées structurellement).

---

## Recommandations ouvertes

Améliorations issues de la deuxième analyse, pas encore implémentées (produit/processus) :

- **O1 🟠 — Localisation de l'app.** L'UI est codée en dur en allemand ; pas d'i18n à l'exécution (pas de `QTranslator`/`tr()`), bien que la doc existe en cinq langues. Les messages d'état sont déjà centralisés (`status_messages.py`). De façon incrémentale via Qt Linguist (`.ts`) ou une table de chaînes légère selon `QLocale`.
- **O2 🟡 — App Linux / empaquetage.** Pas de bundle pour Linux ; lancement seulement via `python -m bgremover` depuis une venv. Un paquet installable (AppImage/Flatpak/`.deb`) pour **Raspberry Pi OS** et les grandes distributions (Debian/Ubuntu/Fedora) abaisse la barrière d'entrée pour les non-développeurs — analogue au bundle `.app` de macOS.
- **O3 🟡 — Matrice CI complète plus tôt.** La matrice complète (Linux/macOS × 3.10–3.13) ne tourne qu'aux tags/release ; les régressions sous macOS ou Python 3.10/3.13 apparaissent tard. La lancer aussi au push sur `main` ou via un cron hebdomadaire.
- **O4 🟢 — Raccourcis clavier pour les outils.** Baguette/pinceau/gomme/lasso ne sont accessibles qu'à la souris ; ajouter un changement par touche unique (p. ex. `B`/`E`).

---

## Série précédente (v2.2, « admiring-mayer »)

Liste externe de 15 points vérifiée face au code : **#1–#15 terminés, #4 abandonné** (faux positif). Détails dans les PR fusionnées et l'archive.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
