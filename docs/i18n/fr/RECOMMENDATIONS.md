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

### Encore Ouvert

- **O1 🟠 — Langues runtime supplémentaires.** L'allemand et l'anglais sont
  sélectionnables dans l'app. Les langues documentaires es/fr/uk/zh ne sont pas
  des locales runtime ; les ajouter clé par clé dans `bgremover.i18n` et tester.
- **O7 ✅ — Sous-processus pour rembg/ONNX fait (PR #283, issue #270 close).**
  L'inférence IA non interruptible tourne désormais dans un processus lancé via
  `spawn` (`ai_process.py`) ; `QThread.terminate()` comme sortie d'urgence IA a
  disparu. Les constats de suivi robustesse/mémoire sont corrigés et clos dans
  **#285** (PR #289).

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-18)

Au 2026-06-18, **12** issues sont ouvertes. Depuis la dernière évaluation
(2026-06-15), **#161** (URL de clonage du README) a été **close** le 2026-06-17 ;
en même temps, le cycle de release v2.4.x a apporté une vague d'issues de
durcissement des tests/release (**#299, #307–#312**) ; **#313** suit le snapshot
des recommendations lui-même. Restent ouverts les trois constats de performance
**#277/#278/#279** (benchmark hebdomadaire #280, selon le triage du propriétaire
**pas encore** confirmés comme régression de code) et **#245** (quota CI, bloqué
en externe). Toutes les issues ouvertes ont été revérifiées sur le code actuel.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#313](https://github.com/NikolayDA/picture_helper/issues/313) | Docs : mettre à jour le snapshot d'issues de RECOMMENDATIONS | 🟡 Moyenne | 🟢 Basse | Meta-issue du snapshot : l'aligner avec cette mise à jour puis la fermer ; sinon elle se compte elle-même comme 12e issue ouverte |
| [#312](https://github.com/NikolayDA/picture_helper/issues/312) | CI : passer les actions node20 à Node 24 | 🟠 Haute | 🟢 Basse | GitHub force déjà Node 24 avec un avertissement ; passer les actions concernées (`github-script`, `upload/download-artifact`) aux majors node24 de façon uniforme, test garde optionnel |
| [#311](https://github.com/NikolayDA/picture_helper/issues/311) | Release : remplir le corps de la release depuis le CHANGELOG | 🟡 Moyenne | 🟡 Moyenne | Compléter le corps de v2.4.1 à la main ; faire dériver les notes de `## [X.Y.Z]` par `release-linux.yml` au lieu d'un texte fixe — aussi lors du réemploi |
| [#310](https://github.com/NikolayDA/picture_helper/issues/310) | Test : version de LICENSES.md == pyproject | 🟡 Moyenne | 🟢 Basse | Pytest rapide comparant la version du titre à `[project].version` — détecte le drift de bump avant le lourd License Check |
| [#309](https://github.com/NikolayDA/picture_helper/issues/309) | Test : le caller couvre les permissions du WF réutilisable | 🟡 Moyenne | 🟢 Basse | Généraliser `test_release_gate.py` : le job caller doit accorder chaque permission déclarée par le workflow appelé (OIDC `id-token: write`) |
| [#308](https://github.com/NikolayDA/picture_helper/issues/308) | Test : chaîne IA importable dans l'artefact `--ai` | 🟠 Haute | 🟡 Moyenne | Autotest par spawn sans réseau dans le build `--ai` chargeant les métadonnées de `rembg`+`pymatting` (régression #306) |
| [#307](https://github.com/NikolayDA/picture_helper/issues/307) | Test : lancer l'artefact construit en headless | 🟠 Haute | 🟡 Moyenne | Lancer le bundle en headless dans le job build (attraper crash au démarrage #304 / fork bomb #305) ; `publish` reste gardé par `needs: build` |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | 🟢 Basse | 🟢 Basse | Pas de bug de correction ; le plus utile d'abord (déplacement d'endpoint, consolider `set_brush_size`), le reste au besoin |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | Régression de performance : JPEG (+38.4%) | 🟡 Moyenne | 🟡 Moyenne | Pas encore confirmé comme régression de code. Étendre le benchmark avec une empreinte d'environnement + runs de confirmation (médiane) ; regrouper avec #278/#279 |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | Régression de performance : TIFF (+21.8%) | 🟡 Moyenne | 🟡 Moyenne | Comme #277 : durcissement partagé du benchmark ; enquêter sur le chemin d'encode (`save_image_file`) seulement après un run de confirmation compatible |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | Régression de performance : WebP (+13.7%) | 🟡 Moyenne | 🟡 Moyenne | Comme #277/#278 : une PR partagée pour empreinte + confirmation par médiane ; ne signaler que les régressions confirmées |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec « Quota exceeded » | 🟡 Moyenne | 🟢 Basse | Bloqué (externe) : restaurer le quota côté compte. Dans le dépôt, seulement une gestion d'échec plus claire (skip propre) + un bump optionnel vers Node 24 |

### Issues Regroupables

- **#307/#308** vont ensemble : une PR de vérification des artefacts de release peut lancer les bundles GUI et `--ai` en headless et ajouter le self-check spawn IA.
- **#309/#310** sont de petits tests garde et peuvent partager une PR de durcissement de tests ; **#311** reste mieux séparée car elle touche le workflow de release, l'extraction du CHANGELOG et les notes existantes.
- **#277/#278/#279** doivent être traitées ensemble comme PR de fiabilisation du benchmark ; l'analyse d'encode par format ne vaut le coup qu'après.
- **#312** est une PR dédiée de modernisation CI sur tous les workflows ; la partie Node 24 de **#245** peut y passer, mais le quota OpenAI reste externe.
- **#299** est de l'hygiène de tests opportuniste et ne devrait accompagner que si un test déjà touché est concerné.

### Ordre de PR Recommandé

1. **#313** — mettre à jour ce snapshot et fermer la meta-issue pour que le comptage ne reste pas autoréférentiel.
2. **#307/#308** — smoke-test en headless des bundles de release (GUI + `--ai`) ; évite de republier des crashs au démarrage/fork bombs.
3. **#312** — passer les actions node20 à Node 24 avant que GitHub ne retire le fallback.
4. **#309/#310** — permissions génériques de workflows et version de LICENSES dans une PR rapide de durcissement de tests.
5. **#311** — dériver le corps de release depuis CHANGELOG et compléter les notes v2.4.1.
6. **#277/#278/#279** — empreinte benchmark + confirmation par médiane partagées ; ne signaler une régression que face à une baseline compatible.
7. **#245** — restaurer le quota à l'extérieur ; côté dépôt, seulement clarifier la gestion d'échec.
8. **#299** — hygiène des tests au besoin.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
