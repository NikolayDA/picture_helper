"""Drift-Schutz für die Qt-System-Paketlisten (Befund N6).

PyQt6 braucht zur Laufzeit einige Qt-Systembibliotheken – allen voran
``libGL.so.1`` (Paket ``libgl1``) und ``libEGL.so.1`` (``libegl1``). Diese
werden an mehreren Stellen installiert: in den GitHub-Workflows und im
SessionStart-Hook für Claude Code on the web. Fehlt eine Bibliothek in einer
der Listen, scheitert dort bereits ``import PyQt6`` mit
``libGL.so.1: cannot open shared object file`` – und zwar erst spät, weil die
Vollmatrix nur bei Tags/Releases läuft. Dieser Test hält die Listen
konsistent, statt sich auf zufällig vorinstallierte Runner-Bibliotheken zu
verlassen.
"""
from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent

# Dateien, die Qt-Systembibliotheken per apt installieren. ``license-check.yml``
# fehlt bewusst – es baut nur Python-Tooling und braucht kein Qt. ``benchmark.yml``
# importiert ueber bgremover.image_ops transitiv PyQt6 und braucht die Libs daher.
# ``coverage.yml`` (#293) fuehrt ``make coverage`` (= die Test-Suite) aus und
# braucht die Libs ebenfalls.
_PACKAGE_SOURCES = (
    ".github/workflows/ci.yml",
    ".github/workflows/pr-ci.yml",
    ".github/workflows/ui-nightly.yml",
    ".github/workflows/benchmark.yml",
    ".github/workflows/coverage.yml",
    ".claude/hooks/session-start.sh",
)

# Qt-Laufzeitbibliotheken, die in JEDER Liste stehen müssen. ``libegl1`` und
# ``libgl1`` sind die beiden, deren Fehlen den PyQt6-Import direkt killt; die
# xcb-Familie deckt die Plattform-Plugins ab. ``zsh``/``shellcheck`` sind
# bewusst NICHT enthalten – die installiert nur ein Teil der Workflows extra.
_REQUIRED_QT_PACKAGES = (
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
)


@pytest.mark.parametrize("rel_path", _PACKAGE_SOURCES)
def test_qt_package_list_is_complete(rel_path: str) -> None:
    """Jede Qt-Paketquelle installiert die vollständige Qt-Lib-Liste.

    Token-Vergleich (whitespace-getrennt) statt Substring, damit z. B.
    ``libgl1`` nicht versehentlich in ``libegl1`` „gefunden" wird.
    """
    path = _ROOT / rel_path
    tokens = set(path.read_text(encoding="utf-8").split())
    missing = [pkg for pkg in _REQUIRED_QT_PACKAGES if pkg not in tokens]
    assert not missing, (
        f"{rel_path} installiert nicht alle Qt-Systembibliotheken – fehlend: "
        f"{missing}. Ohne libgl1/libegl1 scheitert dort der PyQt6-Import "
        f"(libGL.so.1: cannot open shared object file). Listen konsistent "
        f"halten (siehe Befund N6)."
    )
