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

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-20)

Au 2026-06-20, **14** issues sont ouvertes. Depuis l'évaluation du 2026-06-19,
**#311** (corps de release) a été close. Les nouveautés sont l'épopée **#329**
(modèle de données projet/calques — fondation pour la height map, le gloss et
l'export EufyMake) avec ses six sous-issues **#330–#335**, ainsi que le constat
de couverture de tests **#326** (GIF déclaré comme format d'entrée mais non
testé). L'épopée des calques est le rang #1 priorisé de la feuille de route :
**#330** (modèle de domaine sans Qt) est la clé de voûte sans dépendance et
faisable tout de suite, tandis que les sous-issues restantes sont bloquées le
long de la chaîne de dépendances (#330 → #331 → #332/#333 → #334 → #335). Encore
ouverts depuis la série précédente : **#318** (garde de permissions), **#245**
(quota CI, bloqué en externe), les trois suivis de durcissement de **#245**
**#322–#324**, et l'élément d'hygiène de tests de basse priorité **#299**. Toutes
les issues ouvertes ont été revérifiées sur le code actuel.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#329](https://github.com/NikolayDA/picture_helper/issues/329) | [Épopée] Modèle de données projet/calques (fondation pour height map/gloss/EufyMake) | 🟠 Haute | 🟠 Haute | **Épopée / suivi** — rang #1 de la feuille de route ; avancer via les six sous-issues, pas de PR propre |
| [#330](https://github.com/NikolayDA/picture_helper/issues/330) | Modèle de domaine `Project` + `Layer` (sans Qt) | 🟠 Haute | 🟡 Moyenne | **Prêt pour PR** — clé de voûte sans dépendance ; sans Qt, strictement typé, compositing/rôles, `tests/test_project_model.py`. Point de départ de l'épopée |
| [#331](https://github.com/NikolayDA/picture_helper/issues/331) | Undo/redo à l'échelle du projet (historique conscient des calques) | 🟠 Haute | 🟠 Haute | **Bloqué par #330** — historique conscient des calques, testable isolément avant le câblage canvas |
| [#332](https://github.com/NikolayDA/picture_helper/issues/332) | Canvas : rendu composite + calque actif | 🟠 Haute | 🟠 Haute | **Bloqué par #330/#331** — le plus gros morceau ; bascule du comportement vers le mode calques, parité mono-calque |
| [#333](https://github.com/NikolayDA/picture_helper/issues/333) | Format de fichier projet : sauvegarde/chargement (versionné, atomique, validé) | 🟠 Haute | 🟠 Haute | **Bloqué par #330** (en parallèle de #332) — conteneur ZIP `.bgrproj`, atomique/validé/versionné |
| [#334](https://github.com/NikolayDA/picture_helper/issues/334) | UI : panneau des calques + menu projet + i18n | 🟠 Haute | 🟠 Haute | **Bloqué par #330/#332/#333** — panneau + actions de menu, parité i18n de/en |
| [#335](https://github.com/NikolayDA/picture_helper/issues/335) | Migration & intégration (image→projet, récents, réglages, export) | 🟠 Haute | 🟡 Moyenne | **Bloqué par #330/#332/#333/#334** — issue de clôture de l'épopée ; aucune régression dans les flux existants |
| [#326](https://github.com/NikolayDA/picture_helper/issues/326) | Tests : le format d'entrée GIF est déclaré mais non testé | 🟡 Moyenne | 🟢 Basse | **Prêt pour PR, faisable maintenant** — un test de chargement via `ImageLoadWorker` couvre le garde `_ALLOWED_IMAGE_FORMATS` pour le GIF ; pas de sauvegarde/export |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test : respecter les surcharges de permissions au niveau job dans le WF réutilisable | 🟡 Moyenne | 🟡 Moyenne | **À affiner** — confirmer d'abord la sémantique de validation au démarrage de GitHub (niveau top vs. effectif par job) ; actuellement un faux positif purement théorique (aucune surcharge au niveau job dans `ci.yml`), et le garde OIDC #303 ne doit pas s'affaiblir |
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI : ajouter un chemin de maintenance/skip pour le Codex Security Scan planifié | 🟡 Moyenne | 🟡 Moyenne | **Suivi de #245** — décision de périmètre interrupteur manuel vs. auto-skip propre visible (vs. les deux) ; gate dans le job `cadence`, « disabled → skipped, pas failed », garder le moindre privilège (pas de `issues: write` dans le job de scan), test statique |
| [#323](https://github.com/NikolayDA/picture_helper/issues/323) | Tests : couvrir le sync des issues de sécurité pour le filtre de sévérité et les findings vides | 🟢 Basse | 🟢 Basse | **Suivi de #245, réalisable maintenant** — tests de régression pour `reportable: false`, le seuil de sévérité et « No reportable findings » ; sans réseau via `--dry-run`/appels directs |
| [#324](https://github.com/NikolayDA/picture_helper/issues/324) | Security : test de gouvernance docs pour le prompt du Codex scan vs. périmètre du dépôt | 🟢 Basse | 🟢 Basse | **Suivi de #245, réalisable maintenant** — test statique que le prompt nomme toujours les surfaces de sécurité de haut niveau actuelles ; complète les assertions de prompt existantes |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | 🟢 Basse | 🟢 Basse | Pas de bug de correction ; le plus utile d'abord (déplacement d'endpoint, consolider `set_brush_size`), le reste au besoin |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec « Quota exceeded » | 🟡 Moyenne | 🟢 Basse | **Bloqué (externe) :** restaurer le quota côté compte. Le durcissement côté dépôt est suivi dans **#322–#324** ; le skip propre est la variante B de #322 |

### Issues Regroupables

- L'épopée des calques **#329** est avancée via ses sous-issues dans l'ordre prescrit ; **#332** et **#333** peuvent être parallélisées après #330.
- **#323/#324** (les deux suivis de #245, tests statiques du scan de sécurité sans réseau) peuvent être regroupées dans une seule PR.
- **#318** reste séparée — elle nécessite d'abord une sémantique GitHub documentée avant de toucher à `_required_permissions`.
- **#299** est de l'hygiène de tests opportuniste et ne devrait accompagner que si un test déjà touché est concerné.

### Ordre de PR Recommandé

1. **#330** — la clé de voûte sans dépendance de l'épopée des calques ; débloque #331/#332/#333.
2. **#326** — gain rapide et bien cadré (test de chargement GIF) qui comble une lacune de couverture.
3. **#323 / #324** — durcissement sans réseau du scan de sécurité, réalisable à tout moment.
4. **#331 → #332 / #333 → #334 → #335** — l'épopée des calques le long de sa chaîne de dépendances.
5. **#322** — chemin de maintenance/skip après une décision délibérée auto/manuel (suivi de #245).
6. **#318** — affiner le garde de permissions une fois la sémantique de GitHub documentée, sans affaiblir le cas de régression OIDC.
7. **#245** — restaurer le quota côté compte (bloqué en externe).
8. **#299** — hygiène des tests au besoin.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
