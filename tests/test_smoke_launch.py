"""Tests für den Headless-Smoke-Launcher mit Fork-Bomb-Wächter (#307).

Übt die drei Fehlersignale des Wächters mit echten Hilfsprozessen, ohne ein
echtes Bundle zu bauen: Start-Crash (Exit != 0), Fork-Bomb (Instanz-Explosion)
und Nicht-Terminieren (Timeout). Der gut sich verhaltende Fall liefert Exit 0.
"""
from __future__ import annotations

import importlib.util
import sys
import time
import uuid
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / "scripts" / "smoke_launch.py"

_spec = importlib.util.spec_from_file_location("smoke_launch", _SCRIPT)
assert _spec is not None and _spec.loader is not None
smoke_launch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(smoke_launch)


def test_script_exists_and_is_executable() -> None:
    assert _SCRIPT.is_file()
    # Wird im CI direkt als ``python3 scripts/smoke_launch.py`` aufgerufen.
    txt = _SCRIPT.read_text(encoding="utf-8")
    assert "BGREMOVER_SMOKE_TEST" in txt
    assert "offscreen" in txt


def test_clean_exit_passes() -> None:
    """Ein sauber mit 0 endender Prozess (keine Instanz-Explosion) → Exit 0."""
    rc = smoke_launch.run(
        [sys.executable, "-c", "print('hochgefahren')"],
        match_token="kein-treffer-token-xyz",
        timeout=30,
        max_instances=1,
        poll_interval=0.05,
    )
    assert rc == 0


def test_nonzero_exit_is_detected_as_start_crash() -> None:
    """Exit-Code != 0 (Start-Crash, #304) → Exit 1."""
    rc = smoke_launch.run(
        [sys.executable, "-c", "import sys; sys.exit(3)"],
        match_token="kein-treffer-token-xyz",
        timeout=30,
        max_instances=1,
        poll_interval=0.05,
    )
    assert rc == 1


def test_timeout_is_detected_and_process_is_killed() -> None:
    """Ein nicht terminierender Start (Hänger/Fork-Bomb-Symptom) → Exit 1."""
    start = time.monotonic()
    rc = smoke_launch.run(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        match_token="kein-treffer-token-xyz",
        timeout=1.0,
        max_instances=1,
        poll_interval=0.05,
    )
    elapsed = time.monotonic() - start
    assert rc == 1
    # Der Wächter wartet nicht die vollen 60s ab, sondern killt nach dem Timeout.
    assert elapsed < 20


def test_fork_bomb_is_detected_before_timeout(tmp_path: Path) -> None:
    """Eine Instanz-Explosion über ``--max-instances`` → sofort Exit 1.

    Die „Bombe" startet mehrere Kindprozesse, deren Kommandozeile denselben
    eindeutigen Token trägt; der Wächter zählt sie über ``ps`` und schlägt fehl,
    sobald mehr als erlaubt gleichzeitig laufen – lange vor dem Timeout.
    """
    token = f"forkbomb-{uuid.uuid4().hex}"
    bomb = tmp_path / "bomb.py"
    bomb.write_text(
        "import subprocess, sys, time\n"
        "token = sys.argv[1]\n"
        "for _ in range(6):\n"
        "    subprocess.Popen(\n"
        "        [sys.executable, '-c', 'import sys, time; time.sleep(60)', token]\n"
        "    )\n"
        "time.sleep(60)\n",
        encoding="utf-8",
    )

    start = time.monotonic()
    rc = smoke_launch.run(
        [sys.executable, str(bomb), token],
        match_token=token,
        timeout=30,
        max_instances=2,
        poll_interval=0.05,
    )
    elapsed = time.monotonic() - start
    assert rc == 1
    # Schlägt schnell fehl (Explosion erkannt), nicht erst am 30s-Timeout.
    assert elapsed < 20
    # Der gesamte Prozessbaum wurde per killpg beendet – keine zurückbleibenden
    # Instanzen mit dem Token.
    time.sleep(0.5)
    assert smoke_launch._count_instances(token, set()) == 0


def test_main_requires_target_command() -> None:
    """Ohne Zielkommando nach ``--`` bricht das CLI mit Fehler ab."""
    with pytest.raises(SystemExit) as excinfo:
        smoke_launch.main(["--match", "x"])
    assert excinfo.value.code != 0


def test_main_parses_and_runs_clean_command() -> None:
    """``main`` parst Optionen/``--``-Trennung und liefert den run()-Code."""
    rc = smoke_launch.main([
        "--match", "kein-treffer-token-xyz",
        "--timeout", "30",
        "--poll-interval", "0.05",
        "--",
        sys.executable, "-c", "print('ok')",
    ])
    assert rc == 0
