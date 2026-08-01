"""Governance für die Headless-Smoke-Launches im Release-Build (#307/#308).

Textbasiert (ohne PyYAML, analog zu ``tests/test_ci_qt_packages.py``): stellt
sicher, dass der ``build``-Job jedes frisch gebaute Artefakt headless startet,
den Fork-Bomb-Wächter nutzt und im ``--ai``-Build den KI-Selbsttest fährt.
Das ``publish``-Gating (``needs: build``) wird bewusst nicht hier erneut
geprüft – die stärkere, geparste Prüfung dazu lebt in
``tests/test_release_gate.py::test_release_jobgraph_gates_publish_on_tests_and_tag``
(#659, konsolidiert aus einem vormals identischen Regex-Duplikat).
"""
from __future__ import annotations

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


def test_linux_smokes_start_artifacts_in_a_neutral_workdir() -> None:
    """Beide Linux-Smokes starten das Artefakt außerhalb des Checkouts (#740).

    Der AppRun-Entrypoint ruft ``python -m bgremover``; CPython stellt dabei
    das cwd an den Anfang von ``sys.path``. Ohne Wechsel gewinnt das
    ``bgremover/`` des Workspace-Checkouts gegen das gebündelte Paket, und der
    Smoke prüft nicht das Artefakt, sondern den Checkout.
    """
    text = _release_text()
    # Nur der Linux-Abschnitt: macOS ist durch das eingefrorene PyInstaller-
    # Bundle immun (sys.path[0] = base_library.zip, kein cwd-Eintrag).
    start = text.index("Smoke-launch built AppImage")
    linux = text[start:text.index("macOS: .app + .dmg", start)]
    aufrufe = linux.split("scripts/smoke_launch.py")[1:]
    assert len(aufrufe) == 3, (
        f"Erwartet: KI-Selbsttest, AppImage-Smoke, .deb-Smoke – gefunden: {len(aufrufe)}"
    )
    for i, aufruf in enumerate(aufrufe, 1):
        # Nur die Optionen bis zum ``--``-Trenner gehören zum Wächter selbst.
        optionen = aufruf.split(" -- ")[0]
        assert "--workdir" in optionen, (
            f"Linux-Smoke-Aufruf {i} startet ohne --workdir im Checkout (#740)."
        )
    assert 'neutral="$(mktemp -d)"' in linux


def test_linux_smoke_artifact_paths_are_absolute_when_workdir_is_set() -> None:
    """Mit ``--workdir`` müssen Artefaktpfade absolut sein (#740, Codex-P1).

    ``subprocess.Popen`` löst das Zielkommando gegen ``cwd`` auf. Ein
    relativer ``dist/...``-Pfad zeigt dann ins leere Wächter-Verzeichnis und
    der Start bricht mit ``FileNotFoundError`` ab, bevor das Artefakt läuft –
    im KI-Selbsttest ebenso, weil ``env`` das Artefakt seinerseits relativ zu
    seinem cwd exect. Der reine Vorhandenseins-Test auf ``--workdir`` hat
    diesen Fehler nicht gefunden; deshalb prüft dieser Test die Auflösung.
    """
    text = _release_text()
    start = text.index("Smoke-launch built AppImage")
    linux = text[start:text.index("macOS: .app + .dmg", start)]

    # Die Variable, die an den Wächter geht, wird absolut abgeleitet …
    assert 'appimage="$(ls -1 "$PWD"/dist/*.AppImage | head -1)"' in linux, (
        "AppImage-Pfad muss absolut sein, sonst scheitert der Start unter --workdir."
    )

    # … und kein Wächter-Aufruf übergibt einen relativen dist/-Pfad. Dafür
    # Zeilenfortsetzungen zu logischen Kommandozeilen zusammenfassen.
    flach = linux.replace("\\\n", " ")
    aufrufe = [z for z in flach.splitlines() if "scripts/smoke_launch.py" in z]
    assert len(aufrufe) == 3, f"drei Linux-Wächter-Aufrufe erwartet, gefunden: {len(aufrufe)}"
    for aufruf in aufrufe:
        assert " -- " in aufruf, f"kein Zielkommando im Aufruf: {aufruf.strip()[:80]}"
        ziel = aufruf.split(" -- ", 1)[1]
        assert "dist/" not in ziel, (
            f"Relativer dist/-Pfad im Wächter-Aufruf trotz --workdir: {ziel.strip()[:80]}"
        )
