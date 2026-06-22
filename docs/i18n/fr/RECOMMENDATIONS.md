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

## Issues GitHub Ouvertes — État du Triage (2026-06-22)

Au 2026-06-22, GitHub affiche **9** issues ouvertes. Nouveauté : l'**épic
d'export EufyMake #351** avec les sous-issues **#352–#355** (rang #3 de la
roadmap). Le chemin maintenance/skip précédemment listé, **#322**, a été livré
via **#342** et est désormais **clos** ; les issues projet/couches et tests
sécurité **#323/#324/#326** et **#329–#335** restent terminées dans
**#337/#338/#340**.

Évaluation : **Pertinence** = importance pour la roadmap/les utilisateurs,
**Complexité** = effort d'implémentation estimé.

| # | Titre | Pertinence | Complexité | Prochaine étape recommandée |
|---|-------|------------|------------|-----------------------------|
| [#351](https://github.com/NikolayDA/picture_helper/issues/351) | [Épic] Paquet d'export EufyMake cohérent | 🟠 Haute | 🔴 Haute (épic) | **Needs refinement** – selon la deep research (commentaire de l'issue), recentrer le scope sur « assets d'import robustes pour EufyMake Studio » ; la génération native de `.empf` **n'est pas** l'objectif par défaut. Traité via #352–#355. |
| [#352](https://github.com/NikolayDA/picture_helper/issues/352) | Modèle de données d'export et définition du paquet (sans Qt) + ADR | 🟠 Haute | 🟡 Moyenne | **Ready for PR** – tâche de recherche faite, la décision ADR est dans les commentaires. `eufymake_export.py` sans Qt avec `ExportPlan`/`ExportAsset` (motif couleur PNG+alpha, hauteur en gris clair=haut, masque gloss) ; marquer 16 bits/sémantique gloss/`.empf` natif comme « ouvert ». Fondation — débloque #353–#355. |
| [#353](https://github.com/NikolayDA/picture_helper/issues/353) | Rendu des assets et écriture atomique du paquet | 🟠 Haute | 🟡 Moyenne | **Blocked** – nécessite #352 ; bien cadré ensuite (rendu + écriture atomique). |
| [#354](https://github.com/NikolayDA/picture_helper/issues/354) | Contrôle de cohérence avant export | 🟠 Haute | 🟡 Moyenne | **Blocked** – nécessite #352. Garder les briques de contrôle réutilisables (synergie avec le contrôle d'erreurs général avant export). |
| [#355](https://github.com/NikolayDA/picture_helper/issues/355) | UI : dialogue d'export EufyMake + menu + i18n + réglages | 🟠 Haute | 🟡 Moyenne | **Blocked** – nécessite #352–#354. Libellé UI selon la deep research : « préparer des assets pour EufyMake Studio », pas « produire un projet fini ». |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec "Quota exceeded" | 🟡 Moyenne | 🟢 Basse | **Blocked (externe)** – le durcissement côté repo via #322/#342 (clos) est fait ; le blocage restant est la quota OpenAI/billing. Après restauration, lancer une fois le scan programmé manuellement puis clore. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test : respecter les overrides de permissions job-level dans le reusable WF | 🟢 Basse | 🟡 Moyenne | **Needs refinement** – d'abord documenter la sémantique GitHub (top-level vs. effectif-par-job) ; ne pas affaiblir le guard OIDC #303. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF n'est pas supporté comme format d'entrée | 🟢 Basse | 🟢 Basse | **Ready for PR (docs)** – le mainteneur a **exclu HEIC délibérément** (commentaire 2026-06-21). Clarifier seulement README/ANLEITUNG, puis clore. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | 🟢 Basse | 🟢 Basse | **Ready for PR (opportuniste)** – pas un bloqueur produit ou CI ; le plus utile d'abord (asserter l'extrémité du lasso, la ligne de `test_helpers`, consolider les tests `set_brush_size`). |

### Prochaines étapes recommandées (ordre des PR)

1. **#352** d'abord — fondation de l'épic, bien cadré après le refinement de
   l'ADR ; débloque #353/#354.
2. **#353** et **#354** en parallèle une fois #352 mergée.
3. **#355** pour clore l'épic.
4. **#339** (petite PR docs) et **#299** (cleanup de tests) comme bouche-trous
   basse priorité entre-temps.
5. Reporter **#318** jusqu'à ce que la sémantique des permissions GitHub soit
   documentée.
6. Garder **#245** bloqué externe (aucun patch repo ne restaure la quota).

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
