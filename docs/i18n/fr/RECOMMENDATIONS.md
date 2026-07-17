[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-17)

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests locale restent la base avant tout nouveau PR. La version **v2.6.0** a été publiée le 2026-07-16 depuis le commit approuvé `f24cef69829da8e37aa400dad471dc4d607b89b3` : workflow du tag [29531147950](https://github.com/NikolayDA/picture_helper/actions/runs/29531147950), [release GitHub publique](https://github.com/NikolayDA/picture_helper/releases/tag/v2.6.0), cinq artefacts applicatifs retéléchargés et vérifiés par SHA-256, et smokes natifs verts pour Linux x86_64/aarch64 et macOS arm64. Les tickets de release **#580/#583/#584/#585**, le constat **#607** et le pipeline de hauteur 16 bits complet **#581/#587–#590** sont achevés. État en direct : **10** tickets ouverts — #245/#551, l'epic 3D **#582** avec #592–#595, les constats de couverture **N15/N16** (#597/#598) et la lacune du guide **#606**.

### Terminé depuis la dernière revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8** et **O2–O7** restent faits ; les epics **#329/#344/#358/#384** (N9–N12) plus le correctif d'export **#363** fusionnés/archivés ; depuis le 2026-06-25, également **#404/#406/#408** (PR #412) clos.
- **Redesign et publication v2.5.0 :** cœur du redesign/rail/zoom/inspecteur en cartes/Dark Mode/suivi UI (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) via PR #412–#522 ; vague de publication **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, modèle de PR **#552**, sync **#549**, correctif SessionStart **#553**, formalisation v2.3.0 **#550** – tout clos depuis le 2026-07-12.
- **N14 — Epic #563 (mises à jour de l'app et gestion du modèle d'IA) entièrement clos :** `app_update.py` (#564), `ai_model_status.py` (#568), intégration menu/dialogue (#565/#569), vérification automatique optionnelle au démarrage (#566), câblage du warmup avec observateurs multiples/annulation coopérative (#570) via PR #573/#574 ; clôture documentation (#567/#571).
- **Release v2.6.0 entièrement achevée :** scope-freeze (#583), gate candidat sur le SHA final de `main` (#584), tag/release/vérification post-release (#585) et epic de suivi #580 sont terminés ; cette mise à jour résout la dérive #607. L'ADR HEIGHT 16 bits (#586) et le contrat ADR/UX 3D (#591, PR #603) restent également achevés.
- **Pipeline de hauteur 16 bits entièrement achevé :** modèle de domaine/historique et format de projet v2 (#587/#588, PR #610), import/génération/opérations (#589, PR #612), puis aperçu/export/UI/E2E (#590, PR #613) sont dans `main` ; l'epic #581 est clos après des gates verts, des revues résolues et une matrice de recette complète.

### Encore ouvert

- **O8 🟢 — Imprécision du prototype :** les outils de hauteur restent verrouillés dans la maquette après génération ; n'affecte que la simulation (#347).
- **N15 🟡 — Câblage de dialogue non testé :** `MainWindow._open_ai_install_dialog` (`main_window.py:1566`) n'a aucun test dédié, contrairement à la méthode sœur structurellement identique `_open_ai_model_dialog` (#597).
- **N16 🟡 — Conversion non-RGBA non testée :** les branches non-RGBA de `pil_to_qpixmap`/`pil_to_numpy_readonly` (`image_utils.py:16`/`:43`) ne sont jamais exercées avec une image source RGB/palette/niveaux de gris (#598).
- **Lacune documentaire 🟢 — Nouvelles fonctions Extras/réglages absentes du guide :** la vérification des mises à jour, la gestion/installation du modèle IA et le réglage automatique doivent être ajoutés aux six versions d'ANLEITUNG (#606).

## Tickets GitHub ouverts — Triage (2026-07-17)

État en direct après l'achèvement du pipeline de hauteur 16 bits : **10** tickets ouverts. **#581/#587–#590** sont achevés via les PR #610/#612/#613. Les commentaires propriétaire du 2026-07-15 sur **#245**/**#551** et leurs corps de ticket resserrés restent valides.

### Regroupements pertinents

- **Aperçu de relief 3D** (#582 → #592 → #593 → #594 → #595 ; #591 et les prérequis 16 bits sont achevés) : #592 est la prochaine étape exécutable ; #594 n'attend plus que #593.
- **#245/#551** restent liés, mais la décision stratégique est désormais prise : #551 ne suit plus que l'implémentation du modèle hybride (CodeQL automatique, Codex manuel), #245 uniquement la preuve externe de quota OpenAI.
- **#597/#598** sont des lacunes de couverture indépendantes et entièrement spécifiées ; **#606** est une lacune documentaire indépendante tout aussi bien délimitée dans les six versions d'ANLEITUNG.

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs, **Complexité** = effort estimé, **Modèle/Effort** = modèle/effort recommandés.

| # | Titre | Pertinence | Complexité | Modèle/Effort | Prochaine étape recommandée |
|---|-------|------------|------------|----------------|-----------------------------|
| [#592](https://github.com/NikolayDA/picture_helper/issues/592) | [3D] Pipeline de géométrie/normales/décimation sans Qt | 🟡 Moyenne | 🟠 Élevée (très large) | Opus 4.8 · élevé | **Ready for PR** – #586 et #591 sont achevés ; plus aucune dépendance ouverte. |
| [#593](https://github.com/NikolayDA/picture_helper/issues/593) | [3D] Visualiseur interactif avec orbit/pan/zoom, fallback | 🟡 Moyenne | 🟠 Élevée (très large) | Opus 4.8 · xélevé | **Blocked** – attend #592 ; la partie la plus risquée (Qt/OpenGL spécifique à la plateforme). |
| [#594](https://github.com/NikolayDA/picture_helper/issues/594) | [3D] Intégration workflow, état et cache | 🟡 Moyenne | 🟠 Élevée (très large) | Opus 4.8 · élevé | **Blocked** – attend #593 ; les prérequis 16 bits #587/#588 sont achevés. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, packaging, documentation, recette end-to-end | 🟡 Moyenne | 🟠 Élevée | Sonnet 5 · élevé | **Blocked** – attend #594. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Véritable aperçu de relief 3D | 🟡 Moyenne | 🟠 Élevée (très large) | – (epic de suivi) | **In progress** – avance via #592→…→#595 ; #591 est achevé. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Automatiser CodeQL, n'exécuter Codex Security que manuellement | 🟡 Moyenne | 🟡 Moyenne | Sonnet 5 · moyen | **Ready for PR** – décision stratégique prise le 2026-07-15 (modèle hybride : CodeQL automatique + Codex manuel via `workflow_dispatch`) ; le corps du ticket contient déjà la checklist complète de mise en œuvre. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurer le quota OpenAI pour la vérification manuelle Codex Security | 🟢 Faible | 🟢 Faible | – (aucune tâche de code) | **Blocked (external)** – périmètre resserré encore le 2026-07-15 : purement un tracker externe de facturation/quota OpenAI, ne bloque ni CodeQL, ni la publication, ni #551. |
| [#597](https://github.com/NikolayDA/picture_helper/issues/597) | test : `_open_ai_install_dialog` sans test de câblage (N15) | 🟢 Faible | 🟢 Faible | Sonnet 5 · faible | **Ready for PR** – l'esquisse de test est déjà dans le ticket, aucune dépendance. |
| [#598](https://github.com/NikolayDA/picture_helper/issues/598) | test : chemins de conversion non-RGBA non testés dans `image_utils.py` (N16) | 🟢 Faible | 🟢 Faible | Sonnet 5 · faible | **Ready for PR** – l'esquisse de test est déjà dans le ticket, aucune dépendance ; peut être combiné avec #597 en un seul PR. |
| [#606](https://github.com/NikolayDA/picture_helper/issues/606) | docs : update check/gestion du modèle IA absents d'ANLEITUNG | 🟢 Faible | 🟢 Faible | Sonnet 5 · faible | **Ready for PR** – checklist complète dans le ticket ; mettre à jour ensemble les six versions linguistiques. |

### Recommandé ensuite (ordre des PR)

1. **#592** — démarrer le pipeline de géométrie 3D ; #586, #591 et les prérequis 16 bits sont achevés.
2. **#606** — documenter les nouveaux contrôles de mise à jour/IA dans les six versions d'ANLEITUNG.
3. **#551** — implémenter le modèle hybride convenu (CodeQL automatique, Codex uniquement manuel via `workflow_dispatch`).
4. **#597 + #598** — fermer les deux lacunes de couverture dans un petit PR.

*Dérive :* cette mise à jour retire la chaîne 16 bits achevée du triage ouvert, corrige le compteur en direct à 10 et supprime les dépendances 3D obsolètes. Les futures mises à jour continuent de revérifier statuts, checklists et dépendances en direct plutôt que de reporter un horodatage.

## Tours précédents

- **2026-07-17 (clôture de l'epic 16 bits)** — #581/#587–#590 achevés via PR #610/#612/#613 ; tous les gates et revues verts, matrice de recette présente, état en direct 10.
- **2026-07-16 (release v2.6.0)** — tag sur `f24cef69829da8e37aa400dad471dc4d607b89b3`, exécution 29531147950 verte, cinq artefacts publics retéléchargés et vérifiés par SHA-256 ; #580/#585/#607 clos, état en direct 15.
- **2026-07-16 (gate candidat)** — #584 clos via le véritable gate à cinq artefacts (exécution finale 29529595934 sur `f24cef69829da8e37aa400dad471dc4d607b89b3`, SHA-256 + analyse de secrets par artefact, smokes plateforme natifs) ; #585 débloqué.
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
