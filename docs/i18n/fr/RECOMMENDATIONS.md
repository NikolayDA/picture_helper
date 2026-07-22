[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-22, avant la préparation du release)

Ruff, mypy et la suite de tests locale restent la base avant tout nouveau PR. Depuis le dernier tour, les deux tickets d'audit auparavant ouverts ont été fermés individuellement :

1. **#660** — le correctif TESTING.md déjà terminé (branche `claude/festive-gates-4dkzds`, commit `80b7aa0`) a été fusionné via le PR #664 (commit `92c14ba`) : un court paragraphe sur le marqueur `gl_smoke` a été ajouté.
2. **#659** — la validation du propriétaire pour **N9**/**O8** est acquise ; les neuf points de la liste de mise en œuvre ont été réalisés via le PR #665 (commit `c4ab92a`) : `tests/test_i18n_sync.py` supprimé en tant que porte souple redondante (toujours couvert par le test strict `test_i18n_docs.py`), les assertions tautologiques/conditionnellement vides de `test_viewer_3d.py` remplacées par des vérifications déterministes, la distribution souris/molette/clavier ainsi que les branches négatives post-« ready » dans `screenshot3d.py`/`viewer_3d.py`/`preview3d_capability.py`/`height_map.py` testées isolément, les doublons de copier-coller confirmés supprimés, les vérifications redondantes de release/EufyMake consolidées. `make check` : 1995 passed/5 skipped (base 1962/5) ; `make coverage` : 93 % (base 92 %, gate `fail_under=86`). Le problème de big-endian suspecté dans `gloss_preview.py` **n'a pas** été confirmé (aucun bug de production).

De plus, deux PR purement liés aux assets ont été fusionnés et n'ont **toujours pas d'entrée CHANGELOG** : **#666** (un nouveau jeu complet de captures d'écran, y compris les états 3D natifs, provenance du rendu Apple M3 Max) et **#667** (une nouvelle icône d'application « Liquid Glass », 1024×1024 RGBA — le `.icns` macOS, l'AppImage et le `.deb` dérivent tous du même master `BgRemover_icon.png` ; les tests de packaging Linux ont été étendus pour vérifier dimensions/canal alpha).

État en direct : **2** tickets ouverts — le niveau le plus bas depuis le début de ce journal.

### Résultat de la revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7** et tout ce qui a été achevé depuis le **2026-06-25** reste fait.
- **#660/#659 sont désormais vérifiés et fermés**, chacun via son propre PR (#664/#665), sans effet domino de fermeture automatique. **N9**/**O8** doivent désormais être considérés comme achevés.
- **Aucun blocage de code ouvert :** les deux tickets restants (#656, #245) sont, selon leurs propres listes de critères d'acceptation, purement externes/opérationnels (configurer un secret vs. facturation/quota) et explicitement **pas un blocage pour le release**.
- **Nouvellement identifié (cette revue) :** en vue de la prochaine préparation de release, la section `[Unreleased]` de `CHANGELOG.md` est déjà bien remplie (pipeline de hauteur 16 bits #581, aperçu de relief 3D #582, refonte CodeQL/Codex #551), mais `pyproject.toml`/`LICENSES.md`/`de.bgremover.app.metainfo.xml` restent à `2.6.0` — un incrément de version et le déplacement des entrées du CHANGELOG sont nécessaires avant le prochain tag. Les assets de #666/#667 (icône/captures) n'ont encore aucune ligne CHANGELOG.

## Tickets GitHub ouverts — Triage (2026-07-22)

| # | Titre | Pertinence | Complexité | Modèle recommandé (effort) | Prochaine étape |
|---|-------|------------|------------|------------------------------|------------------|
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Activer le secret ANTHROPIC_API_KEY pour la pré-évaluation vision | 🟡 Moyenne (améliore seulement la qualité des preuves ; pas un blocage selon le contrat) | 🟢 Faible (purement opérationnel, aucun code) | – (aucun agent ; propriétaire du dépôt : Settings → Secrets) | Bloquée (externe) – réalisable indépendamment |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurer le quota OpenAI pour la vérification manuelle Codex Security | 🟢 Faible (ne bloque qu'un scan manuel optionnel) | 🟢 Faible (purement opérationnel, aucun code) | – (aucun agent ; propriétaire du dépôt : facturation) | Bloquée (externe) – régler la facturation/le quota sur le projet de la plateforme OpenAI |

### Recommandé ensuite

1. Traiter **#656** indépendamment si de véritables verdicts vision sont souhaités — c'est une amélioration de qualité, pas un blocage.
2. Laisser **#245** comme pur tracker externe de facturation/quota ; aucune action possible ni nécessaire dans le dépôt.
3. La chaîne recette/3D/audit de tests (#646/#639/#595/#582/#659/#660) est entièrement close et ne nécessite plus aucune action.
4. Pour le prochain release : incrémenter la version (`pyproject.toml` + `CHANGELOG.md`/`LICENSES.md` + traductions + `de.bgremover.app.metainfo.xml`), déplacer `[Unreleased]` vers une nouvelle section de version, exécuter le gate candidat (`make pr-check`/`coverage`/`ui` + matrice CI complète) et déclencher un nouveau dispatch `release-abnahme.yml` contre le commit cible réel (la dernière exécution, exécution #4/commit `9165c00`, précède le changement d'icône #667).

## Tours précédents

- **2026-07-22 (clôture de l'audit de tests)** — les deux tickets d'audit auparavant ouverts ont été fermés : #660 via le PR #664 (commit `92c14ba`, marqueur `gl_smoke` documenté dans TESTING.md), #659 via le PR #665 (commit `c4ab92a`, N9/O8 entièrement mis en œuvre, `make check` 1995/5, `make coverage` 93 %). Deux PR liés aux assets également fusionnés (#666 jeu de captures, #667 nouvelle icône d'application), tous deux encore sans entrée CHANGELOG. État en direct : 2 tickets ouverts (tous deux externes/opérationnels, pas un blocage) — le niveau le plus bas depuis le début de ce journal.
- **2026-07-22 (clôture de la recette)** — nouveau dispatch `release-abnahme.yml` déclenché (exécution #4, commit `9165c00`) ; matrice comparée à #595 (x86_64 reste documentée en pause mais ne bloque pas) ; #595, #646, #639, #582 vérifiés et fermés individuellement par rapport à leurs propres critères d'acceptation. L'unique véritable lacune trouvée (rigueur mypy pour `scripts/abnahme_vision_check.py`/`abnahme_aggregate.py`, #646) corrigée et fusionnée via le PR #662. Deux nouveaux tickets d'audit enregistrés : #660 avec un correctif terminé non fusionné (prêt pour un PR), #659 en attente d'une véritable décision du propriétaire sur les constats proposés. État en direct : 4 tickets ouverts.
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
