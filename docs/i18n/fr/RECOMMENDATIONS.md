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
- **Lot de sécurité du 2026-06-07 terminé** (#200/#201/#202/#205/#206 via les
  PRs #209/#211/#222) : setuptools/wheel/pip/urllib3/idna épinglés ou exigés,
  chacun protégé par un test de régression lié aux CVE.

### Encore Ouvert

- **O1 🟠 — Langues runtime supplémentaires.** L'allemand et l'anglais sont
  sélectionnables dans l'app. Les langues existantes de documentation
  (es/fr/uk/zh) ne sont pas encore des runtime locales ; au besoin, les ajouter
  clé par clé dans `bgremover.i18n` et les protéger par des tests de
  parité/smoke.

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-12)

Maintenant **14** issues ouvertes : les points de veille #203/#204, la #161
reportée, les constats docs/audit #218/#226/#227/#236, plus le lot qualité de
code #229–#235 issu de l'audit du 2026-06-11. #203/#204 ne sont pas des
dépendances du projet (purement transitives/système) → informatif, aucun
changement de `constraints.txt`.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | Audit README : l'URL de clonage ne mène nulle part | 🟡 Moyenne | 🟢 Basse | Bloqué (décision de l'owner sur la visibilité du dépôt) |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — 6 CVEs | 🟢 Basse | 🟢 Basse | Point de veille, aucune action projet |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — 5 CVEs | 🟢 Basse | 🟢 Basse | Point de veille, aucune action projet |
| [#218](https://github.com/NikolayDA/picture_helper/issues/218) | CHANGELOG : entrées `[Unreleased]` manquantes | 🟡 Moyenne | 🟢 Basse | Prêt pour PR (ajouter les sept entrées dans le style existant) |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | Revue INSTALL : pointe vers des releases vides + deux détails | 🟡 Moyenne | 🟢 Basse | Prêt pour PR (fixes docs) ; la note sur les artefacts dépend de la décision de tag |
| [#227](https://github.com/NikolayDA/picture_helper/issues/227) | Audit RECOMMENDATIONS : aperçu des issues obsolète | 🟡 Moyenne | 🟢 Basse | Résolu par cette mise à jour → fermer l'issue |
| [#229](https://github.com/NikolayDA/picture_helper/issues/229) | Le warmup rembg ne crée pas de session d'inférence réutilisable | 🟠 Haute | 🟡 Moyenne | Prêt pour PR (mettre en cache une session via `new_session`) |
| [#230](https://github.com/NikolayDA/picture_helper/issues/230) | Le fichier est lu entièrement en mémoire avant le contrôle de taille | 🟠 Haute | 🟢 Basse | Prêt pour PR (limite d'octets avant le `read()`) |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` peut interrompre les workers de façon non sûre | 🟡 Moyenne | 🟠 Haute | À affiner (choisir l'option A/B/C ; à court terme l'option C) |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` charge toute la GUI PyQt6 | 🟡 Moyenne | 🟡 Moyenne | Prêt pour PR (exports paresseux via PEP 562) |
| [#233](https://github.com/NikolayDA/picture_helper/issues/233) | Des settings recent_files corrompus cassent le menu | 🟡 Moyenne | 🟢 Basse | Prêt pour PR (`paths()` défensif + tests paramétrés) |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Une migration manquante incrémente quand même `schema_version` | 🟢 Basse | 🟢 Basse | Prêt pour PR (avant la première vraie migration) |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | La limite d'undo ignore redo/image d'origine | 🟢 Basse | 🟡 Moyenne | À affiner (décider docs seules vs. budget partagé) |
| [#236](https://github.com/NikolayDA/picture_helper/issues/236) | Commentaire de session-start.sh : `benchmark.yml` manque | 🟢 Basse | 🟢 Basse | Prêt pour PR (fix de commentaire d'une ligne) |

### Ordre de PR Recommandé

1. **#230** — pertinence maximale pour une faible complexité : limite de taille de fichier avant la lecture, couvre les chemins sync et async de façon centrale.
2. **#229** — réutiliser la session du warmup ; le plus gros gain pour le pipeline IA, et le commentaire erroné est corrigé au passage.
3. **#233** — `paths()` défensif avec tests paramétrés ; cohérent avec l'objectif de robustesse du schéma de settings.
4. **#236 + #218** — petits fixes commentaire/docs, idéalement regroupés ; **#227** est résolu par cette mise à jour et peut être fermé.
5. **#232** — exports paresseux via PEP 562 ; ampleur moyenne à cause de la migration des tests/imports.
6. **#234** — petit fix ; à planifier au plus tard avant la première vraie migration du schéma.
7. **#226** — fixes docs maintenant ; la note sur les artefacts de release dépend de la décision de tag de l'owner.
8. **#235** — décider d'abord la sémantique (docs seules vs. budget partagé), puis implémenter.
9. **#231** — à court terme l'option C (attentes bornées + logging), évaluer à long terme l'option B (sous-processus).
10. **#203/#204** restent des points de veille ; **#161** reste bloqué (décision de l'owner).

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée
  lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
