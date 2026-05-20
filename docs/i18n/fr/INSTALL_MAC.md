[Deutsch](../../../INSTALL_MAC.md) · [English](../en/INSTALL_MAC.md) · [Español](../es/INSTALL_MAC.md) · **Français** · [Українська](../uk/INSTALL_MAC.md) · [简体中文](../zh/INSTALL_MAC.md)

# BgRemover – Installation sur le Mac

Guide rapide pour installer et lancer BgRemover depuis GitHub —
aussi bien depuis la branche `main` que depuis une branche de fonctionnalité (p. ex.
pour tester une pull request ouverte avant la fusion).

## Prérequis

- **macOS**
- **Python 3.10 ou plus récent** — vérifier avec :
  ```bash
  python3 --version
  ```
- **git**

Si Python ou git manquent, le plus simple est de passer par [Homebrew](https://brew.sh) :
```bash
brew install python git
```

## Démarrage rapide depuis `main`

Le script de bundle d'application est **recommandé** — il crée automatiquement un
venv isolé, installe toutes les dépendances (y compris
`onnxruntime` pour l'IA), gère correctement Apple Silicon et copie
les icônes de la barre d'outils dans le bundle :

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

Confirmer avec **Entrée** lors de l'invite relative au venv ; ensuite, lancer `BgRemover.app`
sous `~/Applications` par double-clic.

**Lancement direct dans le terminal** — sur macOS moderne dans un venv, car le
Python système bloque `pip install` selon le PEP 668 :

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -e ".[ai]"
python3 -m bgremover
```

- `.[ai]` installe `rembg[cpu]` y compris `onnxruntime` (suppression d'arrière-plan par IA).
- Sans la fonction d'IA, il suffit de : `python3 -m pip install -e .`

## Variantes de démarrage

Après l'installation, il existe trois façons de lancer le programme :

| Variante | Commande / action | Résultat |
|----------|-----------------|----------|
| **A – Application macOS (recommandé)** | `bash create_BgRemover_app.sh` | Crée un venv isolé, installe toutes les dépendances (y compris `onnxruntime`), copie les icônes et produit un `BgRemover.app` autonome sous `~/Applications`. La quarantaine est automatiquement supprimée ; le projet peut rester dans `~/Documents`. |
| **B – Double-clic** | double-cliquer sur `BgRemover.command` dans le Finder | Démarre dans une fenêtre de terminal ; utilise automatiquement le venv d'application créé par le script (le fichier est déjà exécutable). |
| **C – Terminal** | dans un venv : `python3 -m bgremover` | Lancement direct (configuration du venv : voir le démarrage rapide ci-dessus). |

## Installation depuis une branche (tester des PRs ouvertes)

Les noms des branches de PR figurent dans la pull request correspondante sur GitHub
(« … wants to merge … from **`<branch>`** »).

**Variante 1 – dans le répertoire de clone existant :**
```bash
cd picture_helper
git fetch origin
git branch -r                       # afficher les branches disponibles
git checkout <branch>
# dans le venv (voir Démarrage rapide) ; nécessaire uniquement si les dépendances ont changé :
python3 -m pip install -e ".[ai]"
python3 -m bgremover
```

Sinon, il suffit aussi d'exécuter `bash create_BgRemover_app.sh` sur une branche
— cela prend en charge automatiquement le venv et les dépendances.

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
`pyproject.toml` ont changé.

## Dépannage

- **L'application ne démarre pas / le double-clic ne fait rien** → depuis la v3,
  l'application affiche une boîte de dialogue d'erreur avec « Ouvrir le journal ». Cause la plus fréquente :
  `PyQt6` n'est pas installé dans le Python utilisé par l'application
  (p. ex. parce que `pip install` est allé dans un venv ou un autre Python,
  ou que le Python Homebrew bloque `pip install` selon le PEP 668). Solution :
  réexécuter `bash create_BgRemover_app.sh` et laisser créer le venv
  (confirmer la proposition avec Entrée) — le script installe alors les
  dépendances dans un venv sous
  `~/Library/Application Support/BgRemover/venv` et intègre ce Python
  dans l'application.
- **`[Errno 1] Operation not permitted` lors de l'accès au projet**
  → confidentialité macOS (TCC). Si le projet se trouve dans `~/Documents`,
  `~/Desktop`, `~/Downloads` ou iCloud Drive, une `.app` lancée depuis le
  Finder n'a pas le droit d'y lire. Depuis le tour 5 (coupe en paquet)
  c'est résolu : `create_BgRemover_app.sh` installe le paquet
  `bgremover` de manière **non éditable** dans la venv sous
  `~/Library/Application Support/BgRemover/venv` (copie propre du code
  avec `icons/` en package-data), l'app est donc indépendante du
  dossier du projet. Fix : réexécuter une fois
  `bash create_BgRemover_app.sh`. (Sinon, déplacer le projet vers
  p. ex. `~/picture_helper` et y réexécuter le script.)
- **`numpy ... incompatible architecture (have 'arm64', need 'x86_64')`**
  → Apple Silicon : dans `~/Library/Python/...` se trouve un paquet
  d'architecture étrangère, qui « déteint » dans un Python à l'architecture incompatible. Depuis la v3.1, c'est
  résolu : le lanceur définit `PYTHONNOUSERSITE=1` (le user-site est
  ignoré), force l'architecture CPU native et un venv isolé est
  obligatoirement utilisé. Solution : de préférence, installer d'abord un Python
  natif, puis reconstruire :
  ```bash
  brew install python
  bash create_BgRemover_app.sh   # confirmer l'invite venv avec Entrée
  ```
- **Voir l'erreur directement (diagnostic manuel)** → lancer le lanceur dans le terminal,
  le vrai message d'erreur apparaît alors :
  ```bash
  ~/Applications/BgRemover.app/Contents/MacOS/BgRemover
  ```
  Attendu en cas de paquets manquants : `ModuleNotFoundError: No module named 'PyQt6'`.
- **« python3: command not found »** → `brew install python`
- **Erreur pip lors de l'installation** → mettre d'abord pip à jour :
  ```bash
  python3 -m pip install --upgrade pip
  ```
  puis réexécuter la commande d'installation.
- **Le premier clic d'IA prend du temps** → à la toute première fois, `rembg`
  télécharge son modèle (quelques centaines de Mo, une seule fois, cache dans
  `~/.u2net`). La barre d'état affiche « 🤖 KI-Modell wird geladen… »
  puis « 🤖 KI bereit ».
- **Gatekeeper : « développeur non vérifié »** → clic droit sur
  `BgRemover.app` → **Ouvrir**. Le script de construction supprime déjà la
  quarantaine via `xattr`, mais un clic droit suivi d'Ouvrir suffit en
  cas de doute.
- **L'application plante avec « No onnxruntime backend found »** → les nouvelles
  versions de `rembg` ne fournissent plus le backend. Désormais corrigé
  (l'extra `ai` entraîne `rembg[cpu]`/`onnxruntime` ; s'il manque malgré tout,
  l'application démarre sans IA au lieu de planter). Solution : reconstruire une fois
  avec `bash create_BgRemover_app.sh` — ou l'installer après coup dans le venv :
  `"~/Library/Application Support/BgRemover/venv/bin/python3" -m pip install "rembg[cpu]"`.
- **L'`.app` a un aspect différent de `BgRemover.command`** → ancien bundle
  sans icônes de barre d'outils (l'application utilisait des icônes de remplacement dessinées). Désormais
  corrigé — depuis le tour 5 les icônes sont `package-data` dans
  `bgremover/icons/`, donc reprises automatiquement dans la venv par
  `pip install` et chargées via `importlib.resources` ; reconstruire
  une fois avec `bash create_BgRemover_app.sh`.
- **Diagnostic en cas d'erreur** → consulter le fichier journal `~/.bgremover.log`.
