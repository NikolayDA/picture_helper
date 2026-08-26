"""Smoke-Tests für den App-Start und die macOS-Starter-Skripte.

Verteidigt die behobenen macOS-Start-Regressionen. Wichtig: Diese Tests
sind NICHT mit ``ui`` markiert, laufen also – anders als
``test_ui_interactions`` – auch in der CI (die UI-Tests sind dort über
``-m 'not ui'`` ausgeschlossen). Damit deckt die CI erstmals ab, dass
sich die Anwendung überhaupt vollständig starten lässt.

Abgedeckt:
- ``python -m bgremover`` und das Console-Script ``bgremover`` starten
  aus einem NEUTRALEN Arbeitsverzeichnis vollständig durch
  (``BGREMOVER_SMOKE_TEST`` beendet nach dem ersten Event-Loop-Tick).
- ``qt_plugins.ensure_qt_plugin_path()`` trägt einen gültigen Qt-Plugin-Pfad
  ein (Schutz gegen den ``cocoa``-Plugin-Fehler).
- Die Shell-Starter und der ins Bundle eingebackene Launcher sind
  syntaktisch valide.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────────────────────
# App-Start (headless, vollständiger Hochlauf)
# ─────────────────────────────────────────────────────────────

def _run_app_smoke(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Startet die App mit dem Selbsttest-Hook und gibt das Ergebnis zurück.

    ``BGREMOVER_SMOKE_TEST`` lässt ``main()`` nach dem ersten Event-Loop-
    Durchlauf ``app.quit()`` aufrufen – die App ist dann vollständig
    hochgefahren und beendet sich mit Exit-Code 0.
    """
    env = dict(os.environ,
               QT_QPA_PLATFORM="offscreen",
               BGREMOVER_SMOKE_TEST="1")
    return subprocess.run(cmd, cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=120)


def test_app_starts_via_python_m(tmp_path):
    """``python -m bgremover`` fährt aus einem fremden Verzeichnis durch.

    Neutrales ``cwd`` (``tmp_path``) ist Absicht: aus dem Repo-Root würde
    Pythons ``sys.path[0]=cwd``-Injektion das Quellpaket auch ohne echte
    Installation finden – genau die Falle, die den macOS-Bundle-Start
    brach.
    """
    r = _run_app_smoke([sys.executable, "-m", "bgremover"], tmp_path)
    assert r.returncode == 0, (
        f"python -m bgremover endete mit {r.returncode}\n"
        f"--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"
    )


def test_app_starts_via_console_script(tmp_path):
    """Das Console-Script ``bgremover`` fährt aus einem fremden Verzeichnis durch."""
    exe = shutil.which("bgremover")
    if exe is None:
        pytest.skip("Console-Script 'bgremover' nicht im PATH (Paket nicht installiert)")
    r = _run_app_smoke([exe], tmp_path)
    assert r.returncode == 0, (
        f"bgremover endete mit {r.returncode}\n"
        f"--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"
    )


def test_app_opens_startup_image_path(tmp_path):
    """Echter App-Start mit einem realen temporären Bildpfad öffnet das Bild (#249).

    Vollständiger Subprozess (eigene QApplication + MainWindow): öffnet den Pfad
    über die öffentliche Fassade ``open_paths`` (denselben validierten,
    asynchronen Ladepfad wie Datei-Dialog/Drag & Drop), wartet bis das Bild im
    Canvas liegt und schließt dann sauber. Verifiziert den Start-Open-Pfad
    end-to-end, ohne den Testprozess zu blockieren.
    """
    from PIL import Image

    img = tmp_path / "startup.png"
    Image.new("RGB", (8, 8), (10, 20, 30)).save(img)

    driver = (
        "import sys, time\n"
        "from PyQt6.QtWidgets import QApplication\n"
        "from bgremover.main_window import MainWindow\n"
        "app = QApplication(sys.argv)\n"
        "win = MainWindow(); win.show()\n"
        "win.open_paths([sys.argv[1]])\n"
        "deadline = time.monotonic() + 30\n"
        "while time.monotonic() < deadline and not win._canvas.has_image:\n"
        "    app.processEvents(); time.sleep(0.02)\n"
        "ok = win._canvas.has_image\n"
        "win.close()\n"
        "print('STARTUP_OPEN_OK' if ok else 'STARTUP_OPEN_FAIL')\n"
    )
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    r = subprocess.run(
        [sys.executable, "-c", driver, str(img)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120,
    )
    assert r.returncode == 0 and "STARTUP_OPEN_OK" in r.stdout, (
        f"Start-Open endete mit {r.returncode}\n"
        f"--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"
    )


def test_qt_plugin_path_configured():
    """``qt_plugins.ensure_qt_plugin_path()`` setzt einen existierenden Plugin-Pfad.

    In einem frischen Prozess (ohne vorab gesetzte ``QT_*``-Variablen),
    damit ``os.environ.setdefault`` im App-Code tatsächlich greift.
    """
    code = (
        "import os, pathlib; "
        "os.environ.pop('QT_QPA_PLATFORM_PLUGIN_PATH', None); "
        "os.environ.pop('QT_PLUGIN_PATH', None); "
        "import bgremover.app; "
        "p = os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH'); "
        "assert p, 'QT_QPA_PLATFORM_PLUGIN_PATH nicht gesetzt'; "
        "assert pathlib.Path(p).is_dir(), f'Plugin-Pfad fehlt: {p}'; "
        "print('ok')"
    )
    r = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and "ok" in r.stdout, (
        f"--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"
    )


# ─────────────────────────────────────────────────────────────
# Shell-Starter (Syntax)
# ─────────────────────────────────────────────────────────────

def _shell_for(path: Path) -> str:
    """Shell aus der Shebang-Zeile (zsh/bash)."""
    first = path.read_text(encoding="utf-8").splitlines()[0]
    return "zsh" if "zsh" in first else "bash"


@pytest.mark.parametrize("script", [
    "create_BgRemover_app.sh",
    "BgRemover.command",
    "diagnose_mac.sh",
])
def test_shell_starter_syntax(script):
    """Die macOS-Starter-Skripte sind syntaktisch valide (``<shell> -n``)."""
    path = ROOT / script
    assert path.is_file(), f"{script} fehlt im Repo-Wurzelverzeichnis"
    shell = _shell_for(path)
    if shutil.which(shell) is None:
        pytest.skip(f"{shell} nicht verfügbar (Syntax-Check läuft auf macOS-CI)")
    r = subprocess.run([shell, "-n", str(path)],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"{script}: Syntaxfehler\n{r.stderr}"


def test_bundled_launcher_syntax():
    """Der ins App-Bundle eingebackene Launcher (Heredoc in
    create_BgRemover_app.sh) ist syntaktisch valide.

    ``bash -n`` auf das Hauptskript prüft den Heredoc-Inhalt NICHT – der
    ist dort nur ein String. Hier wird der Launcher-Block extrahiert,
    die Heredoc-Escapes (``\\$``/``\\``` ``/``\\\\``) wie beim ``cat``
    aufgelöst und separat geprüft.
    """
    text = (ROOT / "create_BgRemover_app.sh").read_text(encoding="utf-8")
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines)
                 if ln.strip().endswith("<< LAUNCHER_EOF"))
    end = next(i for i, ln in enumerate(lines)
               if i > start and ln.strip() == "LAUNCHER_EOF")
    body = "\n".join(lines[start + 1:end]) + "\n"
    # Unquoted Heredoc: die Shell löst diese Escapes beim Schreiben auf.
    body = body.replace("\\$", "$").replace("\\`", "`").replace("\\\\", "\\")
    shell = "zsh" if body.splitlines()[0].strip().endswith("zsh") else "bash"
    if shutil.which(shell) is None:
        pytest.skip(f"{shell} nicht verfügbar (Syntax-Check läuft auf macOS-CI)")
    r = subprocess.run([shell, "-n", "/dev/stdin"], input=body,
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"Bundle-Launcher: Syntaxfehler\n{r.stderr}"


def test_mac_bundle_metadata_uses_package_version():
    """Info.plist übernimmt die installierte bgremover-Paketversion."""
    text = (ROOT / "create_BgRemover_app.sh").read_text(encoding="utf-8")

    assert "APP_VERSION=$(" in text
    assert "bgremover.__version__" in text
    assert "<key>CFBundleVersion</key>           <string>$APP_VERSION</string>" in text
    assert "<key>CFBundleShortVersionString</key><string>$APP_VERSION</string>" in text
    assert "<key>CFBundleVersion</key>           <string>3.0.0</string>" not in text
    assert "<key>CFBundleShortVersionString</key><string>3.0</string>" not in text


def test_bundled_launcher_uses_app_data_log_path():
    """Der Bundle-Launcher schreibt Startdiagnosen in den festen macOS-Logordner."""
    text = (ROOT / "create_BgRemover_app.sh").read_text(encoding="utf-8")

    assert 'LOG="\\$HOME/Library/Application Support/BgRemover/bgremover.log"' in text
    assert 'mkdir -p "\\$LOG_DIR"' in text
    assert 'LOG="\\$HOME/.bgremover.log"' not in text


def test_mac_bundle_refreshes_existing_app_venv_from_checkout():
    """Ein erneuter Build darf nicht still die alte Paketkopie weiterverwenden."""
    text = (ROOT / "create_BgRemover_app.sh").read_text(encoding="utf-8")
    branch_start = text.index('if [ -n "$APP_VENV_READY" ]')
    ready_branch = text[branch_start:text.index("\nelif ", branch_start)]

    assert 'Aktualisiere App-venv aus aktuellem Checkout' in ready_branch
    assert 'install_app_project "App-venv aktualisiert"' in ready_branch
    assert 'PYTHON_READY' not in text


def test_mac_bundle_cleans_build_artifacts_before_packaging():
    """Stale ``build/lib``-Paketdaten dürfen nicht in die App-venv zurückwandern."""
    text = (ROOT / "create_BgRemover_app.sh").read_text(encoding="utf-8")
    install_fn = text[text.index("install_app_project()"):text.index(
        "# Die venv liegt bewusst NICHT"
    )]

    assert 'rm -rf "$SCRIPT_DIR/build" "$SCRIPT_DIR/bgremover.egg-info"' in text
    assert 'sysconfig.get_paths()["purelib"]' in text
    assert 'rm -rf "$site_pkg/bgremover" "$site_pkg"/bgremover-*.dist-info' in text
    assert '"$VENV_DIR"/*/site-packages|"$VENV_DIR"/Lib/site-packages' in text
    assert install_fn.count("prepare_project_install") == 2
    assert install_fn.index("prepare_project_install") < install_fn.index(
        'pip_install_project "$VENV_PY" ".[ai]"'
    )
    assert install_fn.rindex("prepare_project_install") < install_fn.index(
        'pip_install_project "$VENV_PY" "."'
    )


def test_mac_bundle_embeds_interpreter_for_process_attribution():
    """macOS ordnet den GUI-Prozess über den Pfad seines Executables dem
    umgebenden Bundle zu (#864): der venv-Stub re-exec't auf Framework-Builds
    das echte Binary in ``Python.framework/…/Python.app`` – App-Umschalter und
    Stage-Manager-Seitenleiste zeigten deshalb dessen Raketen-Icon, egal was
    ``QApplication.setWindowIcon`` setzt. Das Setup bettet eine Kopie des
    echten Binaries ins Bundle ein und startet sie mit ``__PYVENV_LAUNCHER__``
    auf den venv-Stub; der Launcher fällt ohne funktionierenden eingebetteten
    Interpreter zur Laufzeit auf den venv-Start zurück."""
    text = (ROOT / "create_BgRemover_app.sh").read_text(encoding="utf-8")

    assert 'EMBEDDED_PY="$APP_PATH/Contents/MacOS/${APP_NAME}Python"' in text
    assert "Resources/Python.app/Contents/MacOS/Python" in text
    assert 'PYVENV_LAUNCHER_VALUE="$VENV_PY"' in text
    # Der Launcher startet den beim Bau verifizierten Interpreter …
    assert 'PYTHON="$LAUNCH_PY"' in text
    assert 'PYVENV_LAUNCHER="$PYVENV_LAUNCHER_VALUE"' in text
    # … und hat den Laufzeit-Fallback auf den venv-Stub (Heredoc-escaped).
    assert 'export __PYVENV_LAUNCHER__="\\$PYVENV_LAUNCHER"' in text
    assert 'PYTHON="\\$PYVENV_LAUNCHER"' in text
    # Der Selbsttest beim Bauen prüft den venv-Kontext optimierungsfest
    # (kein assert – das wäre unter PYTHONOPTIMIZE wegoptimiert) und räumt
    # ein durchgefallenes Binary wieder auf.
    assert "sys.exit(1) if sys.prefix == sys.base_prefix else None" in text
    assert 'rm -f "$EMBEDDED_PY"' in text
    # Greift der Laufzeit-Fallback, degradiert die App nicht still: die
    # Rückkehr des Python-Icons steht belegbar im Log.
    assert "Eingebetteter Interpreter nicht lauffaehig" in text


def test_mac_bundle_detects_and_repairs_rosetta_app_venv():
    """#866: Hardware-Architektur darf nicht aus einem Rosetta-``uname``
    abgeleitet werden. Eine x86_64-App-venv auf Apple Silicon wird klar
    benannt und nur nach Nutzerentscheidung nativ neu gebaut; der Launcher
    protokolliert anschließend Interpreter-Arch und Übersetzungsstatus."""
    text = (ROOT / "create_BgRemover_app.sh").read_text(encoding="utf-8")

    assert "/usr/sbin/sysctl -n hw.optional.arm64" in text
    assert "supports_native_arch" in text
    assert '[ -n "$NATIVE_ARCH" ] || return 0' in text
    assert "Architektur-Mismatch: Apple-Silicon-Hardware" in text
    assert "App-venv jetzt mit nativem arm64-Python neu bauen? [J/n]" in text
    assert 'FORCE_NATIVE_REBUILD=1' in text
    assert 'supports_native_arch "$FULL_PATH" || continue' in text
    assert "sysctl.proc_translated" in text
    assert "interpreter_arch=\\$PYTHON_ARCH" in text
    assert "proc_translated=\\$PYTHON_TRANSLATED" in text
    assert "hardware_arch=\\$NATIVE_ARCH" in text
    assert "BGREMOVER_RUNTIME|" in text
    assert "libc.sysctlbyname.argtypes" in text
    assert "kein zusätzlicher Python-Kaltstart" in text
    assert "WARNUNG: Python läuft als x86_64 unter Rosetta" in text


def test_mac_diagnostics_report_hardware_binary_and_runtime_architectures():
    """Die read-only Diagnose benennt den Mismatch und seine Abhilfe, statt
    ``uname -m`` irrtümlich als Hardware- oder Python-Arch auszugeben."""
    text = (ROOT / "diagnose_mac.sh").read_text(encoding="utf-8")

    for marker in (
        "/usr/sbin/sysctl -n hw.optional.arm64",
        "hardware_arch:",
        "diagnose_process_arch:",
        "proc_translated:",
        "sysctl -n sysctl.proc_translated",
        "BEFUND: ARCHITEKTUR-MISMATCH",
        "runtime_arch:",
        "/usr/bin/file -L",
        '/usr/bin/arch -"$HARDWARE_ARCH" "$APP_VENV"',
        "brew install python",
        'rm -rf "$HOME/Library/Application Support/BgRemover/venv"',
    ):
        assert marker in text


def test_mac_bundle_document_types_cover_supported_formats():
    """Die macOS-``CFBundleTypeExtensions`` entsprechen genau den tatsächlich
    unterstützten Formaten (Befund #249, AC #10) – die Finder-Dateizuordnung
    bleibt damit mit dem validierten Ladepfad konsistent.
    """
    import re

    from bgremover.constants import _ALLOWED_IMAGE_FORMATS

    text = (ROOT / "create_BgRemover_app.sh").read_text(encoding="utf-8")
    block = re.search(
        r"CFBundleTypeExtensions</key>\s*<array>(.*?)</array>", text, re.S)
    assert block, "CFBundleTypeExtensions-Block nicht gefunden"
    declared = set(re.findall(r"<string>([^<]+)</string>", block.group(1)))

    # Format → Dateiendung(en); deckt jeden Eintrag aus _ALLOWED_IMAGE_FORMATS ab.
    fmt_to_exts = {
        "PNG": {"png"}, "JPEG": {"jpg", "jpeg"}, "WEBP": {"webp"},
        "TIFF": {"tiff"}, "BMP": {"bmp"}, "GIF": {"gif"},
    }
    expected = set().union(*(fmt_to_exts[fmt] for fmt in _ALLOWED_IMAGE_FORMATS))
    assert declared == expected


def test_disabled_ai_tooltip_uses_existing_install_command():
    """Der deaktivierte KI-Button darf nicht auf ein nicht existentes Skript verweisen.

    Seit #458 lebt die KI-Aktion nicht mehr in der Rail; den Missing-Tooltip
    setzt das MainWindow am Inspector-Primärbutton (#437).
    """
    window_text = (ROOT / "bgremover" / "main_window.py").read_text(encoding="utf-8")
    i18n_text = (ROOT / "bgremover" / "i18n.py").read_text(encoding="utf-8")

    assert "setup_bgremover.sh" not in window_text + i18n_text
    assert "toolbar.ai.missing.tooltip" in window_text
    assert 'python3 -m pip install -e ".[ai]"' in i18n_text
