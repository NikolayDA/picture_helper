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

La liste active d'analyse de code est vide. Ruff, mypy et la suite locale
restent la baseline avant de nouveaux PRs.

### Terminé Depuis La Dernière Revue

- **N1/N2/N4/N5/N6/N7/N8** sont terminés : chemins d'erreur, limite de taille,
  extensions, sauvegarde atomique, paquets Qt CI, import paresseux et docstring.
- **O2/O3/O4/O5/O6** sont implémentés : paquets Linux, workflow de release,
  matrice complète, `ui_smoke` et raccourcis adaptés aux plateformes.
- Les constats **#163–#206** ont été clos dans les PRs documentés et protégés
  par des tests de régression ou des contrôles CI.

### Encore Ouvert

- **O1 🟠 — Langues runtime supplémentaires.** L'allemand et l'anglais sont
  sélectionnables dans l'app. Les langues documentaires es/fr/uk/zh ne sont pas
  des locales runtime ; les ajouter clé par clé dans `bgremover.i18n` et tester.

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-14)

Après triage, **13** issues restent ouvertes. **#203/#204** ont été closes en
`not planned` car elles ne sont pas des dépendances du projet ; **#226/#244**
étaient déjà résolues par les PR #246 et #256. Onze issues ont un périmètre
implémentable dans le dépôt. #161 exige une décision de publication et #245
demande surtout une correction de quota/facturation côté compte.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README : l'URL de clonage renvoie 404 aux utilisateurs anonymes | 🟢 Basse | 🟢 Basse | « Runde 5 » est corrigé ; décider public vs. privé/sur invitation avant de changer le clonage |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` peut interrompre les workers de façon non sûre | 🟠 Haute | 🟡 Moyenne | Première PR : borner le second wait, journaliser et tester l'échec ; traiter le sous-processus séparément |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` charge toute la GUI PyQt6 | 🟡 Moyenne | 🟡 Moyenne | Prêt pour PR : préserver l'API publique avec des exports paresseux PEP 562 et ajouter un test de régression d'import |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Une migration manquante incrémente quand même `schema_version` | 🟡 Moyenne | 🟢 Basse | Regrouper avec #259 : une migration absente ne doit ni marquer ni modifier les settings |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | La limite mémoire d'undo exclut la pile redo | 🟢 Basse | 🟡 Moyenne | Budget undo/redo partagé ; seulement mesurer/documenter l'original et la mémoire Qt |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec « Quota exceeded » | 🟡 Moyenne | 🟢 Basse | Corriger le quota côté compte ; dans le dépôt, clarifier l'échec, sans changement `setup-node` |
| [#248](https://github.com/NikolayDA/picture_helper/issues/248) | Échap efface la sélection au lieu d'annuler le lasso polygonal | 🟡 Moyenne | 🟡 Moyenne | Regrouper avec #260 : priorité centrale crop → lasso → effacer la sélection |
| [#249](https://github.com/NikolayDA/picture_helper/issues/249) | Les associations de fichiers transmettent des chemins mais l'app ne les ouvre pas | 🟡 Moyenne | 🟡 Moyenne | Prêt pour PR : ouvrir les chemins de démarrage et le `QFileOpenEvent` macOS via le chemin de chargement validé |
| [#257](https://github.com/NikolayDA/picture_helper/issues/257) | Suivis release : contexte publish, tag gate et artefacts de relance | 🟠 Haute | 🟡 Moyenne | PR prioritaire autonome avant le prochain tag ; workflow, docs et tests ensemble |
| [#258](https://github.com/NikolayDA/picture_helper/issues/258) | La limite de chargement peut préallouer 512 Mio | 🟠 Haute | 🟡 Moyenne | PR autonome : lecture par blocs, erreur localisée et limite affichée précisément |
| [#259](https://github.com/NikolayDA/picture_helper/issues/259) | Recent Files modifie un schéma futur | 🟠 Haute | 🟡 Moyenne | Regrouper avec #234 : garder les schémas futurs en lecture seule |
| [#260](https://github.com/NikolayDA/picture_helper/issues/260) | L'abandon automatique du crop laisse le mauvais curseur | 🟡 Moyenne | 🟢 Basse | Regrouper avec #248 et tester annulation centrale plus restauration du curseur |
| [#261](https://github.com/NikolayDA/picture_helper/issues/261) | L'overlay du pinceau scanne tout le masque à chaque mouvement | 🟡 Moyenne | 🟡 Moyenne | PR performance autonome avec compteur de pixels et spy test |

### Ordre de PR Recommandé

1. **#257** — fiabiliser le workflow de release avant le prochain tag.
2. **#258** — supprimer la préallocation et corriger les erreurs de taille.
3. **#234 + #259** — migration QSettings et protection du schéma futur.
4. **#248 + #260** — annulation centrale Échap/crop et curseur correct.
5. **#231** — livrer un fallback borné ; sous-processus dans un travail ultérieur.
6. **#261** — retirer le scan O(taille image) du chemin fréquent du pinceau.
7. **#249** — traiter les associations et événements open de macOS.
8. **#232** — imports légers via des exports paresseux PEP 562.
9. **#235** — implémenter un budget historique undo/redo partagé.
10. **#245** — restaurer le quota à l'extérieur ; durcissement du workflow séparé.
11. **#161** — décider la publication, puis modifier la doc ou clore.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
