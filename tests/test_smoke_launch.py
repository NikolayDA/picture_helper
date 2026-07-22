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


def test_default_env_forces_offscreen_smoke_test() -> None:
    """Ohne ``env_overrides`` bleibt der bisherige Default aktiv (offscreen)."""
    rc = smoke_launch.run(
        [sys.executable, "-c",
         "import os, sys; sys.exit(0 if os.environ.get('BGREMOVER_SMOKE_TEST') == '1' "
         "and os.environ.get('QT_QPA_PLATFORM') == 'offscreen' else 4)"],
        match_token="kein-treffer-token-xyz", timeout=10, max_instances=1, poll_interval=0.05,
    )
    assert rc == 0


def test_env_overrides_replace_default_smoke_env() -> None:
    """Ein eigenes ``env_overrides``-Mapping ersetzt ``_SMOKE_ENV`` vollständig (#648)."""
    rc = smoke_launch.run(
        [sys.executable, "-c",
         "import os, sys; sys.exit(0 if os.environ.get('BGREMOVER_SMOKE_TEST') is None "
         "and os.environ.get('FOO') == 'bar' else 5)"],
        match_token="kein-treffer-token-xyz", timeout=10, max_instances=1, poll_interval=0.05,
        env_overrides={"FOO": "bar"},
    )
    assert rc == 0


def test_main_native_flag_skips_forced_offscreen_env() -> None:
    """``--native --env FOO=bar`` startet ohne erzwungenes ``BGREMOVER_SMOKE_TEST`` (#648)."""
    rc = smoke_launch.main([
        "--match", "kein-treffer-token-xyz", "--timeout", "10", "--poll-interval", "0.05",
        "--native", "--env", "FOO=bar",
        "--",
        sys.executable, "-c",
        "import os, sys; sys.exit(0 if os.environ.get('BGREMOVER_SMOKE_TEST') is None "
        "and os.environ.get('FOO') == 'bar' else 6)",
    ])
    assert rc == 0


def test_main_env_without_native_still_forces_offscreen() -> None:
    """``--env`` allein (ohne ``--native``) ergänzt nur, ersetzt den Default nicht."""
    rc = smoke_launch.main([
        "--match", "kein-treffer-token-xyz", "--timeout", "10", "--poll-interval", "0.05",
        "--env", "FOO=bar",
        "--",
        sys.executable, "-c",
        "import os, sys; sys.exit(0 if os.environ.get('BGREMOVER_SMOKE_TEST') == '1' "
        "and os.environ.get('FOO') == 'bar' else 7)",
    ])
    assert rc == 0


def test_main_env_requires_key_value() -> None:
    """Ein ``--env``-Eintrag ohne ``=`` bricht das CLI kontrolliert ab."""
    with pytest.raises(SystemExit) as excinfo:
        smoke_launch.main([
            "--match", "x", "--env", "NOVALUE", "--", sys.executable, "-c", "pass",
        ])
    assert excinfo.value.code != 0


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


# ── Maschinenlesbare Wächter-Ergebniszeile (#642-Nachtrag) ─────────────────


def test_parse_result_line_returns_none_without_marker() -> None:
    assert smoke_launch.parse_result_line("nur normaler Text\nkeine Ergebniszeile\n") is None


def test_parse_result_line_returns_none_on_malformed_json() -> None:
    broken = smoke_launch.RESULT_LINE_PREFIX + "{nicht valides json"
    assert smoke_launch.parse_result_line(broken) is None


def test_parse_result_line_extracts_payload_among_other_output() -> None:
    payload = smoke_launch.format_result_line(
        match_token="tok", timeout=30.0, max_instances=1, peak_instances=1,
        exit_code=0, status="ok", detail="sauber gestartet",
    )
    stdout = f"irgendeine andere Zeile\n{payload}\nnoch eine Zeile\n"
    parsed = smoke_launch.parse_result_line(stdout)
    assert parsed == {
        "match": "tok", "timeout_s": 30.0, "max_instances": 1, "peak_instances": 1,
        "exit_code": 0, "status": "ok", "detail": "sauber gestartet",
    }


def test_run_clean_exit_emits_ok_result_line(capsys) -> None:  # type: ignore[no-untyped-def]
    rc = smoke_launch.run(
        [sys.executable, "-c", "print('hochgefahren')"],
        match_token="kein-treffer-token-xyz", timeout=30, max_instances=1, poll_interval=0.05,
    )
    assert rc == 0
    parsed = smoke_launch.parse_result_line(capsys.readouterr().out)
    assert parsed is not None
    assert parsed["status"] == "ok"
    assert parsed["exit_code"] == 0
    assert parsed["peak_instances"] == 0
    assert parsed["max_instances"] == 1


def test_run_start_crash_emits_structured_exit_code(capsys) -> None:  # type: ignore[no-untyped-def]
    rc = smoke_launch.run(
        [sys.executable, "-c", "import sys; sys.exit(3)"],
        match_token="kein-treffer-token-xyz", timeout=30, max_instances=1, poll_interval=0.05,
    )
    assert rc == 1
    parsed = smoke_launch.parse_result_line(capsys.readouterr().out)
    assert parsed is not None
    assert parsed["status"] == "start_crash"
    assert parsed["exit_code"] == 3


def test_run_timeout_emits_structured_status(capsys) -> None:  # type: ignore[no-untyped-def]
    rc = smoke_launch.run(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        match_token="kein-treffer-token-xyz", timeout=1.0, max_instances=1, poll_interval=0.05,
    )
    assert rc == 1
    parsed = smoke_launch.parse_result_line(capsys.readouterr().out)
    assert parsed is not None
    assert parsed["status"] == "timeout"
    # Hart per SIGKILL beendet: negativer Exit-Code (Signalnummer), kein 0.
    assert parsed["exit_code"] != 0


def test_run_fork_bomb_emits_structured_peak_instances(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
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
    rc = smoke_launch.run(
        [sys.executable, str(bomb), token],
        match_token=token, timeout=30, max_instances=2, poll_interval=0.05,
    )
    assert rc == 1
    parsed = smoke_launch.parse_result_line(capsys.readouterr().out)
    assert parsed is not None
    assert parsed["status"] == "fork_bombe"
    assert parsed["peak_instances"] > 2
