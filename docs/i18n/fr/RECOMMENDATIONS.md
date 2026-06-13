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

Il reste **8** issues ouvertes. La revue des descriptions, du code, des tests et
de la documentation confirme cinq constats actionnables. Trois issues
(#161/#203/#204) ne démontrent pas de tâche pour ce dépôt sans preuve
supplémentaire et devraient être fermées ou complétées par une reproduction.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README : l'URL de clonage renvoie 404 aux utilisateurs anonymes | 🟢 Basse | 🟢 Basse | L'URL HTTPS est correcte ; fermer en `not planned` tant que le dépôt est privé, ou définir le mode de publication |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — collection de CVE | 🟢 Basse | 🟢 Basse | Absent du snapshot du projet ; fermer en `not planned` sans chemin de dépendance reproductible et ne pas conserver les sévérités erronées |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | PyJWT 2.7.0 — collection de CVE | 🟢 Basse | 🟢 Basse | Absent du snapshot ; fermer en `not planned` sans chemin reproductible, puis corriger les sévérités et le lien GHSA cassé |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | Revue INSTALL : releases, Raspberry Pi et diagnostic macOS | 🟡 Moyenne | 🟢 Basse | Les trois constats restent valides ; corriger le document racine et cinq traductions avec une note honnête sur les artefacts |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` peut interrompre les workers de façon non sûre | 🟡 Moyenne | 🟠 Haute | Constat pertinent de sûreté/stabilité ; les appels natifs bloquants exigent un choix d'architecture et le test actuel conserve le défaut |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` charge toute la GUI PyQt6 | 🟡 Moyenne | 🟡 Moyenne | Correct, suffisamment documenté et prêt pour PR ; préserver l'API publique avec des exports paresseux PEP 562 |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Une migration manquante incrémente quand même `schema_version` | 🟡 Moyenne | 🟢 Basse | Bug confirmé ; inverser le test et définir explicitement la sémantique de la version 0 avant de vraies migrations |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | La limite mémoire d'undo exclut la pile redo | 🟢 Basse | 🟡 Moyenne | Réduire le périmètre à un budget undo/redo partagé ; inclure l'image d'origine et les allocations Qt seulement après mesure |

### Ordre de PR Recommandé

1. **#226** — petit correctif documentaire confirmé dans les six langues ; décider ou préciser clairement la disponibilité des releases.
2. **#232** — exports paresseux PEP 562 avec tests de régression d'import ; aucune clarification supplémentaire requise.
3. **#234** — empêcher l'avancement de version si une migration manque et corriger le test qui attend actuellement l'inverse.
4. **#231** — choisir d'abord le modèle d'annulation ; un sous-processus est robuste pour les appels natifs bloqués durablement.
5. **#235** — implémenter éventuellement un budget mémoire undo/redo partagé après définition du périmètre.
6. **#161/#203/#204** — fermer en `not planned` sauf si un chemin concret de publication ou de dépendance est fourni.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
