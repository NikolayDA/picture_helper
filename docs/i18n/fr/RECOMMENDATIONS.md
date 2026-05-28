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

## État actuel (2026, après la série 5)

La découpe monolithe→package est terminée : `BgRemover.py` a été remplacé par le package `bgremover/`. L'état du canvas est encapsulé dans `CanvasHistory`, `CanvasLasso` et `CanvasSelection` ; `MainWindow` est séparé en toolbar, popup d'historique, worker controller, RightPanel, MenuActions et RecentFiles. Les tests ne dépendent plus des champs privés du Canvas, et mypy s'exécute sans les anciennes classes d'erreurs désactivées par code.

Les constats historiques complets et journaux de travail des séries 1-5 sont archivés dans [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).

---

## Points de polissage ouverts

| Priorité | Recommandation | Effort | État |
|----------|----------------|--------|------|
| 🟢 | Ajouter les classifiers Python 3.11/3.13 | Petit | Ouvert |
| 🟡 | Revoir le périmètre linguistique de `CHANGELOG.md` ; alternative : garder DE/EN comme canoniques et lier les autres langues, car les changelogs dérivent vite | Petit | Ouvert |
| 🟢 | Unifier la langue de documentation là où les modules mélangent DE/EN | Moyen | Ouvert |
