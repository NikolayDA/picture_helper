[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-23, release v2.7.0 publié)

Ruff, mypy et la suite de tests locale restent la base avant tout nouveau PR. Depuis le dernier tour, le cycle complet du release v2.7.0 est allé à son terme :

1. Le **PR #670** (incrément de version de `pyproject.toml`/`LICENSES.md`/`de.bgremover.app.metainfo.xml` vers 2.7.0, bascule du CHANGELOG `[Unreleased]` → `[2.7.0]`, entrée de l'icône #667, conciliation de RECOMMENDATIONS) a été fusionné (commit squash `6f103ed` sur `main`).
2. Comme la fusion squash a produit un **nouveau** SHA de commit (différent du `245f727` déjà validé), le gate candidat complet a été **rejoué** contre `6f103ed` — exactement la règle documentée dans `docs/history/RELEASE-2.6.0-candidate-gate.md` (« note pour #585 ») : matrice CI complète (exécution [29989059554](https://github.com/NikolayDA/picture_helper/actions/runs/29989059554), verte), build candidat (exécution [29990198925](https://github.com/NikolayDA/picture_helper/actions/runs/29990198925), les trois plateformes vertes, analyse de secrets propre), recette matérielle (exécution [29991314117](https://github.com/NikolayDA/picture_helper/actions/runs/29991314117) : macOS arm64 ✅, Linux aarch64 ✅, x86_64 documentée en pause, matrice de recette publiée sur #595).
3. Le tag `v2.7.0` a été posé sur `6f103ed` et poussé (le propriétaire du dépôt a dû le faire lui-même — le proxy git de cette session n'autorise que les push vers la branche de travail assignée, pas les tags ni `main`). L'exécution du workflow de release [29998307692](https://github.com/NikolayDA/picture_helper/actions/runs/29998307692) est verte, le job `Publish GitHub Release` a réussi : **[v2.7.0](https://github.com/NikolayDA/picture_helper/releases/tag/v2.7.0)** publié avec les cinq artefacts (AppImage + `.deb` Linux x86_64/aarch64, `.dmg` macOS arm64).

De plus, deux nouveaux tickets d'audit automatisé sont apparus depuis le dernier instantané :

- **#669** — signale à juste titre que l'état en direct précédent de ce document était obsolète (listant encore #659/#660 comme ouverts, #668 manquant). Corrigé par cette mise à jour.
- **#668** — `ANLEITUNG.md` référence encore le jeu de captures du 2026-07-19 au lieu de l'actuel du 2026-07-22 (une lacune de suivi de #666) ; pure hygiène de dépôt, aucune erreur de contenu dans le guide lui-même. **Correction (revue Codex sur le PR #671) :** le jeu n'est pas entièrement orphelin — `README.md` (dans les six langues) et `docs/history/EPIC-582-ABNAHME.md` référencent aussi des fichiers qu'il contient ; un correctif doit migrer toutes les références restantes ou conserver l'ancien répertoire, pas simplement le supprimer.

État en direct : **4** tickets ouverts (#669, #668, #656, #245) — les quatre relèvent de l'hygiène documentaire ou sont purement externes/opérationnels, aucun blocage de code.

### Résultat de la revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8/N9**, **O1–O8** et tout ce qui a été achevé depuis le **2026-06-25** reste fait.
- **Le release v2.7.0 est entièrement clos et vérifié :** le tag, la publication et les trois étapes du gate (matrice CI, build candidat, recette matérielle) ont tourné contre le commit réellement taggé `6f103ed` — aucune dérive entre ce qui a été validé et ce qui a été publié.
- **#669 est résolu par cette mise à jour** ; **#668** est une petite tâche de nettoyage documentaire bien délimitée (mauvaise date de jeu de captures dans une référence, analogue à la #638 déjà résolue), pas un blocage.
- **#656/#245** restent, sans changement, de purs trackers externes/opérationnels sans lien avec le code.

## Tickets GitHub ouverts — Triage (2026-07-23)

| # | Titre | Pertinence | Complexité | Modèle recommandé (effort) | Prochaine étape |
|---|-------|------------|------------|------------------------------|------------------|
| [#669](https://github.com/NikolayDA/picture_helper/issues/669) | État en direct de RECOMMENDATIONS.md obsolète (#659/#660 encore listés ouverts, #668 manquant) | 🟢 Faible (pure exactitude documentaire, aucun impact fonctionnel) | 🟢 Faible (corrigé par cette mise à jour) | – (aucun agent nécessaire) | Fait avec cette mise à jour — le ticket peut être fermé |
| [#668](https://github.com/NikolayDA/picture_helper/issues/668) | ANLEITUNG.md référence un jeu de captures obsolète (20260719 au lieu de 20260722) | 🟢 Faible (hygiène de dépôt, aucune erreur de contenu) | 🟢 Faible (consolider les références dans ANLEITUNG.md **et** README.md/EPIC-582-ABNAHME.md ; ne supprimer le jeu qu'après migration complète — selon la revue Codex, il n'est pas entièrement orphelin) | Sonnet 5 (faible) | Ready for PR – petit correctif autonome possible |
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Activer le secret ANTHROPIC_API_KEY pour la pré-évaluation vision | 🟡 Moyenne (améliore seulement la qualité des preuves ; pas un blocage selon le contrat) | 🟢 Faible (purement opérationnel, aucun code) | – (aucun agent ; propriétaire du dépôt : Settings → Secrets) | Bloquée (externe) – réalisable indépendamment |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurer le quota OpenAI pour la vérification manuelle Codex Security | 🟢 Faible (ne bloque qu'un scan manuel optionnel) | 🟢 Faible (purement opérationnel, aucun code) | – (aucun agent ; propriétaire du dépôt : facturation) | Bloquée (externe) – régler la facturation/le quota sur le projet de la plateforme OpenAI |

### Recommandé ensuite

1. Fermer **#669** — l'état en direct est à jour suite à cette mise à jour.
2. Mettre en œuvre **#668** comme un petit PR autonome : migrer toutes les références restantes vers le jeu du 2026-07-19 (`ANLEITUNG.md` + traductions, mais aussi `README.md` + traductions et `docs/history/EPIC-582-ABNAHME.md`) vers le jeu du 2026-07-22 avant de supprimer l'ancien — il n'est pas entièrement orphelin (correction après la revue Codex sur le PR #671).
3. Traiter **#656** indépendamment si de véritables verdicts vision sont souhaités — c'est une amélioration de qualité, pas un blocage.
4. Laisser **#245** comme pur tracker externe de facturation/quota ; aucune action possible ni nécessaire dans le dépôt.
5. Le release v2.7.0 est entièrement publié — aucune autre étape liée au release n'est nécessaire.

## Tours précédents

- **2026-07-23 (release v2.7.0)** — le PR #670 (incrément de version + bascule CHANGELOG + entrée icône) a été fusionné (`6f103ed`) ; le gate complet a été rejoué contre le nouveau commit de fusion (matrice CI, build candidat, recette matérielle, tout vert) ; le tag `v2.7.0` a été posé et publié (cinq artefacts). Deux nouveaux tickets d'audit enregistrés : #669 (état en direct obsolète, corrigé par cette mise à jour) et #668 (jeu de captures orphelin dans ANLEITUNG.md, hygiène mineure de dépôt). État en direct : 4 tickets ouverts, tous d'hygiène documentaire ou externes, aucun blocage de code.
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
