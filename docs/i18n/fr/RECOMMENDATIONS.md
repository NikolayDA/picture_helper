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

Il reste **15** issues ouvertes. La revue des descriptions, du code, des tests
et de la documentation montre : **neuf** constats sont bien cadrés et prêts pour
une PR, deux (#231/#235) requièrent d'abord une décision d'architecture ou de
périmètre, #245 est un problème d'infrastructure/facturation (pas un défaut de
code) et trois (#161/#203/#204) ne démontrent pas de tâche pour ce dépôt sans
preuve supplémentaire.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README : l'URL de clonage renvoie 404 aux utilisateurs anonymes | 🟢 Basse | 🟢 Basse | L'URL HTTPS est correcte ; fermer en `not planned` tant que le dépôt est privé, ou définir le mode de publication |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — collection de CVE | 🟢 Basse | 🟢 Basse | Absent du snapshot du projet ; fermer en `not planned` sans chemin de dépendance reproductible et ne pas conserver les sévérités erronées |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | PyJWT 2.7.0 — collection de CVE | 🟢 Basse | 🟢 Basse | Absent du snapshot ; fermer en `not planned` sans chemin reproductible, puis corriger les sévérités et le lien GHSA cassé |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | Revue INSTALL : releases, Raspberry Pi et diagnostic macOS | 🟡 Moyenne | 🟢 Basse | Prêt pour PR : les trois constats restent valides ; corriger le document racine et cinq traductions avec une note honnête sur les artefacts |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` peut interrompre les workers de façon non sûre | 🟡 Moyenne | 🟠 Haute | À affiner : les appels natifs bloquants exigent un choix d'architecture (sous-processus) ; le test actuel conserve le défaut |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` charge toute la GUI PyQt6 | 🟡 Moyenne | 🟡 Moyenne | Prêt pour PR : préserver l'API publique avec des exports paresseux PEP 562 et ajouter un test de régression d'import |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Une migration manquante incrémente quand même `schema_version` | 🟡 Moyenne | 🟢 Basse | Prêt pour PR : empêcher l'avancement de version, inverser le test et définir la sémantique de la version 0 |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | La limite mémoire d'undo exclut la pile redo | 🟢 Basse | 🟡 Moyenne | À affiner : réduire le périmètre à un budget undo/redo partagé ; inclure l'image d'origine et les allocations Qt seulement après mesure |
| [#244](https://github.com/NikolayDA/picture_helper/issues/244) | Code mort : `ImageCanvas._zoom` et le wrapper `launch_worker` inutilisé | 🟢 Basse | 🟢 Basse | Prêt pour PR : supprimer `_zoom`, décider suppression vs. API documentée pour `launch_worker` ; petite PR de nettoyage |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec « Quota exceeded » | 🟡 Moyenne | 🟢 Basse | Infrastructure/facturation : restaurer le quota OpenAI côté compte ; rendre le workflow résilient aux ruptures de quota et passer `setup-node` à Node 24 |
| [#247](https://github.com/NikolayDA/picture_helper/issues/247) | Un crop actif survit aux transformations et produit de mauvais pixels | 🟠 Haute | 🟡 Moyenne | Prêt pour PR (prioritaire) : réinitialiser l'état transitoire à chaque changement d'image ; test de régression (400×200 + rotation 90°) décrit dans l'issue |
| [#248](https://github.com/NikolayDA/picture_helper/issues/248) | Échap efface la sélection au lieu d'annuler le lasso polygonal | 🟡 Moyenne | 🟡 Moyenne | Prêt pour PR : priorité d'Échap crop → lasso → effacer la sélection ; partage le contrat d'état transitoire avec #247 |
| [#249](https://github.com/NikolayDA/picture_helper/issues/249) | Les associations de fichiers transmettent des chemins mais l'app ne les ouvre pas | 🟡 Moyenne | 🟡 Moyenne | Prêt pour PR : ouvrir les chemins de démarrage et le `QFileOpenEvent` macOS via le chemin de chargement validé |
| [#250](https://github.com/NikolayDA/picture_helper/issues/250) | Le workflow de release publie des artefacts sans gate CI complet | 🟠 Haute | 🟡 Moyenne | Prêt pour PR (avant le prochain tag) : imposer la CI complète via `needs`, vérifier tag/`project.version`, retirer `\|\| true` |
| [#251](https://github.com/NikolayDA/picture_helper/issues/251) | Une sélection vide conserve la QPixmap d'overlay après effacement | 🟡 Moyenne | 🟢 Basse | Prêt pour PR (rapide) : libérer la pixmap d'overlay quand le masque est vide ; correctif exact dans l'issue |

### Ordre de PR Recommandé

1. **#247** — Haute : bug de correction/données (un rectangle de crop périmé génère des pixels transparents) ; entièrement cadré, avec test de régression.
2. **#250** — Haute avant le prochain tag de release : imposer le gate CI complet via `needs`, réconcilier tag/version, retirer `|| true`.
3. **#251** — correctif mémoire rapide : un masque vide libère la pixmap d'overlay ; le correctif exact est dans l'issue.
4. **#244** — nettoyage de code mort (supprimer `_zoom`, décider pour `launch_worker`) ; petite PR à faible risque.
5. **#234** — empêcher l'avancement de version si une migration manque et corriger le test qui attend actuellement l'inverse.
6. **#248** — priorité d'Échap crop → lasso → effacer la sélection ; partage le contrat d'état transitoire avec #247 et peut être regroupé.
7. **#232** — exports paresseux PEP 562 avec un test de régression d'import.
8. **#249** — ouvrir les chemins de démarrage et le `QFileOpenEvent` macOS via le chemin de chargement validé.
9. **#226** — correctif documentaire dans les six langues ; documenter honnêtement la disponibilité des releases.
10. **#245** — restaurer la facturation OpenAI côté compte ; rendre le workflow de scan résilient aux ruptures de quota et passer `setup-node` à Node 24.
11. **#231** — choisir d'abord le modèle d'annulation (sous-processus pour les appels natifs durablement bloqués), puis implémenter.
12. **#235** — implémenter un budget mémoire undo/redo partagé seulement après définition du périmètre.
13. **#161/#203/#204** — fermer en `not planned` sauf si un chemin concret de publication ou de dépendance est fourni.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
