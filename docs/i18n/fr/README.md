[Deutsch](../../../README.md) · [English](../en/README.md) · [Español](../es/README.md) · **Français** · [Українська](../uk/README.md) · [简体中文](../zh/README.md)

# BgRemover

Un outil de retouche d'image pour macOS permettant de **supprimer, remplacer et modifier les arrière-plans** — avec détourage automatique basé sur l'IA, sélection à la baguette magique, pinceau/gomme, recadrage dans différents formats, rotation, miroir et arrondi des coins.

## Fonctionnalités

- **🤖 Suppression d'arrière-plan par IA** via [rembg](https://github.com/danielgatis/rembg) – un clic, et c'est terminé.
- **🪄 Baguette magique** – sélectionne les zones de couleur contiguës par remplissage par diffusion (flood-fill), avec curseur de tolérance.
- **🖌 Pinceau / gomme** – dessiner ou effacer la sélection manuellement.
- **🎨 Remplacer l'arrière-plan** – remplir la sélection avec une couleur quelconque ou la rendre transparente.
- **✂ Recadrage** avec grille des tiers : cercle, 1:1, 16:9, 4:3, 3:2, 2:1, 14:9, 9:16, 3:4.
- **⟲ Rotation** par pas de 90° ou selon un angle quelconque ; **↔ Miroir** horizontal/vertical.
- **⬤ Arrondir les coins** avec un rayon réglable.
- **↩ Historique** avec annulation et retour à n'importe quelle étape antérieure.
- **📥 Glisser-déposer** des images directement sur la fenêtre.
- Enregistrement en **PNG** (avec transparence), **JPEG** (sur fond blanc), **WebP** ou **TIFF**.
- **⚙ Paramètres persistants** – les répertoires par défaut et le format de fichier préféré restent enregistrés.

## Captures d'écran

<!--
  Avant la publication, placer une capture d'écran/un GIF sous docs/screenshot.png
  et décommenter la ligne suivante (l'espace réservé n'affiche
  volontairement pas d'image cassée tant que le fichier est absent) :

![BgRemover – fenêtre principale](../../screenshot.png)
-->

> _Capture d'écran à venir._ Une image de la fenêtre principale (barre d'outils, canevas avec
> sélection, panneau d'onglets de droite) a sa place ici avant la publication —
> chemin recommandé `docs/screenshot.png`.

## Prérequis

- **macOS** (le bundle d'application fourni utilise des outils spécifiques à macOS comme `iconutil`)
- **Python 3.10 ou plus récent** (le code utilise des annotations de type PEP 604
  comme `QThread | None` directement dans les signatures — Python 3.9 échoue)
- Les dépendances (`PyQt6`, `Pillow`, `numpy`, et facultativement `rembg` pour la
  fonction d'IA) sont installées via `pyproject.toml`.

## Installation

**Recommandé (macOS) : construire le bundle d'application.** Le script crée automatiquement
un venv isolé, installe toutes les dépendances (y compris
`onnxruntime` pour l'IA), gère correctement Apple Silicon et produit
un `BgRemover.app` autonome :

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

Confirmer avec **Entrée** lors de l'invite relative au venv. Ensuite, lancer `BgRemover.app`
(sous `~/Applications`) par double-clic — fonctionnellement identique au
**`BgRemover.command`** fourni. Le projet peut rester dans
`~/Documents` (l'application est construite de façon autonome).

**Sinon, directement dans le terminal** — sur macOS moderne dans un venv,
car le Python système bloque `pip install` selon le PEP 668 :

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -e ".[ai]"
python3 -m bgremover
```

`.[ai]` entraîne l'installation des dépendances d'IA (`rembg[cpu]` y compris `onnxruntime`) ;
sans la fonction d'IA, `python3 -m pip install -e .` suffit.

**Linux :** il n'y a pas de bundle d'application ; l'application fonctionne via le
lancement direct depuis un venv :

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -e ".[ai]"
python3 -m bgremover
```

Au préalable, quelques bibliothèques système Qt sont nécessaires — voir les
détails dans **[INSTALL_LINUX.md](INSTALL_LINUX.md)**.

Sur **Raspberry Pi OS (Desktop)**, c'est particulièrement simple — sans aucun
venv/pip (PyQt6, Pillow, numpy en tant que paquets système via `apt`) ; voir la
section Raspberry Pi dans **[INSTALL_LINUX.md](INSTALL_LINUX.md)**.

> Des instructions détaillées — y compris l'**installation depuis une branche**
> (pour tester des pull requests ouvertes) et le **dépannage** — figurent dans
> **[INSTALL_MAC.md](INSTALL_MAC.md)** (macOS) ou
> **[INSTALL_LINUX.md](INSTALL_LINUX.md)** (Linux).

## Utilisation

1. **Ouvrir une image** via `Fichier → Ouvrir` (⌘O) ou par glisser-déposer dans la fenêtre.
2. **Effectuer une sélection** avec la baguette magique, le pinceau ou la gomme (onglet *🎯 Sélection*).
   - `Maj+Clic` ajoute à la sélection, `Ctrl+Clic` retire.
3. **Modifier l'arrière-plan** (onglet *🖼 Arr.-plan*) : le rendre transparent ou remplacer la couleur — ou directement l'**IA** dans la barre d'outils.
4. **Transformer l'image** (onglet *⟲ Trans.*) : pivoter, mettre en miroir.
5. **Forme et recadrage** (onglet *⬤ Forme*) : arrondir les coins ou recadrer au format — déplacer/redimensionner le cadre, puis ✓ Appliquer.
6. **Enregistrer** via `Fichier → Enregistrer` (⌘S) en PNG, JPEG, WebP ou TIFF.

### Paramètres

Via `Outils → Paramètres…` (⌘,), trois préférences utilisateur peuvent être enregistrées de façon permanente :

| Paramètre | Description |
|---|---|
| Répertoire par défaut pour l'ouverture | Répertoire de départ de la boîte de dialogue d'ouverture ; vide = dernier répertoire utilisé |
| Répertoire par défaut pour l'export/l'enregistrement | Répertoire de départ de la boîte de dialogue d'enregistrement ; vide = dernier répertoire utilisé |
| Format de fichier image préféré | PNG, JPEG, WebP ou TIFF – apparaît comme première option dans la boîte de dialogue d'enregistrement |

Les paramètres sont enregistrés de façon persistante via **QSettings** et automatiquement restaurés au prochain démarrage du programme.

### Raccourcis clavier

| Action | Raccourci |
|--------|----------|
| Ouvrir une image | ⌘O |
| Enregistrer l'image | ⌘S |
| Enregistrer l'image sous… | ⇧⌘S |
| Annuler | ⌘Z |
| Rétablir | ⇧⌘Z |
| Pivoter de 90° à gauche | ⌘← |
| Pivoter de 90° à droite | ⌘→ |
| Désélectionner | Esc |
| Inverser la sélection | ⌘⇧I |
| Fit to View | ⌘0 |
| Ouvrir les paramètres | ⌘, |

Le menu Fichier comporte en outre un sous-menu **« Récemment ouverts »** avec
les 10 dernières images chargées — l'état est persisté avec les
autres paramètres via QSettings.

## Développement et tests

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv
source .venv/bin/activate
make pr-check
```

La suite de tests s'exécute en mode headless (plateforme Qt `offscreen`) et vérifie les
opérations sur l'image, la géométrie de recadrage et la logique d'enregistrement. Les pull
requests lancent une CI GitHub légère (Ubuntu, Python 3.12, `make pr-check`).
La matrice complète Linux/macOS sous Python 3.10 et 3.12 s'exécute lors
de la publication d'une release ou manuellement. Voir
[TESTING.md](../../../TESTING.md) pour le flux complet de tests.

Vérification du style de code et contrôle de typage statique :

```bash
make lint
make type
```

## Architecture (aperçu rapide)

Depuis le tour 5, BgRemover est un paquet installable (`bgremover/`,
lancé via `python -m bgremover` ou le script de console `bgremover`) :

- **`ImageCanvas`** (QGraphicsView) gère l'état de l'image, le masque de sélection,
  les piles d'annulation/rétablissement et les outils (baguette magique, pinceau, lasso, recadrage).
- **`MainWindow`** construit la barre d'outils, le panneau d'onglets de droite (quatre constructeurs `_build_tab_*`),
  le menu et relie le tout au canevas.
- Les **workers** (`ImageLoadWorker`, `AIWorker`, `RembgWarmupWorker`) s'exécutent dans
  leurs propres `QThread` ; `_launch_worker()` encapsule le cycle de vie du thread.
- Un **compteur de version** monotone dans le canevas rejette les résultats d'IA obsolètes,
  si une autre image a été chargée entre-temps.
- La pile d'annulation n'est pas limitée par `maxlen`, mais par une
  **limite de mémoire** (`_UNDO_MEMORY_LIMIT`) ; une somme courante
  d'octets évince les entrées les plus anciennes.

## Limitations connues

- **Taille d'image maximale : 40 mégapixels.** Les images plus grandes sont refusées avec un
  message d'état. La sélection à la baguette magique (flood-fill) s'exécute
  de façon synchrone dans le thread d'interface ; au-delà de cette limite, même la
  variante vectorisée provoquerait un retard perceptible. Pillow est en outre protégé contre
  les images de type « bombe de décompression ».
- La **construction du bundle d'application** est spécifique à macOS ; sous Linux/Windows
  l'application fonctionne via le lancement direct `python -m bgremover`.

## Fichier journal

Au démarrage du programme, un fichier journal `bgremover.log` est créé dans le
répertoire de données d'application spécifique à la plateforme
(macOS : `~/Library/Application Support/BgRemover/`,
Linux : `~/.local/share/BgRemover/`). Il contient les traces d'appels et les
messages d'état et constitue le premier point de contact en cas de problème.

## Licence

BgRemover est sous la **GNU General Public License v3.0 ou
ultérieure** (`GPL-3.0-or-later`) — voir [LICENSE](../../../LICENSE).

Une liste complète de toutes les bibliothèques, outils et assets utilisés
ainsi que de leurs licences figure dans **[RESOURCES.md](RESOURCES.md)**.

> **Remarque concernant PyQt6 :** la dépendance d'interface PyQt6 (Riverbank) est
> elle-même sous licence GPL v3 (ou commerciale). La GPL-3.0 a été
> choisie délibérément afin que l'application distribuée — en particulier le
> `BgRemover.app` empaqueté — soit conforme à la licence. Pour viser un
> modèle permissif (MIT/Apache-2.0), il faudrait remplacer PyQt6 par
> **PySide6** sous licence LGPL.
