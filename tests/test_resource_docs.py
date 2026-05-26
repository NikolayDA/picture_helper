"""Static checks that keep the resource inventory aligned with the repo."""

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
    text = _read(ROOT / "RESOURCES.md")
    expected = {
        ".github/workflows/pr-ci.yml",
        ".github/workflows/ci.yml",
        ".github/workflows/license-check.yml",
        "actions/checkout@v5",
        "actions/setup-python@v6",
        "actions/upload-artifact@v4",
        "actions/github-script@v7",
    }
    missing = {token for token in expected if token not in text}
    assert not missing

    stale = {"actions/checkout@v4", "actions/setup-python@v5"}
    assert all(token not in text for token in stale)
