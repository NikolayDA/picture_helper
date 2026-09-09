[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-09-09, v2.9.0 publiée, inventaire ouvert entièrement audité)

**Audit quotidien du 2026-09-09 (état `dd6c572`) :** les 56 tickets ouverts ont été
revus ; les quinze nouveaux (#1031–#1045) figurent désormais dans le tableau de triage.
La nouveauté de fond est l'épopée de processus #1032 avec onze lots de travail : la
fenêtre `85eeea4^..dd6c572` compte 156 commits de la branche principale, dont 28 (18 %)
constitués uniquement d'entretien de triage – c'est-à-dire du tableau même que cette
entrée met à jour (#1032 en compte 27 ; l'écart est un commit qui touche aussi l'archive). #1040 veut le supprimer avec le workflow de vérification en direct ;
d'ici là il reste le contrat valable, et cette vérification est rouge depuis le
2026-09-08 pour cette raison précise (exécution 34282863300), sans le moindre changement
de code. Le seul constat nouveau qui touche la base de preuves est #1031 (priorité 0) :
un `bgremover` non éditable et obsolète fait que les tests lancés par chemin de fichier
mesurent du code étranger – la direction dangereuse étant un test qui devient ainsi
**vert**. #1044 (lacune de test pour #1004/#1005, couverture 93 %) et #1045 (référence
`#1023` manquante dans le CHANGELOG) sont deux petites PR immédiatement réalisables.
Aucun nouveau défaut produit et aucun constat 🔴.

**Évaluation de publication : v2.10.0 est recommandée.** Depuis `v2.9.0` (2026-08-29),
83 commits de premier parent, dont douze touchant le code produit. `[Unreleased]` porte
donc un périmètre mineur complet : profil cible EufyMake v2 avec le préflight Studio
4.3.3 (#681/#691), dimensions du plateau confirmées 335 × 420 mm (#971), DPI du projet en
`pHYs` PNG (#996), le passage de Qt à 6.11 (#994, une dizaine d'avis dont CVE-2025-10728
et CVE-2025-10729) et quatre correctifs 3D (#1002, #1004, #1023, #1024), dont #1024
répare une erreur de segmentation. Deux raisons déconseillent d'attendre : l'effet de
sécurité du saut Qt n'atteint les utilisateurs qu'avec l'artefact, et le seuil glibc
relevé (aarch64 2.39, x86_64 2.34) est un changement de plateforme qui mérite d'être
publié et annoncé. Le moteur de tonalité COLOR (#693 et suiv.) n'est **pas** une raison
d'attendre : c'est le périmètre suivant. Avant la construction du candidat (le point 1
de #1045, la référence `#1023` dans le CHANGELOG, est traité) : les étapes 1/2 du
runbook via `scripts/prepare_release.py 2.10.0`, y compris les lacunes
rédactionnelles `TODO(release)` (`NOTES-01`). La même exécution fournit aussi la preuve
de bout en bout encore manquante pour #914 et #918.

**EufyMake #681/#687–#691 :** le jeu reproductible contient 42 fixtures unitaires et sept vrais paquets d'export inchangés (schéma 5). Les 29 cellules d'import obligatoires sans impression sont terminées dans la référence historique Studio 4.2.2 comme dans le test de régression complet 4.3.3 ; I-09 (`.empf`) reste non bloquant.
Les 13/13 projets natifs préparés se chargent et douze projets actifs atteignent l'aperçu. Cela prouve l'interface et la préparation des projets, mais aucun effet physique de HEIGHT, de dimension, de gloss ou de repérage. Restent les mesures E1 de #688–#690 et la revue finale de #687.

Inchangé et fermé : **N1/N2/N4/N5/N6/N7/N8**, **O1–O8**, tout ce qui est terminé depuis le **2026-06-25**, les versions v2.7.0 à v2.9.0, ainsi que l'épopée #741 avec ses onze tickets enfants, l'épopée #805 avec #806–#811, #817 et #821 ; nouvellement clôturés depuis la dernière synchronisation : #943 (PR #944), #692 (PR #947), ainsi que la revue ANLEITUNG #963 avec #964–#966, #968 et #969 (PR #972) et #967 (PR #973), ainsi que l'audit de la suite de tests #949 (PR #977) et la garde du PDF #974 (PR #979), ainsi que l'escalade par paliers du heartbeat #958 (PR #981), ainsi que la synchronisation de la documentation #982 (PR #984), ainsi que le rattrapage des porte-étiquettes #975 (PR #986), ainsi que le rattrapage du tableau de triage #995 (PR #997), ainsi que la suppression de code mort #992/#993 (PR #998), ainsi que la montée de version Qt #994 (détails : Tours précédents).

En cours : une ligne par ticket dans le tableau de triage ci-dessous. Depuis #821, ni le compte ni les lignes ne sont maintenus à la main – `scripts/recommendations_live_check.py --write` met à jour les six versions depuis l'état en direct GitHub, tandis que les colonnes d'évaluation restent un travail éditorial.

## Tickets GitHub ouverts — Triage

| # | Titre | Pertinence | Complexité | Modèle recommandé (effort) | Prochaine étape |
|---|-------|------------|------------|------------------------------|------------------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Épopée] Profil cible EufyMake – valider Height/Gloss/mm-DPI | 🟠 Élevée (justesse de la principale cible d'export) | 🔴 Élevée (5 sous-tickets, matériel physique requis) | – (épopée) | Intégration et 29 cellules obligatoires sans impression terminées ; I-09 non bloquant. Restent #688–#690 et la revue finale |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Inventaire des hypothèses, sources fabricant, matrice de tests | 🟠 Élevée (base contraignante pour #688–#691) | 🔴 Élevée (matériel du dépôt complet ; suite sur matériel réel) | – (aucun agent ; matériel EufyMake réel requis) | Bloquée (externe) – 17/18 critères et les 29 cellules d'import obligatoires terminés. Seule la revue après #688–#690 reste |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | Valider la profondeur de bits/sémantique HEIGHT sur matériel réel | 🟠 Élevée (affecte directement la hauteur du relief) | 🔴 Élevée (imprimante physique, fixtures, journal de mesures) | – (aucun agent ; matériel EufyMake réel requis) | Bloqué (externe) – y compris la paire I-14 directe de filtrage/normalisation, toutes les prévalidations sont terminées ; restent les mesures physiques de précision, filtrage, relief et mm |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | Valider le contrat mm/DPI, taille cible, positionnement | 🟠 Élevée (taille d'impression/registration) | 🔴 Élevée (mesures physiques, motifs de contrôle) | – (aucun agent ; matériel réel requis) | Bloqué (externe) – contrat Studio, recadrage et gestion du ratio HEIGHT compris, prouvé. Restent seulement recalage physique, mesures et tolérances |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Valider la sémantique gloss/vernis | 🟡 Moyenne (gloss déjà marqué « expérimental » dans le code) | 🔴 Élevée (impressions physiques, consommation de matériau) | – (aucun agent ; matériel réel requis) | Bloqué (externe) – mode natif `Gloss Varnish` prévalidé ; restent recalage par cellule, polarité, intensité et effet physique |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Intégrer le profil cible versionné dans validator/writer/dialogue/documentation | 🟠 Élevée (renforce le chemin d'export de production) | 🟢 Faible pour le reliquat critique ; 🔴 matériel pour clore | Sonnet, moyen + matériel ensuite | Implémentation prête pour release : v2 est le profil par défaut pour Studio 4.3.3/firmware 4.0.9 et v1 reste figé et sélectionnable. Après #688–#690, revoir seulement l'état des preuves ; toute nouvelle sémantique exige une autre version du profil |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Épopée] Moteur de tonalité/niveaux de gris COLOR | 🟡 Moyen-élevé (fondation de la feuille de route laser, pas de bug actif) | 🔴 Élevé (4 tickets enfants restants : noyau→UI→intégration→recette) | – (épopée) | En cours : l'ADR #692 est approuvé ; vient ensuite le noyau #693 |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | Noyau sans Qt : histogramme/niveaux de gris/niveaux/gamma | 🟡 Moyen-élevé | 🟡 Moyen (étend `color_ops.py`, bien isolé et testable) | Sonnet, élevé | Prêt à démarrer : l'ADR #692 (PR #947) fournit le contrat de données ; implémenter et tester le noyau selon ses formules |
| [#694](https://github.com/NikolayDA/picture_helper/issues/694) | Aperçu en direct + interface pour histogramme/niveaux/gamma | 🟡 Moyenne | 🟡 Moyenne-élevée (UI Qt, garde debounce/génération comme l'aperçu de hauteur) | Sonnet, élevé | Bloqué – attend le noyau #693 |
| [#695](https://github.com/NikolayDA/picture_helper/issues/695) | Intégration calques/sélection/historique/projet | 🟡 Moyenne | 🟠 Élevée (nombreuses transitions d'état : annuler/rétablir, sélection, état modifié) | Opus, élevé | Bloqué – attend #693/#694 |
| [#696](https://github.com/NikolayDA/picture_helper/issues/696) | Recette performance/E2E/documentation/interface laser | 🟡 Moyenne (gate de clôture, pas une nouvelle fonctionnalité) | 🟠 Élevée (suite de benchmarks, E2E, documentation, contrat d'adaptateur) | Opus, élevé | Bloqué – ticket de clôture après #695 |
| [#882](https://github.com/NikolayDA/picture_helper/issues/882) | [Epic] BgRemover dans le Mac App Store | 🟡 Moyenne-haute (nouveau canal, pas un défaut actuel) | 🔴 Haute (licence, sandbox, packaging, store et gouvernance) | – (Epic) | Bloquée – décider #883 d'abord, en séparant licence Qt/code et provenance/droits non résolus du modèle |
| [#883](https://github.com/NikolayDA/picture_helper/issues/883) | [MAS] Stratégie de licence : PySide6 vs Riverbank et relicensing | 🟠 Haute (bloque tout travail technique MAS) | 🔴 Haute (décision licence/owner, port Qt possible, risque résiduel) | Opus, élevé + revue owner/juridique | Prête – ADR/décision et preuve de source, licence et redistribution du `u2net.onnx` exact, ou modèle de remplacement |
| [#884](https://github.com/NikolayDA/picture_helper/issues/884) | [MAS] Inscription Apple Developer Program | 🟠 Haute (bloque certificats et accès store) | 🟢 Faible (étape manuelle compte/paiement) | – (aucun agent ; account holder) | Bloquée – régler compte, inscription/2FA et renewal ; une app gratuite évite le Paid Apps Agreement, mais un trader peut devoir fournir un compte de paiement (#904) |
| [#885](https://github.com/NikolayDA/picture_helper/issues/885) | [MAS] Identités de signature, App ID et profil de provisioning | 🟠 Haute (prérequis du build signé) | 🟡 Moyenne (secrets owner et contrat bundle-ID/packaging) | – (aucun agent ; account holder/admin) | Bloquée – attend #884 ; créer certificats, App ID/profil explicites et figer le bundle ID |
| [#886](https://github.com/NikolayDA/picture_helper/issues/886) | [MAS] Définir et appliquer les entitlements App Sandbox | 🟠 Haute (prérequis obligatoire store/exécution) | 🟠 Haute (tous les Mach-O, packaging et preuve matérielle) | Opus, élevé | Bloquée – attend la décision #883 ; implémenter entitlements minimaux et tests artefact/matériel |
| [#887](https://github.com/NikolayDA/picture_helper/issues/887) | [MAS] Processus enfant d'inférence compatible sandbox | 🟠 Haute (la fonction IA centrale doit fonctionner) | 🔴 Haute (spawn/signature helper, règle deux clés, vraie sandbox) | Opus, élevé | Bloquée – attend #886 ; décider re-exec/helper et prouver le self-check IA sur matériel |
| [#888](https://github.com/NikolayDA/picture_helper/issues/888) | [MAS] Signets security-scoped pour fichiers et dossiers | 🟠 Haute (Récents et sauvegarde rapide cassent après redémarrage) | 🟠 Haute (autorisations persistantes, images/projets/dossiers, gating) | Opus, élevé | Bloquée – attend #886 ; implémenter le contrat de signets et tester le redémarrage sandboxed |
| [#889](https://github.com/NikolayDA/picture_helper/issues/889) | [MAS] Écritures sandbox-safe et export EufyMake | 🟠 Haute (sauvegarde/export et intégrité des données) | 🔴 Haute (atomicité multi-chemins et autorisations Powerbox) | Opus, élevé | Bloquée – attend #886 ; concevoir écritures/extensions/cible dans le grant et tester sur matériel |
| [#890](https://github.com/NikolayDA/picture_helper/issues/890) | [MAS] Cache du modèle IA dans le conteneur sandbox | 🟡 Moyenne (chemin modèle déterministe) | 🟡 Moyenne (contrat isolé et décision de migration) | Sonnet, élevé | Bloquée – attend #886 et se coordonne avec #893 ; fixer `U2NET_HOME` et décider la migration |
| [#891](https://github.com/NikolayDA/picture_helper/issues/891) | [MAS] Indicateur de canal et gating du contrôle des mises à jour | 🟠 Haute (règle 2.4.5, aucune auto-mise à jour) | 🟠 Moyenne-haute (indicateur central sur menu, réglages, workers, hooks) | Sonnet, élevé | Bloquée – attend #883 ; ajouter le contrat de canal et tester négativement réseau/UI MAS |
| [#892](https://github.com/NikolayDA/picture_helper/issues/892) | [MAS] Retirer AiInstallDialog et intégrer le backend IA | 🟠 Haute (aucune installation de code exécutable) | 🟡 Moyenne (gating et test de packaging contraignant) | Sonnet, élevé | Bloquée – attend #891 ; masquer dialogue/menu et prouver rembg/onnxruntime intégrés |
| [#893](https://github.com/NikolayDA/picture_helper/issues/893) | [MAS] Intégrer u2net ou le télécharger au premier lancement | 🟠 Haute (risque review et fonction IA) | 🟠 Haute (décision produit/review, packaging ou nouveau flux i18n) | Opus, élevé | Bloquée – avant la variante, prouver source/licence/redistribution via #883 ou changer de modèle ; puis #890/#891 et sandbox |
| [#894](https://github.com/NikolayDA/picture_helper/issues/894) | [MAS] Choisir le packaging Briefcase vs py2app | 🟠 Haute (détermine la viabilité technique) | 🟠 Haute (spike sandbox/signature/upload ouvert) | Opus, élevé | Bloquée – attend #883 ; tester Briefcase, repli py2app et consigner l'ADR |
| [#895](https://github.com/NikolayDA/picture_helper/issues/895) | [MAS] App onedir, signature inside-out et nettoyage Qt | 🟠 Haute (build exécutable central) | 🔴 Haute (binaires, Qt, provisioning, validation upload) | Opus, élevé | Bloquée – après #885/#886/#894, implémenter, choisir `AppTransaction` ou receipt fail-closed et valider sans erreurs ITMS |
| [#896](https://github.com/NikolayDA/picture_helper/issues/896) | [MAS] Info.plist et icônes complets | 🟡 Moyenne-haute (métadonnées et contrat plateforme) | 🟡 Moyenne (champs, architecture, assets déterministes) | Sonnet, élevé | Bloquée – attend #895 ; décider OS/architecture/types et ajouter les tests |
| [#897](https://github.com/NikolayDA/picture_helper/issues/897) | [MAS] PKG productbuild signé et upload Transporter | 🟠 Haute (artefact soumissible) | 🟠 Haute (seconde signature, automatisation, premier upload manuel) | Opus, élevé + account holder | Bloquée – attend #885/#895/#896 ; créer un PKG reproductible et consigner la livraison |
| [#898](https://github.com/NikolayDA/picture_helper/issues/898) | [MAS] CI, contrat six artefacts et scan PKG | 🟠 Haute (intégrité fail-closed) | 🔴 Haute (secrets, contrat, extracteur, malware/chemins) | Opus, élevé | Bloquée – attend #895/#897 ; étendre leg, contrat, scan payload et tests |
| [#899](https://github.com/NikolayDA/picture_helper/issues/899) | [MAS] Smokes sandboxed sur matériel réel | 🟠 Haute (preuve runtime contraignante) | 🔴 Haute (PKG, spawn IA, Powerbox, 3D, schéma) | Opus, élevé + matériel macOS | Bloquée – après #898, exécuter sur ARM64 self-hosted et inclure la preuve de téléchargement valide et, si reproductible, invalide |
| [#900](https://github.com/NikolayDA/picture_helper/issues/900) | [MAS] Bêta TestFlight macOS | 🟠 Haute (preuve précoce review/appareil externe) | 🟡 Moyenne (coordination ASC/testeur manuelle) | – (aucun agent ; titulaire/testeur) | Bloquée – attend #897/#901 ; tester IA, fichiers et 3D sur un autre appareil |
| [#901](https://github.com/NikolayDA/picture_helper/issues/901) | [MAS] Fiche ASC et métadonnées en six langues | 🟠 Haute (nom, listing et prérequis de soumission) | 🟠 Moyenne-haute (owner et six jeux localisés) | Sonnet, élevé + titulaire | Bloquée – attend #884/#885 ; réserver nom, versionner/charger textes, rating/storefronts |
| [#902](https://github.com/NikolayDA/picture_helper/issues/902) | [MAS] Captures Store 16:10 | 🟡 Moyenne-haute (matériel obligatoire) | 🟡 Moyenne (formats, alpha, décision langues) | Sonnet, élevé | Bloquée – attend le build #895 ; étendre l'automatisation et vérifier le jeu |
| [#903](https://github.com/NikolayDA/picture_helper/issues/903) | [MAS] Politique de confidentialité et App Privacy | 🟠 Haute (obligatoire dans le store et l'app) | 🟡 Moyenne (policy, hébergement, lien i18n, questionnaire) | Sonnet, élevé + owner | Bloquée – attend #891/#893 ; publier/lier et prouver « Data Not Collected » |
| [#904](https://github.com/NikolayDA/picture_helper/issues/904) | [MAS] Statut DSA UE, mentions légales et GPSR | 🟠 Haute (storefronts UE et obligations) | 🟠 Moyenne-haute (classement, vérification, risque juridique) | – (aucun agent ; owner/juridique) | Bloquée – après #884, documenter trader, contacts publics, compte de paiement si requis et DDG/GPSR avec owner/rappel |
| [#905](https://github.com/NikolayDA/picture_helper/issues/905) | [MAS] Étendre la gouvernance release | 🟠 Haute (évite un canal hors contrat fail-closed) | 🟠 Haute (runbook, checklist, contrat, policy, six changelogs) | Opus, élevé | Bloquée – accompagne #898/#899 ; porter contrats/tests à six artefacts |
| [#906](https://github.com/NikolayDA/picture_helper/issues/906) | [MAS] Première soumission et revue | 🟠 Haute (gate manuel de publication) | 🔴 Haute (dépendances, risques, communication Apple) | – (aucun agent ; release owner) | Bloquée – après #896/#897/#899/#901–#905, prévalider aussi le téléchargement, soumettre et consigner le résultat |
| [#907](https://github.com/NikolayDA/picture_helper/issues/907) | [MAS] Exploitation : renouvellement, mises à jour, canaux | 🟡 Moyenne-haute (disponibilité et séparation à long terme) | 🟡 Moyenne (runbook, responsabilités, rappels, matrice) | Opus, élevé + owner | Bloquée – préparer tôt, finaliser après #906 ; fixer routines renewal/update/web |
| [#914](https://github.com/NikolayDA/picture_helper/issues/914) | [Épopée] Processus de publication : runners, preuves automatisées, gel de main | 🟠 Élevé (exploitation ; implémentation presque finie) | 🟢 Faible (une preuve liée à un événement) | – (épopée) | Presque terminée : le premier dry-run planifié du 2026-09-03 s'est exécuté avec succès (run 33737226157) ; ne reste que la preuve E2E incluant #918 au prochain vrai release |
| [#918](https://github.com/NikolayDA/picture_helper/issues/918) | Réf de publication au lieu du gel de main (ADR + garde-fous fail-closed) | 🟠 Élevé (`main` reste fusionnable pendant une publication) | 🟢 Faible (code, documentation et ruleset en place) | – (aucun agent ; prochaine publication) | Bloqué (externe) : rouvert le 2026-08-31 après son contrôle de clôture ; la PR #936 et le ruleset actif 21941216 sont documentés, il ne manque qu'une exécution dont la recette post-publication a démarré de façon démontrable sur `release/vX.Y.Z` |
| [#939](https://github.com/NikolayDA/picture_helper/issues/939) | Exploitation : runners auto-hébergés (canal d'alerte du heartbeat) | 🟡 Moyen (canal d'exploitation, pas de code produit) | 🟢 Faible (observation seule) | – (aucun agent ; owner du dépôt) | Ouvert en permanence : ne pas fermer (`RUNNER_HEARTBEAT_ISSUE`) ; le FAIL du 2026-08-31 était le test prévu du canal d'alerte et l'étape de nettoyage est faite (exécution planifiée 33496675995 verte, x86_64 ignoré, Mac et Pi réussis) |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurer le quota OpenAI pour la vérification manuelle Codex Security | 🟢 Faible (ne bloque qu'un scan manuel optionnel) | 🟢 Faible (purement opérationnel, aucun code) | – (aucun agent ; propriétaire du dépôt : facturation) | Bloquée (externe) – la dernière exécution (29233060507, 2026-07-13) ne prouve aucun scan réussi ; facturation/quota toujours non résolu |
| [#1043](https://github.com/NikolayDA/picture_helper/issues/1043) | Réduire `docs/PROZESSE_UML.md` au chemin nominal | 🟡 Moyenne (773 lignes et 30 losanges ; duplique la matrice de reprise du runbook) | 🟡 Moyenne (quatre diagrammes plus les renvois vers le runbook et les ADR) | Sonnet, élevé | Bloqué : dernier lot de travail ; attend #1040, #1035, #1036, #1037 et #1041 |
| [#1042](https://github.com/NikolayDA/picture_helper/issues/1042) | Basculer les commandes d'analyse (`.claude/commands/analyze-*`) vers les tickets GitHub | 🟡 Moyenne (les résultats d'analyse arrivent là où l'inventaire ouvert est tenu) | 🟢 Faible (cinq fichiers de commande) | Sonnet, moyen | Bloqué : attend #1040 ; recommandé dans la même PR |
| [#1041](https://github.com/NikolayDA/picture_helper/issues/1041) | `make pr-ready` : détecter les devoirs de dérive à partir du diff | 🟡 Moyenne (remplace six losanges de décision manuels par une commande) | 🟠 Moyenne-élevée (nouveau script typé strictement, chemins séparés par NUL, renommages, matrice Python 3.10) | Opus, élevé | Bloqué : attend #1040 ; pertinent seulement après #1036 et #1037, car deux devoirs disparaissent alors |
| [#1040](https://github.com/NikolayDA/picture_helper/issues/1040) | Supprimer le triage en direct des recommandations (tableau, statut, workflow, gardiens) | 🟠 Élevée (le plus grand levier de l'épopée : 2 123 lignes de mécanique et plus aucune exécution rouge due à un changement d'état) | 🟡 Moyenne (six versions linguistiques, script, workflow, 42 fonctions de test dans trois fichiers, références résiduelles dans `TESTING.md` et `docs/PROZESSE_UML.md`) | Opus, élevé | Bloqué : attend #1033 ; recommandé de façon atomique avec #1042 |
| [#1039](https://github.com/NikolayDA/picture_helper/issues/1039) | Script owner pour les dispatches de publication au lieu de copier les run-IDs à la main | 🟡 Moyenne (travail manuel du flux de publication, aucun risque produit) | 🟡 Moyenne (résolution run-ID/artefacts via l'API, typage strict, test dépendant du réseau) | Sonnet, élevé | Reporté : l'épopée le place volontairement après la prochaine vraie publication ; d'ici là, la voie manuelle est la référence pour #914/#918 |
| [#1038](https://github.com/NikolayDA/picture_helper/issues/1038) | Filtres de chemins pour CodeQL, l'audit de dépendances et la vérification de licences sur les PR | 🟢 Faible (économise du temps CI, sans gain de qualité ni de risque) | 🟢 Faible (trois blocs `paths-ignore`) | Sonnet, moyen | Ready for PR : peu critique car aucune des trois exécutions n'est un check obligatoire (le seul est `Lightweight PR checks`) |
| [#1037](https://github.com/NikolayDA/picture_helper/issues/1037) | Politique de chemins : les chemins inconnus avertissent au lieu de bloquer | 🟠 Élevée (le gate tourne sur chaque PR ; 22 modifications de politique dans la fenêtre mesurée) | 🟡 Moyenne (version de politique 17→18, addendum à l'ADR, `prepare_release.py`, document de freeze, tests) | Opus, élevé | Ready for PR : les gates de publication restent intacts : la classification ne change pas, seul le blocage disparaît. Preuve via le prochain dry-run |
| [#1035](https://github.com/NikolayDA/picture_helper/issues/1035) | Réglages du dépôt : squash uniquement, suppression automatique des branches, un relecteur automatique | 🟡 Moyenne (moins de bruit de fusion et de relecture, aucun effet produit) | 🟢 Faible (réglages et configuration du connecteur, sans code) | – (pas d'agent ; owner du dépôt) | Prêt à démarrer (owner) : la comparaison en direct du 2026-09-09 confirme les quatre valeurs actuelles ; le réglage de relecture automatique de `chatgpt-codex-connector` n'est visible que dans la configuration du connecteur |
| [#1034](https://github.com/NikolayDA/picture_helper/issues/1034) | Formulaires de tickets pour l'application de bureau au lieu des modèles par défaut | 🟡 Moyenne (qualité des signalements ; les champs navigateur/smartphone ne conviennent pas à une application PyQt6) | 🟢 Faible (deux formulaires YAML plus `config.yml`) | Sonnet, moyen | Ready for PR : indépendant de #1033/#1040, insérable à tout moment |
| [#1033](https://github.com/NikolayDA/picture_helper/issues/1033) | Transférer le contenu de triage dans les tickets et introduire des étiquettes priorité/blocage | 🟠 Élevée (prérequis dur pour #1040 ; sinon les textes curés sont perdus) | 🟡 Moyenne (sans code, mais étiqueter tous les tickets ouverts et commenter 41 d'entre eux) | Sonnet, élevé | Prêt à démarrer : curation de tickets via l'API, pas une PR ; l'inventaire au 2026-09-09 est de 56 tickets ouverts, et non les 54 notés |
| [#1032](https://github.com/NikolayDA/picture_helper/issues/1032) | [Épopée] Allègement du processus : triage vers GitHub, moins de devoirs de dérive | 🟠 Élevée (28 des 156 commits de la branche principale dans la fenêtre mesurée ne sont que de l'entretien de triage) | 🔴 Élevée (onze lots de travail #1033–#1043 avec ordre et dépendances) | – (épopée) | En cours : ordre #1033 → #1040 (+#1042) → #1041/#1043 ; #1031 passe en priorité 0 avant |

### Recommandé ensuite

1. **#1031** (priorité 0) : le contrôle de provenance dans le hook SessionStart ; sans
   lui, un test par sous-processus au vert peut avoir vérifié du code ancien.
2. **#1044** et **#1045** : traités : la lacune de test #1004/#1005 dans
   `tests/test_preview3d_controller.py` et la référence `#1023` manquante dans six
   versions du CHANGELOG.
3. **Lancer v2.10.0** : le périmètre est dans `[Unreleased]` ; les étapes
   1/2 du runbook via `scripts/prepare_release.py 2.10.0`. Cette exécution referme aussi
   la preuve de bout en bout en attente pour #914 et #918.
4. **#1033 → #1040 (+#1042)** : démarrer l'allègement du processus ; #1034, #1035, #1037 et
   #1038 sont indépendants et insérables à tout moment (#1036 est réalisé).
5. **#693** (cœur sans Qt) : ADR #692 est approuvé ; viennent ensuite #694, #695 et #696.
6. **#883** : décider la licence Qt/code et prouver droits/provenance de `u2net.onnx`, ou
   choisir un modèle de remplacement clairement licencié.
7. Après validation du matériel et de l'appareil, effectuer les mesures physiques
   restantes de **#689** avec le reste de #687, #688 et #690 ; revoir ensuite l'état des
   preuves du profil v2. Le profil v1 reste figé, et toute sémantique nouvelle ou
   contradictoire exige une autre version du profil.

## Tours précédents

Protocoles détaillés depuis v2.2 : [RECOMMENDATIONS-2026-v2.2-v2.9.fr.md](../../history/RECOMMENDATIONS-2026-v2.2-v2.9.fr.md).

Constats historiques et journaux de travail (tours 1–5) : [RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
