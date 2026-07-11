[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-11)

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests
locale restent la base avant tout nouveau PR. **#430** (i18n à l'exécution
pour ES/FR/UK/ZH) a été fusionné via PR #526 et est fermé — vérifié :
`bgremover/i18n.py::_TRANSLATIONS` contient désormais `de/en/es/fr/uk/zh`,
chacun avec 494 clés en parité complète. Cela clôt également **O1** (langues
d'exécution supplémentaires). GitHub affiche actuellement **10** tickets
ouverts.

### Terminé depuis la dernière revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8** et **O2–O7** restent
  faits ; les epics **#329/#344/#358/#384** (N9–N12) plus le correctif
  d'export **#363** sont fusionnés et archivés.
- **Fermé depuis le 2026-06-25 :** **#404/#406/#408** (PR #412) — constats
  aperçu/code mort/audit faits.
- **Cœur du redesign, rail/zoom, inspecteur en cartes, Dark Mode, suivi UI :**
  **#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517** ont
  atterri via PR #412/#423/#466/#467/#473/#482/#489/#504/#506/#512/#513/
  #518/#519 et PR #520/#521/#522 ; **#490** et **#433/#434** de même
  (l'epic **#426** ne dépend plus que de **#435**).
- **Fermé depuis le 2026-07-11 :** **#430** (PR #526) — i18n à l'exécution
  pour ES/FR/UK/ZH entièrement maintenue et vérifiée en parité ; **O1** est
  fait (l'epic **#425** ne dépend plus que de **#431**/**#432**).

### Encore ouvert

- **O8 🟢 — Imprécision du prototype :** les outils de hauteur restent
  verrouillés dans la maquette après génération ; n'affecte que la
  simulation (#347).

## Tickets GitHub ouverts — Triage (2026-07-11)

Au 2026-07-11, GitHub affiche **10** tickets ouverts : i18n/docs
(**#425/#431/#432**), rollout/publication (**#426/#435/#392/#389**) et
backlog/points externes (**#299/#318/#245**).

### Regroupements pertinents

- **i18n/docs :** #430 est fait ; #431/#432 sont maintenant prêts à
  implémenter (le blocage du gel UI est levé selon l'audit de #431 du
  2026-07-09).
- **Rollout/publication :** #426 ne dépend que de #435 ; coordonner avec
  #392, puis clore #426/#389.
- **Backlog :** #299 après la publication ; affiner #318 d'abord ; #245
  reste bloqué en externe.

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs,
**Complexité** = effort de mise en œuvre estimé, **Modèle/Effort** = modèle
Claude et effort de raisonnement recommandés pour l'implémentation par
Claude Code.

| # | Titre | Pertinence | Complexité | Modèle/Effort | Prochaine étape recommandée |
|---|-------|------------|------------|----------------|-----------------------------|
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC : Internationalisation et documentation | 🟠 Élevée | 🟢 Faible | – (ticket de suivi) | **En cours** – #431/#432 ouverts, #430 fait. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Mettre ANLEITUNG et README au workflow guidé | 🟡 Moyenne | 🟡 Moyenne | Sonnet 5 · moyen | **Prêt pour PR** – audit du 2026-07-09 déjà fait (inclut la correction de la liste des 6 formats de recadrage). |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Refaire les captures de l'app pour le redesign | 🟢 Faible | 🟢 Faible | Sonnet 5 · faible | **Prêt pour PR** – blocage #500 levé (PR #504) ; une vérification visuelle par l'utilisateur reste utile. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC : QA et déploiement du redesign | 🟠 Élevée | 🟢 Faible | – (ticket de suivi) | **Presque fini** – seul #435 reste ouvert. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG et bump de version du redesign | 🟡 Moyenne | 🟢 Faible | Sonnet 5 · faible | **Prêt pour PR** – mécanique, bien délimité. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Publier la version v2.5.0 | 🟠 Élevée | 🟡 Moyenne | Sonnet 5 · moyen | **Prête** – séquencer après #435 ; le build `.dmg` macOS nécessite un runner local/macOS hors de ce conteneur distant. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC : Màj docs utilisateur et publication | 🟠 Élevée | 🟢 Faible | – (ticket de suivi) | **Clore après #392** – seule la publication reste. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | 🟢 Faible | 🟡 Moyenne | Sonnet 5 · moyen | **Prêt pour PR** – catalogue plus les suites N13 du triage du 2026-07-08 sont documentés ; prioriser après la publication. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Overrides de permissions par job dans WF réutilisable | 🟢 Faible | 🟡 Moyenne | Opus 4.8 · élevé | **À affiner** – prouver d'abord la sémantique GitHub (top-level vs. effective par job) ; ne doit pas affaiblir le garde-fou de régression OIDC. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan « Quota exceeded » | 🟡 Moyenne | 🟢 Faible | – (aucune tâche de code) | **Bloqué (externe)** – restaurer la facturation/le quota OpenAI est une action de compte, pas un PR. |

### Recommandé ensuite (ordre des PR)

1. **#431**/**#432** — tous deux prêts à implémenter, plus aucun blocage.
2. **Publication :** mener **#435** + **#392** de façon coordonnée, puis
   clore **#426**/**#389**.
3. **#299** après la publication ; n'étudier que **#318** ; garder **#245**
   bloqué en externe.

## Tours précédents

- **2026-07-11** — #430 fermé (PR #526, i18n d'exécution ES/FR/UK/ZH
  complète ; O1 fait) ; l'epic #425 ne dépend plus que de #431/#432.
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
