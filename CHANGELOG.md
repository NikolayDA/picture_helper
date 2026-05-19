**Deutsch** · [English](docs/i18n/en/CHANGELOG.md) · [Español](docs/i18n/es/CHANGELOG.md) · [Français](docs/i18n/fr/CHANGELOG.md) · [Українська](docs/i18n/uk/CHANGELOG.md) · [简体中文](docs/i18n/zh/CHANGELOG.md)

# Changelog

Alle nennenswerten Änderungen an BgRemover werden in dieser Datei
dokumentiert. Das Format orientiert sich an
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/); das Projekt
folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Geändert

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

Erste öffentlich getaggte Veröffentlichung.

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

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/NikolayDA/picture_helper/releases/tag/v2.0.0
