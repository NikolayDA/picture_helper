# Beitragen zu BgRemover

Danke für dein Interesse! Bugs, Verbesserungsvorschläge und Pull Requests sind willkommen.

## Inhaltsverzeichnis

1. [Verhaltenskodex](#verhaltenskodex)
2. [Fehler melden](#fehler-melden)
3. [Feature-Vorschläge](#feature-vorschläge)
4. [Entwicklungsumgebung einrichten](#entwicklungsumgebung-einrichten)
5. [Code beitragen](#code-beitragen)
6. [Konventionen](#konventionen)
7. [Tests](#tests)
8. [Dokumentation](#dokumentation)

---

## Verhaltenskodex

Konstruktiver, respektvoller Umgang ist Voraussetzung für Beiträge. Beleidigungen, Diskriminierung oder Trolling führen zum Ausschluss.

## Fehler melden

1. Zunächst prüfen, ob das Issue bereits existiert.
2. Ein neues Issue mit dem Template **Bug Report** öffnen.
3. Angaben: BgRemover-Version, Python-Version, Betriebssystem, reproduzierbare Schritte, erwartetes vs. tatsächliches Verhalten, ggf. Log-Ausschnitt (Log-Pfad: Einstellungen → Log-Datei anzeigen).

Sicherheitslücken bitte **nicht** als öffentliches Issue melden — siehe [SECURITY.md](SECURITY.md).

## Feature-Vorschläge

Ein Issue mit dem Template **Feature Request** öffnen und beschreiben:
- Welches Problem soll gelöst werden?
- Wie soll die Funktion bedienbar sein?
- Alternativen, die du bereits erwogen hast.

Größere Änderungen am Architektur vorab im Issue diskutieren, bevor Code geschrieben wird.

## Entwicklungsumgebung einrichten

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[test]"
```

Unter Linux werden Qt-Systembibliotheken benötigt:

```bash
sudo apt-get install -y \
  libgl1 libglib2.0-0 libdbus-1-3 libxkbcommon0 \
  libxcb1 libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
  libxcb-shape0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0 \
  libegl1 libxcb-util1
```

Prüfen, ob alles in Ordnung ist:

```bash
make doctor
```

## Code beitragen

1. Repository forken und einen Feature-Branch anlegen:
   ```bash
   git checkout -b feature/kurze-beschreibung
   ```
2. Änderungen vornehmen — die [Konventionen](#konventionen) beachten.
3. Tests schreiben oder anpassen (siehe [Tests](#tests)).
4. Gate lokal bestehen lassen:
   ```bash
   make check
   ```
5. Commit mit aussagekräftiger Nachricht (Englisch oder Deutsch, Imperativ):
   ```
   feat(canvas): Drehen via Tastenkürzel ergänzen
   fix(workers): Race-condition beim Abbruch beheben
   ```
6. Pull Request gegen `main` öffnen und das PR-Template ausfüllen.

Pull Requests, die `make check` nicht bestehen, werden nicht gemergt.

## Konventionen

| Bereich | Regel |
|---------|-------|
| **Sprache (Kommentare/Docstrings)** | Deutsch |
| **Sprache (Code-Identifier, Commits, PR-Titel)** | Englisch oder Deutsch |
| **Zeilenlänge** | 100 Zeichen (ruff, `E501` ignoriert) |
| **Linter** | `ruff check` mit Regeln `E,F,W,I,B,UP,SIM` |
| **Formatter** | `ruff format` |
| **Typprüfung** | `mypy` (Qt-arme Module streng, Qt-lastige laxer) |
| **Stil** | Kompakt — keine unnötigen Zwischenzeilen oder Kommentare |

Der bestehende Stil (Dateilänge, Kompaktheit, deutschen Kommentare) soll erhalten bleiben. Keine unnötigen Refactorings außerhalb des eigentlichen Änderungsbereichs.

## Tests

```bash
make test        # CI-Subset (ohne volle UI-Suite)
make coverage    # Coverage-Report (Schwelle: 86 %)
make ui          # Volle qtbot-UI-Suite (nur bei Bedarf / nightly)
```

Für headless-Umgebungen (Server, CI) muss `QT_QPA_PLATFORM=offscreen` gesetzt sein — `make` erledigt das automatisch.

Neue Features brauchen Tests. Bugfixes idealerweise einen Regressionstest. Marker:
- `@pytest.mark.ui` — volle UI-Tests (nightly)
- `@pytest.mark.ui_smoke` — leichtgewichtige UI-Tests (laufen in CI mit)

## Dokumentation

BgRemover ist mehrsprachig (Deutsch, Englisch, Spanisch, Französisch, Ukrainisch, Chinesisch). Änderungen an deutschen Basisdokumenten (`README.md`, `ANLEITUNG.md`, `CHANGELOG.md` usw.) müssen in den entsprechenden `docs/i18n/`-Dateien gespiegelt werden, damit die i18n-Paritätstests grün bleiben.

Markdown-Links werden durch Tests geprüft — keine toten Links einführen.

## Fragen?

Ein Issue öffnen oder auf einen bestehenden PR/Issue antworten. Danke für deinen Beitrag!
