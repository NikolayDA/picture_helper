[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-22)

Ruff, mypy et la suite de tests locale restent la base avant tout nouveau PR. Depuis le dernier tour, **#640–#645** et **#648** ont été intégralement acceptés puis fermés (preuves matérielles issues du dispatch `release-abnahme.yml` du 2026-07-21 ; le commentaire de matrice de recette sur #595 montre les smokes macOS-arm64 et Pi-5, l'E2E 3D natif et la performance GL en direct tous **✅ satisfaits**). État en direct : **6** tickets ouverts — le niveau le plus bas depuis le début de l'epic 3D.

### Résultat de la revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7** et tout ce qui a été achevé depuis le **2026-06-25** reste fait.
- L'epic **#639** est achevé pour 7 de ses 8 tickets enfants ; la liste de contrôle du corps du ticket avait toutes les cases décochées alors que #640–#645/#648 étaient fermés depuis longtemps — réconcilié aujourd'hui (commentaire + édition du corps sur #639), sans impact code.
- **Aucun ticket ne se qualifie actuellement comme « prêt pour un PR »** au sens classique : les six tickets ouverts restants sont soit des tâches purement externes/opérationnelles (configurer un secret, régler une facturation), soit des epics bloqués exclusivement par ces mêmes tâches externes. Il n'existe actuellement aucune tâche ouverte côté code non traitée.
- Le seul blocage restant pour toute la chaîne : le secret de dépôt `ANTHROPIC_API_KEY` est manquant (**#656**), donc la ligne « Screenshots (pré-évaluation vision) » de la matrice de recette affiche toujours `❓ non évalué` au lieu de véritables verdicts. Le chemin de repli lui-même fonctionne exactement comme prévu.

## Tickets GitHub ouverts — Triage (2026-07-22)

| # | Titre | Pertinence | Complexité | Modèle recommandé (effort) | Prochaine étape |
|---|-------|------------|------------|------------------------------|------------------|
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Activer le secret ANTHROPIC_API_KEY pour la pré-évaluation vision | 🟠 Élevée (dernier blocage de toute la chaîne de recette) | 🟢 Faible (purement opérationnel, aucun code) | – (aucun agent ; propriétaire du dépôt : Settings → Secrets) | Bloquée (externe) – configurer le secret, puis revérifier le dispatch |
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | Pré-évaluation vision, agrégation des preuves, matrice de recette | 🟠 Élevée (dernier ticket enfant ouvert de l'epic #639) | 🟢 Faible (code/tests déjà fusionnés dans PR #649) | Sonnet 5 (faible) – vérification uniquement, aucun nouveau code attendu | Vérification nécessaire – après #656, contrôler un dispatch réel avec vision, puis fermer |
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | [Epic] Recette de publication automatisée | 🟠 Élevée (epic, 7/8 tickets enfants faits) | 🟢 Faible (seul #646 reste) | – (epic, pas d'usage direct d'agent) | Bloquée – se ferme automatiquement avec #646 |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, packaging, documentation, recette end-to-end | 🟠 Élevée (porte de recette de l'epic #582) | 🟢 Faible (tous les critères satisfaits sauf la ligne vision) | – (aucune tâche de code) | Bloquée – attend #646/#656, puis fermer |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Véritable aperçu de relief 3D | 🟠 Élevée (epic volumineux, presque terminé) | 🟢 Faible (seul #595 reste) | – (epic, pas d'usage direct d'agent) | Bloquée – se ferme automatiquement avec #595 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurer le quota OpenAI pour la vérification manuelle Codex Security | 🟢 Faible (ne bloque qu'un scan manuel optionnel) | 🟢 Faible (purement opérationnel, aucun code) | – (aucun agent ; propriétaire du dépôt : facturation) | Bloquée (externe) – régler la facturation/le quota sur le projet de la plateforme OpenAI |

### Recommandé ensuite

1. Régler d'abord **#656** (configurer le secret de dépôt `ANTHROPIC_API_KEY`) — le seul levier restant qui débloque toute la chaîne #646 → #639 → #595 → #582.
2. Ensuite, dispatcher à nouveau `release-abnahme.yml` via `workflow_dispatch` et vérifier si la ligne vision de la matrice de recette affiche de véritables verdicts au lieu de `non évalué` (contrôler ponctuellement un couple par rapport aux captures, comme l'exige #656).
3. Une fois la ligne vision au vert, fermer **#646** ; cela ferme en cascade **#639**, **#595** et **#582** (revérifier brièvement chacun avant de le fermer manuellement).
4. Laisser **#245** comme pur tracker externe de facturation/quota ; aucune action possible ni nécessaire dans le dépôt.
5. Il n'existe actuellement **aucun** ticket ouvert justifiant un nouveau PR de code — la prochaine tâche d'agent sensée est la vérification après #656, pas une nouvelle implémentation.

## Tours précédents

- **2026-07-22 (revue des tickets)** — réévaluation complète de tous les tickets ouverts : #640–#645 et #648 avaient déjà été acceptés et fermés via le dispatch de recette du 2026-07-21, mais la liste de contrôle des tickets enfants de l'epic #639 n'avait pas été réconciliée (corrigé aujourd'hui via édition du corps + commentaire, sans impact code). Nouveau blocage **#656** (secret `ANTHROPIC_API_KEY` manquant) identifié comme seul levier restant pour #646/#639/#595/#582. État en direct : 6 tickets ouverts — le niveau le plus bas depuis l'epic #582.
- **2026-07-21 (automatisation de la recette de publication, epic #639)** — epic #639 ouvert et largement implémenté en une seule journée : ADR/documentation (#640), squelette de workflow (#641), smokes matériels Linux/macOS (#642/#643), test de régression E2E (#644), suite de performance GL en direct (#645), pré-évaluation vision + matrice de recette (#646) — tous fusionnés via PR #647/#649 mais non fermés automatiquement en raison de mots-clés de clôture en allemand ; le ticket de suivi #648 (preuve de rendu 3D natif) reste la seule tâche de code ouverte. État en direct : 12 tickets ouverts.
- **2026-07-20 (smoke matériel Pi 5)** — trois véritables bogues de packaging trouvés et corrigés sur Raspberry Pi 5 (PR #627/#631) ; le démarrage de l'application est confirmé, aperçu 3D inclus.
- **2026-07-18 (audit post-merge)** — #551 et #592–#594 confirmés ; #582/#595 rouverts pour preuves manquantes ; état en direct 3.
- **2026-07-18 (suivi d'audit #614–#616)** — durcissement des versions futures de la PR #614 consigné ; #597/#598 achevés via PR #615 et #606 via PR #616 ; état en direct 7.
- **2026-07-17 (clôture de l'epic 16 bits)** — #581/#587–#590 achevés via PR #610/#612/#613 ; tous les gates et revues verts, matrice de recette présente, état en direct 10.
- **2026-07-16 (release v2.6.0)** — tag sur `f24cef69829da8e37aa400dad471dc4d607b89b3`, exécution 29531147950 verte, cinq artefacts publics retéléchargés et vérifiés par SHA-256 ; #580/#585/#607 clos, état en direct 15.
- **2026-07-16 (gate candidat)** — #584 clos via le véritable gate à cinq artefacts (exécution finale 29529595934 sur `f24cef69829da8e37aa400dad471dc4d607b89b3`, SHA-256 + analyse de secrets par artefact, smokes plateforme natifs) ; #585 débloqué.
- **2026-07-15/16 (suivi d'audit)** — #583/#586/#591 achevés ; #584 rouvert après confirmation que le gate candidat reste à faire ; état en direct 17.
- **2026-07-14** — état en direct toujours à 2 tickets ouverts (#245, #551), inchangé depuis la clôture de l'epic la veille.
- **2026-07-13 (clôture d'epic)** — epic **#563** entièrement clos : les huit sous-tickets (**#564–#571**) fermés via PR #573/#574 ; instantané réduit à 2.
- **2026-07-13 (audit des tickets)** — epic **#563** + huit sous-tickets ouverts, les 11 tickets ouverts réévalués, commentaires du propriétaire pris en compte ; aucun fermé ; instantané mis à jour à 11.
- **2026-07-12** — formalisation v2.3.0 (#550), correctif SessionStart (#553), sync (#549, modèle de PR #552 via PR #557), audit (#542 clos, #549–#553 ouverts) et version **v2.5.0** (vague #435/#392/#426/#389, #299/#541/#318).
- **2026-07-11** — epic #425 achevé (#430 PR #526, i18n runtime ES/FR/UK/ZH complète, **O1** fait ; #431/#432 PR #529 ; suivi final #530/#531 PR #533/#535).
- **2026-07-05–10** — #509/#510/#514–#517 (PR #520–#522), #490, vague Dark Mode/icônes rail, inspecteur en cartes (#413/#414), #499–#501/#503, peaufinage icônes/barre d'état.
- **2026-06-29** — #404/#406/#408 achevés (PR #412), vague de redesign ouverte.
- **v2.2, « admiring-mayer » (#1–#15)** — liste externe, achevée ou écartée en cas de faux positif.

Constats historiques et journaux de travail (tours 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
