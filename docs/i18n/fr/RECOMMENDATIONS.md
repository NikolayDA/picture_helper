[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de Code et Recommandations Priorisées : BgRemover

## Échelle de Priorité

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bugs, plantages ou perte de données |
| 🟠 | Haute | Impact clair sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile pour la qualité, la lisibilité ou les tests |
| 🟢 | Basse | Polissage optionnel ou amélioration de processus |

## État Actuel (2026-06-24)

La liste active d'analyse de code est vide. Ruff, mypy et la suite locale
restent la baseline avant de nouveaux PRs.

### Terminé Depuis La Dernière Revue

- **N1/N2/N4/N5/N6/N7/N8** sont terminés : chemins d'erreur, limite de taille,
  extensions, sauvegarde atomique, paquets Qt CI, import paresseux et docstring.
- **O2/O3/O4/O5/O6** sont implémentés : paquets Linux, workflow de release,
  matrice complète, `ui_smoke` et raccourcis adaptés aux plateformes.
- Les anciens constats clos (dont l'epic EufyMake **#351**/**#352–#355** et le
  sous-processus rembg/ONNX **#270**/**#285**/**#286**) sont terminés dans les
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
- **N12 ✅ — Aperçu 2D combiné (epic #384) livré.** Moteurs relief/gloss sans Qt
  (#385/#386), modes explicites indépendants du calque actif avec cache borné
  (#387), et menu Affichage/panneau Aperçu synchronisés avec intensité en direct
  et bascule gloss (#388) ; la matrice mode×calque préserve bit pour bit le contrat
  d'export #363. Le suivi #397 (PR #398) fait passer les aperçus transitoires par
  la même pipeline, respecte les calques de données masqués et évite efficacement
  le relief d'intensité 0.
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

Au 2026-06-24, après #384/#387/#388 et le suivi P2 **#397** (PR #398), GitHub
affiche **9** issues ouvertes. Les epics **#375** (sortie physique mm/DPI +
validation d'export) et **#384** (aperçu 2D combiné) sont terminés et clos.
L'epic roadmap restant est :

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
substantielle des issues ; #397 est déjà close par la PR #398.

### Regroupements Recommandés

- **Lot guide :** **#390 + #357** et la partie ANLEITUNG de **#339**.
- **Lot README :** **#391**, la partie README de **#339** et des captures à jour.
- **Lot release :** garder **#392** séparé et ne le lancer qu'après les deux PR docs.
- Ne pas mêler **#299/#318/#245** au chemin de release : qualité, recherche et
  exploitation bloquée en externe sont indépendantes.

Évaluation : **Pertinence** = importance pour la roadmap/les utilisateurs,
**Complexité** = effort d'implémentation estimé.

| # | Titre | Pertinence | Complexité | Prochaine étape recommandée |
|---|-------|------------|------------|-----------------------------|
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | [Epic] Mettre à jour la doc utilisateur & publier la release | 🟠 Haute | 🟡 Moyenne (epic) | **Prêt à démarrer** – deux lots docs en parallèle, puis #392. |
| [#390](https://github.com/NikolayDA/picture_helper/issues/390) | Mettre à jour le guide utilisateur ANLEITUNG (+ 5 i18n) pour les nouvelles fonctionnalités | 🟠 Haute | 🔴 Haute (L, 6 langues) | **Lot A** – inclure **#357** et la partie ANLEITUNG de **#339**. |
| [#391](https://github.com/NikolayDA/picture_helper/issues/391) | Mettre à jour le README + captures d'écran + i18n | 🟡 Moyenne–Haute | 🟡 Moyenne | **Lot B** – inclure la partie README de **#339** et des captures actuelles. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Publier la release v2.5.0 (CHANGELOG/version/tag/artefacts) | 🟠 Haute | 🟡 Moyenne | **Blocked** – nécessite #390 + #391. |
| [#357](https://github.com/NikolayDA/picture_helper/issues/357) | Docs : ouverture par chemin initial/Finder absente d'ANLEITUNG §4 | 🟢 Basse | 🟢 Basse | **Dans le lot A** – ne pas traiter séparément ; clore avec #390. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF n'est pas supporté comme format d'entrée | 🟢 Basse | 🟢 Basse | **Répartir entre A/B** – ANLEITUNG dans #390, README dans #391 ; clore après les deux. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | 🟢 Basse | 🟢 Basse | **Après v2.5.0** – lasso, résultat NumPy modifiable, masque wand complet et paramétrage brush d'abord. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test : respecter les overrides de permissions job-level dans le reusable WF | 🟢 Basse | 🟡 Moyenne | **Recherche parallèle** – prouver la sémantique ; coder seulement pour un faux positif démontré et préserver #303. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec "Quota exceeded" | 🟡 Moyenne | 🟢 Basse | **Blocked (externe)** – le durcissement côté repo via #322/#342 (clos) est fait ; le blocage restant est la quota OpenAI/billing. Après restauration, lancer une fois le scan programmé manuellement puis clore. |

### Prochaines étapes recommandées (ordre des PR)

1. Livrer en parallèle le **lot A (#390 + #357 + partie ANLEITUNG de #339)** et
   le **lot B (#391 + partie README de #339)** ; clore #339 après les deux.
2. Exécuter **#392** ensuite et clore l'epic **#389** après vérification du tag,
   du release body et des deux artefacts.
3. Traiter **#299** après v2.5.0 ; rechercher **#318** en parallèle sans coder sans
   preuve et garder **#245** bloqué jusqu'au retour de la quota externe.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
