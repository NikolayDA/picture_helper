# CLAUDE.md

Kurzanleitung für Claude Code in diesem Repository. **BgRemover** ist ein
Desktop-Tool zum Entfernen von Bildhintergründen und für einfache
Bildbearbeitung (PyQt6, macOS + Linux, Python ≥ 3.10).

## Standard-Gate (vor jedem PR)

Alles läuft über den Makefile-Wrapper. Er nutzt `python -m <tool>` (robust
gegen PATH-/venv-Eigenheiten) und setzt `QT_QPA_PLATFORM=offscreen` für den
headless-Qt-Betrieb:

- `make check` — Lint + Typecheck + Tests. **Die maßgebliche Baseline.**
- `make lint` — `ruff check bgremover scripts tests` (+ shellcheck, falls installiert)
- `make type` — `mypy`
- `make test` — `pytest` (ohne volle UI-Suite, das `ui_smoke`-Subset läuft mit)
- `make coverage` — Coverage-Report (`fail_under = 86`)
- `make ui` — volle qtbot-UI-Suite (sonst nur nightly)
- `make pr-check` — wie die PR-CI: nicht-editable Install + `doctor` + `check`
- `make doctor` — prüft die Test-Umgebung (`scripts/check_test_env.py`)

Bei direkten `pytest`-Aufrufen `QT_QPA_PLATFORM=offscreen` setzen; `make` und
`tests/conftest.py` (per `setdefault`) erledigen das selbst.

## Architektur

Ein Paket, `bgremover/`:

- **Einstieg:** `app.py` (`main()`), `__main__.py` → `python -m bgremover`;
  `main_window.py` verdrahtet die UI.
- **Canvas/Bearbeitung:** `canvas.py` + `canvas_*.py` (History, Selection, Lasso,
  Transform, Viewport, Crop), `crop.py`, `image_ops.py`, `image_utils.py`;
  `image_loading.py` ist der gemeinsame Lade-Helfer für Canvas und Worker.
- **Hintergrund-Entfernung:** `workers.py` / `worker_controller.py`; die nicht
  unterbrechbare rembg/ONNX-Inferenz läuft in einem eigenen, per `spawn`
  gestarteten Prozess (`ai_process.py`), den der KI-Worker nur pollt – Abbruch
  und Schließen beenden ihn hart, ohne `QThread.terminate()` (#270). `rembg` ist
  optionales `ai`-Extra und wird erst im Kindprozess lazy importiert.
- **UI-Bausteine:** `main_toolbar.py`, `right_panel*.py`, `settings_dialog.py`,
  `menu_actions.py`, `crop_bar.py`, `history_popup.py`, `widgets.py`, `theme.py`,
  `icons*.py`.
- **Infrastruktur:** `constants.py` + `logging_config.py` (Logger/Log-Pfad),
  `qt_plugins.py` (Qt-Pluginpfade), `settings_schema.py` (QSettings-Versionierung),
  `status_messages.py` (zentrale Meldungsstrings), `recent_files.py`
  („Zuletzt geöffnet"-Persistenz).
- **i18n:** `i18n.py` — Runtime-Sprachen **de/en** umschaltbar; Doku-Übersetzungen
  unter `docs/i18n/`.

## Konventionen

- **Kommentare & Docstrings auf Deutsch** (Code-Identifier englisch). Den
  bestehenden, bewusst kompakten Stil treffen.
- **ruff:** line-length 100, Regeln `E,F,W,I,B,UP,SIM`, `E501` ignoriert, Ziel
  py310. In `bgremover/*` ist `E702` erlaubt (kompakter Stil), in
  `tests/conftest.py` `E402`.
- **mypy:** Qt-arme Logikmodule (`ai_process`, `image_ops`, `image_utils`,
  `crop`, `recent_files`, `canvas_history/_selection/_lasso/_transform/_viewport`)
  sind streng getypt (`disallow_untyped_defs`); Qt-lastige Module bewusst laxer.
- **Tests:** Marker `ui` (nightly, voll) vs. `ui_smoke` (läuft in CI mit).
  Default-`addopts`: `-m 'not ui or ui_smoke'`. Viele Doku-Governance-Tests
  (Markdown-Links, i18n-Parität, CHANGELOG, Lizenzen) — Docs als Code behandeln.
- **Befunde** werden in `RECOMMENDATIONS.md` mit IDs geführt (`N#`/`O#`);
  Historie unter `docs/history/`.

## Wichtig: Drift-Disziplin (Befund N6)

Die Qt-apt-Paketliste muss in **sechs** Dateien identisch bleiben:
`.github/workflows/ci.yml`, `pr-ci.yml`, `ui-nightly.yml`, `benchmark.yml`,
`coverage.yml` und `.claude/hooks/session-start.sh`.
`tests/test_ci_qt_packages.py` erzwingt das — beim Ändern einer Liste alle sechs
anpassen, sonst schlägt der Test fehl (und `import PyQt6` bricht andernorts mit
`libGL.so.1: cannot open shared object file`).

## Web-/Remote-Umgebung

Der `SessionStart`-Hook (`.claude/hooks/session-start.sh`) installiert in
Web-Sessions die Qt-Systembibliotheken + `.[test]` und setzt
`QT_QPA_PLATFORM=offscreen`. Er läuft nur, wenn `CLAUDE_CODE_REMOTE=true`; lokal
richtest du deine venv selbst ein (siehe `INSTALL_MAC.md` / `INSTALL_LINUX.md`).
