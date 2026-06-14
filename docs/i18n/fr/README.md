[Deutsch](../../../README.md) · [English](../en/README.md) · [Español](../es/README.md) · **Français** · [Українська](../uk/README.md) · [简体中文](../zh/README.md)

# BgRemover

Un outil de retouche d'image pour macOS et Linux permettant de **supprimer, remplacer et modifier les arrière-plans** — avec détourage automatique basé sur l'IA, sélection à la baguette magique, pinceau/gomme, lasso polygonal, recadrage dans différents formats, rotation, miroir et arrondi des coins.

## Fonctionnalités

- **🤖 Suppression d'arrière-plan par IA** via [rembg](https://github.com/danielgatis/rembg) – un clic, et c'est terminé.
- **🪄 Baguette magique** – sélectionne les zones de couleur contiguës par remplissage par diffusion (flood-fill), avec curseur de tolérance.
- **🖌 Pinceau / gomme** – dessiner ou effacer la sélection manuellement.
- **➰ Lasso polygonal** – délimiter précisément la sélection en plaçant des sommets.
- **🎨 Remplacer l'arrière-plan** – remplir la sélection avec une couleur quelconque ou la rendre transparente.
- **✂ Recadrage** avec grille des tiers : cercle, 1:1, 16:9, 4:3, 3:2, 2:1, 14:9, 9:16, 3:4.
- **⟲ Rotation** par pas de 90° ou selon un angle quelconque ; **↔ Miroir** horizontal/vertical.
- **⬤ Arrondir les coins** avec un rayon réglable.
- **↩ Historique** avec annulation et retour à n'importe quelle étape antérieure.
- **📥 Glisser-déposer** des images directement sur la fenêtre.
- Enregistrement en **PNG** (avec transparence), **JPEG** (sur fond blanc), **WebP** ou **TIFF**.
- **⚙ Paramètres persistants** – les répertoires par défaut et le format de fichier préféré restent enregistrés ; le fichier journal peut être localisé depuis les paramètres et son dossier peut être ouvert.

## Captures d'écran

![BgRemover – fenêtre principale](../../screenshot.png)

## Prérequis

- **macOS** ou un **environnement de bureau Linux** (le bundle
  d'application facultatif utilise des outils spécifiques à macOS comme `iconutil`)
- **Python 3.10 ou plus récent** (le code utilise des annotations de type PEP 604
  comme `QThread | None` directement dans les signatures — Python 3.9 échoue)
- Les dépendances (`PyQt6`, `Pillow`, `numpy`, et facultativement `rembg` pour la
  fonction d'IA) sont installées via `pyproject.toml`.

**Python 3.11 ou plus récent** est recommandé pour le snapshot IA/app
reproductible : certaines dépendances transitives actuelles de l'IA ne
sont plus disponibles sous Python 3.10. L'application de base sans IA
continue de prendre en charge Python 3.10.

## Installation

**Recommandé (macOS) : construire le bundle d'application.** Le script crée automatiquement
un venv isolé pour l'application, tente d'installer les dépendances d'IA
y compris `onnxruntime`, gère correctement Apple Silicon et produit un
lanceur `BgRemover.app` :

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

Si le venv de l'application est créé, confirmer l'invite avec **Entrée**.
Ensuite, lancer `BgRemover.app` (sous `~/Applications`) par double-clic —
fonctionnellement identique au **`BgRemover.command`** fourni. Le lanceur
utilise le venv installé séparément sous
`~/Library/Application Support/BgRemover/venv`, le projet peut donc rester
dans `~/Documents`. L'application et son venv vont toutefois de pair :
le fichier `.app` n'est pas portable à lui seul. Si l'installation des
dépendances d'IA échoue, le script construit une application utilisable
sans IA.

Après une mise à jour ou un changement de branche, relancer
`bash create_BgRemover_app.sh`. Le script réinstalle le checkout actuel
de façon non éditable par-dessus le venv existant de l'application et
reconstruit le lanceur.

**Sinon, directement dans le terminal** — sur macOS moderne dans un venv,
car le Python système bloque `pip install` selon le PEP 668 :

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

`.[ai]` entraîne l'installation des dépendances d'IA (`rembg[cpu]` y compris `onnxruntime`) ;
sans la fonction d'IA, `python3 -m pip install -c requirements/constraints.txt -e .` suffit.

**Linux :** Pour les utilisateurs finaux, les artefacts de release sont
recommandés : une **AppImage** portable et un **`.deb`** installable (tous deux
pour x86_64 et aarch64/Raspberry Pi OS). Consultez
**[INSTALL_LINUX.md](INSTALL_LINUX.md)** pour l'installation et
**[packaging/linux/README.md](../../../packaging/linux/README.md)** pour les
détails de build/paquetage. De tels artefacts sont disponibles à partir de
**v2.3.0** — d'ici là, utilisez la voie venv ci-dessous.

Le lancement direct depuis un venv reste la meilleure voie pour le
développement, les tests de branches et les changements locaux :

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

Avant le lancement depuis le venv, quelques bibliothèques système Qt sont
nécessaires — voir **[INSTALL_LINUX.md](INSTALL_LINUX.md)**. Sur
**Raspberry Pi OS (Desktop)**, c'est aussi possible sans venv/pip (PyQt6,
Pillow, numpy en paquets système via `apt`) ; voir également
**[INSTALL_LINUX.md](INSTALL_LINUX.md)**.

> Des instructions détaillées — y compris l'**installation depuis une branche**
> (pour tester des pull requests ouvertes) et le **dépannage** — figurent dans
> **[INSTALL_MAC.md](INSTALL_MAC.md)** (macOS) ou
> **[INSTALL_LINUX.md](INSTALL_LINUX.md)** (Linux).

## Utilisation

1. **Ouvrir une image** via `Fichier → Ouvrir` (⌘O) ou par glisser-déposer dans la fenêtre.
2. **Effectuer une sélection** avec la baguette magique, le pinceau, la gomme ou le lasso polygonal (onglet *🎯 Sélection*).
   - `Maj+Clic` ajoute à la sélection ; `⌘+Clic` (macOS) ou `Ctrl+Clic` (Linux) retire.
   - Changer d'outil au clavier : `W` baguette, `B` pinceau, `E` gomme, `L` lasso.
3. **Modifier l'arrière-plan** (onglet *🖼 Arr.-plan*) : le rendre transparent ou remplacer la couleur — ou directement l'**IA** dans la barre d'outils.
4. **Transformer l'image** (onglet *⟲ Trans.*) : pivoter, mettre en miroir.
5. **Forme et recadrage** (onglet *⬤ Forme*) : arrondir les coins ou recadrer au format — déplacer/redimensionner le cadre, puis ✓ Appliquer.
6. **Enregistrer** via `Fichier → Enregistrer` (⌘S) en PNG, JPEG, WebP ou TIFF.

### Paramètres

Via `Outils → Paramètres…` (⌘,), les paramètres suivants peuvent être gérés :

| Paramètre | Description |
|---|---|
| Répertoire par défaut pour l'ouverture | Répertoire de départ de la boîte de dialogue d'ouverture ; vide = dernier répertoire utilisé |
| Répertoire par défaut pour l'export/l'enregistrement | Répertoire de départ de la boîte de dialogue d'enregistrement ; vide = dernier répertoire utilisé |
| Format de fichier image préféré | PNG, JPEG, WebP ou TIFF – apparaît comme première option dans la boîte de dialogue d'enregistrement |
| Langue | Allemand ou anglais ; le changement s’applique après un redémarrage |
| Fichier journal | Affiche le chemin du fichier journal ; le bouton « Ouvrir le dossier » ouvre le répertoire dans le gestionnaire de fichiers |

Les répertoires, le format préféré et la langue sont enregistrés de façon
persistante via **QSettings** et restaurés automatiquement au prochain
démarrage du programme.

### Raccourcis clavier

Sur macOS, la touche modificatrice est **⌘ (Cmd)** ; sur Linux, **Ctrl**.

| Action | Raccourci |
|--------|----------|
| Sélectionner la baguette magique | W |
| Sélectionner le pinceau | B |
| Sélectionner la gomme | E |
| Sélectionner le lasso polygonal | L |
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
La matrice complète Linux/macOS sous Python 3.10, 3.11, 3.12 et 3.13 s'exécute lors
du push d'un tag de version (candidat à la release), de la publication d'une
release ou manuellement. Toutes les installations
de test locales/CI utilisent `requirements/constraints.txt` ; on peut le
remplacer si nécessaire via `PIP_CONSTRAINT=... make pr-check`. Voir
[TESTING.md](../../../TESTING.md) pour le flux complet de tests.

Vérification du style de code et contrôle de typage statique :

```bash
make lint
make type
```

### Régénérer le PDF du guide

`ANLEITUNG.pdf` est généré depuis `ANLEITUNG.md` (Markdown vers HTML
puis PDF via WeasyPrint). Après une modification de la source Markdown,
reconstruire le PDF de manière reproductible. Sous Linux, les polices
DejaVu et les paquets de distribution Pango/Cairo/GDK-Pixbuf sont
nécessaires. Sous macOS, le générateur utilise les polices système
Arial/Courier New ; installer Pango avec `brew install pango` :

```bash
pip install -e ".[docs]"
python scripts/generate_anleitung_pdf.py
```

## Architecture (aperçu rapide)

BgRemover est un paquet installable (`bgremover/`, lancé via
`python -m bgremover` ou le script de console `bgremover`) :

- **`ImageCanvas`** (QGraphicsView) gère l'état de l'image, le masque de sélection,
  les piles d'annulation/rétablissement et les outils (baguette magique, pinceau, lasso, recadrage).
- **`MainWindow`** construit la barre d'outils, la barre d'état/recadrage,
  et relie le canevas, les menus, le panneau droit et les workers.
- **`right_panel`** construit les quatre onglets droits pour la sélection,
  l'arrière-plan, la rotation/miroir et la forme/recadrage à partir d'un
  jeu de callbacks.
- **`menu_actions`** construit la barre de menus, les actions et les
  raccourcis ; `MainWindow` ne fournit plus que les callbacks.
- **`RecentFiles`** encapsule la persistance, la déduplication et
  l'adaptateur de menu « Ouvrir récent », de sorte que `MainWindow` ne
  délègue plus que le chemin de chargement.
- Les **workers** (`ImageLoadWorker`, `AIWorker`, `RembgWarmupWorker`,
  `FloodFillWorker`) s'exécutent dans
  leurs propres `QThread` ; `WorkerController` encapsule le démarrage,
  les références fortes aux workers, `deleteLater` et le shutdown.
- Un **compteur de version** monotone dans le canevas rejette les résultats
  d'IA et de flood-fill obsolètes si une autre image a été chargée ou si
  l'état de l'image a changé entre-temps.
- La pile d'annulation n'est pas limitée par `maxlen`, mais par une
  **limite de mémoire** (`_UNDO_MEMORY_LIMIT`) ; une somme courante
  d'octets évince les entrées les plus anciennes.

## Limitations connues

- **Taille d'image maximale : 40 mégapixels.** Les images plus grandes sont refusées avec un
  message d'état afin de limiter l'utilisation de la mémoire et le temps
  de traitement. La sélection à la baguette magique (flood-fill) s'exécute
  de façon asynchrone dans son propre `QThread`, afin que l'interface reste
  réactive pendant le calcul. Pillow est en outre protégé contre les images
  de type « bombe de décompression ».
- La **construction du bundle d'application** est spécifique à macOS ;
  sous Linux l'application fonctionne via le lancement direct
  `python -m bgremover`. Windows ne fait actuellement pas partie de la
  matrice testée officiellement.

## Fichier journal

Le logger interne de l'application utilise un fichier `bgremover.log` dans
le répertoire de données déterminé par Qt. Le chemin exact dépend de la
plateforme et de la configuration Qt ; avec la configuration macOS
actuelle, il s'agit de
`~/Library/Application Support/BgRemover/BgRemover/bgremover.log`, tandis
que sous Linux le fichier se trouve sous `~/.local/share/`. Il contient
les messages d'exécution et les traces des erreurs journalisées et est
créé lors de la première entrée de journal.

Le lanceur du bundle macOS écrit en outre les diagnostics de démarrage
dans `~/Library/Application Support/BgRemover/bgremover.log`.

Le chemin interne exact est affiché sous `Outils → Paramètres… → Fichier
journal` ; le bouton « Ouvrir le dossier » ouvre directement le répertoire
dans le gestionnaire de fichiers.

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
