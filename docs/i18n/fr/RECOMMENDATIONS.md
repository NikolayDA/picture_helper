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

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-19)

Au 2026-06-19, **7** issues sont ouvertes. Depuis l'évaluation du 2026-06-18, la
vague de durcissement des tests/release a été en grande partie intégrée :
**#307, #308, #309, #310** et **#312** sont désormais **closes** (tout comme la
meta-issue du snapshot **#313**). La PR **#317** (qui a clos #309/#310) a fait
naître un nouveau suivi **#318** issu de sa revue Codex (surcharges de
permissions au niveau job dans le garde du workflow réutilisable). Restent
ouverts **#311** (corps de release), les trois constats de performance
**#277/#278/#279** (benchmark hebdomadaire #280, selon le triage du propriétaire
**pas encore** confirmés comme régression de code), **#245** (quota CI, bloqué en
externe) et l'élément d'hygiène de tests de basse priorité **#299**. Toutes les
issues ouvertes ont été revérifiées sur le code actuel.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#311](https://github.com/NikolayDA/picture_helper/issues/311) | Release : remplir le corps de la release depuis le CHANGELOG | 🟡 Moyenne | 🟡 Moyenne | **Prêt pour PR** — bien cadré : compléter le corps de v2.4.1 à la main ; faire dériver les notes de `## [X.Y.Z]` par `release-linux.yml` au lieu d'un texte fixe (aussi lors du réemploi), avec un test de régression dans `test_release_gate.py` |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test : respecter les surcharges de permissions au niveau job dans le WF réutilisable | 🟡 Moyenne | 🟡 Moyenne | **À affiner** — confirmer d'abord la sémantique de validation au démarrage de GitHub (niveau top vs. effectif par job) ; actuellement un faux positif purement théorique (aucune surcharge au niveau job dans `ci.yml`), et le garde OIDC #303 ne doit pas s'affaiblir |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | Régression de performance : JPEG (+38.4%) | 🟡 Moyenne | 🟡 Moyenne | Pas encore confirmé comme régression de code. Étendre le benchmark avec une empreinte d'environnement + runs de confirmation (médiane) ; regrouper avec #278/#279 |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | Régression de performance : TIFF (+21.8%) | 🟡 Moyenne | 🟡 Moyenne | Comme #277 : durcissement partagé du benchmark ; enquêter sur le chemin d'encode (`save_image_file`) seulement après un run de confirmation compatible |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | Régression de performance : WebP (+13.7%) | 🟡 Moyenne | 🟡 Moyenne | Comme #277/#278 : une PR partagée pour empreinte + confirmation par médiane ; ne signaler que les régressions confirmées |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec « Quota exceeded » | 🟡 Moyenne | 🟢 Basse | **Bloqué (externe) :** restaurer le quota côté compte. Le périmètre du dépôt n'est qu'une gestion d'échec plus claire (skip propre) |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | 🟢 Basse | 🟢 Basse | Pas de bug de correction ; le plus utile d'abord (déplacement d'endpoint, consolider `set_brush_size`), le reste au besoin |

### Issues Regroupables

- **#277/#278/#279** doivent être traitées ensemble comme PR de fiabilisation du benchmark ; l'analyse d'encode par format ne vaut le coup qu'après.
- **#318** est le suivi du garde de permissions déjà intégré (#309/#310) et reste séparée — elle nécessite d'abord une sémantique GitHub documentée avant de toucher à `_required_permissions`.
- **#311** reste autonome car elle touche le workflow de release, l'extraction du CHANGELOG et les notes de release existantes.
- **#299** est de l'hygiène de tests opportuniste et ne devrait accompagner que si un test déjà touché est concerné.

### Ordre de PR Recommandé

1. **#311** — dériver le corps des releases depuis le CHANGELOG et compléter les notes v2.4.1 ; bien cadré et visible par l'utilisateur (les correctifs livrés sont sinon invisibles sur la page de release).
2. **#277/#278/#279** — empreinte benchmark + confirmation par médiane partagées ; ne signaler une régression que face à une baseline compatible.
3. **#318** — affiner le garde de permissions une fois la sémantique de GitHub documentée, sans affaiblir le cas de régression OIDC.
4. **#245** — restaurer le quota à l'extérieur ; le travail côté dépôt n'est ensuite qu'une gestion d'échec plus claire.
5. **#299** — hygiène des tests au besoin.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
