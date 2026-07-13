[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-13)

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests
locale restent la base avant tout nouveau PR. La version **v2.5.0** a été
publiée le 2026-07-11 (PR #538) ; la vague de rollout **#435/#392/#426/#389**
est close, ainsi que **#299** (PR #539) avec le suivi N13 **#541** (PR #543),
**#318** (PR #540) et la synchronisation d'instantané **#542**. Un audit du
dépôt du 2026-07-12 a ouvert **#549–#553** ; **#552/#549/#553/#550** sont
désormais clos via PR #557–#560. Depuis le dernier instantané (#245, #551),
l'epic **#563** (« vérification des mises à jour et gestion du modèle
d'IA ») avec huit sous-tickets (**#564–#571**) a été ouvert le 2026-07-13.
État en direct : **11** tickets ouverts – #245, #551, #563–#571.

### Terminé depuis la dernière revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8** et **O2–O7** restent
  faits ; les epics **#329/#344/#358/#384** (N9–N12) plus le correctif
  d'export **#363** fusionnés/archivés. Depuis le 2026-06-25, également
  **#404/#406/#408** (PR #412) clos.
- **Redesign et publication :** cœur du redesign/rail/zoom/inspecteur en
  cartes/Dark Mode/suivi UI (**#413/#414/#455–#464/#474–#489/#499–#501/
  #503/#509/#510/#514–#517**, **#490**, **#433/#434**) via PR #412–#522.
  Vague de publication **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/
  #542**, modèle de PR **#552**, sync **#549**, correctif SessionStart
  **#553**, formalisation v2.3.0 **#550** – tout clos depuis le 2026-07-12.

### Encore ouvert

- **O8 🟢 — Imprécision du prototype :** les outils de hauteur restent
  verrouillés dans la maquette après génération ; n'affecte que la
  simulation (#347).

## Tickets GitHub ouverts — Triage (2026-07-13)

État en direct : **11** tickets ouverts – deux tickets CI/sécurité
préexistants (**#245**, **#551**) plus l'epic **#563** avec huit sous-tickets
(**#564–#571**) pour deux groupes indépendants : mises à jour de l'app
(#564–#567) et gestion du modèle d'IA (#568–#571). Tous les commentaires
revus – les notes de triage du propriétaire du 2026-07-13 couvrent déjà
l'ordre/le périmètre ; aucune description de ticket n'a dû être modifiée.

### Regroupements pertinents

#245/#551 sont liés (scan Codex : action de compte vs. décision
stratégique). Les huit sous-tickets de #563 forment deux chaînes
internement séquentielles mais mutuellement indépendantes : **mises à jour
de l'app** (#564→#565→#566→#567) et **téléchargement du modèle d'IA**
(#568→#569→#570→#571) – confirmé par l'auteur le 2026-07-13 (commentaires
sur #563/#569/#570).

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs,
**Complexité** = effort estimé, **Modèle/Effort** = modèle/effort recommandés.

| # | Titre | Pertinence | Complexité | Modèle/Effort | Prochaine étape recommandée |
|---|-------|------------|------------|----------------|-----------------------------|
| [#563](https://github.com/NikolayDA/picture_helper/issues/563) | Epic : extension de menu, mises à jour de l'app et gestion du modèle d'IA | 🟠 Élevée | 🟠 Élevée (8 sous-tickets) | – (suivi pur) | **Blocked (on sub-issues)** – se ferme avec #564–#571 ; ordre dans le commentaire du 2026-07-13. |
| [#564](https://github.com/NikolayDA/picture_helper/issues/564) | Mises à jour de l'app : logique cœur de vérification (`app_update.py`) | 🟠 Élevée | 🟢 Faible (taille S, sans dépendance) | Sonnet 5 · faible–moyen | **Ready for PR** – sans Qt, strictement typé, critères d'acceptation clairs. |
| [#565](https://github.com/NikolayDA/picture_helper/issues/565) | Mises à jour de l'app : intégration menu/dialogue « Rechercher des mises à jour… » | 🟠 Élevée | 🟡 Moyenne (taille S–M, QThread async + i18n) | Sonnet 5 · moyen | **Needs #564** – prêt pour un PR juste après. |
| [#566](https://github.com/NikolayDA/picture_helper/issues/566) | Mises à jour de l'app : vérification automatique optionnelle au démarrage | 🟡 Moyenne | 🟢 Faible (taille S) | Sonnet 5 · faible | **Needs #564+#565**. |
| [#567](https://github.com/NikolayDA/picture_helper/issues/567) | Mises à jour de l'app : clôture documentation + gouvernance i18n | 🟢 Faible | 🟢 Faible (taille XS) | Sonnet 5 · faible | **Needs #564–#566 fusionnés**. |
| [#568](https://github.com/NikolayDA/picture_helper/issues/568) | Téléchargement du modèle d'IA : détection d'état (sans Qt) | 🟠 Élevée | 🟢 Faible (taille S, sans dépendance) | Sonnet 5 · faible–moyen | **Ready for PR** – sans Qt, strictement typé, critères d'acceptation clairs. |
| [#569](https://github.com/NikolayDA/picture_helper/issues/569) | Téléchargement du modèle d'IA : intégration menu/dialogue « Gérer le modèle d'IA… » | 🟠 Élevée | 🟡 Moyenne (taille M, dialogue+progression+annulation simulés) | Sonnet 5 · moyen | **Needs #568** – chemin simulé suffit (clarification 2026-07-13). |
| [#570](https://github.com/NikolayDA/picture_helper/issues/570) | Téléchargement du modèle d'IA : câblage avec le warmup/WorkerController existant | 🟠 Élevée | 🟡 Moyenne–Élevée (taille S–M, nouveau hook `cancel_warmup()` requis) | Sonnet 5 · moyen–élevé | **Needs #568+#569**. |
| [#571](https://github.com/NikolayDA/picture_helper/issues/571) | Téléchargement du modèle d'IA : clôture documentation + gouvernance i18n | 🟢 Faible | 🟢 Faible (taille XS) | Sonnet 5 · faible | **Needs #568–#570 fusionnés**. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Décision de stratégie pour Codex Security Scan (réactiver/retirer/remplacer) | 🟡 Moyenne | 🟡 Moyenne | Sonnet 5 · moyen | **Needs refinement** – choix entre trois options ; recommandation : option 2 (retirer/désactiver) vu le blocage externe de semaines et la redondance avec pip-audit/license/CI. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan « Quota exceeded » | 🟡 Moyenne | 🟢 Faible | – (aucune tâche de code) | **Bloqué (externe)** – restaurer la facturation/le quota OpenAI est une action de compte, pas un PR. |

### Recommandé ensuite (ordre des PR)

1. **#564+#568** — logique cœur sans Qt d'abord et en parallèle
   (indépendantes, prêtes pour un PR).
2. **#565+#569** — intégration menu/dialogue par groupe après fusion de la
   logique cœur (chemin simulé suffit).
3. **#566+#570** — vérification au démarrage / câblage du warmup ; #570
   nécessite en plus le nouveau hook `cancel_warmup()` (commentaire
   2026-07-13).
4. **#567+#571** — clôture documentation par groupe (XS, trivial).
5. **#551** — décision sur la stratégie du scan (liée à #245), puis ajuster
   le workflow.
6. **#245** — reste bloqué en externe ; vérifier seulement après
   restauration du quota OpenAI.

*Dérive :* revérifier en direct le nombre de tickets ouverts avant chaque
mise à jour, sans le reporter tel quel (#542 → #549 : même décalage).

## Tours précédents

- **2026-07-13 (audit des tickets)** — epic **#563** + huit sous-tickets
  (**#564–#571**) ouvert ; les 11 tickets ouverts réévalués, commentaires du
  propriétaire pris en compte. Aucun fermé. Recommandation : #564/#568
  d'abord. Instantané mis à jour à 11.
- **2026-07-12** — formalisation v2.3.0 (**#550**), correctif SessionStart
  (**#553**), sync (**#549**, modèle de PR **#552** via PR #557), audit
  (**#542** clos, #549–#553 ouverts) et version **v2.5.0** (vague
  #435/#392/#426/#389, #299/#541/#318) – instantané réduit à 2.
- **2026-07-11** — epic #425 achevé (#430 PR #526, i18n ES/FR/UK/ZH
  complète, O1 fait ; #431/#432 PR #529 ; suivi final #530/#531 PR
  #533/#535).
- **2026-07-05–10** — #509/#510/#514–#517 (PR #520–#522), #490, vague Dark
  Mode/icônes rail, inspecteur en cartes (#413/#414), #499–#501/#503,
  peaufinage icônes/barre d'état.
- **2026-06-29** — #404/#406/#408 achevés (PR #412), vague de redesign
  ouverte.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, achevée ou écartée
  en cas de faux positif.

Constats historiques et journaux de travail (tours 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
