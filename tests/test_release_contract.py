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


# ── Release-Ref statt main-Freeze (#918) ────────────────────────────────────


def _ref_payload(sha: str = HEAD, *, ref: str = "refs/heads/release/v2.7.2",
                 kind: str = "commit") -> dict:
    """Antwort von ``gh api repos/OWNER/REPO/git/ref/heads/release/vX.Y.Z``."""
    return {"ref": ref, "object": {"type": kind, "sha": sha}}


def test_release_ref_must_point_at_the_candidate_commit() -> None:
    assert rc.validate_release_ref(
        _ref_payload(), expected_ref=f"release/{TAG}", expected_sha=HEAD
    ) == HEAD


def test_release_ref_rejects_a_ref_that_moved_off_the_candidate() -> None:
    """Der Kernfall: ein nachtraeglich bewegter oder verwechselter Ref.

    Ohne diese Pruefung liefe der Dispatch auf fremdem Code – erkannt erst im
    ``candidate-source``-Gate der Abnahme, also nach dem Lauf.
    """
    with pytest.raises(rc.ContractError, match="zeigt auf b{40}"):
        rc.validate_release_ref(
            _ref_payload("b" * 40), expected_ref=f"release/{TAG}", expected_sha=HEAD
        )


def test_release_ref_rejects_another_ref_and_non_commit_targets() -> None:
    # Verwechselter Ref: Die Antwort gehoert zu main statt zum Release-Ref.
    with pytest.raises(rc.ContractError, match="refs/heads/main"):
        rc.validate_release_ref(
            _ref_payload(ref="refs/heads/main"),
            expected_ref=f"release/{TAG}", expected_sha=HEAD,
        )
    # Annotiertes Tag: der SHA waere der des Tag-Objekts, nicht des Commits.
    with pytest.raises(rc.ContractError, match="statt auf einen Commit"):
        rc.validate_release_ref(
            _ref_payload(kind="tag"), expected_ref=f"release/{TAG}", expected_sha=HEAD
        )
    with pytest.raises(rc.ContractError, match="ohne Objektangabe"):
        rc.validate_release_ref(
            {"ref": f"refs/heads/release/{TAG}"},
            expected_ref=f"release/{TAG}", expected_sha=HEAD,
        )


@pytest.mark.parametrize(
    "ref",
    [
        "main",
        "hotfix/v2.7.2",
        "release/2.7.2",
        "release/v2.7",
        # Dieselbe Versionsregel wie der uebrige Vertrag (_SEMVER_RE), nicht eine
        # zweite, laxere: keine fuehrenden Nullen, keine 0-Hauptversion, kein
        # Vorabsuffix. Der Ref entsteht aus RELEASE_TAG = "v${RELEASE_VERSION}".
        "release/v01.2.3",
        "release/v0.1.0",
        "release/v2.7.2-rc1",
    ],
)
def test_release_ref_enforces_the_naming_scheme(ref: str) -> None:
    """Nur ``release/vX.Y.Z``: Das Ruleset schuetzt genau dieses Muster."""
    with pytest.raises(rc.ContractError, match="Schema"):
        rc.validate_release_ref(_ref_payload(), expected_ref=ref, expected_sha=HEAD)


def test_release_ref_uses_the_same_version_rule_as_the_rest_of_the_contract() -> None:
    """Zwei Versionsschemata in einer Datei waeren der Anfang der Drift."""
    assert rc._SEMVER_RE.pattern.strip("^$") in rc._RELEASE_REF_RE.pattern


def test_acceptance_run_on_a_foreign_ref_is_rejected() -> None:
    """Das harte Gate bleibt der SHA-Vergleich, nicht der Ref-Name (#918).

    Ein Lauf, der auf einem anderen Commit startete – etwa versehentlich auf
    ``main`` dispatcht –, wird abgewiesen, auch wenn Run-ID und Workflow
    stimmen.
    """
    with pytest.raises(rc.ContractError, match="gehoert zu"):
        rc.validate_workflow_run(
            _run(ACCEPTANCE_RUN_ID, rc.ACCEPTANCE_WORKFLOW, head="c" * 40),
            expected_run_id=ACCEPTANCE_RUN_ID,
            expected_workflow=rc.ACCEPTANCE_WORKFLOW,
            expected_head_sha=HEAD,
        )


# ── Tag-Anlage im Publish-Workflow (#919, Stufe 1) ──────────────────────────

TAG_OBJECT_SHA = "b" * 40


def _tag_ref(sha: str = HEAD, *, ref: str = f"refs/tags/{TAG}", kind: str = "commit") -> dict:
    """Antwort von ``gh api repos/OWNER/REPO/git/ref/tags/vX.Y.Z``."""
    return {"ref": ref, "object": {"type": kind, "sha": sha}}


def _tag_object(commit: str = HEAD, *, sha: str = TAG_OBJECT_SHA) -> dict:
    """Antwort von ``gh api repos/OWNER/REPO/git/tags/<tag-objekt-sha>``."""
    return {"sha": sha, "object": {"type": "commit", "sha": commit}}


def test_missing_tag_is_planned_for_creation_on_the_manifest_commit(tmp_path: Path) -> None:
    manifest, _ = _manifest(tmp_path)
    assert rc.plan_release_tag(manifest, tag=TAG, ref_payload=None) == (
        rc.TAG_PLAN_CREATE, HEAD,
    )


def test_existing_correct_tag_is_only_verified(tmp_path: Path) -> None:
    """Wiederanlauf ist idempotent: Ein passender Tag wird nicht neu gesetzt."""
    manifest, _ = _manifest(tmp_path)
    assert rc.plan_release_tag(manifest, tag=TAG, ref_payload=_tag_ref()) == (
        rc.TAG_PLAN_ALREADY_CORRECT, HEAD,
    )


def test_divergent_tag_blocks_instead_of_being_moved(tmp_path: Path) -> None:
    """Ein Tag wird nie verschoben - auch nicht "zur Reparatur"."""
    manifest, _ = _manifest(tmp_path)
    with pytest.raises(rc.ContractError, match="wird nicht verschoben"):
        rc.plan_release_tag(manifest, tag=TAG, ref_payload=_tag_ref("c" * 40))


def test_annotated_tag_is_dereferenced_before_the_sha_comparison(tmp_path: Path) -> None:
    """Der Ref eines annotierten Tags zeigt auf das Tag-Objekt, nicht den Commit.

    Ohne Dereferenzierung verglichen wir den Tag-Objekt-SHA gegen den
    Kandidaten-SHA - der Vergleich schluege immer fehl (oder, schlimmer, ginge
    bei einer laxeren Pruefung still durch). Runbook-Schritt 7 setzt bewusst
    ein **annotiertes** Tag, dieser Pfad ist also der Regelfall.
    """
    manifest, _ = _manifest(tmp_path)
    assert rc.plan_release_tag(
        manifest,
        tag=TAG,
        ref_payload=_tag_ref(TAG_OBJECT_SHA, kind="tag"),
        tag_object_payload=_tag_object(),
    ) == (rc.TAG_PLAN_ALREADY_CORRECT, HEAD)

    # Dasselbe annotierte Tag auf einem fremden Commit blockiert.
    with pytest.raises(rc.ContractError, match="wird nicht verschoben"):
        rc.plan_release_tag(
            manifest,
            tag=TAG,
            ref_payload=_tag_ref(TAG_OBJECT_SHA, kind="tag"),
            tag_object_payload=_tag_object("c" * 40),
        )


def test_annotated_tag_without_its_object_payload_fails_closed(tmp_path: Path) -> None:
    manifest, _ = _manifest(tmp_path)
    with pytest.raises(rc.ContractError, match="annotiert"):
        rc.plan_release_tag(manifest, tag=TAG, ref_payload=_tag_ref(TAG_OBJECT_SHA, kind="tag"))


def test_tag_object_payload_must_belong_to_the_referenced_tag(tmp_path: Path) -> None:
    """Eine untergeschobene Tag-Objekt-Antwort darf den Vergleich nicht tragen."""
    manifest, _ = _manifest(tmp_path)
    with pytest.raises(rc.ContractError, match="gehoert nicht zu"):
        rc.plan_release_tag(
            manifest,
            tag=TAG,
            ref_payload=_tag_ref(TAG_OBJECT_SHA, kind="tag"),
            tag_object_payload=_tag_object(sha="d" * 40),
        )


def test_tag_plan_rejects_a_foreign_ref_answer_and_a_manifest_mismatch(tmp_path: Path) -> None:
    manifest, _ = _manifest(tmp_path)
    with pytest.raises(rc.ContractError, match="gehoert zu"):
        rc.plan_release_tag(manifest, tag=TAG, ref_payload=_tag_ref(ref="refs/tags/v9.9.9"))
    with pytest.raises(rc.ContractError, match="weicht vom Manifest-Tag"):
        rc.plan_release_tag(manifest, tag="v9.9.9", ref_payload=None)


def test_tag_plan_rejects_a_branch_object_behind_the_tag_ref(tmp_path: Path) -> None:
    manifest, _ = _manifest(tmp_path)
    with pytest.raises(rc.ContractError, match="statt auf Commit oder Tag-Objekt"):
        rc.plan_release_tag(manifest, tag=TAG, ref_payload=_tag_ref(kind="tree"))


def test_matching_refs_selection_ignores_prefix_neighbours() -> None:
    """`git/matching-refs` sucht per Praefix - das darf nie als Treffer gelten.

    Laut GitHub-Referenz liefert `tags/v2.7.2` auch `v2.7.2-rc1`. Ohne exakte
    Auswahl haette ein Vorabtag den Anschein erweckt, der Release-Tag existiere
    schon: Der Workflow haette dann `already-correct` oder einen Konflikt
    gemeldet, statt den Tag anzulegen.
    """
    neighbours = [
        _tag_ref(ref=f"refs/tags/{TAG}-rc1"),
        _tag_ref(ref=f"refs/tags/{TAG}.1"),
    ]
    assert rc.select_tag_ref(neighbours, tag=TAG) is None
    assert rc.select_tag_ref([], tag=TAG) is None
    exact = _tag_ref()
    assert rc.select_tag_ref([*neighbours, exact], tag=TAG) == exact
    with pytest.raises(rc.ContractError, match="mehrfach"):
        rc.select_tag_ref([exact, exact], tag=TAG)
    with pytest.raises(rc.ContractError, match="keine Liste"):
        rc.select_tag_ref({"ref": f"refs/tags/{TAG}"}, tag=TAG)


def test_plan_tag_cli_reports_action_and_candidate(tmp_path: Path, capsys) -> None:
    manifest, _ = _manifest(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    refs_path = tmp_path / "matching-refs.json"

    # Leere Liste = Tag fehlt (der Endpunkt antwortet immer mit HTTP 200).
    refs_path.write_text("[]", encoding="utf-8")
    args = ["plan-tag", "--manifest", str(manifest_path), "--tag", TAG,
            "--matching-refs-json", str(refs_path)]
    assert rc.main(args) == 0
    assert "create" in capsys.readouterr().out

    refs_path.write_text(json.dumps([_tag_ref()]), encoding="utf-8")
    assert rc.main(args) == 0
    assert "already-correct" in capsys.readouterr().out

    refs_path.write_text(json.dumps([_tag_ref("c" * 40)]), encoding="utf-8")
    assert rc.main(args) == 2

    # Nur ein Praefix-Nachbar: der Tag selbst fehlt weiterhin.
    refs_path.write_text(json.dumps([_tag_ref(ref=f"refs/tags/{TAG}-rc1")]), encoding="utf-8")
    assert rc.main(args) == 0
    assert "create" in capsys.readouterr().out



# ── Finale Release-Instanz (#919, Stufe 3) ──────────────────────────────────


def _update_payload(ok: bool = True, **overrides: object) -> dict:
    payload = {
        "schema": 1,
        "kind": "abnahme-update-check",
        "erzeugt_am": "2026-08-30T22:00:00+00:00",
        "kandidaten_version": VERSION,
        "ok": ok,
        "pruefungen": [
            {"rolle": "vorgaenger", "befund": "ok" if ok else "STATUS_UNERWARTET"},
            {"rolle": "kandidat", "befund": "ok"},
        ],
    }
    payload.update(overrides)
    return payload


def _write_update_evidence(root: Path, platform: str, payload: dict, *, attempt: int = 1) -> None:
    target = root / f"abnahme-{platform}-{attempt}" / "update_check"
    target.mkdir(parents=True, exist_ok=True)
    (target / "update_check.json").write_text(json.dumps(payload), encoding="utf-8")


def test_update_check_constants_stay_in_sync_with_the_smoke_writer() -> None:
    """Handgepflegte Kopie gegen ihre Quelle (Drift-Disziplin).

    ``release_contract`` spiegelt Schema, Kind und Dateiname bewusst, statt
    ``abnahme_smoke`` zu importieren - der Vertrag bleibt so von der
    Smoke-Maschinerie unabhaengig. Ohne diesen Waechter bliebe eine
    Schemaanhebung im Schreiber still, und die Auswertung wuerde sie als
    "unbekannte Nutzlast" abweisen statt sie zu lesen.
    """
    smoke_spec = importlib.util.spec_from_file_location(
        "abnahme_smoke_probe", ROOT / "scripts" / "abnahme_smoke.py"
    )
    assert smoke_spec is not None and smoke_spec.loader is not None
    smoke = importlib.util.module_from_spec(smoke_spec)
    sys.modules["abnahme_smoke_probe"] = smoke
    smoke_spec.loader.exec_module(smoke)
    assert rc.UPDATE_CHECK_SCHEMA == smoke.UPDATE_CHECK_SUMMARY_SCHEMA
    assert rc.UPDATE_CHECK_KIND == smoke.UPDATE_CHECK_SUMMARY_KIND
    assert rc.UPDATE_CHECK_SUMMARY_NAME == smoke.UPDATE_CHECK_SUMMARY_NAME
    assert rc.UPDATE_CHECK_CRITERIA["linux-arm64"] == "UPDATE-LINUX-ARM-01"
    assert rc.UPDATE_CHECK_CRITERIA["macos-arm64"] == "UPDATE-MACOS-ARM-01"


def _status(payload: dict | None) -> tuple[str, str]:
    return rc.update_check_status(payload, expected_version=VERSION)


def test_update_status_maps_evidence_to_pass_fail_pending() -> None:
    assert _status(_update_payload(True))[0] == "PASS"
    # FAIL statt WAIVED: Der Fund betrifft alle ausgelieferten Installationen.
    status, detail = _status(_update_payload(False))
    assert status == "FAIL" and "STATUS_UNERWARTET" in detail
    assert _status(None)[0] == "PENDING"


def test_unknown_update_payload_throws_instead_of_looking_like_pending() -> None:
    """Ein Schemabruch darf nicht wie ein nicht gelaufener Nachweis aussehen."""
    with pytest.raises(rc.ContractError, match="Unbekannte Update-Check-Nutzlast"):
        _status(_update_payload(schema=2))
    with pytest.raises(rc.ContractError, match="Unbekannte Update-Check-Nutzlast"):
        _status(_update_payload(kind="etwas-anderes"))
    with pytest.raises(rc.ContractError, match="ok-Feld"):
        _status(_update_payload(ok="ja"))


def test_pass_needs_more_than_the_aggregate_boolean() -> None:
    """`ok: true` allein schliesst kein nicht waiverfaehiges Kriterium ab.

    Eine veraltete oder leere Nutzlast traegt denselben Wahrheitswert wie ein
    echter Nachweis. Weil das Ergebnis direkt ein POST_RELEASE-Kriterium auf
    PASS setzt, wird die Bindung geprueft, die die Nutzlast belegt haben soll.
    """
    # Fremde Kandidatenversion: gehoert zu einem anderen Release.
    with pytest.raises(rc.ContractError, match="gehoert zu Version"):
        _status(_update_payload(True, kandidaten_version="9.9.9"))
    # Leere Pruefungsliste: nichts wurde tatsaechlich geprueft.
    with pytest.raises(rc.ContractError, match="ohne Rollen"):
        _status(_update_payload(True, pruefungen=[]))
    # Nur eine Rolle: der Vorgaengernachweis fehlt.
    with pytest.raises(rc.ContractError, match="ohne Rollen"):
        _status(_update_payload(True, pruefungen=[{"rolle": "kandidat", "befund": "ok"}]))
    with pytest.raises(rc.ContractError, match="ohne Pruefungsliste"):
        _status(_update_payload(True, pruefungen="ok"))
    # Widerspruch in der Evidenz selbst: ok, aber eine Rolle nicht ok.
    with pytest.raises(rc.ContractError, match="meldet ok"):
        _status(_update_payload(True, pruefungen=[
            {"rolle": "kandidat", "befund": "ok"},
            {"rolle": "vorgaenger", "befund": "HOOK_FEHLT"},
        ]))


def test_evidence_loader_picks_the_newest_attempt_per_platform(tmp_path: Path) -> None:
    root = tmp_path / "evidenz"
    _write_update_evidence(root, "linux-arm64", _update_payload(False), attempt=1)
    _write_update_evidence(root, "linux-arm64", _update_payload(True), attempt=2)
    _write_update_evidence(root, "macos-arm64", _update_payload(True), attempt=1)
    payloads = rc.load_update_check_payloads(root)
    assert set(payloads) == {"linux-arm64", "macos-arm64"}
    # Der Versuch bleibt erhalten - das hochgeladene Artefakt heisst
    # abnahme-<plattform>-<versuch>, ein Verweis ohne ihn zeigt ins Leere.
    assert payloads["linux-arm64"] == (2, payloads["linux-arm64"][1])
    assert payloads["linux-arm64"][1]["ok"] is True
    assert rc.load_update_check_payloads(tmp_path / "fehlt") == {}


def _instance_for(tmp_path: Path) -> tuple[dict, dict, Path]:
    """Instanz im Zustand nach dem publish-seitigen Job (Stufe 3a)."""
    manifest, _ = _manifest(tmp_path)
    instance = copy.deepcopy(manifest["release_instance"])
    assert isinstance(instance, dict)
    checklist = rc.load_release_checklist(CHECKLIST)
    for criterion in ("PUBLISH-01", "PUBLISH-02", "PUBLISH-03", "PUBLIC-DOWNLOAD-01"):
        instance = rc.set_release_instance_criterion(
            instance, checklist=checklist, checklist_path=CHECKLIST,
            criterion_id=criterion, status="PASS", evidence=["https://example.invalid/run"],
        )
    return instance, checklist, CHECKLIST


def test_both_platform_criteria_are_filled_from_their_own_evidence(tmp_path: Path) -> None:
    instance, checklist, checklist_path = _instance_for(tmp_path)
    root = tmp_path / "evidenz"
    _write_update_evidence(root, "linux-arm64", _update_payload(True))
    _write_update_evidence(root, "macos-arm64", _update_payload(True))
    updated, log = rc.apply_update_criteria(
        instance, checklist=checklist, checklist_path=checklist_path,
        payloads=rc.load_update_check_payloads(root),
        run_url="https://example.invalid/abnahme",
    )
    states = {item["id"]: item["status"] for item in updated["criteria"]}
    assert states["UPDATE-LINUX-ARM-01"] == "PASS"
    assert states["UPDATE-MACOS-ARM-01"] == "PASS"
    assert len(log) == 2
    # Evidenzverweis nennt das Artefakt so, wie es wirklich heisst.
    evidence = {item["id"]: item["evidence"] for item in updated["criteria"]}
    assert "Artefakt abnahme-linux-arm64-1" in evidence["UPDATE-LINUX-ARM-01"]
    rc.validate_release_instance_completion(
        updated, checklist=checklist, checklist_path=checklist_path,
        through_phase="post-release",
    )


def test_a_platform_without_evidence_stays_pending_and_blocks_completion(
    tmp_path: Path,
) -> None:
    """Kein Mitziehen: Ein Linux-PASS belegt macOS nicht."""
    instance, checklist, checklist_path = _instance_for(tmp_path)
    root = tmp_path / "evidenz"
    _write_update_evidence(root, "linux-arm64", _update_payload(True))
    updated, _ = rc.apply_update_criteria(
        instance, checklist=checklist, checklist_path=checklist_path,
        payloads=rc.load_update_check_payloads(root),
        run_url="https://example.invalid/abnahme",
    )
    states = {item["id"]: item for item in updated["criteria"]}
    assert states["UPDATE-LINUX-ARM-01"]["status"] == "PASS"
    assert states["UPDATE-MACOS-ARM-01"]["status"] == "PENDING"
    # PENDING traegt keine Evidenz - sonst saehe ein nicht erbrachter
    # Nachweis belegt aus.
    assert states["UPDATE-MACOS-ARM-01"]["evidence"] == []
    with pytest.raises(rc.ContractError, match="UPDATE-MACOS-ARM-01"):
        rc.validate_release_instance_completion(
            updated, checklist=checklist, checklist_path=checklist_path,
            through_phase="post-release",
        )


def test_a_failed_update_check_blocks_completion_and_is_never_waived(
    tmp_path: Path,
) -> None:
    instance, checklist, checklist_path = _instance_for(tmp_path)
    root = tmp_path / "evidenz"
    _write_update_evidence(root, "linux-arm64", _update_payload(False))
    _write_update_evidence(root, "macos-arm64", _update_payload(True))
    updated, _ = rc.apply_update_criteria(
        instance, checklist=checklist, checklist_path=checklist_path,
        payloads=rc.load_update_check_payloads(root),
        run_url="https://example.invalid/abnahme",
    )
    states = {item["id"]: item["status"] for item in updated["criteria"]}
    assert states["UPDATE-LINUX-ARM-01"] == "FAIL"
    with pytest.raises(rc.ContractError, match="fehlgeschlagen"):
        rc.validate_release_instance_completion(
            updated, checklist=checklist, checklist_path=checklist_path,
            through_phase="post-release",
        )


def test_instance_download_picks_the_newest_attempt_deterministically(
    tmp_path: Path,
) -> None:
    """Ein wiederholter Publish-Lauf legt mehrere Versuchsartefakte ab.

    Werden sie in ein Verzeichnis entpackt, gewinnt die zuletzt entpackte
    Datei - und die Reihenfolge ist nicht zugesichert. Der Abnahme-Lauf traege
    dann still die Instanz eines ueberholten Versuchs nach. Dieselbe Regel wie
    fuer die Freeze-Provenienz (#760/#761): juengster Versuch, alles
    Mehrdeutige bricht ab.
    """
    root = tmp_path / "publish-instance"
    for attempt, marker in ((1, "alt"), (2, "neu")):
        target = root / f"release-acceptance-instance-{attempt}"
        target.mkdir(parents=True)
        (target / "release-acceptance-instance.json").write_text(
            json.dumps({"marker": marker}), encoding="utf-8"
        )
    selected = rc.select_instance_payload(root)
    assert json.loads(selected.read_text(encoding="utf-8"))["marker"] == "neu"


def test_flat_instance_download_is_accepted_but_never_mixed(tmp_path: Path) -> None:
    """Ein einzelner Treffer wird flach entpackt - das bleibt gueltig."""
    root = tmp_path / "flach"
    root.mkdir()
    payload = root / "release-acceptance-instance.json"
    payload.write_text("{}", encoding="utf-8")
    assert rc.select_instance_payload(root) == payload

    # Flach UND benannt zugleich ist kein deterministisches Layout.
    (root / "release-acceptance-instance-2").mkdir()
    with pytest.raises(rc.ContractError, match="genau eine regulaere Datei"):
        rc.select_instance_payload(root)


def test_instance_download_rejects_unknown_entries_and_missing_payloads(
    tmp_path: Path,
) -> None:
    root = tmp_path / "kaputt"
    (root / "release-acceptance-instance-1").mkdir(parents=True)
    with pytest.raises(rc.ContractError, match="ohne Nutzlast"):
        rc.select_instance_payload(root)

    other = tmp_path / "fremd"
    (other / "irgendwas").mkdir(parents=True)
    with pytest.raises(rc.ContractError, match="Unerwarteter Eintrag"):
        rc.select_instance_payload(other)

    with pytest.raises(rc.ContractError, match="Instanz-Download fehlt"):
        rc.select_instance_payload(tmp_path / "gibt-es-nicht")


def test_finalize_cli_accepts_a_directory_and_selects_the_newest(tmp_path: Path) -> None:
    instance, _, _ = _instance_for(tmp_path)
    root = tmp_path / "publish-instance"
    for attempt in (1, 2):
        target = root / f"release-acceptance-instance-{attempt}"
        target.mkdir(parents=True)
        (target / "release-acceptance-instance.json").write_text(
            json.dumps(instance), encoding="utf-8"
        )
    evidence = tmp_path / "evidenz"
    for platform in ("linux-arm64", "macos-arm64"):
        _write_update_evidence(evidence, platform, _update_payload(True))
    output = tmp_path / "final.json"
    assert rc.main([
        "finalize-instance", "--checklist", str(CHECKLIST),
        "--instance", str(root), "--evidence-dir", str(evidence),
        "--run-url", "https://example.invalid/abnahme", "--output", str(output),
    ]) == 0



def test_finalize_cli_writes_the_instance_even_when_it_blocks(tmp_path: Path) -> None:
    """Die Evidenz eines FAIL darf nicht mit dem FAIL verschwinden."""
    instance, _, _ = _instance_for(tmp_path)
    instance_path = tmp_path / "instance.json"
    instance_path.write_text(json.dumps(instance), encoding="utf-8")
    root = tmp_path / "evidenz"
    _write_update_evidence(root, "linux-arm64", _update_payload(False))
    _write_update_evidence(root, "macos-arm64", _update_payload(True))
    output = tmp_path / "final.json"
    code = rc.main([
        "finalize-instance", "--checklist", str(CHECKLIST),
        "--instance", str(instance_path), "--evidence-dir", str(root),
        "--run-url", "https://example.invalid/abnahme", "--output", str(output),
    ])
    assert code == 2
    written = json.loads(output.read_text(encoding="utf-8"))
    states = {item["id"]: item["status"] for item in written["criteria"]}
    assert states["UPDATE-LINUX-ARM-01"] == "FAIL"
    assert states["UPDATE-MACOS-ARM-01"] == "PASS"


def test_versioned_checklist_has_exact_scope_stable_ids_and_required_fields() -> None:
    checklist = rc.load_release_checklist(CHECKLIST)
    # 2.1.0 (#919): PUBLISH-01 wird von CI gesetzt, nicht mehr vom
    # Release-Owner - Kriteriumssemantik und IDs unveraendert.
    assert checklist["checklist_version"] == "2.1.0"
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


def test_update_criteria_declare_exactly_what_each_platform_proves() -> None:
    """#917: Die Deklaration darf nicht mehr behaupten als der Lauf erbringt.

    Vorher deckte ein gemeinsames ``UPDATE-01`` drei Artefakte ab, während der
    reale Nachweis nur den Linux-arm64-Kanal prüfte.
    """
    checklist = rc.load_release_checklist(CHECKLIST)
    criteria = {str(item["id"]): item for item in checklist["criteria"]}
    assert "UPDATE-01" not in criteria
    linux = criteria["UPDATE-LINUX-ARM-01"]
    macos = criteria["UPDATE-MACOS-ARM-01"]

    assert set(linux["artifacts"]) == {"linux-arm64-appimage", "linux-arm64-deb"}
    assert set(macos["artifacts"]) == {"macos-arm64-dmg"}
    # Kein macOS-Artefakt mehr im Linux-Kriterium und umgekehrt.
    assert not set(linux["artifacts"]) & set(macos["artifacts"])
    # Die .deb-Identitaetsbegruendung steht im Kriteriumstext, nicht nur in
    # der Betriebsdoku.
    assert "byte-identical" in linux["description"].lower()
    # Die macOS-Hook-Grenze ist Teil des Vertrags.
    assert "2.7.3" in macos["description"]
    for item in (linux, macos):
        assert item["phase"] == "post-release"
        assert item["requirement"] == "POST_RELEASE"
        assert item["verification"] == "post-release"
        assert item["waiver_allowed"] is False
        assert item["not_applicable_allowed"] is False


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


def test_a_foreign_file_is_named_but_never_hashed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#925: Ein Lesefehler auf einer Fremddatei darf das Gate nicht entgleisen.

    Ihr Hash ist keine Evidenz ueber den Release; wuerde er trotzdem berechnet,
    ersetzte ein ``OSError`` die klare ``Artefaktmenge weicht ab``-Meldung.
    """
    manifest, files = _manifest(tmp_path)
    (files / "unerwartet.bin").write_bytes(b"nicht im manifest")
    hashed: list[str] = []
    original = rc._sha256_file

    def recording(path: Path) -> str:
        hashed.append(path.name)
        if path.name == "unerwartet.bin":
            raise OSError(5, "Input/output error")
        return str(original(path))

    monkeypatch.setattr(rc, "_sha256_file", recording)
    results = {item["name"]: item for item in rc.compare_artifact_directory(manifest, files)}
    assert results["unerwartet.bin"]["sha256"] is None
    assert results["unerwartet.bin"]["bytes"] == len(b"nicht im manifest")
    assert "unerwartet.bin" not in hashed

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
