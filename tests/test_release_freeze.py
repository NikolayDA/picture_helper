"""Vertragstests fuer Pfadpolicy und externe Freeze-Provenienz (#742/#743)."""
from __future__ import annotations

import ast
import copy
import json
import re
import subprocess
from pathlib import Path

import pytest

from scripts import (
    extract_release_notes as extract,
)
from scripts import (
    release_path_policy as rpp,
)
from scripts import (
    verify_release_freeze as vrf,
)

ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = ("de", "en", "es", "fr", "uk", "zh")
GITHUB_ACTIONS_ENV = (
    "GITHUB_ACTIONS",
    "GITHUB_SHA",
    "GITHUB_REPOSITORY",
    "GITHUB_WORKFLOW",
    "GITHUB_RUN_ID",
    "GITHUB_RUN_ATTEMPT",
    "GITHUB_JOB",
    "GITHUB_REF",
)


@pytest.fixture(autouse=True)
def _isolate_outer_github_actions_context(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mini-Repositories duerfen den Actions-Kontext des Testjobs nicht erben."""
    for name in GITHUB_ACTIONS_ENV:
        monkeypatch.delenv(name, raising=False)


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version = "([^"]+)"$', text)
    assert match is not None
    return match.group(1)


def _freeze_doc_text() -> str:
    path = ROOT / vrf.FREEZE_DOC_TEMPLATE.format(version=_pyproject_version())
    assert path.is_file()
    return path.read_text(encoding="utf-8")


def _changelog(language: str) -> str:
    path = ROOT / "CHANGELOG.md" if language == "de" else (
        ROOT / "docs" / "i18n" / language / "CHANGELOG.md"
    )
    return path.read_text(encoding="utf-8")


# ── Stabiler Freeze-Vertrag ────────────────────────────────────────────


def test_freeze_doc_contains_only_pre_merge_machine_fields() -> None:
    text = _freeze_doc_text()
    doc = vrf.parse_freeze_doc(text)
    assert doc.version == _pyproject_version()
    assert doc.base_tag == "v2.7.1"
    assert re.fullmatch(r"[0-9a-f]{40}", doc.base_sha)
    assert doc.scope == "patch-release-2.7.2"
    assert doc.policy_version == rpp.load_policy().version
    assert "Protokollierter Kandidaten-SHA" not in text
    assert "Commits im Fenster" not in text
    assert "Kandidaten-Commit`" not in text


@pytest.mark.parametrize("missing", ["Release-Scope", "Pfadpolicy", "Basis-Tag"])
def test_freeze_doc_rejects_missing_stable_field(missing: str) -> None:
    lines = [line for line in _freeze_doc_text().splitlines() if f"**{missing}:**" not in line]
    with pytest.raises(vrf.DocFormatError, match=missing):
        vrf.parse_freeze_doc("\n".join(lines))


def test_published_release_body_names_all_required_aspects() -> None:
    version = _pyproject_version()
    for language in LANGUAGES:
        notes = extract.extract_release_notes(_changelog(language), version)
        assert not vrf.missing_release_body_markers(notes, language)


def test_release_body_markers_cover_six_languages_and_four_aspects() -> None:
    assert set(vrf.RELEASE_BODY_MARKERS) == set(LANGUAGES)
    assert all(len(set(markers)) == 4 for markers in vrf.RELEASE_BODY_MARKERS.values())


# ── Versionierte positive Pfadpolicy (#743) ───────────────────────────


def test_every_neutral_rule_has_reason_evidence_and_a_covered_sample() -> None:
    policy = rpp.load_policy()
    assert policy.neutral_rules
    for rule in policy.neutral_rules:
        result = rpp.classify_path(rule.sample_path, policy)
        assert result.classification == rpp.RELEASE_NEUTRAL, rule.rule_id
        assert result.explicit and result.rule_id == rule.rule_id
        assert rule.reason.strip() and rule.evidence


def test_every_relevant_rule_has_a_covered_sample() -> None:
    policy = rpp.load_policy()
    assert policy.relevant_rules
    for rule in policy.relevant_rules:
        result = rpp.classify_path(rule.sample_path, policy)
        assert result.classification == rpp.CANDIDATE_RELEVANT, rule.rule_id
        assert result.explicit and result.rule_id == rule.rule_id


@pytest.mark.parametrize(
    "path",
    [
        "README.md",
        "CHANGELOG.md",
        "LICENSES.md",
        "docs/i18n/fr/CHANGELOG.md",
        "docs/i18n/zh/LICENSES.md",
        "bgremover/app.py",
        "packaging/linux/build_appimage.sh",
        "scripts/verify_release_freeze.py",
        "tests/test_release_gate.py",
        ".github/workflows/release-linux.yml",
        "docs/RELEASE_PROCESS.md",
        "docs/RELEASE_ACCEPTANCE_CHECKLIST.md",
        "docs/history/ADR-2026-release-abnahme-automatisierung.md",
        "docs/history/ADR-2026-release-manifest-publish.md",
        "docs/history/ADR-2026-clamav-signaturcache.md",
    ],
)
def test_known_release_inputs_are_explicitly_candidate_relevant(path: str) -> None:
    result = rpp.classify_path(path, rpp.load_policy())
    assert (result.classification, result.explicit) == (rpp.CANDIDATE_RELEVANT, True)


def test_docs_i18n_is_not_a_broad_neutral_class() -> None:
    policy = rpp.load_policy()
    for language in vrf.LANGUAGES:
        translated_readme = rpp.classify_path(f"docs/i18n/{language}/README.md", policy)
        assert (translated_readme.classification, translated_readme.explicit) == (
            rpp.RELEASE_NEUTRAL,
            True,
        )
    assert rpp.classify_path("docs/i18n/en/RECOMMENDATIONS.md", policy).classification == (
        rpp.RELEASE_NEUTRAL
    )
    assert rpp.classify_path("docs/i18n/en/CHANGELOG.md", policy).classification == (
        rpp.CANDIDATE_RELEVANT
    )
    unknown = rpp.classify_path("docs/i18n/en/NEW_RELEASE_INPUT.md", policy)
    assert (unknown.classification, unknown.explicit) == (rpp.CANDIDATE_RELEVANT, False)


def test_docs_history_is_not_a_broad_neutral_class() -> None:
    policy = rpp.load_policy()
    dry_run = rpp.classify_path("docs/history/RELEASE-RUNBOOK-DRY-RUN-2026-08-01.md", policy)
    assert (dry_run.classification, dry_run.explicit) == (rpp.RELEASE_NEUTRAL, True)
    unknown = rpp.classify_path("docs/history/NEW_RELEASE_CONTRACT.md", policy)
    assert (unknown.classification, unknown.explicit) == (rpp.CANDIDATE_RELEVANT, False)


def test_unknown_path_is_relevant_and_blocking() -> None:
    result = rpp.classify_path("irgendein/neuer/pfad.txt", rpp.load_policy())
    assert result.classification == rpp.CANDIDATE_RELEVANT
    assert not result.explicit and result.rule_id == rpp.UNKNOWN_RULE_ID


def test_candidate_relevant_paths_uses_the_same_classifier() -> None:
    policy = rpp.load_policy()
    assert vrf.candidate_relevant_paths(
        ("RECOMMENDATIONS.md", "CHANGELOG.md", "irgendein/neuer/pfad.txt"), policy
    ) == ("CHANGELOG.md", "irgendein/neuer/pfad.txt")


def test_policy_rejects_overlapping_neutral_and_relevant_rules() -> None:
    raw = json.loads((ROOT / rpp.POLICY_PATH).read_text(encoding="utf-8"))
    raw["candidate_relevant"].append(
        {
            "id": "conflict",
            "kind": "prefix",
            "path": "docs/i18n/en/",
            "sample_path": "docs/i18n/en/ANLEITUNG.md",
            "reason": "absichtlicher Testkonflikt",
        }
    )
    with pytest.raises(rpp.PolicyFormatError, match="mehrdeutige"):
        rpp.parse_policy(json.dumps(raw))


def test_policy_rejects_non_blocking_unknown_behavior() -> None:
    raw = json.loads((ROOT / rpp.POLICY_PATH).read_text(encoding="utf-8"))
    raw["unknown_path_behavior"] = "release-neutral"
    with pytest.raises(rpp.PolicyFormatError, match="candidate-relevant-blocking"):
        rpp.parse_policy(json.dumps(raw))


@pytest.mark.parametrize("path", ["docs//notes.md", "docs/./notes.md"])
def test_policy_rejects_non_normalised_paths(path: str) -> None:
    raw = json.loads((ROOT / rpp.POLICY_PATH).read_text(encoding="utf-8"))
    raw["release_neutral"][0]["path"] = path
    raw["release_neutral"][0]["sample_path"] = "docs/notes.md"
    with pytest.raises(rpp.PolicyFormatError, match="nicht normalisierter"):
        rpp.parse_policy(json.dumps(raw))


def test_pyproject_file_inputs_are_explicitly_guarded() -> None:
    policy = rpp.load_policy()
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = re.search(r'(?m)^readme = "([^"]+)"$', text)
    licenses = re.search(r"(?m)^license-files = (\[[^\n]+\])$", text)
    assert readme is not None and licenses is not None
    actual = {readme.group(1), *ast.literal_eval(licenses.group(1))}
    assert actual == set(policy.drift_guards["pyproject_file_inputs"])
    for path in actual:
        result = rpp.classify_path(path, policy)
        assert result.explicit and result.classification == rpp.CANDIDATE_RELEVANT


def test_pyproject_package_roots_are_explicitly_guarded() -> None:
    policy = rpp.load_policy()
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    packages = re.search(r"(?m)^packages = (\[[^\n]+\])$", text)
    assert packages is not None
    actual = {f"{name}/" for name in ast.literal_eval(packages.group(1))}
    assert actual == set(policy.drift_guards["pyproject_package_roots"])
    for root in actual:
        result = rpp.classify_path(f"{root}__init__.py", policy)
        assert result.explicit and result.classification == rpp.CANDIDATE_RELEVANT


def test_release_document_drift_guard_is_explicit_and_current() -> None:
    policy = rpp.load_policy()
    guarded = set(policy.drift_guards["release_documents"])
    discovered = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "docs").glob("RELEASE*.md")
    }
    discovered.add(vrf.FREEZE_DOC_TEMPLATE.format(version=_pyproject_version()))
    assert discovered <= guarded
    for path in guarded:
        result = rpp.classify_path(path, policy)
        assert result.explicit and result.classification == rpp.CANDIDATE_RELEVANT


# ── Git-Historie und abgeleitetes Ledger ──────────────────────────────


def _run(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _write(repo: Path, relative: str, text: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _head(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _commit_all(repo: Path, message: str) -> str:
    _run(repo, "add", "-A")
    _run(repo, "commit", "-q", "-m", message)
    return _head(repo)


@pytest.fixture
def tiny_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo, "init", "-q", "-b", "main")
    _run(repo, "config", "user.email", "test@example.invalid")
    _run(repo, "config", "user.name", "Test")
    _write(repo, "README.md", "base\n")
    _commit_all(repo, "base")
    return repo


def test_derive_candidate_ignores_release_neutral_successor(tiny_repo: Path) -> None:
    base = _head(tiny_repo)
    _write(tiny_repo, "bgremover/fix.py", "x = 1\n")
    relevant = _commit_all(tiny_repo, "relevant")
    _write(tiny_repo, "RECOMMENDATIONS.md", "status\n")
    _commit_all(tiny_repo, "neutral")
    assert vrf.derive_candidate(tiny_repo, base, "HEAD", rpp.load_policy()) == relevant


def test_derive_candidate_ignores_discarded_side_branch(tiny_repo: Path) -> None:
    base = _head(tiny_repo)
    _run(tiny_repo, "checkout", "-q", "-b", "side")
    _write(tiny_repo, "bgremover/leak.py", "x = 1\n")
    side = _commit_all(tiny_repo, "side change")
    _run(tiny_repo, "checkout", "-q", "main")
    _write(tiny_repo, "RECOMMENDATIONS.md", "neutral\n")
    _commit_all(tiny_repo, "neutral")
    _run(tiny_repo, "merge", "-q", "-s", "ours", "--no-edit", "side")
    assert side in vrf.commits_between(tiny_repo, base, "HEAD")
    assert side not in vrf.commits_between(tiny_repo, base, "HEAD", first_parent=True)
    assert vrf.derive_candidate(tiny_repo, base, "HEAD", rpp.load_policy()) is None


def test_rename_from_relevant_into_neutral_stays_relevant(tiny_repo: Path) -> None:
    _write(tiny_repo, "bgremover/x.py", "x = 1\n")
    _commit_all(tiny_repo, "code")
    _run(tiny_repo, "mv", "bgremover/x.py", "RECOMMENDATIONS.md")
    moved = _commit_all(tiny_repo, "move")
    paths = vrf.changed_paths(tiny_repo, moved)
    assert "bgremover/x.py" in paths and "RECOMMENDATIONS.md" in paths
    assert vrf.candidate_relevant_paths(paths, rpp.load_policy()) == ("bgremover/x.py",)


def _minimal_policy(freeze_path: str) -> str:
    return json.dumps(
        {
            "schema": 1,
            "policy_version": 1,
            "unknown_path_behavior": "candidate-relevant-blocking",
            "release_neutral": [
                {
                    "id": "notes",
                    "kind": "exact",
                    "path": "NOTES.md",
                    "sample_path": "NOTES.md",
                    "reason": "kein Build-Eingang",
                    "evidence": ["Mini-Repository-Test"],
                }
            ],
            "candidate_relevant": [
                {
                    "id": "app",
                    "kind": "prefix",
                    "path": "bgremover/",
                    "sample_path": "bgremover/app.py",
                    "reason": "Anwendung",
                },
                {
                    "id": "freeze",
                    "kind": "exact",
                    "path": freeze_path,
                    "sample_path": freeze_path,
                    "reason": "Freeze",
                },
                {
                    "id": "policy",
                    "kind": "exact",
                    "path": rpp.POLICY_PATH,
                    "sample_path": rpp.POLICY_PATH,
                    "reason": "Policy",
                },
            ],
            "drift_guards": {"pyproject_file_inputs": [], "release_documents": [freeze_path]},
        },
        indent=2,
    )


def _seed_release_repo(repo: Path) -> tuple[str, str]:
    _write(repo, "pyproject.toml", '[project]\nversion = "9.9.9"\n')
    base = _commit_all(repo, "release base")
    _run(repo, "tag", "v9.9.8", base)
    freeze_path = vrf.FREEZE_DOC_TEMPLATE.format(version="9.9.9")
    _write(repo, rpp.POLICY_PATH, _minimal_policy(freeze_path))
    _write(
        repo,
        freeze_path,
        "# Freeze\n\n"
        f"- **Basis-Tag:** `v9.9.8` (= `{base}`)\n"
        "- **Kandidatenversion:** `9.9.9`\n"
        "- **Release-Scope:** `test`\n"
        "- **Pfadpolicy:** `release/path-policy.json` (Version `1`)\n",
    )
    _write(repo, "bgremover/app.py", "x = 1\n")
    candidate = _commit_all(repo, "candidate without self pin")
    return base, candidate


def _disable_content_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(vrf, "_check_versions", lambda repo, rev, doc: [])
    monkeypatch.setattr(vrf, "_check_release_body", lambda repo, rev, doc: [])


def test_changed_policy_requires_version_bump(tiny_repo: Path) -> None:
    freeze_path = vrf.FREEZE_DOC_TEMPLATE.format(version="9.9.9")
    _write(tiny_repo, rpp.POLICY_PATH, _minimal_policy(freeze_path))
    base = _commit_all(tiny_repo, "policy base")
    policy_data = json.loads(_minimal_policy(freeze_path))
    policy_data["release_neutral"][0]["reason"] = "geänderte Begründung"
    _write(tiny_repo, rpp.POLICY_PATH, json.dumps(policy_data, indent=2))
    _commit_all(tiny_repo, "policy changed without bump")
    doc = vrf.FreezeDoc("9.9.9", "v9.9.8", base, "test", 1)

    finding = vrf._check_policy(tiny_repo, doc, vrf.load_policy_at_rev(tiny_repo, "HEAD"))

    assert finding.severity == "error"
    assert finding.code == "policy-version-not-bumped"


def test_candidate_merge_passes_without_follow_up_commit(
    tiny_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _disable_content_checks(monkeypatch)
    _base, first = _seed_release_repo(tiny_repo)
    _write(tiny_repo, "bgremover/fix.py", "fixed = True\n")
    second = _commit_all(tiny_repo, "candidate relevant merge result")

    findings = vrf.verify(tiny_repo, "HEAD")
    assert not [finding for finding in findings if finding.severity == "error"]
    provenance = vrf.build_provenance(tiny_repo, "HEAD")
    assert provenance["candidate_sha"] == second
    assert provenance["content_candidate_sha"] == second
    assert provenance["candidate_sha"] != first
    assert provenance["commit_count"] == 2


def test_unknown_path_blocks_freeze_gate(
    tiny_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _disable_content_checks(monkeypatch)
    _seed_release_repo(tiny_repo)
    _write(tiny_repo, "unknown/new.txt", "x\n")
    _commit_all(tiny_repo, "unknown input")
    findings = vrf.verify(tiny_repo, "HEAD")
    assert "unclassified-path" in {finding.code for finding in findings}
    with pytest.raises(vrf.DocFormatError, match="fehlerhaftem Gate"):
        vrf.build_provenance(tiny_repo, "HEAD")


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("candidate", "provenance-candidate-mismatch"),
        ("base", "provenance-base-mismatch"),
        ("policy", "provenance-policy-mismatch"),
        ("count", "provenance-commit-count-mismatch"),
        ("commits", "provenance-commit-list-mismatch"),
    ],
)
def test_provenance_manipulation_is_detected(
    tiny_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    expected_code: str,
) -> None:
    _disable_content_checks(monkeypatch)
    _seed_release_repo(tiny_repo)
    evidence = vrf.build_provenance(tiny_repo, "HEAD")
    changed = copy.deepcopy(evidence)
    if mutation == "candidate":
        changed["candidate_sha"] = "0" * 40
    elif mutation == "base":
        changed["release"]["base_sha"] = "0" * 40  # type: ignore[index]
    elif mutation == "policy":
        changed["policy"]["version"] = 999  # type: ignore[index]
    elif mutation == "count":
        changed["commit_count"] = 999
    else:
        changed["commits"] = []
    findings = vrf.verify_provenance(tiny_repo, changed, "HEAD")
    assert expected_code in {finding.code for finding in findings}


def test_actions_context_requires_candidate_and_run_ids(
    tiny_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _disable_content_checks(monkeypatch)
    _seed_release_repo(tiny_repo)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    for name in ("GITHUB_SHA", "GITHUB_REPOSITORY", "GITHUB_WORKFLOW", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT"):
        monkeypatch.delenv(name, raising=False)
    findings = vrf.verify(tiny_repo, "HEAD")
    codes = {finding.code for finding in findings}
    assert "workflow-candidate-missing" in codes
    assert "workflow-provenance-missing" in codes


def test_release_workflow_uploads_attempt_bound_provenance() -> None:
    workflow = (ROOT / ".github/workflows/release-linux.yml").read_text(encoding="utf-8")
    verify_job = workflow.split("  verify-candidate:", 1)[1].split("\n  test:", 1)[0]
    assert "--require-pin" not in verify_job
    assert "--output-provenance release-evidence/release-freeze-provenance.json" in verify_job
    assert "release-freeze-provenance-${{ github.run_attempt }}" in verify_job
    assert "actions/upload-artifact@v7" in verify_job
    assert "fetch-depth: 0" in verify_job


def test_make_target_no_longer_requires_a_pin() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    target = makefile.split("release-freeze-check:", 1)[1].split("\n\n", 1)[0]
    assert "verify_release_freeze.py" in target
    assert "--require-pin" not in target


def test_no_pin_checker_remains_in_the_implementation() -> None:
    assert not hasattr(vrf, "_check_pin")
    source = (ROOT / "scripts/verify_release_freeze.py").read_text(encoding="utf-8")
    assert '"--require-pin"' not in source
