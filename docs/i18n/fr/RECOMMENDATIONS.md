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

### Encore Ouvert

- **O1 🟠 — Langues runtime supplémentaires.** L'allemand et l'anglais sont
  sélectionnables dans l'app. Les langues documentaires es/fr/uk/zh ne sont pas
  des locales runtime ; les ajouter clé par clé dans `bgremover.i18n` et tester.
- **O7 🟠 — Sous-processus pour rembg/ONNX (suite de #231, suivi dans #270).**
  La PR #267 a borné le fallback d'arrêt, mais le travail IA non interruptible
  tourne encore dans le thread avec `terminate()` en sortie d'urgence. La
  solution complète déplace rembg/ONNX dans un sous-processus.

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-14, triage de clôture)

Après la fusion des PRs **#263–#269** et la clôture de **#261** (résolue par la
PR #268), **5** issues restent ouvertes. Neuf issues précédemment ouvertes —
**#231, #234, #248, #249, #257, #258, #259, #260** et **#261** — ont été closes
via les PRs fusionnées. Le suivi d'architecture reporté de #231 (sous-processus
rembg/ONNX, feuille de route **O7**) a été ouvert comme **#270**. Toutes les
issues ouvertes ont été revérifiées sur le code actuel.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#270](https://github.com/NikolayDA/picture_helper/issues/270) | Déplacer l'inférence rembg/ONNX dans un sous-processus (suite de #231) | 🟠 Haute | 🟡 Moyenne | PR d'architecture dédiée : la PR #267 n'a que borné l'arrêt. Déplacer rembg/ONNX dans un sous-processus pour que `terminate()` ne soit plus la sortie d'urgence IA ; tests fermeture/annulation/appel bloqué |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` charge toute la GUI PyQt6 | 🟡 Moyenne | 🟡 Moyenne | Prêt pour PR : préserver l'API publique avec des exports paresseux PEP 562, ajouter un test de régression d'import. Code inchangé : `__init__.py:15-43` ré-exporte toujours la GUI |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec « Quota exceeded » | 🟡 Moyenne | 🟢 Basse | Corriger le quota côté compte ; dans le dépôt, clarifier l'échec plus un bump optionnel vers Node 24, sans changement forcé `setup-node` |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | La limite mémoire d'undo exclut la pile redo | 🟢 Basse | 🟡 Moyenne | Budget undo/redo partagé ; seulement mesurer l'original/la mémoire Qt. Code inchangé : `canvas_history.py` ne compte que `_undo_bytes`, redo borné uniquement par `maxlen` |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README : l'URL de clonage renvoie 404 aux utilisateurs anonymes | 🟢 Basse | 🟢 Basse | « Runde 5 » est corrigé ; décider public vs. privé/sur invitation d'abord, puis mettre à jour la doc ou clore |

### Ordre de PR Recommandé

1. **#232** — imports légers via des exports paresseux PEP 562.
2. **#245** — restaurer le quota à l'extérieur ; durcissement optionnel du workflow (Node 24) séparé.
3. **#235** — implémenter un budget historique undo/redo partagé.
4. **#161** — décider le modèle de publication, puis modifier la doc ou clore.
5. **#270** — planifier le sous-processus rembg/ONNX comme PR d'architecture dédiée (suite de #231).

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
