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

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-07)

Maintenant **six** issues ouvertes : un bloqueur 🟠 CI (#195) et cinq 🟡/🟢 :
deux `documentation` (#161, #166), deux `quality/testing` (#176, #178) et un
constat de sécurité/vie privée (#185). #163/#165/#177/#180 ainsi que les trois
constats de sécurité les plus prioritaires du scan Codex `8c04b92`
(#182/#183/#184) sont clos et vérifiés depuis la dernière revue.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#195](https://github.com/NikolayDA/picture_helper/issues/195) | Bloqueur Full-CI (mypy/3.10) : shape-typing dans `canvas_selection.py` – stubs numpy-2.2.6 | 🟠 Haute | 🟢 Basse | Prêt pour PR ; `self._mask: npt.NDArray[np.bool_]` — correctif d'une ligne vérifié |
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | Suite de la revue de code (Low) : E741, check_untyped_defs, UX de cancel_ai, shutdown_all | 🟡 Moyenne | 🟢 Basse | Prêt pour PR (de #167) ; `E741`/`check_untyped_defs` dans `pyproject.toml` encore inchangés |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | Audit README : un lien externe brisé, une référence interne | 🟡 Moyenne | 🟢 Basse | Partiellement fait : jargon « Runde 5 » retiré ; seule l'URL de clonage reste (décision de l'owner) |
| [#185](https://github.com/NikolayDA/picture_helper/issues/185) | Sécurité : le diagnostic macOS divulgue des chemins locaux + queue de log brute (vie privée) | 🟢 Basse | 🟡 Moyenne | Prêt pour PR ; masquer `$HOME`/chemins + flag `--include-raw-logs` + test shell |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | Suite de l'audit de tests (Low) : découpler des internals privés + dédupliquer | 🟢 Basse | 🟡 Moyenne | Prêt pour PR (de #168) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Audit des commentaires : incohérences de langue et imprécision mineure | 🟢 Basse | 🟢 Basse | Prêt pour PR ; docstrings en anglais dans `right_panel.py`/`main_window.py` |

### Ordre de PR Recommandé

1. **#195** — `self._mask: npt.NDArray[np.bool_]` dans `canvas_selection.py` ; cellules Full-CI Python-3.10 à nouveau vertes.
2. **#176** — Lot qualité de code de #167 : restreindre `E741`, `check_untyped_defs` progressivement, UX de cancel_ai, annuler les références de threads dans `shutdown_all`.
3. **#185** — Masquer le diagnostic macOS (`$HOME`/chemins) + flag `--include-raw-logs` + test shell.
4. **#178** — Découpler les tests des internals privés + réduire les tests en double (de #168).
5. **#166** — Nettoyage de langue dans les docstrings en tant que petit PR de maintenance.
6. **#161 reporté** — « Runde 5 » fait ; il ne reste que l'URL de clonage (décision de l'owner sur la visibilité du dépôt).

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée
  lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
