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
(PR #540). GitHub n'affiche désormais plus que **2** tickets ouverts.

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
  tests **#541** (PR #543) et **#318** (PR #540). Tous les points redesign/
  publication/backlog du dernier instantané sont ainsi soldés.

### Encore ouvert

- **O8 🟢 — Imprécision du prototype :** les outils de hauteur restent
  verrouillés dans la maquette après génération ; n'affecte que la
  simulation (#347).

## Tickets GitHub ouverts — Triage (2026-07-12)

Au 2026-07-12, GitHub n'affiche plus que **2** tickets ouverts : le blocage
externe de quota/facturation **#245** et cette synchronisation de
documentation **#542**.

### Regroupements pertinents

- **Bloqué en externe :** #245 dépend de la facturation/du quota OpenAI — une
  action de compte, pas un PR du dépôt.
- **Documentation :** #542 aligne les six miroirs de recommandations sur
  l'état en direct et est résolu par le PR associé.

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs,
**Complexité** = effort de mise en œuvre estimé, **Modèle/Effort** = modèle
Claude et effort de raisonnement recommandés pour l'implémentation par
Claude Code.

| # | Titre | Pertinence | Complexité | Modèle/Effort | Prochaine étape recommandée |
|---|-------|------------|------------|----------------|-----------------------------|
| [#542](https://github.com/NikolayDA/picture_helper/issues/542) | Rafraîchir l'instantané des recommandations après v2.5.0 | 🟢 Faible | 🟢 Faible | Sonnet 5 · faible | **En cours** – ce PR aligne les six miroirs sur l'état en direct, structurellement synchronisés. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan « Quota exceeded » | 🟡 Moyenne | 🟢 Faible | – (aucune tâche de code) | **Bloqué (externe)** – restaurer la facturation/le quota OpenAI est une action de compte, pas un PR. |

### Recommandé ensuite (ordre des PR)

1. Clore **#542** avec ce PR (synchronisation structurelle de l'instantané
   sur les six miroirs).
2. **#245** reste bloqué en externe — aucun PR du dépôt n'est possible ;
   vérifier manuellement seulement après restauration du quota OpenAI.

## Tours précédents

- **2026-07-12** — version **v2.5.0** publiée ; vague de rollout
  #435/#392/#426/#389 close ; #299 (PR #539), suivi N13 #541 (PR #543) et
  #318 (PR #540) clos ; instantané des tickets ouverts réduit à #245 + #542.
- **2026-07-11 (suivi final)** — #425 fermé formellement ; #530/#531 fermés
  via PR #533/#535 ; instantané des tickets ouverts mis à jour à 7 tickets
  restants.
- **2026-07-11 (2ᵉ triage)** — #431/#432 fermés (PR #529, ANLEITUNG/README/
  captures amenés au workflow guidé en 6 étapes) ; l'epic #425 est complet.
  Nouveaux tickets #530/#531 ouverts à partir d'un cas de support warmup IA.
- **2026-07-11** — #430 fermé (PR #526, i18n d'exécution ES/FR/UK/ZH
  complète ; O1 fait) ; l'epic #425 ne dépendait plus alors que de #431/#432.
- **2026-07-10** — #509/#510 fermés, #514–#517 achevés, suivi de la colonne
  droite terminé via PR #520/#521/#522 ; workflow de baseline benchmark passé
  aux PR au lieu des pushs directs.
- **2026-07-06** — #499/#500/#501 (PR #504) et #503 (PR #506) achevés ;
  peaufinage icônes/barre d'état via PR #507/#508.
- **2026-07-05** — #490 (dérive d'instantané) en cours, vague Dark
  Mode/icônes rail et inspecteur en cartes (#413/#414) achevés.
- **2026-06-29** — #404/#406/#408 achevés (PR #412), vague de redesign ouverte.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, achevée ou écartée en cas de faux positif.

Constats historiques et journaux de travail (tours 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
