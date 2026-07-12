[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-12)

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests
locale restent la base avant tout nouveau PR. La version **v2.5.0** a été
publiée le 2026-07-11 (CHANGELOG curé, version montée — PR #538). Toute la
vague de rollout/publication est donc close : **#435** (PR #538), **#392**,
**#426** et **#389**. Également clos : **#299** (PR #539) avec le suivi
d'hygiène des tests N13 traité séparément **#541** (PR #543), plus **#318**
(PR #540) et la synchronisation de l'instantané de recommandations **#542**.
Un audit du dépôt du 2026-07-12 a ouvert cinq nouveaux constats sous forme de
tickets (**#549–#553**) ; GitHub affiche désormais **6** tickets ouverts :
**#245** plus **#549–#553**.

### Terminé depuis la dernière revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8** et **O2–O7** restent
  faits ; les epics **#329/#344/#358/#384** (N9–N12) plus le correctif
  d'export **#363** sont fusionnés et archivés.
- **Fermé depuis le 2026-06-25 :** **#404/#406/#408** (PR #412) — constats
  aperçu/code mort/audit faits.
- **Cœur du redesign, rail/zoom, inspecteur en cartes, Dark Mode, suivi UI :**
  **#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517** ont
  atterri via PR #412/#423/#466/#467/#473/#482/#489/#504/#506/#512/#513/
  #518/#519 et PR #520/#521/#522 ; **#490** et **#433/#434** de même.
- **Fermé depuis le 2026-07-12 :** la vague de publication **#435/#392/#426/
  #389** (v2.5.0, PR #538) plus **#299** (PR #539), le suivi d'hygiène des
  tests **#541** (PR #543), **#318** (PR #540) et la synchronisation de
  l'instantané de recommandations **#542**. Tous les points redesign/
  publication/backlog du dernier instantané sont ainsi soldés.

### Encore ouvert

- **O8 🟢 — Imprécision du prototype :** les outils de hauteur restent
  verrouillés dans la maquette après génération ; n'affecte que la
  simulation (#347).

## Tickets GitHub ouverts — Triage (2026-07-12)

Au 2026-07-12, GitHub affiche **6** tickets ouverts : le blocage externe de
quota/facturation **#245** plus cinq nouveaux constats issus de l'audit du
dépôt en cours — **#549** (instantané de recommandations), **#550**
(cohérence tag/release de v2.3.0), **#551** (décision de stratégie pour
Codex Security Scan), **#552** (modèle de PR) et **#553** (vérification du
hook SessionStart).

### Regroupements pertinents

#245 et #551 sont liés en contenu (scan Codex) : #245 est une pure action de
compte, tandis que #551 requiert sa propre décision stratégique
(réactiver/retirer/remplacer). #550 requiert aussi d'abord une décision
(tag+release vs. clarification doc seule). #549 (ce PR), #552 et #553 sont
indépendants et peuvent avancer immédiatement.

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs,
**Complexité** = effort de mise en œuvre estimé, **Modèle/Effort** = modèle
Claude et effort de raisonnement recommandés pour l'implémentation par
Claude Code.

| # | Titre | Pertinence | Complexité | Modèle/Effort | Prochaine étape recommandée |
|---|-------|------------|------------|----------------|-----------------------------|
| [#552](https://github.com/NikolayDA/picture_helper/issues/552) | Ajouter un modèle de PR avec checklist du gate standard | 🟡 Moyenne | 🟢 Faible | Sonnet 5 · faible | **Ready for PR** – un seul nouveau fichier, aucune dépendance. |
| [#553](https://github.com/NikolayDA/picture_helper/issues/553) | Vérifier la fiabilité du hook SessionStart dans les sessions web | 🟡 Moyenne | 🟡 Moyenne | Sonnet 5 · moyen | **Ready for PR** – reproduire dans une session web neuve, puis corriger/documenter si besoin. |
| [#549](https://github.com/NikolayDA/picture_helper/issues/549) | Rafraîchir l'instantané des recommandations sur l'état en direct | 🟢 Faible | 🟢 Faible | Sonnet 5 · faible | **Ready for PR** – couvert par cette synchronisation d'instantané. |
| [#550](https://github.com/NikolayDA/picture_helper/issues/550) | v2.3.0 : réconcilier le CHANGELOG avec l'historique tag/release | 🟡 Moyenne | 🟡 Moyenne | Sonnet 5 · moyen | **Needs refinement** – la variante A (tag+release) vs. B (clarification doc seule) nécessite une décision avant implémentation. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Décision de stratégie pour Codex Security Scan (réactiver/retirer/remplacer) | 🟡 Moyenne | 🟡 Moyenne | Sonnet 5 · moyen | **Needs refinement** – nécessite un choix délibéré entre trois options ; recommandation : option 2 (retirer/désactiver) vu le blocage externe de plusieurs semaines et la redondance avec pip-audit/license/CI. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan « Quota exceeded » | 🟡 Moyenne | 🟢 Faible | – (aucune tâche de code) | **Bloqué (externe)** – restaurer la facturation/le quota OpenAI est une action de compte, pas un PR. |

### Recommandé ensuite (ordre des PR)

1. **#552** — ajouter le modèle de PR (autonome, faible risque).
2. **#549** — clore avec ce PR (synchronisation de l'instantané sur les six
   miroirs, y compris #550–#553).
3. **#553** — reproduire le comportement du hook SessionStart dans une
   session web neuve et corriger si besoin.
4. **#550** — obtenir une décision sur la variante A/B, puis ajuster le
   CHANGELOG/tag/release.
5. **#551** — obtenir une décision sur la stratégie du scan (liée à #245),
   puis ajuster le workflow.
6. **#245** — reste bloqué en externe ; vérifier manuellement seulement
   après restauration du quota OpenAI.

## Tours précédents

- **2026-07-12 (audit des tickets)** — #542 clos ; un audit du dépôt a ouvert
  cinq nouveaux tickets (#549–#553) ; instantané des tickets ouverts mis à
  jour à 6 (#245 + #549–#553).
- **2026-07-12** — version **v2.5.0** publiée ; vague de rollout
  #435/#392/#426/#389 close ; #299 (PR #539), suivi N13 #541 (PR #543) et
  #318 (PR #540) clos ; instantané des tickets ouverts réduit à #245 + #542.
- **2026-07-11 (suivi final)** — #425 fermé formellement ; #530/#531 fermés
  via PR #533/#535 ; instantané mis à jour à 7 tickets restants.
- **2026-07-11 (2ᵉ triage)** — #431/#432 fermés (PR #529) ; epic #425
  complet. Nouveaux tickets #530/#531 d'un cas de support warmup IA.
- **2026-07-11** — #430 fermé (PR #526, i18n ES/FR/UK/ZH complète ; O1 fait) ;
  epic #425 ne dépendait plus que de #431/#432.
- **2026-07-10** — #509/#510 fermés, #514–#517 achevés, suivi de la colonne
  droite terminé via PR #520/#521/#522 ; workflow de baseline benchmark passé
  aux PR au lieu des pushs directs.
- **2026-07-05/06** — #490 (dérive d'instantané), vague Dark Mode/icônes
  rail, inspecteur en cartes (#413/#414), #499–#501/#503 (PR #504/#506) et
  peaufinage icônes/barre d'état (PR #507/#508) achevés.
- **2026-06-29** — #404/#406/#408 achevés (PR #412), vague de redesign ouverte.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, achevée ou écartée en cas de faux positif.

Constats historiques et journaux de travail (tours 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
