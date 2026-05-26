**Deutsch** · [English](docs/i18n/en/CHANGELOG.md) · [Español](docs/i18n/es/CHANGELOG.md) · [Français](docs/i18n/fr/CHANGELOG.md) · [Українська](docs/i18n/uk/CHANGELOG.md) · [简体中文](docs/i18n/zh/CHANGELOG.md)

# Changelog

Alle nennenswerten Änderungen an BgRemover werden in dieser Datei
dokumentiert. Das Format orientiert sich an
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/); das Projekt
folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Geändert

- **CI-Testmatrix erweitert.** Der Full-CI-Workflow prüft jetzt Python
  3.10, 3.11, 3.12 und 3.13 auf Ubuntu und macOS.

### Entfernt

- **Toten Code aus Canvas, Lasso und MainWindow entfernt.** Der ungenutzte
  Schatten-Zähler `ImageCanvas._version`, die nicht mehr referenzierte
  Methode `CanvasLasso.close_to_mask` und die ungenutzte Toolbar-Button-
  Group-Referenz `MainWindow._btn_grp` sind ersatzlos entfallen.

## [2.2.0] – 2026-05-25

### Hinzugefügt

- **Reproduzierbarer Dependency-Snapshot** (`requirements/constraints.txt`).
  Makefile, Lizenz-Workflow und macOS-App-Build verwenden denselben
  committeten Constraint-Satz für Test-, CI-, Lizenz- und App-Bundle-
  Installationen.
- **Lokaler Testumgebungs-Doctor** (`make doctor`,
  `scripts/check_test_env.py`). Prüft Python-Version, `[test]`-
  Abhängigkeiten, nicht-editable Paketinstallation, `bgremover`-
  Console-Script und Qt-`offscreen`, bevor ein lokaler Lauf tief in
  Pytest scheitert.
- **CI-Smoke-Test für den App-Start** (`tests/test_app_smoke.py`). Die
  bisherigen UI-Tests sind in der CI über `-m 'not ui'` ausgeschlossen,
  d. h. die CI prüfte nie, ob sich die Anwendung überhaupt vollständig
  starten lässt – genau die Lücke, durch die die macOS-Startfehler
  unbemerkt blieben. Neu, ohne `ui`-Marker (läuft also in der CI):
  `python -m bgremover` und das Console-Script `bgremover` werden aus
  einem neutralen Arbeitsverzeichnis vollständig hochgefahren (neuer
  Selbsttest-Hook `BGREMOVER_SMOKE_TEST` beendet nach dem ersten
  Event-Loop-Tick mit Exit-Code 0); das Qt-Plugin-Setup wird auf einen
  gültigen Plugin-Pfad geprüft; die Starter-Skripte
  (`create_BgRemover_app.sh`, `BgRemover.command`, `diagnose_mac.sh`)
  sowie der ins App-Bundle eingebackene Launcher werden auf
  Shell-Syntax geprüft. `zsh` wird dafür im Linux-CI-Job mitinstalliert.

### Geändert

- **MainWindow weiter modularisiert.** Die Persistenz- und Menülogik für
  „Zuletzt geöffnet“ liegt jetzt in `bgremover/recent_files.py`; `MainWindow`
  delegiert nur noch Laden, Statusmeldung und Einbindung ins Dateimenü.
- **Menü-/Action-Aufbau aus `MainWindow` extrahiert.** `bgremover/menu_actions.py`
  baut Menüleiste, `QAction`s, Shortcuts und Recent-Files-Untermenü; `MainWindow`
  übergibt nur noch die fachlichen Callbacks.
- **Rechtes Tab-Panel aus `MainWindow` extrahiert.** `bgremover/right_panel.py`
  baut Auswahl-, Hintergrund-, Transform- und Form-Tab inklusive Slider,
  Spinboxen und Panel-Buttons; `MainWindow` übergibt nur noch Canvas-Callbacks.
- **Worker-Steuerung aus `MainWindow` gekapselt.** `bgremover/worker_controller.py`
  besitzt jetzt Lade-, KI- und Warmup-Threads inklusive starker Worker-Referenz,
  `deleteLater`-Verdrahtung und gemeinsamem Shutdown.

### Behoben

- **Release-/Changelog-Links auf reale Refs korrigiert.**
  `[Unreleased]` vergleicht ab `v2.1.0`; `[2.1.0]` nutzt den
  dokumentierten 2.0.0-Release-Commit als Basis, weil im Repo kein
  historischer `v2.0.0`-Tag existiert.
- **KI-Ergebnisse werden nach Zwischenbearbeitungen verworfen.** Der
  Stale-Check nutzt eine öffentliche Canvas-Version, die der
  Content-Revision folgt und bei jeder sichtbaren Bildänderung steigt
  (z. B. Drehen, Zuschnitt, Undo). Dadurch überschreibt ein spät
  eintreffendes `rembg`-Ergebnis keine inzwischen bearbeiteten Bilder
  mehr.
- **App-Bundle: `bgremover`-Erkennung im Setup unabhängig vom
  Arbeitsverzeichnis.** `create_BgRemover_app.sh` stufte die venv als
  „fertig" ein, obwohl `bgremover` dort gar nicht installiert war: der
  `has_deps`-Check lief mit `cwd` im Projektordner, und Python hängt
  das aktuelle Verzeichnis automatisch an `sys.path[0]` – dadurch fand
  `import bgremover` das `bgremover/`-**Quellverzeichnis** des Repos
  statt einer echten venv-Installation. Der App-Launcher startet mit
  anderem `cwd`, sieht das Quellverzeichnis nicht und meldete deshalb
  „Das bgremover-Paket fehlt in der venv". `has_deps` und der finale
  Sanity-Check laufen jetzt aus `$HOME` (Subshell `cd "$HOME"`), prüfen
  also dieselbe Realität wie der Launcher; fehlt das Paket, greift der
  pip-Install-Schnellpfad. `diagnose_mac.sh` testet ebenfalls aus
  `$HOME` und zeigt zusätzlich `pip show bgremover` der App-venv
  (cwd-unabhängiger Beweis, ob/wohin das Paket installiert ist).
- **macOS-Startwege wieder funktionsfähig.** Nach dem Paket-Schnitt
  (Runde 5) suchte `BgRemover.command` weiterhin die nicht mehr
  existierende `BgRemover.py` und brach mit „nicht gefunden" ab; auch
  `INSTALL_MAC.md` (deutsch) plus die i18n-Versionen von
  `INSTALL_LINUX.md`/`README.md` zeigten teils noch die alten Kommandos
  (Schritt 15 des Paket-Schnitts hatte das deutsche `INSTALL_MAC.md`
  und die i18n-Installations-Doku im Glob übersehen, sowie
  `Exec=python3 /PFAD/.../BgRemover.py` in den i18n-`.desktop`-Mustern).
  Folge: auf macOS war keiner der drei dokumentierten Start-Wege
  (App-Bundle, Doppelklick auf `.command`, Terminal) verlässlich
  benutzbar. `BgRemover.command` startet jetzt via `python3 -m
  bgremover` und prüft vorab `import bgremover` (sonst sprechender
  Hinweis auf `create_BgRemover_app.sh`). INSTALL_MAC + alle i18n-Docs
  spiegeln das aktuelle Paket-Modell (inkl. nicht-editable Install des
  Pakets in die App-venv und `importlib.resources`-Asset-Lookup).
- **`create_BgRemover_app.sh`: bestehende venv wird sauber migriert.**
  Eine venv aus der Monolith-Ära (PyQt6/Pillow/numpy installiert, aber
  natürlich noch ohne `bgremover`) galt fälschlich als „ready", weil
  der Setup-Check `has_deps` `bgremover` nicht prüfte. Beim re-run des
  Skripts wurde das Paket-Install daher übersprungen – und der
  App-Launcher meldete dann zur Laufzeit „Das bgremover-Paket fehlt
  in der venv". Der Check umfasst nun auch `import bgremover`;
  zusätzlich gibt es einen Schnellpfad: existiert die App-venv schon
  mit PyQt6/Pillow/numpy, wird nur `pip install ".[ai]"` darin
  nachgeschoben (Sekunden), statt die venv mit allen Dependencies neu
  zu bauen (Minuten).

### Geändert

- **Pure Image-Operationen aus `ImageCanvas` gelöst.**
  `bgremover/image_ops.py` kapselt nun Hintergrund entfernen/ersetzen,
  Speichern, Drehen, Spiegeln, Ecken abrunden und Crop-Maskierung als
  Qt-freie PIL/NumPy-Funktionen. `ImageCanvas` behält UI-Zustand,
  Undo/Redo, Signale und Overlays; `tests/test_image_ops.py` prüft die
  Pixeloperationen direkt ohne `QApplication`.
- **Recommendations-Doku auf aktuellen Status gebracht.**
  `RECOMMENDATIONS.md` und die i18n-Versionen enthalten nun einen
  Runde-6-Statusblock für die jüngste PR-Serie (#70, #72–#78) und
  markieren die alten Monolith-Befunde ausdrücklich als historischen
  Kontext. `tests/test_recommendations_docs.py` schützt diesen Block.
- **Ressourcen-Doku synchronisiert.** `RESOURCES.md` und die i18n-
  Versionen spiegeln jetzt das Paketlayout (`bgremover/` statt
  `BgRemover.py`), die Paketdaten unter `bgremover/icons/`, den
  reproduzierbaren Constraints-Snapshot sowie PR-/Full-/Lizenz-
  Workflows. Ein statischer Test schützt diese Angaben gegen erneutes
  Veralten.
- **`make pr-check` macht die lokale PR-Prüfung robuster.** Der Target
  installiert das Paket frisch mit `[test]`, führt den Doctor aus und
  startet danach `ruff`, `mypy` und `pytest`. Das Makefile findet
  `.venv/bin/python` automatisch und fällt sonst auf `python`/`python3`
  zurück; GitHub PR CI und Full CI nutzen denselben Target. Das
  gemeinsame Qt-Plugin-Setup staged die Platform-Plugins bei Bedarf ins
  System-Temp-Verzeichnis, damit lokale macOS-Headless-Läufe nicht an
  Qt-Plugin-Listing-Problemen im Projektpfad scheitern.
- **Leichte PR-CI ergänzt und Test-Doku synchronisiert.** Pull Requests
  bekommen jetzt einen günstigen Ubuntu/Python-3.12-Workflow mit
  `make pr-check`; die volle Linux/macOS-Matrix bleibt Release- und
  manuellen Läufen vorbehalten. Die Test-Workflows installieren das
  Paket nicht-editable, damit die App-Smoke-Tests die installierte
  Realität aus fremdem `cwd` prüfen. `README`, i18n-READMEs,
  `TESTING.md` und `Makefile` beschreiben nun denselben Ablauf.
- **Monolith → Paket (Runde 5).** Die Einzeldatei `BgRemover.py`
  (3026 Zeilen) wurde in das installierbare Paket `bgremover/`
  aufgeteilt (14 Module: `constants`, `image_utils`, `icons`, `theme`,
  `workers`, `crop`, `canvas`, `widgets`, `settings_dialog`,
  `logging_config`, `main_window`, `app`, `__main__`, `__init__`).
  Start künftig via `python -m bgremover` oder dem Console-Script
  `bgremover`; die alte `python BgRemover.py`-Form entfällt
  ersatzlos. `BgRemover.py` ist gelöscht. Phasiert in **13 mechanischen
  Schritten** durchgeführt, jeder mit dem grünen Test-Oracle als Gate
  (140 Unit- + 16 UI-Tests, ruff, mypy). Einzige bewusste, verhaltens-
  neutrale Code-Änderung: `make_tool_icon` löst Icons jetzt über
  `importlib.resources` aus den Paket-Daten (`bgremover/icons/`) auf
  statt über `__file__`/`sys.argv`/`cwd` – Kontrakt unverändert.
  `pyproject.toml`, `Makefile`, CI-Workflow und macOS-Build-Skript
  (`create_BgRemover_app.sh`) sind im selben Schnitt mitgezogen; die
  venv installiert das Paket nicht-editierbar (inkl. package-data),
  daher unabhängig vom Projektordner.
- Übergangs-Re-Exporte in `BgRemover.py` (Phase B) und alle
  `BgRemover`-Test-Importe sind im finalen Schritt auf das Paket
  umgestellt.

## [2.1.0] – 2026-05-19

### Geändert

- Frühausstieg-Guard „Kein Bild geladen“ der fünf `ImageCanvas`-
  Methoden (`apply_round_corners`, `apply_rotate`, `apply_flip`,
  `start_crop_circle`, `start_crop_ratio`) im Decorator
  `@_requires_image` zusammengefasst – der zuvor byte-identisch
  wiederholte Block entfällt; Verhalten unverändert (durch die
  bestehende Test-Suite verteidigt).
- Hintergrund-Worker `AIWorker` und `ImageLoadWorker` nutzen jetzt die
  gemeinsame Basisklasse `_Worker`, die den identischen
  `try/except → logger.exception → error.emit`-Ablauf kapselt;
  Unterklassen implementieren nur noch `_work()`. `RembgWarmupWorker`
  bleibt bewusst eigenständig (kein `error`-Signal, `finished` stets im
  `finally`).
- Versions-Schnitt **2.1.0**: `pyproject.toml` und der
  `__version__`-Fallback in `BgRemover.py` auf `2.1.0` gehoben; die
  zuvor unter `[Unreleased]` gesammelten Änderungen (#48/#52/#53,
  INSTALL_LINUX, Runde 3/4) sind hiermit als 2.1.0 datiert.
- Interne Refaktorierung: Der in `_apply_pil`, `undo`, `redo`,
  `undo_to` und `restore_original` identische Bildzustands-Block
  (Pixmap setzen, Maske leeren, Ansicht aktualisieren) ist in die
  Helfer `_set_image_state()` / `_emit_history()` zusammengeführt.
  Verhalten unverändert (verteidigt durch die bestehende Test-Suite).
- UI-Farbpalette in `_Theme` zentralisiert: die mehrfach wiederholten
  Stylesheet-Farben (Akzent, Panel-/Tab-Hintergrund, Rahmen,
  Trennlinien, heller Text) verweisen jetzt auf eine zentrale Stelle,
  damit künftige UI-Erweiterungen konsistente Farben nutzen. Als
  byte-identisch verifiziert – alle 218 Widget-Stylesheets unverändert,
  kein visueller Unterschied.

### Entfernt

- Tote Stylesheet-Konstanten `BTN_STYLE` und `GRP_STYLE` (nirgends
  referenziert) entfernt.

### Behoben

- `save_image()` fängt E/A-Fehler ab (nicht beschreibbarer Pfad, voller
  Datenträger, unbekanntes Format) und meldet sie als Statusmeldung,
  statt unbehandelt zu propagieren – konsistent zu `apply_remove`/
  `apply_replace`. „Speichern unter…“ merkt einen fehlgeschlagenen Pfad
  nicht mehr als Quick-Save-Ziel.

### Dokumentation

- Installationsanleitung für Linux (`INSTALL_LINUX.md`) ergänzt:
  Systempakete je Distribution (apt/dnf/pacman), venv-Setup,
  Starter-Skript bzw. `.desktop`-Eintrag und Troubleshooting; im README
  verlinkt. Inkl. besonders einfachem Weg für Raspberry Pi OS (Desktop)
  ohne venv/pip (PyQt6/Pillow/numpy als Systempakete via `apt`), mit
  optionalem KI-Nachrüst-Schritt.
- `RECOMMENDATIONS.md` (+ i18n en/es/fr/uk/zh) um die Sektion „Runde 3"
  ergänzt: die bewertete Empfehlungsliste mit Status (erledigt #48/#52/
  #53/#51 bzw. offen), damit der Optimierungsstand dauerhaft im Repo
  nachvollziehbar ist.
- `RECOMMENDATIONS.md` (+ i18n en/es/fr/uk/zh) um „Runde 4 –
  Standortbestimmung & nächster Schritt" ergänzt: Code-Gesundheit
  (ruff/mypy sauber, 140 Tests grün) plus priorisierte Liste, was als
  Nächstes anzugehen ist. Empfohlener nächster Schritt: Release-Schnitt
  2.1.0 + git-Tag (kein git-Tag vorhanden trotz CHANGELOG-Behauptung;
  `[Unreleased]` seit 2.0.0 mit #48/#52/#53/#55 gefüllt).

## [2.0.0] – 2026-05-17

Erster dokumentierter 2.0.0-Release-Stand. Ein historischer
`v2.0.0`-Git-Tag existiert im Repo nicht.

### Funktionen

- KI-Hintergrundentfernung über `rembg` (optionales `ai`-Extra) inkl.
  Hintergrund-Warmup, damit der erste Klick nicht blockiert.
- Auswahlwerkzeuge: Zauberstab (vektorisierter Flood-Fill mit
  Toleranz-Slider), Pinsel, Radiergummi und Polygon-Lasso; Shift/Ctrl
  für additive bzw. subtraktive Auswahl.
- Hintergrund transparent setzen oder mit Farbe ersetzen.
- Transformationen: Drehen (90°-Schritte und freier Winkel), Spiegeln,
  Ecken abrunden, Zuschnitt in mehreren Formaten mit Rule-of-Thirds-Raster.
- Verlauf mit Undo/Redo (Toolbar-Buttons) und Sprung zu beliebigem
  früheren Schritt über ein schwebendes Historien-Popup.
- Drag & Drop sowie „Zuletzt geöffnet" (10 Einträge), beide über den
  asynchronen Lade-Worker – kein UI-Freeze.
- Speichern als PNG, JPEG, WebP oder TIFF.
- Persistente Einstellungen (Standard-Verzeichnisse, bevorzugtes
  Dateiformat) via `QSettings`.
- macOS-App-Bundle-Build (`create_BgRemover_app.sh`) inkl. isolierter
  venv, Apple-Silicon-Handling und Icon-Setzung; unterstützt Python
  3.10–3.15.

### Stabilität & Qualität

- Worker-Threads abgesichert (kein verfrühtes GC des Workers,
  sauberes Thread-Shutdown im `closeEvent`, KI-Race über monotonen
  Canvas-Versionszähler).
- Bildgrößen-Limit (40 MP) und Decompression-Bomb-Schutz beim Laden.
- Speicherbegrenzter Undo-Stack (256 MB) mit O(1)-Byte-Tracking.
- Plattformunabhängiger Log-Pfad (`bgremover.log` im App-Datenverzeichnis).
- 108 Tests; `ruff` und `mypy` als CI-Schritte; CI auf Ubuntu und macOS
  unter Python 3.10 und 3.12.
- `__version__` wird aus den Paket-Metadaten gelesen (Single Source);
  Version erscheint im Fenstertitel.

### Dokumentation & Lizenz

- Lizenz **GPL-3.0-or-later** (`LICENSE`); bedingt durch das
  GPL-lizenzierte PyQt6-Binding.
- `RESOURCES.md` (alle Bibliotheken/Werkzeuge/Assets samt Lizenzen),
  `LICENSES.md` und automatisierter Lizenz-/Compliance-Workflow.
- README mit Architektur, bekannten Einschränkungen und Installations-
  anleitung; ausführliche `INSTALL_MAC.md`.

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/v2.2.0...HEAD
[2.2.0]: https://github.com/NikolayDA/picture_helper/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/NikolayDA/picture_helper/compare/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1...v2.1.0
[2.0.0]: https://github.com/NikolayDA/picture_helper/tree/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1
