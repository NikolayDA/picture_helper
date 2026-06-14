**Deutsch** · [English](docs/i18n/en/INSTALL_LINUX.md) · [Español](docs/i18n/es/INSTALL_LINUX.md) · [Français](docs/i18n/fr/INSTALL_LINUX.md) · [Українська](docs/i18n/uk/INSTALL_LINUX.md) · [简体中文](docs/i18n/zh/INSTALL_LINUX.md)

# BgRemover – Installation unter Linux

Kurzanleitung zum Installieren und Starten von BgRemover aus GitHub —
sowohl aus dem `main`-Branch als auch aus einem Feature-Branch (z. B.
um einen offenen Pull Request vor dem Merge zu testen).

> Das macOS-App-Bundle (`create_BgRemover_app.sh`) ist macOS-spezifisch.
> Unter Linux sind AppImage und `.deb` die empfohlenen Endnutzer-Artefakte;
> der direkte Start aus einer venv bleibt für Entwicklung, Branch-Tests und
> lokale Änderungen dokumentiert.

## Empfohlen: Release-Artefakte verwenden

Für normale Installation unter Linux sind die Release-Artefakte der bequemste
Weg — **ohne venv, ohne pip und ohne Git-Checkout**:

> **Hinweis zur Verfügbarkeit:** Fertige AppImage-/`.deb`-Artefakte gibt es ab
> **v2.3.0**. Ältere Releases (z. B. v2.2.0) enthalten noch keine solchen
> Assets — solange auf der Releases-Seite nichts zum Herunterladen liegt, den
> venv-/Git-Weg weiter unten nutzen.

- **AppImage:** portable Einzeldatei; ausführbar machen und starten.
- **`.deb`:** installierbares Paket für Debian/Ubuntu/Raspberry Pi OS mit
  Menüeintrag und sauberem Entfernen über apt/dpkg.

Lade das passende Artefakt von der [GitHub-Releases-Seite](https://github.com/NikolayDA/picture_helper/releases) herunter:

```bash
# AppImage (Beispiel x86_64)
chmod +x BgRemover-*-x86_64.AppImage
./BgRemover-*-x86_64.AppImage

# .deb (Beispiel amd64; apt installiert die FUSE-Abhängigkeit mit)
sudo apt install ./BgRemover-*-amd64.deb
```

Es gibt Builds für **x86_64** und **aarch64/Raspberry Pi OS 64-bit**. Die
folgenden venv-/Git-Anleitungen bleiben wichtig, wenn du aus `main`, aus einem
Feature-Branch oder mit lokalen Änderungen testen willst.

## Voraussetzungen

> **Raspberry Pi OS (Desktop)?** Dann den deutlich einfacheren Weg
> [weiter unten](#raspberry-pi-os-desktop--der-einfache-weg) nehmen —
> ganz ohne venv und pip. Der folgende Abschnitt gilt für allgemeines
> Linux.

- **Eine Linux-Distribution mit Desktop** (X11 oder Wayland)
- **Python 3.10 oder neuer** — prüfen mit:
  ```bash
  python3 --version
  ```
- **git** und das **venv**-Modul (`python3-venv`)
- **Qt-Systembibliotheken** für PyQt6 — die PyQt6-Wheels enthalten Qt
  selbst, benötigen aber einige X11/XCB-Systembibliotheken. Ohne sie
  startet die GUI mit dem Fehler *„qt.qpa.plugin: Could not load the Qt
  platform plugin xcb"*.

> **KI-Hinweis:** Die Kern-App läuft mit Python 3.10+. Die
> KI-Hintergrundentfernung (`.[ai]`) benötigt **Python 3.11 oder neuer**
> (die aktuellen `onnxruntime`- und `rembg`-Builds zielen auf Python 3.11+).

### Systempakete installieren

**Debian / Ubuntu / Linux Mint** (`apt`):
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git \
  libegl1 libgl1 libfontconfig1 libxkbcommon0 libxkbcommon-x11-0 \
  libdbus-1-3 libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
  libxcb-xinerama0 libxcb-xkb1
```
(`libxcb-cursor0` wird von Qt 6.5+ für das `xcb`-Plugin u. a. unter
Ubuntu 24.04 benötigt.)

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

## Raspberry Pi OS (Desktop) – der einfache Weg

Auf **Raspberry Pi OS „Bookworm" Desktop** (Debian 12) oder neuer
(z. B. „Trixie"/Debian 13, 64-Bit empfohlen) ist die Installation
deutlich einfacher: PyQt6, Pillow und
numpy gibt es als fertige Systempakete über `apt`. Es wird **keine
venv, kein `pip` und kein editable-Install** benötigt — BgRemover läuft
direkt aus dem Klon. Das Paket `python3-pyqt6` zieht die nötigen
Qt6-/XCB-Bibliotheken automatisch als Abhängigkeit mit (die lange
XCB-Liste oben entfällt).

```bash
sudo apt update
sudo apt install -y git python3-pyqt6 python3-numpy python3-pil
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m bgremover
```

Das war's — das Hauptfenster öffnet sich. Die manuellen Werkzeuge
(Zauberstab, Pinsel/Radierer, Zuschnitt, Drehen, Spiegeln, Ecken
abrunden) funktionieren vollständig. Die **KI-Hintergrundentfernung ist
in dieser Minimal-Installation deaktiviert** (der KI-Button ist
ausgegraut) — bei Bedarf optional nachrüstbar (siehe unten).

Aktualisieren später einfach per `git pull` im Projektordner; ein
erneuter Installationsschritt entfällt.

### Optional: Start aus dem Anwendungsmenü

Eine Datei `~/.local/share/applications/bgremover.desktop` anlegen und
`/PFAD/ZU/picture_helper` durch den absoluten Projektpfad ersetzen:
```ini
[Desktop Entry]
Type=Application
Name=BgRemover
Comment=Hintergrund entfernen und Bilder bearbeiten
Exec=python3 -m bgremover
Path=/PFAD/ZU/picture_helper
Icon=/PFAD/ZU/picture_helper/BgRemover_icon.png
Categories=Graphics;Photography;
Terminal=false
```
BgRemover erscheint danach im Anwendungsmenü und startet per Klick —
ohne venv oder Wrapper-Skript.

### Optional: KI-Hintergrundentfernung nachrüsten

> **Hinweis:** Auf dem Raspberry Pi ist die KI (`rembg` +
> `onnxruntime`) **deutlich langsamer und speicherhungrig**. Empfohlen
> nur auf **64-Bit Raspberry Pi OS** (`uname -m` → `aarch64`) und einem
> Pi 4/5 mit ausreichend RAM (≥ 4 GB). Auf 32-Bit (`armv7l`/armhf) gibt
> es i. d. R. keine passenden `onnxruntime`-Wheels — dort die KI besser
> auslassen.

Da `rembg` per pip nachinstalliert wird, dafür eine venv **mit Zugriff
auf die System-Qt-Pakete** verwenden:
```bash
cd picture_helper
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install "rembg[cpu]"
python3 -m bgremover
```
`--system-site-packages` macht die per `apt` installierten
PyQt6/Pillow/numpy in der venv sichtbar, sodass nur `rembg` und
`onnxruntime` nachgeladen werden. Beim allerersten KI-Klick lädt `rembg`
sein Modell einmalig herunter (einige hundert MB, Cache in `~/.u2net`).
Künftige Starts dann aus der venv: `source .venv/bin/activate` und
`python3 -m bgremover`.

## Schnellstart aus `main`

Auf modernem Linux blockieren System-Python-Installationen `pip install`
per PEP 668 („externally-managed-environment"). Deshalb wird in einer
isolierten venv installiert:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

- `.[ai]` installiert `rembg[cpu]` inkl. `onnxruntime`
  (KI-Hintergrundentfernung).
- Ohne KI-Funktion reicht: `python3 -m pip install -c requirements/constraints.txt -e .`

Bei einer neuen Shell vor dem Start die venv erneut aktivieren:
```bash
cd picture_helper
source .venv/bin/activate
python3 -m bgremover
```

## Startvarianten

| Variante | Befehl / Aktion | Ergebnis |
|----------|-----------------|----------|
| **A – Terminal (empfohlen)** | venv aktivieren, dann `python3 -m bgremover` | Direkter Start aus dem Projektverzeichnis. |
| **B – Starter-Skript** | `./bgremover.sh` (siehe unten) | Aktiviert die venv automatisch und startet die App. |
| **C – Anwendungsmenü** | `.desktop`-Eintrag (siehe unten) | Start per Doppelklick / aus dem Anwendungsmenü. |

### B – Starter-Skript

Eine Datei `bgremover.sh` im Projektverzeichnis anlegen:
```bash
#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
source .venv/bin/activate
exec python3 -m bgremover "$@"
```
Ausführbar machen und starten:
```bash
chmod +x bgremover.sh
./bgremover.sh
```

### C – Desktop-Eintrag (Anwendungsmenü)

Eine Datei `~/.local/share/applications/bgremover.desktop` anlegen und
`/PFAD/ZU/picture_helper` durch den absoluten Projektpfad ersetzen:
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
Danach die Desktop-Datenbank aktualisieren (optional):
```bash
update-desktop-database ~/.local/share/applications 2>/dev/null || true
```
BgRemover erscheint nun im Anwendungsmenü.

## Installation aus einem Branch (offene PRs testen)

PR-Branch-Namen stehen im jeweiligen Pull Request auf GitHub
(„… wants to merge … from **`<branch>`**").

**Variante 1 – im vorhandenen Klon-Verzeichnis:**
```bash
cd picture_helper
git fetch origin
git branch -r                       # verfügbare Branches anzeigen
git checkout <branch>
source .venv/bin/activate
# nur nötig, wenn sich Abhängigkeiten geändert haben:
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

**Variante 2 – einen Branch direkt klonen:**
```bash
git clone --branch <branch-name> \
  https://github.com/NikolayDA/picture_helper.git
```

## Aktualisieren / Branch wechseln

```bash
git checkout main && git pull          # neueste Hauptversion
git checkout <branch> && git pull      # bestimmten Branch aktualisieren
```

Der Editable-Install (`pip install -e`) muss nach `git pull` **nicht**
erneut ausgeführt werden — außer die Abhängigkeiten in
`pyproject.toml` oder `requirements/constraints.txt` haben sich geändert.

## Troubleshooting

- **`qt.qpa.plugin: Could not load the Qt platform plugin "xcb"`** →
  Es fehlen Qt-Systembibliotheken. Die Pakete aus dem Abschnitt
  *„Systempakete installieren"* nachinstallieren (insbesondere
  `libxcb-cursor0` unter Ubuntu 24.04). Welche Bibliothek genau fehlt,
  zeigt:
  ```bash
  QT_DEBUG_PLUGINS=1 python3 -m bgremover 2>&1 | grep -i "cannot\|not found"
  ```
- **`error: externally-managed-environment` bei `pip install`** → PEP
  668: nicht ins System-Python installieren, sondern in eine venv (siehe
  Schnellstart). venv-Modul fehlt? → `sudo apt install python3-venv`.
- **„python3: command not found" oder Version < 3.10** → einen aktuellen
  Python über den Paketmanager der Distribution installieren (der Code
  nutzt PEP-604-Typannotationen wie `QThread | None`; Python 3.9 schlägt
  fehl).
- **Wayland: Fenster/Skalierung wirkt fehlerhaft** → testweise auf das
  X11-Plugin (XWayland) wechseln:
  ```bash
  QT_QPA_PLATFORM=xcb python3 -m bgremover
  ```
- **pip-Fehler beim Installieren** → in der aktiven venv erst pip
  aktualisieren, dann den Install-Befehl wiederholen:
  ```bash
  python3 -m pip install --upgrade "pip>=26.1.2"
  ```
- **Erster KI-Klick dauert lange** → Beim allerersten Mal lädt `rembg`
  sein Modell herunter (einige hundert MB, einmalig, Cache in
  `~/.u2net`). Die Statusleiste zeigt „🤖 KI-Modell wird geladen…"
  und danach „🤖 KI bereit".
- **App startet ohne KI / „No onnxruntime backend found"** → Das
  `ai`-Extra wurde nicht installiert. In der venv nachinstallieren:
  ```bash
  python3 -m pip install "rembg[cpu]"
  ```
- **Raspberry Pi: `Unable to locate package python3-pyqt6`** → Ältere
  Raspberry Pi OS-Versionen (Bullseye) liefern nur PyQt5. Auf
  „Bookworm" (oder neuer) aktualisieren — oder dem allgemeinen
  venv-/pip-Weg oben folgen.
- **Raspberry Pi OS „Bookworm" (Pi 4/5) nutzt Wayland** → Bei Fenster-
  oder Skalierungsproblemen testweise auf das X11-Plugin wechseln:
  `QT_QPA_PLATFORM=xcb python3 -m bgremover` (siehe Wayland-Hinweis
  oben).
- **Diagnose bei Fehlern** → Den genauen Pfad des internen Laufzeit-Logs
  zeigt `Extras → Einstellungen… → Protokolldatei`; unter Linux liegt
  es im von Qt ermittelten Verzeichnis unter `~/.local/share/`. Beim
  Start aus dem Terminal erscheint die Fehlermeldung zusätzlich direkt
  auf der Konsole.
