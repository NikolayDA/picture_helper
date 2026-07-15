[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-15)

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests locale restent la base avant tout nouveau PR. La version **v2.5.0** a été publiée le 2026-07-11 (PR #538) ; la vague de rollout **#435/#392/#426/#389** est close, ainsi que **#299** (PR #539) avec le suivi N13 **#541** (PR #543), **#318** (PR #540) et la synchronisation d'instantané **#542**. Un audit du dépôt du 2026-07-12 a ouvert **#549–#553** ; **#552/#549/#553/#550** sont désormais clos via PR #557–#560. L'epic **#563** (« vérification des mises à jour et gestion du modèle d'IA », huit sous-tickets **#564–#571**) a été entièrement implémenté et clos le 2026-07-13 via PR #573/#574 (**N14**). État en direct : **20** tickets ouverts – les tickets préexistants #245/#551 plus trois epics ouverts le 2026-07-15 (**Release v2.6.0** #580 avec sous-tickets #583–#585, le **pipeline de hauteur 16 bits** #581 avec sous-tickets #586–#590, l'**aperçu de relief 3D** #582 avec sous-tickets #591–#595) plus deux constats de couverture de tests **N15/N16** (#597/#598) ouverts le même jour suite à un audit de couverture.

### Terminé depuis la dernière revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8** et **O2–O7** restent faits ; les epics **#329/#344/#358/#384** (N9–N12) plus le correctif d'export **#363** fusionnés/archivés ; depuis le 2026-06-25, également **#404/#406/#408** (PR #412) clos.
- **Redesign et publication v2.5.0 :** cœur du redesign/rail/zoom/inspecteur en cartes/Dark Mode/suivi UI (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) via PR #412–#522 ; vague de publication **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, modèle de PR **#552**, sync **#549**, correctif SessionStart **#553**, formalisation v2.3.0 **#550** – tout clos depuis le 2026-07-12.
- **N14 — Epic #563 (mises à jour de l'app et gestion du modèle d'IA) entièrement clos :** `app_update.py` (#564), `ai_model_status.py` (#568), intégration menu/dialogue (#565/#569), vérification automatique optionnelle au démarrage (#566), câblage du warmup avec observateurs multiples/annulation coopérative (#570) via PR #573/#574 ; clôture documentation (#567/#571).

### Encore ouvert

- **O8 🟢 — Imprécision du prototype :** les outils de hauteur restent verrouillés dans la maquette après génération ; n'affecte que la simulation (#347).
- **N15 🟡 — Câblage de dialogue non testé :** `MainWindow._open_ai_install_dialog` (`main_window.py:1566`) n'a aucun test dédié, contrairement à la méthode sœur structurellement identique `_open_ai_model_dialog` (#597).
- **N16 🟡 — Conversion non-RGBA non testée :** les branches non-RGBA de `pil_to_qpixmap`/`pil_to_numpy_readonly` (`image_utils.py:16`/`:43`) ne sont jamais exercées avec une image source RGB/palette/niveaux de gris (#598).

## Tickets GitHub ouverts — Triage (2026-07-15)

État en direct : **20** tickets ouverts – une nouvelle hausse depuis les **18** précédents : en plus des trois epics, deux constats de couverture de tests issus d'un audit du 2026-07-15 ont été ouverts (**#597**/**#598**, correspondant à **N15**/**N16** ci-dessus). La vérification des commentaires n'a rien trouvé nécessitant une action : #245 a été commenté pour la dernière fois le 2026-06-19 (statut toujours valide), et les 19 autres tickets n'ont aucun commentaire.

### Regroupements pertinents

- **Release v2.6.0** (#580 → #583 → #584 → #585, strictement séquentiel) : publie l'état déjà construit des mises à jour/gestion IA depuis `main` ; priorité maximale vu le faible risque et la valeur utilisateur immédiate.
- **Pipeline de hauteur 16 bits** (#581 → #586 → #587 → {#588 ‖ #589} → #590) : #586 (ADR) peut explicitement avancer en parallèle de la publication, mais l'implémentation qui change le schéma (#587+) ne démarre qu'après #585 (mandat de scope-freeze de #580).
- **Aperçu de relief 3D** (#582 → #591 → #592 → #593 → #594 → #595) : #591 dépend en plus de #586 (il consomme le même contrat HEIGHT) – #582 est donc de fait en aval de la chaîne 16 bits et représente le plus gros bloc d'effort de cette ronde.
- **#245/#551** restent liés (scan Codex : action de compte vs. décision stratégique).
- **#597/#598** sont des lacunes de couverture indépendantes et entièrement spécifiées (l'esquisse de test est déjà dans le ticket) – aucune chaîne, aucune dépendance envers les trois epics.

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs, **Complexité** = effort estimé, **Modèle/Effort** = modèle/effort recommandés.

| # | Titre | Pertinence | Complexité | Modèle/Effort | Prochaine étape recommandée |
|---|-------|------------|------------|----------------|-----------------------------|
| [#580](https://github.com/NikolayDA/picture_helper/issues/580) | [Epic] Release v2.6.0 | 🟠 Élevée | 🟠 Élevée | – (epic de suivi) | **In progress** – avance via #583→#584→#585, pas de PR propre. |
| [#583](https://github.com/NikolayDA/picture_helper/issues/583) | Release 2.6.0 : scope-freeze, version, CHANGELOG | 🟠 Élevée | 🟡 Moyenne | Sonnet 5 · moyen | **Ready for PR** – aucune dépendance ouverte, fige la valeur utilisateur déjà construite à faible risque. |
| [#584](https://github.com/NikolayDA/picture_helper/issues/584) | Release 2.6.0 : gate candidat, cinq artefacts | 🟠 Élevée | 🟠 Élevée | Sonnet 5 · élevé | **Blocked** – attend #583 ; les cinq smokes d'artefacts se prêtent bien à une orchestration parallèle par workflow. |
| [#585](https://github.com/NikolayDA/picture_helper/issues/585) | Release 2.6.0 : tag, GitHub Release, vérification post-release | 🟠 Élevée | 🟡 Moyenne | Sonnet 5 · moyen | **Blocked** – attend #584. |
| [#586](https://github.com/NikolayDA/picture_helper/issues/586) | [16 bits] ADR : contrat de données HEIGHT canonique, migration, budget mémoire | 🟠 Élevée | 🟠 Élevée | Opus 4.8 · élevé | **Ready for PR** – travail pur d'analyse/ADR, peut avancer en parallèle de la publication ; bloque #587–590 et #591. |
| [#587](https://github.com/NikolayDA/picture_helper/issues/587) | [16 bits] Modèle de domaine HEIGHT et ProjectHistory sans perte | 🟠 Élevée | 🟠 Élevée (très large) | Opus 4.8 · élevé | **Blocked** – attend #586 et la publication de la version (#585). |
| [#588](https://github.com/NikolayDA/picture_helper/issues/588) | [16 bits] Format de projet v2 : persistance, migration, validation | 🟠 Élevée | 🟠 Élevée | Opus 4.8 · élevé | **Blocked** – attend #586/#587. |
| [#589](https://github.com/NikolayDA/picture_helper/issues/589) | [16 bits] Import/génération/opérations de hauteur sans quantification 8 bits | 🟠 Élevée | 🟠 Élevée | Opus 4.8 · élevé | **Blocked** – attend #586/#587. |
| [#590](https://github.com/NikolayDA/picture_helper/issues/590) | [16 bits] Aperçu, export, UI, recette end-to-end | 🟠 Élevée | 🟠 Élevée | Opus 4.8 · élevé | **Blocked** – attend #588/#589. |
| [#581](https://github.com/NikolayDA/picture_helper/issues/581) | [Epic] Pipeline de hauteur 16 bits de bout en bout | 🟠 Élevée | 🟠 Élevée (très large) | – (epic de suivi) | **In progress** – avance via #586→#587→(#588‖#589)→#590. |
| [#591](https://github.com/NikolayDA/picture_helper/issues/591) | [3D] ADR/contrat UX : backend de rendu, fallback, budgets | 🟡 Moyenne | 🟠 Élevée | Opus 4.8 · élevé | **Blocked** – attend l'acceptation de #586. |
| [#592](https://github.com/NikolayDA/picture_helper/issues/592) | [3D] Pipeline de géométrie/normales/décimation sans Qt | 🟡 Moyenne | 🟠 Élevée (très large) | Opus 4.8 · élevé | **Blocked** – attend #586/#591. |
| [#593](https://github.com/NikolayDA/picture_helper/issues/593) | [3D] Visualiseur interactif avec orbit/pan/zoom, fallback | 🟡 Moyenne | 🟠 Élevée (très large) | Opus 4.8 · xélevé | **Blocked** – attend #591/#592 ; la partie la plus risquée (Qt/OpenGL spécifique à la plateforme). |
| [#594](https://github.com/NikolayDA/picture_helper/issues/594) | [3D] Intégration workflow, état et cache | 🟡 Moyenne | 🟠 Élevée (très large) | Opus 4.8 · élevé | **Blocked** – attend #593, #587, #588. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, packaging, documentation, recette end-to-end | 🟡 Moyenne | 🟠 Élevée | Sonnet 5 · élevé | **Blocked** – attend #594. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Véritable aperçu de relief 3D | 🟡 Moyenne | 🟠 Élevée (très large) | – (epic de suivi) | **In progress** – avance via #591→…→#595 ; bloqué par #586. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Décision de stratégie pour Codex Security Scan (réactiver/retirer/remplacer) | 🟡 Moyenne | 🟡 Moyenne | Sonnet 5 · moyen | **Ready for PR** – la recommandation reste l'option 2 (retirer/désactiver), désormais bloquée en externe depuis 5+ semaines. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan « Quota exceeded » | 🟢 Faible | 🟢 Faible | – (aucune tâche de code) | **Blocked (external)** – restaurer la facturation/le quota OpenAI est une action de compte, pas un PR. |
| [#597](https://github.com/NikolayDA/picture_helper/issues/597) | test : `_open_ai_install_dialog` sans test de câblage (N15) | 🟢 Faible | 🟢 Faible | Sonnet 5 · faible | **Ready for PR** – l'esquisse de test est déjà dans le ticket, aucune dépendance. |
| [#598](https://github.com/NikolayDA/picture_helper/issues/598) | test : chemins de conversion non-RGBA non testés dans `image_utils.py` (N16) | 🟢 Faible | 🟢 Faible | Sonnet 5 · faible | **Ready for PR** – l'esquisse de test est déjà dans le ticket, aucune dépendance ; peut être combiné avec #597 en un seul PR. |

### Recommandé ensuite (ordre des PR)

1. **#583** — traiter d'abord le scope-freeze de v2.6.0 : aucune dépendance ouverte, fige la valeur utilisateur déjà construite à faible risque.
2. **#586** — démarrer dès maintenant l'ADR 16 bits plutôt qu'après #585 : il bloque deux epics complets (#581 directement, #582 indirectement via #591) et peut explicitement avancer en parallèle de la publication.
3. **#551** — trancher la décision de stratégie, courte et indépendante ; la recommandation reste l'option 2 (retirer/désactiver).
4. **#597 + #598** — le gain de couverture le plus rapide de cette ronde, les deux esquisses de test sont déjà dans les tickets ; réalisable en un seul PR commun.
5. **#584/#585** ainsi que tous les sous-tickets 16 bits/3D suivent leurs dépendances de façon séquentielle – voir le tableau, aucun déclencheur supplémentaire nécessaire.

*Dérive :* revérifier en direct le nombre de tickets ouverts avant chaque mise à jour, sans le reporter tel quel – le bond de 2 à 18 plus les deux tickets de couverture (#597/#598) ouverts peu après montrent à quelle vitesse l'instantané se périme.

## Tours précédents

- **2026-07-14** — état en direct toujours à 2 tickets ouverts (#245, #551), inchangé depuis la clôture de l'epic la veille.
- **2026-07-13 (clôture d'epic)** — epic **#563** entièrement clos : les huit sous-tickets (**#564–#571**) fermés via PR #573/#574 ; instantané réduit à 2.
- **2026-07-13 (audit des tickets)** — epic **#563** + huit sous-tickets ouverts, les 11 tickets ouverts réévalués, commentaires du propriétaire pris en compte ; aucun fermé ; instantané mis à jour à 11.
- **2026-07-12** — formalisation v2.3.0 (#550), correctif SessionStart (#553), sync (#549, modèle de PR #552 via PR #557), audit (#542 clos, #549–#553 ouverts) et version **v2.5.0** (vague #435/#392/#426/#389, #299/#541/#318).
- **2026-07-11** — epic #425 achevé (#430 PR #526, i18n runtime ES/FR/UK/ZH complète, **O1** fait ; #431/#432 PR #529 ; suivi final #530/#531 PR #533/#535).
- **2026-07-05–10** — #509/#510/#514–#517 (PR #520–#522), #490, vague Dark Mode/icônes rail, inspecteur en cartes (#413/#414), #499–#501/#503, peaufinage icônes/barre d'état.
- **2026-06-29** — #404/#406/#408 achevés (PR #412), vague de redesign ouverte.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, achevée ou écartée en cas de faux positif.

Constats historiques et journaux de travail (tours 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
