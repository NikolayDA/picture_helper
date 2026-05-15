# BgRemover – Installation auf dem Mac

Kurzanleitung zum Installieren und Starten von BgRemover aus GitHub —
sowohl aus dem `main`-Branch als auch aus einem Feature-Branch (z. B.
um einen offenen Pull Request vor dem Merge zu testen).

## Voraussetzungen

- **macOS**
- **Python 3.9 oder neuer** — prüfen mit:
  ```bash
  python3 --version
  ```
- **git**

Falls Python oder git fehlen, am einfachsten über [Homebrew](https://brew.sh):
```bash
brew install python git
```

## Schnellstart aus `main`

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m pip install -e ".[ai]"
python3 BgRemover.py
```

- `.[ai]` installiert auch `rembg` (KI-Hintergrundentfernung).
- Ohne KI-Funktion reicht: `python3 -m pip install -e .`

## Startvarianten

Nach der Installation gibt es drei Wege, das Programm zu starten:

| Variante | Befehl / Aktion | Ergebnis |
|----------|-----------------|----------|
| **A – macOS-App** | `bash create_BgRemover_app.sh` | Legt `BgRemover.app` unter `~/Applications` an (Doppelklick im Finder/Dock), entfernt die Quarantäne automatisch |
| **B – Doppelklick** | `chmod +x BgRemover.command`, dann im Finder doppelklicken | Startet die App über ein Terminalfenster |
| **C – Terminal** | `python3 BgRemover.py` | Direkter Start |

## Installation aus einem Branch (offene PRs testen)

PR-Branch-Namen stehen im jeweiligen Pull Request auf GitHub
(„… wants to merge … from **`<branch>`**").

**Variante 1 – im vorhandenen Klon-Verzeichnis:**
```bash
cd picture_helper
git fetch origin
git branch -r                       # verfügbare Branches anzeigen
git checkout claude/selection-features-03824
python3 -m pip install -e ".[ai]"   # nur nötig, wenn sich Abhängigkeiten geändert haben
python3 BgRemover.py
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
`pyproject.toml` haben sich geändert.

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
- **`[Errno 1] Operation not permitted` beim Öffnen von `BgRemover.py`**
  → macOS-Datenschutz (TCC). Liegt das Projekt in `~/Documents`,
  `~/Desktop`, `~/Downloads` oder iCloud Drive, darf eine aus dem
  Finder gestartete `.app` dort nicht lesen. Seit v3 ist das gelöst:
  `BgRemover.py` wird ins App-Bundle kopiert und die venv liegt in
  Application Support — `bash create_BgRemover_app.sh` einmal neu
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
- **Diagnose bei Fehlern** → Logdatei `~/.bgremover.log` ansehen.
