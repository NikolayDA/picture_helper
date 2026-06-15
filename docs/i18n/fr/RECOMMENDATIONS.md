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
  **#235, #270 et #275 sont désormais clos.** La revue Codex post-merge de #283
  et #264 a produit deux issues de suivi : **#285** et **#286**.

### Encore Ouvert

- **O1 🟠 — Langues runtime supplémentaires.** L'allemand et l'anglais sont
  sélectionnables dans l'app. Les langues documentaires es/fr/uk/zh ne sont pas
  des locales runtime ; les ajouter clé par clé dans `bgremover.i18n` et tester.
- **O7 ✅ — Sous-processus pour rembg/ONNX fait (PR #283, issue #270 close).**
  L'inférence IA non interruptible tourne désormais dans un processus lancé via
  `spawn` (`ai_process.py`) ; `QThread.terminate()` comme sortie d'urgence IA a
  disparu. Les constats de suivi robustesse/mémoire sont suivis dans **#285**.

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-15)

Après la vague de PR **#280–#284**, **7** issues restent ouvertes. **#235**
(PR #281), **#270** (PR #283) et **#275** (PR #282) sont implémentées **et
closes**. La revue Codex post-merge de deux PR a produit deux issues de suivi :
**#285** (robustesse/mémoire du sous-processus rembg, suite de #283) et **#286**
(pics de mémoire dans la lecture de fichier plafonnée, suite de #264). S'y
ajoutent trois constats de performance — **#277/#278/#279** — issus du run de
benchmark hebdomadaire (#280) ; selon le triage du propriétaire **pas encore**
confirmés comme régression de code, car la baseline du 2026-06-08 ne porte pas
d'empreinte d'environnement. Toutes les issues ouvertes ont été revérifiées sur
le code actuel.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#285](https://github.com/NikolayDA/picture_helper/issues/285) | Robustesse et mémoire du sous-processus rembg (`ai_process.py`, suite de #283) | 🟠 Haute | 🟡 Moyenne | Quatre constats Codex post-merge : ré-init de session après un échec transitoire, libération du payload au repos, surcoût de pickle des PNG par la pipe (risque d'OOM avec de grandes images), course au stop pendant le démarrage du processus. Regrouper et couvrir par des tests |
| [#286](https://github.com/NikolayDA/picture_helper/issues/286) | Pics de mémoire dans la lecture de fichier plafonnée (`image_loading._read_capped`, suite de #264) | 🟡 Moyenne | 🟢 Basse | Deux constats Codex : `b"".join(chunks)` double le tampon (~1 Gio, P1), la première lecture ignore la taille de `fstat()` (8 Mio, P2). `bytearray.extend` + première lecture bornée par la taille |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | Régression de performance : JPEG (+38.4%) | 🟡 Moyenne | 🟡 Moyenne | Affinage : pas encore confirmé comme régression de code. Étendre le benchmark avec une empreinte d'environnement + runs de confirmation (médiane), puis comparer seulement à une baseline compatible. Regrouper avec #278/#279 |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | Régression de performance : TIFF (+21.8%) | 🟡 Moyenne | 🟡 Moyenne | Comme #277 : durcissement partagé du benchmark ; enquêter sur le chemin d'encode (`save_image_file`) seulement après un run de confirmation compatible |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | Régression de performance : WebP (+13.7%) | 🟡 Moyenne | 🟡 Moyenne | Comme #277/#278 : une PR partagée pour empreinte + confirmation par médiane ; ne signaler que les régressions confirmées |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec « Quota exceeded » | 🟡 Moyenne | 🟢 Basse | Bloqué (externe) : restaurer le quota côté compte. Dans le dépôt, seulement une gestion d'échec plus claire (skip propre) + un bump optionnel vers Node 24, sans changement forcé `setup-node` |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README : l'URL de clonage renvoie 404 aux utilisateurs anonymes | 🟢 Basse | 🟢 Basse | Décision nécessaire : public vs. privé/sur invitation, puis mettre à jour le guide de clonage ou clore (« Runde 5 » est déjà corrigé) |

### Ordre de PR Recommandé

1. **#285** — regrouper les quatre constats Codex de suivi sur le sous-processus rembg (risque mémoire/OOM avec de grandes images d'abord), avec des tests de régression.
2. **#286** — désamorcer la lecture de fichier plafonnée (`bytearray` au lieu de `b"".join`, première lecture bornée par la taille). Petit et bien délimité.
3. **#277/#278/#279** — une PR partagée : étendre le benchmark avec une empreinte d'environnement et des runs de confirmation (médiane) ; ne signaler une régression que face à une baseline compatible.
4. **#245** — restaurer le quota à l'extérieur ; durcissement optionnel du workflow (skip propre + Node 24) en petite PR séparée.
5. **#161** — décider le modèle de publication, puis modifier la doc ou clore.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
