[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de Code et Recommandations Priorisées : BgRemover

## Échelle de Priorité

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bugs, plantages ou perte de données |
| 🟠 | Haute | Impact clair sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile pour la qualité, la lisibilité ou les tests |
| 🟢 | Basse | Polissage optionnel ou amélioration de processus |

## État Actuel (2026-06-04)

La liste active d'analyse de code est vide. La dernière revue de suivi est
implémentée et couverte par des tests ; ruff, mypy et la suite locale restent
la baseline avant de nouveaux PRs.

### Terminé Depuis La Dernière Revue

- **N1/N2/N4/N5/N6/N7/N8** sont terminés : chemin d'erreur de la baguette,
  limite de taille en rotation, extensions honnêtes, sauvegarde atomique,
  paquets Qt CI, import paresseux de `rembg` et docstring `load_image`.
- **O2/O3/O4/O5/O6** sont implémentés : Linux AppImage/`.deb`, workflow de
  release, matrice complète hebdomadaire, `ui_smoke` en PR/Full CI et
  raccourcis d'outils avec indications par plateforme.
- **#164/#167/#168** sont terminés (PRs #172/#174/#173) ; les constats
  restants ont depuis été clos eux aussi via #176/#178.
- **Vérifié comme proprement résolu le 2026-06-06** (PRs #188–#193, chacun avec
  test de régression, `make check` au vert – 504 passed) : **#163** (liens du
  CHANGELOG basculés vers de vrais SHAs de commit résolubles sur GitHub ; quatre
  features 2.3.0 manquantes + entrée idna/urllib3 ; vrais tags git
  volontairement non créés), **#165/#180** (TESTING.md : filtre `addopts`,
  `ui_smoke`, schedule hebdomadaire, shellcheck, `make coverage`), **#184**
  (génération de chargement + revérification `content_revision` contre les
  chargements async tardifs), **#182** (`PIP_CONSTRAINT` intégré au build
  AppImage), **#183** (license-check en lecture seule + job de commentaire
  isolé), **#177** (assertions comportementales + nouveau
  `tests/test_history_popup.py`).

### Encore Ouvert

- **O1 🟠 — Langues runtime supplémentaires.** L'allemand et l'anglais sont
  sélectionnables dans l'app. Les langues existantes de documentation
  (es/fr/uk/zh) ne sont pas encore des runtime locales ; au besoin, les ajouter
  clé par clé dans `bgremover.i18n` et les protéger par des tests de
  parité/smoke.

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-11)

Maintenant **cinq** issues ouvertes : les points de veille #203/#204, la #161
reportée, plus les constats documentaires #218 (lacunes du CHANGELOG) et #226
(revue INSTALL). **#176 est résolue** (lot qualité de
code via les PRs #198/#214, issue close) ; auparavant #166/#178/#185
(PRs #219–#221), #205/#206 (PR #222) et #199/#200/#201/#202
(PRs #215/#209/#211). Du lot `pip-audit` du 2026-06-07 (#200–#206) ne
restent ouverts que les points de veille #203/#204 ; #195 reste clos et
vérifié.

Triage du lot de sécurité face à l'état réel du projet
(`requirements/constraints.txt` + `pyproject.toml`) :

- **#200/#201 sont faites (PR #209)** — `setuptools` est désormais épinglé à
  `>=78.1.1` dans `pyproject.toml` (`[build-system]`) et `constraints.txt`, et
  `wheel` à `==0.46.2` ; des tests de régression liés aux CVE les protègent.
- **#202 (pip) est faite (PR #211)** — `pip>=26.1.2` est exigé dans les étapes
  de setup CI (`ci.yml`/`pr-ci.yml`/`ui-nightly.yml`/`benchmark.yml`/
  `license-check.yml`), le hook SessionStart web et les docs d'installation dev ;
  un test de régression lié aux CVE le protège.
- **#203 (cryptography)/#204 (pyjwt)** **ne sont pas** des dépendances du projet
  (purement transitives/système) → informatif, aucun changement de
  `constraints.txt`.
- **#205 (urllib3)/#206 (idna) sont faites (PR #222)** — le projet épingle les
  versions corrigées (`urllib3==2.7.0`, `idna==3.15`) ; des tests de régression
  liés aux CVE les gèlent et le hook SessionStart installe désormais avec les
  constraints.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | Audit README : un lien externe brisé, une référence interne | 🟡 Moyenne | 🟢 Basse | Bloqué : jargon « Runde 5 » retiré ; seule l'URL de clonage reste (décision de l'owner sur la visibilité du dépôt) |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — HIGH/MEDIUM : 6 CVEs | 🟢 Basse | 🟢 Basse | Pas une dépendance du projet (transitive/système) → informatif, aucun changement de `constraints.txt` |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — HIGH/MEDIUM : 5 CVEs | 🟢 Basse | 🟢 Basse | Pas une dépendance du projet → informatif, aucune action projet |
| [#218](https://github.com/NikolayDA/picture_helper/issues/218) | CHANGELOG : plusieurs entrées `[Unreleased]` manquent (PRs #174, #190–#215) | 🟡 Moyenne | 🟢 Basse | Ajouter les sept entrées manquantes via un PR docs dans le style existant |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | Revue INSTALL : la section artefacts de release pointe vers des releases vides + deux détails | 🟡 Moyenne | 🟢 Basse | Ajouter une note « artefacts à partir de v2.3.0 » (ou taguer v2.3.0, décision de l'owner) ; « Bookworm ou plus récent » + renvoi à `diagnose_mac.sh` via PR docs |

### Ordre de PR Recommandé

1. **#200 faite (PR #209)** — `setuptools>=78.1.1` épinglé dans `pyproject.toml` (`[build-system]`) **et** `constraints.txt` ; RCE CRITICAL fermée.
2. **#201 faite (PR #209)** — `wheel==0.46.2` épinglé dans `constraints.txt` ; regroupé avec #200 en un seul PR d'épinglage de chaîne d'approvisionnement.
3. **#202 faite (PR #211)** — `pip>=26.1.2` exigé dans les étapes de setup CI, le hook SessionStart + docs d'installation dev ; lot de CVE (path traversal/lien symbolique/détournement de module) fermé.
4. **#176 faite (PRs #198/#214)** — ignore global `E741` retiré, `check_untyped_defs` actif pour `canvas`/`main_window`/`worker_controller`, l'attente de cancel_ai est visible via un message de statut, `shutdown_all` annule les références de threads ; tests dédiés pour `app.py`/`main_window.py`. Vérifié contre `main` le 2026-06-10 (`make check` au vert).
5. **#199 faite (PR #215)** — `_redo_max` (écriture seule) supprimé de `canvas_history.py` ; test de régression `test_redo_stack_capped_by_maxlen`, `make check` au vert.
6. **#166 faite (PR #219)** — docstrings/commentaires anglais germanisés dans tout le paquet ; commentaire « pas de copie propre » précisé.
7. **#185 faite (PR #220)** — le diagnostic caviarde `$HOME`/chemins et n'affiche plus qu'un résumé filtré du log ; flag `--include-raw-logs` + test shell.
8. **#178 faite (PR #221)** — tests passés aux accesseurs publics, checks AST remplacés par des tests comportementaux, tests en double supprimés (de #168).
9. **#205/#206 faites (PR #222)** — épinglages propres gelés par tests de régression liés aux CVE, le hook SessionStart installe avec les constraints ; issues closes.
10. **#203/#204 comme points de veille** — pas des dépendances du projet ; épingler seulement si une future fonctionnalité les introduit directement.
11. **#161 reporté** — « Runde 5 » fait ; il ne reste que l'URL de clonage (décision de l'owner sur la visibilité du dépôt).
12. **#218 comme prochain PR docs** — ajouter les sept entrées `[Unreleased]` manquantes au CHANGELOG.
13. **#226 ensuite** — mettre à jour les guides INSTALL ; la note sur les artefacts de release dépend de la décision de l'owner sur le tag.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée
  lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
