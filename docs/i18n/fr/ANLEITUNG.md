[Deutsch](../../../ANLEITUNG.md) · [English](../en/ANLEITUNG.md) · [Español](../es/ANLEITUNG.md) · **Français** · [Українська](../uk/ANLEITUNG.md) · [简体中文](../zh/ANLEITUNG.md)

> **Remarque :** La version PDF de ce guide n'est générée que pour l'original
> en allemand (`ANLEITUNG.pdf`). Aucun PDF n'est produit pour cette traduction.

# BgRemover – Guide d'utilisation

Ce guide explique étape par étape comment utiliser **BgRemover** — de
l'ouverture de la première image à l'enregistrement du résultat final. Il
s'adresse aux utilisateurs sans expérience préalable en retouche d'image.

> Les notes sur l'**installation** ne sont pas incluses ici intentionnellement ;
> consultez [INSTALL_MAC.md](INSTALL_MAC.md) (macOS) ou
> [INSTALL_LINUX.md](INSTALL_LINUX.md) (Linux). Ce guide suppose que
> l'application peut déjà être lancée.

---

## Table des matières

1. [Que peut faire BgRemover ?](#1-que-peut-faire-bgremover-)
2. [La fenêtre de l'application en un coup d'œil](#2-la-fenêtre-de-lapplication-en-un-coup-dœil)
3. [Démarrage rapide en 5 étapes](#3-démarrage-rapide-en-5-étapes)
4. [Ouvrir une image](#4-ouvrir-une-image)
5. [La barre d'outils (gauche)](#5-la-barre-doutils-gauche)
6. [Faire une sélection](#6-faire-une-sélection)
7. [Onglet « Sélection »](#7-onglet--sélection-)
8. [Onglet « Arrière-plan »](#8-onglet--arrière-plan-)
9. [Onglet « Ajuster » – Correction des couleurs](#9-onglet--ajuster---correction-des-couleurs)
10. [Onglet « Rotation/Miroir »](#10-onglet--rotationmiroir-)
11. [Onglet « Forme » – Coins et recadrage](#11-onglet--forme---coins-et-recadrage)
12. [Redimensionner et dimensions physiques](#12-redimensionner-et-dimensions-physiques)
13. [Calques et projets](#13-calques-et-projets)
14. [Espace de travail des cartes de hauteur](#14-espace-de-travail-des-cartes-de-hauteur)
15. [Aperçu 2D (couleur, relief, hauteur, brillance)](#15-aperçu-2d-couleur-relief-hauteur-brillance)
16. [Enregistrer et exporter](#16-enregistrer-et-exporter)
17. [Paramètres](#17-paramètres)
18. [Raccourcis clavier](#18-raccourcis-clavier)
19. [Flux de travail typiques](#19-flux-de-travail-typiques)
20. [Conseils et astuces](#20-conseils-et-astuces)
21. [Limitations connues](#21-limitations-connues)
22. [Résolution de problèmes et fichier journal](#22-résolution-de-problèmes-et-fichier-journal)
23. [Licence](#23-licence)

---

## 1. Que peut faire BgRemover ?

BgRemover est un outil de retouche d'image pour **supprimer, remplacer et
modifier les arrière-plans** — avec des fonctionnalités supplémentaires pour
l'optimisation d'image simple, les calques/projets et la préparation d'assets
d'impression UV. Les fonctionnalités principales :

- **Suppression d'arrière-plan par IA** – supprimez l'arrière-plan
  automatiquement en un seul clic.
- **Sélection manuelle** avec baguette magique, pinceau, gomme et lasso
  polygonal.
- **Remplacer l'arrière-plan** – rendre la sélection transparente ou la
  remplir avec n'importe quelle couleur.
- **Transformer** – faire pivoter (par paliers de 90° ou angle libre) et
  retourner.
- **Forme et recadrage** – arrondir les coins, recadrer en cercle ou selon
  un rapport d'aspect fixe.
- **Optimisation d'image** – ajuster la luminosité, le contraste et la
  saturation, et adoucir le bord alpha (feather).
- **Taille et dimensions physiques** – modifier la taille en pixels ou définir
  une taille d'impression via les millimètres et les DPI (avec indication de la
  zone d'impression).
- **Calques et projets** – gérer plusieurs calques (couleur/hauteur/brillance/
  générique) et enregistrer et ouvrir l'ensemble en tant que projet `.bgrproj`.
- **Cartes de hauteur** – générer une carte de hauteur à partir d'une image,
  puis la modifier et l'optimiser.
- **Aperçu 2D** – vérifier la couleur, le relief, la hauteur et la brillance à
  l'écran.
- **Export EufyMake Studio** – générer des assets d'import pour l'impression UV.
- **Historique** avec annuler/rétablir et saut vers n'importe quelle étape
  précédente.
- **Enregistrer** en PNG, JPEG, WebP ou TIFF.

---

## 2. La fenêtre de l'application en un coup d'œil

![BgRemover – fenêtre principale après le lancement](../../../app_screenshots/bgremover_complete_20260528_214013/01_main_empty.png)

*La fenêtre principale juste après le lancement : la barre d'outils à gauche, le
canevas avec le damier de transparence au centre, le panneau d'onglets à droite
(ici l'onglet « Sélection ») et la barre d'état en bas. Les captures montrent
l'interface en allemand ; les libellés correspondent aux termes utilisés dans
ce guide.*

La fenêtre est divisée en quatre zones :

```
┌──────────┬───────────────────────────────┬──────────────────┐
│          │                               │                  │
│  Barre   │          Canevas              │  Panneau         │
│  d'outils│     (image + sélection)       │  d'onglets       │
│  (gauche)│                               │  (paramètres)    │
│          │                               │                  │
├──────────┴───────────────────────────────┴──────────────────┤
│ Barre d'état (conseils et messages)                          │
└──────────────────────────────────────────────────────────────┘
```

| Zone | Rôle |
|---|---|
| **Barre de menus** (haut) | Fichier, Projet, Édition, Affichage, Extras |
| **Barre d'outils** (gauche) | Outils de sélection, IA, historique, ouvrir/enregistrer |
| **Canevas** (centre) | Affiche l'image et la sélection actuelle |
| **Panneau d'onglets** (droite) | Huit onglets : Aperçu, Sélection, Arrière-plan, Ajuster, Rotation/Miroir, Forme, Calques, Hauteur |
| **Barre d'état** (bas) | Conseils et retours de l'application |

### Menus « Édition », « Affichage » et « Projet »

De nombreuses actions sont aussi accessibles depuis la barre de menus :

- **Édition** – annuler/rétablir, rotation (90° gauche/droite), retournement
  horizontal/vertical, *Redimensionner…*, ainsi que désélectionner/inverser la
  sélection et *Restaurer l'original*. Pratique si vous préférez le menu à la
  barre d'outils ou à un onglet.
- **Affichage** – *Ajuster à la vue* (⌘0) et le sous-menu *Mode d'aperçu* (voir
  la [section 15](#15-aperçu-2d-couleur-relief-hauteur-brillance)) ; voir aussi
  « Zoom et affichage » ci-dessous.
- **Projet** – *Nouveau projet*, *Ouvrir un projet…*, *Enregistrer le projet* /
  *…sous…* (`.bgrproj`) et *Exporter des assets pour EufyMake Studio…* (voir la
  [section 13](#13-calques-et-projets) et la [section 16](#16-enregistrer-et-exporter)).

![Le menu « Édition »](../../../app_screenshots/bgremover_complete_20260528_214013/22_menu_edit.png)

*Le menu « Édition » regroupe annuler/rétablir, rotation, retournement et les
actions de sélection.*

### Zoom et affichage

- **Zoom :** utilisez la **molette de la souris** sur le canevas pour
  agrandir ou réduire.
- **Déplacer :** si l'image est plus grande que la fenêtre, naviguez avec
  les **barres de défilement** des bords droit et inférieur.
- **Ajuster :** `Affichage → Ajuster à la vue` (⌘0) remet l'image
  entièrement à l'échelle dans la fenêtre. Cela se produit aussi
  automatiquement au chargement d'une image.

---

## 3. Démarrage rapide en 5 étapes

Supprimez un arrière-plan en moins d'une minute :

1. **Ouvrir une image** – `Fichier → Ouvrir` (⌘O / Ctrl+O) ou glissez-déposez
   l'image dans la fenêtre.
2. **Lancer l'IA** – cliquez sur l'**icône IA** dans la barre d'outils gauche.
   L'arrière-plan est supprimé automatiquement.
3. **Retoucher (facultatif)** – utilisez la **gomme** pour supprimer les restes
   de la sélection ou le **pinceau** pour l'agrandir.
4. **Vérifier** – si nécessaire, appuyez sur **Annuler** (⌘Z) pour revenir
   en arrière.
5. **Enregistrer** – `Fichier → Enregistrer` (⌘S), choisissez le format **PNG**
   (conserve la transparence).

![Résultat de la suppression d'arrière-plan par IA](../../../app_screenshots/bgremover_complete_20260528_214013/54_function_ai_result.png)

*Après un clic sur l'icône IA, l'arrière-plan est détouré automatiquement ; la
barre d'état confirme que la suppression d'arrière-plan par IA est terminée, et
le damier indique les zones transparentes.*

Les sections suivantes expliquent chaque étape en détail.

---

## 4. Ouvrir une image

Il existe plusieurs façons de charger une image :

- **Menu :** `Fichier → Ouvrir…` (⌘O / Ctrl+O).
- **Glisser-déposer :** faites glisser un fichier image depuis le gestionnaire
  de fichiers directement sur le canevas. Si vous glissez plusieurs fichiers,
  seule la première image est chargée.
- **Fichiers récents :** `Fichier → Fichiers récents` liste les 10 dernières
  entrées ouvertes. Il s'agit aussi bien d'images que de **projets** `.bgrproj`
  (voir la [section 13](#13-calques-et-projets)) ; au clic, l'application
  détecte le type et l'ouvre en conséquence.
- **Démarrer avec un chemin d'image :** lorsque le programme est démarré avec un
  chemin d'image — via la **ligne de commande** (`bgremover image.png`) ou un
  **lanceur de bureau Linux** (association de fichiers) — il charge cette image
  directement au démarrage.
- **Ouverture via le Finder macOS :** sur macOS, une image peut aussi être
  transmise à BgRemover par **double-clic**, via « Ouvrir avec… » ou par une
  **association de fichiers** dans le Finder.

Toutes ces voies utilisent le même **chemin de chargement validé et asynchrone** :
les mêmes contrôles de format et de taille s'appliquent, et les grandes images
sont chargées en arrière-plan — la barre d'état affiche la progression.

![Le menu « Fichier »](../../../app_screenshots/bgremover_complete_20260528_214013/20_menu_file.png)

*Le menu « Fichier » regroupe Ouvrir (⌘O), « Fichiers récents »,
Enregistrer (⌘S) et Enregistrer sous… (⇧⌘S).*

**Les formats d'entrée pris en charge** sont, de manière contraignante, **PNG,
JPEG, WebP, TIFF, BMP et GIF**. Cette liste est le contrat d'entrée actuel, pas
un exemple : les autres formats sont rejetés de façon contrôlée. En particulier,
**HEIC/HEIF n'est actuellement pas pris en charge à dessein** — un fichier
HEIC/HEIF est rejeté comme format non pris en charge. L'enregistrement se fait
en PNG, JPEG, WebP ou TIFF (voir la [section 16](#16-enregistrer-et-exporter)).

> **Taille maximale de l'image : 40 mégapixels.** Les images plus grandes sont
> rejetées avec un message dans la barre d'état.

---

## 5. La barre d'outils (gauche)

La barre verticale sur le bord gauche contient, de haut en bas :

### Outils de sélection

| Icône | Outil | Fonction |
|---|---|---|
| 🪄 | **Baguette magique** | Sélectionne une zone continue de couleur similaire en un clic (remplissage par diffusion). Ajustable via la *Tolérance*. |
| 🖌 | **Pinceau** | Peindre une sélection manuellement. |
| 🧽 | **Gomme** | Supprimer la sélection peinte. |
| ⬡ | **Lasso polygonal** | Cliquez sur les points un par un ; **double-clic** ferme le polygone. **Échap** annule. |

Changement rapide au clavier : **W** baguette, **B** pinceau,
**E** gomme, **L** lasso.

Pour tous les outils de sélection :

- **Shift + clic** → **ajouter** à la sélection
- **Ctrl/Cmd + clic** → **soustraire** de la sélection

### Suppression d'arrière-plan par IA

| Icône | Fonction |
|---|---|
| ✨ | **IA** – supprime l'arrière-plan entièrement de façon automatique. Le modèle d'IA est chargé à la première utilisation, ce qui peut prendre un moment. |

> Si le composant IA (`rembg`) n'est pas installé, le bouton est grisé.
> Consultez le guide d'installation pour configurer la fonctionnalité IA.

### Historique

| Icône | Fonction |
|---|---|
| ↩ | **Annuler** (⌘Z) – revenir sur la dernière étape |
| ↪ | **Rétablir** (⇧⌘Z) – réappliquer l'étape annulée |
| ⟲ | **Restaurer l'original** – abandonner toutes les modifications |
| 🕘 | **Historique des modifications** – liste de toutes les étapes ; **double-clic** sur une entrée pour revenir à cet état |

![Fenêtre « Historique des modifications »](../../../app_screenshots/bgremover_complete_20260528_214013/40_popup_history.png)

*L'historique des modifications liste chaque étape ; un double-clic sur une
entrée revient exactement à cet état.*

### Fichier

| Icône | Fonction |
|---|---|
| 📂 | **Ouvrir une image** (⌘O) |
| 💾 | **Enregistrer l'image** (⌘S) |

> **Conseil :** Survolez une icône pour afficher une brève infobulle.

---

## 6. Faire une sélection

Presque toutes les modifications (rendre transparent, remplacer la couleur)
s'appliquent à la **zone actuellement sélectionnée**. La sélection est mise en
surbrillance en couleur sur l'image.

![Une image chargée avec une sélection active](../../../app_screenshots/bgremover_complete_20260528_214013/02_main_loaded_selection.png)

*Une image chargée avec une sélection active : la zone d'arrière-plan
sélectionnée est mise en surbrillance en couleur sur le canevas.*

### Avec la baguette magique (recommandé pour les arrière-plans unis)

1. Choisissez la baguette magique dans la barre d'outils.
2. Cliquez sur l'arrière-plan – toutes les couleurs similaires et contiguës
   sont sélectionnées.
3. Pas assez ? Utilisez **Shift+clic** pour ajouter d'autres zones ou
   augmentez la **Tolérance** (onglet *Sélection*).

### Avec le pinceau et la gomme (pour des corrections fines)

- **Pinceau :** peignez sur la zone souhaitée pour l'ajouter à la sélection.
- **Gomme :** peignez sur les zones incorrectement sélectionnées pour les
  supprimer.
- Réglez la **taille du pinceau** dans l'onglet *Sélection*.

### Avec le lasso polygonal (pour les bords droits)

1. Choisissez le lasso.
2. Cliquez coin par coin autour de l'objet.
3. **Double-clic** ferme le polygone et crée la sélection.
4. **Échap** annule l'opération.

---

## 7. Onglet « Sélection »

Le premier onglet d'édition du panneau droit contrôle le comportement de la
sélection ; il apparaît déjà dans la vue d'ensemble ci-dessus ([section 2](#2-la-fenêtre-de-lapplication-en-un-coup-dœil)) et dans la figure
de la [section 6](#6-faire-une-sélection).

### Indications sur les outils

En haut, les quatre outils de sélection sont répertoriés avec une brève
description et les touches modificatrices (Shift = ajouter,
Ctrl/Cmd = soustraire).

### Paramètres

| Curseur | Plage | Effet |
|---|---|---|
| **Tolérance (baguette magique)** | 0 – 255 (par défaut : 30) | Degré de similitude que doivent avoir les couleurs pour être sélectionnées ensemble. **Bas** = uniquement les couleurs très similaires · **Haut** = de nombreuses nuances. |
| **Taille du pinceau** | 4 – 200 px (par défaut : 30 px) | Diamètre du pinceau et de la gomme. |

### Actions de sélection

- **Désélectionner** – efface la sélection actuelle. **Échap** annule d'abord
  un recadrage actif ou un lasso polygonal commencé, puis efface la sélection
  uniquement si aucune de ces interactions n'est active.
- **Inverser la sélection** (⌘⇧I) – échange les zones sélectionnées et non
  sélectionnées. Utile : sélectionnez d'abord l'*objet*, puis inversez pour
  modifier l'*arrière-plan*.
- **Développer / Réduire** – agrandit ou réduit la sélection du rayon
  adjacent (1 – 20 px, par défaut : 2 px). Utile pour supprimer un fin liseré coloré après le
  détourage.

---

## 8. Onglet « Arrière-plan »

C'est ici que la sélection actuelle est réellement modifiée.

![L'onglet « Arrière-plan »](../../../app_screenshots/bgremover_complete_20260528_214013/11_tab_background.png)

*L'onglet « Arrière-plan » : « Supprimer (transparent) » rend la sélection
transparente ; le carré de couleur et « Remplacer la couleur » la remplissent
d'une couleur.*

| Action | Description |
|---|---|
| **Supprimer (transparent)** | Rend la zone sélectionnée complètement transparente. Conseil : sélectionnez d'abord l'arrière-plan avec la baguette magique. |
| **Choisir une couleur** | Ouvre un sélecteur de couleur. Le petit bouton coloré affiche la couleur de remplacement actuellement choisie. |
| **Remplacer la couleur** | Remplit la zone sélectionnée avec la couleur choisie. |

![Boîte de dialogue du sélecteur de couleur](../../../app_screenshots/bgremover_complete_20260528_214013/31_dialog_color_picker.png)

*« Choisir une couleur » ouvre le sélecteur de couleur ; la couleur choisie
apparaît dans le carré et s'applique à la sélection avec « Remplacer la
couleur ».*

**Flux de travail typique :** sélectionner l'arrière-plan avec la baguette
magique/l'IA → *Supprimer (transparent)* pour un PNG détouré, **ou** choisir
une couleur et *Remplacer la couleur* pour un arrière-plan uni (p. ex. blanc
pour des photos d'identité).

### Adoucir le bord (feather)

Dans la section *Adoucir le bord* du même onglet, vous pouvez adoucir le **bord
alpha** — utile contre les bordures dures à l'aspect « découpé » après une
suppression.

- **Rayon :** 0 – 20 px (par défaut : 2 px) règle la largeur de la transition
  douce.
- **Adoucir le bord** applique le lissage. Il n'affecte que le **canal de
  transparence** (les couleurs restent inchangées) et — lorsqu'une sélection est
  active — uniquement à l'intérieur de la sélection.

---

## 9. Onglet « Ajuster » – Correction des couleurs

L'onglet *Ajuster* contient une **correction des couleurs** simple. Elle agit
sur le **calque couleur actif** (voir la [section 13](#13-calques-et-projets))
et laisse la transparence inchangée.

| Curseur | Plage | Effet |
|---|---|---|
| **Luminosité** | 0 – 200 % (par défaut : 100 %) | Éclaircir ou assombrir l'image. |
| **Contraste** | 0 – 200 % (par défaut : 100 %) | Différence entre les zones claires et sombres. |
| **Saturation** | 0 – 200 % (par défaut : 100 %) | Intensité des couleurs ; 0 % donne des niveaux de gris. |

- Pendant que vous déplacez les curseurs, le canevas affiche un **aperçu en
  direct**.
- **Appliquer** valide la correction (annulable/rétablissable dans
  l'historique).
- **Réinitialiser** ramène les trois curseurs à 100 % et abandonne l'aperçu.

---

## 10. Onglet « Rotation/Miroir »

![L'onglet « Rotation/Miroir »](../../../app_screenshots/bgremover_complete_20260528_214013/12_tab_transform.png)

*L'onglet « Rotation/Miroir » avec la rotation rapide (90°/180°/270°), l'angle
libre et les boutons pour retourner horizontalement et verticalement.*

### Rotation

- **Rotation rapide :** boutons pour *90° gauche*, *90° droite*, *180°* et
  *270°*.
- **Angle libre :** curseur ou champ de saisie de **−180° à +180°**, puis
  cliquez sur **Appliquer l'angle**. Les angles obliques produisent des coins
  transparents.

### Miroir

- **Horizontal** – retourner gauche ↔ droite.
- **Vertical** – retourner haut ↕ bas.

> La rotation rapide est également disponible via le clavier : ⌘← (90°
> gauche) et ⌘→ (90° droite). Tout en bas de l'onglet, **Redimensionner…**
> mène à la boîte de dialogue de la [section 12](#12-redimensionner-et-dimensions-physiques).

---

## 11. Onglet « Forme » – Coins et recadrage

![L'onglet « Forme »](../../../app_screenshots/bgremover_complete_20260528_214013/13_tab_shape_crop.png)

*L'onglet « Forme » : en haut « Arrondir les coins » avec le curseur de rayon ;
en dessous, les formats de recadrage (spéciaux, paysage et portrait).*

### Arrondir les coins

1. Utilisez le curseur **Rayon** pour régler l'arrondi (0 = pas d'arrondi,
   jusqu'à 500 px = maximum).
2. Cliquez sur **Arrondir les coins**.

Le résultat est enregistré avec des coins transparents — de préférence en PNG.

### Format de sortie et recadrage

1. Choisissez un format – un **cadre** apparaît sur l'image :
   - **Formats spéciaux :** ⬤ Cercle, ■ 1:1 (carré)
   - **Paysage :** 16:9, 4:3, 3:2, 2:1, 7:4.5 (14:9)
   - **Portrait :** 9:16, 3:4
2. **Déplacer le cadre :** cliquez au centre et faites glisser.
3. **Redimensionner :** faites glisser les coins – le rapport d'aspect est
   préservé.
4. Une barre apparaît au-dessus du canevas :
   - **✓ Appliquer le recadrage** – recadre l'image.
   - **✗ Annuler** – abandonne le cadre.

![Recadrage circulaire actif avec barre de confirmation](../../../app_screenshots/bgremover_complete_20260528_214013/61_crop_circle_overlay.png)

*Exemple « Cercle » : le cadre de recadrage se place sur l'image avec des
poignées. « ✓ Appliquer le recadrage » recadre l'image, « ✗ Annuler » abandonne
le cadre.*

---

## 12. Redimensionner et dimensions physiques

Via `Édition → Redimensionner…` (Ctrl+R) ou le bouton **Redimensionner…** de
l'onglet *Rotation/Miroir*, vous mettez l'image à l'échelle d'une nouvelle
taille cible. La boîte de dialogue propose deux unités :

### Redimensionner en pixels

En mode **Pixels**, vous saisissez la **Largeur** et la **Hauteur** directement
en pixels. Avec **Lier le rapport d'aspect**, le rapport est préservé. La
méthode de rééchantillonnage détermine la qualité :

| Méthode | Adaptée à |
|---|---|
| **Lanczos** | Meilleure qualité (par défaut), idéale pour réduire. |
| **Bicubique** | Résultats lisses, bon polyvalent. |
| **Bilinéaire** | Plus rapide, un peu plus doux. |
| **Plus proche voisin** | Conserve les bords/pixels nets, sans lissage. |

La boîte de dialogue affiche le nombre de mégapixels obtenu et respecte la
limite de **40 mégapixels**.

### Dimensions physiques (mm/DPI) et zone d'impression

En mode **Millimètres (mm + DPI)**, vous définissez la **largeur/hauteur en
millimètres** et une **résolution (DPI)** ; la taille en pixels en découle.
Cette taille physique est la taille d'impression de référence et est enregistrée
dans le projet `.bgrproj`.

Via **Support cible**, vous choisissez un support d'impression courant (p. ex.
A4 ou A3). Si le motif y tient, la boîte de dialogue le confirme ; s'il est plus
grand que le support, une indication signale que la zone d'impression est
dépassée.

---

## 13. Calques et projets

BgRemover peut gérer plusieurs **calques** dans un **projet** et enregistrer
l'ensemble en tant que fichier `.bgrproj`. Pour l'édition d'arrière-plan
classique, vous n'avez pas à vous en soucier — une seule image se comporte comme
un unique calque couleur.

### Types et rôles de calque

Chaque calque a un **type** et, éventuellement, un **rôle**. Seuls les **calques
couleur** alimentent l'image couleur visible ; les autres types sont des calques
de données pour la préparation de l'impression.

| Type / rôle | Signification |
|---|---|
| **Couleur** (motif couleur) | L'image visible. Plusieurs calques couleur forment ensemble le composite, qui est aussi exporté. |
| **Hauteur** (carte de hauteur) | Une carte de hauteur en niveaux de gris pour le relief/l'impression UV (voir la [section 14](#14-espace-de-travail-des-cartes-de-hauteur)). |
| **Brillance** (masque de brillance) | Un masque pour les effets de brillance (expérimental). |
| **Générique** | Un calque de données neutre sans rôle fixe. |

### L'onglet « Calques »

Dans l'onglet *Calques*, vous gérez la liste des calques :

| Action | Description |
|---|---|
| **Nouveau calque / Dupliquer / Supprimer** | Ajouter un calque, copier le calque actif ou le supprimer. |
| **Monter / Descendre** | Modifier l'ordre d'empilement des calques. |
| **Renommer** | Renommer le calque actif. |
| **Rôle** | Attribuer un rôle au calque actif (seules les combinaisons compatibles sont autorisées). |
| **Visibilité** | Afficher ou masquer un calque. |
| **Sélectionner** | Choisir un calque comme calque **actif** – les outils agissent dessus. |
| **Opacité** | Opacité du calque (appliquée au relâchement). |

### Fichiers de projet (.bgrproj)

Via le menu **Projet**, vous travaillez avec des fichiers de projet :

- **Nouveau projet** (Ctrl+N), **Ouvrir un projet…** (Ctrl+Maj+O).
- **Enregistrer le projet** (Ctrl+Alt+S) et **Enregistrer le projet sous…**
  (Ctrl+Alt+Maj+S).

Un fichier `.bgrproj` est une archive comprenant un **manifeste** (ordre, types,
rôles, noms, dimensions physiques) et **un PNG par calque**. Ainsi, tous les
calques sont conservés sans perte, transparence comprise. Les projets
apparaissent aussi sous « Fichiers récents » (voir la [section 4](#4-ouvrir-une-image)).

---

## 14. Espace de travail des cartes de hauteur

Une **carte de hauteur** est un calque en niveaux de gris où la luminosité
représente une hauteur : **clair = haut, sombre = bas**. Elle est la base du
relief et de l'impression UV. L'onglet *Hauteur* est divisé en trois sections et
travaille sur le **calque de hauteur** actif ; les fonctions d'édition et
d'optimisation ne sont actives que lorsqu'un calque de hauteur est actif.

### Obtenir

- **Générer depuis l'image** – convertit de façon déterministe l'image couleur
  actuelle en carte de hauteur et la crée comme nouveau calque de hauteur.
- **Importer des niveaux de gris…** – charge une image en niveaux de gris comme
  carte de hauteur et la met à l'échelle de la taille du projet.

### Modifier

- **Éclaircir / Assombrir** – augmente ou diminue la hauteur ; l'**Intensité**
  contrôle l'ampleur.
- **Définir la hauteur** – fixe la hauteur à une **valeur** déterminée.
- **Inverser** – échange haut et bas.

Lorsqu'une sélection est active, ces actions n'agissent qu'à l'intérieur de la
sélection, sinon sur tout le calque.

### Optimiser

Les opérations d'optimisation affichent un **aperçu en direct** ; **Appliquer**
valide (annulable/rétablissable), **Abandonner l'aperçu** l'abandonne.

| Opération | Effet |
|---|---|
| **Niveaux (noir/blanc)** | Définir le point noir et blanc de la hauteur. |
| **Gamma** | Tirer les hauteurs moyennes vers le clair/sombre. |
| **Flou gaussien (rayon)** | Lissage doux et uniforme. |
| **Flou médian (rayon)** | Lisse tout en préservant les bords. |
| **Seuil** | Diviser la hauteur en deux niveaux. |
| **Paliers** | Quantifier la hauteur en un nombre de niveaux. |
| **Plage (min/max)** | Limiter la hauteur à une plage de valeurs. |

---

## 15. Aperçu 2D (couleur, relief, hauteur, brillance)

L'**aperçu 2D** montre différentes vues du même motif directement sur le
canevas. C'est un **affichage à l'écran pur** qui ne modifie ni l'image ni
l'export. Choisissez le mode dans l'onglet *Aperçu* ou via
`Affichage → Mode d'aperçu`.

| Mode | Affichage |
|---|---|
| **Couleur** | L'image couleur normale. |
| **Relief sur couleur** | Un relief ombré issu de la carte de hauteur, multiplié par-dessus l'image couleur. |
| **Hauteur (niveaux de gris)** | La carte de hauteur en image en niveaux de gris. |
| **Brillance** | Le masque de brillance sous forme de reflet satiné. |
| **Combiné** | Couleur, relief et brillance ensemble. |

- Avec **Intensité du relief**, vous réglez l'intensité du relief ; à 0 %, le
  relief est ignoré.
- **Afficher la brillance** active ou désactive le calque de brillance.

L'onglet d'aperçu et le sous-menu Affichage restent synchronisés. Les calques de
données masqués sont ignorés dans l'aperçu.

---

## 16. Enregistrer et exporter

- **Enregistrer :** `Fichier → Enregistrer` (⌘S / Ctrl+S)
- **Enregistrer sous… :** `Fichier → Enregistrer sous…` (⇧⌘S)

À l'enregistrement, c'est toujours le **composite couleur** qui est écrit (quel
que soit le calque actif ou le mode d'aperçu défini). Choisissez le **format de
fichier** souhaité dans la boîte de dialogue :

| Format | Propriétés | Recommandation |
|---|---|---|
| **PNG** | Avec transparence | Pour les objets détourés – **recommandation par défaut** |
| **JPEG** | Sans canal alpha ; les zones transparentes deviennent blanches | Pour les photos avec arrière-plan opaque |
| **WebP** | Format web moderne, transparence prise en charge | Pour une utilisation sur le web |
| **TIFF** | Sans perte, transparence prise en charge | Pour l'archivage/l'impression |

> Pour conserver le détourage, **choisissez toujours PNG, WebP ou TIFF** —
> JPEG remplit les zones transparentes de blanc.

### Exporter pour EufyMake Studio

Via `Projet → Exporter des assets pour EufyMake Studio…` (Ctrl+Alt+E), BgRemover
écrit des **assets d'import** pour EufyMake Studio – **pas** un fichier `.empf`
fini :

- **Motif couleur** (obligatoire) en PNG RGBA – à partir d'un calque ayant le rôle
  *Motif couleur*, ou du composite couleur si aucun n'existe.
- **Carte de hauteur** (facultative) en niveaux de gris avec **clair = haut,
  sombre = bas** – disponible uniquement lorsqu'un calque porte le rôle *Carte de
  hauteur* (p. ex. un calque de hauteur créé via « Générer depuis l'image » ; un
  simple calque de hauteur sans ce rôle n'est pas exporté).
- **Masque de brillance** (facultatif, expérimental) comme asset auxiliaire –
  disponible uniquement lorsqu'un calque porte le rôle *Brillance*.

Dans la boîte de dialogue, vous choisissez le dossier d'export, les assets
facultatifs et la **profondeur de bits** de la carte de hauteur (8 bits par
défaut, 16 bits expérimental). Une **vérification de pré-export** s'exécute en
continu et signale les constats par gravité :

- **Erreurs** (⛔) bloquent l'export jusqu'à correction – p. ex. un motif couleur
  manquant ou des tailles non concordantes.
- **Avertissements** (⚠️) doivent être confirmés délibérément – p. ex. des
  données de hauteur/brillance vides ou la sortie 16 bits non confirmée.

Ensuite, vous importez et positionnez les assets dans EufyMake Studio, y
attribuez les modes d'encre/calques et enregistrez le projet Studio lui-même en
`.empf`.

---

## 17. Paramètres

Via `Extras → Paramètres…` (⌘, / Ctrl+,), vous pouvez gérer les paramètres
suivants :

![La boîte de dialogue des paramètres](../../../app_screenshots/bgremover_complete_20260528_214013/30_dialog_settings.png)

*La boîte de dialogue des paramètres : langue, répertoires d'ouverture et
d'enregistrement par défaut, format d'image préféré et chemin du fichier journal
avec le bouton « Ouvrir le dossier ».*

| Paramètre | Description |
|---|---|
| **Répertoire d'ouverture par défaut** | Dossier de départ de la boîte de dialogue d'ouverture (vide = dernier utilisé) |
| **Répertoire d'export/enregistrement par défaut** | Dossier de départ de la boîte de dialogue d'enregistrement (vide = dernier utilisé) |
| **Format d'image préféré** | PNG, JPEG, WebP ou TIFF – apparaît comme première option dans la boîte de dialogue d'enregistrement |
| **Langue** | Allemand ou anglais ; le changement s'applique après un redémarrage |
| **Fichier journal** | Affiche le chemin du fichier journal ; le bouton « Ouvrir le dossier » ouvre le répertoire dans le gestionnaire de fichiers |

Les répertoires, le format préféré et la langue sont mémorisés entre les
redémarrages de l'application.

---

## 18. Raccourcis clavier

Sur macOS, la touche modificatrice est **⌘ (Cmd)**, sur Linux/Windows
**Ctrl**.

| Action | Raccourci |
|---|---|
| Sélectionner la baguette magique | W |
| Sélectionner le pinceau | B |
| Sélectionner la gomme | E |
| Sélectionner le lasso polygonal | L |
| Ouvrir une image | ⌘O |
| Enregistrer l'image | ⌘S |
| Enregistrer l'image sous… | ⇧⌘S |
| Nouveau projet | ⌘N |
| Ouvrir un projet… | ⇧⌘O |
| Enregistrer le projet | ⌥⌘S |
| Enregistrer le projet sous… | ⇧⌥⌘S |
| Exporter des assets pour EufyMake Studio… | ⌥⌘E |
| Annuler | ⌘Z |
| Rétablir | ⇧⌘Z |
| Redimensionner… | ⌘R |
| Rotation 90° gauche | ⌘← |
| Rotation 90° droite | ⌘→ |
| Désélectionner (sans recadrage/lasso actif) | Échap |
| Inverser la sélection | ⌘⇧I |
| Ajuster à la vue | ⌘0 |
| Ouvrir les paramètres | ⌘, |

---

## 19. Flux de travail typiques

### A) Détourer une photo de produit (arrière-plan transparent)

1. Ouvrez l'image.
2. Cliquez sur **IA** dans la barre d'outils.
3. Affinez les bords avec la **gomme**/**pinceau**.
4. Dans l'onglet *Sélection*, appliquez éventuellement **Réduire** (1–2 px)
   pour supprimer le liseré coloré.
5. Enregistrez en **PNG**.

### B) Photo d'identité avec fond blanc

1. Ouvrez l'image.
2. Cliquez avec la **baguette magique** sur l'arrière-plan (ajustez la
   tolérance).
3. Onglet *Arrière-plan* → **Choisir une couleur** (blanc) →
   **Remplacer la couleur**.
4. Onglet *Forme* → choisissez le format **1:1**, positionnez le cadre,
   cliquez sur **✓ Appliquer le recadrage**.
5. Enregistrez en **JPEG** ou **PNG**.

### C) Photo de profil ronde

1. Ouvrez l'image.
2. Supprimez l'arrière-plan avec **l'IA** (facultatif).
3. Onglet *Forme* → choisissez **⬤ Cercle**, faites glisser le cadre sur le
   visage.
4. Cliquez sur **✓ Appliquer le recadrage**.
5. Enregistrez en **PNG** (transparent en dehors du cercle).

### D) Conserver l'objet, remplacer uniquement l'arrière-plan

1. Ouvrez l'image, cliquez avec la **baguette magique** sur l'**objet**.
2. Onglet *Sélection* → **Inverser la sélection** (⌘⇧I) → l'arrière-plan
   est maintenant sélectionné.
3. Onglet *Arrière-plan* → choisissez une couleur → **Remplacer la couleur**.
4. Enregistrez.

### E) Asset de relief de hauteur pour EufyMake Studio

1. Ouvrez et détourez l'image.
2. Onglet *Hauteur* → **Générer depuis l'image**.
3. Affinez la hauteur dans la section *Optimiser* (p. ex. *Niveaux*, *Flou*) et
   cliquez sur **Appliquer**.
4. Dans l'*aperçu 2D*, choisissez le mode **Relief sur couleur** ou **Combiné**
   pour vérifier.
5. `Projet → Exporter des assets pour EufyMake Studio…`, vérifiez les constats
   et exportez.

---

## 20. Conseils et astuces

- **D'abord grossier, puis fin :** détourez grossièrement avec l'IA ou la
  baguette magique, puis corrigez avec le pinceau/la gomme.
- **Ajustez la tolérance :** si trop est sélectionné → réduisez la tolérance.
  Si trop peu → augmentez la tolérance ou utilisez Shift+clic.
- **Supprimer le liseré :** après le détourage, appliquez « Réduire » de
  1–2 px dans l'onglet *Sélection* avant de supprimer l'arrière-plan.
- **Bords doux :** avec *Adoucir le bord* (onglet *Arrière-plan*), les bordures
  détourées paraissent moins dures.
- **Reculer :** chaque étape est enregistrée dans l'historique — double-cliquez
  sur n'importe quelle entrée de l'**Historique des modifications** (🕘) pour
  revenir à cet état.
- **Bloqué ?** **Restaurer l'original** réinitialise l'image à son état de
  chargement.

---

## 21. Limitations connues

- **Taille maximale de l'image : 40 mégapixels.** Les images plus grandes sont
  rejetées.
- **Formats d'entrée :** PNG, JPEG, WebP, TIFF, BMP et GIF sont pris en charge.
  **HEIC/HEIF n'est actuellement pas pris en charge** et est rejeté de façon
  contrôlée.
- La **fonctionnalité IA** nécessite le composant facultatif `rembg`. Sans lui,
  le bouton IA est désactivé ; tous les outils manuels continuent de
  fonctionner.
- L'**aperçu 2D** est un affichage à l'écran pur ; l'export d'image écrit sans
  changement le composite couleur.
- L'**export EufyMake** ne produit que des assets d'import, **pas** un fichier
  `.empf` natif ; la sortie de hauteur 16 bits est expérimentale.
- Le **bundle d'application** (`BgRemover.app`) est spécifique à macOS ; sous
  Linux, l'application est lancée directement. Windows ne fait actuellement
  pas partie de la matrice officiellement testée.

---

## 22. Résolution de problèmes et fichier journal

En cas de problème, consultez le **fichier journal** interne
`bgremover.log`. Il est stocké dans le répertoire de données déterminé par Qt
et créé lors de la première entrée de journal. Le chemin exact peut varier
selon la plateforme et la configuration de Qt :

- **macOS (configuration actuelle) :**
  `~/Library/Application Support/BgRemover/BgRemover/bgremover.log`
- **Linux :** sous `~/.local/share/`

Le lanceur du bundle d'application macOS écrit en plus ses diagnostics de
démarrage dans `~/Library/Application Support/BgRemover/bgremover.log`.

Le fichier interne contient des messages d'exécution et des détails sur les
erreurs (traces de pile) et constitue le premier point de contact pour les
demandes d'assistance.

Le moyen le plus simple de trouver le fichier est via
`Extras → Paramètres… → Fichier journal` : le chemin complet y est affiché,
et le bouton **« Ouvrir le dossier »** ouvre le répertoire directement dans le
gestionnaire de fichiers — idéal pour joindre le fichier journal à un e-mail
d'assistance.

| Problème | Solution possible |
|---|---|
| Bouton IA grisé | `rembg` n'est pas installé – consultez le guide d'installation |
| L'image ne peut pas être ouverte | Plus de 40 mégapixels ? Format pris en charge (pas de HEIC/HEIF) ? Lisez la barre d'état |
| L'IA prend très longtemps | Le premier appel charge le modèle – une seule fois, plus rapide ensuite |
| Transparence perdue après enregistrement | Enregistré en JPEG → choisissez PNG/WebP/TIFF à la place |
| Le projet ne peut pas être ouvert | Fichier `.bgrproj` endommagé/incomplet ? Lisez la barre d'état |

---

## 23. Licence

BgRemover est distribué sous la **Licence Publique Générale GNU v3.0 ou
ultérieure** (`GPL-3.0-or-later`) – consultez [LICENSE](../../../LICENSE). Une
liste complète de toutes les bibliothèques utilisées et de leurs licences se
trouve dans [RESOURCES.md](RESOURCES.md).

---

*Ce guide fait partie du projet BgRemover. Pour toute question ou suggestion,
veuillez ouvrir un ticket dans le dépôt GitHub.*
