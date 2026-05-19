[Deutsch](../../../INSTALL_LINUX.md) · **English** · [Español](../es/INSTALL_LINUX.md) · [Français](../fr/INSTALL_LINUX.md) · [Українська](../uk/INSTALL_LINUX.md) · [简体中文](../zh/INSTALL_LINUX.md)

# BgRemover – Installation on Linux

A quick guide to installing and starting BgRemover from GitHub —
both from the `main` branch and from a feature branch (e.g.
to test an open pull request before merging).

> The macOS app bundle (`create_BgRemover_app.sh`) is macOS-specific.
> On Linux, BgRemover runs by starting it directly with
> `python3 -m bgremover` from a virtual environment (venv) — optionally
> with a desktop launcher for double-clicking (see below).

## Requirements

> **Raspberry Pi OS (Desktop)?** Then take the much simpler path
> [below](#raspberry-pi-os-desktop--the-easy-way) — entirely
> without venv and pip. The following section applies to general
> Linux.

- **A Linux distribution with a desktop** (X11 or Wayland)
- **Python 3.10 or newer** — check with:
  ```bash
  python3 --version
  ```
- **git** and the **venv** module (`python3-venv`)
- **Qt system libraries** for PyQt6 — the PyQt6 wheels contain Qt
  itself but require a few X11/XCB system libraries. Without them
  the GUI fails to start with the error *"qt.qpa.plugin: Could not load the Qt
  platform plugin xcb"*.

### Installing system packages

**Debian / Ubuntu / Linux Mint** (`apt`):
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git \
  libegl1 libgl1 libfontconfig1 libxkbcommon0 libxkbcommon-x11-0 \
  libdbus-1-3 libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
  libxcb-xinerama0 libxcb-xkb1
```
(`libxcb-cursor0` is required by Qt 6.5+ for the `xcb` plugin, among
others under Ubuntu 24.04.)

**Fedora / RHEL** (`dnf`):
```bash
sudo dnf install -y python3 python3-pip git \
  libxcb xcb-util-cursor xcb-util-image xcb-util-keysyms \
  xcb-util-renderutil xcb-util-wm libxkbcommon-x11 \
  fontconfig mesa-libGL mesa-libEGL dbus-libs
```

**Arch / Manjaro** (`pacman`):
```bash
sudo pacman -S --needed python python-pip git \
  libxcb xcb-util-cursor xcb-util-image xcb-util-keysyms \
  xcb-util-renderutil xcb-util-wm libxkbcommon-x11 \
  fontconfig mesa
```

## Raspberry Pi OS (Desktop) – the easy way

On **Raspberry Pi OS "Bookworm" Desktop** (Debian 12, 64-bit
recommended) the installation is much simpler: PyQt6, Pillow, and
numpy are available as ready-made system packages via `apt`. **No
venv, no `pip`, and no editable install** are needed — BgRemover runs
directly from the clone. The `python3-pyqt6` package automatically
pulls in the necessary Qt6/XCB libraries as dependencies (the long
XCB list above is not needed).

```bash
sudo apt update
sudo apt install -y git python3-pyqt6 python3-numpy python3-pil
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m bgremover
```

That's it — the main window opens. The manual tools
(magic wand, brush/eraser, crop, rotate, flip, round
corners) work fully. The **AI background removal is
disabled in this minimal installation** (the AI button is
grayed out) — it can optionally be added later if needed (see below).

To update later, simply run `git pull` in the project folder; a
repeated installation step is not necessary.

### Optional: Starting from the application menu

Create a file `~/.local/share/applications/bgremover.desktop` and
replace `/PFAD/ZU/picture_helper` with the absolute project path:
```ini
[Desktop Entry]
Type=Application
Name=BgRemover
Comment=Hintergrund entfernen und Bilder bearbeiten
Exec=python3 /PFAD/ZU/picture_helper/BgRemover.py
Path=/PFAD/ZU/picture_helper
Icon=/PFAD/ZU/picture_helper/BgRemover_icon.png
Categories=Graphics;Photography;
Terminal=false
```
BgRemover then appears in the application menu and starts on click —
without a venv or wrapper script.

### Optional: Adding AI background removal

> **Note:** On the Raspberry Pi the AI (`rembg` +
> `onnxruntime`) is **much slower and memory-hungry**. Recommended
> only on **64-bit Raspberry Pi OS** (`uname -m` → `aarch64`) and a
> Pi 4/5 with sufficient RAM (≥ 4 GB). On 32-bit (`armv7l`/armhf) there
> are usually no suitable `onnxruntime` wheels — better to leave out the
> AI there.

Since `rembg` is installed afterwards via pip, use a venv **with access
to the system Qt packages** for it:
```bash
cd picture_helper
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install "rembg[cpu]"
python3 -m bgremover
```
`--system-site-packages` makes the PyQt6/Pillow/numpy installed via
`apt` visible in the venv, so that only `rembg` and
`onnxruntime` are loaded additionally. On the very first AI click, `rembg`
downloads its model once (a few hundred MB, cached in `~/.u2net`).
Future starts then run from the venv: `source .venv/bin/activate` and
`python3 -m bgremover`.

## Quick start from `main`

On modern Linux, system Python installations block `pip install`
via PEP 668 ("externally-managed-environment"). Therefore the install
is done in an isolated venv:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -e ".[ai]"
python3 -m bgremover
```

- `.[ai]` installs `rembg[cpu]` including `onnxruntime`
  (AI background removal).
- Without the AI feature, this is sufficient: `python3 -m pip install -e .`

In a new shell, re-activate the venv before starting:
```bash
cd picture_helper
source .venv/bin/activate
python3 -m bgremover
```

## Start variants

| Variant | Command / action | Result |
|----------|-----------------|----------|
| **A – Terminal (recommended)** | activate the venv, then `python3 -m bgremover` | Direct start from the project directory. |
| **B – Starter script** | `./bgremover.sh` (see below) | Activates the venv automatically and starts the app. |
| **C – Application menu** | `.desktop` entry (see below) | Start by double-click / from the application menu. |

### B – Starter script

Create a file `bgremover.sh` in the project directory:
```bash
#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
source .venv/bin/activate
exec python3 -m bgremover "$@"
```
Make it executable and start it:
```bash
chmod +x bgremover.sh
./bgremover.sh
```

### C – Desktop entry (application menu)

Create a file `~/.local/share/applications/bgremover.desktop` and
replace `/PFAD/ZU/picture_helper` with the absolute project path:
```ini
[Desktop Entry]
Type=Application
Name=BgRemover
Comment=Hintergrund entfernen und Bilder bearbeiten
Exec=/PFAD/ZU/picture_helper/bgremover.sh
Icon=/PFAD/ZU/picture_helper/BgRemover_icon.png
Categories=Graphics;Photography;
Terminal=false
```
Then update the desktop database (optional):
```bash
update-desktop-database ~/.local/share/applications 2>/dev/null || true
```
BgRemover now appears in the application menu.

## Installation from a branch (testing open PRs)

PR branch names are listed in the respective pull request on GitHub
("… wants to merge … from **`<branch>`**").

**Variant 1 – in the existing clone directory:**
```bash
cd picture_helper
git fetch origin
git branch -r                       # show available branches
git checkout <branch>
source .venv/bin/activate
# only needed if dependencies have changed:
python3 -m pip install -e ".[ai]"
python3 -m bgremover
```

**Variant 2 – cloning a branch directly:**
```bash
git clone --branch <branch-name> \
  https://github.com/NikolayDA/picture_helper.git
```

## Updating / switching branch

```bash
git checkout main && git pull          # latest main version
git checkout <branch> && git pull      # update a specific branch
```

The editable install (`pip install -e`) does **not** need to be run
again after `git pull` — unless the dependencies in
`pyproject.toml` have changed.

## Troubleshooting

- **`qt.qpa.plugin: Could not load the Qt platform plugin "xcb"`** →
  Qt system libraries are missing. Install the packages from the section
  *"Installing system packages"* afterwards (in particular
  `libxcb-cursor0` under Ubuntu 24.04). Which library exactly is missing
  is shown by:
  ```bash
  QT_DEBUG_PLUGINS=1 python3 -m bgremover 2>&1 | grep -i "cannot\|not found"
  ```
- **`error: externally-managed-environment` on `pip install`** → PEP
  668: do not install into the system Python, but into a venv (see
  Quick start). The venv module is missing? → `sudo apt install python3-venv`.
- **"python3: command not found" or version < 3.10** → install a current
  Python via your distribution's package manager (the code
  uses PEP 604 type annotations like `QThread | None`; Python 3.9 fails).
- **Wayland: window/scaling appears faulty** → for testing, switch to the
  X11 plugin (XWayland):
  ```bash
  QT_QPA_PLATFORM=xcb python3 -m bgremover
  ```
- **pip error during installation** → in the active venv, first update
  pip, then repeat the install command:
  ```bash
  python3 -m pip install --upgrade pip
  ```
- **First AI click takes a long time** → On the very first time, `rembg`
  downloads its model (a few hundred MB, one-time, cached in
  `~/.u2net`). The status bar shows "🤖 KI-Modell wird geladen…"
  and then "🤖 KI bereit".
- **App starts without AI / "No onnxruntime backend found"** → The
  `ai` extra was not installed. Install it afterwards in the venv:
  ```bash
  python3 -m pip install "rembg[cpu]"
  ```
- **Raspberry Pi: `Unable to locate package python3-pyqt6`** → Older
  Raspberry Pi OS versions (Bullseye) ship only PyQt5. Update to
  "Bookworm" (or newer) — or follow the general
  venv/pip path above.
- **Raspberry Pi OS "Bookworm" (Pi 4/5) uses Wayland** → For window
  or scaling issues, switch to the X11 plugin for testing:
  `QT_QPA_PLATFORM=xcb python3 -m bgremover` (see the Wayland note
  above).
- **Diagnosing errors** → Check the log file
  `~/.local/share/BgRemover/bgremover.log` (stack traces and
  status messages). When started from the terminal, the
  error message additionally appears directly on the console.
