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

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée
  lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
