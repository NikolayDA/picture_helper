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
- **#164** est terminé et fusionné (PR #172) : note IA Python 3.11, lien
  releases et chaînes UI localisées dans les guides d'installation.
- **#167 / #168** sont clos : les constats High/Medium ont été livrés via
  PR #173/#174 ; le reste se poursuit de façon ciblée dans #176/#177/#178.

### Encore Ouvert

- **O1 🟠 — Langues runtime supplémentaires.** L'allemand et l'anglais sont
  sélectionnables dans l'app. Les langues existantes de documentation
  (es/fr/uk/zh) ne sont pas encore des runtime locales ; au besoin, les ajouter
  clé par clé dans `bgremover.i18n` et les protéger par des tests de
  parité/smoke.

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-05)

8 issues ouvertes, toutes `documentation` ou `quality/testing`. Aucun bug de
code ouvert (🔴) : les constats critiques de #167/#168 ont été livrés via
#173/#174 ; il reste des corrections de documentation et du durcissement de
tests.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#163](https://github.com/NikolayDA/picture_helper/issues/163) | CHANGELOG.md : liens de version brisés + entrées 2.3.0 manquantes | 🔴 Haute | 🟡 Moyenne | Modifications de contenu → Prêtes pour PR ; tags git à affiner séparément |
| [#177](https://github.com/NikolayDA/picture_helper/issues/177) | Suite de l'audit de tests (Medium) : assertions comportementales + lacunes de couverture | 🟠 Haute | 🟡 Moyenne | Prêt pour PR (de #168) ; commentaire 2026-06-05 ajoute `history_popup.py` (35 % couverture) |
| [#165](https://github.com/NikolayDA/picture_helper/issues/165) | TESTING.md : trois inexactitudes par rapport au code actuel | 🟡 Moyenne | 🟢 Basse | Prêt pour PR ; regrouper avec #180 |
| [#180](https://github.com/NikolayDA/picture_helper/issues/180) | TESTING.md : deux inexactitudes (filtre addopts, ligne coverage manquante) | 🟡 Moyenne | 🟢 Basse | Prêt pour PR ; chevauche #165 (addopts) — à faire ensemble |
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | Suite de la revue de code (Low) : E741, check_untyped_defs, UX de cancel_ai, shutdown_all | 🟡 Moyenne | 🟢 Basse | Prêt pour PR (de #167) |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | Audit README : un lien externe brisé, une référence interne | 🟡 Moyenne | 🟢 Basse | Partiellement bloqué : jargon « Runde 5 » corrigé ; URL de clonage reportée (décision de l'owner) |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | Suite de l'audit de tests (Low) : découpler des internals privés + dédupliquer | 🟢 Basse | 🟡 Moyenne | Prêt pour PR (de #168) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Audit des commentaires : incohérences de langue et imprécision mineure | 🟢 Basse | 🟢 Basse | Prêt pour PR |

### Ordre de PR Recommandé

1. **#165 + #180** — Corrections de TESTING.md regroupées (les deux touchent le filtre `addopts`) : faible risque et bien délimité.
2. **#163 contenu** — Ajouter les features 2.3.0 manquantes + entrées `[Unreleased]` dans CHANGELOG ; gérer les tags git séparément.
3. **#177** — Durcissement des tests : ajouter des assertions comportementales + combler les lacunes de couverture, incl. `history_popup.py` (de #168).
4. **#176** — Lot qualité de code de #167 : E741, check_untyped_defs, UX de cancel_ai, shutdown_all.
5. **#178** — Découpler les tests des internals privés + réduire les tests en double (de #168).
6. **#166** — Nettoyage de langue dans les docstrings en tant que petit PR de maintenance.
7. **#161 reporté** — « Runde 5 » fait ; il ne reste que l'URL de clonage (décision de l'owner sur la visibilité du dépôt).

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée
  lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
