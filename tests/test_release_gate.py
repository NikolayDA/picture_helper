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


# ── Release-Follow-ups (#257) ──────────────────────────────────────────

def test_test_job_requires_verify_tag() -> None:
    """Der wiederverwendbare Test-Job wartet auf verify-tag – ein ungültiger
    oder zur Paketversion unpassender Tag startet die teure Matrix nicht."""
    assert re.search(r"(?m)^\s*needs:\s*verify-tag\b", _release_text()), (
        "test (uses: ci.yml) muss per needs auf verify-tag warten (#257)."
    )


def test_publish_provides_repo_context_for_gh() -> None:
    assert "GH_REPO: ${{ github.repository }}" in _release_text(), (
        "Die gh-release-Schritte brauchen GH_REPO (kein Checkout), damit der "
        "Repo-Kontext auf einem frischen Runner sicher ist (#257)."
    )


def test_release_passes_id_token_through_to_reusable_ci() -> None:
    """Textbasiert (ohne PyYAML): release-linux.yml muss ``id-token: write``
    gewaehren, weil das aufgerufene ci.yml es fuer den Codecov-OIDC-Upload
    (#303) verlangt. Ein per ``uses`` aufgerufener Workflow darf nicht mehr
    Rechte verlangen als der Aufrufer – fehlt das Recht, lehnt GitHub den
    gesamten Run beim Start ab (startup_failure)."""
    assert re.search(r"(?m)^\s*id-token:\s*write\b", _release_text()), (
        "release-linux.yml muss id-token: write an die aufgerufene Full-CI-"
        "Matrix durchreichen, sonst scheitert der Release-Run beim Start."
    )


def test_publish_artifact_download_is_rerun_resilient() -> None:
    text = _release_text()
    assert "run-id: ${{ github.run_id }}" in text, (
        "download-artifact muss run-id setzen, damit ein Re-run die Artefakte "
        "des Original-Runs findet (#257)."
    )
    assert "github-token: ${{ github.token }}" in text, (
        "download-artifact per run-id braucht ein github-token."
    )
    assert re.search(r"(?m)^\s*actions:\s*read\b", text), (
        "Der Publish-Job braucht actions: read für den API-Download per run-id."
    )


# ── Struktur des Job-Graphen (geparstes YAML, übersprungen ohne PyYAML) ─

def test_release_jobgraph_gates_publish_on_tests_and_tag() -> None:
    jobs = _load(_RELEASE)["jobs"]

    # Die Full-CI-Matrix wird als wiederverwendbarer Workflow aufgerufen.
    assert jobs["test"].get("uses") == "./.github/workflows/ci.yml"

    # #257: der Test-Job selbst wartet auf verify-tag – ein ungültiger Tag
    # startet die teure Matrix gar nicht erst.
    assert "verify-tag" in _needs_list(jobs["test"]), jobs["test"].get("needs")

    # #303: ci.yml fordert id-token: write (Codecov-OIDC). Der aufrufende
    # test-Job muss dieses Recht durchreichen, sonst lehnt GitHub den Run beim
    # Start ab (ein aufgerufener Workflow darf nicht mehr Rechte verlangen als
    # der Aufrufer).
    assert jobs["test"].get("permissions", {}).get("id-token") == "write", (
        jobs["test"].get("permissions")
    )

    # build hängt sowohl an der Matrix als auch am Tag/Version-Abgleich.
    build_needs = _needs_list(jobs["build"])
    assert "test" in build_needs, build_needs
    assert "verify-tag" in build_needs, build_needs

    # publish hängt an einem erfolgreichen build und läuft nur auf Tags.
    publish = jobs["publish"]
    assert "build" in _needs_list(publish), publish.get("needs")
    assert "refs/tags/" in publish.get("if", "")

    # #257: Publish braucht Schreibrecht aufs Release UND Leserecht auf die
    # Actions-API (Re-run-resilienter Download per run-id).
    perms = publish.get("permissions", {})
    assert perms.get("contents") == "write", perms
    assert perms.get("actions") == "read", perms
    # #257: Repo-Kontext für gh ohne Checkout.
    assert publish.get("env", {}).get("GH_REPO") == "${{ github.repository }}"
    # #257: Re-run-resilienter Artefakt-Download (run-id + Token).
    dl_step = next(
        s for s in publish["steps"]
        if "download-artifact" in str(s.get("uses", ""))
    )
    dl = dl_step.get("with", {})
    assert dl.get("run-id") == "${{ github.run_id }}", dl
    assert dl.get("github-token") == "${{ github.token }}", dl


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
