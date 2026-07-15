[Deutsch](../../../INSTALL_LINUX.md) · [English](../en/INSTALL_LINUX.md) · [Español](../es/INSTALL_LINUX.md) · **Français** · [Українська](../uk/INSTALL_LINUX.md) · [简体中文](../zh/INSTALL_LINUX.md)

# BgRemover – Installation sous Linux

Guide rapide pour installer et lancer BgRemover depuis GitHub —
aussi bien depuis la branche `main` que depuis une branche de fonctionnalité (p. ex.
pour tester une pull request ouverte avant la fusion).

> Le bundle d'application macOS (`create_BgRemover_app.sh`) est spécifique à macOS.
> Sous Linux, AppImage et `.deb` sont les artefacts recommandés pour les
> utilisateurs finaux ; le lancement direct depuis un venv reste documenté
> pour le développement, les tests de branches et les changements locaux.

## Recommandé : utiliser les artefacts de release

Pour une installation Linux normale, les artefacts de release sont la voie la
plus simple — **sans venv, sans pip et sans checkout Git** :

> **Note de disponibilité :** Les artefacts AppImage/`.deb` préconstruits —
> **avec l'IA déjà intégrée** — sont disponibles à partir de **v2.4.0**. Les
> versions antérieures (v2.1.0/v2.2.0)
> ne contiennent pas encore de tels assets — tant qu'il n'y a rien à télécharger
> sur la page des releases, utilisez la voie venv/Git ci-dessous.

- **AppImage :** fichier portable unique ; rendez-le exécutable puis lancez-le.
- **`.deb` :** paquet installable pour Debian/Ubuntu/Raspberry Pi OS avec entrée
  de menu et désinstallation propre via apt/dpkg.

Téléchargez l'artefact adapté depuis la [page des releases GitHub](https://github.com/NikolayDA/picture_helper/releases)
— le nom de fichier indique la version, la plateforme/l'appareil et si l'IA
est intégrée : `BgRemover-<version>-<tag-plateforme>[-ai].<extension>`.

```bash
# AppImage (exemple x86_64)
chmod +x BgRemover-*-linux-x86_64-ai.AppImage
./BgRemover-*-linux-x86_64-ai.AppImage

# .deb (exemple x86_64 ; apt installe la dépendance FUSE)
sudo apt install ./BgRemover-*-linux-x86_64-ai.deb
```

Des builds existent pour **x86_64** (`linux-x86_64`) et **aarch64/Raspberry
Pi OS 64-bit** (`linux-raspberrypi-arm64`) — en AppImage et en `.deb`, avec un
suffixe `-ai` dès que la suppression d'arrière-plan par IA est intégrée (par
défaut pour les téléchargements de releases, voir ci-dessus). Les
instructions venv/Git ci-dessous restent utiles pour tester depuis `main`,
une branche de fonctionnalité ou avec des changements locaux.

## Prérequis

> **Raspberry Pi OS (Desktop) ?** Alors empruntez la voie nettement plus simple
> [plus bas](#raspberry-pi-os-desktop--la-voie-simple) —
> totalement sans venv ni pip. La section suivante concerne Linux
> en général.

- **Une distribution Linux avec bureau** (X11 ou Wayland)
- **Python 3.10 ou plus récent** — vérifier avec :
  ```bash
  python3 --version
  ```
- **git** et le module **venv** (`python3-venv`)
- **Bibliothèques système Qt** pour PyQt6 — les wheels PyQt6 contiennent Qt
  lui-même, mais nécessitent quelques bibliothèques système X11/XCB. Sans elles,
  l'interface démarre avec l'erreur *« qt.qpa.plugin: Could not load the Qt
  platform plugin xcb »*.

> **Remarque IA :** L'application principale fonctionne avec Python 3.10+. La
> suppression d'arrière-plan par IA (`.[ai]`) nécessite **Python 3.11 ou plus
> récent** (les builds actuels d'`onnxruntime` et de `rembg` ciblent Python 3.11+).

### Installer les paquets système

**Debian / Ubuntu / Linux Mint** (`apt`) :
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git \
  libegl1 libgl1 libfontconfig1 libxkbcommon0 libxkbcommon-x11-0 \
  libdbus-1-3 libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
  libxcb-xinerama0 libxcb-xkb1
```
(`libxcb-cursor0` est requis par Qt 6.5+ pour le plugin `xcb`, entre autres sous
Ubuntu 24.04.)

**Fedora / RHEL** (`dnf`) :
```bash
sudo dnf install -y python3 python3-pip git \
  libxcb xcb-util-cursor xcb-util-image xcb-util-keysyms \
  xcb-util-renderutil xcb-util-wm libxkbcommon-x11 \
  fontconfig mesa-libGL mesa-libEGL dbus-libs
```

**Arch / Manjaro** (`pacman`) :
```bash
sudo pacman -S --needed python python-pip git \
  libxcb xcb-util-cursor xcb-util-image xcb-util-keysyms \
  xcb-util-renderutil xcb-util-wm libxkbcommon-x11 \
  fontconfig mesa
```

## Raspberry Pi OS (Desktop) – la voie simple

Sur **Raspberry Pi OS « Bookworm » Desktop** (Debian 12) ou plus récent
(par ex. « Trixie »/Debian 13, 64 bits recommandé), l'installation est
nettement plus simple : PyQt6, Pillow et
numpy sont disponibles sous forme de paquets système prêts à l'emploi via `apt`. **Aucun
venv, aucun `pip` et aucune installation editable** ne sont nécessaires — BgRemover fonctionne
directement depuis le clone. Le paquet `python3-pyqt6` entraîne automatiquement les
bibliothèques Qt6/XCB nécessaires en tant que dépendance (la longue
liste XCB ci-dessus est inutile).

```bash
sudo apt update
sudo apt install -y git python3-pyqt6 python3-numpy python3-pil
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m bgremover
```

C'est tout — la fenêtre principale s'ouvre. Les outils manuels
(baguette magique, pinceau/gomme, recadrage, rotation, miroir, arrondi des
coins) fonctionnent intégralement. La **suppression d'arrière-plan par IA est
désactivée dans cette installation minimale** (le bouton d'IA est
grisé) — ajoutable facultativement au besoin (voir ci-dessous).

Pour mettre à jour plus tard, il suffit de faire `git pull` dans le dossier du projet ; une
nouvelle étape d'installation est inutile.

### Facultatif : lancement depuis le menu des applications

Créer un fichier `~/.local/share/applications/bgremover.desktop` et
remplacer `/PFAD/ZU/picture_helper` par le chemin absolu du projet :
```ini
[Desktop Entry]
Type=Application
Name=BgRemover
Comment=Supprimer l'arrière-plan et modifier les images
Exec=python3 -m bgremover
Path=/PFAD/ZU/picture_helper
Icon=/PFAD/ZU/picture_helper/BgRemover_icon.png
Categories=Graphics;Photography;
Terminal=false
```
BgRemover apparaît ensuite dans le menu des applications et démarre par un clic —
sans venv ni script wrapper.

### Facultatif : ajouter la suppression d'arrière-plan par IA

> **Remarque :** sur le Raspberry Pi, l'IA (`rembg` +
> `onnxruntime`) est **nettement plus lente et gourmande en mémoire**. Recommandée
> uniquement sur **Raspberry Pi OS 64 bits** (`uname -m` → `aarch64`) et un
> Pi 4/5 avec suffisamment de RAM (≥ 4 Go). Sur 32 bits (`armv7l`/armhf), il
> n'existe en général pas de wheels `onnxruntime` adaptés — dans ce cas, mieux vaut
> renoncer à l'IA.

Comme `rembg` est installé après coup via pip, utiliser pour cela un venv **avec accès
aux paquets Qt du système** :
```bash
cd picture_helper
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install "rembg[cpu]"
python3 -m bgremover
```
`--system-site-packages` rend les PyQt6/Pillow/numpy installés via `apt`
visibles dans le venv, de sorte que seuls `rembg` et
`onnxruntime` sont chargés en plus. Au prochain **démarrage** de l'app,
`rembg` télécharge automatiquement son modèle une seule fois (quelques
centaines de Mo, cache dans `~/.u2net`) ; la barre d'état affiche
entre-temps « Chargement du modèle IA… » et le bouton IA reste
désactivé jusque-là — c'est le comportement attendu.
Pour les démarrages suivants, depuis le venv : `source .venv/bin/activate` et
`python3 -m bgremover`.

En alternative au téléchargement automatique au démarrage, l'état du
modèle peut être vérifié à tout moment via `Outils → Gérer le modèle
d'IA…`, qui permet un téléchargement/nouvel essai manuel (avec indicateur
d'activité et bouton d'annulation) – utile si le téléchargement au
démarrage a échoué hors ligne.

## Démarrage rapide depuis `main`

Sur Linux moderne, les installations Python système bloquent `pip install`
selon le PEP 668 (« externally-managed-environment »). C'est pourquoi l'installation se fait dans un
venv isolé :

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

- `.[ai]` installe `rembg[cpu]` y compris `onnxruntime`
  (suppression d'arrière-plan par IA).
- Sans la fonction d'IA, il suffit de : `python3 -m pip install -c requirements/constraints.txt -e .`

Dans un nouveau shell, réactiver le venv avant le démarrage :
```bash
cd picture_helper
source .venv/bin/activate
python3 -m bgremover
```

## Variantes de démarrage

| Variante | Commande / action | Résultat |
|----------|-----------------|----------|
| **A – Terminal (recommandé)** | activer le venv, puis `python3 -m bgremover` | Lancement direct depuis le répertoire du projet. |
| **B – Script de lancement** | `./bgremover.sh` (voir ci-dessous) | Active automatiquement le venv et démarre l'application. |
| **C – Menu des applications** | entrée `.desktop` (voir ci-dessous) | Lancement par double-clic / depuis le menu des applications. |

### B – Script de lancement

Créer un fichier `bgremover.sh` dans le répertoire du projet :
```bash
#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
source .venv/bin/activate
exec python3 -m bgremover "$@"
```
Le rendre exécutable et le démarrer :
```bash
chmod +x bgremover.sh
./bgremover.sh
```

### C – Entrée de bureau (menu des applications)

Créer un fichier `~/.local/share/applications/bgremover.desktop` et
remplacer `/PFAD/ZU/picture_helper` par le chemin absolu du projet :
```ini
[Desktop Entry]
Type=Application
Name=BgRemover
Comment=Supprimer l'arrière-plan et modifier les images
Exec=/PFAD/ZU/picture_helper/bgremover.sh
Icon=/PFAD/ZU/picture_helper/BgRemover_icon.png
Categories=Graphics;Photography;
Terminal=false
```
Ensuite, mettre à jour la base de données du bureau (facultatif) :
```bash
update-desktop-database ~/.local/share/applications 2>/dev/null || true
```
BgRemover apparaît désormais dans le menu des applications.

## Installation depuis une branche (tester des PRs ouvertes)

Les noms des branches de PR figurent dans la pull request correspondante sur GitHub
(« … wants to merge … from **`<branch>`** »).

**Variante 1 – dans le répertoire de clone existant :**
```bash
cd picture_helper
git fetch origin
git branch -r                       # afficher les branches disponibles
git checkout <branch>
source .venv/bin/activate
# nécessaire uniquement si les dépendances ont changé :
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

**Variante 2 – cloner directement une branche :**
```bash
git clone --branch <branch-name> \
  https://github.com/NikolayDA/picture_helper.git
```

## Mettre à jour / changer de branche

```bash
git checkout main && git pull          # dernière version principale
git checkout <branch> && git pull      # mettre à jour une branche donnée
```

L'installation editable (`pip install -e`) n'a **pas** besoin d'être
réexécutée après `git pull` — sauf si les dépendances dans
`pyproject.toml` ou `requirements/constraints.txt` ont changé.

## Dépannage

- **`qt.qpa.plugin: Could not load the Qt platform plugin "xcb"`** →
  Il manque des bibliothèques système Qt. Réinstaller les paquets de la section
  *« Installer les paquets système »* (en particulier
  `libxcb-cursor0` sous Ubuntu 24.04). Quelle bibliothèque manque exactement
  est indiqué par :
  ```bash
  QT_DEBUG_PLUGINS=1 python3 -m bgremover 2>&1 | grep -i "cannot\|not found"
  ```
- **`error: externally-managed-environment` lors de `pip install`** → PEP
  668 : ne pas installer dans le Python système, mais dans un venv (voir
  Démarrage rapide). Le module venv manque ? → `sudo apt install python3-venv`.
- **« python3: command not found » ou version < 3.10** → installer un Python
  récent via le gestionnaire de paquets de la distribution (le code
  utilise des annotations de type PEP 604 comme `QThread | None` ; Python 3.9 échoue).
- **Wayland : fenêtre/mise à l'échelle semble défaillante** → basculer à titre d'essai vers le
  plugin X11 (XWayland) :
  ```bash
  QT_QPA_PLATFORM=xcb python3 -m bgremover
  ```
- **Erreur pip lors de l'installation** → dans le venv actif, mettre d'abord pip
  à jour, puis réessayer la commande d'installation :
  ```bash
  python3 -m pip install --upgrade "pip>=26.1.2"
  ```
- **Le bouton IA reste désactivé un instant après le démarrage** → Ce
  n'est pas une erreur d'installation : dès que `rembg` est installé,
  l'app télécharge automatiquement son modèle une seule fois au
  **démarrage de l'app** (pas au premier clic d'IA), quelques centaines
  de Mo, cache dans `~/.u2net`. La barre d'état affiche entre-temps
  « Chargement du modèle IA… » puis « IA prête » ; le bouton IA reste
  désactivé jusque-là (et de toute façon sans image chargée). Si le
  téléchargement a échoué hors ligne, l'état peut être vérifié à tout
  moment via `Outils → Gérer le modèle d'IA…`, qui permet un
  téléchargement/nouvel essai manuel.
- **L'application démarre sans IA / « No onnxruntime backend found »** → l'extra
  `ai` n'a pas été installé. L'installer après coup dans le venv :
  ```bash
  python3 -m pip install "rembg[cpu]"
  ```
- **Raspberry Pi : `Unable to locate package python3-pyqt6`** → les anciennes
  versions de Raspberry Pi OS (Bullseye) ne fournissent que PyQt5. Passer à
  « Bookworm » (ou plus récent) — ou suivre la voie générale
  venv/pip ci-dessus.
- **Raspberry Pi OS « Bookworm » (Pi 4/5) utilise Wayland** → en cas de problème de fenêtre
  ou de mise à l'échelle, basculer à titre d'essai vers le plugin X11 :
  `QT_QPA_PLATFORM=xcb python3 -m bgremover` (voir la remarque Wayland
  ci-dessus).
- **Diagnostic en cas d'erreur** → le chemin exact du journal
  d'exécution interne est affiché sous
  `Outils → Réglages… → Fichier journal` ; sous Linux, il se trouve
  dans le dossier déterminé par Qt sous `~/.local/share/`. Lors d'un
  lancement depuis le terminal, le message d'erreur apparaît en plus
  directement dans la console.
