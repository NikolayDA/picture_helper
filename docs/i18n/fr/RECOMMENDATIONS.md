[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-09-02, v2.9.0 publiée, inventaire ouvert entièrement audité)

**Audit quotidien 2026-09-02 (état `1ec9d96`) :** 42 tickets ouverts confrontés
à l'état réel de GitHub. Le tableau de triage était faux dans les six versions
depuis le 2026-08-30 – `recommendations-live-check` est rouge depuis :
**#914**, **#918**, **#939** et **#949** manquaient, et **#692** figurait encore
comme ouvert (clos le 2026-09-01 via la PR #947). L'audit du 2026-08-31 donnait
en outre #918 pour clos ; il avait été rouvert le même jour après son contrôle
de clôture et n'attend plus que la prochaine vraie publication. Ce tour corrige
les deux. Nouvelles évaluations : #949 (audit de la suite de tests, quatre
modifications de tests actionnables, aucun défaut de production), #939 (canal
d'alerte permanent du heartbeat, ne pas fermer) et l'épopée #914. Aucun nouveau
constat 🔴.

**Évaluation de publication : aucune nouvelle version n'est due.** Depuis
`v2.9.0` (2026-08-29), 25 commits sur la branche principale, exclusivement
automatisation de publication, documentation et gouvernance ; `[Unreleased]` est
vide et, dans le paquet `bgremover/`, seul le hook de preuve
`update_check_probe.py` (#917) a changé. Une construction candidate n'apporterait
aucun contenu visible pour les utilisateurs. Périmètre prévu pour une future
**v2.10.0** : le moteur de tonalité/niveaux de gris COLOR (#693/#694 de l'épopée
#682) sur la base de l'ADR #692 désormais approuvé, éventuellement avec #949.

**EufyMake #681/#687–#691 :** la PR #951 est fusionnée et #690 étend le jeu reproductible à 41 fixtures individuels et sept vrais paquets d'export. Les DPI X/Y séparés, les conflits manifeste/`pHYs`, Gloss 0/128/255, la normalisation 64…192, les dimensions divergentes, Alpha×Gloss et HEIGHT×Gloss sont couverts automatiquement. Studio 4.2.2 confirme le contrat d'import de #689 ; les nouveaux imports #690 et toutes les mesures physiques Gloss/HEIGHT restent ouverts. #687 atteint 17/18 critères et attend la revue finale après les tests réels.

Inchangé et fermé : **N1/N2/N4/N5/N6/N7/N8**, **O1–O8**, tout ce qui est terminé depuis le **2026-06-25**, les versions v2.7.0 à v2.9.0, ainsi que l'épopée #741 avec ses onze tickets enfants, l'épopée #805 avec #806–#811, #817 et #821 ; nouvellement clôturés depuis la dernière synchronisation : #943 (PR #944) et #692 (PR #947) (détails : Tours précédents).

En cours : une ligne par ticket dans le tableau de triage ci-dessous. Depuis #821, ni le compte ni les lignes ne sont maintenus à la main – `scripts/recommendations_live_check.py --write` met à jour les six versions depuis l'état en direct GitHub, tandis que les colonnes d'évaluation restent un travail éditorial.

## Tickets GitHub ouverts — Triage

| # | Titre | Pertinence | Complexité | Modèle recommandé (effort) | Prochaine étape |
|---|-------|------------|------------|------------------------------|------------------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Épopée] Profil cible EufyMake – valider Height/Gloss/mm-DPI | 🟠 Élevée (justesse de la principale cible d'export) | 🔴 Élevée (5 sous-tickets, matériel physique requis) | – (épopée) | #687 atteint 17/18 CA ; seule la revue finale après les tests réels reste, tandis que #691 attend #688–#690 |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Inventaire des hypothèses, sources fabricant, matrice de tests | 🟠 Élevée (base contraignante pour #688–#691) | 🔴 Élevée (livrables propres terminés ; lacunes fixtures/cellules de #688–#690 ouvertes, le reste nécessite du matériel réel) | – (aucun agent ; matériel EufyMake réel requis) | Bloquée (externe) – 17/18 critères remplis ; I-06 est observé dans Studio et seule la revue finale après #688–#690 reste |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | Valider la profondeur de bits/sémantique HEIGHT sur matériel réel | 🟠 Élevée (affecte directement la hauteur du relief) | 🔴 Élevée (imprimante physique, fixtures, journal de mesures) | – (aucun agent ; matériel EufyMake réel requis) | Bloqué (externe) : la PR #948 est fusionnée et la préparation du dépôt est complète ; restent la matrice d'import et les mesures physiques sûres d'impression, de relief et en mm sur E1 |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | Valider le contrat mm/DPI, taille cible, positionnement | 🟠 Élevée (taille d'impression/registration) | 🔴 Élevée (mesures physiques, motifs de contrôle) | – (aucun agent ; matériel réel requis) | En cours : le jeu du dépôt et le sous-contrat Studio sont documentés — repli 72 DPI, `pHYs` X/Y, limite du manifeste, taille manuelle, rotation et recadrage d'une image. Restent le recadrage/enregistrement inter-rôles, les mesures physiques et les tolérances d'impression |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Valider la sémantique gloss/vernis | 🟡 Moyenne (gloss déjà marqué « expérimental » dans le code) | 🔴 Élevée (impressions physiques, consommation de matériau) | – (aucun agent ; matériel réel requis) | Bloqué (externe) + préparation complète : le schéma 4 couvre absent/0/128/255, rampe limitée, dimensions, Alpha×Gloss, HEIGHT×Gloss et repérage ; restent l'import Studio et la preuve physique |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Intégrer le profil cible versionné dans validator/writer/dialogue/documentation | 🟠 Élevée (renforce le chemin d'export de production) | 🟠 Élevée (transversal sur eufymake_export/_validate/_writer + UI) | Opus, élevé | Bloqué – attend #688–#690 |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Épopée] Moteur de tonalité/niveaux de gris COLOR | 🟡 Moyen-élevé (fondation de la feuille de route laser, pas de bug actif) | 🔴 Élevé (4 tickets enfants restants : noyau→UI→intégration→recette) | – (épopée) | En cours : l'ADR #692 est approuvé ; vient ensuite le noyau #693 |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | Noyau sans Qt : histogramme/niveaux de gris/niveaux/gamma | 🟡 Moyen-élevé | 🟡 Moyen (étend `color_ops.py`, bien isolé et testable) | Sonnet, élevé | Prêt à démarrer : l'ADR #692 (PR #947) fournit le contrat de données ; implémenter et tester le noyau selon ses formules |
| [#694](https://github.com/NikolayDA/picture_helper/issues/694) | Aperçu en direct + interface pour histogramme/niveaux/gamma | 🟡 Moyenne | 🟡 Moyenne-élevée (UI Qt, garde debounce/génération comme l'aperçu de hauteur) | Sonnet, élevé | Bloqué – attend le noyau #693 |
| [#695](https://github.com/NikolayDA/picture_helper/issues/695) | Intégration calques/sélection/historique/projet | 🟡 Moyenne | 🟠 Élevée (nombreuses transitions d'état : annuler/rétablir, sélection, état modifié) | Opus, élevé | Bloqué – attend #693/#694 |
| [#696](https://github.com/NikolayDA/picture_helper/issues/696) | Recette performance/E2E/documentation/interface laser | 🟡 Moyenne (gate de clôture, pas une nouvelle fonctionnalité) | 🟠 Élevée (suite de benchmarks, E2E, documentation, contrat d'adaptateur) | Opus, élevé | Bloqué – ticket de clôture après #695 |
| [#882](https://github.com/NikolayDA/picture_helper/issues/882) | [Epic] BgRemover dans le Mac App Store | 🟡 Moyenne-haute (nouveau canal, pas un défaut actuel) | 🔴 Haute (licence, sandbox, packaging, store et gouvernance) | – (Epic) | Bloquée – créer et décider d'abord la stratégie de licence comme sous-tâche concrète de phase 0 |
| [#883](https://github.com/NikolayDA/picture_helper/issues/883) | [MAS] Stratégie de licence : PySide6 vs Riverbank et relicensing | 🟠 Haute (bloque tout travail technique MAS) | 🔴 Haute (décision licence/owner, port Qt possible, risque résiduel) | Opus, élevé + revue owner/juridique | Prête – rédiger l'ADR et la décision ; créer une issue de port si PySide6 est choisi |
| [#884](https://github.com/NikolayDA/picture_helper/issues/884) | [MAS] Inscription Apple Developer Program | 🟠 Haute (bloque certificats et accès store) | 🟢 Faible (étape manuelle compte/paiement) | – (aucun agent ; account holder) | Bloquée (externe) – choisir le type de compte, terminer inscription/2FA et attribuer le renouvellement |
| [#885](https://github.com/NikolayDA/picture_helper/issues/885) | [MAS] Identités de signature, App ID et profil de provisioning | 🟠 Haute (prérequis du build signé) | 🟡 Moyenne (secrets owner et contrat bundle-ID/packaging) | – (aucun agent ; account holder/admin) | Bloquée – attend #884 ; créer certificats, App ID/profil explicites et figer le bundle ID |
| [#886](https://github.com/NikolayDA/picture_helper/issues/886) | [MAS] Définir et appliquer les entitlements App Sandbox | 🟠 Haute (prérequis obligatoire store/exécution) | 🟠 Haute (tous les Mach-O, packaging et preuve matérielle) | Opus, élevé | Bloquée – attend la décision #883 ; implémenter entitlements minimaux et tests artefact/matériel |
| [#887](https://github.com/NikolayDA/picture_helper/issues/887) | [MAS] Processus enfant d'inférence compatible sandbox | 🟠 Haute (la fonction IA centrale doit fonctionner) | 🔴 Haute (spawn/signature helper, règle deux clés, vraie sandbox) | Opus, élevé | Bloquée – attend #886 ; décider re-exec/helper et prouver le self-check IA sur matériel |
| [#888](https://github.com/NikolayDA/picture_helper/issues/888) | [MAS] Signets security-scoped pour fichiers et dossiers | 🟠 Haute (Récents et sauvegarde rapide cassent après redémarrage) | 🟠 Haute (autorisations persistantes, images/projets/dossiers, gating) | Opus, élevé | Bloquée – attend #886 ; implémenter le contrat de signets et tester le redémarrage sandboxed |
| [#889](https://github.com/NikolayDA/picture_helper/issues/889) | [MAS] Écritures sandbox-safe et export EufyMake | 🟠 Haute (sauvegarde/export et intégrité des données) | 🔴 Haute (atomicité multi-chemins et autorisations Powerbox) | Opus, élevé | Bloquée – attend #886 ; concevoir écritures/extensions/cible dans le grant et tester sur matériel |
| [#890](https://github.com/NikolayDA/picture_helper/issues/890) | [MAS] Cache du modèle IA dans le conteneur sandbox | 🟡 Moyenne (chemin modèle déterministe) | 🟡 Moyenne (contrat isolé et décision de migration) | Sonnet, élevé | Bloquée – attend #886 et se coordonne avec #893 ; fixer `U2NET_HOME` et décider la migration |
| [#891](https://github.com/NikolayDA/picture_helper/issues/891) | [MAS] Indicateur de canal et gating du contrôle des mises à jour | 🟠 Haute (règle 2.4.5, aucune auto-mise à jour) | 🟠 Moyenne-haute (indicateur central sur menu, réglages, workers, hooks) | Sonnet, élevé | Bloquée – attend #883 ; ajouter le contrat de canal et tester négativement réseau/UI MAS |
| [#892](https://github.com/NikolayDA/picture_helper/issues/892) | [MAS] Retirer AiInstallDialog et intégrer le backend IA | 🟠 Haute (aucune installation de code exécutable) | 🟡 Moyenne (gating et test de packaging contraignant) | Sonnet, élevé | Bloquée – attend #891 ; masquer dialogue/menu et prouver rembg/onnxruntime intégrés |
| [#893](https://github.com/NikolayDA/picture_helper/issues/893) | [MAS] Intégrer u2net ou le télécharger au premier lancement | 🟠 Haute (risque review et fonction IA) | 🟠 Haute (décision produit/review, packaging ou nouveau flux i18n) | Opus, élevé | Bloquée – attend #890/#891 et #883 ; documenter, implémenter et vérifier la variante en sandbox |
| [#894](https://github.com/NikolayDA/picture_helper/issues/894) | [MAS] Choisir le packaging Briefcase vs py2app | 🟠 Haute (détermine la viabilité technique) | 🟠 Haute (spike sandbox/signature/upload ouvert) | Opus, élevé | Bloquée – attend #883 ; tester Briefcase, repli py2app et consigner l'ADR |
| [#895](https://github.com/NikolayDA/picture_helper/issues/895) | [MAS] App onedir, signature inside-out et nettoyage Qt | 🟠 Haute (build exécutable central) | 🔴 Haute (binaires, Qt, provisioning, validation upload) | Opus, élevé | Bloquée – attend #885/#886/#894 ; implémenter et valider sans erreurs ITMS |
| [#896](https://github.com/NikolayDA/picture_helper/issues/896) | [MAS] Info.plist et icônes complets | 🟡 Moyenne-haute (métadonnées et contrat plateforme) | 🟡 Moyenne (champs, architecture, assets déterministes) | Sonnet, élevé | Bloquée – attend #895 ; décider OS/architecture/types et ajouter les tests |
| [#897](https://github.com/NikolayDA/picture_helper/issues/897) | [MAS] PKG productbuild signé et upload Transporter | 🟠 Haute (artefact soumissible) | 🟠 Haute (seconde signature, automatisation, premier upload manuel) | Opus, élevé + account holder | Bloquée – attend #885/#895/#896 ; créer un PKG reproductible et consigner la livraison |
| [#898](https://github.com/NikolayDA/picture_helper/issues/898) | [MAS] CI, contrat six artefacts et scan PKG | 🟠 Haute (intégrité fail-closed) | 🔴 Haute (secrets, contrat, extracteur, malware/chemins) | Opus, élevé | Bloquée – attend #895/#897 ; étendre leg, contrat, scan payload et tests |
| [#899](https://github.com/NikolayDA/picture_helper/issues/899) | [MAS] Smokes sandboxed sur matériel réel | 🟠 Haute (preuve runtime contraignante) | 🔴 Haute (PKG, spawn IA, Powerbox, 3D, schéma) | Opus, élevé + matériel macOS | Bloquée (externe) – attend #898 ; implémenter et exécuter sur ARM64 self-hosted |
| [#900](https://github.com/NikolayDA/picture_helper/issues/900) | [MAS] Bêta TestFlight macOS | 🟠 Haute (preuve précoce review/appareil externe) | 🟡 Moyenne (coordination ASC/testeur manuelle) | – (aucun agent ; titulaire/testeur) | Bloquée – attend #897/#901 ; tester IA, fichiers et 3D sur un autre appareil |
| [#901](https://github.com/NikolayDA/picture_helper/issues/901) | [MAS] Fiche ASC et métadonnées en six langues | 🟠 Haute (nom, listing et prérequis de soumission) | 🟠 Moyenne-haute (owner et six jeux localisés) | Sonnet, élevé + titulaire | Bloquée – attend #884/#885 ; réserver nom, versionner/charger textes, rating/storefronts |
| [#902](https://github.com/NikolayDA/picture_helper/issues/902) | [MAS] Captures Store 16:10 | 🟡 Moyenne-haute (matériel obligatoire) | 🟡 Moyenne (formats, alpha, décision langues) | Sonnet, élevé | Bloquée – attend le build #895 ; étendre l'automatisation et vérifier le jeu |
| [#903](https://github.com/NikolayDA/picture_helper/issues/903) | [MAS] Politique de confidentialité et App Privacy | 🟠 Haute (obligatoire dans le store et l'app) | 🟡 Moyenne (policy, hébergement, lien i18n, questionnaire) | Sonnet, élevé + owner | Bloquée – attend #891/#893 ; publier/lier et prouver « Data Not Collected » |
| [#904](https://github.com/NikolayDA/picture_helper/issues/904) | [MAS] Statut DSA UE, mentions légales et GPSR | 🟠 Haute (storefronts UE et obligations) | 🟠 Moyenne-haute (classement, vérification, risque juridique) | – (aucun agent ; owner/juridique) | Bloquée – attend #884 ; déclarer trader et documenter DDG/GPSR avec owner/rappel |
| [#905](https://github.com/NikolayDA/picture_helper/issues/905) | [MAS] Étendre la gouvernance release | 🟠 Haute (évite un canal hors contrat fail-closed) | 🟠 Haute (runbook, checklist, contrat, policy, six changelogs) | Opus, élevé | Bloquée – accompagne #898/#899 ; porter contrats/tests à six artefacts |
| [#906](https://github.com/NikolayDA/picture_helper/issues/906) | [MAS] Première soumission et revue | 🟠 Haute (gate manuel de publication) | 🔴 Haute (dépendances, risques, communication Apple) | – (aucun agent ; release owner) | Bloquée – après #896/#897/#899/#901–#905 contrôler, soumettre et consigner résultat/issues |
| [#907](https://github.com/NikolayDA/picture_helper/issues/907) | [MAS] Exploitation : renouvellement, mises à jour, canaux | 🟡 Moyenne-haute (disponibilité et séparation à long terme) | 🟡 Moyenne (runbook, responsabilités, rappels, matrice) | Opus, élevé + owner | Bloquée – préparer tôt, finaliser après #906 ; fixer routines renewal/update/web |
| [#914](https://github.com/NikolayDA/picture_helper/issues/914) | [Épopée] Processus de publication : runners, preuves automatisées, gel de main | 🟠 Élevé (exploitation des publications ; 8 des 9 lots livrés) | 🟡 Moyen (il ne reste que le reliquat de #918) | – (épopée) | Presque terminée : il ne manque que le critère de succès « `main` reste fusionnable », que la prochaine publication réelle démontre via #918 |
| [#918](https://github.com/NikolayDA/picture_helper/issues/918) | Réf de publication au lieu du gel de main (ADR + garde-fous fail-closed) | 🟠 Élevé (`main` reste fusionnable pendant une publication) | 🟢 Faible (code, documentation et ruleset en place) | – (aucun agent ; prochaine publication) | Bloqué (externe) : rouvert le 2026-08-31 après son contrôle de clôture ; la PR #936 et le ruleset actif 21941216 sont documentés, il ne manque qu'une exécution dont la recette post-publication a démarré de façon démontrable sur `release/vX.Y.Z` |
| [#939](https://github.com/NikolayDA/picture_helper/issues/939) | Exploitation : runners auto-hébergés (canal d'alerte du heartbeat) | 🟡 Moyen (canal d'exploitation, pas de code produit) | 🟢 Faible (observation seule) | – (aucun agent ; owner du dépôt) | Ouvert en permanence : ne pas fermer (`RUNNER_HEARTBEAT_ISSUE`) ; le FAIL du 2026-08-31 était le test prévu du canal d'alerte et l'étape de nettoyage est faite (exécution planifiée 33496675995 verte, x86_64 ignoré, Mac et Pi réussis) |
| [#949](https://github.com/NikolayDA/picture_helper/issues/949) | Audit de la suite de tests 2026-09-02 (dérive RESOURCES, CropOverlay, lacunes de couverture) | 🟡 Moyen (qualité des tests et protection contre la dérive, aucun défaut de production) | 🟢 Faible-moyen (quatre modifications de tests bien délimitées, sans changement de production) | Sonnet, moyen | Prêt à démarrer : dériver les valeurs attendues de `RESOURCES.md` des vraies lignes `uses:`, faire passer `test_crop_overlay.py` à `set_position()`/`crop_rect()` et couvrir la branche rectangle de `crop_image()` ainsi que la branche non RGBA d'`adjust_color()` |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurer le quota OpenAI pour la vérification manuelle Codex Security | 🟢 Faible (ne bloque qu'un scan manuel optionnel) | 🟢 Faible (purement opérationnel, aucun code) | – (aucun agent ; propriétaire du dépôt : facturation) | Bloquée (externe) – la dernière exécution (29233060507, 2026-07-13) ne prouve aucun scan réussi ; facturation/quota toujours non résolu |

### Recommandé ensuite

1. **#693** (noyau sans Qt) : l'ADR #692 est approuvé, l'épopée COLOR #682 peut donc démarrer ;
   viennent ensuite #694, #695 et #696 dans cet ordre.
2. **#949** : quatre petites modifications de tests bien délimitées, sans risque de production ;
   une bonne PR en parallèle de l'épopée.
3. Après validation du matériel et de l'appareil, effectuer les mesures physiques restantes de
   **#689** avec le reste de #687, #688 et #690 ; la partie import Studio de #689 est documentée.
4. **#883** (stratégie de licence MAS) décide la voie Mac App Store #882 : sans
   cette décision de l'owner, toute la chaîne #884–#907 reste bloquée.

## Tours précédents

Protocoles détaillés depuis v2.2 : [RECOMMENDATIONS-2026-v2.2-v2.9.fr.md](../../history/RECOMMENDATIONS-2026-v2.2-v2.9.fr.md).

Constats historiques et journaux de travail (tours 1–5) : [RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
