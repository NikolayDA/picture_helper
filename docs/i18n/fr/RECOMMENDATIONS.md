[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-07-21)

Ruff, mypy et la suite de tests locale restent la base avant tout nouveau PR. Les PR **#647**, **#649**, **#650**, **#651** et **#652** ont été fusionnées aujourd'hui. ADR, workflow, smokes, E2E, GL en direct, agrégation et hook natif de l'artefact sont dans `main`. **#640** et **#641** sont fermés. **#648** a été rouvert faute d'une exécution matérielle réussie avec preuves distinctes pour AppImage, `.deb` installé et DMG. État en direct : **10** tickets ouverts.

### Résultat de la revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8** et **O2–O7** restent faits ; les epics **#329/#344/#358/#384** (N9–N12) plus le correctif d'export **#363** sont fusionnés/archivés ; depuis le 2026-06-25, également **#404/#406/#408** (PR #412) clos.
- **Pipeline de hauteur 16 bits entièrement achevé :** l'epic **#581** incluant **#587/#588** (PR #610), **#589** (PR #612) et **#590** (PR #613) est dans `main` ; tous les gates/revues sont verts, matrice de recette complète présente.
- **Modèle de sécurité et cœur 3D achevés :** **#551** (CodeQL automatique, Codex manuel uniquement) via PR #619 ; **#592–#594** (cœur géométrique, viewer, intégration workflow/cache) via PR #620 dans `main`. Les lacunes de couverture **#597/#598** closes via PR #615 ; la lacune du guide **#606** corrigée dans les six langues via PR #616.
- **Packaging Raspberry Pi 5 durci :** trois véritables bogues de démarrage trouvés et corrigés sur le matériel cible — point d'entrée AppImage (PR #627), compatibilité glibc aarch64 (PR #627), mise en place des plugins Qt/RUNPATH (PR #631) ; le démarrage de l'application sur le Pi 5 est confirmé, aperçu 3D fonctionnel inclus.
- **Code de recette complet, preuve matérielle en attente :** ce suivi ajoute une capture par classe de paquet, des contrôles de session graphique, une nouvelle preuve 3D après Save/Open, trois mesures GL avec RSS réel du processus et un champ `target_issue` validé.

- **Preuve opérationnelle 🟡 :** #642–#646 et #648 rouvert restent ouverts jusqu'à un vrai dispatch matériel graphique.
- **Tracker externe 🟢 :** #245 reste une question de facturation/quota OpenAI hors dépôt.

## Tickets GitHub ouverts — Triage (2026-07-21)

État en direct : **10** tickets ouverts. Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs, **Complexité** = effort d'implémentation estimé, **Modèle/Effort** = modèle Claude et effort de raisonnement recommandés.

- **Automatisation de la recette** (#639 → #642–#646 + #648) : les chemins de code existent ; la clôture exige des preuves complètes du matériel cible.
- **#648** est rouvert pour les preuves, pas pour un hook manquant : AppImage, `.deb` installé et DMG doivent chacun produire capture 3D native et provenance.
- **Aperçu de relief 3D** (#582 → #595) : le MVP est terminé ; #595 attend la même recette matérielle verte.
- **#245** reste un pur tracker externe de facturation/quota OpenAI et ne bloque ni CodeQL, ni la publication, ni la 3D.

| # | Titre | Pertinence | Complexité | Modèle/Effort | Prochaine étape recommandée |
|---|-------|------------|------------|----------------|-----------------------------|
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | [Epic] Recette de publication automatisée | 🟠 Élevée | 🟠 Élevée (code presque terminé) | – (epic de suivi) | **En cours** – configurer les runners, dispatcher le workflow et examiner les preuves. |
| [#642](https://github.com/NikolayDA/picture_helper/issues/642) | Smokes Linux (AppImage/.deb) avec preuve de provenance GL | 🟠 Élevée | 🟡 Moyenne (logique principale terminée) | – (aucune tâche de code) | **Ready to close / needs live verification** – `abnahme_smoke.py` + tests présents via PR #647 ; l'exécution réelle n'aura lieu qu'après dispatch sur le runner Pi 5. |
| [#643](https://github.com/NikolayDA/picture_helper/issues/643) | Smoke DMG macOS avec preuve Retina/HiDPI | 🟠 Élevée | 🟡 Moyenne (logique principale terminée) | – (aucune tâche de code) | **Ready to close / needs live verification** – même base que #642, pour le runner M3. |
| [#644](https://github.com/NikolayDA/picture_helper/issues/644) | Scénario de régression de publication E2E en test `ui` | 🟠 Élevée | 🟡 Moyenne (terminé) | – (aucune tâche de code) | **Ready to close / needs live verification** – `tests/test_e2e_release_regression.py` (ui_smoke) présent via PR #649 ; la branche Ready nécessite un véritable dispatch GL. |
| [#645](https://github.com/NikolayDA/picture_helper/issues/645) | Suite de performance GL en direct dans le harnais de benchmark | 🟡 Moyenne | 🟡 Moyenne (terminé) | – (aucune tâche de code) | **Ready to close / needs live verification** – suite `preview3d-live` dans `scripts/benchmark.py` présente via PR #649. |
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | Pré-évaluation vision, agrégation des preuves, matrice de recette | 🟡 Moyenne | 🟡 Moyenne (terminé) | – (aucune tâche de code) | **Ready to close / needs live verification** – `abnahme_vision_check.py`/`abnahme_aggregate.py` présents via PR #647/#649 ; nécessite aussi un secret `ANTHROPIC_API_KEY` pour une évaluation réelle. |
| [#648](https://github.com/NikolayDA/picture_helper/issues/648) | Preuve de rendu 3D natif de l'artefact packagé | 🟡 Moyenne | 🟡 Moyenne (code terminé) | – (preuve) | **Rouvert** – fermer seulement après preuves natives AppImage, `.deb` installé et DMG. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, packaging, documentation, recette end-to-end | 🟡 Moyenne | 🟡 Moyenne | – (preuve) | **Bloqué** – attend le dispatch matériel vert de #639. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Véritable aperçu de relief 3D | 🟡 Moyenne | 🟠 Élevée (très large, MVP terminé) | – (epic de suivi) | **Blocked** – attend uniquement #595. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurer le quota OpenAI pour la vérification manuelle Codex Security | 🟢 Faible | 🟢 Faible | – (aucune tâche de code) | **Blocked (external)** – inchangé depuis le 2026-07-15 : un pur tracker externe de facturation qui ne bloque rien dans le dépôt. |

### Recommandé ensuite (ordre des PR)

1. Fusionner ce suivi et configurer les runners dans leurs sessions graphiques selon `docs/RELEASE_AUTOMATION.md`.
2. Dispatcher `release-abnahme.yml` avec tag ou ID de build, toutes les plateformes disponibles et le `target_issue` voulu.
3. Fermer **#642–#646** et **#648** uniquement avec des preuves entièrement vertes, puis **#595** et **#582**.
4. Garder **#245** séparé comme tracker externe de facturation/quota.

*Dérive :* cette mise à jour réconcilie l'instantané avec l'état réel de `main` (historique Git complet, auparavant masqué par un clone superficiel) et une requête GitHub en direct ; elle remplace l'état du 2026-07-18 à 3 tickets ouverts. Les mises à jour futures continuent de revérifier en direct les statuts, listes de contrôle et dépendances plutôt que de reporter un horodatage.

## Tours précédents

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
