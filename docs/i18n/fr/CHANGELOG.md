[Deutsch](../../../CHANGELOG.md) · [English](../en/CHANGELOG.md) · [Español](../es/CHANGELOG.md) · **Français** · [Українська](../uk/CHANGELOG.md) · [简体中文](../zh/CHANGELOG.md)

# Changelog

Toutes les modifications notables de BgRemover sont
documentées dans ce fichier. Le format s'inspire de
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/) ; le projet
suit le [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

## [2.6.0] – 2026-07-15

### Ajouté

- **Logique centrale de vérification des mises à jour (#564, partie de
  l'Epic #563).** Nouveau module sans Qt `app_update.py` :
  `check_for_update(current_version)` interroge l'API GitHub Releases
  (uniquement `urllib.request` de la bibliothèque standard, sans téléchargement
  d'actif) et renvoie un `UpdateCheckResult` structuré (`UP_TO_DATE` /
  `UPDATE_AVAILABLE` / `CHECK_FAILED`) ; toute erreur réseau/d'analyse est
  renvoyée sous forme de `CHECK_FAILED` avec un message lisible, jamais sous
  forme d'exception.
- **Détection de l'état du modèle d'IA (#568, partie de l'Epic #563).**
  Nouveau module sans Qt `ai_model_status.py` : `get_model_status()` détecte
  si le modèle par défaut de rembg (`u2net.onnx`) est déjà présent dans le
  répertoire de cache (`U2NET_HOME` ou `~/.u2net`) — sans importer `rembg` et
  sans déclencher de téléchargement.
- **Entrée de menu « Rechercher des mises à jour… » (#565, partie de l'Epic
  #563).** La vérification manuelle des mises à jour dans le menu Outils
  s'exécute sans bloquer dans son propre thread de travail
  (`UpdateCheckWorker`, analogue au warmup rembg existant) et affiche une
  boîte de dialogue traduite adaptée au résultat : version actuelle, nouvelle
  version avec un bouton « Ouvrir la page de la version », ou un message
  d'erreur sans trace technique. Une protection contre la réentrance empêche
  une seconde vérification parallèle.
- **Entrée de menu « Gérer le modèle d'IA… » (#569, partie de l'Epic #563).**
  Nouvelle boîte de dialogue `ai_model_dialog.py` affichant l'état du cache du
  modèle rembg (Téléchargé/Non téléchargé/Fonction d'IA indisponible) avec des
  boutons télécharger/réessayer et annuler ainsi qu'un indicateur d'activité ;
  l'entrée de menu est désactivée sans rembg installé (avec une infobulle
  explicative).
- **Vérification automatique des mises à jour au démarrage (#566, partie de
  l'Epic #563).** Nouveau réglage « Rechercher automatiquement des mises à
  jour au démarrage » (désactivé **par défaut** – opt-in explicite) dans la
  boîte de dialogue des réglages. Une fois activé, une vérification
  silencieuse s'exécute peu après le démarrage ; `CHECK_FAILED` reste
  totalement silencieux, seul `UPDATE_AVAILABLE` affiche un indice discret et
  cliquable dans la barre d'état qui ouvre la même boîte de dialogue de
  résultat que la vérification manuelle – sans nouvelle requête réseau.
- **Téléchargement du modèle d'IA : véritable connexion avec le mécanisme de
  warmup (#570, partie de l'Epic #563).** Le bouton de téléchargement dans la
  boîte de dialogue du modèle d'IA se rattache désormais à un warmup de
  démarrage déjà en cours au lieu de démarrer un second processus/thread
  (`WorkerController.start_warmup` prend désormais en charge plusieurs
  observateurs) ; la barre d'état et la boîte de dialogue n'affichent jamais
  d'états contradictoires. Le bouton d'annulation utilise une nouvelle
  annulation coopérative (`RembgWarmupWorker.cancel()`, analogue à
  `AIWorker`/`FloodFillWorker`) : le processus enfant d'inférence est arrêté
  proprement, sans signaler à tort l'annulation comme un succès ou un échec.
- **Élément de menu « Installer la suppression d'arrière-plan par IA… ».** Le
  nouveau dialogue `ai_install_dialog.py` affiche, pour les utilisateur·rice·s
  sans backend rembg installé (p. ex. après l'installation minimale sur
  Raspberry Pi), la commande appropriée pour l'installer, avec un bouton de
  copie dans le presse-papiers – spécifique à la plateforme (Linux : recette
  venv/pip ; macOS : `create_BgRemover_app.sh`, car une venv dédiée au
  bundle d'application y est maintenue) et avec un avertissement lorsque la
  version de Python active est inférieure au 3.11 requis par
  rembg/onnxruntime. Volontairement aucune tentative d'installation
  automatique depuis l'application : PEP 668 bloque de toute façon `pip`
  vers le Python système, et un paquet fraîchement installé ne serait
  visible dans le processus en cours qu'après un redémarrage.

### Modifié

- **Épinglage de setuptools relevé contre une nouvelle CVE.** `setuptools`
  est relevé dans `pyproject.toml` (`[build-system]`) et
  `requirements/constraints.txt` de `78.1.1` à `>=83.0.0` (`==83.0.0` dans
  `constraints.txt`) – corrige `PYSEC-2026-3447` (contournement de
  normalisation Unicode dans les motifs d'exclusion de `MANIFEST.in`, macOS
  APFS/HFS+), en plus des CVE-2024-6345/CVE-2025-47273 déjà épinglées.

### Corrigé

- **Erreur de préchauffage visible dans la boîte de dialogue du modèle d'IA
  (#575).** Si le préchauffage automatique au démarrage échoue avec une
  erreur concrète du processus enfant d'inférence (p. ex. un
  `ModuleNotFoundError` dû à une discordance de venv/interpréteur, ou une
  coupure de connexion/`EOFError`), « Gérer le modèle d'IA… » affiche
  désormais la cause technique dès la prochaine ouverture, au lieu du simple
  message neutre « Non téléchargé » sans aucun indice sur le problème –
  auparavant l'erreur n'apparaissait que dans le journal.
- **« Gérer le modèle d'IA… » n'est plus muet sans rembg (#575).** Sans
  rembg installé, l'entrée de menu était silencieusement désactivée – et
  comme Qt n'affiche pas les infobulles dans les menus par défaut, un clic
  ressemblait à un bug (« ne fait rien ») sans aucune explication. L'entrée
  est désormais toujours active : la boîte de dialogue affiche elle-même
  l'état « Fonction d'IA indisponible » et nomme en plus l'environnement
  Python actif (`sys.executable`) – un lancement avec le mauvais
  interpréteur (p. ex. Python système au lieu de la venv contenant rembg)
  est ainsi immédiatement reconnaissable.

## [2.5.0] – 2026-07-11

### Ajouté

- **Interface d'exécution en six langues (i18n de la refonte, #430).** La table
  complète des chaînes d'exécution est désormais également maintenue en
  espagnol, français, ukrainien et chinois simplifié – y compris les nouvelles
  chaînes du flux de travail de la refonte (libellés d'étapes, titres et
  descriptions d'étapes, titres de cartes, navigation). Les langues
  apparaissent automatiquement dans le sélecteur de langue du dialogue des
  réglages ; l'allemand reste la langue de repli garantie et les tests de
  parité i18n (égalité des clés et des espaces réservés, un test de fumée de
  l'interface par langue) couvrent les six langues (partie de l'épopée #425).
- **Thème clair et jetons de design (refonte de l'interface, épopée #424).** Un
  système de thèmes centralisé et basé sur des jetons (une `Palette` avec un
  schéma clair et un schéma sombre) colore toute l'interface via une `QPalette` et
  une feuille de style à l'échelle de l'application. « Affichage → Thème clair »
  permet de basculer entre clair et sombre à l'exécution ; le choix est mémorisé
  dans les réglages et appliqué au démarrage. Accessibilité : chaque élément
  interactif affiche un anneau de focus visible (y compris après un changement de
  thème), la barre d'étapes se pilote au clavier (Tab + Entrée/Espace), toutes les
  commandes respectent des tailles de cible minimales et une matrice de contraste
  WCAG AA protège durablement les deux schémas de couleurs (#427–#429, #441).
- **Flux guidé avec inspecteur en cartes (refonte de l'interface, épopées #413/#418).**
  La colonne de droite guide désormais l'édition en six étapes claires (Ouvrir ·
  Détourer · Ajuster · Forme et dimensions · Relief et calques · Exporter) : une barre
  d'étapes en haut, un inspecteur avec en-tête d'étape et une navigation fixe
  Précédent/Suivant, ainsi qu'une barre d'outils contextuelle (outils de sélection
  uniquement à l'étape de détourage). Les étapes 2 à 6 restent verrouillées tant
  qu'aucune image n'est chargée ; le chargement passe automatiquement à l'étape de
  détourage. Le câblage des actions existant est inchangé (#419–#422, #415–#417).

- **Aperçu 2D combiné sélectionnable par l'utilisateur (fin de phase 1).** Le
  canevas propose désormais les modes explicites Couleur, Relief sur couleur,
  Hauteur (niveaux de gris), Gloss et Combiné, indépendants du calque actif. Un
  cache limité à une image est invalidé par révision du contenu, mode et réglages
  d'affichage ; le menu Affichage et le nouvel onglet Aperçu restent synchronisés,
  tandis que l'intensité du relief et la visibilité du gloss agissent en direct.
  Un avis clair et une matrice de tests mode×calque préservent le contrat #363 :
  « Enregistrer l'image » exporte toujours uniquement le composite COLOR (#387,
  #388 ; achève l'epic #384).
- **Moteurs de relief et de gloss sans Qt pour l'aperçu 2D combiné.** Les nouveaux
  modules strictement typés `bgremover/relief_preview.py` et
  `bgremover/gloss_preview.py` produisent un hillshade directionnel déterministe à
  partir de `HeightField` (équivalent en 8/16 bits) et un reflet de gloss visible.
  Tous deux composent leur effet sur un motif couleur RGBA après validation de la
  taille, conservent son canal alpha bit pour bit et offrent de vrais no-op neutres ;
  des tests purs de pixels/limites couvrent direction, couverture, intensité et alpha
  (#385, #386).
- **Contrôle pré-export lors d'un enregistrement normal.** « Enregistrer »/
  « Enregistrer sous… » exécute désormais le contrôle général (#379) sur le projet
  avant l'écriture et affiche les constats comme le flux EufyMake : les **erreurs
  bloquent** l'enregistrement avec un message clair (aucun appel d'écriture), les
  **avertissements** exigent une confirmation délibérée. L'annulation est sans effet
  de bord (pas d'écriture, pas de fichiers temporaires). La transparence partielle
  n'est volontairement **pas** signalée : c'est le résultat normal d'un outil de
  détourage. Tous les textes en de/en ; l'affichage des constats réutilise la même
  logique `format_finding` que l'affichage EufyMake (#380). Cela achève l'epic #375
  (sortie aux dimensions exactes + contrôles d'export).
- **Mode mm/PPP dans le dialogue « Redimensionner… » + contrôle de surface
  d'impression.** Le dialogue de redimensionnement propose désormais deux unités :
  pixels (comme avant) et **millimètres + PPP**. En mode mm, on saisit largeur/hauteur
  en mm et le PPP, la **taille en pixels** résultante s'affiche en direct via la
  géométrie partagée (#376) et le rapport d'aspect peut être verrouillé. Un **contrôle
  de surface d'impression** compare le motif à un support cible sélectionnable
  (A3/A4/A5/Letter) et avertit clairement en cas de dépassement. À l'application, la
  taille physique cible (mm) est ancrée dans le projet via les setters de
  `project_model` (canonique ; le PPP découle de mm + taille en pixels) et survit au
  cycle `.bgrproj` ; le rééchantillonnage reste purement en pixels (`Project.resize`).
  Tous les textes en de/en (#377).
- **Contrôle pré-export général et sans Qt (cadre partagé).** Un nouveau module
  strictement typé `bgremover/export_checks.py` hisse le cadre de constats de
  `eufymake_validate` (#354) sur une base partagée : un contrat générique
  `Finding`/`CheckCode`/`Severity` avec des codes stables, des clés i18n
  (`export.checks.*`, de/en) et un tri déterministe. Il implémente des contrôles
  indépendants du format pour les dimensions (px > 0, limite de mégapixels), la
  plausibilité de la résolution (PPP de #376), l'espace colorimétrique (RGBA attendu),
  la transparence (entièrement transparent / alpha partiel inattendu), la sortie vide
  et le contrôle de surface d'impression/marge (taille physique vs support cible).
  `eufymake_validate` s'appuie désormais sur cette base partagée (réexporte `Severity`/
  `has_blocking_errors`/`split_findings`) ; les codes spécifiques à EufyMake y restent
  et tous les tests EufyMake antérieurs restent verts sans modification (#379).
- **Ancrer le PPP/la résolution dans les sorties.** Lors de l'enregistrement
  d'images matricielles, `image_ops.save_image_file` intègre désormais en option le
  PPP du projet (#376) sous forme de métadonnées pures : PNG (`pHYs`), JPEG (densité
  JFIF) et TIFF (`Resolution`/`ResolutionUnit`) ; le WebP ne porte pas de PPP. Le
  chemin d'enregistrement du canevas transmet la résolution déduite de la taille
  physique + la taille en pixels ; sans PPP de projet, le comportement est inchangé et
  les pixels/alpha ne sont jamais modifiés (l'export bit à bit d'une seule couche
  COLOR est préservé). L'export EufyMake alimente désormais son `ExportTarget` à partir
  des getters mm/PPP du modèle plutôt que d'une dérivation locale (#378).
- **mm/PPP comme propriété du projet + géométrie partagée sans Qt.** Un nouveau
  module strictement typé `bgremover/units.py` regroupe en un seul endroit toute la
  mathématique px↔mm↔PPP : à partir de deux grandeurs connues, il déduit la troisième de
  façon déterministe (`MM_PER_INCH = 25,4`), valide les entrées et signale les valeurs
  invalides (≤ 0, non numériques, forme incorrecte) par des erreurs structurées
  `UnitsError` au lieu de les corriger silencieusement. `Project` reçoit des setters/getters
  validés pour la taille physique cible (mm) et la résolution (PPP) : la taille physique est
  la source canonique, les PPP en découlent avec la taille en pixels (sans dérive) et
  survivent au cycle enregistrement/chargement `.bgrproj` à valeur égale. L'export EufyMake
  utilise désormais la même géométrie (`_derive_physical_size`/`_derive_dpi`/`MM_PER_INCH`)
  sans changement de comportement (#376).
- **Import EufyMake Studio : menu, dialogue, affichage des constats et réglages.**
  Une nouvelle action de menu « Exporter des assets pour EufyMake Studio… » (menu
  Projet, Ctrl+Alt+E) ouvre un dialogue Qt (`eufymake_export_dialog.py`) : le motif
  couleur est obligatoire, la carte de hauteur/le masque de brillance ne sont
  sélectionnables que si le projet le permet (brillance marquée expérimentale),
  profondeur de bits 8/16 (16 marquée non confirmée), taille cible/physique dérivée
  et un **affichage des constats en direct** issu du contrôle (#354) : les erreurs
  bloquent, les avertissements exigent une confirmation explicite. L’écriture est
  atomique via `write_export` ; l’annulation/les erreurs ne modifient ni le projet
  ni la cible, et une confirmation d’écrasement protège les dossiers existants. Le
  dialogue de succès indique le chemin et les étapes suivantes dans Studio
  (importer, positionner, attribuer mode d’encre/calque, enregistrer en `.empf`).
  Le dossier d’export et les options générales sont mémorisés dans les QSettings
  versionnés (schéma v2, clés additives avec migration).
  `build_export_plan`/`write_export` ont reçu `optional_roles`/`bit_depth` pour la
  sélection de l’IU. Toutes les chaînes en de/en ; l’IU parle toujours d’assets
  d’import, jamais d’un projet `.empf` fini (#355).
- **Exportation EufyMake : rendu, écriture atomique et contrôle de cohérence
  (sans Qt).** Deux nouveaux modules strictement typés s’appuient sur le plan de
  #352 : `bgremover/eufymake_validate.py` (`validate_export`) collecte des constats
  structurés triés de façon déterministe (code stable, `error`/`warning`, rôle, clé
  i18n) ; les erreurs dures (motif couleur manquant, rôle sélectionné manquant,
  taille incohérente, paramètres cibles invalides) bloquent, tandis que les
  avertissements (données de hauteur/brillance vides/constantes, 16 bits non
  confirmé, brillance en tant qu’asset auxiliaire de mode d’encre, taille physique
  sans contrat fabricant) n’autorisent l’export qu’après confirmation, tous les
  messages en de/en (#354). `bgremover/eufymake_writer.py`
  (`render_export`/`write_export`) rend le motif couleur (= composite, RGBA
  préservant l’alpha), la carte de hauteur (niveaux de gris clair = haut, 8/16 bits)
  et le masque de brillance facultatif à la taille cible avec `manifest.json`, et
  les écrit de manière **atomique** (rendu dans un répertoire temporaire,
  publication en une seule étape `os.replace` ; un échec préserve une cible
  existante, les données temporaires sont nettoyées ; comportement de collision via
  `overwrite`). Pas de `.empf` natif (#353).
- **Exportation EufyMake : modèle de données et planification (sans Qt).** Nouveau
  module strictement typé `bgremover/eufymake_export.py` :
  `build_export_plan(project)` associe de façon déterministe les rôles de calque à
  un `ExportPlan` d’`ExportAsset` — le motif couleur en PNG RGBA est **obligatoire**
  (rôle `COLOR_MOTIF` explicite ou composite COLOR), tandis que la carte de hauteur
  et le masque de brillance sont des PNG niveaux de gris **facultatifs** (brillance
  expérimentale). Les noms de fichier, la version de profil et les valeurs par
  défaut sont des **conventions BgRemover** documentées (et non une spécification
  officielle EufyMake) ; la sémantique de hauteur **clair = haut** est fixée dans le
  contrat de types, tandis que les questions ouvertes de profondeur de bits/brillance
  et l’absence délibérée d’un `.empf` natif restent explicitement signalées. La
  taille physique, les DPI et la profondeur de bits sont dérivés de façon
  reproductible des métadonnées du projet ou des valeurs par défaut ; les valeurs
  invalides produisent des erreurs structurées. Un modèle de données pur, sans
  rendu/écriture/IU (suite dans #353–#355) (#352).
- **ADR du paquet d’exportation EufyMake.** Une nouvelle décision d’architecture
  documente la convention de paquet orientée import pour #352/#351 : motif
  couleur en PNG RGBA, carte de hauteur en PNG niveaux de gris avec clair = haut,
  masque de brillance facultatif et questions ouvertes sur le 16 bits, la
  sémantique de la brillance et le format natif `.empf`.
- **Finition du détourage : lissage des bords / fondu.** Nouvelle fonction sans Qt
  et strictement typée `feather_alpha(img, radius, *, mask=None)` dans
  `image_ops.py` : flou gaussien **du seul canal alpha** (RVB préservé bit à bit ;
  `radius = 0` = no-op ; les calques entièrement opaques restent sans artefact au
  bord). Le canevas l’intègre comme `feather_active_edges(radius)` sur le calque
  actif, **limitée à la sélection** (si présente) et **annulable/rétablissable**
  via le chemin d’application existant. IU : curseur de rayon + bouton « Lisser le
  bord » dans l’onglet Arrière-plan (à côté du détourage). Toutes les nouvelles
  chaînes en parité de/en (#361).
- **Correction des couleurs du calque couleur actif (luminosité/contraste/saturation).**
  Nouveau module sans Qt et strictement typé `bgremover/color_ops.py` avec
  `adjust_color` (Pillow `ImageEnhance`, **canal alpha exactement préservé**,
  valeurs neutres = no-op identique au bit près), une primitive de tonalité
  réutilisable pour le moteur partagé ultérieur (rang #6). Le canevas fournit un
  **aperçu en direct** générique (`preview_color_op`/`cancel_color_preview`,
  transitoire sans modifier le modèle ; l’aperçu est prioritaire dans
  `_refresh_image`) et une validation annulable/rétablissable (`apply_color_op`)
  sur le calque **COLOR** actif (sans effet sur les calques non COLOR). Un nouvel
  onglet « Ajuster » dans le panneau de droite propose des curseurs
  luminosité/contraste/saturation avec **Réinitialiser** et **Appliquer**. Toutes
  les nouvelles chaînes en parité de/en (#360).
- **Redimensionner / mettre à l’échelle vers une taille cible (rééchantillonnage).**
  Nouvelles opérations d’image sans Qt et strictement typées
  `resize_image`/`resized_size` dans `image_ops.py` (sans effet si la taille est
  identique ; assistant de rapport d’aspect/garde mégapixels) et `Project.resize`
  dans `project_model.py`, qui rééchantillonne **toutes les couches** et la taille
  du canevas de façon cohérente (COLOR selon la méthode choisie, HEIGHT sans perte
  via la représentation de hauteur ; le composite couleur reste aligné). Le
  canevas l’intègre avec annuler/rétablir et une garde mégapixels (refus clair et
  traduit en cas de dépassement, sans allouer le tampon surdimensionné) ; une
  nouvelle boîte de dialogue « Redimensionner… » (largeur/hauteur en px,
  **lier le rapport d’aspect**, méthode de rééchantillonnage) est accessible via le
  menu « Édition » (Ctrl+R) et l’onglet Transformation. La taille physique
  réservée (`META_PHYSICAL_SIZE_MM`) reste intacte (mm/PPP est réservé aux rangs
  ultérieurs). Toutes les nouvelles chaînes en parité de/en (#359).
- **Représentation de hauteur et visualisation 2D (fondation height-map).**
  Nouveau module sans Qt et strictement typé `bgremover/height_map.py` :
  conversion sans perte hauteur ↔ tableau en niveaux de gris (`HeightField`,
  convention `R==G==B==hauteur`, `A==couverture`), normalisation de valeurs
  arbitraires sur la plage de hauteur et validation de la taille du canevas,
  stocké en interne en `uint16` et donc extensible à 16 bits (`max_value`). Le
  canevas affiche désormais un **calque HEIGHT actif** en niveaux de gris ; le
  composite couleur reste inchangé (parité) (#345, #344).
- **Générer et importer une carte de hauteur (sans IA).**
  `bgremover/height_map.py` gagne `generate_from_image` : construit de manière
  **déterministe** une carte de hauteur à partir d'une image couleur
  (pondération des canaux/luminance → courbe tonale → gamma → inversion). Le
  canevas le câble, avec annuler/rétablir, en tant que nouveau calque HEIGHT
  actif avec le rôle `HEIGHT_MAP` : `generate_height_map` depuis le calque
  COLOR actif ou le composite, et `import_height_map` charge un fichier en
  niveaux de gris validé via `open_validated_image` (protection
  format/taille de fichier/mégapixels, message d'erreur clair et traduit) et
  le met à l'échelle de la taille du canevas (#346, #344).
- **Éditeur de carte de hauteur (éclaircir/assombrir/définir/inverser).**
  `bgremover/height_map.py` gagne des opérations de hauteur sans perte et
  conscientes de la sélection (`adjust_height`, `set_height`, `invert_height` ;
  bornées, entrée préservée). Le canevas les câble au **calque HEIGHT actif**
  (`lighten_/darken_/set_/invert_active_height`) : elles respectent une
  sélection existante (sinon globales), sont annulables/rétablissables et ne
  font délibérément rien sur les calques COLOR (aucune régression dans
  l'édition couleur). Réutilisation maximale des chemins
  pinceau/sélection/historique existants (#347, #344).
- **Optimisation de carte de hauteur (`height_ops`).** Nouveau module sans Qt,
  strictement typé et compatible 16 bits `bgremover/height_ops.py` avec des
  opérations pures et déterministes sur les champs de hauteur : tonalité
  (`levels`/`gamma`), lissage (`gaussian_blur` séparable, `median_blur`
  préservant les contours – numpy pur, sans nouvelle dépendance), `threshold`,
  réduction de niveaux (`quantize`) et bornage de plage de hauteur
  (`clamp_range`) – les mêmes primitives de tonalité/niveaux de gris que
  partagent les rangs ultérieurs. Le canevas ajoute un **aperçu en direct**
  générique (`preview_height_op`/`cancel_height_preview`, transitoire sans
  modifier le modèle) et un commit annulable/rétablissable (`apply_height_op`)
  sur le calque HEIGHT actif (#348, #344).
- **Espace de travail carte de hauteur utilisable (UI) – epic terminé.** Nouvel
  onglet « Hauteur » dans le panneau de droite (`height_map_panel.py`) :
  **générer** une carte de hauteur depuis l'image ou **importer** un niveau de
  gris, l'**éditer** avec éclaircir/assombrir/définir/inverser et l'**optimiser**
  via niveaux/gamma/lissage (gaussien, médian)/seuil/paliers/plage avec un aperçu
  en direct. Éditer et optimiser sont **contextuels au mode** – actifs uniquement
  quand le calque actif est un calque HEIGHT ou porte le rôle `HEIGHT_MAP` ;
  l'édition couleur reste inchangée. Tout le flux (générer → peindre → optimiser →
  inverser → enregistrer/recharger sans perte dans `.bgrproj`) est désormais
  utilisable depuis l'UI. Toutes les nouvelles chaînes via `i18n.py` (parité
  de/en) ; termine l'epic carte de hauteur (#349, #344).
- **Modèle de données projet/calques sans Qt.** Nouveau module
  `bgremover/project_model.py`, strictement typé, avec `Project` et `Layer`
  (`LayerKind` couleur/hauteur/gloss/générique, rôles uniques à l'échelle du
  projet) comme fondation de l'epic des calques : calques ordonnés, exactement
  un calque actif, opérations pures (ajout/suppression/réordonnancement/
  duplication/renommage, visibilité/opacité/verrouillage/rôles) et un composite
  alpha des calques de couleur visibles — sans aucun couplage Qt, rendu,
  persistance ou historique (#330, #329).
- **Historique annuler/rétablir conscient des calques et sans Qt.** Nouveau
  module strictement typé `bgremover/project_history.py` (`ProjectHistory`) fait
  passer annuler/rétablir d'une image unique au modèle de projet : il couvre les
  changements structurels (ajout/suppression/réordonnancement/duplication d'un
  calque, calque actif, visibilité/opacité/verrouillage/rôle) et les
  modifications de pixels par calque. Stratégie mémoire : des instantanés
  structurels légers plus un pool de pixels avec déduplication qui ne compte
  qu'une fois les calques inchangés dans le budget annuler/rétablir partagé
  (l'original et l'état courant restent hors budget) ;
  `descriptions()`/`undo_to()`/« restaurer l'original » sont conservés. Pas
  encore relié au canevas (#331, #329 ; suite dans #332).
- **Format de fichier projet `.bgrproj` (enregistrement/chargement sans perte).**
  De nouveaux modules sans Qt `bgremover/project_io.py` et
  `bgremover/project_schema.py` écrivent/lisent un projet multicalque complet sous
  forme de conteneur ZIP (`manifest.json` avec version de format, taille du
  canevas, liste ordonnée des calques incl. rôles/métadonnées + un PNG RGBA par
  calque). L'enregistrement est atomique (`mkstemp`+`os.replace`) ; le chargement
  valide de façon défensive (limite de taille de fichier, plafond de mégapixels
  par calque, défense contre le zip-slip/les entrées inattendues, messages
  d'erreur clairs et traduits). Le schéma est versionné avec des points de
  migration : les anciennes versions migrent, les plus récentes restent intactes
  (avertissement seulement). Pas encore relié aux menus/dialogues
  (#333, #329 ; suite dans #334/#335).
- **Panneau de calques et menu projet.** Le panneau de droite gagne un nouvel
  onglet « Calques » : créer des calques, sélectionner (le calque d'édition
  actif), afficher/masquer, changer l'opacité, réordonner haut/bas, dupliquer,
  supprimer, renommer et attribuer un rôle (motif couleur/carte de hauteur/gloss) ;
  toutes les modifications agissent sur le composite du canevas (#332) et sont
  annulables/rétablissables (#331). Un nouveau menu « Projet » ajoute « Nouveau
  projet » (`Ctrl+N`), « Ouvrir un projet… » (`Ctrl+Shift+O`), « Enregistrer le
  projet » (`Ctrl+Alt+S`) et « Enregistrer le projet sous… » (`Ctrl+Alt+Shift+S`),
  relié au format `.bgrproj` (#333) ; `Ctrl+O`/`Ctrl+S` restent réservés aux flux
  d'images. Les erreurs de chargement/enregistrement s'affichent sous forme de
  messages clairs et traduits. Toutes les nouvelles chaînes passent par `i18n.py`
  (de/en en parité) (#334, #329 ; la migration image→projet suit dans #335).

### Modifié

- **Intégration image→projet et « Récemment ouverts » pour les projets.**
  « Ouvrir une image » et le glisser-déposer créent désormais un projet à un seul
  calque (le chargement validé via `image_loading` est inchangé) ; « Récemment
  ouverts » liste les images **et** les projets `.bgrproj` et ouvre chaque type
  correctement (selon l'extension). Le dernier répertoire de projet utilisé est
  mémorisé (clé de paramètres additive ; pas de migration de schéma nécessaire —
  la protection de version future est déjà testée). L'export d'image unique écrit
  toujours le composite (projet à un calque au bit près), et « restaurer
  l'original » renvoie le document dans son état chargé. Clôt l'epic des calques
  (#335, #329).
- **L'éditeur fonctionne désormais par calques (rendu du composite + calque
  actif).** Le canevas contient un `Project` (#330) au lieu d'une seule image et
  affiche/enregistre le **composite** des calques visibles
  (ordre/visibilité/opacité) ; tous les outils (baguette/sélection, pinceau/gomme,
  lasso, détourage IA, remplacer l'arrière-plan, miroir, coins arrondis) agissent
  sur le **calque actif**, et le masque de sélection s'y rapporte. La géométrie qui
  change la taille (rotation, recadrage) s'applique uniformément à tous les calques
  pour préserver l'invariant du modèle. Annuler/rétablir et « restaurer l'original »
  passent par l'historique conscient des calques `ProjectHistory` (#331). Un projet
  avec exactement un calque COLOR se comporte au bit près comme avant (parité, y
  compris les valeurs RGB conservées sous les pixels transparents à
  l'enregistrement) ; l'annulation de l'IA reste sans régression
  `QThread.terminate()` (#332, #329 ; le panneau de calques de l'UI suit dans #334).
- **Les notes de version GitHub proviennent désormais du CHANGELOG.** Le flux
  de publication (`release-linux.yml`) dérive le corps de la version pour une
  étiquette `vX.Y.Z` de la section `## [X.Y.Z]` de `CHANGELOG.md` et le
  transmet via `--notes-file` à `gh release` — y compris lors de la
  réutilisation d'une version existante (`gh release edit`), pas seulement à la
  première création. Le texte figé « Automated build… » disparaît ; si la
  section correspondante manque, le job de publication échoue clairement (pas
  de repli silencieux) (#311).
- **Le benchmark hebdomadaire ne signale plus les artefacts d'environnement
  comme des régressions.** Chaque résultat (`benchmarks/results/`) porte
  désormais une empreinte d'environnement (version de Python/Pillow/NumPy,
  architecture, nombre de CPU, runner) ; la comparaison ignore les références non
  comparables (empreinte manquante, versions ou paramètres de benchmark
  différents) et confirme une valeur suspecte dans la même exécution via
  plusieurs répétitions (médiane) avant d'ouvrir un ticket (#277, #278, #279).

### Corrigé

- **Couleurs de fond du mode sombre alignées sur le prototype.** Les fonds du
  mode sombre (`theme.DARK` : panneau inspecteur, barre d'étapes, barre
  d'outils, pied de navigation, barre de statut, contrôles et cartes)
  utilisent désormais la teinte bleu-gris froide du prototype validé
  (`design/Prototyp A - Geführter Workflow.dc.html`) au lieu d'un noir quasi
  neutre. `card_bg` utilise désormais lui aussi la valeur du prototype
  `#2e353f` ; `docs/REDESIGN_SPEC.md` §2 documente les valeurs reprises et la
  déviation intentionnelle de token restante (#475, #496).
- **Les bordures du mode sombre sont des superpositions douces au lieu de
  tons gris durs.** `border` et `hairline` sont désormais des superpositions
  blanches translucides comme dans le prototype (elles se démarquent
  différemment selon la surface sous-jacente au lieu de paraître uniformément
  dures) ; un nouveau token `border_2` couvre la teinte de bordure secondaire
  des boutons secondaires neutres (format de recadrage, format
  d'enregistrement, etc., `panel_btn_style`). La barre de menu partage
  désormais la teinte `toolbar` avec la barre d'outils au lieu de la barre de
  statut, comme dans le prototype où les deux partagent la même couleur
  (#476).
- **Bleu d'accent du mode sombre aligné sur le prototype.**
  `accent`/`accent2` (ainsi que les surfaces dérivées `accent_soft`/
  `accent_line`/`accent_shadow`) sont désormais le bleu plus clair et
  bleu-lavande du prototype au lieu d'une teinte plus terne — visible dans
  le dégradé du bouton primaire, le bouton « Suivant », les outils actifs,
  le cercle actif du stepper et le curseur du slider. `accent_text`
  correspondait déjà exactement à la valeur du prototype ; `accent_shadow`
  reste une simple valeur de couleur sans effet de lueur (Qt QSS ne connaît
  pas `box-shadow`, #477).
- **Les sliders de la colonne droite reproduisent le prototype.** Les sliders
  Qt suivent désormais le `input[type=range]` du prototype : pistes de 8 px,
  segment rempli en `accent`, reste gris clair, bord de piste blanc, poignée
  blanche de 16 px et espacement vertical `9px 0 2px`, y compris le slider
  d'opacité du panneau des calques (#496).
- **Le contrôle segmenté d'aperçu (étape 6) utilise désormais la bonne
  surface du prototype.** Le conteneur « Couleur/Relief/Hauteur/Gloss »
  (`_ModeSegments`) utilisait à tort la teinte `tabbar` ; en vérifiant les
  règles CSS réelles du prototype (pas seulement les variables `:root`), la
  surface en retrait `--inset` s'est révélée être la bonne valeur — ajoutée
  comme nouveau token `inset` et connectée. Deux autres tokens déclarés mais
  inutilisés dans le prototype (`label`, `good_line`) ont été ajoutés à
  `Palette` par souci d'exhaustivité, sans consommateur actuel ; une
  contrepartie `bad_line` n'existe pas dans le prototype et n'a donc pas été
  inventée (#479).
- **Le damier de transparence du canevas suit désormais le thème actif.** Le
  motif en damier derrière les zones transparentes de l'image était fixé en
  gris clair (`QColor(170,170,170)`/`(210,210,210)`) et ressemblait à une
  tache lumineuse au milieu du canevas en mode sombre. `checker_a`/
  `checker_b` corrigent cela via la palette (sombre : `#2c313a`/`#353b45`,
  clair : `#dde2ea`/`#eef1f5`) ; `make_checker_brush` reçoit désormais la
  palette active, et `ImageCanvas.apply_palette` actualise le motif en
  direct lors du changement de thème, sans redémarrage de l'application
  (#478).
- **Correction des tableaux de couleurs de REDESIGN_SPEC.md + ajout d'un
  test de régression de dérive.** La documentation prétendait être copiée
  1:1 depuis le prototype, mais selon sa propre note de provenance, elle
  n'avait jamais été réellement vérifiée par rapport aux valeurs de couleur
  réelles — une comparaison ligne par ligne a révélé une dérive propre à la
  documentation, indépendante de `theme.py` (`checker_a`/`checker_b`,
  `inset`, `label`, `good_line`, `border_2` manquants ; le schéma clair
  n'était qu'un extrait en prose au lieu d'un tableau). Les §2/§3 sont
  désormais des tableaux complets qui correspondent exactement à
  `theme.DARK`/`theme.LIGHT` ; la dérive restante du schéma clair par
  rapport au prototype, délibérément hors périmètre de cet épique, est
  maintenant explicitée au lieu d'être passée sous silence. Deux nouveaux
  tests dans `tests/test_theme.py` protègent cela durablement : l'un compare
  les tableaux de la spec aux palettes, un second vérifie en plus
  `theme.DARK` directement par rapport aux variables CSS intégrées dans le
  bundle du prototype — les deux échouent dès que le code et la
  documentation redivergent (#480, clôture l'épique #474).
- **L'aperçu en direct se rabat sur COLOR pour les calques de données de taille
  incompatible.** Lorsque la taille en pixels d'un calque HEIGHT/GLOSS (état de
  projet anormal ou étranger) ne correspond plus à la base, `_render_preview_uncached`
  traite désormais ce calque comme un rôle manquant dans **chaque** mode d'aperçu et
  se rabat sur le composite COLOR au lieu d'afficher une vue de taille incorrecte ou
  d'interrompre le rendu par une exception — à l'image de la règle existante
  « rôle manquant/invisible = dégrader ». Des tests de régression rendu/pixels
  envoient un calque HEIGHT/GLOSS de taille divergente dans
  `HEIGHT`/`RELIEF`/`GLOSS`/`COMBINED` et vérifient le résultat COLOR (#404).
- **Suppression d'un chemin de géométrie mort dans l'export EufyMake.** La fonction
  privée `_derive_physical_size` — orpheline depuis le passage aux getters du modèle
  de projet (#377/#378) — et l'import `parse_size_mm` utilisé uniquement là ont
  disparu ; `_derive_target` dérive toujours la taille physique et les DPI de
  `project.physical_size_mm`/`project.dpi`. Aucun changement de comportement ; la
  description de géométrie de CLAUDE.md pointe désormais vers le chemin réellement
  utilisé (#406).
- **Aperçu du canevas cohérent après la fin de la phase 1.** Les aperçus en direct
  de couleur et de hauteur passent désormais par le mode choisi comme contenu de
  calque temporaire ; le mode, l'intensité du relief et le commutateur de brillance
  agissent immédiatement sans modifier le modèle ni l'export. Les calques de rôle
  Height/Gloss masqués ne sont plus rendus et un relief à 0 évite entièrement le
  hillshade coûteux (#397, suivi de #396).
- **Export d'image avec un calque de hauteur actif.** « Enregistrer l'image »
  écrit de nouveau le composite COLOR indépendamment du calque d'édition actif.
  La vue HEIGHT en niveaux de gris reste limitée au canevas et ne peut plus être
  exportée silencieusement comme image normale ; l'export bit à bit d'un unique
  calque COLOR, y compris le RGB sous les pixels transparents, est préservé (#363).
- **Le filtre médian Height Map est borné en mémoire.**
  `height_ops.median_blur` ne matérialise plus une pile de fenêtres complète
  `(2r+1)² × H × W` (qui aurait atteint ~33 Gio à 40 MP/rayon 10) ; il traite
  désormais l'image en **bandes de lignes** avec une pile par bande strictement
  plafonnée via `_MEDIAN_MAX_TEMP_BYTES`. La mémoire supplémentaire est donc
  indépendante de la taille de l'image et ne croît plus avec le rayon, tandis que
  le résultat reste **bit à bit** identique (même bord, `coverage`, `max_value`,
  16 bits). `gaussian_blur`, convolution séparable, est déjà `O(H × W)` et
  indépendant du rayon — évalué dans son docstring. Des tests de régression
  couvrent l'équivalence avec la pile complète pour tous les rayons de l'UI et le
  budget mémoire pour le cas 40 MP (#365).
- **Contexte de hauteur : modèle, interface et canevas suivent un contrat.** Un
  calque est compatible hauteur *exactement quand* `kind == LayerKind.HEIGHT` ;
  le rôle `HEIGHT_MAP` ne peut être que sur un calque HEIGHT. Une nouvelle règle
  centrale, sans Qt (`role_allowed_for_kind`), est la seule source de vérité :
  les API du modèle (`Layer`, `assign_role`) refusent `HEIGHT_MAP` sur COLOR/
  GLOSS/GENERIC avec `IncompatibleRoleError`, le panneau des calques ne propose
  le rôle que pour les calques HEIGHT, et l'onglet carte de hauteur n'active ses
  outils que pour un calque HEIGHT actif — l'interface ne promet donc plus une
  opération que le canevas refuse ensuite. Le chargement d'un projet
  historiquement incompatible supprime sans perte uniquement le rôle invalide
  (type, nom, pixels, ordre et métadonnées restent identiques) et affiche un
  avertissement traduit (#364).

## [2.4.1] – 2026-06-17

### Corrigé

- **L'app de téléchargement macOS (`.dmg`) ouvrait des fenêtres sans fin après
  le démarrage.** Dans le bundle figé, l'inférence IA démarre son processus
  enfant via multiprocessing « spawn », qui relance le binaire de l'app
  lui-même ; sans `multiprocessing.freeze_support()` dans le point d'entrée du
  bundle, chaque enfant relançait la GUI → une « fork bomb » de plus de 100
  fenêtres que seul un redémarrage arrêtait. Le point d'entrée PyInstaller
  appelle désormais `freeze_support()` en premier, afin que le processus enfant
  d'inférence démarre correctement au lieu d'ouvrir la GUI.

- **L'app de téléchargement macOS (`.dmg`) ne démarrait pas.** Le bundle figé
  s'interrompait dès `import bgremover` avec `PackageNotFoundError` puis
  `FileNotFoundError`, car PyInstaller n'incluait pas les métadonnées du
  paquet et le bundle ne dispose d'aucun `pyproject.toml` de repli — l'icône
  ne faisait que clignoter brièvement, puis rien ne se passait. La spec
  PyInstaller embarque désormais les métadonnées `*.dist-info`
  (`copy_metadata`), et la détection de version ne peut plus interrompre le
  démarrage (repli défensif au lieu d'une exception non gérée).

- **La suppression d'arrière-plan par IA dans le `.dmg` ne se chargeait pas.**
  Le processus enfant d'inférence mourait à l'`import rembg` avec
  `PackageNotFoundError` (« No package metadata was found for pymatting ») :
  PyInstaller embarque le code des dépendances de rembg mais pas leurs
  métadonnées `*.dist-info`, alors que `pymatting` lit sa propre version à
  l'import. La spec embarque désormais les métadonnées de toute la chaîne de
  dépendances de rembg (`copy_metadata(…, recursive=True)`).

## [2.4.0] – 2026-06-15

### Ajouté

- **App macOS en téléchargement (`.dmg`).** Un bundle `BgRemover.app` autonome
  (PyInstaller, Apple Silicon/arm64) est généré en `.dmg` et joint à la release
  GitHub — comme l'AppImage Linux et sans installation locale de Python. Le
  bundle est **non signé** pour l'instant : au premier lancement, ouvrez-le une
  fois via clic droit → « Ouvrir ». Compilation via
  `packaging/mac/build_macos.sh`.
- **Les artefacts de téléchargement incluent désormais la suppression
  d'arrière-plan par IA.** L'AppImage Linux et le `.dmg` macOS embarquent
  `rembg`/`onnxruntime`, si bien que l'IA en un clic fonctionne sans
  installation supplémentaire (artefacts d'autant plus volumineux).
- **Le workflow de release compile en multiplateforme.** `release-linux.yml`
  produit désormais, en plus de l'AppImage et du `.deb` Linux (x86_64 +
  aarch64/Raspberry Pi OS), un `.dmg` macOS arm64 pour le tag `vX.Y.Z` et
  publie tous les artefacts ensemble.
- **Ouvrir des images via l'association de fichiers et la ligne de commande.**
  `bgremover image.png` et `python -m bgremover image.png` ouvrent le chemin
  après la construction de la fenêtre, par le même chemin de chargement validé et
  asynchrone que la boîte de dialogue, les fichiers récents et le glisser-déposer ;
  l'entrée de bureau Linux (`%F`) et les `QFileOpenEvent` macOS (Finder « Ouvrir
  avec », double-clic) sont aussi traités. Plusieurs chemins : le premier est
  ouvert, les autres ignorés avec leur nombre dans la barre d'état ; les chemins
  manquants, non pris en charge ou non locaux sont rejetés de façon contrôlée au
  lieu d'interrompre le démarrage, et la confirmation des modifications non
  enregistrées s'applique avant de remplacer une image éditée. Les threads de
  travail en cours sont en outre arrêtés proprement à la fermeture (#249).
- **Benchmark de performance du pipeline d'images.** `scripts/benchmark.py`
  mesure le temps de traitement par format de sortie (PNG/JPEG/WebP/TIFF) via les
  vrais chemins `image_ops`, enregistre des résultats datés sous
  `benchmarks/results/` et compare les exécutions successives ; les formats qui
  régressent de plus de 10 % sont signalés et éventuellement remontés comme
  tickets GitHub (`make bench` / `make bench-compare`). Un workflow CI
  hebdomadaire (`.github/workflows/benchmark.yml`) exécute et compare sur un
  matériel constant et réenregistre le résultat comme prochaine référence.
- **Tests comportementaux renforcés.** La couverture des tests comportementaux
  pour des chemins jusqu'ici lacunaires a été étendue (#177, #192).
- **Tests unitaires dédiés pour `app.py` et `main_window.py`.** Couverture de
  `app.py` 0 % → 100 % et `main_window.py` 68 % → 100 % ; la couverture globale
  est passée à 94 % (#214).

### Modifié

- **Dépendances mises à jour.** `idna` passe à 3.15 et `urllib3` à 2.7.0 ;
  `LICENSES.md` est synchronisé avec le nouveau snapshot de dépendances.
- **Backend de build épinglé contre des CVE de chaîne d'approvisionnement.**
  `setuptools` passe à `>=78.1.1` dans `pyproject.toml` (`[build-system]`) et
  `requirements/constraints.txt` (CVE-2024-6345 RCE, CVE-2025-47273 path
  traversal), et `wheel` à `==0.46.2` dans `constraints.txt` (CVE-2026-24049).
  Le build isolé du wheel ne peut plus tirer d'outils de build vulnérables
  (#200, #201).
- **pip relevé à une version corrigée en CI/dev.** Les workflows CI qui
  installent avec pip (`ci.yml`, `pr-ci.yml`, `ui-nightly.yml`, `benchmark.yml`,
  `license-check.yml`) et le hook SessionStart web montent `pip` à `>=26.1.2`
  avant l'installation, tout comme la doc d'installation dev
  (`README.md`/`INSTALL_MAC.md`/`INSTALL_LINUX.md`). Clôt le lot `pip-audit` de
  CVE de path traversal, lien symbolique et détournement de module ; pip est
  l'outil d'installation lui-même et ne peut donc pas être épinglé via
  `constraints.txt` (#202).
- **Le diagnostic macOS caviarde les chemins sensibles.** `diagnose_mac.sh`
  remplace désormais `$HOME` par `~` par défaut, raccourcit les autres chemins
  `/Users/<name>` et affiche un résumé filtré des erreurs avec chemins
  caviardés au lieu des 40 dernières lignes brutes du log — la sortie peut
  être jointe sans risque aux rapports de bug. Le nouveau drapeau
  `--include-raw-logs` fournit le diagnostic complet (log brut inclus) ; un
  test shell (`tests/test_diagnose_mac.py`) garantit que le répertoire home et
  les chemins d'images n'atteignent jamais la sortie par défaut (#185).
- **Dépendances de release AppImage épinglées.** Un snapshot
  `requirements/constraints.txt` fixe les versions pour le workflow de build
  AppImage (#182, #191).
- **Permissions du workflow de licences renforcées.** Le workflow s'exécute
  désormais avec des permissions minimales (#183, #193).
- **`CanvasHistory._redo_max` supprimé.** L'attribut en écriture seule n'était
  jamais lu ; la limite de redo est appliquée uniquement via `deque(maxlen=…)`
  (#199, #215).
- **`import bgremover` ne charge plus le stack Qt.** Le point d'entrée du paquet
  (`bgremover/__init__.py`) n'exporte plus directement que des métadonnées légères
  (`__version__`, `get_version`) ; les ré-exports GUI/Qt établis (`ImageCanvas`,
  `MainWindow`, workers …) restent compatibles mais sont chargés paresseusement
  via un `__getattr__` PEP 562 au premier accès d'attribut. Les requêtes de version
  et de métadonnées fonctionnent désormais headless sans PyQt6 ; un test de
  régression en sous-processus garantit qu'un import léger n'amène ni
  `bgremover.canvas`/`main_window` ni PyQt6 dans `sys.modules` (#232).

### Corrigé

- **Sous-processus rembg renforcé (robustesse et mémoire).** Quatre constats de
  suivi issus de la revue Codex de #283 dans `bgremover/ai_process.py` : après un
  échec transitoire de `new_session()`, la session rembg est reconstruite — une
  seule fois — à la requête suivante, au lieu de basculer sur
  `remove(..., session=None)` et de recharger le modèle à chaque appel (la
  garantie de #229 est préservée) ; le processus enfant inactif libère
  immédiatement le dernier PNG d'entrée au lieu de le conserver ; les PNG
  d'entrée et de résultat transitent comme trames d'octets brutes
  (`send_bytes`/`recv_bytes`) plutôt que sérialisées par pickle dans le tube, ce
  qui supprime les pics de mémoire et le risque d'OOM sur de grandes images
  (jusqu'à 40 MP) ; et un `request_stop()` arrivant exactement pendant le
  démarrage du processus est reporté sur le nouveau processus via le couple
  `_proc_lock`/`_stop_pending`. Des tests de régression couvrent les quatre
  chemins (#285).
- **Pics de mémoire dans la lecture de fichier plafonnée atténués.** Deux constats
  de suivi de la revue Codex de #264 dans
  `bgremover/image_loading._read_capped` : au lieu de `b"".join(chunks)` (qui
  gardait les chunks **et** le résultat en même temps, ~1 Gio près de la limite
  de 512 Mio), le contenu est assemblé dans un unique `bytearray` pré-dimensionné
  et transmis directement — plus de pic ~2×. La première lecture est en outre
  bornée par la taille connue via `os.fstat()`, si bien qu'un petit fichier ne
  demande plus ~8 Mio de marge ; une petite lecture de suivi détecte toujours une
  croissance entre `fstat()` et la lecture (TOCTOU) ou un `st_size` peu fiable
  (pipes/sockets). La détection limite/dépassement (`None`) est inchangée ; des
  tests de régression couvrent les deux chemins (#286).
- **Limite de taille du fichier d'entrée avant la lecture.**
  `open_validated_image` contrôle désormais le fichier d'entrée via `os.fstat()`
  par rapport à une limite d'octets documentée (`_MAX_INPUT_FILE_BYTES`,
  512 Mo) **avant** que son contenu ne soit entièrement lu en mémoire ; un
  `read()` borné supplémentaire protège contre les objets fichier inhabituels et
  un changement de taille entre `fstat()` et `read()` (TOCTOU). Le message
  distingue la taille de fichier (Mo) de la limite de mégapixels (MP). Les
  chemins de chargement synchrone et asynchrone partagent le même contrôle ; la
  limite de mégapixels existante et la protection TOCTOU sont préservées (#230).
- **La session d'inférence rembg est réutilisée.** Le warmup crée désormais
  exactement une session rembg/ONNX via `new_session()` et la stocke au niveau
  du module ; chaque `AIWorker` ultérieur la passe à `remove(..., session=...)`
  au lieu de réinitialiser le modèle. La création est thread-safe via un
  double-checked locking et s'exécute au plus une fois sur plusieurs appels IA ;
  un init échoué signale toujours l'erreur du worker et ne laisse aucun état
  faussement « prêt ». Le commentaire trompeur (un `remove()` factice mettrait
  la session en cache) est corrigé au passage (#229).
- **`recent_files` est robuste face à des réglages corrompus.**
  `RecentFiles.paths()` traite désormais chaque type brut stocké de façon
  défensive : une simple chaîne reste une entrée, les listes/tuples sont filtrés
  élément par élément vers des chaînes non vides, et toute autre valeur (p. ex.
  entier, `None`) donne une liste vide au lieu d'un `TypeError`. Le nouveau
  `sanitize()` réécrit une fois au démarrage une valeur réellement corrompue
  sous forme nettoyée (avec avertissement de log) ; l'inoffensive chaîne
  mono-élément de QSettings reste intacte. Une valeur `recent_files` éditée à la
  main ou obsolète n'interrompt donc plus le menu ni le démarrage de l'app ; un
  schéma plus récent (futur) est lui aussi laissé intact pour éviter une perte de
  données lors d'un downgrade (#233, #240).
- **Double-checked lock pour l'import paresseux de rembg et protection TOCTOU
  dans `open_validated_image`.** Deux threads pouvaient entrer dans l'import en
  même temps (race) et le fichier était ouvert deux fois (fenêtre TOCTOU) ; les
  deux sont couverts par des tests de régression (#174).
- **Les résultats de chargement d'image asynchrones obsolètes sont rejetés.** Un
  compteur monotone `_load_generation` dans `MainWindow` empêche un callback de
  chargement tardif d'écraser une image plus récente (analogue au stale-check
  IA) (#190).
- **Typage du masque de sélection du canevas corrigé.** Un type incorrect
  provoquait une erreur mypy dans l'exécution CI complète (#196, #197).
- **YAML du workflow CI réparé.** Le nom non quoté de l'étape de mise à jour de
  pip cassait l'analyse du workflow (#213).
- **Un recadrage actif ne survit plus à un changement d'état de l'image.** Chaque
  changement visible d'image (rotation, miroir, résultat IA, annuler/refaire,
  restauration de l'original, confirmation du recadrage) abandonne désormais de
  façon centralisée dans `_set_image_state` un overlay de recadrage actif et un
  lasso en cours, et émet `cropModeChanged(False)` exactement une fois. Un
  rectangle de recadrage obsolète ne peut donc plus être appliqué à la nouvelle
  image ni produire de pixels de remplissage transparents (#247).
- **Le workflow de release ne publie qu'après un gate Full CI au vert.**
  `release-linux.yml` appelle désormais la matrice Full CI de référence
  (`ci.yml`) comme workflow réutilisable et y lie build et publish via `needs` ;
  un job `verify-tag` séparé échoue si le tag ne respecte pas `vX.Y.Z` ou diffère
  de `project.version`. AppImage/`.deb` sont vérifiés (nom, architecture,
  exécutabilité, métadonnées Debian) avant l'envoi, et les erreurs de
  `gh release create` ne sont plus masquées par `|| true` (une release existante
  est réutilisée explicitement). Ainsi, aucun artefact issu d'un commit aux tests
  rouges ou à version divergente n'atterrit plus dans une release (#250).
- **Une sélection vide libère immédiatement le pixmap de l'overlay.**
  `_refresh_overlay` vérifie désormais l'état vide du masque **avant** le chemin
  incrémental (dirty). Lorsque la gomme retire le dernier pixel sélectionné,
  `_overlay_pixmap` et le `QGraphicsPixmapItem` sont vidés aussitôt au lieu de
  conserver une QPixmap transparente de la taille de l'image (~160 Mio à 40 MP)
  jusqu'à la prochaine reconstruction complète. L'effacement partiel ne met
  toujours à jour que le rectangle modifié (#251).
- **Suivis du workflow de release durcis.** Le job de publication définit
  désormais `GH_REPO` pour que `gh release` cible le bon dépôt sans checkout ; le
  job de test réutilisable dépend de `verify-tag`, si bien qu'un tag invalide ou
  ne correspondant pas à la version ne démarre plus la matrice ; et
  `download-artifact` récupère les artefacts via `run-id`/`github-token` (avec
  `actions: read`) sur l'ensemble du run, de sorte que « Re-run failed jobs » ne
  perd plus les artefacts d'une tentative précédente. README/RESOURCES (y compris
  les traductions) ne décrivent plus le trigger supprimé `release: published`
  (#257).
- **Limite de chargement d'image sans préallocation de 512 Mio et localisée.**
  `open_validated_image` lit désormais le contenu par blocs de 8 Mio (au lieu de
  `read(limit + 1)`, qui sur le lecteur tamponné de CPython réserve aussitôt
  ~512 Mio et peut faire échouer un petit fichier avec `MemoryError` en mémoire
  restreinte) ; la croissance entre `fstat()` et la lecture est toujours
  détectée via `limit + 1`. Le message de taille passe par la clé de traduction
  `status.file_too_large` (entièrement localisé de/en au lieu d'un message mixte)
  et arrondit la valeur réelle vers le haut et la limite vers le bas, de sorte
  qu'elle est visiblement plus grande à « limite + 1 octet » (p. ex. « 513 MB »
  pour un maximum de « 512 MB », au lieu d'afficher les deux comme « 512 MB »
  avec `.0f`) (#258).
- **La migration de schéma QSettings est sûre au downgrade.** Une migration
  manquante ne pousse plus `schema_version` à la valeur courante sans
  vérification, et un schéma futur plus élevé n'est plus réécrit lors de la
  construction du menu des fichiers récents — un downgrade accidentel ne perd
  ainsi aucun réglage (#234, #259).
- **Échap annule d'abord le lasso en cours ; curseur d'outil restauré après le
  recadrage.** Un lasso polygonal en cours est désormais annulé par Échap avant
  l'effacement de la sélection (ordre recadrage > lasso > sélection). Quand un
  recadrage actif est abandonné automatiquement, `_finish_mode` restaure le
  curseur de l'outil actif au lieu de conserver le curseur de recadrage
  (#248, #260).
- **L'arrêt des workers est borné dans le temps.** À la fermeture de l'app, le
  `WorkerController` n'attend plus que brièvement sur `quit()`/`wait()` avant de
  recourir à `terminate()` avec un autre `wait()` borné ; un worker qui ne répond
  pas ne bloque plus la fermeture indéfiniment, et le chemin d'erreur est journalisé.
  Le vrai risque de `terminate()` pour le travail ONNX natif a ensuite été résolu
  en déplaçant l'inférence rembg/ONNX dans son propre processus démarré via
  `spawn` (`ai_process`) : le worker IA ne fait que sonder le résultat et peut
  être arrêté de façon coopérative, l'annulation et la fermeture terminent
  brutalement le processus d'inférence, et `terminate()` n'est plus la sortie
  d'urgence pour le travail IA (#270, suite de #231).
- **L'overlay du pinceau évite un scan complet du masque par mouvement.**
  `canvas_selection` tient le compteur de sélection de manière incrémentale et
  utilise la bounding box du changement au lieu de scanner tout le masque à
  chaque mouvement de pinceau/gomme ; `has_selection` est ainsi en O(1). Cela
  garde les grandes images fluides lors d'un dessin rapide (#261).

### Supprimé

- **Code mort supprimé (#244).** La méthode jamais appelée `ImageCanvas._zoom`
  et le wrapper `WorkerController.launch_worker` inutilisé en production ont été
  supprimés ; les tests de cycle de vie des threads passent désormais par le
  chemin réellement utilisé `_build_thread`.

## [2.3.0] – 2026-06-04


### Ajouté

- **Couverture de tests portée à 88 % (deuxième ronde, auparavant 82 %).** Le
  nouveau fichier `tests/test_canvas_events.py` couvre les gestionnaires
  d'événements et la logique de `canvas.py` : souris, clavier, molette,
  glisser-déposer, flux de résultat de la baguette, réglages d'outils,
  undo/redo/undo-to pendant un crop actif et guards sans image chargée.
  `canvas.py` passe de 64 % à 99 % et `fail_under` de 80 à 86.
- **Couverture de tests portée à 82 % (auparavant 74 %).** De nouveaux tests de
  comportement couvrent `tests/test_lasso.py`, `tests/test_canvas_crop.py`,
  `tests/test_viewport.py`, `tests/test_crop_overlay.py`,
  `tests/test_settings_schema.py` et `tests/test_settings_dialog.py`. Plusieurs
  modules atteignent 100 %, `canvas_crop.py` 98 %, et `fail_under` passe de 68 à
  80.
- **i18n de ANLEITUNG.md.** Cinq traductions du guide allemand ont été ajoutées
  dans `docs/i18n/{en,es,fr,uk,zh}/ANLEITUNG.md`; `tests/test_i18n_docs.py`
  inclut désormais `"ANLEITUNG.md"` et chaque traduction précise que
  `ANLEITUNG.pdf` n'est généré que pour l'original allemand.
- **Test soft-drift `tests/test_i18n_sync.py`.** Compare la hiérarchie des
  titres et le nombre de blocs de code de `CHANGELOG.md`, `INSTALL_MAC.md` et
  `INSTALL_LINUX.md` avec les originaux allemands ; les écarts produisent des
  avertissements lisibles plutôt que des échecs bloquants.
- **`bgremover/status_messages.py` – messages d'état centralisés.** Les textes
  d'état visibles depuis `canvas.py`, `canvas_crop.py` et `main_window.py` sont
  regroupés dans `StatusMessages`, en préparation d'une future localisation.
- **i18n runtime avec support anglais.** L'allemand et l'anglais peuvent être
  changés à l'exécution ; le dialogue de réglages inclut un sélecteur de langue
  persistant avec indication de redémarrage, et les textes UI du canvas, des
  dialogues et du panneau droit utilisent la couche centrale de traduction.
- **Raccourcis clavier pour les outils.** Les outils d'édition peuvent être
  changés au clavier ; les tooltips de la barre d'outils et la documentation
  listent les raccourcis adaptés à chaque plateforme.
- **Paquet Linux AppImage.** Le build de release produit désormais un AppImage
  comme voie recommandée pour les utilisateurs Linux, avec scripts de packaging,
  couverture CI et notes d'installation.
- **Linux `.deb`, aarch64/Raspberry Pi et workflow de release.** Le packaging
  Linux ajoute les paquets Debian, le support aarch64/Pi et le workflow de
  release associé.
- **Version de schéma QSettings.** Nouveau `bgremover/settings_schema.py` avec
  `SCHEMA_VERSION = 1` et `migrate(settings)` ; `MainWindow.__init__` lance la
  migration à la création de `QSettings`. Protection downgrade, valeurs
  corrompues et tests dans `tests/test_settings_schema.py` sont couverts.
- **Test runtime pour `RembgWarmupWorker`.** De nouveaux tests dans
  `tests/test_workers.py` et `tests/test_worker_controller.py` vérifient que le
  warmup émet toujours `finished` et que le cycle de vie du thread se termine
  même si `rembg_remove` échoue au premier démarrage.

### Modifié

- Documentation et commentaires de code nettoyés : les marqueurs PR/séries
  obsolètes ont été retirés des docs vivantes, les notes d'installation macOS
  ont été actualisées et les recommandations résumées à l'état review/roadmap
  courant.
- La version du projet passe à 2.3.0 dans les métadonnées du paquet,
  AppStream, les aperçus de licences et les liens du changelog.

- **Langue des docstrings unifiée.** `bgremover/image_ops.py`,
  `bgremover/recent_files.py` et `bgremover/worker_controller.py` passent de
  docstrings anglaises à l'allemand, conformément au reste du projet.
- **Documentation utilisateur des paquets Linux et du réglage de langue mise à
  jour.** README, `INSTALL_LINUX.md` et `ANLEITUNG.md` mentionnent AppImage/`.deb`
  comme voie recommandée pour les utilisateurs Linux et documentent la langue
  persistante avec l'indication de redémarrage ; les copies i18n sont
  synchronisées.
- **Ronde d'hygiène de code.** Le fallback de version lit `pyproject.toml`,
  `_paint_brush` reçoit `additive` explicitement, `apply_remove`/`apply_replace`
  ne capturent que les erreurs attendues, les effets globaux et cas QSettings
  sont documentés, `make clean` nettoie plus d'artefacts et la description du
  projet reflète le support macOS/Linux.
- **La sélection par baguette ne bloque plus l'UI.** Le flood-fill passe dans
  `FloodFillWorker` sur un `QThread` court avec vérification stale par
  `content_revision`; pan/zoom restent réactifs et seul un clic parallèle de
  baguette est bloqué avec un message d'état.
- **Matrice CI étendue.** Full CI vérifie Python 3.10, 3.11, 3.12 et 3.13 sur
  Ubuntu et macOS.
- **`RembgWarmupWorker` hérite de `_Worker`.** Le boilerplate commun passe dans
  la base avec le hook `_always_finished()`, tout en conservant le contrat
  `finished` et en unifiant logging, erreurs et annotations de `WorkerController`.
- **Les sous-modules Canvas utilisent l'API publique d'édition.** `CanvasCrop` et
  `CanvasTransform` utilisent `apply_edit(...)` et `ImageCanvas.current_tool` ;
  plusieurs opérations de sélection utilisent `_requires_image` et l'état vide
  signale désormais clairement l'absence d'image.
- **API publique du paquet allégée.** Les symboles privés ne sont plus
  réexportés depuis `bgremover`; les consommateurs doivent importer depuis les
  sous-modules. `logger`, `LOG_FILENAME`, `REMBG_AVAILABLE` et
  `current_log_file` restent publics ; la façade de test `MainWindow._recent_paths()`
  est supprimée.

### Corrigé

- **`apply_remove`/`apply_replace` ne masquent plus les vrais bugs.** Le filtre
  étroit laisse remonter `AttributeError`, `AssertionError` et similaires tout en
  convertissant les erreurs image/IO attendues en messages d'état.
- **Le chemin de chargement synchrone utilise les mêmes protections que le
  worker.** `ImageCanvas.load_image` appelle désormais `open_validated_image`,
  donc les fichiers manipulés et formats non pris en charge se terminent aussi
  proprement via message d'état lors du drag & drop.
- **License check stabilisé.** `coverage` est épinglé dans
  `requirements/constraints.txt` (`==7.14.0`) pour éviter un drift de
  `LICENSES.md` dû aux releases upstream.
- **License check renforcé contre le drift de fuseau horaire.**
  `actions/checkout` utilise `fetch-depth: 0` et la date est calculée avec
  `TZ=UTC` et `--date=short-local`, afin de trouver le vrai commit et de
  formater la date de manière déterministe.

### Supprimé

- **Code mort supprimé de Canvas, Lasso et MainWindow.** `ImageCanvas._version`,
  `CanvasLasso.close_to_mask` et `MainWindow._btn_grp` sont supprimés.

## [2.2.0] – 2026-05-25

### Ajouté

- **Snapshot reproductible des dépendances**
  (`requirements/constraints.txt`). Le Makefile, le workflow de licences
  et le build de l'app macOS utilisent le même jeu de constraints commité
  pour les installations de tests, CI, licences et App Bundle.
- **Doctor local de l'environnement de tests** (`make doctor`,
  `scripts/check_test_env.py`). Vérifie la version de Python, les
  dépendances `[test]`, l'installation non éditable du paquet, le script
  console `bgremover` et Qt `offscreen` avant qu'un échec local
  n'apparaisse tard dans pytest.
- **Test de smoke CI pour le démarrage de l'app**
  (`tests/test_app_smoke.py`). Les tests d'UI existants sont exclus de
  la CI via `-m 'not ui'` ; la CI ne vérifiait donc jamais si
  l'application démarre tout court – exactement la faille par laquelle
  les échecs de démarrage macOS sont passés. Nouveau, sans le marqueur
  `ui` (donc exécuté en CI) : `python -m bgremover` et le script de
  console `bgremover` démarrent entièrement depuis un répertoire de
  travail neutre (le nouveau hook d'autotest `BGREMOVER_SMOKE_TEST`
  quitte après le premier tour de boucle d'événements avec le code 0) ;
  on vérifie que la configuration des plugins Qt produit un chemin
  valide ; la syntaxe shell des scripts de démarrage
  (`create_BgRemover_app.sh`, `BgRemover.command`, `diagnose_mac.sh`)
  et du lanceur intégré au paquet d'app est contrôlée. `zsh` est
  installé dans le job CI Linux à cet effet.

### Modifié

- **MainWindow est encore modularisé.** La persistance et la sémantique
  du menu « Ouvrir récent » vivent maintenant dans
  `bgremover/recent_files.py`; `MainWindow` ne délègue plus que le
  chargement, les messages d'état et l'intégration au menu Fichier.
- **Construction des menus/actions extraite de `MainWindow`.**
  `bgremover/menu_actions.py` construit la barre de menus, les `QAction`,
  les raccourcis et le sous-menu des fichiers récents ; `MainWindow`
  ne fournit plus que les callbacks métier.
- **Panneau d'onglets droit extrait de `MainWindow`.**
  `bgremover/right_panel.py` construit les onglets Sélection, Arrière-plan,
  Transformation et Forme, y compris sliders, spinboxes et boutons de
  panneau ; `MainWindow` ne fournit plus que les callbacks du canevas.
- **Orchestration des workers encapsulée hors de `MainWindow`.**
  `bgremover/worker_controller.py` possède maintenant les threads de
  chargement, d'IA et de warmup, y compris les références fortes aux
  workers, le câblage `deleteLater` et le shutdown partagé.

### Corrigé

- **Liens de release/changelog corrigés vers des refs réelles.**
  `[Unreleased]` compare maintenant depuis `v2.1.0` ; `[2.1.0]`
  utilise comme base le commit de release 2.0.0 documenté, car le dépôt
  n'a pas de tag historique `v2.0.0`.
- **Paquet d'app : la détection de `bgremover` au setup ne dépend plus
  du répertoire de travail.** `create_BgRemover_app.sh` considérait la
  venv comme « prête » alors que `bgremover` n'y était pas installé :
  la vérification `has_deps` s'exécutait avec `cwd` dans le dossier du
  projet, et Python ajoute automatiquement le répertoire courant à
  `sys.path[0]` – donc `import bgremover` trouvait le **répertoire
  source** `bgremover/` du dépôt au lieu d'une vraie installation dans
  la venv. Le lanceur de l'app démarre avec un autre `cwd`, ne voit
  pas le répertoire source et signalait donc « Le paquet bgremover
  manque dans la venv ». `has_deps` et la vérification finale
  s'exécutent maintenant depuis `$HOME` (sous-shell `cd "$HOME"`), et
  vérifient ainsi la même réalité que le lanceur ; si le paquet
  manque, le chemin rapide pip install s'enclenche. `diagnose_mac.sh`
  teste aussi depuis `$HOME` et affiche en plus `pip show bgremover`
  de la venv de l'app (preuve indépendante du cwd indiquant si/où le
  paquet est installé).
- **Chemins de lancement macOS de nouveau fonctionnels.** Après la
  coupe en paquet (tour 5), `BgRemover.command` cherchait encore le
  fichier `BgRemover.py` qui n'existe plus et s'arrêtait sur « non
  trouvé » ; le `INSTALL_MAC.md` allemand ainsi que les versions i18n
  de `INSTALL_LINUX.md` et `README.md` conservaient aussi quelques
  anciennes commandes (l'étape 15 du tour 5 avait raté le
  `INSTALL_MAC.md` allemand et la documentation d'installation i18n
  dans le glob, ainsi que `Exec=python3 /CHEMIN/.../BgRemover.py`
  dans les extraits `.desktop` i18n). Conséquence : sur macOS aucune
  des trois voies de lancement documentées (paquet app, double-clic
  sur `.command`, terminal) n'était utilisable de façon fiable.
  `BgRemover.command` démarre maintenant via `python3 -m bgremover`
  et vérifie au préalable `import bgremover` (sinon affiche une
  indication claire vers `create_BgRemover_app.sh`). INSTALL_MAC +
  tous les documents i18n reflètent le modèle de paquet actuel (y
  compris l'installation non éditable du paquet dans la venv de
  l'app et la résolution des ressources via `importlib.resources`).
- **`create_BgRemover_app.sh` : venv existante migrée proprement.**
  Une venv de l'ère monolithique (avec PyQt6/Pillow/numpy installés,
  mais bien sûr pas encore `bgremover`) était considérée à tort comme
  « ready » parce que la vérification de setup `has_deps` ne testait
  pas `bgremover`. Lors du re-run, l'installation du paquet était
  donc ignorée — et le lanceur de l'app signalait ensuite à l'exécution
  « Le paquet bgremover manque dans la venv ». La vérification inclut
  désormais aussi `import bgremover` ; en outre, il y a un chemin
  rapide : si la venv de l'app a déjà PyQt6/Pillow/numpy, on ajoute
  seulement `pip install ".[ai]"` (secondes) au lieu de reconstruire
  la venv avec toutes les dépendances (minutes).

### Modifié

- **Opérations d'image pures extraites de `ImageCanvas`.**
  `bgremover/image_ops.py` contient désormais suppression/remplacement
  d'arrière-plan, enregistrement, rotation, miroir, coins arrondis et
  masquage de crop sous forme de fonctions PIL/NumPy sans Qt.
  `ImageCanvas` conserve l'état UI, undo/redo, signaux et overlays ;
  `tests/test_image_ops.py` vérifie directement les opérations de pixels
  sans `QApplication`.
- **Documentation des recommandations mise à l'état actuel.**
  `RECOMMENDATIONS.md` et les versions i18n contiennent maintenant un
  bloc d'état du tour 6 pour la série récente de PRs (#70, #72–#78) et
  signalent explicitement les anciens constats du monolithe comme
  contexte historique. `tests/test_recommendations_docs.py` protège ce
  bloc.
- **Documentation des ressources synchronisée.** `RESOURCES.md` et les
  versions i18n reflètent maintenant le layout de paquet (`bgremover/`
  au lieu de `BgRemover.py`), les package-data sous `bgremover/icons/`,
  le snapshot reproductible de constraints ainsi que les workflows PR,
  full et licences. Un test statique protège ces références contre un
  nouveau vieillissement.
- **`make pr-check` rend la vérification locale de PR plus robuste.** La
  cible réinstalle le paquet avec `[test]`, lance le doctor puis démarre
  `ruff`, `mypy` et `pytest`. Le Makefile trouve automatiquement
  `.venv/bin/python` et, sinon, retombe sur `python`/`python3` ; GitHub
  PR CI et Full CI utilisent la même cible. La configuration partagée
  des plugins Qt copie les plugins de plateforme dans le répertoire
  temporaire système si nécessaire, afin que les exécutions headless
  locales sur macOS n'échouent pas sur le listing des plugins dans le
  chemin du projet.
- **CI légère pour PR ajoutée et documentation de tests synchronisée.**
  Les pull requests disposent maintenant d'un workflow peu coûteux
  Ubuntu/Python 3.12 avec `make pr-check` ; la matrice complète Linux/macOS
  reste réservée aux releases et aux exécutions manuelles. Les workflows
  de test installent le paquet en mode non éditable afin que les smoke
  tests de l'app vérifient la réalité installée depuis un `cwd` externe.
  `README`, READMEs i18n, `TESTING.md` et `Makefile` décrivent
  désormais le même flux.
- **Monolithe → paquet (tour 5).** Le fichier unique `BgRemover.py`
  (3026 lignes) a été scindé dans le paquet installable `bgremover/`
  (14 modules : `constants`, `image_utils`, `icons`, `theme`,
  `workers`, `crop`, `canvas`, `widgets`, `settings_dialog`,
  `logging_config`, `main_window`, `app`, `__main__`, `__init__`).
  Lancement désormais via `python -m bgremover` ou le script de
  console `bgremover` ; l'ancienne forme `python BgRemover.py` est
  supprimée sans remplacement. `BgRemover.py` est supprimé. Réalisé
  en **13 étapes mécaniques**, chacune verrouillée par l'oracle vert
  (140 tests unitaires + 16 tests UI, ruff, mypy). Le seul changement
  de code intentionnel, neutre en comportement : `make_tool_icon`
  résout désormais les icônes via `importlib.resources` depuis les
  données du paquet (`bgremover/icons/`) au lieu de `__file__`/
  `sys.argv`/`cwd` — contrat inchangé. `pyproject.toml`, `Makefile`,
  workflow CI et le script de build macOS (`create_BgRemover_app.sh`)
  ont suivi dans la même coupe ; la venv installe le paquet en mode
  non éditable (avec package-data), rendant l'application indépendante
  du dossier du projet.
- Les re-exports transitoires dans `BgRemover.py` (phase B) et toutes
  les importations `BgRemover` des tests ont été basculés vers le
  paquet dans l'étape finale.

## [2.1.0] – 2026-05-19

### Modifié

- Garde de retour anticipé « aucune image chargée » des cinq méthodes
  de `ImageCanvas` (`apply_round_corners`, `apply_rotate`,
  `apply_flip`, `start_crop_circle`, `start_crop_ratio`) regroupée dans
  le décorateur `@_requires_image` – le bloc auparavant octet-identique
  disparaît ; comportement inchangé (défendu par la suite de tests
  existante).
- Les workers d'arrière-plan `AIWorker` et `ImageLoadWorker` partagent
  désormais la classe de base commune `_Worker`, qui encapsule le flux
  identique `try/except → logger.exception → error.emit` ; les
  sous-classes n'implémentent plus que `_work()`. `RembgWarmupWorker`
  reste délibérément autonome (pas de signal `error`, `finished`
  toujours dans `finally`).
- Coupe de version **2.1.0** : `pyproject.toml` et le repli
  `__version__` dans `BgRemover.py` passés à `2.1.0` ; les changements
  auparavant regroupés sous `[Unreleased]` (#48/#52/#53, INSTALL_LINUX,
  tours 3/4) sont désormais datés comme 2.1.0.

### Supprimé

- Suppression des constantes de stylesheet mortes `BTN_STYLE` et
  `GRP_STYLE`.

### Corrigé

- `save_image()` signale désormais les erreurs d'E/S comme message de
  statut au lieu de les propager sans gestion.

### Documentation

- Ajout d'un guide d'installation pour Linux (`INSTALL_LINUX.md`) :
  paquets système par distribution (apt/dnf/pacman), configuration du venv,
  script de lancement ou entrée `.desktop` et dépannage ; lié depuis le README.
  Y compris une voie particulièrement simple pour Raspberry Pi OS (Desktop)
  sans venv/pip (PyQt6/Pillow/numpy en tant que paquets système via `apt`), avec
  une étape facultative d'ajout de l'IA.

## [2.0.0] – 2026-05-17

Premier état de release 2.0.0 documenté. Le dépôt n'a pas de tag Git
historique `v2.0.0`.

### Fonctionnalités

- Suppression d'arrière-plan par IA via `rembg` (extra `ai` facultatif) y compris
  préchauffage en arrière-plan, pour que le premier clic ne bloque pas.
- Outils de sélection : baguette magique (flood-fill vectorisé avec
  curseur de tolérance), pinceau, gomme et lasso polygonal ; Maj/Ctrl
  pour une sélection additive ou soustractive.
- Rendre l'arrière-plan transparent ou le remplacer par une couleur.
- Transformations : rotation (par pas de 90° et angle libre), miroir,
  arrondi des coins, recadrage dans plusieurs formats avec grille des tiers.
- Historique avec annulation/rétablissement (boutons de la barre d'outils) et retour à n'importe quelle
  étape antérieure via une fenêtre flottante d'historique.
- Glisser-déposer ainsi que « Récemment ouverts » (10 entrées), tous deux via le
  worker de chargement asynchrone – pas de gel de l'interface.
- Enregistrement en PNG, JPEG, WebP ou TIFF.
- Paramètres persistants (répertoires par défaut, format de fichier
  préféré) via `QSettings`.
- Construction d'un bundle d'application macOS (`create_BgRemover_app.sh`) y compris venv
  isolé, gestion d'Apple Silicon et définition de l'icône ; prend en charge Python
  3.10–3.15.

### Stabilité et qualité

- Threads de worker sécurisés (pas de GC prématuré du worker,
  arrêt propre du thread dans `closeEvent`, course de l'IA via un compteur de version
  monotone du canevas).
- Limite de taille d'image (40 MP) et protection contre les bombes de décompression au chargement.
- Pile d'annulation limitée en mémoire (256 Mo) avec suivi des octets en O(1).
- Chemin de journal indépendant de la plateforme (`bgremover.log` dans le répertoire de données d'application).
- 108 tests ; `ruff` et `mypy` comme étapes de CI ; CI sur Ubuntu et macOS
  sous Python 3.10 et 3.12.
- `__version__` est lu depuis les métadonnées du paquet (source unique) ;
  la version apparaît dans le titre de la fenêtre.

### Documentation et licence

- Licence **GPL-3.0-or-later** (`LICENSE`) ; conditionnée par le
  binding PyQt6 sous licence GPL.
- `RESOURCES.md` (toutes les bibliothèques/outils/assets ainsi que leurs licences),
  `LICENSES.md` et un workflow automatisé de licence/conformité.
- README avec architecture, limitations connues et guide
  d'installation ; `INSTALL_MAC.md` détaillé.

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/v2.5.0...HEAD
[2.5.0]: https://github.com/NikolayDA/picture_helper/compare/v2.4.1...v2.5.0
[2.4.1]: https://github.com/NikolayDA/picture_helper/compare/v2.4.0...v2.4.1
[2.4.0]: https://github.com/NikolayDA/picture_helper/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/NikolayDA/picture_helper/compare/79f61c5514f283fae31ce9d21f31786a3acfbe16...v2.3.0
[2.2.0]: https://github.com/NikolayDA/picture_helper/compare/666d4a3932f70eabaafde8de4bfc2a0574be5d16...79f61c5514f283fae31ce9d21f31786a3acfbe16
[2.1.0]: https://github.com/NikolayDA/picture_helper/compare/d80067dbc064a8eab5774457eaaffab733c4cab6...666d4a3932f70eabaafde8de4bfc2a0574be5d16
[2.0.0]: https://github.com/NikolayDA/picture_helper/tree/d80067dbc064a8eab5774457eaaffab733c4cab6
