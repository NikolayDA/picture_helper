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
- **#164/#167/#168** sont terminés (PRs #172/#174/#173) ; le reste se poursuit
  de façon ciblée dans #176/#178.
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

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-09)

Maintenant **onze** issues ouvertes. **#200/#201 sont résolues depuis la PR
#209** (backend de build épinglé). Le lot de sécurité `pip-audit` du 2026-06-07
(#200–#206) plus un constat de code mort (#199) restent triés ; #195 est clos et
vérifié.

Triage du lot de sécurité face à l'état réel du projet
(`requirements/constraints.txt` + `pyproject.toml`) :

- **#200/#201 sont faites (PR #209)** — `setuptools` est désormais épinglé à
  `>=78.1.1` dans `pyproject.toml` (`[build-system]`) et `constraints.txt`, et
  `wheel` à `==0.46.2` ; des tests de régression liés aux CVE les protègent.
- **#202 (pip)** reste réellement actionnable : `pip` arrive sans contrôle en
  CI/dev.
- **#203 (cryptography)/#204 (pyjwt)** **ne sont pas** des dépendances du projet
  (purement transitives/système) → informatif, aucun changement de
  `constraints.txt`.
- **#205 (urllib3)/#206 (idna)** sont déjà **épinglés proprement** dans le projet
  (`urllib3==2.7.0`, `idna==3.15`) ; constat système uniquement → clôturable.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#202](https://github.com/NikolayDA/picture_helper/issues/202) | pip 24.0 — HIGH/MEDIUM : 5 CVEs (path traversal, symlink) | 🟡 Moyenne | 🟢 Basse | Prêt pour PR ; exiger `pip>=26.1.2` dans les étapes de setup CI + docs dev |
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | Suite de la revue de code (Low) : E741, check_untyped_defs, UX de cancel_ai, shutdown_all | 🟡 Moyenne | 🟢 Basse | Prêt pour PR (de #167) ; `E741`/`check_untyped_defs` dans `pyproject.toml` encore inchangés |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | Audit README : un lien externe brisé, une référence interne | 🟡 Moyenne | 🟢 Basse | Bloqué : jargon « Runde 5 » retiré ; seule l'URL de clonage reste (décision de l'owner sur la visibilité du dépôt) |
| [#199](https://github.com/NikolayDA/picture_helper/issues/199) | Code mort (Low) : `_redo_max` en écriture seule dans `canvas_history.py` | 🟢 Basse | 🟢 Basse | Prêt pour PR ; supprimer une ligne (module strictement typé — `make check`) |
| [#185](https://github.com/NikolayDA/picture_helper/issues/185) | Sécurité : le diagnostic macOS divulgue des chemins locaux + queue de log brute (vie privée) | 🟢 Basse | 🟡 Moyenne | Prêt pour PR ; masquer `$HOME`/chemins + flag `--include-raw-logs` + test shell |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | Suite de l'audit de tests (Low) : découpler des internals privés + dédupliquer | 🟢 Basse | 🟡 Moyenne | Prêt pour PR (de #168) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Audit des commentaires : incohérences de langue et imprécision mineure | 🟢 Basse | 🟢 Basse | Prêt pour PR ; docstrings en anglais dans `right_panel.py`/`main_window.py` |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — HIGH/MEDIUM : 6 CVEs | 🟢 Basse | 🟢 Basse | Pas une dépendance du projet (transitive/système) → informatif, aucun changement de `constraints.txt` |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — HIGH/MEDIUM : 5 CVEs | 🟢 Basse | 🟢 Basse | Pas une dépendance du projet → informatif, aucune action projet |
| [#205](https://github.com/NikolayDA/picture_helper/issues/205) | urllib3 2.6.3 — MEDIUM : 2 CVEs | 🟢 Basse | 🟢 Basse | Aucune action ; le projet épingle déjà `urllib3==2.7.0` (propre) → clôturable |
| [#206](https://github.com/NikolayDA/picture_helper/issues/206) | idna 3.11 — MEDIUM : DoS via `idna.encode()` | 🟢 Basse | 🟢 Basse | Aucune action ; le projet épingle déjà `idna==3.15` (propre) → clôturable |

### Ordre de PR Recommandé

1. **#200 faite (PR #209)** — `setuptools>=78.1.1` épinglé dans `pyproject.toml` (`[build-system]`) **et** `constraints.txt` ; RCE CRITICAL fermée.
2. **#201 faite (PR #209)** — `wheel==0.46.2` épinglé dans `constraints.txt` ; regroupé avec #200 en un seul PR d'épinglage de chaîne d'approvisionnement.
3. **#202** — exiger `pip>=26.1.2` dans les étapes de setup CI + docs d'installation dev.
4. **#176** — Lot qualité de code de #167 : restreindre `E741`, `check_untyped_defs` progressivement, UX de cancel_ai, annuler les références de threads dans `shutdown_all`.
5. **#199** — supprimer `_redo_max` (écriture seule) de `canvas_history.py` (correctif trivial, régression couverte par `make check`).
6. **#166** — Nettoyage de langue dans les docstrings en tant que petit PR de maintenance.
7. **#185** — Masquer le diagnostic macOS (`$HOME`/chemins) + flag `--include-raw-logs` + test shell.
8. **#178** — Découpler les tests des internals privés + réduire les tests en double (de #168).
9. **#205/#206 clôturables** — épinglage du projet déjà correct (`urllib3==2.7.0`, `idna==3.15`) ; constats système uniquement.
10. **#203/#204 comme points de veille** — pas des dépendances du projet ; épingler seulement si une future fonctionnalité les introduit directement.
11. **#161 reporté** — « Runde 5 » fait ; il ne reste que l'URL de clonage (décision de l'owner sur la visibilité du dépôt).

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée
  lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
