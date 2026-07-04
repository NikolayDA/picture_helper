[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-05)

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests
locale restent la base avant tout nouveau PR. Depuis l'instantané du
2026-07-04, le groupe d'alignement Dark Mode/prototype **#474–#480** (PR #482)
et la vague icônes du rail/couleurs d'état **#483–#488** (PR #489) sont fermés.
Avant ce suivi, GitHub affiche **12** tickets ouverts dont **#490** ; après la
fusion/clôture de ce correctif d'instantané, il restera **11** tickets de
roadmap/backlog.

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
  `tests/test_workflow.py`).
- **Vague rail/zoom terminée :** **#455/#456/#457/#458/#463/#464** ont atterri
  via PR #466, et **#465** est volontairement `not_planned` ; PR #467 a fermé
  les trois P2 de #466 et actualisé l'instantané de triage.
- **Inspecteur en cartes terminé :** **#414** a atterri via PR #473 (jetons
  `CARD_*` centraux, style de carte clair/sombre, garde anti-hex d'accent).
  Cela termine aussi l'epic **#413**.
- **Dark Mode et icônes du rail terminés :** PR #482 ferme **#474–#480**
  (surfaces dark, hairlines, accents, checkerboard, jetons manquants, test de
  dérive REDESIGN_SPEC) ; PR #489 ferme **#483–#488** (icônes vectorielles,
  couleurs d'état/thème, fallbacks PNG retirés, docs/tests/revue).
- **#490 en cours :** Cette PR corrige la dérive de l'instantané Recommendations
  après PR #482/#489 et garde synchronisés les six miroirs de langue.

### Encore ouvert

- **O1 🟠 — Langues d'exécution supplémentaires.** L'allemand et l'anglais sont
  commutables ; es/fr/uk/zh ne sont pas encore des locales d'exécution.
  Correspond au ticket de redesign **#430** — les ajouter clé par clé dans
  `bgremover.i18n` et les couvrir par des tests.
- **O8 🟢 — Imprécision du prototype : les outils de hauteur restent
  verrouillés après génération.** Dans `design/Prototyp A - Geführter
  Workflow.dc.html`, « Générer la carte de hauteur à partir de l'image » ne
  fait qu'activer `heightGen` sans basculer le calque actif sur le rôle
  `Höhe` — `heightDisabled` reste lié à l'ancien rôle (constat de revue sur
  la PR #460). N'affecte que la simulation de la maquette ; l'application
  réelle active déjà automatiquement le nouveau calque HEIGHT (#347).

## Tickets GitHub ouverts — Triage (2026-07-05)

Au 2026-07-05, GitHub affiche **12** tickets ouverts avant cette PR, dont
**#490**. Après fusion/clôture de ce suivi, il restera **11** tickets de
roadmap/backlog : i18n/docs (**#425/#430/#431/#432**), rollout/publication
(**#426/#435/#392/#389**) et backlog/points externes (**#299/#318/#245**).

### Regroupements pertinents

- **#490 :** Cette PR clôt la dérive d'instantané après PR #482/#489 ; aucun
  ticket d'implémentation de suivi n'en découle.
- **i18n/docs (#425) :** #430 (ES/FR/UK/ZH) débloque les tests de parité ; #431
  (docs) et #432 (captures) suivent quand l'UI sera visuellement définitive.
- **Rollout/publication :** #426 ne reste ouvert que via #435 ; coordonner #435
  avec #392, puis clore #426/#389.
- **Backlog :** traiter #299 après la publication ; affiner #318 d'abord ; #245
  reste bloqué par la facturation/le quota OpenAI.

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs,
**Complexité** = effort de mise en œuvre estimé.

| # | Titre | Pertinence | Complexité | Prochaine étape recommandée |
|---|-------|------------|------------|-----------------------------|
| [#490](https://github.com/NikolayDA/picture_helper/issues/490) | Actualiser le snapshot de triage après Dark Mode et icônes rail | 🟡 Moyenne | 🟢 Faible | **Cette PR** – fermer après merge. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC : Internationalisation et documentation | 🟠 Élevée | 🟡 Moyenne | **En cours** – #430/#431/#432 ouverts. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | Nouvelles chaînes d'UI (étapes/cartes/navigation) | 🟠 Élevée | 🟡 Moyenne | **Prêt pour PR** – ES/FR/UK/ZH ; DE/EN via PR #423. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Mettre ANLEITUNG et README au workflow guidé | 🟡 Moyenne | 🟡 Moyenne | **Après gel de l'UI** – miroir en 6 langues. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Refaire les captures de l'app pour le redesign | 🟢 Faible | 🟢 Faible | **Bloqué** – seulement quand l'UI est définitive. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC : QA et déploiement du redesign | 🟠 Élevée | 🟢 Faible | **Presque fini** – seul #435 reste ouvert. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG et bump de version du redesign | 🟡 Moyenne | 🟢 Faible | **Aligner sur #392** – définir la séquence. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Publier la version v2.5.0 | 🟠 Élevée | 🟡 Moyenne | **Prête** – décider la séquence avec le redesign. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC : Màj docs utilisateur et publication | 🟠 Élevée | 🟢 Faible | **Clore après #392** – seule la publication reste. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | 🟢 Faible | 🟢 Faible | **Après la publication** – plus fort impact d'abord. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Overrides de permissions par job dans WF réutilisable | 🟢 Faible | 🟡 Moyenne | **À affiner** – prouver la sémantique GitHub. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan « Quota exceeded » | 🟡 Moyenne | 🟢 Faible | **Bloqué (externe)** – facturation/quota OpenAI. |

### Recommandé ensuite (ordre des PR)

1. Avancer **#430** (chaînes ES/FR/UK/ZH) — débloque la parité i18n ; puis
   **#431**/**#432** quand l'UI est définitive.
2. **Publication :** mener **#435** + **#392** de façon coordonnée, puis clore les
   epics **#426** et **#389**.
3. **#299** après la publication ; n'étudier que **#318** (à affiner) ; garder
   **#245** bloqué en externe.

## Tours précédents

- **Triage 2026-06-29** — #404/#406/#408 achevés (PR #412), vague de redesign ouverte.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, achevée ou écartée en cas de faux positif.

Constats historiques et journaux de travail (tours 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
