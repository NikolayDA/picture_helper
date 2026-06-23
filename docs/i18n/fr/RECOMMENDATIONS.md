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

## Issues GitHub Ouvertes — État du Triage (2026-06-23, mis à jour)

Au 2026-06-23, GitHub affiche **11** issues ouvertes. L'epic EufyMake **#351**
est clos après les PR **#372–#374** : #352–#355 couvrent ADR/modèle, rendu et
writer atomique, validation et UI/settings. #374 corrige aussi l'épuisement des
générateurs `optional_roles` et empêche de remplacer un fichier par un dossier.
Le nouvel epic roadmap **#375** et #376–#380 couvre désormais les sorties mm/DPI
et la validation générale d'export. Restent aussi **#357**, **#339**, **#318**,
**#299** et **#245** ; la revue EufyMake ne nécessite aucun suivi supplémentaire.

Évaluation : **Pertinence** = importance pour la roadmap/les utilisateurs,
**Complexité** = effort d'implémentation estimé.

| # | Titre | Pertinence | Complexité | Prochaine étape recommandée |
|---|-------|------------|------------|-----------------------------|
| [#375](https://github.com/NikolayDA/picture_helper/issues/375) | [Epic] Sortie aux dimensions exactes (mm/DPI) + validation générale d'export | 🟠 Haute | 🔴 Haute (epic) | **Ready for PR — fondation d'abord :** #376 (géométrie sans Qt + métadonnées), puis #377/#378/#379 en parallèle ; #380 achève l'UI et l'epic. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec "Quota exceeded" | 🟡 Moyenne | 🟢 Basse | **Blocked (externe)** – le durcissement côté repo via #322/#342 (clos) est fait ; le blocage restant est la quota OpenAI/billing. Après restauration, lancer une fois le scan programmé manuellement puis clore. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test : respecter les overrides de permissions job-level dans le reusable WF | 🟢 Basse | 🟡 Moyenne | **Needs refinement** – d'abord documenter la sémantique GitHub (top-level vs. effectif-par-job) ; ne pas affaiblir le guard OIDC #303. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF n'est pas supporté comme format d'entrée | 🟢 Basse | 🟢 Basse | **Ready for PR (docs)** – le mainteneur a **exclu HEIC délibérément** (commentaire 2026-06-21). Clarifier seulement README/ANLEITUNG, puis clore. |
| [#357](https://github.com/NikolayDA/picture_helper/issues/357) | Docs : ouverture par chemin initial/Finder absente d'ANLEITUNG §4 | 🟢 Basse | 🟢 Basse | **Ready for PR (docs).** Mettre à jour le guide principal et les cinq copies i18n ; préciser que Récents inclut images et projets `.bgrproj`. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | 🟢 Basse | 🟢 Basse | **Ready for PR (opportuniste)** – pas un bloqueur produit ou CI ; le plus utile d'abord (asserter l'extrémité du lasso, la ligne de `test_helpers`, consolider les tests `set_brush_size`). |

### Revue des PRs/issues fermés le 2026-06-23

Les PR **#372–#374** et les issues **#351–#355** fermées aujourd'hui ont été
revues. ADR, modules sans Qt, UI, persistance et correction post-#373 sont
présents et testés. Aucun constat ne nécessite une nouvelle issue ou un commentaire.

### Prochaines étapes recommandées (ordre des PR)

1. Implémenter **#376** comme fondation, puis **#377**, **#378** et **#379** en
   parallèle, et enfin **#380**.
2. Intercaler **#357** et **#339** comme petits PR docs indépendants.
3. Traiter **#299** opportunément ; reporter **#318** et garder **#245** bloqué
   en externe.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
