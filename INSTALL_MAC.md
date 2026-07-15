**Deutsch** · [English](docs/i18n/en/INSTALL_MAC.md) · [Español](docs/i18n/es/INSTALL_MAC.md) · [Français](docs/i18n/fr/INSTALL_MAC.md) · [Українська](docs/i18n/uk/INSTALL_MAC.md) · [简体中文](docs/i18n/zh/INSTALL_MAC.md)

# BgRemover – Installation auf dem Mac

Kurzanleitung zum Installieren und Starten von BgRemover aus GitHub —
sowohl aus dem `main`-Branch als auch aus einem Feature-Branch (z. B.
um einen offenen Pull Request vor dem Merge zu testen).

## Fertige App herunterladen (`.dmg`)

Der einfachste Weg – **ohne Python, git oder Terminal**: das fertige
App-Bundle aus den [GitHub-Releases](https://github.com/NikolayDA/picture_helper/releases)
laden. Für Apple Silicon (arm64) gibt es `BgRemover-<Version>-macos-arm64-ai.dmg`
(der Dateiname nennt Plattform und Architektur); die KI-Hintergrundentfernung
ist bereits eingebaut — erkennbar am `-ai`-Suffix, wie bei den Linux-Artefakten.

1. `.dmg` öffnen und `BgRemover.app` in den Ordner **Programme** ziehen.
2. Beim **ersten** Start per **Rechtsklick → „Öffnen"** bestätigen – das Bundle
   ist noch nicht von Apple signiert/notarisiert, daher warnt Gatekeeper sonst
   vor einem „nicht verifizierten Entwickler".

Alternativ lässt sich die Quarantäne vorab im Terminal entfernen:

```bash
xattr -dr com.apple.quarantine /Applications/BgRemover.app
```

Wer lieber aus dem Quellcode baut (z. B. für Intel-Macs oder eigene
Anpassungen), folgt den Abschnitten unten.

## Voraussetzungen

- **macOS**
- **Python 3.10 oder neuer** — prüfen mit:
  ```bash
  python3 --version
  ```
- **git**

> **KI-Hinweis:** Die Kern-App läuft mit Python 3.10+. Die
> KI-Hintergrundentfernung (`.[ai]`) benötigt **Python 3.11 oder neuer**
> (die aktuellen `onnxruntime`- und `rembg`-Builds zielen auf Python 3.11+).

Falls Python oder git fehlen, am einfachsten über [Homebrew](https://brew.sh):
```bash
brew install python git
```

## Schnellstart aus `main`

**Empfohlen** ist das App-Bundle-Skript — es legt automatisch eine
dedizierte App-venv unter `~/Library/Application Support/BgRemover/venv`
an, installiert das aktuelle Checkout nicht-editierbar samt Icons,
versucht die KI-Abhängigkeiten inkl. `onnxruntime` zu installieren und
behandelt Apple Silicon korrekt:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

Falls die App-venv neu angelegt wird, den Hinweis mit **Enter**
bestätigen; danach `BgRemover.app` unter `~/Applications` per Doppelklick
starten.

**Direkter Terminal-Start** — auf modernem macOS in einer venv, da
System-Python `pip install` per PEP 668 blockiert:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

- `.[ai]` installiert `rembg[cpu]` inkl. `onnxruntime` (KI-Hintergrundentfernung).
- Ohne KI-Funktion reicht: `python3 -m pip install -c requirements/constraints.txt -e .`

## Startvarianten

Nach der Installation gibt es drei Wege, das Programm zu starten:

| Variante | Befehl / Aktion | Ergebnis |
|----------|-----------------|----------|
| **A – macOS-App (empfohlen)** | `bash create_BgRemover_app.sh` | Aktualisiert eine dedizierte App-venv, versucht die KI-Abhängigkeiten inkl. `onnxruntime` zu installieren und erzeugt einen `BgRemover.app`-Launcher unter `~/Applications`. App und venv gehören zusammen; das Projekt darf in `~/Documents` bleiben. |
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
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

Alternativ auch auf einem Branch einfach `bash create_BgRemover_app.sh`
ausführen — das übernimmt venv und Abhängigkeiten automatisch mit dem
committeten Constraint-Snapshot aus `requirements/constraints.txt` und
installiert das aktuelle Checkout neu in die App-venv.

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

Für das App-Bundle nach einem Update oder Branch-Wechsel einfach
`bash create_BgRemover_app.sh` erneut ausführen. Das Skript aktualisiert
die nicht-editierbare Paketkopie in der App-venv automatisch.

## Troubleshooting

- **App startet nicht / Doppelklick passiert nichts** → Die App zeigt
  einen Fehlerdialog mit „Log öffnen". Häufigste Ursache:
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
  Finder gestartete `.app` dort nicht lesen. Der Paket-Schnitt löst das:
  `create_BgRemover_app.sh` installiert das
  `bgremover`-Paket **nicht-editierbar** in die venv unter
  `~/Library/Application Support/BgRemover/venv` (eigene Kopie des
  Codes inkl. `icons/`-Paket-Daten), die App ist damit unabhängig vom
  Projektordner. Lösung: einmal `bash create_BgRemover_app.sh` neu
  ausführen. (Alternativ das Projekt nach z. B. `~/picture_helper`
  verschieben und das Skript dort erneut ausführen.)
- **`numpy ... incompatible architecture (have 'arm64', need 'x86_64')`**
  → Apple Silicon: in `~/Library/Python/...` liegt ein arch-fremdes
  Paket, das in einen mismatched Python „durchblutet". Der Launcher
  setzt `PYTHONNOUSERSITE=1` (user-site wird
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
  Noch bequemer: `bash diagnose_mac.sh` im Projektordner sammelt diese
  Startdiagnose automatisch (inkl. `pip show bgremover` der App-venv); die
  Ausgabe ist standardmäßig redigiert und kann an einen Bug-Report angehängt
  werden.
- **„python3: command not found"** → `brew install python`
- **pip-Fehler beim Installieren** → erst pip aktualisieren:
  ```bash
  python3 -m pip install --upgrade "pip>=26.1.2"
  ```
  danach den Install-Befehl erneut ausführen.
- **KI-Button bleibt nach dem Start kurz deaktiviert** → Das ist kein
  Installationsfehler: Sobald `rembg` installiert ist, lädt die App
  automatisch beim **App-Start** (nicht erst beim ersten KI-Klick)
  einmalig ihr Modell herunter (einige hundert MB, Cache in
  `~/.u2net`). Die Statusleiste zeigt währenddessen „KI-Modell wird
  geladen…" und danach „KI bereit"; der KI-Button bleibt bis dahin
  (und ohne geladenes Bild ohnehin) deaktiviert. Ist der Download offline
  fehlgeschlagen, lässt sich der Status jederzeit über `Extras → KI-Modell
  verwalten…` prüfen und ein erneuter Download/Retry manuell auslösen.
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
  ohne Toolbar-Icons (App nutzte gezeichnete Ersatz-Icons). Die Icons
  sind `package-data` in `bgremover/icons/` und werden bei `pip install`
  automatisch in die venv
  übernommen und über `importlib.resources` geladen; einmal
  `bash create_BgRemover_app.sh` neu bauen.
- **Diagnose bei Fehlern** → Der Bundle-Launcher schreibt Startdiagnosen
  nach `~/Library/Application Support/BgRemover/bgremover.log`. Den
  genauen Pfad des internen Laufzeit-Logs zeigt
  `Extras → Einstellungen… → Protokolldatei`; unter der aktuellen
  macOS-Konfiguration ist es
  `~/Library/Application Support/BgRemover/BgRemover/bgremover.log`.
