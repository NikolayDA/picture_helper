"""Static checks that keep the resource inventory aligned with the repo."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESOURCE_DOCS = [
    ROOT / "RESOURCES.md",
    ROOT / "docs/i18n/en/RESOURCES.md",
    ROOT / "docs/i18n/es/RESOURCES.md",
    ROOT / "docs/i18n/fr/RESOURCES.md",
    ROOT / "docs/i18n/uk/RESOURCES.md",
    ROOT / "docs/i18n/zh/RESOURCES.md",
]


#: Die Workflows, die RESOURCES.md als Test-/Qualitaets-CI fuehrt. Welche der
#: 17 Workflows das Dokument aufnimmt, ist eine redaktionelle Entscheidung und
#: bleibt deshalb literal; die Action-Pins darunter werden daraus abgeleitet.
CI_WORKFLOWS = (
    ".github/workflows/pr-ci.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/ui-nightly.yml",
    ".github/workflows/license-check.yml",
)

# ``uses:`` steht mal als eigener Schluessel, mal als erster Schluessel
# eines Listeneintrags (``- uses: ...``). Ohne den optionalen Strich
# faehrt die Suche an ``checkout`` und ``setup-python`` vorbei.
_USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)
_ACTION_RE = re.compile(r"^(?P<name>[^@]+)@v(?P<major>\d+)$")
_PYTHON_MATRIX_RE = re.compile(r"python-version:\s*\[([^\]]+)\]")


def _used_actions() -> dict[str, int]:
    """Action-Name -> hoechste in den CI-Workflows verwendete Hauptversion."""
    used: dict[str, int] = {}
    for relative in CI_WORKFLOWS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for reference in _USES_RE.findall(text):
            match = _ACTION_RE.match(reference)
            if match is None:
                continue  # lokaler oder wiederverwendbarer Workflow, kein Pin
            name, major = match["name"], int(match["major"])
            used[name] = max(used.get(name, 0), major)
    assert used, "no pinned actions found in the CI workflows"
    return used


def _python_matrix() -> list[str]:
    """Die Python-Versionen der Voll-Matrix aus ``ci.yml``, aufsteigend."""
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    matches = _PYTHON_MATRIX_RE.findall(text)
    assert len(matches) == 1, f"expected exactly one python-version matrix, found {len(matches)}"
    versions = re.findall(r'"([^"]+)"', matches[0])
    assert versions, "python-version matrix is empty"
    return sorted(versions, key=lambda v: tuple(int(part) for part in v.split(".")))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_resource_docs_track_package_layout() -> None:
    for path in RESOURCE_DOCS:
        text = _read(path)
        assert "BgRemover.py" not in text, f"{path} still documents the old monolith"
        assert "bgremover/" in text
        assert "bgremover/icons/*.png" in text
        assert "importlib.resources" in text


def test_resource_docs_track_constraints_snapshot() -> None:
    for path in RESOURCE_DOCS:
        text = _read(path)
        assert "requirements/constraints.txt" in text


def test_root_resource_doc_tracks_current_ci_workflows() -> None:
    """Die dokumentierten Action-Pins muessen den Workflows entsprechen.

    Frueher stand hier eine handgeschriebene Literal-Menge. Sie konnte
    gemeinsam mit der Doku veralten, ohne dass der Test es bemerkt (#949);
    genau das war passiert - ``codecov/codecov-action`` lief in ``ci.yml``,
    stand aber in keiner Fassung von RESOURCES.md. Seither wird die
    Soll-Menge aus den echten ``uses:``-Zeilen abgeleitet.
    """
    text = _read(ROOT / "RESOURCES.md")

    for relative in CI_WORKFLOWS:
        assert relative in text, f"RESOURCES.md documents no {relative}"
        assert (ROOT / relative).is_file(), f"{relative} does not exist"

    used = _used_actions()
    missing = sorted(f"{name}@v{major}" for name, major in used.items() if f"{name}@v{major}" not in text)
    assert not missing, "RESOURCES.md documents no pin for: " + ", ".join(missing)

    # Ein abgeloester Vorgaenger darf nicht zurueckkehren (#312). Die Regel
    # kommt aus den aktuellen Hauptversionen selbst, nicht aus einer zweiten
    # Literal-Liste, die ihrerseits veralten koennte.
    stale = sorted(
        f"{name}@v{older}"
        for name, major in used.items()
        for older in range(1, major)
        if f"{name}@v{older}" in text
    )
    assert not stale, "RESOURCES.md still documents superseded pins: " + ", ".join(stale)


def test_root_resource_doc_tracks_current_python_matrix() -> None:
    """Die dokumentierte Voll-Matrix muss zur ``ci.yml`` passen.

    Die Spanne wird aus der echten Matrix abgeleitet; das fruehere Literal
    ``3.10-3.13`` haette eine Matrixaenderung stillschweigend ueberlebt. Der
    ebenfalls entfallene Negativtest auf ``3.10/3.12`` ist damit redundant -
    eine veraltete Angabe enthaelt die abgeleitete Spanne schlicht nicht.
    """
    versions = _python_matrix()
    expected = f"{versions[0]}–{versions[-1]}"  # Halbgeviertstrich wie im Dokument

    text = _read(ROOT / "RESOURCES.md")
    assert expected in text, f"RESOURCES.md does not document the matrix {expected}"
