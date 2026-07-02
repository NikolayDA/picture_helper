[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-02)

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests
locale restent la base avant tout nouveau PR. Nouveauté de ce tour : le triage
des tickets ouverts est remis au niveau réel (18 tickets ouverts).

### Terminé depuis la dernière revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8** et **O2–O7** restent faits ;
  les epics **#329/#344/#358/#384** (N9–N12) plus le correctif d'export **#363**
  sont fusionnés, couverts par les tests/CI et archivés.
- **Fermés depuis la revue du 2026-06-25 :** **#404**, **#406** et **#408**
  (PR #412) — les constats aperçu/code mort/audit sont faits ;
  `_derive_physical_size` n'existe plus et le chemin de rendu se rabat sur COLOR
  en cas d'écart de taille.
- **Cœur du redesign livré :** la barre d'étapes/`stepper.py`, l'inspecteur en
  cartes, la navigation guidée, les outils contextuels et les jetons de design
  (`ACCENT`/`CARD_STYLE`) ont atterri via PR #412/#423 (chaînes DE/EN,
  `tests/test_workflow.py`) ; il ne reste que le peaufinage (voir le triage).

### Encore ouvert

- **O1 🟠 — Langues d'exécution supplémentaires.** L'allemand et l'anglais sont
  commutables ; es/fr/uk/zh ne sont pas encore des locales d'exécution.
  Correspond au ticket de redesign **#430** — les ajouter clé par clé dans
  `bgremover.i18n` et les couvrir par des tests.

## Tickets GitHub ouverts — Triage (2026-07-02)

Au 2026-07-02, GitHub affiche **18** tickets ouverts. L'instantané du 2026-06-29
est périmé : #404/#406/#408 sont fermés (PR #412), et la **vague de redesign
(workflow guidé)** est la feuille de route active. Son cœur est déjà livré ; il
reste le peaufinage (**#414**), i18n/docs (epic **#425** : #430/#431/#432),
QA/déploiement (epic **#426** : #433/#434/#435), la publication en attente
**#392** et les points indépendants **#299/#318/#245**. **#442** suit précisément
cette mise à jour de documentation.

**Revue des commentaires :** Aucun nouveau commentaire externe. Les notes du
propriétaire sur #245/#299/#392 correspondent à l'état actuel ; #442 (2026-07-02)
consigne cet audit — aucune mise à jour de ticket nécessaire.

### Regroupements pertinents

- **Epics presque finis :** #418 et #424 ont **tous** leurs sous-tickets fermés →
  vérifier et clore. #413 n'a plus que #414 ouvert ; ses jetons sont déjà dans
  `theme.py` — ajouter le style de carte clair, puis clore.
- **i18n/docs (#425) :** #430 (ES/FR/UK/ZH) débloque les tests de parité ; #431
  (docs) et #432 (captures) suivent quand l'UI sera visuellement définitive.
- **QA/déploiement (#426) :** #433 est largement couvert par PR #423 (vérifier
  l'écart, clore) ; #434 est prêt pour PR ; aligner #435 (CHANGELOG/version) sur #392.
- **Publication :** décider si le redesign sort en **v2.5.0** (#392/#435 ensemble)
  ou dans un incrément ultérieur.

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs,
**Complexité** = effort de mise en œuvre estimé.

| # | Titre | Pertinence | Complexité | Prochaine étape recommandée |
|---|-------|------------|------------|-----------------------------|
| [#418](https://github.com/NikolayDA/picture_helper/issues/418) | EPIC : Workflow guidé – barre d'étapes et navigation | 🟠 Élevée | 🟢 Faible | **Vérifier et clore** – sous-tickets fermés (PR #423). |
| [#413](https://github.com/NikolayDA/picture_helper/issues/413) | EPIC : Inspecteur en cartes – colonne droite | 🟠 Élevée | 🟢 Faible | **Presque fini** – seul #414 ouvert. |
| [#414](https://github.com/NikolayDA/picture_helper/issues/414) | Centraliser conteneur de carte et jetons d'accent | 🟡 Moyenne | 🟢 Faible | **Prêt pour PR** – jetons présents ; style clair à ajouter. |
| [#424](https://github.com/NikolayDA/picture_helper/issues/424) | EPIC : Système de design unifié et theming | 🟠 Élevée | 🟢 Faible | **Vérifier et clore** – sous-tickets fermés. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC : Internationalisation et documentation | 🟠 Élevée | 🟡 Moyenne | **En cours** – #430/#431/#432 ouverts. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | Nouvelles chaînes d'UI (étapes/cartes/navigation) | 🟠 Élevée | 🟡 Moyenne | **Prêt pour PR** – ES/FR/UK/ZH ; DE/EN via PR #423. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Mettre ANLEITUNG et README au workflow guidé | 🟡 Moyenne | 🟡 Moyenne | **Après gel de l'UI** – miroir en 6 langues. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Refaire les captures de l'app pour le redesign | 🟢 Faible | 🟢 Faible | **Bloqué** – seulement quand l'UI est définitive. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC : QA et déploiement du redesign | 🟠 Élevée | 🟢 Faible | **En cours** – #433/#434/#435 ouverts. |
| [#433](https://github.com/NikolayDA/picture_helper/issues/433) | Tests de fumée étapes/cartes/navigation | 🟡 Moyenne | 🟢 Faible | **Vérifier l'écart** – largement couvert par PR #423. |
| [#434](https://github.com/NikolayDA/picture_helper/issues/434) | Régression visibilité et câblage des actions | 🟡 Moyenne | 🟢 Faible | **Prêt pour PR** – callbacks d'action par étape. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG et bump de version du redesign | 🟡 Moyenne | 🟢 Faible | **Aligner sur #392** – définir la séquence. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Publier la version v2.5.0 | 🟠 Élevée | 🟡 Moyenne | **Prête** – décider la séquence avec le redesign. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC : Màj docs utilisateur et publication | 🟠 Élevée | 🟢 Faible | **Clore après #392** – seule la publication reste. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | 🟢 Faible | 🟢 Faible | **Après la publication** – plus fort impact d'abord. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Overrides de permissions par job dans WF réutilisable | 🟢 Faible | 🟡 Moyenne | **À affiner** – prouver la sémantique GitHub. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan « Quota exceeded » | 🟡 Moyenne | 🟢 Faible | **Bloqué (externe)** – facturation/quota OpenAI. |
| [#442](https://github.com/NikolayDA/picture_helper/issues/442) | RECOMMENDATIONS.md est périmé | 🟡 Moyenne | 🟢 Faible | **Résolu par cette mise à jour** – peut être clos. |

### Recommandé ensuite (ordre des PR)

1. **Maintenance :** vérifier les sous-tickets et clore les epics presque finis
   **#418** et **#424** ; finir **#414** (style clair), puis clore **#413**.
2. Avancer **#430** (chaînes ES/FR/UK/ZH) — débloque la parité i18n ; puis
   **#431**/**#432** quand l'UI est définitive.
3. Implémenter **#434** (régression) ; confirmer la couverture de **#433** de
   PR #423 et la clore.
4. **Publication :** mener **#435** + **#392** de façon coordonnée, puis clore les
   epics **#426** et **#389**.
5. **#299** après la publication ; n'étudier que **#318** (à affiner) ; garder
   **#245** bloqué ; clore **#442** une fois cette mise à jour intégrée.

## Tours précédents

- **Triage 2026-06-29** — #404/#406/#408 achevés (PR #412), vague de redesign ouverte.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, achevée ou écartée en cas de faux positif.

Constats historiques et journaux de travail (tours 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
