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

La liste active d'analyse de code est vide. Ruff, mypy et la suite de tests locale restent la base avant tout nouveau PR. Depuis le dernier instantané (2026-07-18, 3 tickets ouverts), un tout nouvel epic est apparu et a été largement implémenté en une seule journée : **#639** (recette de publication automatisée via des runners matériels auto-hébergés) avec les sous-tickets **#640–#646** et le ticket de suivi **#648**. État en direct selon la requête GitHub : **12** tickets ouverts.

### Terminé depuis la dernière revue

- **Ancienne base stable :** **N1/N2/N4/N5/N6/N7/N8** et **O2–O7** restent faits ; les epics **#329/#344/#358/#384** (N9–N12) plus le correctif d'export **#363** sont fusionnés/archivés.
- **Pipeline de hauteur 16 bits entièrement achevé :** l'epic **#581** incluant **#587/#588** (PR #610), **#589** (PR #612) et **#590** (PR #613) est dans `main` ; tous les gates/revues sont verts, matrice de recette complète présente.
- **Modèle de sécurité et cœur 3D achevés :** **#551** (CodeQL automatique, Codex manuel uniquement) via PR #619 ; **#592–#594** (cœur géométrique, viewer, intégration workflow/cache) via PR #620 dans `main`. Les lacunes de couverture **#597/#598** closes via PR #615 ; la lacune du guide **#606** corrigée dans les six langues via PR #616.
- **Packaging Raspberry Pi 5 durci :** trois véritables bogues de démarrage trouvés et corrigés sur le matériel cible — point d'entrée AppImage (PR #627), compatibilité glibc aarch64 (PR #627), mise en place des plugins Qt/RUNPATH (PR #631) ; le démarrage de l'application sur le Pi 5 est confirmé, aperçu 3D fonctionnel inclus.
- **Nouvel epic #639 ouvert ET largement implémenté :** ADR + documentation opérationnelle (#640), squelette de workflow `release-abnahme.yml` (#641), smokes matériels Linux/macOS avec preuve de provenance GL (#642/#643), test de régression E2E de publication (#644), suite de performance GL en direct (#645), et pré-évaluation vision + matrice de recette (#646) sont entièrement implémentés et vérifiés dans `main` via PR #647 et PR #649. Ils restent listés comme ouverts uniquement parce que les descriptions des PR utilisent une formulation allemande (« Löst #640 … ») au lieu des mots-clés de clôture anglais reconnus par GitHub (voir le commentaire sur #639 du 2026-07-21).

### Encore ouvert

- **O8 🟢 — Imprécision du prototype :** les outils de hauteur restent verrouillés dans la maquette après génération ; cela ne concerne que la maquette, l'application réelle n'est pas affectée (#347).
- **Suivi administratif 🟢 — Quatre tickets sont terminés mais non fermés :** #640–#643 sont entièrement implémentés via PR #647 ; seul le mot-clé de clôture anglais manquant dans la description de la PR a empêché la fermeture automatique (voir le commentaire sur #639).
- **Lacune documentaire 🟢 — README.md ne mentionne pas la section 3D :** l'aperçu de relief 3D est documenté dans `ANLEITUNG.md` et `CHANGELOG.md`, mais `README.md` ne le mentionne toujours pas (liste des fonctionnalités, étape 5 d'utilisation, captures d'écran). Cela correspond au critère encore ouvert « documentation ANLEITUNG/README/architecture mise à jour » dans #582/#595.

## Tickets GitHub ouverts — Triage (2026-07-21)

État en direct : **12** tickets ouverts. Évaluation : **Pertinence** = importance pour la feuille de route/les utilisateurs, **Complexité** = effort d'implémentation estimé, **Modèle/Effort** = modèle Claude et effort de raisonnement recommandés.

### Regroupements pertinents

- **Automatisation de la recette de publication** (#639 → {#640 ‖ #641} → {#642 ‖ #643} → #644 → #645 → #646) : techniquement déjà implémentée via PR #647/#649 ; il ne reste que la vérification par preuves matérielles réelles (dispatch des runners) et les quatre fermetures administratives #640–#643.
- **#648** est la seule véritable tâche de code restante dans ce domaine : un mode automatisation/capture d'écran intégré à l'artefact packagé, afin que la preuve de rendu 3D provienne du paquet réel plutôt que d'un checkout source.
- **Aperçu de relief 3D** (#582 → #595) : le MVP fonctionnel est terminé (Go pour le périmètre automatisable, voir le rapport de recette sur #582) ; #595 attend le même dispatch matériel que ci-dessus, plus #648.
- **#245** reste un pur tracker externe de facturation/quota OpenAI et ne bloque ni CodeQL, ni la publication, ni la 3D.

| # | Titre | Pertinence | Complexité | Modèle/Effort | Prochaine étape recommandée |
|---|-------|------------|------------|----------------|-----------------------------|
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | [Epic] Recette de publication automatisée | 🟠 Élevée | 🟠 Élevée (très large, largement implémenté) | – (epic de suivi) | **In progress, nearly done** – #640–#646 techniquement implémentés via PR #647/#649 ; attend la vérification par les runners + la fermeture des sous-tickets ; #648 est le seul effort réellement restant. |
| [#640](https://github.com/NikolayDA/picture_helper/issues/640) | ADR + documentation opérationnelle/sécurité pour les runners de recette auto-hébergés | 🟡 Moyenne | 🟢 Faible (terminé) | – (aucune tâche de code) | **Ready to close** – ADR + `RELEASE_AUTOMATION.md` intégralement présents via PR #647 ; seul le mot-clé de clôture manque. |
| [#641](https://github.com/NikolayDA/picture_helper/issues/641) | Workflow `release-abnahme.yml` : squelette, récupération des artefacts, format des preuves | 🟠 Élevée | 🟢 Faible (terminé) | – (aucune tâche de code) | **Ready to close** – workflow + test de gouvernance présents via PR #647 ; seul le mot-clé de clôture manque. |
| [#642](https://github.com/NikolayDA/picture_helper/issues/642) | Smokes Linux (AppImage/.deb) avec preuve de provenance GL | 🟠 Élevée | 🟡 Moyenne (logique principale terminée) | – (aucune tâche de code) | **Ready to close / needs live verification** – `abnahme_smoke.py` + tests présents via PR #647 ; l'exécution réelle n'aura lieu qu'après dispatch sur le runner Pi 5. |
| [#643](https://github.com/NikolayDA/picture_helper/issues/643) | Smoke DMG macOS avec preuve Retina/HiDPI | 🟠 Élevée | 🟡 Moyenne (logique principale terminée) | – (aucune tâche de code) | **Ready to close / needs live verification** – même base que #642, pour le runner M3. |
| [#644](https://github.com/NikolayDA/picture_helper/issues/644) | Scénario de régression de publication E2E en test `ui` | 🟠 Élevée | 🟡 Moyenne (terminé) | – (aucune tâche de code) | **Ready to close / needs live verification** – `tests/test_e2e_release_regression.py` (ui_smoke) présent via PR #649 ; la branche Ready nécessite un véritable dispatch GL. |
| [#645](https://github.com/NikolayDA/picture_helper/issues/645) | Suite de performance GL en direct dans le harnais de benchmark | 🟡 Moyenne | 🟡 Moyenne (terminé) | – (aucune tâche de code) | **Ready to close / needs live verification** – suite `preview3d-live` dans `scripts/benchmark.py` présente via PR #649. |
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | Pré-évaluation vision, agrégation des preuves, matrice de recette | 🟡 Moyenne | 🟡 Moyenne (terminé) | – (aucune tâche de code) | **Ready to close / needs live verification** – `abnahme_vision_check.py`/`abnahme_aggregate.py` présents via PR #647/#649 ; nécessite aussi un secret `ANTHROPIC_API_KEY` pour une évaluation réelle. |
| [#648](https://github.com/NikolayDA/picture_helper/issues/648) | Preuve de rendu 3D natif de l'artefact packagé | 🟡 Moyenne | 🟡 Moyenne | Sonnet 5 · moyen | **Ready for PR** – une lacune clairement délimitée et indépendante (un point d'ancrage d'automatisation de capture d'écran dans l'artefact packagé plutôt qu'un checkout source) ; la seule véritable tâche de code restante de l'automatisation de recette. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, packaging, documentation, recette end-to-end | 🟡 Moyenne | 🟡 Moyenne (en baisse, l'automatisation existe désormais) | Sonnet 5 · moyen | **Blocked** – attend le même dispatch matériel que #639, plus #648 ; README.md a aussi toujours besoin de la section 3D. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Véritable aperçu de relief 3D | 🟡 Moyenne | 🟠 Élevée (très large, MVP terminé) | – (epic de suivi) | **Blocked** – attend uniquement #595. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurer le quota OpenAI pour la vérification manuelle Codex Security | 🟢 Faible | 🟢 Faible | – (aucune tâche de code) | **Blocked (external)** – inchangé depuis le 2026-07-15 : un pur tracker externe de facturation qui ne bloque rien dans le dépôt. |

### Recommandé ensuite (ordre des PR)

1. **Fermer #640–#643** — l'implémentation est complète (PR #647) ; seule la confirmation manuelle du propriétaire manque.
2. **Implémenter #648** — la seule tâche de code restante : un mode automatisation/capture d'écran dans l'artefact packagé pour une véritable preuve de rendu 3D.
3. **Enregistrer les runners auto-hébergés et dispatcher `release-abnahme.yml`** — vérifie #642–#646 avec des preuves matérielles réelles et produit la matrice de recette pour #595.
4. **Après une exécution verte + #648 :** fermer #595, puis #582 (bloqué uniquement par #595) ; ajouter la section 3D à README.md.
5. **#245** reste en l'état — aucun correctif du dépôt ne peut résoudre le blocage externe de facturation OpenAI.

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
