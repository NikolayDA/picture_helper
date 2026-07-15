[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-16)

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests locale restent la base avant tout nouveau PR. La version **v2.5.0** a été publiée le 2026-07-11 (PR #538) ; la vague de rollout **#435/#392/#426/#389** est close, ainsi que **#299** (PR #539) avec le suivi N13 **#541** (PR #543), **#318** (PR #540) et la synchronisation d'instantané **#542**. Un audit du dépôt du 2026-07-12 a ouvert **#549–#553** ; **#552/#549/#553/#550** sont désormais clos via PR #557–#560. L'epic **#563** (« vérification des mises à jour et gestion du modèle d'IA », huit sous-tickets **#564–#571**) a été entièrement implémenté et clos le 2026-07-13 via PR #573/#574 (**N14**). État en direct : **17** tickets ouverts – les tickets préexistants #245/#551 plus trois epics ouverts le 2026-07-15 (**Release v2.6.0** #580, le **pipeline de hauteur 16 bits** #581, l'**aperçu de relief 3D** #582) avec leurs sous-tickets encore ouverts, plus deux constats de couverture **N15/N16** (#597/#598). **#583** (scope-freeze v2.6.0), **#586** (ADR 16 bits) et **#591** (contrat ADR/UX 3D, PR #603) sont achevés. **#584** a été rouvert lors de l'audit en direct du 2026-07-16 : les PR #601–#604 durcissent le nommage des artefacts et la réutilisation de release, mais le véritable gate candidat avec SHA final, cinq artefacts réels, sommes de contrôle, smokes plateforme et décision Go/No-Go reste à faire.

### Terminé depuis la dernière revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8** et **O2–O7** restent faits ; les epics **#329/#344/#358/#384** (N9–N12) plus le correctif d'export **#363** fusionnés/archivés ; depuis le 2026-06-25, également **#404/#406/#408** (PR #412) clos.
- **Redesign et publication v2.5.0 :** cœur du redesign/rail/zoom/inspecteur en cartes/Dark Mode/suivi UI (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) via PR #412–#522 ; vague de publication **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, modèle de PR **#552**, sync **#549**, correctif SessionStart **#553**, formalisation v2.3.0 **#550** – tout clos depuis le 2026-07-12.
- **N14 — Epic #563 (mises à jour de l'app et gestion du modèle d'IA) entièrement clos :** `app_update.py` (#564), `ai_model_status.py` (#568), intégration menu/dialogue (#565/#569), vérification automatique optionnelle au démarrage (#566), câblage du warmup avec observateurs multiples/annulation coopérative (#570) via PR #573/#574 ; clôture documentation (#567/#571).
- **#583/#586/#591 achevés, #584 rouvert :** le scope-freeze/version/CHANGELOG v2.6.0 (#583), l'ADR HEIGHT 16 bits (#586) et le contrat ADR/UX 3D (#591, PR #603) sont achevés. #584 reste ouvert jusqu'à preuve du gate candidat complet.

### Encore ouvert

- **Gate de release #584 🟠 :** figer le SHA candidat final, construire cinq artefacts réels dans le workflow sans publication, documenter les sommes de contrôle et smokes plateforme, puis décider Go/No-Go.
- **O8 🟢 — Imprécision du prototype :** les outils de hauteur restent verrouillés dans la maquette après génération ; n'affecte que la simulation (#347).
- **N15 🟡 — Câblage de dialogue non testé :** `MainWindow._open_ai_install_dialog` (`main_window.py:1566`) n'a aucun test dédié, contrairement à la méthode sœur structurellement identique `_open_ai_model_dialog` (#597).
- **N16 🟡 — Conversion non-RGBA non testée :** les branches non-RGBA de `pil_to_qpixmap`/`pil_to_numpy_readonly` (`image_utils.py:16`/`:43`) ne sont jamais exercées avec une image source RGB/palette/niveaux de gris (#598).

## Tickets GitHub ouverts — Triage (2026-07-16)

État en direct : **17** tickets ouverts. **#591** est achevé via PR #603 ; **#584** a été rouvert après l'audit car le gate candidat complet reste à faire, et **#585** demeure donc bloqué. Les commentaires propriétaire du 2026-07-15 sur **#245**/**#551** et leurs corps de ticket resserrés restent valides.

### Regroupements pertinents

- **Release v2.6.0** (#580 → #584 → #585 ; #583 déjà clos) : publie l'état déjà construit des mises à jour/gestion IA depuis `main` ; priorité maximale vu le faible risque et la valeur utilisateur immédiate.
- **Pipeline de hauteur 16 bits** (#581 → #587 → {#588 ‖ #589} → #590 ; l'ADR #586 déjà clos) : l'implémentation qui change le schéma (#587+) ne démarre toujours qu'après #585 (mandat de scope-freeze de #580).
- **Aperçu de relief 3D** (#582 → #592 → #593 → #594 → #595 ; #591 est achevé) : le pipeline de géométrie sans Qt #592 peut maintenant démarrer en parallèle de l'implémentation du modèle 16 bits ; #582 reste malgré tout le plus gros bloc d'effort de cette ronde.
- **#245/#551** restent liés, mais la décision stratégique est désormais prise : #551 ne suit plus que l'implémentation du modèle hybride (CodeQL automatique, Codex manuel), #245 uniquement la preuve externe de quota OpenAI.
- **#597/#598** sont des lacunes de couverture indépendantes et entièrement spécifiées (l'esquisse de test est déjà dans le ticket) – aucune chaîne, aucune dépendance envers les trois epics.

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs, **Complexité** = effort estimé, **Modèle/Effort** = modèle/effort recommandés.

| # | Titre | Pertinence | Complexité | Modèle/Effort | Prochaine étape recommandée |
|---|-------|------------|------------|----------------|-----------------------------|
| [#580](https://github.com/NikolayDA/picture_helper/issues/580) | [Epic] Release v2.6.0 | 🟠 Élevée | 🟠 Élevée | – (epic de suivi) | **In progress** – avance via #584→#585 (#583 clos), pas de PR propre. |
| [#584](https://github.com/NikolayDA/picture_helper/issues/584) | Release 2.6.0 : gate candidat, cinq artefacts | 🟠 Élevée | 🟠 Élevée | Sonnet 5 · élevé | **In progress (rouvert)** – figer le SHA final, exécuter le build sans publication de cinq artefacts avec sommes de contrôle/smokes et documenter Go/No-Go. |
| [#585](https://github.com/NikolayDA/picture_helper/issues/585) | Release 2.6.0 : tag, GitHub Release, vérification post-release | 🟠 Élevée | 🟡 Moyenne | Sonnet 5 · moyen | **Blocked** – attend #584. |
| [#587](https://github.com/NikolayDA/picture_helper/issues/587) | [16 bits] Modèle de domaine HEIGHT et ProjectHistory sans perte | 🟠 Élevée | 🟠 Élevée (très large) | Opus 4.8 · élevé | **Blocked** – #586 est clos ; n'attend plus désormais que la publication de la version (#585). |
| [#588](https://github.com/NikolayDA/picture_helper/issues/588) | [16 bits] Format de projet v2 : persistance, migration, validation | 🟠 Élevée | 🟠 Élevée | Opus 4.8 · élevé | **Blocked** – attend #587. |
| [#589](https://github.com/NikolayDA/picture_helper/issues/589) | [16 bits] Import/génération/opérations de hauteur sans quantification 8 bits | 🟠 Élevée | 🟠 Élevée | Opus 4.8 · élevé | **Blocked** – attend #587. |
| [#590](https://github.com/NikolayDA/picture_helper/issues/590) | [16 bits] Aperçu, export, UI, recette end-to-end | 🟠 Élevée | 🟠 Élevée | Opus 4.8 · élevé | **Blocked** – attend #588/#589. |
| [#581](https://github.com/NikolayDA/picture_helper/issues/581) | [Epic] Pipeline de hauteur 16 bits de bout en bout | 🟠 Élevée | 🟠 Élevée (très large) | – (epic de suivi) | **In progress** – avance via #587→(#588‖#589)→#590 (#586 clos). |
| [#592](https://github.com/NikolayDA/picture_helper/issues/592) | [3D] Pipeline de géométrie/normales/décimation sans Qt | 🟡 Moyenne | 🟠 Élevée (très large) | Opus 4.8 · élevé | **Ready for PR** – #586 et #591 sont achevés ; plus aucune dépendance ouverte. |
| [#593](https://github.com/NikolayDA/picture_helper/issues/593) | [3D] Visualiseur interactif avec orbit/pan/zoom, fallback | 🟡 Moyenne | 🟠 Élevée (très large) | Opus 4.8 · xélevé | **Blocked** – attend #592 ; la partie la plus risquée (Qt/OpenGL spécifique à la plateforme). |
| [#594](https://github.com/NikolayDA/picture_helper/issues/594) | [3D] Intégration workflow, état et cache | 🟡 Moyenne | 🟠 Élevée (très large) | Opus 4.8 · élevé | **Blocked** – attend #593, #587, #588. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, packaging, documentation, recette end-to-end | 🟡 Moyenne | 🟠 Élevée | Sonnet 5 · élevé | **Blocked** – attend #594. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Véritable aperçu de relief 3D | 🟡 Moyenne | 🟠 Élevée (très large) | – (epic de suivi) | **In progress** – avance via #592→…→#595 ; #591 est achevé. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Automatiser CodeQL, n'exécuter Codex Security que manuellement | 🟡 Moyenne | 🟡 Moyenne | Sonnet 5 · moyen | **Ready for PR** – décision stratégique prise le 2026-07-15 (modèle hybride : CodeQL automatique + Codex manuel via `workflow_dispatch`) ; le corps du ticket contient déjà la checklist complète de mise en œuvre. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurer le quota OpenAI pour la vérification manuelle Codex Security | 🟢 Faible | 🟢 Faible | – (aucune tâche de code) | **Blocked (external)** – périmètre resserré encore le 2026-07-15 : purement un tracker externe de facturation/quota OpenAI, ne bloque ni CodeQL, ni la publication, ni #551. |
| [#597](https://github.com/NikolayDA/picture_helper/issues/597) | test : `_open_ai_install_dialog` sans test de câblage (N15) | 🟢 Faible | 🟢 Faible | Sonnet 5 · faible | **Ready for PR** – l'esquisse de test est déjà dans le ticket, aucune dépendance. |
| [#598](https://github.com/NikolayDA/picture_helper/issues/598) | test : chemins de conversion non-RGBA non testés dans `image_utils.py` (N16) | 🟢 Faible | 🟢 Faible | Sonnet 5 · faible | **Ready for PR** – l'esquisse de test est déjà dans le ticket, aucune dépendance ; peut être combiné avec #597 en un seul PR. |

### Recommandé ensuite (ordre des PR)

1. **#584** — achever réellement le gate rouvert : prouver le SHA final, cinq artefacts réels, les sommes de contrôle, les smokes plateforme et Go/No-Go.
2. **#592** — démarrer maintenant le pipeline de géométrie 3D : #586 et #591 sont achevés, aucune dépendance ne reste ouverte.
3. **#551** — passer à la mise en œuvre du modèle hybride déjà décidé (automatiser CodeQL pour Python, réduire le workflow Codex à un `workflow_dispatch` pur) ; plus aucune question de stratégie ouverte.
4. **#597 + #598** — le gain de couverture le plus rapide de cette ronde, les deux esquisses de test sont déjà dans les tickets ; réalisable en un seul PR commun.
5. **#585** ainsi que tous les sous-tickets 16 bits/3D restants suivent leurs dépendances de façon séquentielle – voir le tableau, aucun déclencheur supplémentaire nécessaire.

*Dérive :* le suivi en direct a révélé la clôture prématurée de #584 et l'achèvement réel de #591. #584 est rouvert ; les futures mises à jour doivent revérifier statuts, checklists et dépendances en direct plutôt que reporter un horodatage.

## Tours précédents

- **2026-07-15/16 (suivi d'audit)** — #583/#586/#591 achevés ; #584 rouvert après confirmation que le gate candidat reste à faire ; état en direct 17.
- **2026-07-14** — état en direct toujours à 2 tickets ouverts (#245, #551), inchangé depuis la clôture de l'epic la veille.
- **2026-07-13 (clôture d'epic)** — epic **#563** entièrement clos : les huit sous-tickets (**#564–#571**) fermés via PR #573/#574 ; instantané réduit à 2.
- **2026-07-13 (audit des tickets)** — epic **#563** + huit sous-tickets ouverts, les 11 tickets ouverts réévalués, commentaires du propriétaire pris en compte ; aucun fermé ; instantané mis à jour à 11.
- **2026-07-12** — formalisation v2.3.0 (#550), correctif SessionStart (#553), sync (#549, modèle de PR #552 via PR #557), audit (#542 clos, #549–#553 ouverts) et version **v2.5.0** (vague #435/#392/#426/#389, #299/#541/#318).
- **2026-07-11** — epic #425 achevé (#430 PR #526, i18n runtime ES/FR/UK/ZH complète, **O1** fait ; #431/#432 PR #529 ; suivi final #530/#531 PR #533/#535).
- **2026-07-05–10** — #509/#510/#514–#517 (PR #520–#522), #490, vague Dark Mode/icônes rail, inspecteur en cartes (#413/#414), #499–#501/#503, peaufinage icônes/barre d'état.
- **2026-06-29** — #404/#406/#408 achevés (PR #412), vague de redesign ouverte.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, achevée ou écartée en cas de faux positif.

Constats historiques et journaux de travail (tours 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
