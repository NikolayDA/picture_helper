"""Machine-readable release promotion contract (#744/#747)."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "release_contract", ROOT / "scripts" / "release_contract.py"
)
assert SPEC is not None and SPEC.loader is not None
rc = importlib.util.module_from_spec(SPEC)
sys.modules["release_contract"] = rc
SPEC.loader.exec_module(rc)

HEAD = "a" * 40
VERSION = "2.7.2"
TAG = f"v{VERSION}"
CANDIDATE_RUN_ID = 101
ACCEPTANCE_RUN_ID = 202
APPROVAL_ARTIFACT = "release-approval-manifest-1"
CHECKLIST = ROOT / "docs" / "RELEASE_ACCEPTANCE_CHECKLIST.md"


def _run(run_id: int, workflow: str, *, head: str = HEAD) -> dict:
    return {
        "id": run_id,
        "run_attempt": 1,
        "path": workflow,
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "head_sha": head,
    }


def _container_reference(name: str, artifact_id: int) -> dict:
    return {
        "name": name,
        "artifact_id": artifact_id,
        "archive_digest": "sha256:" + (str(artifact_id % 10) * 64),
    }


def _write_release_files(directory: Path) -> list[dict]:
    directory.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    for index, name in enumerate(rc.expected_artifact_names(VERSION, with_ai=True), start=1):
        payload = f"accepted-release-byte-sequence-{index}".encode()
        (directory / name).write_bytes(payload)
        records.append(
            {
                "name": name,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "platform": rc.platform_for_artifact(name),
            }
        )
    return records


def _candidate_artifacts(*freeze_attempts: int) -> list[dict]:
    if not freeze_attempts:
        freeze_attempts = (1,)
    return [
        {
            "id": index,
            "name": name,
            "digest": "sha256:" + (str(index % 10) * 64),
            "expired": False,
        }
        for index, name in enumerate(
            (
                *rc.ARTIFACT_CONTAINERS,
                *(f"release-freeze-provenance-{attempt}" for attempt in freeze_attempts),
            ),
            start=1,
        )
    ]


def _write_freeze_payload(path: Path, *, candidate_sha: str = HEAD) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": 1,
                "kind": "release-freeze-provenance",
                "release": {"version": VERSION},
                "candidate_sha": candidate_sha,
                "workflow": {"run_id": CANDIDATE_RUN_ID},
            }
        ),
        encoding="utf-8",
    )


def _candidate_contract(records: list[dict]) -> dict:
    return {
        "schema": 1,
        "kind": "release-candidate-contract",
        "policy_version": rc.POLICY_VERSION,
        "candidate": {
            "run_id": CANDIDATE_RUN_ID,
            "run_attempt": 1,
            "workflow": rc.BUILD_WORKFLOW,
            "head_sha": HEAD,
            "version": VERSION,
            "expected_tag": TAG,
            "artifact_containers": [
                _container_reference(name, index)
                for index, name in enumerate(rc.ARTIFACT_CONTAINERS, start=10)
            ],
            "freeze_provenance": {
                **_container_reference("release-freeze-provenance-1", 99),
                "payload_sha256": "f" * 64,
            },
        },
        "artifacts": records,
        "generated_at": "2026-08-01T10:00:00+00:00",
    }


def _write_evidence(root: Path, records: list[dict]) -> None:
    for platform in ("macos-arm64", "linux-arm64"):
        target = root / f"abnahme-{platform}"
        target.mkdir(parents=True)
        selected = [record for record in records if record["platform"] == platform]
        evidence = {
            "schema": 1,
            "kind": "abnahme-evidenz",
            "platform": platform,
            "status": "bestanden",
            "commit_sha": HEAD,
            "quelle": {"art": "run-id", "wert": str(CANDIDATE_RUN_ID)},
            "artefakte": [
                {
                    "name": item["name"],
                    "sha256": item["sha256"],
                    "bytes": item["bytes"],
                }
                for item in selected
            ],
        }
        (target / "evidenz.json").write_text(json.dumps(evidence), encoding="utf-8")


def _manifest(tmp_path: Path) -> tuple[dict, Path]:
    files = tmp_path / "files"
    records = _write_release_files(files)
    evidence = tmp_path / "evidence"
    _write_evidence(evidence, records)
    manifest = rc.create_approval_manifest(
        candidate_contract=_candidate_contract(records),
        checklist_path=CHECKLIST,
        evidence_dir=evidence,
        acceptance_summary={
            "schema": 1,
            "kind": "release-acceptance-summary",
            "commit_sha": HEAD,
            "blocking": False,
            "platforms": {
                "macos-arm64": "approved",
                "linux-arm64": "approved",
                "linux-x86_64": "paused",
            },
            "generated_at": "2026-08-01T10:05:00+00:00",
        },
        acceptance_run_id=ACCEPTANCE_RUN_ID,
        acceptance_run_attempt=1,
        acceptance_head_sha=HEAD,
        approval_artifact_name=APPROVAL_ARTIFACT,
    )
    return manifest, files


def _validate(manifest: dict, **overrides: object) -> None:
    args = {
        "expected_tag": TAG,
        "expected_candidate_run_id": CANDIDATE_RUN_ID,
        "expected_acceptance_run_id": ACCEPTANCE_RUN_ID,
        "expected_approval_artifact_name": APPROVAL_ARTIFACT,
        "candidate_run": _run(CANDIDATE_RUN_ID, rc.BUILD_WORKFLOW),
        "acceptance_run": _run(ACCEPTANCE_RUN_ID, rc.ACCEPTANCE_WORKFLOW),
        "tag_sha": HEAD,
        "checklist_path": CHECKLIST,
    }
    args.update(overrides)
    rc.validate_approval_manifest(manifest, **args)


def test_manifest_schema_binds_runs_head_tag_provenance_platforms_and_five_hashes(
    tmp_path: Path,
) -> None:
    manifest, files = _manifest(tmp_path)
    _validate(manifest)
    rc.verify_artifact_directory(manifest, files)
    assert manifest["schema"] == rc.MANIFEST_SCHEMA
    assert manifest["policy_version"] == rc.POLICY_VERSION
    assert manifest["candidate"]["run_id"] == CANDIDATE_RUN_ID
    assert manifest["candidate"]["head_sha"] == HEAD
    assert manifest["candidate"]["expected_tag"] == TAG
    assert manifest["acceptance"]["run_id"] == ACCEPTANCE_RUN_ID
    assert manifest["acceptance"]["platforms"]["linux-x86_64"] == "paused"
    assert manifest["provenance_reference"]["artifact_id"] == 99
    assert len(manifest["artifacts"]) == 5
    assert all(len(item["sha256"]) == 64 for item in manifest["artifacts"])
    assert manifest["release_instance"]["checklist"]["path"] == rc.CHECKLIST_PATH
    assert manifest["release_instance"]["candidate_sha"] == HEAD


def test_versioned_checklist_has_exact_scope_stable_ids_and_required_fields() -> None:
    checklist = rc.load_release_checklist(CHECKLIST)
    assert checklist["checklist_version"] == "1.1.0"
    assert tuple(item["id"] for item in checklist["artifacts"]) == rc.CHECKLIST_ARTIFACTS
    assert not any("windows" in json.dumps(item).lower() for item in checklist["artifacts"])
    criteria = checklist["criteria"]
    assert len({item["id"] for item in criteria}) == len(criteria)
    assert all(
        item[field]
        for item in criteria
        for field in ("id", "phase", "requirement", "owner", "evidence_source")
    )


def test_checklist_version_header_matches_the_machine_contract() -> None:
    """Die Kopfzeile ist eine handgepflegte Kopie ihrer eigenen JSON-Quelle."""
    checklist = rc.load_release_checklist(CHECKLIST)
    header = re.search(
        r"(?m)^\*\*Checklisten-Version:\*\* `([0-9]+\.[0-9]+\.[0-9]+)`$",
        CHECKLIST.read_text(encoding="utf-8"),
    )
    assert header is not None, "Kopfzeile mit Checklisten-Version fehlt"
    assert header.group(1) == checklist["checklist_version"]


def test_public_download_is_machine_generated_evidence_since_1_1_0() -> None:
    """#916: `PUBLIC-DOWNLOAD-01` darf nicht auf die Handprozedur zurueckfallen."""
    checklist = rc.load_release_checklist(CHECKLIST)
    criterion = next(
        item for item in checklist["criteria"] if item["id"] == "PUBLIC-DOWNLOAD-01"
    )
    assert criterion["verification"] == "publish"
    assert criterion["requirement"] == "MUST"
    assert criterion["waiver_allowed"] is False
    assert "public-download-report.json" in criterion["evidence_source"]
    assert set(criterion["artifacts"]) == set(rc.CHECKLIST_ARTIFACTS)
    # Der Nachweis entsteht erst nach dem Publish; die Instanz startet PENDING.
    assert criterion["phase"] == "publish"


def test_checklist_rejects_a_second_machine_contract_block(tmp_path: Path) -> None:
    changed = tmp_path / "docs" / "RELEASE_ACCEPTANCE_CHECKLIST.md"
    changed.parent.mkdir()
    changed.write_text(
        CHECKLIST.read_text(encoding="utf-8")
        + "\n<!-- release-checklist-json:start -->\n<!-- release-checklist-json:end -->\n",
        encoding="utf-8",
    )
    with pytest.raises(rc.ContractError, match="genau einen JSON-Vertragsblock"):
        rc.load_release_checklist(changed)


@pytest.mark.parametrize(
    ("original", "replacement", "field"),
    [
        (
            "| `VERSION-01` | Pre-Release | MUST | Release-Owner |",
            "| `VERSION-01` | Publish | MUST | Release-Owner |",
            "phase",
        ),
        (
            "| `VERSION-01` | Pre-Release | MUST | Release-Owner |",
            "| `VERSION-01` | Pre-Release | SHOULD | Release-Owner |",
            "requirement",
        ),
        (
            "| `VERSION-01` | Pre-Release | MUST | Release-Owner |",
            "| `VERSION-01` | Pre-Release | MUST | CI |",
            "owner",
        ),
    ],
)
def test_checklist_rejects_semantic_drift_between_table_and_json(
    tmp_path: Path,
    original: str,
    replacement: str,
    field: str,
) -> None:
    changed = tmp_path / "docs" / "RELEASE_ACCEPTANCE_CHECKLIST.md"
    changed.parent.mkdir()
    source = CHECKLIST.read_text(encoding="utf-8")
    assert source.count(original) == 1
    changed.write_text(source.replace(original, replacement), encoding="utf-8")

    with pytest.raises(rc.ContractError, match=rf"VERSION-01: Tabellenfeld {field} driftet"):
        rc.load_release_checklist(changed)


def test_release_instance_preserves_pending_x86_and_passes_pre_release_must(
    tmp_path: Path,
) -> None:
    manifest, _ = _manifest(tmp_path)
    instance = manifest["release_instance"]
    records = {item["id"]: item for item in instance["criteria"]}
    assert records["LINUX-X64-APPIMAGE-01"]["status"] == "PENDING"
    assert records["LINUX-X64-DEB-01"]["status"] == "PENDING"
    assert all(
        item["status"] == "PASS"
        for item in records.values()
        if item["phase"] == "pre-release" and item["requirement"] == "MUST"
    )
    rc.validate_release_instance_completion(
        instance,
        checklist=rc.load_release_checklist(CHECKLIST),
        checklist_path=CHECKLIST,
        through_phase="pre-release",
    )


def test_failed_should_criterion_blocks_phase_completion(tmp_path: Path) -> None:
    manifest, _ = _manifest(tmp_path)
    checklist = rc.load_release_checklist(CHECKLIST)
    failed = rc.set_release_instance_criterion(
        manifest["release_instance"],
        checklist=checklist,
        checklist_path=CHECKLIST,
        criterion_id="MALWARE-01",
        status="FAIL",
        evidence=["https://example.invalid/malware-finding"],
    )

    with pytest.raises(rc.ContractError, match="Kriterium MALWARE-01 ist fehlgeschlagen"):
        rc.validate_release_instance_completion(
            failed,
            checklist=checklist,
            checklist_path=CHECKLIST,
            through_phase="pre-release",
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("hash", "Dateihash"),
        ("id", "exakt alle Checklisten-IDs"),
        ("waiver", "Waiver ist fuer VERSION-01 nicht erlaubt"),
        ("fail-no-evidence", "FAIL ohne Evidenz fuer PUBLISH-01"),
    ],
)
def test_release_instance_tampering_or_forbidden_waiver_is_blocked(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    manifest, _ = _manifest(tmp_path)
    instance = copy.deepcopy(manifest["release_instance"])
    if mutation == "hash":
        instance["checklist"]["sha256"] = "0" * 64
    elif mutation == "id":
        instance["criteria"].pop()
    elif mutation == "waiver":
        record = next(item for item in instance["criteria"] if item["id"] == "VERSION-01")
        record.update(
            {
                "status": "WAIVED",
                "evidence": ["https://example.invalid/decision"],
                "waiver": {
                    "owner": "release-owner",
                    "reason": "not allowed",
                    "evidence": ["https://example.invalid/decision"],
                },
            }
        )
    else:
        record = next(item for item in instance["criteria"] if item["id"] == "PUBLISH-01")
        record["status"] = "FAIL"
    with pytest.raises(rc.ContractError, match=message):
        rc.validate_release_instance(
            instance,
            checklist=rc.load_release_checklist(CHECKLIST),
            checklist_path=CHECKLIST,
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing-schema", "Schema"),
        ("candidate-head", "unterschiedliche Commit-SHAs"),
        ("candidate-run", "anderen Kandidaten-Run"),
        ("acceptance-run", "anderen Abnahme-Run"),
        ("workflow", "falschen Build-Workflow"),
        ("container", "Artefaktcontainer"),
        ("platform", "Falscher Abnahmestatus"),
        ("provenance", "Provenienzreferenz"),
    ],
)
def test_manipulated_manifest_is_blocked(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    manifest, _ = _manifest(tmp_path)
    changed = copy.deepcopy(manifest)
    if mutation == "missing-schema":
        del changed["schema"]
    elif mutation == "candidate-head":
        changed["candidate"]["head_sha"] = "b" * 40
    elif mutation == "candidate-run":
        changed["candidate"]["run_id"] = 999
    elif mutation == "acceptance-run":
        changed["acceptance"]["run_id"] = 999
    elif mutation == "workflow":
        changed["candidate"]["workflow"] = ".github/workflows/evil.yml"
    elif mutation == "container":
        changed["candidate"]["artifact_containers"][0]["name"] = "bgremover-evil"
    elif mutation == "platform":
        changed["artifacts"][0]["acceptance_status"] = "blocked"
    else:
        changed["provenance_reference"]["artifact_id"] = 1000
    with pytest.raises(rc.ContractError, match=message):
        _validate(changed)


@pytest.mark.parametrize(
    ("override", "value", "message"),
    [
        ("expected_tag", "v9.9.9", "Tag und Manifest-Version"),
        ("tag_sha", "b" * 40, "Tag zeigt nicht"),
        (
            "candidate_run",
            _run(CANDIDATE_RUN_ID, ".github/workflows/other.yml"),
            "Falscher Workflow",
        ),
        (
            "acceptance_run",
            _run(ACCEPTANCE_RUN_ID, rc.ACCEPTANCE_WORKFLOW, head="b" * 40),
            "gehoert zu",
        ),
    ],
)
def test_wrong_tag_head_or_run_metadata_is_blocked(
    tmp_path: Path,
    override: str,
    value: object,
    message: str,
) -> None:
    manifest, _ = _manifest(tmp_path)
    with pytest.raises(rc.ContractError, match=message):
        _validate(manifest, **{override: value})


@pytest.mark.parametrize("mutation", ["missing", "extra", "hash"])
def test_missing_extra_or_hash_mismatched_candidate_files_are_blocked(
    tmp_path: Path,
    mutation: str,
) -> None:
    manifest, files = _manifest(tmp_path)
    if mutation == "missing":
        next(iter(files.iterdir())).unlink()
    elif mutation == "extra":
        (files / "unexpected.bin").write_bytes(b"x")
    else:
        next(iter(files.iterdir())).write_bytes(b"manipulated")
    with pytest.raises(rc.ContractError):
        rc.verify_artifact_directory(manifest, files)


def test_publish_plan_is_idempotent_and_blocks_partial_or_divergent_state(
    tmp_path: Path,
) -> None:
    manifest, files = _manifest(tmp_path)
    empty = tmp_path / "empty"
    empty.mkdir()
    assert rc.plan_publish(manifest, exists=False, is_draft=False, existing_dir=empty) == (
        "create-draft-upload"
    )
    assert rc.plan_publish(manifest, exists=True, is_draft=True, existing_dir=empty) == (
        "upload-to-draft"
    )
    assert rc.plan_publish(manifest, exists=True, is_draft=True, existing_dir=files) == (
        "publish-existing-draft"
    )
    assert rc.plan_publish(manifest, exists=True, is_draft=False, existing_dir=files) == (
        "already-complete"
    )

    partial = tmp_path / "partial"
    partial.mkdir()
    first = next(iter(files.iterdir()))
    (partial / first.name).write_bytes(first.read_bytes())
    with pytest.raises(rc.ContractError, match="teilweise"):
        rc.plan_publish(manifest, exists=True, is_draft=True, existing_dir=partial)

    divergent = tmp_path / "divergent"
    divergent.mkdir()
    for source in files.iterdir():
        (divergent / source.name).write_bytes(source.read_bytes())
    next(iter(divergent.iterdir())).write_bytes(b"different-published-bytes")
    with pytest.raises(rc.ContractError, match="abweichend"):
        rc.plan_publish(manifest, exists=True, is_draft=True, existing_dir=divergent)


def test_approval_creation_rejects_wrong_summary_or_extra_evidence(tmp_path: Path) -> None:
    files = tmp_path / "files"
    records = _write_release_files(files)
    evidence = tmp_path / "evidence"
    _write_evidence(evidence, records)
    summary = {
        "schema": 1,
        "kind": "release-acceptance-summary",
        "commit_sha": "b" * 40,
        "blocking": False,
        "platforms": {
            "macos-arm64": "approved",
            "linux-arm64": "approved",
            "linux-x86_64": "paused",
        },
        "generated_at": "2026-08-01T10:05:00+00:00",
    }

    def create(current_summary: dict) -> dict:
        return rc.create_approval_manifest(
            candidate_contract=_candidate_contract(records),
            checklist_path=CHECKLIST,
            evidence_dir=evidence,
            acceptance_summary=current_summary,
            acceptance_run_id=ACCEPTANCE_RUN_ID,
            acceptance_run_attempt=1,
            acceptance_head_sha=HEAD,
            approval_artifact_name=APPROVAL_ARTIFACT,
        )

    with pytest.raises(rc.ContractError, match="anderen Commit"):
        create(summary)

    summary["commit_sha"] = HEAD
    extra = evidence / "abnahme-unexpected"
    extra.mkdir()
    (extra / "evidenz.json").write_text(
        json.dumps({"platform": "unexpected"}),
        encoding="utf-8",
    )
    with pytest.raises(rc.ContractError, match="Evidenzmenge"):
        create(summary)


def test_per_file_comparison_is_the_single_rule_behind_the_publish_gate(
    tmp_path: Path,
) -> None:
    """#916: Bericht und Verdikt duerfen nie auseinanderlaufen."""
    manifest, files = _manifest(tmp_path)
    assert [item["status"] for item in rc.compare_artifact_directory(manifest, files)] == [
        "PASS"
    ] * 5

    names = sorted(path.name for path in files.iterdir())
    (files / names[0]).write_bytes(b"andere-bytes-gleiche-datei")
    (files / names[1]).unlink()
    (files / "unerwartet.bin").write_bytes(b"nicht im manifest")
    results = {item["name"]: item for item in rc.compare_artifact_directory(manifest, files)}

    assert results[names[0]]["status"] == "FAIL"
    assert results[names[0]]["sha256"] != results[names[0]]["expected_sha256"]
    assert results[names[1]]["status"] == "MISSING"
    assert results[names[1]]["sha256"] is None
    assert results["unerwartet.bin"]["status"] == "UNEXPECTED"
    assert results["unerwartet.bin"]["expected_sha256"] is None
    with pytest.raises(rc.ContractError, match="Artefaktmenge weicht ab"):
        rc.verify_artifact_directory(manifest, files)


def test_hash_only_divergence_still_blocks_the_publish_gate(tmp_path: Path) -> None:
    manifest, files = _manifest(tmp_path)
    victim = sorted(path.name for path in files.iterdir())[0]
    original = (files / victim).read_bytes()
    (files / victim).write_bytes(b"x" * len(original))

    results = {item["name"]: item for item in rc.compare_artifact_directory(manifest, files)}
    assert results[victim]["detail"] == "SHA-256 weicht ab"
    assert results[victim]["bytes"] == results[victim]["expected_bytes"]
    with pytest.raises(rc.ContractError, match="SHA-256 weicht ab"):
        rc.verify_artifact_directory(manifest, files)


def test_successful_publish_verification_proves_byte_equality(tmp_path: Path) -> None:
    """Simulates the post-upload re-download gate used by release-publish.yml."""
    manifest, candidate_files = _manifest(tmp_path)
    published = tmp_path / "published-download"
    published.mkdir()
    for source in candidate_files.iterdir():
        (published / source.name).write_bytes(source.read_bytes())
    rc.verify_artifact_directory(manifest, published)
    candidate_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in candidate_files.iterdir()
    }
    published_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in published.iterdir()
    }
    assert published_hashes == candidate_hashes


@pytest.mark.parametrize("layout", ["flat", "named"])
def test_prepare_candidate_accepts_download_artifact_layouts(
    tmp_path: Path, layout: str
) -> None:
    files = tmp_path / "files"
    records = _write_release_files(files)
    provenance_root = tmp_path / "provenance"
    provenance_parent = (
        provenance_root
        if layout == "flat"
        else provenance_root / "release-freeze-provenance-1"
    )
    _write_freeze_payload(provenance_parent / "release-freeze-provenance.json")

    contract = rc.prepare_candidate_contract(
        run=_run(CANDIDATE_RUN_ID, rc.BUILD_WORKFLOW),
        listing={"artifacts": _candidate_artifacts()},
        candidate_dir=files,
        provenance_dir=provenance_root,
        expected_run_id=CANDIDATE_RUN_ID,
        output_dir=tmp_path / "out",
    )

    assert contract["artifacts"] == records
    assert contract["candidate"]["freeze_provenance"]["name"] == (
        "release-freeze-provenance-1"
    )
    assert (tmp_path / "out" / "release-freeze-provenance.json").is_file()


def test_prepare_candidate_selects_latest_named_provenance_after_rerun(
    tmp_path: Path,
) -> None:
    files = tmp_path / "files"
    _write_release_files(files)
    provenance_root = tmp_path / "provenance"
    _write_freeze_payload(
        provenance_root
        / "release-freeze-provenance-1"
        / "release-freeze-provenance.json",
        candidate_sha="b" * 40,
    )
    _write_freeze_payload(
        provenance_root
        / "release-freeze-provenance-2"
        / "release-freeze-provenance.json"
    )

    contract = rc.prepare_candidate_contract(
        run=_run(CANDIDATE_RUN_ID, rc.BUILD_WORKFLOW),
        listing={"artifacts": _candidate_artifacts(1, 2)},
        candidate_dir=files,
        provenance_dir=provenance_root,
        expected_run_id=CANDIDATE_RUN_ID,
        output_dir=tmp_path / "out",
    )

    assert contract["candidate"]["freeze_provenance"]["name"] == (
        "release-freeze-provenance-2"
    )


@pytest.mark.parametrize("payload_count", [0, 2])
def test_prepare_candidate_rejects_missing_or_ambiguous_freeze_payload(
    tmp_path: Path, payload_count: int
) -> None:
    files = tmp_path / "files"
    _write_release_files(files)
    provenance_root = tmp_path / "provenance"
    provenance_root.mkdir()
    if payload_count:
        _write_freeze_payload(provenance_root / "release-freeze-provenance.json")
        _write_freeze_payload(
            provenance_root
            / "release-freeze-provenance-1"
            / "release-freeze-provenance.json"
        )

    with pytest.raises(rc.ContractError, match="Freeze-Provenienzdownload"):
        rc.prepare_candidate_contract(
            run=_run(CANDIDATE_RUN_ID, rc.BUILD_WORKFLOW),
            listing={"artifacts": _candidate_artifacts()},
            candidate_dir=files,
            provenance_dir=provenance_root,
            expected_run_id=CANDIDATE_RUN_ID,
            output_dir=tmp_path / "out",
        )


def test_prepare_candidate_rejects_wrong_freeze_provenance(tmp_path: Path) -> None:
    files = tmp_path / "files"
    _write_release_files(files)
    provenance_root = tmp_path / "provenance"
    provenance = provenance_root / "release-freeze-provenance-1"
    _write_freeze_payload(
        provenance / "release-freeze-provenance.json", candidate_sha="b" * 40
    )
    with pytest.raises(rc.ContractError, match="anderen Kandidaten"):
        rc.prepare_candidate_contract(
            run=_run(CANDIDATE_RUN_ID, rc.BUILD_WORKFLOW),
            listing={"artifacts": _candidate_artifacts()},
            candidate_dir=files,
            provenance_dir=provenance_root,
            expected_run_id=CANDIDATE_RUN_ID,
            output_dir=tmp_path / "out",
        )
