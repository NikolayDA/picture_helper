[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-14)

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests
locale restent la base avant tout nouveau PR. La version **v2.5.0** a été
publiée le 2026-07-11 (PR #538) ; la vague de rollout **#435/#392/#426/#389**
est close, ainsi que **#299** (PR #539) avec le suivi N13 **#541** (PR #543),
**#318** (PR #540) et la synchronisation d'instantané **#542**. Un audit du
dépôt du 2026-07-12 a ouvert **#549–#553** ; **#552/#549/#553/#550** sont
désormais clos via PR #557–#560. L'epic **#563** (« vérification des mises à
jour et gestion du modèle d'IA », huit sous-tickets **#564–#571**) a été
entièrement implémenté et clos le 2026-07-13 via PR #573/#574 (**N14**).
État en direct : **2** tickets ouverts – #245, #551.

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
- **N14 — Epic #563 (mises à jour de l'app et gestion du modèle d'IA)
  entièrement clos :** logique cœur de vérification `app_update.py` (#564) et
  logique cœur de statut du modèle `ai_model_status.py` (#568) – toutes deux
  sans Qt, strictement typées et dans la liste mypy strict (PR #573).
  Intégration menu/dialogue « Rechercher des mises à jour… »/« Gérer le
  modèle d'IA… » (#565/#569, PR #573). Vérification automatique optionnelle
  au démarrage (#566) et câblage réel du téléchargement du modèle au mécanisme
  de warmup existant avec observateurs multiples/annulation coopérative
  (#570, PR #574, avec trois correctifs de revue Codex : on_success/
  on_finished séparés, vérification manuelle rattachée à une vérification de
  démarrage en cours, protection de course au rattachement). Clôture
  documentation (README/CLAUDE.md/CHANGELOG/RESOURCES/INSTALL_*, six
  langues) via #567/#571.

### Encore ouvert

- **O8 🟢 — Imprécision du prototype :** les outils de hauteur restent
  verrouillés dans la maquette après génération ; n'affecte que la
  simulation (#347).

## Tickets GitHub ouverts — Triage (2026-07-14)

État en direct : **2** tickets ouverts – tous deux sont des tickets
CI/sécurité préexistants, inchangés depuis la ronde précédente (l'epic #563
et ses huit sous-tickets sont désormais entièrement clos).

### Regroupements pertinents

#245/#551 sont liés (scan Codex : action de compte vs. décision
stratégique).

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs,
**Complexité** = effort estimé, **Modèle/Effort** = modèle/effort recommandés.

| # | Titre | Pertinence | Complexité | Modèle/Effort | Prochaine étape recommandée |
|---|-------|------------|------------|----------------|-----------------------------|
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Décision de stratégie pour Codex Security Scan (réactiver/retirer/remplacer) | 🟡 Moyenne | 🟡 Moyenne | Sonnet 5 · moyen | **Needs refinement** – choix entre trois options ; recommandation : option 2 (retirer/désactiver) vu le blocage externe de semaines et la redondance avec pip-audit/license/CI. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan « Quota exceeded » | 🟡 Moyenne | 🟢 Faible | – (aucune tâche de code) | **Bloqué (externe)** – restaurer la facturation/le quota OpenAI est une action de compte, pas un PR. |

### Recommandé ensuite (ordre des PR)

1. **#551** — décision sur la stratégie du scan (liée à #245), puis ajuster
   le workflow.
2. **#245** — reste bloqué en externe ; vérifier seulement après
   restauration du quota OpenAI.

*Dérive :* revérifier en direct le nombre de tickets ouverts avant chaque
mise à jour, sans le reporter tel quel (#542 → #549 : même décalage).

## Tours précédents

- **2026-07-13 (clôture d'epic)** — epic **#563** entièrement clos : les
  huit sous-tickets (**#564–#571**) fermés via PR #573 (#564/#565/#568/#569)
  et PR #574 (#566/#570 + clôture documentation #567/#571). Instantané réduit
  à 2 (#245, #551).
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
