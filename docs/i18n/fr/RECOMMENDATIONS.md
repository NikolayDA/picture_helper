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
- Les anciens constats clos (**#163–#290**, dont l'epic EufyMake **#351**/**#352–#355**
  et le sous-processus rembg/ONNX **#270**/**#285**/**#286**) sont terminés dans les
  PRs documentés, couverts par des tests/CI et archivés.

- **N9 ✅ — Modèle de données projet/calques (epic #329) livré.** Modèle de
  domaine sans Qt (#330), historique conscient des calques (#331), canevas de
  composite (#332), format `.bgrproj` (#333), panneau de calques/menu projet
  (#334) et migration/intégration (#335) — parité image unique préservée,
  `make check`/`make ui` au vert.
- **N10 ✅ — Espace de travail Height Map (epic #344) livré.** Représentation de
  hauteur et vue 2D sans Qt (#345), génération/import (#346), édition (#347),
  optimisation `height_ops` avec aperçu (#348) et onglet Hauteur contextuel (#349).
- **N11 ✅ — Polissage phase 0 (epic #358) livré.** Redimensionnement du projet
  (#359), luminosité/contraste/saturation préservant l'alpha (#360) et feather
  du bord alpha limité à la sélection (#361), annulables et persistés en `.bgrproj`.
- **#363 ✅ — Régression d'export corrigée (PR #367).** Enregistrer l'image écrit
  de nouveau le composite COLOR quel que soit le calque actif ; les rendus
  d'affichage et d'export sont séparés, couverts par un test de régression au pixel.

### Encore Ouvert

- **O1 🟠 — Langues runtime supplémentaires.** L'allemand et l'anglais sont
  sélectionnables dans l'app. Les langues documentaires es/fr/uk/zh ne sont pas
  des locales runtime ; les ajouter clé par clé dans `bgremover.i18n` et tester.
- **O7 ✅ — Sous-processus pour rembg/ONNX fait (PR #283, issue #270 close).**
  L'inférence IA non interruptible tourne désormais dans un processus lancé via
  `spawn` (`ai_process.py`) ; `QThread.terminate()` comme sortie d'urgence IA a
  disparu. Les constats de suivi robustesse/mémoire sont corrigés et clos dans
  **#285** (PR #289).

## Issues GitHub Ouvertes — État du Triage (2026-06-24, mis à jour)

Au 2026-06-24, GitHub affiche **14** issues ouvertes. L'epic **#375** (sortie
physique mm/DPI + validation générale d'export) est terminé via **#376–#380**
(PR #382/#383) et clos. Depuis le dernier triage, **deux nouveaux epics** ont
été ajoutés qui structurent la clôture des phases 0/1 :

- **#384 – Aperçu 2D combiné** (MVP du cœur relief, le dernier point fonctionnel
  ouvert de la phase 1, actuellement ~55 %) avec les sous-issues **#385** (rendu
  de relief-shading, sans Qt), **#386** (visualisation du gloss, sans Qt),
  **#387** (modes d'aperçu du canevas + pipeline de composite) et **#388**
  (bascules UI + i18n).
- **#389 – Mettre à jour la doc utilisateur & publier la release v2.5.0** avec
  les sous-issues **#390** (le guide utilisateur ANLEITUNG, 6 langues — clôt
  aussi **#357**), **#391** (README + captures d'écran + i18n) et **#392**
  (release v2.5.0).

Les lacunes documentaires **#357** (désormais couverte par #390) et **#339**
plus les constats test/CI **#318**, **#299** et **#245** restent également.

**Revue des commentaires (2026-06-24) :** Les commentaires sur **#245**, **#299** et **#339**
proviennent tous du mainteneur (triage) et confirment l'état documenté : #245 reste bloqué en
externe sur quota/billing, #299 reste de l'hygiène de tests à basse priorité, et #339 est
confirmée comme une exclusion HEIC délibérée. Aucun commentaire ne nécessite de mise à jour
substantielle des issues ; aucune nouvelle issue de suivi n'est requise.

Évaluation : **Pertinence** = importance pour la roadmap/les utilisateurs,
**Complexité** = effort d'implémentation estimé.

| # | Titre | Pertinence | Complexité | Prochaine étape recommandée |
|---|-------|------------|------------|-----------------------------|
| [#384](https://github.com/NikolayDA/picture_helper/issues/384) | [Epic] Aperçu 2D combiné (couleur/transparence/relief/gloss) | 🟠 Haute | 🔴 Haute (epic) | **En cours (epic)** – le dernier point fonctionnel de la phase 1. Ordre : #385/#386 en parallèle → #387 → #388. |
| [#385](https://github.com/NikolayDA/picture_helper/issues/385) | Rendu de relief-shading (sans Qt) | 🟠 Haute | 🟡 Moyenne | **✅ Ready for PR** – proprement délimité, sans dépendances, sans Qt + strictement typé. Le PR suivant le plus solide ; débloque #387. |
| [#386](https://github.com/NikolayDA/picture_helper/issues/386) | Rendu de visualisation du gloss (sans Qt) | 🟡 Moyenne | 🟢 Basse–Moyenne | **✅ Ready for PR** – en parallèle de #385, sans dépendances ; logique d'image pure sans Qt. |
| [#387](https://github.com/NikolayDA/picture_helper/issues/387) | Canevas : modes d'aperçu + pipeline de composite | 🟠 Haute | 🟠 Moyenne–Haute | **Blocked** – nécessite #385 + #386 ; préserver le contrat d'export #363 avec un test de régression. |
| [#388](https://github.com/NikolayDA/picture_helper/issues/388) | UI : sélecteur de mode d'aperçu + bascules relief/gloss + i18n | 🟡 Moyenne | 🟡 Moyenne | **Blocked** – nécessite #387 ; clôt l'epic #384. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | [Epic] Mettre à jour la doc utilisateur & publier la release | 🟠 Haute | 🟡 Moyenne (epic) | **En cours (epic)** – #390/#391 en parallèle maintenant → (merge epic #384) → #392. |
| [#390](https://github.com/NikolayDA/picture_helper/issues/390) | Mettre à jour le guide utilisateur ANLEITUNG (+ 5 i18n) pour les nouvelles fonctionnalités | 🟠 Haute | 🔴 Haute (L, 6 langues) | **Ready for PR** – bien délimité mais volumineux ; clôt aussi **#357**. |
| [#391](https://github.com/NikolayDA/picture_helper/issues/391) | Mettre à jour le README + captures d'écran + i18n | 🟡 Moyenne–Haute | 🟡 Moyenne | **Ready for PR (avec réserve)** – la partie texte est immédiatement faisable ; les captures nécessitent un lancement à jour de l'app. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Publier la release v2.5.0 (CHANGELOG/version/tag/artefacts) | 🟠 Haute | 🟡 Moyenne | **Blocked** – nécessite #390 + #391, idéalement après #384. |
| [#357](https://github.com/NikolayDA/picture_helper/issues/357) | Docs : ouverture par chemin initial/Finder absente d'ANLEITUNG §4 | 🟢 Basse | 🟢 Basse | **Fusionnée dans #390** – encore possible comme petit PR indépendant, mais sera normalement close avec #390. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF n'est pas supporté comme format d'entrée | 🟢 Basse | 🟢 Basse | **Ready for PR (docs)** – HEIC exclu délibérément (commentaire 2026-06-21). Clarifier seulement README/ANLEITUNG, puis clore. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | 🟢 Basse | 🟢 Basse | **Ready for PR (opportuniste)** – pas un bloqueur produit ou CI ; le plus utile d'abord (asserter l'extrémité du lasso, la ligne de `test_helpers`, consolider les tests `set_brush_size`). |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test : respecter les overrides de permissions job-level dans le reusable WF | 🟢 Basse | 🟡 Moyenne | **Needs refinement** – d'abord documenter la sémantique GitHub (top-level vs. effectif-par-job) ; ne pas affaiblir le guard OIDC #303. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec "Quota exceeded" | 🟡 Moyenne | 🟢 Basse | **Blocked (externe)** – le durcissement côté repo via #322/#342 (clos) est fait ; le blocage restant est la quota OpenAI/billing. Après restauration, lancer une fois le scan programmé manuellement puis clore. |

### Prochaines étapes recommandées (ordre des PR)

1. Implémenter **#385** et **#386** (rendus relief/gloss sans Qt) comme petits PR
   parallélisables — les meilleurs candidats « prêts & bien délimités » ; ils
   débloquent #387.
2. Enchaîner avec **#387** → **#388** pour terminer l'epic **#384** (aperçu 2D
   combiné) ; préserver le contrat d'export #363 avec un test de régression.
3. Intégrer **#390** et **#391** en parallèle comme PR docs (clôt aussi **#357**) ;
   caser **#339** comme petit PR indépendant.
4. Publier **#392** (release v2.5.0) seulement après #390/#391 et idéalement
   après #384.
5. Traiter **#299** opportunément ; reporter **#318** jusqu'à ce que la sémantique
   soit établie et garder **#245** bloqué en externe.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
