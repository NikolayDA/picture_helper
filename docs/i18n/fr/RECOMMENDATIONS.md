[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-04)

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests
locale restent la base avant tout nouveau PR. Nouveauté de ce tour : **#461**,
**#414** et l'epic **#413** sont fermés. La PR #473 centralise les métriques de
cartes et supprime le dernier hex d'accent hors de `theme.py`. Le nouveau groupe
ouvert d'alignement Dark Mode/prototype est **#474–#480**. GitHub affiche
désormais **18** tickets ouverts de roadmap/backlog.

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
  via PR #466, et **#465** est volontairement `not_planned`. Le PR #467 ferme
  les trois P2 tardifs de #466 (direction du zoom, ancrage au viewport, aperçu
  des dabs de hauteur) et a actualisé l'instantané de triage.
- **#461 fermé (2026-07-04) :** L'instantané actualisé par le PR #467
  correspond à l'état réel de GitHub ; le ticket lui-même était resté ouvert
  après la fusion et est fermé dans ce tour.
- **Inspecteur en cartes terminé :** **#414** a atterri via PR #473 (jetons
  `CARD_*` centraux, style de carte clair/sombre, garde anti-hex d'accent).
  Cela termine aussi l'epic **#413**.

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

## Tickets GitHub ouverts — Triage (2026-07-04)

Au 2026-07-04, GitHub affiche **18** tickets ouverts de roadmap/backlog :
alignement Dark Mode/prototype (**#474/#475/#476/#477/#478/#479/#480**),
i18n/docs (**#425/#430/#431/#432**), rollout/publication
(**#426/#435/#392/#389**) et les points indépendants **#299/#318/#245**.
**#461** était la dérive d'instantané déjà résolue ; **#414** et **#413** sont
aussi fermés après PR #473.

### Regroupements pertinents

- **Dark Mode 1:1 (#474) :** regrouper #475/#476/#477/#479 comme vague de tokens,
  #478 comme correctif du checker canvas et #480 comme passe finale spec/drift.
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
| [#474](https://github.com/NikolayDA/picture_helper/issues/474) | EPIC : Dark Mode 1:1 avec Prototype A | 🟠 Élevée | 🟡 Moyenne | **Nouveau** – grouper #475–#480. |
| [#475](https://github.com/NikolayDA/picture_helper/issues/475) | Dark : aligner les surfaces de fond | 🟠 Élevée | 🟢 Faible | **Commencer ici** – bases d'abord. |
| [#476](https://github.com/NikolayDA/picture_helper/issues/476) | Dark : bordures/hairlines transparentes | 🟡 Moyenne | 🟢 Faible | **Avec #475** – tokens de bord. |
| [#477](https://github.com/NikolayDA/picture_helper/issues/477) | Dark : aligner accents/boutons | 🟠 Élevée | 🟢 Faible | **Avec #475** – couleurs interactives. |
| [#478](https://github.com/NikolayDA/picture_helper/issues/478) | Checker canvas ignore le thème | 🟡 Moyenne | 🟡 Moyenne | **Après tokens** – palette + thème. |
| [#479](https://github.com/NikolayDA/picture_helper/issues/479) | Ajouter les tokens couleur manquants | 🟡 Moyenne | 🟡 Moyenne | **Avec spec** – tokens prouvés. |
| [#480](https://github.com/NikolayDA/picture_helper/issues/480) | Tables couleur REDESIGN_SPEC + test drift | 🟡 Moyenne | 🟡 Moyenne | **Passe finale** – après #475–#479. |
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

1. Grouper **#474** : vague de tokens #475/#476/#477/#479, puis #478 et #480.
2. Avancer **#430** (chaînes ES/FR/UK/ZH) — débloque la parité i18n ; puis
   **#431**/**#432** quand l'UI est définitive.
3. **Publication :** mener **#435** + **#392** de façon coordonnée, puis clore les
   epics **#426** et **#389**.
4. **#299** après la publication ; n'étudier que **#318** (à affiner) ; garder
   **#245** bloqué en externe.

## Tours précédents

- **Triage 2026-06-29** — #404/#406/#408 achevés (PR #412), vague de redesign ouverte.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, achevée ou écartée en cas de faux positif.

Constats historiques et journaux de travail (tours 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
