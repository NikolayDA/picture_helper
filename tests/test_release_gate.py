"""Governance für das Release-Gate (#250).

Stellt sicher, dass ``release-linux.yml`` Linux-Artefakte erst veröffentlicht,
wenn die maßgebliche Full-CI-Matrix (``ci.yml``, als wiederverwendbarer
Workflow) für genau diesen Commit grün ist, Tag-Format und ``project.version``
zusammenpassen und kein ``gh release``-Fehler pauschal mit ``|| true``
verschluckt wird.

Die sicherheitskritischen Invarianten sind textbasiert (laufen mit den
deklarierten ``[test]``-Extras, ohne PyYAML – analog zu
``tests/test_ci_qt_packages.py``). Die Struktur des Job-Graphen
(``needs``/``uses``) wird zusätzlich gegen das geparste YAML geprüft, sofern
PyYAML vorhanden ist (sonst übersprungen – analog zu
``tests/test_ci_workflow_yaml.py``).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_CI = _ROOT / ".github" / "workflows" / "ci.yml"
_RELEASE = _ROOT / ".github" / "workflows" / "release-linux.yml"


def _ci_text() -> str:
    return _CI.read_text(encoding="utf-8")


def _release_text() -> str:
    return _RELEASE.read_text(encoding="utf-8")


def _load(path: Path) -> dict:
    yaml = pytest.importorskip("yaml")
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


def _needs_list(job: dict) -> list[str]:
    needs = job.get("needs", [])
    return [needs] if isinstance(needs, str) else list(needs)


# ── Textbasierte Invarianten (laufen ohne PyYAML) ──────────────────────

def test_full_ci_declares_workflow_call() -> None:
    """``ci.yml`` ist wiederverwendbar, damit der Release-Workflow die Matrix
    als Gate aufrufen kann."""
    assert re.search(r"(?m)^\s*workflow_call:\s*$", _ci_text()), (
        "ci.yml muss einen workflow_call-Trigger haben (#250-Release-Gate)."
    )


def test_release_calls_reusable_full_ci() -> None:
    assert "uses: ./.github/workflows/ci.yml" in _release_text(), (
        "release-linux.yml muss die Full-CI-Matrix als wiederverwendbaren "
        "Workflow aufrufen, statt unabhängig auf denselben Tag zu reagieren."
    )


def test_release_build_and_publish_are_wired_with_needs() -> None:
    text = _release_text()
    assert re.search(r"(?m)^\s*needs:\s*\[[^\]]*\btest\b[^\]]*\]", text), (
        "build muss per needs auf die Full-CI-Matrix (test) warten."
    )
    assert re.search(r"(?m)^\s*needs:\s*\[[^\]]*\bverify-tag\b[^\]]*\]", text), (
        "build muss per needs auf verify-tag (Tag/Version-Abgleich) warten."
    )
    assert re.search(r"(?m)^\s*needs:\s*build\b", text), (
        "publish muss per needs auf einen erfolgreichen build warten."
    )


def test_release_does_not_swallow_gh_errors() -> None:
    assert "|| true" not in _release_text(), (
        "Fehler von gh release dürfen nicht pauschal mit '|| true' verborgen "
        "werden (#250)."
    )


def test_release_handles_existing_release_explicitly() -> None:
    text = _release_text()
    assert "gh release view" in text, (
        "Ein bereits existierendes Release muss explizit erkannt werden "
        "(statt '|| true')."
    )
    assert "gh release create" in text
    assert "gh release upload" in text


def test_release_verifies_tag_matches_project_version() -> None:
    text = _release_text()
    assert "tomllib" in text and '["project"]["version"]' in text, (
        "release-linux.yml muss project.version aus pyproject.toml lesen."
    )
    assert "GITHUB_REF_NAME" in text, "Tag-Name (GITHUB_REF_NAME) wird geprüft."
    assert r"v[0-9]+\.[0-9]+\.[0-9]+" in text, "Tag-Format vX.Y.Z wird geprüft."


def test_publish_job_is_gated_on_a_tag_ref() -> None:
    assert "startsWith(github.ref, 'refs/tags/')" in _release_text(), (
        "Der Publish-Job darf nur für Tag-Pushes laufen."
    )


# ── Struktur des Job-Graphen (geparstes YAML, übersprungen ohne PyYAML) ─

def test_release_jobgraph_gates_publish_on_tests_and_tag() -> None:
    jobs = _load(_RELEASE)["jobs"]

    # Die Full-CI-Matrix wird als wiederverwendbarer Workflow aufgerufen.
    assert jobs["test"].get("uses") == "./.github/workflows/ci.yml"

    # build hängt sowohl an der Matrix als auch am Tag/Version-Abgleich.
    build_needs = _needs_list(jobs["build"])
    assert "test" in build_needs, build_needs
    assert "verify-tag" in build_needs, build_needs

    # publish hängt an einem erfolgreichen build und läuft nur auf Tags.
    publish = jobs["publish"]
    assert "build" in _needs_list(publish), publish.get("needs")
    assert "refs/tags/" in publish.get("if", "")


def test_full_ci_is_reusable_and_not_independently_tag_triggered() -> None:
    doc = _load(_CI)
    # PyYAML (YAML 1.1) liest den ``on``-Key als Boolean ``True``.
    on = doc.get(True, doc.get("on"))
    assert isinstance(on, dict)
    assert "workflow_call" in on, "ci.yml muss als Gate aufrufbar sein."
    # Kein eigenständiger Tag-/Release-Trigger mehr → kein doppelter, ungegateter
    # Matrix-Lauf parallel zum Release-Workflow (#250).
    assert "push" not in on, "ci.yml soll nicht mehr unabhängig auf Tags laufen."
    assert "release" not in on, "ci.yml soll nicht mehr auf release:published laufen."
