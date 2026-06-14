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
  et **#249** ; **#261** a été résolu via la PR #268.

### Encore Ouvert

- **O1 🟠 — Langues runtime supplémentaires.** L'allemand et l'anglais sont
  sélectionnables dans l'app. Les langues documentaires es/fr/uk/zh ne sont pas
  des locales runtime ; les ajouter clé par clé dans `bgremover.i18n` et tester.
- **O7 🟠 — Sous-processus pour rembg/ONNX (suite de #231).** La PR #267 a borné
  le fallback d'arrêt, mais le travail IA non interruptible tourne encore dans
  le thread avec `terminate()` en sortie d'urgence. La solution complète déplace
  rembg/ONNX dans un sous-processus — une PR d'architecture dédiée, sans issue.

## Issues GitHub Ouvertes — Évaluation des Priorités (2026-06-14, triage de clôture)

Après la fusion des PRs **#263–#269**, seules **5** issues restent ouvertes.
Huit issues précédemment listées (**#231, #234, #248, #249, #257, #258, #259,
#260**) ont été fusionnées et closes automatiquement. **#261** a été corrigée
par la PR **#268** mais est restée ouverte administrativement faute de mot-clé
`Closes` et devrait être close. Quatre issues actionnables restent ; toutes ont
été revérifiées sur le code actuel.

| # | Titre | Pertinence | Complexité | Recommandation |
|---|-------|------------|------------|----------------|
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` charge toute la GUI PyQt6 | 🟡 Moyenne | 🟡 Moyenne | Prêt pour PR : préserver l'API publique avec des exports paresseux PEP 562, ajouter un test de régression d'import. Code inchangé : `__init__.py:15-43` ré-exporte toujours la GUI |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | La limite mémoire d'undo exclut la pile redo | 🟢 Basse | 🟡 Moyenne | Budget undo/redo partagé ; seulement mesurer l'original/la mémoire Qt. Code inchangé : `canvas_history.py` ne compte que `_undo_bytes`, redo borné uniquement par `maxlen` |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI : Codex Security Scan échoue avec « Quota exceeded » | 🟡 Moyenne | 🟢 Basse | Corriger le quota côté compte ; dans le dépôt, clarifier l'échec plus un bump optionnel vers Node 24, sans changement forcé `setup-node` |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README : l'URL de clonage renvoie 404 aux utilisateurs anonymes | 🟢 Basse | 🟢 Basse | « Runde 5 » est corrigé ; décider public vs. privé/sur invitation d'abord, puis mettre à jour la doc ou clore |
| [#261](https://github.com/NikolayDA/picture_helper/issues/261) | L'overlay du pinceau scanne tout le masque à chaque mouvement | ✅ Fait | — | Résolu par la PR **#268** (fusionnée) ; l'issue est restée ouverte sans mot-clé `Closes` — la clore administrativement |

### Ordre de PR Recommandé

1. **#232** — imports légers via des exports paresseux PEP 562.
2. **#235** — implémenter un budget historique undo/redo partagé.
3. **#245** — restaurer le quota à l'extérieur ; durcissement optionnel du workflow (Node 24, gestion d'erreurs) séparé.
4. **#161** — décider le modèle de publication, puis modifier la doc ou clore.
5. **O7** — planifier le sous-processus rembg/ONNX comme PR d'architecture dédiée (suite de #231).
6. **Admin** — clore **#261** (fait via la PR #268).

## Séries Précédentes

- **2026-06-01, « modest-shannon » (A–E)** — 5 constats, tous terminés.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, terminée ou écartée lorsqu'il s'agissait d'un faux positif.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
