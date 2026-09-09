"""Wächter der Qt-System-Paketliste (#1036, löst Befund N6 ab).

Bis #1036 stand dieselbe apt-Liste in fünf Workflows und im SessionStart-Hook,
und dieser Test hielt die sechs Kopien gegeneinander. Seither gibt es genau
**eine** Quelle, ``scripts/install_qt_apt.sh``; der Test prüft

* dass die Liste dort vollständig ist (über ``--print-packages``, also die
  Sicht des Skripts selbst, nicht einen Textscan),
* dass alle sechs Aufrufer das Skript benutzen und nur der Hook den
  Best-effort-Update-Modus setzt,
* als **Negativkontrolle**, dass keiner der sechs Aufrufer die Liste wieder
  inline führt (Stellvertreter: ``libxcb-xinerama0``),
* und den Update-Modus des Skripts über simulierte ``apt-get``-/``sudo``-
  Kommandos auf dem ``PATH`` – ohne Root und ohne echtes apt.

Textbasiert (parserunabhängig) wie zuvor: greift auch, wenn PyYAML fehlt.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = Path("scripts/install_qt_apt.sh")
_INLINE_SENTINEL = "libxcb-xinerama0"

# Alle Stellen, die Qt-Systempakete installieren. Wer einen Aufrufer hinzufügt,
# trägt ihn hier ein; sonst greift die Negativkontrolle dort nicht.
_WORKFLOW_CALLERS = (
    ".github/workflows/ci.yml",
    ".github/workflows/pr-ci.yml",
    ".github/workflows/ui-nightly.yml",
    ".github/workflows/benchmark.yml",
    ".github/workflows/coverage.yml",
)
_HOOK = ".claude/hooks/session-start.sh"
_CALLERS = (*_WORKFLOW_CALLERS, _HOOK)

# Workflows, deren Jobs `make lint` ausführen und dafür zsh + shellcheck brauchen.
_LINT_WORKFLOWS = (
    ".github/workflows/ci.yml",
    ".github/workflows/pr-ci.yml",
    ".github/workflows/coverage.yml",
)

_REQUIRED_QT_PACKAGES = frozenset(
    {
        "libegl1",
        "libgl1",
        "libfontconfig1",
        "libxkbcommon0",
        "libdbus-1-3",
        "libxcb-icccm4",
        "libxcb-image0",
        "libxcb-keysyms1",
        "libxcb-randr0",
        "libxcb-render-util0",
        "libxcb-shape0",
        "libxcb-xinerama0",
        "libxcb-xkb1",
    }
)

_BASH = shutil.which("bash")
_needs_bash = pytest.mark.skipif(_BASH is None, reason="bash nicht verfügbar")


def _run_script(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    assert _BASH is not None
    return subprocess.run(
        [_BASH, str(_SCRIPT), *args],
        cwd=_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@_needs_bash
def test_script_lists_all_required_qt_packages() -> None:
    result = _run_script("--print-packages")
    assert result.returncode == 0, result.stderr
    listed = set(result.stdout.split())
    missing = _REQUIRED_QT_PACKAGES - listed
    assert not missing, f"{_SCRIPT}: fehlende Qt-Pakete: {sorted(missing)}"


def test_script_is_executable_bash_with_strict_mode() -> None:
    path = _ROOT / _SCRIPT
    text = path.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash\n")
    assert "set -euo pipefail" in text
    assert path.stat().st_mode & stat.S_IXUSR


@pytest.mark.parametrize("rel_path", _CALLERS)
def test_caller_uses_the_shared_script(rel_path: str) -> None:
    text = (_ROOT / rel_path).read_text(encoding="utf-8")
    assert f"bash {_SCRIPT.as_posix()}" in text, f"{rel_path}: ruft {_SCRIPT} nicht auf"


@pytest.mark.parametrize("rel_path", _CALLERS)
def test_caller_has_no_inline_qt_package_list(rel_path: str) -> None:
    """Negativkontrolle: Ein Paketname im Aufrufer heißt, die Liste ist zurück."""
    text = (_ROOT / rel_path).read_text(encoding="utf-8")
    assert _INLINE_SENTINEL not in text, (
        f"{rel_path}: führt die Qt-Paketliste wieder inline – Quelle ist allein {_SCRIPT}"
    )


@pytest.mark.parametrize("rel_path", _CALLERS)
def test_best_effort_update_is_reserved_for_the_hook(rel_path: str) -> None:
    text = (_ROOT / rel_path).read_text(encoding="utf-8")
    call_lines = [line for line in text.splitlines() if f"bash {_SCRIPT.as_posix()}" in line]
    assert call_lines, rel_path
    best_effort = any("--best-effort-update" in line for line in call_lines)
    assert best_effort == (rel_path == _HOOK), (
        f"{rel_path}: --best-effort-update darf nur der SessionStart-Hook setzen"
    )


@pytest.mark.parametrize("rel_path", _LINT_WORKFLOWS)
def test_lint_workflows_request_zsh_and_shellcheck(rel_path: str) -> None:
    text = (_ROOT / rel_path).read_text(encoding="utf-8")
    assert f"bash {_SCRIPT.as_posix()} zsh shellcheck" in text, (
        f"{rel_path}: make lint braucht zsh und shellcheck als Zusatzpakete"
    )


def test_makefile_lints_the_script() -> None:
    makefile = (_ROOT / "Makefile").read_text(encoding="utf-8")
    assert _SCRIPT.as_posix() in makefile, "lint-shell muss scripts/install_qt_apt.sh prüfen"


# --- Update-Modus über simulierte Kommandos ---------------------------------


def _install_fakes(bin_dir: Path, log: Path, update_exit: int, install_exit: int) -> None:
    """Legt `apt-get` und `sudo` als Attrappen ab; jeder Aufruf landet im Log."""
    apt = bin_dir / "apt-get"
    apt.write_text(
        "#!/usr/bin/env bash\n"
        f'printf \'apt-get %s | DEBIAN_FRONTEND=%s\\n\' "$*" "${{DEBIAN_FRONTEND-}}" >> "{log}"\n'
        f'case "$1" in update) exit {update_exit} ;; install) exit {install_exit} ;; esac\n'
        "exit 99\n",
        encoding="utf-8",
    )
    sudo = bin_dir / "sudo"
    sudo.write_text(
        "#!/usr/bin/env bash\n"
        f'printf \'sudo %s\\n\' "$*" >> "{log}"\n'
        'exec env "$@"\n',
        encoding="utf-8",
    )
    for fake in (apt, sudo):
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)


def _run_with_fakes(
    tmp_path: Path, *args: str, update_exit: int = 0, install_exit: int = 0
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    log = tmp_path / "calls.log"
    _install_fakes(bin_dir, log, update_exit, install_exit)
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
    env.pop("DEBIAN_FRONTEND", None)
    result = _run_script(*args, env=env)
    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    return result, calls


def _install_calls(calls: list[str]) -> list[str]:
    return [line for line in calls if line.startswith("apt-get install")]


@_needs_bash
def test_default_mode_fails_closed_when_apt_update_fails(tmp_path: Path) -> None:
    result, calls = _run_with_fakes(tmp_path, update_exit=1)
    assert result.returncode != 0
    assert not _install_calls(calls), "nach gescheitertem apt-get update darf nichts installiert werden"


@_needs_bash
def test_best_effort_mode_continues_when_apt_update_fails(tmp_path: Path) -> None:
    result, calls = _run_with_fakes(tmp_path, "--best-effort-update", update_exit=1)
    assert result.returncode == 0, result.stderr
    assert "fahre fort" in result.stdout
    installs = _install_calls(calls)
    assert len(installs) == 1
    assert set(installs[0].split()) >= _REQUIRED_QT_PACKAGES


@_needs_bash
def test_install_failure_is_always_hard(tmp_path: Path) -> None:
    for args in ((), ("--best-effort-update",)):
        result, calls = _run_with_fakes(tmp_path / f"case{len(args)}", *args, install_exit=100)
        assert result.returncode != 0, args
        assert _install_calls(calls), args


@_needs_bash
def test_install_is_noninteractive_and_appends_extras(tmp_path: Path) -> None:
    result, calls = _run_with_fakes(tmp_path, "zsh", "shellcheck")
    assert result.returncode == 0, result.stderr
    # Reihenfolge der echten apt-Aufrufe – als Nicht-root steht davor je eine sudo-Zeile.
    apt_calls = [line for line in calls if line.startswith("apt-get ")]
    assert apt_calls[0].startswith("apt-get update")
    installs = _install_calls(calls)
    assert len(installs) == 1
    command, _, frontend = installs[0].partition(" | DEBIAN_FRONTEND=")
    assert frontend == "noninteractive"
    tokens = command.split()
    assert tokens[:3] == ["apt-get", "install", "-y"]
    assert tokens[-2:] == ["zsh", "shellcheck"]
    assert set(tokens) >= _REQUIRED_QT_PACKAGES


@_needs_bash
def test_sudo_only_when_not_root(tmp_path: Path) -> None:
    result, calls = _run_with_fakes(tmp_path)
    assert result.returncode == 0, result.stderr
    sudo_calls = [line for line in calls if line.startswith("sudo ")]
    if os.geteuid() == 0:
        assert not sudo_calls, "als root darf das Skript kein sudo voranstellen"
    else:
        assert len(sudo_calls) == 2, sudo_calls


@_needs_bash
def test_help_prints_the_header_without_touching_apt(tmp_path: Path) -> None:
    result, calls = _run_with_fakes(tmp_path, "--help")
    assert result.returncode == 0, result.stderr
    assert "--best-effort-update" in result.stdout
    assert "ZUSATZPAKET" in result.stdout
    # Nur der Kommentarkopf – keine Codezeile, kein apt-Aufruf.
    assert "set -euo pipefail" not in result.stdout
    assert "QT_PACKAGES" not in result.stdout
    assert not calls


@_needs_bash
def test_unknown_option_is_rejected_before_touching_apt(tmp_path: Path) -> None:
    result, calls = _run_with_fakes(tmp_path, "--no-such-option")
    assert result.returncode == 2
    assert "unbekannte Option" in result.stderr
    assert not calls
