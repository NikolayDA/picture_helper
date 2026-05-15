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
