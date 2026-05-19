**Deutsch** · [README](README.md) · [Anleitung](ANLEITUNG.md) · [Installation macOS](INSTALL_MAC.md) · [Installation Linux](INSTALL_LINUX.md)

# BgRemover – Tests ausführen

Diese Anleitung beschreibt, wie die Tests **lokal auf dem Mac** laufen
(als Ersatz für die früheren GitHub-Läufe bei jedem Push) und **wann sie
auf GitHub** noch automatisch ausgeführt werden.

## Warum diese Änderung?

Die GitHub-Actions-Test-Matrix (Ubuntu + macOS × Python 3.10/3.12) lief
früher bei **jedem Push und jedem Pull Request** – das wurde auf Dauer
zu teuer (vor allem die macOS-Runner). Seit jetzt gilt:

| Wo            | Wann                                                        |
|---------------|-------------------------------------------------------------|
| **GitHub CI** | nur beim **Veröffentlichen eines Releases** oder **manuell** |
| **Lokal/Mac** | jederzeit per `make` – ersetzt die alten Push-Läufe         |

Der zweite Workflow `License Check` ist davon **nicht** betroffen und
läuft weiterhin bei Pull Requests.

## Voraussetzungen (einmalig)

Im Projektordner eine virtuelle Umgebung anlegen und die Test-Werkzeuge
installieren:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

Damit stehen `pytest`, `pytest-qt`, `ruff` und `mypy` bereit. Auf macOS
sind **keine zusätzlichen System-Bibliotheken** nötig – die PyQt6-Wheels
bringen Qt mit.

> Bei jeder neuen Terminal-Sitzung zuerst `source .venv/bin/activate`.

## Tests lokal ausführen (`make`)

Im Projektordner (venv aktiv):

| Befehl       | Was passiert                                                              |
|--------------|---------------------------------------------------------------------------|
| `make check` | **Ersatz für die GitHub-Tests:** `ruff` + `mypy` + `pytest` – exakt die CI-Schritte (UI-Tests ausgeschlossen) |
| `make ui`    | Nur die lokalen UI-Interaktionstests                                       |
| `make all`   | Alles zusammen (`check` + `ui`)                                            |
| `make lint`  | Nur `ruff` (Stil/Fehler)                                                   |
| `make type`  | Nur `mypy` (Typprüfung)                                                    |
| `make test`  | Nur `pytest` (ohne UI-Tests, wie die CI)                                   |

Empfohlener Ablauf vor dem Pushen / vor einem Release:

```bash
make all
```

Alles grün ⇒ der Stand entspricht dem, was die GitHub-CI beim Release
ebenfalls prüfen würde.

## Die UI-Tests

`tests/test_ui_interactions.py` enthält automatische, qtbot-gesteuerte
UI-Tests (Smoke, Zeichentools, Menü/Toolbar, Crop-Overlay,
SettingsDialog). Sie sind mit dem Marker `ui` versehen und laufen
**nur lokal**:

- `pytest` (Standard, und damit auch die GitHub-CI) **überspringt** sie
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

## GitHub-Tests manuell oder bei Release auslösen

**Manuell:** Auf GitHub → Reiter **Actions** → Workflow **CI** →
Schaltfläche **Run workflow** → Branch wählen → starten. (Möglich dank
`workflow_dispatch`.)

**Automatisch:** Beim **Veröffentlichen eines Releases** (GitHub →
Releases → *Publish release*) startet die volle Matrix automatisch.
Ein bloßer Push oder ein Pull Request löst die Test-Matrix **nicht**
mehr aus.

## Fehlerbehebung

- **`ModuleNotFoundError: No module named 'PyQt6'`** – venv nicht
  aktiviert oder Abhängigkeiten fehlen: `source .venv/bin/activate`
  und `pip install -e ".[test]"`.
- **`pytest`-Befehl nutzt die falsche Umgebung** – das Makefile ruft
  bewusst `python -m pytest` / `python -m ruff` / `python -m mypy`
  auf, um genau den venv-Interpreter zu verwenden. Bei manuellen
  Aufrufen ebenfalls `python -m pytest` statt nur `pytest` nutzen.
- **UI-Test öffnet ein Fenster / hängt** –
  `QT_QPA_PLATFORM=offscreen` setzen (geschieht in `make`/`conftest.py`
  automatisch).
- **UI-Tests laufen bei `pytest` nicht mit** – das ist beabsichtigt;
  `make ui` bzw. `pytest -m ui` verwenden.
