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

La liste active d'analyse de code est vide. Ruff, mypy et la suite locale
restent la baseline avant de nouveaux PRs.

### Terminé Depuis La Dernière Revue

- **N1/N2/N4/N5/N6/N7/N8** sont terminés : chemins d'erreur, limite de taille,
  extensions, sauvegarde atomique, paquets Qt CI, import paresseux et docstring.
- **O2/O3/O4/O5/O6** sont implémentés : paquets Linux, workflow de release,
  matrice complète, `ui_smoke` et raccourcis adaptés aux plateformes.
- Les constats **#163–#206** ont été clos dans les PRs documentés et protégés
  par des tests de régression ou des contrôles CI.
- Les PRs **#263–#269** ont clos **#257, #258, #234 + #259, #248 + #260, #231**
  et **#249** ; **#261** a été résolu via la PR #268 et clos.
- La PR **#274** a clos **#232** : `import bgremover` ne charge plus le stack Qt
  grâce aux exports paresseux PEP 562 ; un test de régression en sous-processus le couvre.
- La vague de PR **#280–#284** a intégré le benchmark hebdomadaire, implémenté
  trois constats — **#235** (budget undo/redo partagé, PR #281), **#275**
  (message mégapixels localisé, PR #282) et **#270** (sous-processus rembg/ONNX
  via `ai_process.py`, PR #283) — et rafraîchi la feuille de route (PR #284).
  **#235, #270 et #275 sont désormais clos.**
- Les deux constats Codex de suivi post-merge issus de #283 et #264 sont eux
  aussi corrigés **et clos** : **#285** (robustesse/mémoire du sous-processus
  rembg, PR #289) et **#286** (pics de mémoire dans la lecture de fichier
  plafonnée, PR #290).

- **N9 ✅ — Modèle de données projet/calques (epic #329) livré.** Modèle de
  domaine sans Qt (#330), historique conscient des calques (#331), canevas de
  composite (#332), format `.bgrproj` (#333), panneau de calques/menu projet
  (#334) et migration/intégration (#335) — parité image unique préservée,
  `make check`/`make ui` au vert.

### Encore Ouvert

- **O1 🟠 — Langues runtime supplémentaires.** L'allemand et l'anglais sont
  sélectionnables dans l'app. Les langues documentaires es/fr/uk/zh ne sont pas
  des locales runtime ; les ajouter clé par clé dans `bgremover.i18n` et tester.
- **O7 ✅ — Sous-processus pour rembg/ONNX fait (PR #283, issue #270 close).**
  L'inférence IA non interruptible tourne désormais dans un processus lancé via
  `spawn` (`ai_process.py`) ; `QThread.terminate()` comme sortie d'urgence IA a
  disparu. Les constats de suivi robustesse/mémoire sont corrigés et clos dans
  **#285** (PR #289).

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-21)

As of 2026-06-21, only **4** roadmap/follow-up issues remain open after
reviewing yesterday's and today's PRs. Merge commits **#337**, **#338**, and
**#340** cleanly complete the items that were still open yesterday: **#326**,
**#329–#335**, **#323**, and **#324**. The GIF load path is regression-tested,
the project/layer epic is implemented end-to-end from the domain model through
UI/integration, and the security-scan tests cover severity filtering, empty
findings, and prompt scope. The remaining open items are **#322**
(maintenance/skip path for the scheduled Codex Security Scan), **#318**
(permission-guard semantics), **#245** (externally blocked quota), and **#299**
(test hygiene).

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI: add a maintenance/skip path for the scheduled Codex Security Scan | 🟡 Medium | 🟡 Medium | **Next repo-side step for #245** — choose manual switch, visible auto graceful-skip, or both; gate in the `cadence` job, "disabled → skipped, not failed", keep least privilege and add a static test |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟡 Medium | 🟡 Medium | **Needs refinement** — first document GitHub's startup-validation semantics (top-level vs. effective-per-job); no observed repo failure right now, and OIDC guard #303 must not be weakened |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | **Externally blocked** — restore quota account-side; #323/#324 are complete repo-side, #322 remains open as maintenance/skip hardening |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | No correctness bug; improve opportunistically when related tests are touched (highest value: endpoint move, consolidate `set_brush_size`) |

### Issues groupables

- **#322** can be implemented as a standalone CI-hardening PR and complements
  the already completed #323/#324.
- **#318** stays separate because GitHub's semantics must be documented before
  changing code.
- **#299** should only ride along when an affected test is already being edited.

### Ordre de PR recommandé

1. **#322** — final repo-side #245 follow-up with direct operational value.
2. **#318** — refine the permission guard once semantics are documented, without
   weakening the OIDC regression case.
3. **#245** — restore quota account-side (externally blocked).
4. **#299** — test hygiene as needed.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
