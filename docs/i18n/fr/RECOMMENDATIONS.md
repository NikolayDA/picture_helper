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
Un audit du dépôt du 2026-07-12 a ouvert cinq nouveaux constats
(**#549–#553**) ; **#552**, **#549**, **#553** et **#550** sont désormais clos
via PR #557, #558, #559 et #560. État en direct (revérifié) : **2** tickets
ouverts – **#245** et **#551**.

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
  tests **#541** (PR #543), **#318** (PR #540), la synchronisation de
  l'instantané de recommandations **#542**, le modèle de PR **#552**
  (PR #557), cette synchronisation d'instantané **#549**, le correctif du hook
  SessionStart **#553** et la formalisation tag/release v2.3.0 **#550**. Tous
  les points redesign/publication/backlog du dernier instantané sont ainsi
  soldés.

### Encore ouvert

- **O8 🟢 — Imprécision du prototype :** les outils de hauteur restent
  verrouillés dans la maquette après génération ; n'affecte que la
  simulation (#347).

## Tickets GitHub ouverts — Triage (2026-07-12)

État en direct juste avant cette édition : **#552**, **#549**, **#553** et
**#550** sont clos. Il reste **2** tickets ouverts : **#245** (blocage
quota/facturation) et **#551** (décision de stratégie pour Codex Security
Scan).

### Regroupements pertinents

#245 et #551 sont liés en contenu (scan Codex) : #245 est une pure action de
compte, tandis que #551 requiert sa propre décision stratégique
(réactiver/retirer/remplacer).

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs,
**Complexité** = effort de mise en œuvre estimé, **Modèle/Effort** = modèle
Claude et effort de raisonnement recommandés pour l'implémentation par
Claude Code.

| # | Titre | Pertinence | Complexité | Modèle/Effort | Prochaine étape recommandée |
|---|-------|------------|------------|----------------|-----------------------------|
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Décision de stratégie pour Codex Security Scan (réactiver/retirer/remplacer) | 🟡 Moyenne | 🟡 Moyenne | Sonnet 5 · moyen | **Needs refinement** – nécessite un choix délibéré entre trois options ; recommandation : option 2 (retirer/désactiver) vu le blocage externe de plusieurs semaines et la redondance avec pip-audit/license/CI. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan « Quota exceeded » | 🟡 Moyenne | 🟢 Faible | – (aucune tâche de code) | **Bloqué (externe)** – restaurer la facturation/le quota OpenAI est une action de compte, pas un PR. |

### Recommandé ensuite (ordre des PR)

1. **#551** — obtenir une décision sur la stratégie du scan (liée à #245),
   puis ajuster le workflow.
2. **#245** — reste bloqué en externe ; vérifier manuellement seulement
   après restauration du quota OpenAI.

*Dérive :* revérifier en direct le nombre de tickets ouverts avant chaque
mise à jour, sans le reporter tel quel (#542 → #549 : même décalage).

## Tours précédents

- **2026-07-12 (#550)** — tag v2.3.0 et GitHub Release formalisés
  rétroactivement ; les footers CHANGELOG dans les six langues utilisent
  désormais `v2.3.0` au lieu de SHA bruts. Instantané réduit à 2 (#245, #551).
- **2026-07-12 (#553)** — correctif du hook SessionStart : un
  `pip install --upgrade pip` échoué (paquet Debian sans métadonnées RECORD)
  arrêtait le hook avant l'installation `.[test]` ; corrigé avec
  `--ignore-installed`, une vérification idempotente et un piège d'erreur.
- **2026-07-12 (sync #549)** — #552 (modèle de PR) clos via PR #557 ; ce PR
  clôt #549. Instantané réduit à 4 (#245, #550, #551, #553).
- **2026-07-12 (audit des tickets)** — #542 clos ; un audit du dépôt a ouvert
  cinq nouveaux tickets (#549–#553) ; instantané des tickets ouverts mis à
  jour à 6 (#245 + #549–#553).
- **2026-07-12** — version **v2.5.0** publiée ; vague de rollout
  #435/#392/#426/#389 close ; #299 (PR #539), suivi N13 #541 (PR #543) et
  #318 (PR #540) clos ; instantané des tickets ouverts réduit à #245 + #542.
- **2026-07-11 (suivi final)** — #425 fermé formellement ; #530/#531 fermés
  via PR #533/#535 ; instantané mis à jour à 7 tickets restants.
- **2026-07-11 (2ᵉ triage)** — #431/#432 fermés (PR #529) ; epic #425
  complet. Nouveaux tickets #530/#531. #430 fermé (PR #526, i18n ES/FR/UK/ZH
  complète ; O1 fait).
- **2026-07-10** — #509/#510 fermés, #514–#517 achevés, suivi de la colonne
  droite terminé via PR #520/#521/#522.
- **2026-07-05/06** — #490, vague Dark Mode/icônes rail, inspecteur en
  cartes (#413/#414), #499–#501/#503 (PR #504/#506) et peaufinage icônes/
  barre d'état (PR #507/#508).
- **2026-06-29** — #404/#406/#408 achevés (PR #412), vague de redesign ouverte.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, achevée ou écartée en cas de faux positif.

Constats historiques et journaux de travail (tours 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
