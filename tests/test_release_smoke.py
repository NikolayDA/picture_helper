"""Governance für die Headless-Smoke-Launches im Release-Build (#307/#308).

Textbasiert (ohne PyYAML, analog zu ``tests/test_ci_qt_packages.py``): stellt
sicher, dass der ``build``-Job jedes frisch gebaute Artefakt headless startet,
den Fork-Bomb-Wächter nutzt, im ``--ai``-Build den KI-Selbsttest fährt und
``publish`` weiterhin per ``needs: build`` gegated bleibt.
"""
from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_RELEASE = _ROOT / ".github" / "workflows" / "release-linux.yml"
_LAUNCHER = _ROOT / "scripts" / "smoke_launch.py"


def _release_text() -> str:
    return _RELEASE.read_text(encoding="utf-8")


def test_smoke_launcher_script_exists_and_sets_headless_env() -> None:
    assert _LAUNCHER.is_file(), "scripts/smoke_launch.py fehlt"
    txt = _LAUNCHER.read_text(encoding="utf-8")
    # Setzt die headless-Smoke-Umgebung und implementiert den Instanz-Wächter.
    assert "BGREMOVER_SMOKE_TEST" in txt
    assert "offscreen" in txt
    assert "max-instances" in txt


def test_build_smoke_launches_both_artifacts_via_watchdog() -> None:
    text = _release_text()
    # Beide Legs starten das gebaute Artefakt über den Watchdog-Launcher …
    assert text.count("scripts/smoke_launch.py") >= 2, (
        "Linux- UND macOS-Leg müssen den Smoke-Launcher aufrufen."
    )
    # … das macOS-.app-Binary und das Linux-AppImage headless.
    assert "Contents/MacOS/BgRemover" in text
    assert "--appimage-extract-and-run" in text


def test_build_runs_ai_selfcheck_for_ai_builds() -> None:
    text = _release_text()
    # #308: der KI-Selbsttest-Hook wird im --ai-Build ausgeführt.
    assert "BGREMOVER_AI_SELFCHECK=1" in text
    # … abhängig davon, ob die Artefakte rembg bündeln.
    assert "WITH_AI" in text


def test_linux_smoke_installs_qt_runtime_libs() -> None:
    text = _release_text()
    # offscreen-Qt braucht System-libGL/-libEGL auf dem Runner, sonst scheitert
    # der AppImage-Start mit ``libGL.so.1: cannot open shared object file``.
    assert "libgl1" in text and "libegl1" in text


def test_publish_stays_gated_on_build() -> None:
    text = _release_text()
    # Ein durchgefallener Smoke-Launch fällt den build-Job; publish darf erst
    # nach einem erfolgreichen build laufen (AC #307: needs: build).
    assert re.search(r"(?m)^\s*needs:\s*build\b", text), (
        "publish muss per needs: build gegated bleiben."
    )
