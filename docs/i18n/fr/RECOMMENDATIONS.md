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
- La vague de PR **#280–#283** a intégré le benchmark hebdomadaire et implémenté
  trois constats : **#235** (budget undo/redo partagé, PR #281, clos), **#275**
  (message mégapixels localisé, PR #282) et **#270** (sous-processus rembg/ONNX
  via `ai_process.py`, PR #283). #275 et #270 sont faits dans le code et il ne
  reste qu'à clore leurs issues.

### Encore Ouvert

- **O1 🟠 — Langues runtime supplémentaires.** L'allemand et l'anglais sont
  sélectionnables dans l'app. Les langues documentaires es/fr/uk/zh ne sont pas
  des locales runtime ; les ajouter clé par clé dans `bgremover.i18n` et tester.
- **O7 ✅ — Sous-processus pour rembg/ONNX fait (PR #283, issue #270).**
  L'inférence IA non interruptible tourne désormais dans un processus lancé via
  `spawn` (`ai_process.py`) ; `QThread.terminate()` comme sortie d'urgence IA a
  disparu. Il ne reste qu'à clore l'issue #270.

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-15)

Après la vague de PR **#280–#283**, **7** issues restent ouvertes. **#235** a été
close via la PR #281. **#270** (PR #283) et **#275** (PR #282) sont déjà
implémentées dans le code et il ne reste qu'à clore leurs issues. Nouveaux : trois
constats de performance — **#277/#278/#279** — issus du run de benchmark
hebdomadaire (#280) ; selon le triage du propriétaire ils ne sont **pas encore**
confirmés comme régression de code, car la baseline du 2026-06-08 ne porte pas
d'empreinte d'environnement. Toutes les issues ouvertes ont été revérifiées sur
le code actuel.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#270](https://github.com/NikolayDA/picture_helper/issues/270) | Déplacer l'inférence rembg/ONNX dans un sous-processus (suite de #231) | 🟠 Haute | 🟡 Moyenne | **Fait dans le code (PR #283, `ai_process.py`).** Vérifier et clore l'issue ; feuille de route O7 terminée |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | Régression de performance : JPEG (+38.4%) | 🟡 Moyenne | 🟡 Moyenne | Affinage : pas encore confirmé comme régression de code. Étendre le benchmark avec une empreinte d'environnement + runs de confirmation (médiane), puis comparer seulement à une baseline compatible. Regrouper avec #278/#279 |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | Régression de performance : TIFF (+21.8%) | 🟡 Moyenne | 🟡 Moyenne | Comme #277 : durcissement partagé du benchmark ; enquêter sur le chemin d'encode (`save_image_file`) seulement après un run de confirmation compatible |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | Régression de performance : WebP (+13.7%) | 🟡 Moyenne | 🟡 Moyenne | Comme #277/#278 : une PR partagée pour empreinte + confirmation par médiane ; ne signaler que les régressions confirmées |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec « Quota exceeded » | 🟡 Moyenne | 🟢 Basse | Bloqué (externe) : restaurer le quota côté compte. Dans le dépôt, seulement une gestion d'échec plus claire (skip propre) + un bump optionnel vers Node 24, sans changement forcé `setup-node` |
| [#275](https://github.com/NikolayDA/picture_helper/issues/275) | Le message mégapixels « image trop grande » n'est pas localisé | 🟢 Basse | 🟢 Basse | **Fait dans le code (PR #282).** `_too_large_message` passe désormais par `tr("status.image_too_large[_mp]", …)` (de/en) ; vérifier et clore l'issue |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README : l'URL de clonage renvoie 404 aux utilisateurs anonymes | 🟢 Basse | 🟢 Basse | Décision nécessaire : public vs. privé/sur invitation, puis mettre à jour le guide de clonage ou clore (« Runde 5 » est déjà corrigé) |

### Ordre de PR Recommandé

1. **#270 + #275** — les deux sont faits dans le code (PR #283 / #282) : vérifier et clore les issues.
2. **#277/#278/#279** — une PR partagée : étendre le benchmark avec une empreinte d'environnement et des runs de confirmation (médiane) ; ne signaler une régression que face à une baseline compatible. Bien délimité, prêt pour PR.
3. **#245** — restaurer le quota à l'extérieur ; durcissement optionnel du workflow (skip propre + Node 24) en petite PR séparée.
4. **#161** — décider le modèle de publication, puis modifier la doc ou clore.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
