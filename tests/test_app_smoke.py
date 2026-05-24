"""Smoke-Tests für den App-Start und die macOS-Starter-Skripte.

Verteidigt die Mac-Start-Regressionen aus Runde 5 / Phase B. Wichtig:
diese Tests sind NICHT mit ``ui`` markiert, laufen also – anders als
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
    """Der Bundle-Launcher schreibt in denselben macOS-Logordner wie die App."""
    text = (ROOT / "create_BgRemover_app.sh").read_text(encoding="utf-8")

    assert 'LOG="\\$HOME/Library/Application Support/BgRemover/bgremover.log"' in text
    assert 'mkdir -p "\\$LOG_DIR"' in text
    assert 'LOG="\\$HOME/.bgremover.log"' not in text
