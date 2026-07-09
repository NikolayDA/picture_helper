[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-09)

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests
locale restent la base avant tout nouveau PR. Depuis l'instantané du
2026-07-06, les trois suivis de redesign **#499/#500/#501** (PR #504) et le
constat de code mort **#503** (PR #506 ; #505 était un merge accidentel à
diff vide, le contenu a atterri via #506) sont fermés ; s'y ajoute le
peaufinage icônes/barre d'état **PR #507/#508**. Sont nouveaux le bogue d'UI
**#509** (le curseur d'outil ignore le zoom du canevas) et **#510** (ce
rafraîchissement d'instantané). GitHub affiche actuellement **13** tickets
ouverts.

### Terminé depuis la dernière revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8** et **O2–O7** restent
  faits ; les epics **#329/#344/#358/#384** (N9–N12) plus le correctif
  d'export **#363** sont fusionnés et archivés.
- **Fermés depuis la revue du 2026-06-25 :** **#404/#406/#408** (PR #412) —
  constats aperçu/code mort/audit faits.
- **Cœur du redesign, rail/zoom, inspecteur en cartes, Dark Mode :**
  **#413/#414/#455–#464/#474–#489** ont atterri via PR
  #412/#423/#466/#467/#473/#482/#489 ; **#490** et **#433/#434** de même
  (l'epic **#426** ne dépend plus que de **#435**).
- **Fermés depuis le 2026-07-06 :** **#499/#500/#501** (PR #504 — thème
  clair aligné sur le prototype, générateur de captures réparé, widgets
  morts retirés ; le blocage #500 devant **#432** est levé) et **#503**
  (PR #506 — `CanvasHistory`/`_make_panel_btn`/constantes de thème mortes
  retirées).

### Nouveau depuis la dernière revue

- **#509 🟠 :** le curseur pinceau/gomme ne suit pas le zoom du canevas —
  taille affichée ≠ zone réellement affectée (touche aussi les pinceaux de
  hauteur ; cause localisée dans `set_tool`/`set_brush_size`).
- **#510 🟢 :** l'instantané de triage a été dépassé par le PR #504 fusionné
  30 minutes plus tard — résolu par cette mise à jour.

### Encore ouvert

- **O1 🟠 — Langues d'exécution supplémentaires.** DE/EN sont commutables ;
  es/fr/uk/zh manquent encore comme locales d'exécution (correspond à
  **#430**).
- **O8 🟢 — Imprécision du prototype :** les outils de hauteur restent
  verrouillés dans la maquette après génération ; n'affecte que la
  simulation (#347).

## Tickets GitHub ouverts — Triage (2026-07-09)

Au 2026-07-09, GitHub affiche **13** tickets ouverts : bogue d'UI
(**#509**), cet instantané de docs (**#510**), i18n/docs
(**#425/#430/#431/#432**), rollout/publication (**#426/#435/#392/#389**) et
backlog/points externes (**#299/#318/#245**).

### Regroupements pertinents

- **Bogue d'UI :** #509 est localisé avec précision (le curseur n'est
  jamais recalculé sur `zoomChanged`) et est le seul constat de code
  ouvert — bon prochain PR.
- **i18n/docs :** #430 débloque les tests de parité ; #431/#432 suivent
  après le gel de l'UI (le blocage #500 devant #432 est tombé avec le PR
  #504).
- **Rollout/publication :** #426 ne dépend que de #435 ; coordonner avec
  #392, puis clore #426/#389.
- **Backlog :** #299 après la publication ; affiner #318 d'abord ; #245
  reste bloqué en externe.

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs,
**Complexité** = effort de mise en œuvre estimé.

| # | Titre | Pertinence | Complexité | Prochaine étape recommandée |
|---|-------|------------|------------|-----------------------------|
| [#509](https://github.com/NikolayDA/picture_helper/issues/509) | Le curseur pinceau/gomme ignore le zoom du canevas | 🟠 Élevée | 🟡 Moyenne | **Prêt pour PR** – remettre le curseur à l'échelle sur `zoomChanged`/changement de taille. |
| [#510](https://github.com/NikolayDA/picture_helper/issues/510) | Instantané de triage périmé (état 2026-07-06) | 🟢 Faible | 🟢 Faible | **En cours** – cet instantané le résout. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC : Internationalisation et documentation | 🟠 Élevée | 🟡 Moyenne | **En cours** – #430/#431/#432 ouverts. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | Nouvelles chaînes d'UI (étapes/cartes/navigation) | 🟠 Élevée | 🟡 Moyenne | **Prêt pour PR** – ES/FR/UK/ZH ; DE/EN via PR #423. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Mettre ANLEITUNG et README au workflow guidé | 🟡 Moyenne | 🟡 Moyenne | **Après gel de l'UI** – miroir en 6 langues. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Refaire les captures de l'app pour le redesign | 🟢 Faible | 🟢 Faible | **Après gel de l'UI** – blocage #500 levé (PR #504). |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC : QA et déploiement du redesign | 🟠 Élevée | 🟢 Faible | **Presque fini** – seul #435 reste ouvert. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG et bump de version du redesign | 🟡 Moyenne | 🟢 Faible | **Aligner sur #392** – définir la séquence. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Publier la version v2.5.0 | 🟠 Élevée | 🟡 Moyenne | **Prête** – décider la séquence avec le redesign. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC : Màj docs utilisateur et publication | 🟠 Élevée | 🟢 Faible | **Clore après #392** – seule la publication reste. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | 🟢 Faible | 🟢 Faible | **Après la publication** – plus fort impact d'abord. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Overrides de permissions par job dans WF réutilisable | 🟢 Faible | 🟡 Moyenne | **À affiner** – prouver la sémantique GitHub. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan « Quota exceeded » | 🟡 Moyenne | 🟢 Faible | **Bloqué (externe)** – facturation/quota OpenAI. |

### Recommandé ensuite (ordre des PR)

1. **#509** d'abord — seul bogue de code ouvert, cause déjà localisée.
2. Avancer **#430** — débloque la parité i18n ; puis **#431**/**#432**.
3. **Publication :** mener **#435** + **#392** de façon coordonnée, puis
   clore **#426**/**#389**.
4. **#299** après la publication ; n'étudier que **#318** ; garder **#245**
   bloqué en externe.

## Tours précédents

- **2026-07-06** — #499/#500/#501 (PR #504) et #503 (PR #506) achevés ;
  peaufinage icônes/barre d'état via PR #507/#508.
- **2026-07-05** — #490 (dérive d'instantané) en cours, vague Dark
  Mode/icônes rail et inspecteur en cartes (#413/#414) achevés.
- **2026-06-29** — #404/#406/#408 achevés (PR #412), vague de redesign ouverte.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, achevée ou écartée en cas de faux positif.

Constats historiques et journaux de travail (tours 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
