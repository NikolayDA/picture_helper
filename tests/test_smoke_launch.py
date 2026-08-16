"""Tests für den Headless-Smoke-Launcher mit Fork-Bomb-Wächter (#307).

Übt die drei Fehlersignale des Wächters mit echten Hilfsprozessen, ohne ein
echtes Bundle zu bauen: Start-Crash (Exit != 0), Fork-Bomb (Instanz-Explosion)
und Nicht-Terminieren (Timeout). Der gut sich verhaltende Fall liefert Exit 0.
"""
from __future__ import annotations

import importlib.util
import subprocess
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
    # Instanzen mit dem Token. ``run`` drained bereits intern (#642-Nachtrag),
    # kein zusätzlicher Sleep nötig.
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


# ── Nachlauf-Wartezeit auf reparentete Enkelprozesse (#642-Nachtrag) ───────


def test_drain_instances_waits_for_process_to_disappear() -> None:
    """Wartet, bis eine noch laufende Instanz mit dem Token verschwunden ist."""
    token = f"drain-{uuid.uuid4().hex}"
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(0.3)", token])
    try:
        assert smoke_launch._count_instances(token, set()) >= 1
        smoke_launch._drain_instances(token, set(), timeout=3.0, poll_interval=0.02)
        assert smoke_launch._count_instances(token, set()) == 0
    finally:
        proc.wait(timeout=5)


def test_drain_instances_gives_up_after_timeout() -> None:
    """Bleibt eine Instanz am Leben, kehrt der Nachlauf trotzdem zurück (kein Hang)."""
    token = f"drain-stuck-{uuid.uuid4().hex}"
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)", token])
    try:
        start = time.monotonic()
        smoke_launch._drain_instances(token, set(), timeout=0.3, poll_interval=0.05)
        elapsed = time.monotonic() - start
        assert elapsed < 2.0
    finally:
        proc.kill()
        proc.wait(timeout=5)


def test_workdir_sets_child_working_directory(tmp_path: Path) -> None:
    """``--workdir``/``workdir=`` bestimmt das cwd des Zielkommandos (#740)."""
    ziel = tmp_path / "neutral"
    ziel.mkdir()
    ausgabe = tmp_path / "cwd.txt"
    rc = smoke_launch.run(
        [
            sys.executable, "-c",
            f"import os, pathlib; pathlib.Path(r'{ausgabe}').write_text(os.getcwd())",
        ],
        match_token="kein-treffer-token-" + uuid.uuid4().hex,
        timeout=30,
        max_instances=1,
        workdir=str(ziel),
    )
    assert rc == 0
    assert Path(ausgabe.read_text()).resolve() == ziel.resolve()


def test_without_workdir_the_parent_cwd_is_inherited(tmp_path: Path) -> None:
    """Ohne ``workdir`` bleibt das bisherige Verhalten unverändert (#740)."""
    ausgabe = tmp_path / "cwd.txt"
    rc = smoke_launch.run(
        [
            sys.executable, "-c",
            f"import os, pathlib; pathlib.Path(r'{ausgabe}').write_text(os.getcwd())",
        ],
        match_token="kein-treffer-token-" + uuid.uuid4().hex,
        timeout=30,
        max_instances=1,
    )
    assert rc == 0
    assert Path(ausgabe.read_text()).resolve() == Path.cwd().resolve()


def test_neutral_workdir_prevents_checkout_from_shadowing_the_bundle(tmp_path: Path) -> None:
    """Der eigentliche Regressionsfall aus #740.

    Ein Start über ``python -m paket`` stellt das cwd an den Anfang von
    ``sys.path``. Liegt dort ein gleichnamiges Paket (im echten Fall der
    Checkout mit ``bgremover/``), gewinnt es gegen das gebündelte – der Smoke
    prüft dann den falschen Code. Ein neutrales cwd verhindert genau das.
    """
    schatten = tmp_path / "checkout"
    (schatten / "paket").mkdir(parents=True)
    (schatten / "paket" / "__init__.py").write_text("HERKUNFT = 'checkout'\n")
    (schatten / "paket" / "__main__.py").write_text(
        "import paket, pathlib, os, sys\n"
        "pathlib.Path(os.environ['ZIEL']).write_text(paket.HERKUNFT)\n"
    )
    ausgabe = tmp_path / "herkunft.txt"
    neutral = tmp_path / "neutral"
    neutral.mkdir()
    argv = [sys.executable, "-m", "paket"]
    token = "kein-treffer-token-" + uuid.uuid4().hex

    # Ohne neutrales cwd gewinnt der Schatten – das ist der Fehlerzustand.
    rc = smoke_launch.run(
        argv, match_token=token, timeout=30, max_instances=1,
        env_overrides={"ZIEL": str(ausgabe)}, workdir=str(schatten),
    )
    assert rc == 0
    assert ausgabe.read_text() == "checkout"

    # Mit neutralem cwd ist das Paket schlicht nicht auffindbar: der Start
    # scheitert sichtbar, statt still den falschen Code zu prüfen.
    ausgabe.unlink()
    rc = smoke_launch.run(
        argv, match_token=token, timeout=30, max_instances=1,
        env_overrides={"ZIEL": str(ausgabe)}, workdir=str(neutral),
    )
    assert rc != 0
    assert not ausgabe.exists()


def test_relative_command_with_workdir_fails_loudly(tmp_path: Path) -> None:
    """Relativer Programmpfad + ``workdir`` bricht sichtbar ab (#740, Codex-P1).

    Hält die Falle fest, die im Release-Workflow zuerst übersehen wurde:
    ``Popen`` löst das Kommando gegen ``cwd`` auf, ein relativer Pfad zeigt
    also ins neutrale Verzeichnis. Wichtig ist, dass das *laut* scheitert und
    nicht etwa still ein anderes Programm startet.
    """
    (tmp_path / "bin").mkdir()
    skript = tmp_path / "bin" / "artefakt.sh"
    skript.write_text("#!/bin/sh\nexit 0\n")
    skript.chmod(0o755)
    neutral = tmp_path / "neutral"
    neutral.mkdir()
    token = "kein-treffer-token-" + uuid.uuid4().hex

    with pytest.raises(FileNotFoundError):
        smoke_launch.run(
            ["bin/artefakt.sh"], match_token=token, timeout=30,
            max_instances=1, env_overrides={}, workdir=str(neutral),
        )

    # Absolut aufgelöst läuft derselbe Start sauber durch.
    rc = smoke_launch.run(
        [str(skript)], match_token=token, timeout=30,
        max_instances=1, env_overrides={}, workdir=str(neutral),
    )
    assert rc == 0
