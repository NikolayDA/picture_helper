"""Static checks that keep the resource inventory aligned with the repo."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RESOURCE_DOCS = [
    ROOT / "RESOURCES.md",
    ROOT / "docs/i18n/en/RESOURCES.md",
    ROOT / "docs/i18n/es/RESOURCES.md",
    ROOT / "docs/i18n/fr/RESOURCES.md",
    ROOT / "docs/i18n/uk/RESOURCES.md",
    ROOT / "docs/i18n/zh/RESOURCES.md",
]


#: Die Workflows, die die RESOURCES-Dokumente als Test-/Qualitäts-CI führen.
#: Welche der 17 Workflows sie aufnehmen, ist eine redaktionelle Entscheidung
#: und bleibt deshalb literal; die Action-Pins darunter werden daraus
#: abgeleitet (#949).
CI_WORKFLOWS = (
    ".github/workflows/pr-ci.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/ui-nightly.yml",
    ".github/workflows/license-check.yml",
)

# ``uses:`` steht mal als eigener Schlüssel, mal als erster Schlüssel eines
# Listeneintrags (``- uses: …``). Ohne den optionalen Strich fährt die Suche
# an ``checkout`` und ``setup-python`` vorbei.
_USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)
#: Prüfbare Pin-Form: ``owner/action@v5`` oder ``owner/action@v6.1.0``.
_ACTION_RE = re.compile(r"^[^@\s]+@v\d+(?:\.\d+)*$")
#: Dieselbe Form, wie sie in den RESOURCES-Tabellen steht.
_DOCUMENTED_PIN_RE = re.compile(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+@v\d+(?:\.\d+)*")
_PYTHON_MATRIX_RE = re.compile(r"python-version:\s*\[([^\]]+)\]")


def _used_pins() -> set[str]:
    """Die exakten Action-Pins der CI-Workflows.

    Bewusst die vollständigen Pins statt nur der Hauptversion: Nur so fällt
    auf, wenn zwei Workflows während einer Migration verschiedene Stände
    fahren – ein ``max()`` über die Hauptversionen hätte den älteren, real
    laufenden Pin als „abgelöst" abgestempelt (#949).
    """
    pins: set[str] = set()
    for relative in CI_WORKFLOWS:
        path = ROOT / relative
        assert path.is_file(), f"{relative} does not exist"
        for reference in _USES_RE.findall(path.read_text(encoding="utf-8")):
            if reference.startswith("./"):
                continue  # lokaler bzw. wiederverwendbarer Workflow, kein Pin
            if not _ACTION_RE.match(reference):
                # Fail-closed: SHA-Pins, Branch-/Tag-Referenzen und andere
                # Formen ließen sich nicht gegen die Doku prüfen. Sie still
                # zu verwerfen brächte genau die Untererfassung zurück, die
                # #949 abstellen soll.
                pytest.fail(
                    f"{relative}: uses-Form nicht prüfbar gegen die "
                    f"RESOURCES-Dokumente – Regel bewusst erweitern statt "
                    f"still überspringen: {reference}"
                )
            pins.add(reference)
    assert pins, "no pinned actions found in the CI workflows"
    return pins


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


def test_resource_docs_track_current_ci_workflows() -> None:
    """Die dokumentierten Action-Pins müssen den Workflows entsprechen.

    Früher stand hier eine handgeschriebene Literal-Menge, geprüft nur gegen
    die deutsche Fassung. Sie konnte gemeinsam mit der Doku veralten, ohne
    dass der Test es bemerkt (#949) – und genau das war passiert:
    ``codecov/codecov-action`` lief in ``ci.yml``, stand aber in keiner der
    sechs Fassungen. Verglichen wird jetzt in **beide** Richtungen und über
    alle sechs Dokumente.
    """
    used = _used_pins()

    for path in RESOURCE_DOCS:
        text = _read(path)
        where = path.relative_to(ROOT)

        for relative in CI_WORKFLOWS:
            assert relative in text, f"{where} documents no {relative}"

        documented = set(_DOCUMENTED_PIN_RE.findall(text))

        missing = sorted(used - documented)
        assert not missing, f"{where} documents no pin for: " + ", ".join(missing)

        # Die Gegenrichtung: ein Eintrag, den kein Workflow mehr fährt. Das
        # deckt sowohl abgelöste Vorgänger (#312) als auch eine vollständig
        # entfernte Action ab, die sonst für immer stehen bliebe.
        superfluous = sorted(documented - used)
        assert not superfluous, (
            f"{where} documents pins no CI workflow uses: " + ", ".join(superfluous)
        )


def test_resource_docs_track_current_python_matrix() -> None:
    """Die dokumentierte Voll-Matrix muss zur ``ci.yml`` passen.

    Die Spanne wird aus der echten Matrix abgeleitet; das frühere Literal
    ``3.10–3.13`` hätte eine Matrixänderung stillschweigend überlebt. Der
    ebenfalls entfallene Negativtest auf ``3.10/3.12`` ist damit redundant –
    eine veraltete Angabe enthält die abgeleitete Spanne schlicht nicht.
    """
    versions = _python_matrix()
    expected = f"{versions[0]}–{versions[-1]}"  # Halbgeviertstrich wie im Dokument

    for path in RESOURCE_DOCS:
        assert expected in _read(path), (
            f"{path.relative_to(ROOT)} does not document the matrix {expected}"
        )
