**Deutsch** · [English](docs/i18n/en/INSTALL_MAC.md) · [Español](docs/i18n/es/INSTALL_MAC.md) · [Français](docs/i18n/fr/INSTALL_MAC.md) · [Українська](docs/i18n/uk/INSTALL_MAC.md) · [简体中文](docs/i18n/zh/INSTALL_MAC.md)

# BgRemover – Installation auf dem Mac

Kurzanleitung zum Installieren und Starten von BgRemover aus GitHub —
sowohl aus dem `main`-Branch als auch aus einem Feature-Branch (z. B.
um einen offenen Pull Request vor dem Merge zu testen).

## Voraussetzungen

- **macOS**
- **Python 3.10 oder neuer** — prüfen mit:
  ```bash
  python3 --version
  ```
- **git**

Falls Python oder git fehlen, am einfachsten über [Homebrew](https://brew.sh):
```bash
brew install python git
```

## Schnellstart aus `main`

**Empfohlen** ist das App-Bundle-Skript — es legt automatisch eine
isolierte venv an, installiert alle Abhängigkeiten (inkl.
`onnxruntime` für die KI), behandelt Apple Silicon korrekt und kopiert
die Toolbar-Icons ins Bundle:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

Beim venv-Hinweis mit **Enter** bestätigen; danach `BgRemover.app`
unter `~/Applications` per Doppelklick starten.

**Direkter Terminal-Start** — auf modernem macOS in einer venv, da
System-Python `pip install` per PEP 668 blockiert:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

- `.[ai]` installiert `rembg[cpu]` inkl. `onnxruntime` (KI-Hintergrundentfernung).
- Ohne KI-Funktion reicht: `python3 -m pip install -c requirements/constraints.txt -e .`

## Startvarianten

Nach der Installation gibt es drei Wege, das Programm zu starten:

| Variante | Befehl / Aktion | Ergebnis |
|----------|-----------------|----------|
| **A – macOS-App (empfohlen)** | `bash create_BgRemover_app.sh` | Legt eine isolierte venv an, installiert alle Abhängigkeiten (inkl. `onnxruntime`), kopiert die Icons und erzeugt ein eigenständiges `BgRemover.app` unter `~/Applications`. Quarantäne wird automatisch entfernt; das Projekt darf in `~/Documents` bleiben. |
| **B – Doppelklick** | `BgRemover.command` im Finder doppelklicken | Startet im Terminalfenster; nutzt automatisch die vom Skript angelegte App-venv (Datei ist bereits ausführbar). |
| **C – Terminal** | in einer venv: `python3 -m bgremover` | Direkter Start (venv-Setup siehe Schnellstart oben). |

## Installation aus einem Branch (offene PRs testen)

PR-Branch-Namen stehen im jeweiligen Pull Request auf GitHub
(„… wants to merge … from **`<branch>`**").

**Variante 1 – im vorhandenen Klon-Verzeichnis:**
```bash
cd picture_helper
git fetch origin
git branch -r                       # verfügbare Branches anzeigen
git checkout <branch>
# in venv (siehe Schnellstart); nur nötig, wenn sich Abhängigkeiten geändert haben:
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

Alternativ auch auf einem Branch einfach `bash create_BgRemover_app.sh`
ausführen — das übernimmt venv und Abhängigkeiten automatisch mit dem
committeten Constraint-Snapshot aus `requirements/constraints.txt`.

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

- **App startet nicht / Doppelklick passiert nichts** → Seit v3 zeigt
  die App einen Fehlerdialog mit „Log öffnen". Häufigste Ursache:
  `PyQt6` ist nicht in dem Python installiert, das die App nutzt
  (z. B. weil `pip install` in eine venv oder ein anderes Python ging,
  oder Homebrew-Python `pip install` per PEP 668 blockiert). Lösung:
  `bash create_BgRemover_app.sh` erneut ausführen und die venv anlegen
  lassen (Vorschlag mit Enter bestätigen) — das Skript installiert die
  Abhängigkeiten dann in eine venv unter
  `~/Library/Application Support/BgRemover/venv` und backt dieses Python
  in die App.
- **`[Errno 1] Operation not permitted` beim Zugriff auf das Projekt**
  → macOS-Datenschutz (TCC). Liegt das Projekt in `~/Documents`,
  `~/Desktop`, `~/Downloads` oder iCloud Drive, darf eine aus dem
  Finder gestartete `.app` dort nicht lesen. Seit Runde 5 (Paket-
  Schnitt) ist das gelöst: `create_BgRemover_app.sh` installiert das
  `bgremover`-Paket **nicht-editierbar** in die venv unter
  `~/Library/Application Support/BgRemover/venv` (eigene Kopie des
  Codes inkl. `icons/`-Paket-Daten), die App ist damit unabhängig vom
  Projektordner. Lösung: einmal `bash create_BgRemover_app.sh` neu
  ausführen. (Alternativ das Projekt nach z. B. `~/picture_helper`
  verschieben und das Skript dort erneut ausführen.)
- **`numpy ... incompatible architecture (have 'arm64', need 'x86_64')`**
  → Apple Silicon: in `~/Library/Python/...` liegt ein arch-fremdes
  Paket, das in einen mismatched Python „durchblutet". Seit v3.1 ist
  das gelöst: der Launcher setzt `PYTHONNOUSERSITE=1` (user-site wird
  ignoriert), erzwingt die native CPU-Architektur und es wird zwingend
  eine isolierte venv genutzt. Lösung: am besten zuerst einen nativen
  Python installieren, dann neu bauen:
  ```bash
  brew install python
  bash create_BgRemover_app.sh   # venv-Abfrage mit Enter bestätigen
  ```
- **Fehler direkt sehen (manuelle Diagnose)** → Launcher im Terminal
  starten, dann erscheint die echte Fehlermeldung:
  ```bash
  ~/Applications/BgRemover.app/Contents/MacOS/BgRemover
  ```
  Erwartbar bei fehlenden Paketen: `ModuleNotFoundError: No module named 'PyQt6'`.
- **„python3: command not found"** → `brew install python`
- **pip-Fehler beim Installieren** → erst pip aktualisieren:
  ```bash
  python3 -m pip install --upgrade pip
  ```
  danach den Install-Befehl erneut ausführen.
- **Erster KI-Klick dauert lange** → Beim allerersten Mal lädt `rembg`
  sein Modell herunter (einige hundert MB, einmalig, Cache in
  `~/.u2net`). Die Statusleiste zeigt „🤖 KI-Modell wird geladen…"
  und danach „🤖 KI bereit".
- **Gatekeeper: „nicht verifizierter Entwickler"** → Rechtsklick auf
  `BgRemover.app` → **Öffnen**. Das Build-Skript entfernt die
  Quarantäne bereits per `xattr`, ein Rechtsklick-Öffnen genügt im
  Zweifel trotzdem.
- **App stürzt mit „No onnxruntime backend found" ab** → Neuere
  `rembg`-Versionen liefern das Backend nicht mehr mit. Aktuell behoben
  (das `ai`-Extra zieht `rembg[cpu]`/`onnxruntime`; fehlt es dennoch,
  startet die App ohne KI statt abzustürzen). Lösung: einmal
  `bash create_BgRemover_app.sh` neu bauen — oder ins venv nachinstallieren:
  `"~/Library/Application Support/BgRemover/venv/bin/python3" -m pip install "rembg[cpu]"`.
- **`.app` sieht anders aus als `BgRemover.command`** → Älteres Bundle
  ohne Toolbar-Icons (App nutzte gezeichnete Ersatz-Icons). Aktuell
  behoben — seit Runde 5 sind die Icons `package-data` in `bgremover/
  icons/`, werden also bei `pip install` automatisch in die venv
  übernommen und über `importlib.resources` geladen; einmal
  `bash create_BgRemover_app.sh` neu bauen.
- **Diagnose bei Fehlern** → Logdatei `~/.bgremover.log` ansehen.
