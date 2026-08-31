[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-08-31, v2.9.0 publiée, inventaire ouvert entièrement audité)

**Audit quotidien du 2026-08-31 (état `551d055`) :** Les douze PR fusionnées
aujourd'hui (#927–#932, #935–#938, #940 et #941) et les issues fermées
(#918–#923, #933 et #934) ont été contrôlées : diffs de fusion complets,
corrections de revue et, quand ils existent, leurs tests de régression. La
référence de publication, le rapport de sécurité, le heartbeat/dry run, le
squelette de préparation et le préflight Qt/GL sont cohérents. La revue du
PR #942 a toutefois révélé cinq constats résiduels concrets dans les scripts
de processus – vérifiés et regroupés dans l'issue de suivi #943 (ligne infra).

**Contrôle périodique 2026-08-30 (delta après l'audit complet) :** Les 39
issues ouvertes entièrement vérifiées et contre-vérifiées contre `main` (état
produit `411d47c`) le 2026-08-29 sont inchangées ; HEAD `1d31f2a` n'ajoute
ensuite que de la documentation. Les descriptions corrigées de
#681/#882/#905/#906 et les lacunes de fixtures/cellules des tests réels
EufyMake #688–#690 restent donc bien visibles. Le nouveau #912 a été vérifié
séparément contre l'avis Qt et l'artefact épinglé : CVSS 4.0 vaut 6,3, non
6,8, et le `QtCore5Compat` vulnérable n'est pas livré. #912 a été corrigé et
clos « non affecté » ; aucun faux risque accepté ni nouveau constat 🔴.

**Addendum 2026-08-29 :** v2.9.0 est publiée. L'acceptation matérielle est verte
sur macOS arm64 et Linux arm64 avec de vrais moteurs de rendu GPU, le tag et la
publication sont vérifiés octet par octet contre le manifeste d'approbation, et
`PUBLIC-DOWNLOAD-01` comme `UPDATE-01` sont satisfaits. #881 est donc clôturé ;
les critères Linux x86_64 délibérément en pause restent visiblement `PENDING`.
#878 a été implémenté par la PR #908 ; cette synchronisation de clôture ferme le
ticket et le retire des six tableaux de triage actuels.

**Contrôle périodique 2026-08-28 :** La comparaison GitHub en direct ajoute
les issues ouvertes **#878**, **#881**, **#882** et les nouvelles sous-issues
MAS **#883–#907**, jusque-là absentes. À ce moment-là, #878 devait combler
l'écart entre l'interface standard/expert et le guide, avec captures et PDF
actuels ; l'implémentation a depuis été achevée par la PR #908. #881 est le
procès-verbal contraignant d'acceptation et de
publication de 2.9.0 ; le build candidat et le pré-contrôle sont verts, tandis
que l'acceptation matérielle et les validations humaines restent ouvertes.
#882 regroupe la voie Mac App Store comme epic bloqué ; #883–#907 concrétisent
ses phases licence, compte, sandbox, packaging, store et exploitation. La stratégie de licence doit
être décidée avant le travail technique. Aucun nouveau constat 🔴.

**EufyMake #681/#687–#691 :** les 31 fixtures, modèles de protocole et la gouvernance approuvée sont maintenant reflétés dans les tickets. #687 est à 16/18 critères ; seuls I-06 (dossier/manifeste) et la revue finale après les tests réels restent ouverts. Pour le chemin Spot UV séparé, l'hypothèse appuyée par le fabricant est noir = gloss et blanc = sans gloss. L'utilisation complète des 16 bits, la priorité `pHYs`, la conversion gris→mm et l'intensité gloss restent des questions matérielles de #688–#690.

Inchangé et fermé : **N1/N2/N4/N5/N6/N7/N8**, **O1–O8**, tout ce qui est terminé depuis le **2026-06-25**, les versions v2.7.0 à v2.8.0, ainsi que l'épopée #741 avec ses onze tickets enfants, l'épopée #805 avec #806–#811, #817 et #821 ; nouvellement clôturés depuis la dernière synchronisation : #836 (PR #844), #837 (PR #838), #839 (PR #846), #849 (PR #851), #841 (fermée par l'owner), #847 (PR #852), #866 (PR #870/#871), #869 (PR #873), #881 (fermée par l'owner) et #878 (PR #908/#910) (détails : Tours précédents).

En cours : une ligne par ticket dans le tableau de triage ci-dessous. Depuis #821, ni le compte ni les lignes ne sont maintenus à la main – `scripts/recommendations_live_check.py --write` met à jour les six versions depuis l'état en direct GitHub, tandis que les colonnes d'évaluation restent un travail éditorial.

## Tickets GitHub ouverts — Triage

| # | Titre | Pertinence | Complexité | Modèle recommandé (effort) | Prochaine étape |
|---|-------|------------|------------|------------------------------|------------------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Épopée] Profil cible EufyMake – valider Height/Gloss/mm-DPI | 🟠 Élevée (justesse de la principale cible d'export) | 🔴 Élevée (5 sous-tickets, matériel physique requis) | – (épopée) | Préparation #687 à 16/18 CA ; I-06 et revue finale restent, tandis que #691 attend les tests réels #688–#690 |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Inventaire des hypothèses, sources fabricant, matrice de tests | 🟠 Élevée (base contraignante pour #688–#691) | 🔴 Élevée (livrables propres terminés ; lacunes fixtures/cellules de #688–#690 ouvertes, le reste nécessite du matériel réel) | – (aucun agent ; matériel EufyMake réel requis) | Bloquée (externe) – 16/18 critères remplis ; restent I-06 dossier/manifeste et la revue finale après #688–#690 |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | Valider la profondeur de bits/sémantique HEIGHT sur matériel réel | 🟠 Élevée (affecte directement la hauteur du relief) | 🔴 Élevée (imprimante physique, gabarits, journal de mesures) | – (aucun agent ; matériel EufyMake réel requis) | Bloqué (externe) + travail préparatoire incomplet – les fixtures/modèles de protocole de #687 sont disponibles, mais Alpha/couverture n'a ni fixture ni cellule de test (toutes les fixtures COLOR sont opaques) et il manque une paire COLOR/HEIGHT de mêmes dimensions en pixels (I-02/I-08 confondus) ; à compléter avant le jour des tests |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | Valider le contrat mm/DPI, taille cible, positionnement | 🟠 Élevée (taille d'impression/registration) | 🔴 Élevée (mesures physiques, motifs de contrôle) | – (aucun agent ; matériel réel requis) | Bloqué (externe) + travail préparatoire incomplet – la taille de départ dérivée de `pHYs`/DPI dans la boîte de dialogue d'import de Studio reste non prouvée (N10, EM-F04) ; de plus, la cellule I-06 référence le manifeste des fixtures et non un véritable manifeste d'export, et les DPI non carrés ne sont ni testés ni exclus de façon motivée |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Valider la sémantique gloss/vernis | 🟡 Moyenne (gloss déjà marqué « expérimental » dans le code) | 🔴 Élevée (impressions physiques, consommation de matériau) | – (aucun agent ; matériel réel requis) | Bloqué (externe) + travail préparatoire incomplet – le travail préparatoire de #687 n'est que partiel : exactement une cellule gloss (I-10), aucune fixture Alpha/couverture, aucune dimension gloss divergente, gloss × HEIGHT non croisés |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Intégrer le profil cible versionné dans validator/writer/dialogue/documentation | 🟠 Élevée (renforce le chemin d'export de production) | 🟠 Élevée (transversal sur eufymake_export/_validate/_writer + UI) | Opus, élevé | Bloqué – attend #688–#690 |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Épopée] Moteur de tonalité/niveaux de gris COLOR | 🟡 Moyenne-élevée (fondation de la feuille de route laser, pas un bug actif) | 🔴 Élevée (5 sous-tickets, ADR→noyau→UI→intégration→recette) | – (épopée) | En cours – lancer d'abord #692 |
| [#692](https://github.com/NikolayDA/picture_helper/issues/692) | ADR + contrat de données pour tonalité/histogramme/niveaux de gris | 🟠 Élevée (fixe le contrat pour toute l'épopée) | 🟡 Moyenne (décision d'architecture, pas d'implémentation) | Opus, élevé | Prêt à démarrer |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | Noyau sans Qt : histogramme/niveaux de gris/niveaux/gamma | 🟡 Moyenne-élevée | 🟡 Moyenne (étend `color_ops.py`, bien isolé et testable) | Sonnet, élevé | Bloqué – attend l'ADR #692 |
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
| [#943](https://github.com/NikolayDA/picture_helper/issues/943) | Relecture de revue 2026-08-31 : cinq constats de robustesse dans les scripts de processus | 🟠 Haute (le heartbeat annonce PASS sans préparation prouvée) | 🟡 Moyenne (quatre scripts, correctifs isolés avec tests de régression) | Sonnet, élevé | Prête – conclusions du heartbeat d'abord, puis marqueur de dispatch, prepare_release (rétrogradation/ordre d'écriture) et OSError du scanner |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurer le quota OpenAI pour la vérification manuelle Codex Security | 🟢 Faible (ne bloque qu'un scan manuel optionnel) | 🟢 Faible (purement opérationnel, aucun code) | – (aucun agent ; propriétaire du dépôt : facturation) | Bloquée (externe) – la dernière exécution (29233060507, 2026-07-13) ne prouve aucun scan réussi ; facturation/quota toujours non résolu |

### Recommandé ensuite

1. **#692** (ADR) ouvre l'épopée COLOR #682.
2. Avant la prochaine session Studio/imprimante, combler d'abord les lacunes de fixtures/cellules
   documentées dans #688–#690 (alpha/couverture, une paire COLOR/HEIGHT de même taille, cellules
   gloss, un vrai manifeste d'export pour I-06) ; ensuite exécuter #687 (reste), #688, #689 et
   #690 en une seule session groupée.
3. **#883** (stratégie de licence MAS) décide la voie Mac App Store #882 : sans
   cette décision de l'owner, toute la chaîne #884–#907 reste bloquée.

## Tours précédents

Protocoles détaillés depuis v2.2 : [RECOMMENDATIONS-2026-v2.2-v2.9.fr.md](../../history/RECOMMENDATIONS-2026-v2.2-v2.9.fr.md).

Constats historiques et journaux de travail (tours 1–5) : [RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
