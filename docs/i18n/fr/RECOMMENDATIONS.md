[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de Code et Recommandations Priorisées : BgRemover

## Échelle de Priorité

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bugs, plantages ou perte de données |
| 🟠 | Haute | Impact clair sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile pour la qualité, la lisibilité ou les tests |
| 🟢 | Basse | Polissage optionnel ou amélioration de processus |

## État Actuel (2026-06-04)

La liste active d'analyse de code est vide. La dernière revue de suivi est
implémentée et couverte par des tests ; ruff, mypy et la suite locale restent
la baseline avant de nouveaux PRs.

### Terminé Depuis La Dernière Revue

- **N1/N2/N4/N5/N6/N7/N8** sont terminés : chemin d'erreur de la baguette,
  limite de taille en rotation, extensions honnêtes, sauvegarde atomique,
  paquets Qt CI, import paresseux de `rembg` et docstring `load_image`.
- **O2/O3/O4/O5/O6** sont implémentés : Linux AppImage/`.deb`, workflow de
  release, matrice complète hebdomadaire, `ui_smoke` en PR/Full CI et
  raccourcis d'outils avec indications par plateforme.

### Encore Ouvert

- **O1 🟠 — Langues runtime supplémentaires.** L'allemand et l'anglais sont
  sélectionnables dans l'app. Les langues existantes de documentation
  (es/fr/uk/zh) ne sont pas encore des runtime locales ; au besoin, les ajouter
  clé par clé dans `bgremover.i18n` et les protéger par des tests de
  parité/smoke.

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-04)

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#168](https://github.com/NikolayDA/picture_helper/issues/168) | Audit de la suite de tests : tests obsolètes, assertions manquantes, couplage privé, lacunes de couverture | 🔴 Haute | 🔴 Haute | Constats 🔴 → Prêts pour PR immédiatement ; reste : diviser et affiner |
| [#167](https://github.com/NikolayDA/picture_helper/issues/167) | Revue de code : qualité, maintenabilité et problèmes mineurs | 🔴 Haute | 🟡 Moyenne | Constats Medium (race, TOCTOU) → Prêts pour PR ; constats Low : regrouper |
| [#164](https://github.com/NikolayDA/picture_helper/issues/164) | Revue de docs : INSTALL_MAC.md & INSTALL_LINUX.md — 4 problèmes | 🔴 Haute | 🟢 Basse | PR #172 ouvert |
| [#163](https://github.com/NikolayDA/picture_helper/issues/163) | CHANGELOG.md : liens de version brisés + entrées 2.3.0 manquantes | 🔴 Haute | 🟡 Moyenne | Modifications de contenu → Prêtes pour PR ; tags git à affiner séparément |
| [#165](https://github.com/NikolayDA/picture_helper/issues/165) | TESTING.md : trois inexactitudes par rapport au code actuel | 🟡 Moyenne | 🟢 Basse | Prêt pour PR |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | Audit README : un lien externe brisé, une référence interne | 🟡 Moyenne | 🟢 Basse | Correction de « Runde 5 » → Prête pour PR ; URL de clonage → Bloquée (décision de visibilité du dépôt) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Audit des commentaires : incohérences de langue et imprécision mineure | 🟢 Basse | 🟢 Basse | Prêt pour PR |

### Ordre de PR Recommandé

1. **#164** — Docs d'installation (note IA Python 3.11, lien releases + chaînes UI localisées) : implémenté dans **PR #172** (les six versions linguistiques ; fusion en attente).
2. **#168 🔴** — `test_canvas_events.py:174` (assertion locale déjà cassée en CI) et `test_async_load.py:34` (assertion OR faible) : PR de bugfix ciblé.
3. **#167 Medium** — Verrou double-vérification dans `_ensure_rembg_remove()` + fenêtre TOCTOU dans `open_validated_image` : PR de bugfix propre.
4. **#165** — Corrections de TESTING.md : faible risque et bien délimité.
5. **#163 contenu** — Ajouter les features 2.3.0 manquantes + entrées `[Unreleased]` dans CHANGELOG ; gérer les tags git séparément.
6. **#161 partiel** — Supprimer le jargon « Runde 5 » du texte d'architecture du README (correction de l'URL de clonage nécessite une décision de visibilité du dépôt).
7. **#166** — Nettoyage de langue dans les docstrings en tant que petit PR de maintenance.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée
  lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
