[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-06)

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests
locale restent la base avant tout nouveau PR. Depuis l'instantané du
2026-07-05, le correctif d'instantané Recommendations **#490** est fermé. La
vérification du jour sur les epics de redesign
(#413/#418/#424/#455/#463/#474/#483) a révélé trois constats neufs : **#499**
(thème clair pas encore 1:1 avec le prototype), **#500** (script de captures
cassé, bloque #432) et **#501** (widget mort `TopIconTab*`). GitHub affiche
actuellement **14** tickets ouverts.

### Terminé depuis la dernière revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8** et **O2–O7** restent
  faits ; les epics **#329/#344/#358/#384** (N9–N12) plus le correctif
  d'export **#363** sont fusionnés et archivés.
- **Fermés depuis la revue du 2026-06-25 :** **#404/#406/#408** (PR #412) —
  constats aperçu/code mort/audit faits.
- **Cœur du redesign, rail/zoom, inspecteur en cartes, Dark Mode :**
  **#413/#414/#455–#464/#474–#489** ont atterri via PR
  #412/#423/#466/#467/#473/#482/#489 (barre d'étapes, jetons de design,
  alignement Dark Mode, icônes vectorielles).
- **#490 et #433/#434 terminés :** dérive d'instantané corrigée ; smoke
  tests/régression atterris via PR #423 — l'epic **#426** ne dépend plus que
  de **#435**.

### Nouveau depuis la dernière revue

- **#499 🟡 :** `theme.LIGHT` diverge du prototype sur plusieurs jetons
  (même schéma que #474–#480, test déjà dans `tests/test_theme.py`).
- **#500 🟠 :** `scripts/generate_app_screenshots.py` cherche un
  `QTabWidget` qui n'existe plus ; bloque **#432**.
- **#501 🟢 :** `TopIconTabBar`/`TopIconTabWidget` dans `widgets.py` sont des
  widgets morts depuis le passage au stepper.

### Encore ouvert

- **O1 🟠 — Langues d'exécution supplémentaires.** DE/EN sont commutables ;
  es/fr/uk/zh manquent encore comme locales d'exécution (correspond à
  **#430**).
- **O8 🟢 — Imprécision du prototype :** les outils de hauteur restent
  verrouillés dans la maquette après génération ; n'affecte que la
  simulation (#347).

## Tickets GitHub ouverts — Triage (2026-07-06)

Au 2026-07-06, GitHub affiche **14** tickets ouverts : trois suivis de
redesign (**#499/#500/#501**), i18n/docs (**#425/#430/#431/#432**),
rollout/publication (**#426/#435/#392/#389**) et backlog/points externes
(**#299/#318/#245**).

### Regroupements pertinents

- **Suivi de redesign :** #499/#500/#501 sont indépendants et à faible
  risque ; **#500** d'abord car il débloque **#432**.
- **i18n/docs :** #430 débloque les tests de parité ; #431/#432 suivent
  après le gel de l'UI **et** #500.
- **Rollout/publication :** #426 ne dépend que de #435 ; coordonner avec
  #392, puis clore #426/#389.
- **Backlog :** #299 après la publication ; affiner #318 d'abord ; #245
  reste bloqué en externe.

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs,
**Complexité** = effort de mise en œuvre estimé.

| # | Titre | Pertinence | Complexité | Prochaine étape recommandée |
|---|-------|------------|------------|-----------------------------|
| [#500](https://github.com/NikolayDA/picture_helper/issues/500) | Script de captures cassé après le redesign (bloque #432) | 🟠 Élevée | 🟢 Faible | **Prêt pour PR** – faire basculer la navigation sur `Stepper`. |
| [#499](https://github.com/NikolayDA/picture_helper/issues/499) | Aligner le thème clair 1:1 sur le Prototype A | 🟡 Moyenne | 🟢 Faible | **Prêt pour PR** – même schéma que #474–#480. |
| [#501](https://github.com/NikolayDA/picture_helper/issues/501) | Retirer les widgets `TopIconTab*` orphelins | 🟢 Faible | 🟢 Faible | **Prêt pour PR** – nettoyage pur, 3 fichiers. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC : Internationalisation et documentation | 🟠 Élevée | 🟡 Moyenne | **En cours** – #430/#431/#432 ouverts. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | Nouvelles chaînes d'UI (étapes/cartes/navigation) | 🟠 Élevée | 🟡 Moyenne | **Prêt pour PR** – ES/FR/UK/ZH ; DE/EN via PR #423. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Mettre ANLEITUNG et README au workflow guidé | 🟡 Moyenne | 🟡 Moyenne | **Après gel de l'UI** – miroir en 6 langues. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Refaire les captures de l'app pour le redesign | 🟢 Faible | 🟢 Faible | **Bloqué** – nécessite le gel de l'UI **et** #500. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC : QA et déploiement du redesign | 🟠 Élevée | 🟢 Faible | **Presque fini** – seul #435 reste ouvert. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG et bump de version du redesign | 🟡 Moyenne | 🟢 Faible | **Aligner sur #392** – définir la séquence. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Publier la version v2.5.0 | 🟠 Élevée | 🟡 Moyenne | **Prête** – décider la séquence avec le redesign. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC : Màj docs utilisateur et publication | 🟠 Élevée | 🟢 Faible | **Clore après #392** – seule la publication reste. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | 🟢 Faible | 🟢 Faible | **Après la publication** – plus fort impact d'abord. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Overrides de permissions par job dans WF réutilisable | 🟢 Faible | 🟡 Moyenne | **À affiner** – prouver la sémantique GitHub. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan « Quota exceeded » | 🟡 Moyenne | 🟢 Faible | **Bloqué (externe)** – facturation/quota OpenAI. |

### Recommandé ensuite (ordre des PR)

1. **#500** d'abord — débloque **#432** ; **#499**/**#501** dans le même PR
   ou un PR directement suivant.
2. Avancer **#430** — débloque la parité i18n ; puis **#431**/**#432**.
3. **Publication :** mener **#435** + **#392** de façon coordonnée, puis
   clore **#426**/**#389**.
4. **#299** après la publication ; n'étudier que **#318** ; garder **#245**
   bloqué en externe.

## Tours précédents

- **2026-07-05** — #490 (dérive d'instantané) en cours, vague Dark
  Mode/icônes rail et inspecteur en cartes (#413/#414) achevés.
- **2026-06-29** — #404/#406/#408 achevés (PR #412), vague de redesign ouverte.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, achevée ou écartée en cas de faux positif.

Constats historiques et journaux de travail (tours 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
