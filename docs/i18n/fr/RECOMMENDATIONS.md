[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-18)

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests locale restent la base avant tout nouveau PR. La version **v2.6.0** a été publiée le 2026-07-16 depuis le commit approuvé `f24cef69829da8e37aa400dad471dc4d607b89b3` : workflow du tag [29531147950](https://github.com/NikolayDA/picture_helper/actions/runs/29531147950), [release GitHub publique](https://github.com/NikolayDA/picture_helper/releases/tag/v2.6.0), cinq artefacts applicatifs retéléchargés et vérifiés par SHA-256, et smokes natifs verts pour Linux x86_64/aarch64 et macOS arm64. Les tickets de release **#580/#583/#584/#585**, le constat **#607**, le pipeline 16 bits **#581/#587–#590** et le modèle de sécurité hybride **#551** sont achevés. État en direct : **3** tickets ouverts — #245 et **#582/#595** rouverts.

### Terminé depuis la dernière revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8** et **O2–O7** restent faits ; les epics **#329/#344/#358/#384** (N9–N12) plus le correctif d'export **#363** fusionnés/archivés ; depuis le 2026-06-25, également **#404/#406/#408** (PR #412) clos.
- **Redesign et publication v2.5.0 :** cœur du redesign/rail/zoom/inspecteur en cartes/Dark Mode/suivi UI (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) via PR #412–#522 ; vague de publication **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, modèle de PR **#552**, sync **#549**, correctif SessionStart **#553**, formalisation v2.3.0 **#550** – tout clos depuis le 2026-07-12.
- **N14 — Epic #563 (mises à jour de l'app et gestion du modèle d'IA) entièrement clos :** `app_update.py` (#564), `ai_model_status.py` (#568), intégration menu/dialogue (#565/#569), vérification automatique optionnelle au démarrage (#566), câblage du warmup avec observateurs multiples/annulation coopérative (#570) via PR #573/#574 ; clôture documentation (#567/#571).
- **Release v2.6.0 entièrement achevée :** scope-freeze (#583), gate candidat sur le SHA final de `main` (#584), tag/release/vérification post-release (#585) et epic de suivi #580 sont terminés ; cette mise à jour résout la dérive #607. L'ADR HEIGHT 16 bits (#586) et le contrat ADR/UX 3D (#591, PR #603) restent également achevés.
- **Pipeline de hauteur 16 bits entièrement achevé :** modèle de domaine/historique et format de projet v2 (#587/#588, PR #610), import/génération/opérations (#589, PR #612), puis aperçu/export/UI/E2E (#590, PR #613) sont dans `main` ; l'epic #581 est clos après des gates verts, des revues résolues et une matrice de recette complète.
- **Suivi d'audit #614–#616 achevé :** les versions futures sont refusées de façon sûre (#588, PR #614), les lacunes de couverture #597/#598 sont closes via PR #615 et la lacune du guide #606 est corrigée dans les six langues via PR #616.
- **Modèle de sécurité et cœur 3D implémentés :** #551 est achevé via PR #619 ; #592–#594 sont dans `main` via PR #620. L'audit suivant a rouvert #582/#595 car les preuves packaging/plateformes, la recette performance complète et les captures manquent encore.

### Encore ouvert

- **O8 🟢 — Imprécision du prototype :** les outils de hauteur restent verrouillés dans la maquette après génération ; n'affecte que la simulation (#347).

## Tickets GitHub ouverts — Triage (2026-07-18)

État en direct après les PR #619/#620 et l'audit suivant : **3** tickets ouverts. **#551** et **#592–#594** sont achevés ; **#582/#595** sont rouverts pour la recette finale.

### Regroupements pertinents

- **Recette finale 3D** (#582 → #595) : #592–#594 sont achevés ; #595 suit les preuves packaging/plateformes, performance complète, captures et matrice finale.
- **#245** reste un tracker externe de quota OpenAI et ne bloque ni CodeQL, ni publication, ni 3D.

Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs, **Complexité** = effort estimé, **Modèle/Effort** = modèle/effort recommandés.

| # | Titre | Pertinence | Complexité | Modèle/Effort | Prochaine étape recommandée |
|---|-------|------------|------------|----------------|-----------------------------|
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, packaging, documentation, recette end-to-end | 🟡 Moyenne | 🟠 Élevée | Sonnet 5 · élevé | **In progress** – preuves packaging/plateformes, performance complète, captures et matrice finale manquantes. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Véritable aperçu de relief 3D | 🟡 Moyenne | 🟠 Élevée (très large) | – (epic de suivi) | **In progress** – #591–#594 achevés ; attend seulement #595. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurer le quota OpenAI pour la vérification manuelle Codex Security | 🟢 Faible | 🟢 Faible | – (aucune tâche de code) | **Blocked (external)** – périmètre resserré encore le 2026-07-15 : purement un tracker externe de facturation/quota OpenAI, ne bloque ni CodeQL, ni la publication, ni #551. |

### Recommandé ensuite (ordre des PR)

1. **#595** — compléter les preuves restantes avant de clore #582.

*Dérive :* cette mise à jour retire #551/#592–#594 du triage ouvert, rouvre #582/#595 pour preuves manquantes et corrige le compteur à 3.

## Tours précédents

- **2026-07-18 (audit post-merge)** — #551 et #592–#594 confirmés ; #582/#595 rouverts pour preuves manquantes ; état en direct 3.
- **2026-07-18 (suivi d'audit #614–#616)** — durcissement des versions futures de la PR #614 consigné ; #597/#598 achevés via PR #615 et #606 via PR #616 ; état en direct 7.
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
