# Changelog

Alle nennenswerten Änderungen an BgRemover werden in dieser Datei
dokumentiert. Das Format orientiert sich an
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/); das Projekt
folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Dokumentation

- Installationsanleitung für Linux (`INSTALL_LINUX.md`) ergänzt:
  Systempakete je Distribution (apt/dnf/pacman), venv-Setup,
  Starter-Skript bzw. `.desktop`-Eintrag und Troubleshooting; im README
  verlinkt. Inkl. besonders einfachem Weg für Raspberry Pi OS (Desktop)
  ohne venv/pip (PyQt6/Pillow/numpy als Systempakete via `apt`), mit
  optionalem KI-Nachrüst-Schritt.

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
