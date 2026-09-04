[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse de code et recommandations priorisées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | Bogues, plantages ou perte de données |
| 🟠 | Élevée | Impact net sur la fiabilité ou la maintenabilité |
| 🟡 | Moyenne | Amélioration utile de qualité, lisibilité ou testabilité |
| 🟢 | Faible | Peaufinage optionnel ou amélioration de processus |

## État actuel (2026-09-03, v2.9.0 publiée, inventaire ouvert entièrement audité)

**Audit quotidien 2026-09-02 (état `91b32b4`) :** les 42 tickets ouverts ont
été confrontés au code, aux fusions, aux commentaires et, pour l'épopée Mac App
Store, aux sources primaires actuelles. Les corrections de statut figurent dans
#681, #688, #691, #682/#693, #914/#918 et #949. Nouveaux constats : la licence
Apache-2.0 de l'artefact séparé `u2net.onnx` n'est pas établie (#883/#893),
Apple peut demander des coordonnées de compte de paiement aux traders même pour
une app gratuite (#884/#904), et #895/#899/#906 doivent décider et tester la
validation du téléchargement. Aucun défaut produit ni constat 🔴 nouveau.

**Réexamen du 2026-09-03 (état `e7c379d`) :** les nouvelles PR #955–#957 ont
été comparées aux points ouverts. La PR #956 a corrigé la référence de preuve
dans la v1 encore non publiée et ajouté des gardes snapshot/paquets ; l'ancien
point critique de #691 est donc résolu. #955 ne touche que la documentation des
tests et #957 les scripts de publication.

**Évaluation de publication : aucun candidat lancé pour l'instant.** Depuis
`v2.9.0` (2026-08-29), 34 commits sur la branche principale à l'état audité `e7c379d`. Avec la PR #953
(profil cible EufyMake versionné, HEIGHT par défaut en 16 bits, profil et DPI
X/Y dans le dialogue, provenance du manifeste), `[Unreleased]` contient pour la
première fois une entrée visible pour les utilisateurs ; le reste relève de
l'automatisation de publication, de la documentation et de la gouvernance. Que
**v2.10.0** sorte avec #953 seul ou avec le moteur de tonalité COLOR (#693/#694
de l'épopée #682, ADR #692) est une décision de l'owner. La PR #956 a corrigé la
référence avec une décision explicite de conserver v1 et des gardes golden/de
paquets. #691 n'ajoute donc plus de blocage de publication ; le gate normal reste
déterminant.

**EufyMake #681/#687–#691 :** les PR #948, #951–#953, #956 et #959–#961 sont fusionnées. Le schéma 5 contient 42 fixtures unitaires et sept vrais paquets d'export inchangés. Les 29 cellules d'import obligatoires sans impression sont terminées dans Studio 4.2.2. Outre HEIGHT natif 8/16 bits, le recadrage COLOR/HEIGHT et `Gloss Varnish`, le test prouve que des dimensions en pixels différentes avec le même ratio sont acceptées, tandis qu'un ratio HEIGHT différent est rejeté avec `Depth image ratio does not match the original image`. I-14 ajoute une paire bord/impulsion 256/128 pixels générée directement et sans préfiltrage ; les deux variantes ont passé le préflight d'import. I-09 (`.empf`) reste non bloquant. Seules les mesures physiques E1 de #688–#690 et la revue finale de #687 restent ouvertes.

Inchangé et fermé : **N1/N2/N4/N5/N6/N7/N8**, **O1–O8**, tout ce qui est terminé depuis le **2026-06-25**, les versions v2.7.0 à v2.9.0, ainsi que l'épopée #741 avec ses onze tickets enfants, l'épopée #805 avec #806–#811, #817 et #821 ; nouvellement clôturés depuis la dernière synchronisation : #943 (PR #944), #692 (PR #947), ainsi que la revue ANLEITUNG #963 avec #964–#966, #968 et #969 (PR #972) et #967 (PR #973), ainsi que l'audit de la suite de tests #949 (PR #977) et la garde du PDF #974 (PR #979) (détails : Tours précédents).

En cours : une ligne par ticket dans le tableau de triage ci-dessous. Depuis #821, ni le compte ni les lignes ne sont maintenus à la main – `scripts/recommendations_live_check.py --write` met à jour les six versions depuis l'état en direct GitHub, tandis que les colonnes d'évaluation restent un travail éditorial.

## Tickets GitHub ouverts — Triage

| # | Titre | Pertinence | Complexité | Modèle recommandé (effort) | Prochaine étape |
|---|-------|------------|------------|------------------------------|------------------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Épopée] Profil cible EufyMake – valider Height/Gloss/mm-DPI | 🟠 Élevée (justesse de la principale cible d'export) | 🔴 Élevée (5 sous-tickets, matériel physique requis) | – (épopée) | Intégration et 29 cellules obligatoires sans impression terminées ; I-09 non bloquant. Restent #688–#690 et la revue finale |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Inventaire des hypothèses, sources fabricant, matrice de tests | 🟠 Élevée (base contraignante pour #688–#691) | 🔴 Élevée (matériel du dépôt complet ; suite sur matériel réel) | – (aucun agent ; matériel EufyMake réel requis) | Bloquée (externe) – 17/18 critères et les 29 cellules d'import obligatoires terminés. Seule la revue après #688–#690 reste |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | Valider la profondeur de bits/sémantique HEIGHT sur matériel réel | 🟠 Élevée (affecte directement la hauteur du relief) | 🔴 Élevée (imprimante physique, fixtures, journal de mesures) | – (aucun agent ; matériel EufyMake réel requis) | Bloqué (externe) – y compris la paire I-14 directe de filtrage/normalisation, toutes les prévalidations sont terminées ; restent les mesures physiques de précision, filtrage, relief et mm |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | Valider le contrat mm/DPI, taille cible, positionnement | 🟠 Élevée (taille d'impression/registration) | 🔴 Élevée (mesures physiques, motifs de contrôle) | – (aucun agent ; matériel réel requis) | Bloqué (externe) – contrat Studio, recadrage et gestion du ratio HEIGHT compris, prouvé. Restent seulement recalage physique, mesures et tolérances |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Valider la sémantique gloss/vernis | 🟡 Moyenne (gloss déjà marqué « expérimental » dans le code) | 🔴 Élevée (impressions physiques, consommation de matériau) | – (aucun agent ; matériel réel requis) | Bloqué (externe) – mode natif `Gloss Varnish` prévalidé ; restent recalage par cellule, polarité, intensité et effet physique |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Intégrer le profil cible versionné dans validator/writer/dialogue/documentation | 🟠 Élevée (renforce le chemin d'export de production) | 🟢 Faible pour le reliquat critique ; 🔴 matériel pour clore | Sonnet, moyen + matériel ensuite | Implémentation prête pour release – #953 intègre v1 et #956 corrige la référence avec décision v1 et gardes ; seule la promotion après #688–#690 reste |
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
| [#914](https://github.com/NikolayDA/picture_helper/issues/914) | [Épopée] Processus de publication : runners, preuves automatisées, gel de main | 🟠 Élevé (exploitation ; implémentation presque finie) | 🟢 Faible (deux preuves liées au temps/événement) | – (épopée) | Presque terminée : restent le premier dry-run planifié le 2026-09-03 04:40 UTC et la preuve E2E incluant #918 au prochain vrai release |
| [#918](https://github.com/NikolayDA/picture_helper/issues/918) | Réf de publication au lieu du gel de main (ADR + garde-fous fail-closed) | 🟠 Élevé (`main` reste fusionnable pendant une publication) | 🟢 Faible (code, documentation et ruleset en place) | – (aucun agent ; prochaine publication) | Bloqué (externe) : rouvert le 2026-08-31 après son contrôle de clôture ; la PR #936 et le ruleset actif 21941216 sont documentés, il ne manque qu'une exécution dont la recette post-publication a démarré de façon démontrable sur `release/vX.Y.Z` |
| [#939](https://github.com/NikolayDA/picture_helper/issues/939) | Exploitation : runners auto-hébergés (canal d'alerte du heartbeat) | 🟡 Moyen (canal d'exploitation, pas de code produit) | 🟢 Faible (observation seule) | – (aucun agent ; owner du dépôt) | Ouvert en permanence : ne pas fermer (`RUNNER_HEARTBEAT_ISSUE`) ; le FAIL du 2026-08-31 était le test prévu du canal d'alerte et l'étape de nettoyage est faite (exécution planifiée 33496675995 verte, x86_64 ignoré, Mac et Pi réussis) |
| [#975](https://github.com/NikolayDA/picture_helper/issues/975) | eufymake : régénérer et relier les porte-étiquettes 04 et 10 | 🟡 Moyenne (deux champs de test sans étiquette sur le carton ; pas de blocage pour les onze autres) | 🟢 Faible (le générateur est déjà corrigé ; seul le suivi des données reste) | – (pas d'agent ; nécessite macOS avec Arial) | Bloqué (externe) – sous Linux, Liberation Sans produit d'autres octets ; régénérer, relier dans Studio, mettre à jour `projects.json` |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurer le quota OpenAI pour la vérification manuelle Codex Security | 🟢 Faible (ne bloque qu'un scan manuel optionnel) | 🟢 Faible (purement opérationnel, aucun code) | – (aucun agent ; propriétaire du dépôt : facturation) | Bloquée (externe) – la dernière exécution (29233060507, 2026-07-13) ne prouve aucun scan réussi ; facturation/quota toujours non résolu |
| [#958](https://github.com/NikolayDA/picture_helper/issues/958) | Heartbeat : escalade hors ligne à 7/14/21 jours (e-mails, retrait) et garde des délais | 🟡 Moyenne (exploitation et notifications des runners, pas un défaut produit) | 🟠 Élevée (historique, étapes idempotentes, permissions workflow, tests et documentation) | Opus, élevé + décision owner | Décision requise – fixer E1 commentaires quotidiens, E2 retrait automatique/manuel et E3 jours des étapes ; puis implémenter fail-safe et valider via un ticket de test |

### Recommandé ensuite

1. **#693** : ADR #692 est approuvé ; viennent ensuite #694, #695 et #696.
2. **#949** : faire les quatre changements puis remesurer avec plateforme et dépendances optionnelles.
3. **#883** : décider la licence Qt/code et prouver droits/provenance de `u2net.onnx`, ou choisir
   un modèle de remplacement clairement licencié.
4. Après validation du matériel et de l'appareil, effectuer les mesures physiques restantes de
   **#689** avec le reste de #687, #688 et #690 ; les chemins natifs HEIGHT/Gloss et I-08 sont prévalidés. Ensuite clore #691 :
   promouvoir le profil v1 ou créer v2 si les résultats le contredisent.

## Tours précédents

Protocoles détaillés depuis v2.2 : [RECOMMENDATIONS-2026-v2.2-v2.9.fr.md](../../history/RECOMMENDATIONS-2026-v2.2-v2.9.fr.md).

Constats historiques et journaux de travail (tours 1–5) : [RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).
