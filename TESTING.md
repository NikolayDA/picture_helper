**Deutsch** · [README](README.md) · [Anleitung](ANLEITUNG.md) · [Installation macOS](INSTALL_MAC.md) · [Installation Linux](INSTALL_LINUX.md)

# BgRemover – Tests ausführen

Diese Anleitung beschreibt, wie die Tests **lokal auf dem Mac** laufen
und **wann sie auf GitHub** automatisch ausgeführt werden.

## Warum diese Änderung?

Die GitHub-Actions-Test-Matrix (Ubuntu + macOS × Python 3.10/3.12) lief
früher bei **jedem Push und jedem Pull Request** – das wurde auf Dauer
zu teuer (vor allem die macOS-Runner). Seit jetzt gilt:

| Wo                 | Wann                                                                 |
|--------------------|----------------------------------------------------------------------|
| **GitHub PR CI**   | bei jedem Pull Request auf `main`/`master` (Ubuntu + Python 3.12)     |
| **GitHub Full CI** | nur beim **Veröffentlichen eines Releases** oder **manuell**          |
| **Lokal/Mac**      | jederzeit per `make` – dieselben Prüfungen wie die PR-CI plus UI bei Bedarf |

Der zweite Workflow `License Check` ist davon **nicht** betroffen und
läuft weiterhin bei Pull Requests und auf `main`/`master`.

## Voraussetzungen (einmalig)

Im Projektordner eine virtuelle Umgebung anlegen und die Test-Werkzeuge
installieren:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ".[test]"
```

Damit stehen `pytest`, `pytest-qt`, `ruff` und `mypy` bereit. Auf macOS
sind **keine zusätzlichen System-Bibliotheken** nötig – die PyQt6-Wheels
bringen Qt mit.

Für die Test-Referenz wird bewusst eine normale Paketinstallation
verwendet. So prüfen die Smoke-Tests das installierte Paket aus einem
fremden Arbeitsverzeichnis – genau wie CI, Release-Build und App-Bundle.
Nach Änderungen an Paketcode, Startern oder Paketdaten vor `make check`
einmal erneut `pip install ".[test]"` ausführen.

> **Nur `[test]` ins Test-venv** – **nicht** `[ai]` oder `[docs]`. Das
> `ai`-Extra (`rembg`) gehört in die *Anwendungs*-Umgebung (das
> App-Bundle bringt sein eigenes venv mit), nicht in die Test-Umgebung.
> Die CI installiert ebenfalls nur `[test]`. Ein im Test-venv
> installiertes `rembg` würde den rembg-Warmup scharf schalten (Modell-
> Download über das Netz) – die Tests fangen das zwar zentral ab (kein
> echter Warmup im Testlauf), aber das Extra hat dort schlicht nichts
> verloren und bläht die Umgebung nur auf.

> Bei jeder neuen Terminal-Sitzung zuerst `source .venv/bin/activate`.

### Unterstützte Python-Version

Offiziell getestet ist **Python 3.10–3.13** (siehe `pyproject.toml`-
Classifier). **Python 3.14 funktioniert in der Praxis ebenfalls**,
sofern **PyQt6 ≥ 6.11** installiert ist – diese Version bringt
`cp314`-Wheels mit funktionierendem `offscreen`-Plattform-Plugin mit.
Ältere PyQt6-Builds haben für 3.14 **kein** lauffähiges
`offscreen`-Plugin; der QApplication-Start bricht dann hart mit
`Fatal Python error: Aborted` (SIGABRT) ab. Welche Version das venv
nutzt, zeigt `python --version` (bzw. der Pfad `.venv/lib/pythonX.Y/`).

Bei `Fatal Python error: Aborted` unter Python 3.14 zuerst PyQt6
aktualisieren:

```bash
pip install -U PyQt6
```

Hilft das nicht (oder ist eine ältere PyQt6-Version vorgegeben), das
venv gezielt auf einer offiziell getesteten Version neu aufbauen:

```bash
rm -rf .venv
python3.12 -m venv .venv          # oder python3.13
source .venv/bin/activate
pip install ".[test]"
```

`tests/conftest.py` prüft die Qt-Umgebung vor dem ersten GUI-Test in
einem isolierten Subprozess. Schlägt der QApplication-Start fehl, bricht
der Lauf **sauber mit einer erklärenden Meldung** (inkl. der echten
Qt-Fehlerausgabe) ab – statt mit einem unleserlichen SIGABRT-Stacktrace.

## Tests lokal ausführen (`make`)

Im Projektordner (venv aktiv):

| Befehl       | Was passiert                                                              |
|--------------|---------------------------------------------------------------------------|
| `make check` | **Schnelle PR-Prüfung:** `ruff` + `mypy` + `pytest` – exakt wie die PR-CI (UI-Tests ausgeschlossen) |
| `make pr-check` | Alias für `make check`, wenn der Name zur GitHub-PR-CI passen soll |
| `make ui`    | Nur die lokalen UI-Interaktionstests                                       |
| `make all`   | Alles zusammen (`check` + `ui`)                                            |
| `make lint`  | Nur `ruff` (Stil/Fehler)                                                   |
| `make type`  | Nur `mypy` (Typprüfung)                                                    |
| `make test`  | Nur `pytest` (ohne UI-Tests, wie die CI)                                   |

Empfohlener Ablauf vor einem Pull Request:

```bash
make check
```

Empfohlener Ablauf vor einem Release:

```bash
make all
```

Alles grün ⇒ der Stand entspricht lokal den automatischen PR-Prüfungen;
`make all` deckt zusätzlich die bewusst lokalen UI-Interaktionstests ab.

## Die UI-Tests

`tests/test_ui_interactions.py` enthält automatische, qtbot-gesteuerte
UI-Tests (Smoke, Zeichentools, Menü/Toolbar, Crop-Overlay,
SettingsDialog). Sie sind mit dem Marker `ui` versehen und laufen
**nur lokal**:

- `pytest` (Standard, und damit auch PR-CI/Full-CI) **überspringt** sie
  automatisch – konfiguriert über `addopts = "-q -m 'not ui'"` in
  `pyproject.toml`.
- `make ui` bzw. `pytest -m ui` führt **gezielt nur** diese Tests aus
  (das explizite `-m ui` hebt den Standard-Ausschluss auf).

Die Tests laufen headless über `QT_QPA_PLATFORM=offscreen` – es öffnet
sich also **kein Fenster**.

## Einzelne Tests / nützliche Aufrufe

```bash
# Eine einzelne Testdatei
python -m pytest tests/test_zoom.py

# Ein einzelner Test, ausführlich
python -m pytest tests/test_ui_interactions.py::test_crop_cancel -v

# Alle UI-Tests ausführlich
QT_QPA_PLATFORM=offscreen python -m pytest -m ui -v

# Registrierte Marker anzeigen (enthält 'ui')
python -m pytest --markers
```

## GitHub-Tests bei PR, manuell oder Release

**Pull Request:** Der Workflow **PR CI** läuft automatisch auf
Ubuntu/Python 3.12 und führt `make check` aus.

**Manuell:** Auf GitHub → Reiter **Actions** → Workflow **Full CI** →
Schaltfläche **Run workflow** → Branch wählen → starten. (Möglich dank
`workflow_dispatch`.)

**Automatisch:** Beim **Veröffentlichen eines Releases** (GitHub →
Releases → *Publish release*) startet die volle Matrix automatisch.
Ein bloßer Push löst die Test-Matrix **nicht** mehr aus; Pull Requests
bekommen stattdessen die leichte **PR CI**.

## Fehlerbehebung

- **`ModuleNotFoundError: No module named 'PyQt6'`** – venv nicht
  aktiviert oder Abhängigkeiten fehlen: `source .venv/bin/activate`
  und `pip install ".[test]"`.
- **`pytest`-Befehl nutzt die falsche Umgebung** – das Makefile ruft
  bewusst `python -m pytest` / `python -m ruff` / `python -m mypy`
  auf, um genau den venv-Interpreter zu verwenden. Bei manuellen
  Aufrufen ebenfalls `python -m pytest` statt nur `pytest` nutzen.
- **UI-Test öffnet ein Fenster / hängt** –
  `QT_QPA_PLATFORM=offscreen` setzen (geschieht in `make`/`conftest.py`
  automatisch).
- **UI-Tests laufen bei `pytest` nicht mit** – das ist beabsichtigt;
  `make ui` bzw. `pytest -m ui` verwenden.
- **`Fatal Python error: Aborted` / `Abort trap: 6` beim `qapp`-Fixture**
  – Qt kann das `offscreen`-Plugin nicht laden. Häufigste Ursache: ein
  zu altes PyQt6 für die genutzte Python-Version (v. a. Python 3.14).
  Erst `pip install -U PyQt6` (≥ 6.11) versuchen; hilft das nicht, das
  venv auf Python 3.12/3.13 neu aufbauen (siehe „Unterstützte
  Python-Version“ oben). `conftest.py` fängt den Fall ab und gibt eine
  klare Diagnose mit der echten Qt-Meldung aus statt eines
  unleserlichen SIGABRT-Stacktrace.
- **`Fatal Python error: Aborted` mit `rembg`/`pooch`/`download_models`
  im Stacktrace** – im Test-venv ist (fälschlich) das `ai`-Extra
  installiert; `MainWindow` startet dann den rembg-Warmup, der ein
  ~176 MB Modell übers Netz lädt – mehrere Tests parallel reißen den
  Prozess ab. `conftest.py` unterbindet den Warmup inzwischen zentral
  in allen Tests, der Lauf ist also auch dann offline und stabil.
  Sauber ist trotzdem ein Test-venv **ohne** `ai`/`docs`:
  `pip install ".[test]"` (siehe Hinweis unter „Voraussetzungen“).
