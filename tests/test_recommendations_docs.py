"""Static checks for the recommendation/roadmap documentation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RECOMMENDATION_DOCS = [
    ROOT / "RECOMMENDATIONS.md",
    ROOT / "docs/i18n/en/RECOMMENDATIONS.md",
    ROOT / "docs/i18n/es/RECOMMENDATIONS.md",
    ROOT / "docs/i18n/fr/RECOMMENDATIONS.md",
    ROOT / "docs/i18n/uk/RECOMMENDATIONS.md",
    ROOT / "docs/i18n/zh/RECOMMENDATIONS.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_recommendations_docs_have_current_status_log() -> None:
    for path in RECOMMENDATION_DOCS:
        text = _read(path)
        assert "bgremover/" in text
        assert "BgRemover.py" in text
        assert "requirements/constraints.txt" in text
        assert "tests/test_recommendations_docs.py" in text
        assert "tests/test_resource_docs.py" in text
        for pr in ("#70", "#72", "#73", "#74/#75", "#76", "#77", "#78"):
            assert pr in text


def test_root_recommendations_marks_historical_monolith_context() -> None:
    text = _read(ROOT / "RECOMMENDATIONS.md")
    assert "historische Befunde aus der Monolith-" in text
    assert "`BgRemover.py` ist gelöscht" in text
    assert "Aktueller Stand (Runde 6)" in text
