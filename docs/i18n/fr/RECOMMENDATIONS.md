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

## Issues GitHub Ouvertes — État du Triage (2026-06-21)

Au 2026-06-21, GitHub affiche encore **5** issues ouvertes : **#245**, **#299**,
**#318**, **#322** et **#339**. Les issues projet/couches et tests sécurité
précédemment listées, **#323**, **#324**, **#326** et **#329–#335**, sont
terminées dans les merge commits **#337**, **#338** et **#340**. **#322** dispose
aussi maintenant de **#342** et doit être commentée puis close après vérification
du merge.

| # | Titre | Recommandation labels/statut | Proposition commentaire/statut |
|---|-------|------------------------------|--------------------------------|
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec "Quota exceeded" | `security`; **laisser ouvert / bloqué externe** | Commenter que le durcissement côté repo est couvert par #323/#324 et #322/#342 ; le blocage restant est la quota OpenAI/billing. Après restauration, lancer une fois le scan programmé manuellement puis clore. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Hygiène des tests : assertions faibles/redondances | `quality`, `testing`; **ouvert / basse priorité** | Commenter que ce n'est pas un bloqueur produit ou CI ; regrouper en cleanup opportuniste lorsque les tests concernés sont modifiés. Aucun changement de statut requis. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test : respecter les overrides de permissions job-level dans le reusable WF | `enhancement`, `testing`; **needs refinement** | Commenter qu'il faut documenter la sémantique GitHub top-level vs. job-level dans le workflow appelé avant tout changement ; ne pas affaiblir le guard OIDC #303. |
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI : chemin maintenance/skip pour le Codex Security Scan planifié | `security`; **clore après #342** | Commenter que #342 implémente le commutateur manuel conservateur (`CODEX_SECURITY_SCAN_ENABLED=false`) avec sortie skip et tests de régression ; clore après merge vérifié. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF n'est pas supporté comme format d'entrée | **Ajouter labels :** `enhancement`, `documentation` (ou `question` si disponible) ; **needs decision** | Commenter qu'une décision produit est nécessaire : documenter explicitement que HEIC n'est pas supporté, ou planifier `pillow-heif`/allowlist `HEIF` optionnel avec test de chargement. Garder ouvert jusqu'à décision. |

### Actions recommandées pour les issues

1. Commenter et clore **#322** une fois le merge de #342 vers `main` vérifié.
2. Labelliser **#339** et prendre une décision produit explicite (clarification
   documentation vs. feature HEIC).
3. Garder **#245** ouvert mais marqué comme bloqué externe ; lier #322/#342 comme
   partie repo terminée.
4. Ne pas implémenter **#318** immédiatement ; documenter d'abord la sémantique
   des permissions GitHub.
5. Garder **#299** comme cleanup de tests basse priorité.

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
