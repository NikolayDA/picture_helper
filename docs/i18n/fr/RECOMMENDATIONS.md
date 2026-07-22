[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-22, après la clôture de la recette)

Ruff, mypy et la suite de tests locale restent la base avant tout nouveau PR. Le nouveau dispatch `release-abnahme.yml` demandé au tour précédent a été déclenché (exécution [#4](https://github.com/NikolayDA/picture_helper/actions/runs/29908256619), commit `9165c00`, après #657/#658) et a produit une matrice entièrement verte à l'exception de la ligne Linux x86_64 délibérément en pause. Sur cette base, les quatre tickets auparavant bloqués ont été **vérifiés et fermés individuellement par rapport à leurs propres critères d'acceptation** — aucun ticket ne s'est fermé automatiquement avec un autre :

1. **#595** — tous les points de la liste « toujours ouvert » sont satisfaits, **à l'exception** de la ligne Linux x86_64 délibérément en pause : selon l'ADR/`RELEASE_AUTOMATION.md`, elle reste « déclarée ouverte, non satisfaite » — pour cette fermeture, elle a été traitée explicitement comme une exception accordée (waiver), et non requalifiée en critère satisfait (à l'image du propre critère d'acceptation de #639).
2. **#646** — cinq critères sur six étaient déjà satisfaits ; une véritable lacune a été trouvée : `scripts/abnahme_vision_check.py`/`abnahme_aggregate.py` étaient entièrement exclus de `make type`/`make check`, et une exécution stricte d'essai a révélé une véritable erreur `union-attr`. Corrigée et fusionnée via le PR #662 (commit `f47445f`).
3. **#639** — #646 étant fermé, les huit tickets enfants sont désormais fermés ; la liste de contrôle du corps du ticket a été mise à jour.
4. **#582** — les cinq tickets enfants sont fermés ; la décision requise sur la texture comme objectif optionnel figure déjà dans l'ADR, la lacune du README relevée lors de l'audit du 2026-07-20 est corrigée, et `make ui` est confirmé vert.

De plus, deux nouveaux tickets issus d'audits automatisés sont apparus depuis le dernier tour : **#660** est déjà terminé et n'attend plus qu'une fusion, tandis que **#659** attend véritablement une décision du propriétaire.

État en direct : **4** tickets ouverts.

### Résultat de la revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7** et tout ce qui a été achevé depuis le **2026-06-25** reste fait.
- **#646/#639/#595/#582 sont désormais vérifiés individuellement et fermés** (sans effet domino de fermeture automatique) ; l'unique véritable lacune trouvée au passage (rigueur mypy pour les scripts de recette, #646) a été corrigée et fusionnée via le PR #662.
- **#659/#660 sont nouveaux :** #660 est **prêt pour un PR** – un correctif terminé mais non fusionné se trouve déjà sur la branche `claude/festive-gates-4dkzds` (commit `80b7aa0`) ; il n'y a plus rien à décider, seulement à fusionner. #659, en revanche, reste véritablement **non tranché** : une analyse pure sans changement de code, proposant deux nouveaux identifiants de constat (**N9**/**O8**), encore en attente de validation du propriétaire.
- L'étape restante n'est donc **plus** un sujet de recette — il s'agit d'ouvrir/fusionner un PR pour #660 et d'obtenir une décision sur les constats proposés dans #659.

## Tickets GitHub ouverts — Triage (2026-07-22)

| # | Titre | Pertinence | Complexité | Modèle recommandé (effort) | Prochaine étape |
|---|-------|------------|------------|------------------------------|------------------|
| [#660](https://github.com/NikolayDA/picture_helper/issues/660) | Audit de TESTING.md : à jour, une petite lacune corrigée (marqueur `gl_smoke` non documenté) | 🟢 Faible (pure exactitude documentaire, aucun impact fonctionnel) | 🟢 Faible (un court paragraphe, déjà implémenté) | – (aucun agent nécessaire ; le correctif est déjà sur la branche `claude/festive-gates-4dkzds`, commit `80b7aa0`) | Ready for PR – il ne reste qu'à l'ouvrir/le fusionner, puis fermer le ticket |
| [#659](https://github.com/NikolayDA/picture_helper/issues/659) | Audit de la suite de tests : petites lacunes de qualité en 6 lots (`test_i18n_sync`, `test_viewer_3d`, etc.) | 🟡 Moyenne (qualité/couverture des tests, pas un blocage) | 🟡 Moyenne (mélange de suppressions/correctifs triviaux et de véritables lacunes de couverture sur plusieurs modules) | Sonnet 5 (moyen) – si adopté comme N9/O8 | Needs decision – proposition pas encore intégrée à la liste des constats ; validation du propriétaire en attente, puis mise en œuvre en tant que PR dédié |
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Activer le secret ANTHROPIC_API_KEY pour la pré-évaluation vision | 🟡 Moyenne (améliore seulement la qualité des preuves ; pas un blocage selon le contrat) | 🟢 Faible (purement opérationnel, aucun code) | – (aucun agent ; propriétaire du dépôt : Settings → Secrets) | Bloquée (externe) – réalisable indépendamment |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurer le quota OpenAI pour la vérification manuelle Codex Security | 🟢 Faible (ne bloque qu'un scan manuel optionnel) | 🟢 Faible (purement opérationnel, aucun code) | – (aucun agent ; propriétaire du dépôt : facturation) | Bloquée (externe) – régler la facturation/le quota sur le projet de la plateforme OpenAI |

### Recommandé ensuite

1. **#660** : ouvrir un PR pour le correctif TESTING.md déjà validé (branche `claude/festive-gates-4dkzds`, commit `80b7aa0`) et le fusionner ; puis fermer le ticket.
2. **#659** : décider si les constats proposés **N9** (supprimer/fusionner le poids mort `test_i18n_sync.py`) et **O8** (assertions tautologiques dans `viewer_3d` plus lacunes de couverture dans `screenshot3d.py`/`viewer_3d.py`/`preview3d_capability.py`/`height_map.py`/`gloss_preview.py`) sont adoptés ; mettre en œuvre comme PR dédié en cas d'accord.
3. Traiter **#656** indépendamment si de véritables verdicts vision sont souhaités — c'est une amélioration de qualité, pas un blocage.
4. Laisser **#245** comme pur tracker externe de facturation/quota ; aucune action possible ni nécessaire dans le dépôt.
5. La chaîne recette/epic 3D (#646/#639/#595/#582) est entièrement close et ne nécessite plus aucune action.

## Tours précédents

- **2026-07-22 (clôture de la recette)** — nouveau dispatch `release-abnahme.yml` déclenché (exécution #4, commit `9165c00`) ; matrice comparée à #595 (x86_64 reste documentée en pause mais ne bloque pas) ; #595, #646, #639, #582 vérifiés et fermés individuellement par rapport à leurs propres critères d'acceptation. L'unique véritable lacune trouvée (rigueur mypy pour `scripts/abnahme_vision_check.py`/`abnahme_aggregate.py`, #646) corrigée et fusionnée via le PR #662. Deux nouveaux tickets d'audit enregistrés : #660 avec un correctif terminé non fusionné (prêt pour un PR), #659 en attente d'une véritable décision du propriétaire sur les constats proposés. État en direct : 4 tickets ouverts — le niveau le plus bas depuis le début de ce journal.
- **2026-07-22 (revue des tickets, corrigée après revue Codex)** — réévaluation complète de tous les tickets ouverts ; une version antérieure surestimait ce que prouvait le dispatch du 2026-07-21 (depuis dépassé par les PR #657/#658) et présentait à tort la ligne vision consultative (#656) comme un blocage. Corrigé après revue de PR (Codex) : #656 peut être résolu indépendamment, Linux x86_64 reste un critère déclaré ouvert, et #639/#595/#582 ne se ferment pas automatiquement avec leurs tickets enfants. État en direct : 6 tickets ouverts — le niveau le plus bas depuis l'epic #582.
- **2026-07-21 (automatisation de la recette de publication, epic #639)** — epic #639 ouvert et largement implémenté en une seule journée : ADR/documentation (#640), squelette de workflow (#641), smokes matériels Linux/macOS (#642/#643), test de régression E2E (#644), suite de performance GL en direct (#645), pré-évaluation vision + matrice de recette (#646) — tous fusionnés via PR #647/#649 mais non fermés automatiquement en raison de mots-clés de clôture en allemand ; le ticket de suivi #648 (preuve de rendu 3D natif) reste la seule tâche de code ouverte. État en direct : 12 tickets ouverts.
- **2026-07-20 (smoke matériel Pi 5)** — trois véritables bogues de packaging trouvés et corrigés sur Raspberry Pi 5 (PR #627/#631) ; le démarrage de l'application est confirmé, aperçu 3D inclus.
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
