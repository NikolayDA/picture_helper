[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de Code et Recommandations Priorisées : BgRemover

## Échelle de Priorité

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bugs, plantages ou perte de données |
| 🟠 | Haute | Impact clair sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile pour la qualité, la lisibilité ou les tests |
| 🟢 | Basse | Polissage optionnel ou amélioration de processus |

## État Actuel (2026-06-29)

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

## Issues GitHub Ouvertes — État du Triage (2026-06-29, mis à jour)

Au 2026-06-29, GitHub affiche **8** issues ouvertes : **#245**, **#299**, **#318**,
**#389**, **#392**, **#404**, **#406** et **#408**. Nouvelle le même jour :
l'audit doc/code **#408** (docs API/CLI face aux signatures actuelles — sans
drift) ; les issues qualité/robustesse **#406** et **#404** (nouvelles depuis la
revue 2026-06-25) restent ouvertes. Les
lots docs **#390/#391**, la note d'ouverture **#357** et l'exclusion HEIC
**#339** restent closes ; seule l'étape de release **#392** reste dans **#389**.

**Revue des commentaires :** Aucun nouveau commentaire externe ; ceux sur
#392/#299/#245 sont des notes de triage de l'owner cohérentes avec l'état actuel, et #408 est nouvelle et sans commentaire — aucune mise à jour nécessaire.

**Nouveaux constats vérifiés dans le code :** #406 — `_derive_physical_size`
(`eufymake_export.py:217`) n'a aucun appelant (`parse_size_mm` seulement là, par
ailleurs dans `project_model.py`). #404 — `compose_relief`/`compose_gloss`
(`canvas.py:555/564`) lèvent au lieu de dégrader vers COLOR dans le rendu.
#408 — audit sans constat : les signatures de `CLAUDE.md`/`README.md` et le chemin CLI `bgremover image.png` correspondent au code.

### Regroupements Recommandés

- **Lot release :** **#392** est prêt ; clore l'epic **#389** après vérification
  du tag, du release body et des artefacts macOS/Linux.
- **Gains rapides qualité :** **#406** et **#404** sont petits, autonomes et
  prêts pour PR — idéaux comme PRs qualité courtes à côté du chemin de release,
  mais séparées de lui (modules différents, pas de diff commun).
- Ne pas mêler **#299/#318/#245** au chemin de release : qualité, recherche et
  exploitation bloquée en externe sont indépendantes.

Évaluation : **Pertinence** = importance pour la roadmap/les utilisateurs,
**Complexité** = effort d'implémentation estimé.

| # | Titre | Pertinence | Complexité | Prochaine étape recommandée |
|---|-------|------------|------------|-----------------------------|
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Publier la release v2.5.0 (CHANGELOG/version/tag/artefacts) | 🟠 Haute | 🟡 Moyenne | **Prêt** – #390, #391 et #384 sont closes. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | [Epic] Mettre à jour la doc utilisateur & publier la release | 🟠 Haute | 🟢 Basse (reste) | **Presque terminé** – seule #392 reste ouverte. |
| [#404](https://github.com/NikolayDA/picture_helper/issues/404) | Aperçu : un écart de taille ne dégrade pas vers COLOR | 🟡 Moyenne | 🟢 Basse | **Prêt pour PR** – encapsuler `compose_relief`/`compose_gloss` de façon défensive et revenir à `base` en cas d'écart de taille, avec un test de régression de rendu/pixel. Latent mais bien cadré. |
| [#406](https://github.com/NikolayDA/picture_helper/issues/406) | Code mort : `_derive_physical_size` inutilisé dans `eufymake_export.py` | 🟢 Basse | 🟢 Basse | **Prêt pour PR** – supprimer la fonction, nettoyer l'import `parse_size_mm` et mettre à jour la phrase de géométrie de CLAUDE.md vers le chemin `_derive_target`/modèle de projet. Trivial, critères d'acceptation complets. |
| [#408](https://github.com/NikolayDA/picture_helper/issues/408) | Audit doc/code : les docs API/CLI correspondent aux signatures (sans drift) | 🟢 Basse | 🟢 Basse | **Informatif / clôturable** – audit sans constat, aucun correctif code/doc requis. Suivi optionnel : un vrai `docs/api.md` via autodoc pour détecter automatiquement un drift futur. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | 🟢 Basse | 🟢 Basse | **Après v2.5.0** – lasso, résultat NumPy modifiable, masque wand complet et paramétrage brush d'abord. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test : respecter les overrides de permissions job-level dans le reusable WF | 🟢 Basse | 🟡 Moyenne | **À affiner** – prouver la sémantique ; coder seulement pour un faux positif démontré et préserver #303. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec "Quota exceeded" | 🟡 Moyenne | 🟢 Basse | **Blocked (externe)** – le durcissement côté repo via #322/#342 (clos) est fait ; le blocage restant est la quota OpenAI/billing. Après restauration, lancer une fois le scan programmé manuellement puis clore. |

### Prochaines étapes recommandées (ordre des PR)

1. Avancer **#406** et **#404** comme PRs qualité courtes — toutes deux
   vérifiées, autonomes et prêtes pour PR (modules différents, faible risque).
2. Exécuter **#392** ensuite et clore l'epic **#389** après vérification du tag,
   du release body et des deux artefacts.
3. Traiter **#299** après v2.5.0 ; rechercher **#318** seulement (à affiner),
   clore **#408** comme audit informatif sans action et garder **#245** bloqué
   jusqu'au retour de la quota externe.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
