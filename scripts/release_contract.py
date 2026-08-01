#!/usr/bin/env python3
"""Fail-closed contract for release candidates, approval, and publishing.

The contract introduced for #744 binds one successful candidate-build run to
one successful hardware-acceptance run and to exactly five files.  Publishing
may only download those files from the recorded build run and must reproduce
their SHA-256 values byte for byte.  No build is performed in this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, cast

MANIFEST_SCHEMA: Final = 1
MANIFEST_KIND: Final = "release-approval-manifest"
POLICY_VERSION: Final = 1
CANDIDATE_SCHEMA: Final = 1
CANDIDATE_KIND: Final = "release-candidate-contract"
BUILD_WORKFLOW: Final = ".github/workflows/release-linux.yml"
ACCEPTANCE_WORKFLOW: Final = ".github/workflows/release-abnahme.yml"
FREEZE_KIND: Final = "release-freeze-provenance"
APPROVED: Final = "approved"
PAUSED: Final = "paused"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_TAG_RE = re.compile(r"^v(\d+\.\d+\.\d+(?:[.-][0-9A-Za-z.]+)?)$")
_FREEZE_ARTIFACT_RE = re.compile(r"^release-freeze-provenance-(\d+)$")
_APPROVAL_ARTIFACT_RE = re.compile(r"^release-approval-manifest-(\d+)$")

ARTIFACT_CONTAINERS: Final = (
    "bgremover-linux-x86_64",
    "bgremover-linux-raspberrypi-arm64",
    "bgremover-macos-arm64",
)
PLATFORM_STATUSES: Final = {
    "macos-arm64": APPROVED,
    "linux-arm64": APPROVED,
    "linux-x86_64": PAUSED,
}


class ContractError(RuntimeError):
    """The supplied release evidence violates the fail-closed contract."""


def _validate_platform_statuses(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ContractError("Plattformstatus fehlen")
    statuses = {str(key): str(status) for key, status in value.items()}
    expected_keys = set(PLATFORM_STATUSES)
    if set(statuses) != expected_keys:
        raise ContractError("Plattformstatus sind unvollstaendig oder enthalten Zusaetze")
    if statuses["macos-arm64"] != APPROVED or statuses["linux-arm64"] != APPROVED:
        raise ContractError("Aktive macOS-/Linux-arm64-Abnahmen muessen approved sein")
    if statuses["linux-x86_64"] not in (APPROVED, PAUSED):
        raise ContractError("Linux x86_64 muss approved oder explizit paused sein")
    return statuses


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"JSON kann nicht gelesen werden: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"JSON-Wurzel muss ein Objekt sein: {path}")
    return cast(dict[str, Any], value)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool):
        raise ContractError(f"{field} muss eine positive Ganzzahl sein")
    try:
        parsed = int(str(value))
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{field} muss eine positive Ganzzahl sein") from exc
    if parsed < 1:
        raise ContractError(f"{field} muss eine positive Ganzzahl sein")
    return parsed


def _full_sha(value: object, field: str) -> str:
    sha = str(value or "").lower()
    if not _SHA_RE.fullmatch(sha):
        raise ContractError(f"{field} muss ein voller 40-stelliger Commit-SHA sein")
    return sha


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _timestamp(value: object, field: str) -> str:
    text = str(value or "")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ContractError(f"{field} muss ein ISO-8601-Zeitstempel sein") from exc
    if parsed.tzinfo is None:
        raise ContractError(f"{field} muss eine Zeitzone enthalten")
    return text


def expected_artifact_names(version: str, *, with_ai: bool) -> tuple[str, ...]:
    suffix = "-ai" if with_ai else ""
    stem = f"BgRemover-{version}"
    return tuple(sorted((
        f"{stem}-linux-x86_64{suffix}.AppImage",
        f"{stem}-linux-x86_64{suffix}.deb",
        f"{stem}-linux-raspberrypi-arm64{suffix}.AppImage",
        f"{stem}-linux-raspberrypi-arm64{suffix}.deb",
        f"{stem}-macos-arm64{suffix}.dmg",
    )))


def platform_for_artifact(name: str) -> str:
    if "-macos-arm64" in name:
        return "macos-arm64"
    if "-linux-raspberrypi-arm64" in name:
        return "linux-arm64"
    if "-linux-x86_64" in name:
        return "linux-x86_64"
    raise ContractError(f"Artefakt ohne bekannte Zielplattform: {name}")


def validate_workflow_run(
    run: dict[str, Any],
    *,
    expected_run_id: int,
    expected_workflow: str,
    expected_head_sha: str | None = None,
) -> dict[str, Any]:
    """Validate immutable GitHub run metadata and return normalized fields."""
    run_id = _integer(run.get("id"), "run.id")
    if run_id != expected_run_id:
        raise ContractError(f"Falsche Run-ID: {run_id}, erwartet {expected_run_id}")
    workflow = str(run.get("path") or "")
    if workflow != expected_workflow:
        raise ContractError(f"Falscher Workflow: {workflow!r}, erwartet {expected_workflow!r}")
    if run.get("event") != "workflow_dispatch":
        raise ContractError("Release-Vertragslaeufe muessen per workflow_dispatch starten")
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise ContractError(
            f"Run {run_id} ist nicht erfolgreich abgeschlossen: "
            f"status={run.get('status')!r}, conclusion={run.get('conclusion')!r}"
        )
    head_sha = _full_sha(run.get("head_sha"), "run.head_sha")
    if expected_head_sha is not None and head_sha != expected_head_sha:
        raise ContractError(
            f"Run {run_id} gehoert zu {head_sha}, erwartet ist {expected_head_sha}"
        )
    return {
        "run_id": run_id,
        "run_attempt": _integer(run.get("run_attempt"), "run.run_attempt"),
        "workflow": workflow,
        "head_sha": head_sha,
    }


def _release_files(directory: Path) -> dict[str, Path]:
    if not directory.is_dir():
        raise ContractError(f"Artefaktverzeichnis fehlt: {directory}")
    files = {path.name: path for path in directory.rglob("*") if path.is_file()}
    if len(files) != len([path for path in directory.rglob("*") if path.is_file()]):
        raise ContractError("Doppelte Dateinamen in den heruntergeladenen Artefakten")
    return files


def _infer_release_set(files: dict[str, Path], version: str) -> tuple[str, ...]:
    actual = tuple(sorted(files))
    for with_ai in (True, False):
        expected = expected_artifact_names(version, with_ai=with_ai)
        if actual == expected:
            return expected
    raise ContractError(
        "Release-Artefaktmenge ist nicht exakt (2 AppImages, 2 DEBs, 1 DMG "
        f"fuer Version {version} erwartet): {list(actual)}"
    )


def _artifact_listing(listing: dict[str, Any]) -> list[dict[str, Any]]:
    raw = listing.get("artifacts")
    if not isinstance(raw, list):
        raise ContractError("Actions-Artefaktliste enthaelt kein Feld 'artifacts'")
    return [cast(dict[str, Any], item) for item in raw if isinstance(item, dict)]


def _artifact_reference(artifact: dict[str, Any]) -> dict[str, Any]:
    digest = str(artifact.get("digest") or "")
    prefix, separator, value = digest.partition(":")
    if separator != ":" or prefix != "sha256" or not _DIGEST_RE.fullmatch(value):
        raise ContractError(f"Actions-Artefakt {artifact.get('name')!r} ohne SHA-256-Digest")
    if artifact.get("expired") is True:
        raise ContractError(f"Actions-Artefakt {artifact.get('name')!r} ist abgelaufen")
    return {
        "name": str(artifact.get("name") or ""),
        "artifact_id": _integer(artifact.get("id"), "artifact.id"),
        "archive_digest": digest,
    }


def _validate_stored_reference(reference: object, *, freeze: bool = False) -> dict[str, Any]:
    if not isinstance(reference, dict):
        raise ContractError("Actions-Artefaktreferenz fehlt")
    data = cast(dict[str, Any], reference)
    name = str(data.get("name") or "")
    if freeze:
        if not _FREEZE_ARTIFACT_RE.fullmatch(name):
            raise ContractError("Freeze-Provenienzreferenz hat einen ungueltigen Namen")
    elif name not in ARTIFACT_CONTAINERS:
        raise ContractError(f"Unbekannter Artefaktcontainer in Referenz: {name!r}")
    _integer(data.get("artifact_id"), f"artifact_id[{name}]")
    digest = str(data.get("archive_digest") or "")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ContractError(f"Ungueltiger Archiv-Digest fuer {name}")
    if freeze and not _DIGEST_RE.fullmatch(str(data.get("payload_sha256") or "")):
        raise ContractError("Freeze-Provenienzreferenz ohne Nutzlast-SHA-256")
    return data


def _validate_freeze(
    provenance: dict[str, Any], *, source: dict[str, Any], version: str
) -> None:
    if provenance.get("schema") != 1 or provenance.get("kind") != FREEZE_KIND:
        raise ContractError("Unbekanntes Freeze-Provenienzschema")
    if provenance.get("candidate_sha") != source["head_sha"]:
        raise ContractError("Freeze-Provenienz ist an einen anderen Kandidaten gebunden")
    release = provenance.get("release")
    if not isinstance(release, dict) or release.get("version") != version:
        raise ContractError("Freeze-Provenienz nennt eine andere Release-Version")
    workflow = provenance.get("workflow")
    if not isinstance(workflow, dict):
        raise ContractError("Freeze-Provenienz ohne Workflow-Metadaten")
    if _integer(workflow.get("run_id"), "freeze.workflow.run_id") != source["run_id"]:
        raise ContractError("Freeze-Provenienz stammt aus einem anderen Build-Run")


def prepare_candidate_contract(
    *,
    run: dict[str, Any],
    listing: dict[str, Any],
    candidate_dir: Path,
    provenance_dir: Path,
    expected_run_id: int,
    output_dir: Path,
) -> dict[str, Any]:
    source = validate_workflow_run(
        run, expected_run_id=expected_run_id, expected_workflow=BUILD_WORKFLOW,
    )
    artifacts = _artifact_listing(listing)
    by_name: dict[str, list[dict[str, Any]]] = {}
    for artifact in artifacts:
        by_name.setdefault(str(artifact.get("name") or ""), []).append(artifact)
    active_containers: dict[str, dict[str, Any]] = {}
    for name in ARTIFACT_CONTAINERS:
        matches = [item for item in by_name.get(name, []) if item.get("expired") is not True]
        if len(matches) != 1:
            raise ContractError(
                f"Build-Run muss genau ein unverfallenes Actions-Artefakt {name!r} enthalten"
            )
        active_containers[name] = matches[0]
    unexpected = sorted(
        name for name in by_name if name.startswith("bgremover-") and name not in ARTIFACT_CONTAINERS
    )
    if unexpected:
        raise ContractError(f"Unerwartete Release-Artefaktcontainer: {unexpected}")

    freeze_candidates: list[tuple[int, dict[str, Any]]] = []
    for name, matches in by_name.items():
        match = _FREEZE_ARTIFACT_RE.fullmatch(name)
        if match:
            freeze_candidates.extend(
                (int(match.group(1)), item)
                for item in matches
                if item.get("expired") is not True
            )
    if not freeze_candidates:
        raise ContractError("Build-Run enthaelt keine Freeze-Provenienz")
    _, freeze_artifact = max(freeze_candidates, key=lambda item: item[0])
    freeze_reference = _artifact_reference(freeze_artifact)
    freeze_path = provenance_dir / freeze_reference["name"] / "release-freeze-provenance.json"
    provenance = _load_json(freeze_path)

    release = provenance.get("release")
    version = str(release.get("version") or "") if isinstance(release, dict) else ""
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[.-][0-9A-Za-z.]+)?", version):
        raise ContractError(f"Ungueltige Release-Version in der Freeze-Provenienz: {version!r}")
    _validate_freeze(provenance, source=source, version=version)

    files = _release_files(candidate_dir)
    names = _infer_release_set(files, version)
    records = [
        {
            "name": name,
            "sha256": _sha256_file(files[name]),
            "bytes": files[name].stat().st_size,
            "platform": platform_for_artifact(name),
        }
        for name in names
    ]
    contract = {
        "schema": CANDIDATE_SCHEMA,
        "kind": CANDIDATE_KIND,
        "policy_version": POLICY_VERSION,
        "candidate": {
            **source,
            "version": version,
            "expected_tag": f"v{version}",
            "artifact_containers": [
                _artifact_reference(active_containers[name]) for name in ARTIFACT_CONTAINERS
            ],
            "freeze_provenance": {
                **freeze_reference,
                "payload_sha256": _sha256_file(freeze_path),
            },
        },
        "artifacts": records,
        "generated_at": _utc_now(),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "release-candidate-contract.json", contract)
    shutil.copy2(freeze_path, output_dir / "release-freeze-provenance.json")
    return contract


def _validate_candidate_contract(contract: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if (
        contract.get("schema") != CANDIDATE_SCHEMA
        or contract.get("kind") != CANDIDATE_KIND
        or contract.get("policy_version") != POLICY_VERSION
    ):
        raise ContractError("Unbekannter Kandidatenvertrag")
    candidate = contract.get("candidate")
    if not isinstance(candidate, dict):
        raise ContractError("Kandidatenvertrag ohne candidate")
    _integer(candidate.get("run_id"), "candidate.run_id")
    _integer(candidate.get("run_attempt"), "candidate.run_attempt")
    if candidate.get("workflow") != BUILD_WORKFLOW:
        raise ContractError("Kandidatenvertrag nennt den falschen Workflow")
    _full_sha(candidate.get("head_sha"), "candidate.head_sha")
    version = str(candidate.get("version") or "")
    tag_match = _TAG_RE.fullmatch(str(candidate.get("expected_tag") or ""))
    if not tag_match or tag_match.group(1) != version:
        raise ContractError("Kandidatenvertrag hat inkonsistente Version/Tag-Angaben")
    containers = candidate.get("artifact_containers")
    if not isinstance(containers, list) or len(containers) != len(ARTIFACT_CONTAINERS):
        raise ContractError("Kandidatenvertrag ohne exakte Artefaktcontainer-Referenzen")
    container_refs = [_validate_stored_reference(item) for item in containers]
    if {item["name"] for item in container_refs} != set(ARTIFACT_CONTAINERS):
        raise ContractError("Kandidatenvertrag hat unvollstaendige Artefaktcontainer")
    _validate_stored_reference(candidate.get("freeze_provenance"), freeze=True)
    records_raw = contract.get("artifacts")
    if not isinstance(records_raw, list) or not all(isinstance(item, dict) for item in records_raw):
        raise ContractError("Kandidatenvertrag ohne Artefaktliste")
    records = cast(list[dict[str, Any]], records_raw)
    names = tuple(sorted(str(item.get("name") or "") for item in records))
    if names not in (
        expected_artifact_names(version, with_ai=True),
        expected_artifact_names(version, with_ai=False),
    ):
        raise ContractError("Kandidatenvertrag nennt nicht exakt die fuenf Release-Dateien")
    if len(set(names)) != 5:
        raise ContractError("Kandidatenvertrag enthaelt doppelte Dateinamen")
    for record in records:
        if not _DIGEST_RE.fullmatch(str(record.get("sha256") or "")):
            raise ContractError(f"Ungueltiger SHA-256 fuer {record.get('name')!r}")
        _integer(record.get("bytes"), f"bytes[{record.get('name')!r}]")
        if record.get("platform") != platform_for_artifact(str(record.get("name") or "")):
            raise ContractError(f"Falsche Plattform fuer {record.get('name')!r}")
    _timestamp(contract.get("generated_at"), "candidate.generated_at")
    return cast(dict[str, Any], candidate), records


def _load_platform_evidence(root: Path) -> dict[str, dict[str, Any]]:
    selected: dict[str, tuple[int, dict[str, Any]]] = {}
    for path in root.rglob("evidenz.json"):
        data = _load_json(path)
        platform = str(data.get("platform") or "")
        attempt = 0
        pattern = re.compile(rf"^abnahme-{re.escape(platform)}-(\d+)$")
        for part in reversed(path.parts):
            match = pattern.fullmatch(part)
            if match:
                attempt = int(match.group(1))
                break
        if platform not in selected or attempt >= selected[platform][0]:
            selected[platform] = (attempt, data)
    return {platform: item[1] for platform, item in selected.items()}


def create_approval_manifest(
    *,
    candidate_contract: dict[str, Any],
    evidence_dir: Path,
    acceptance_summary: dict[str, Any],
    acceptance_run_id: int,
    acceptance_run_attempt: int,
    acceptance_head_sha: str,
    approval_artifact_name: str,
) -> dict[str, Any]:
    candidate, records = _validate_candidate_contract(candidate_contract)
    acceptance_run_id = _integer(acceptance_run_id, "acceptance.run_id")
    acceptance_run_attempt = _integer(
        acceptance_run_attempt, "acceptance.run_attempt",
    )
    artifact_match = _APPROVAL_ARTIFACT_RE.fullmatch(approval_artifact_name)
    if not artifact_match or int(artifact_match.group(1)) != acceptance_run_attempt:
        raise ContractError("Freigabemanifest-Name und Abnahme-Attempt stimmen nicht ueberein")
    acceptance_head_sha = _full_sha(acceptance_head_sha, "acceptance.head_sha")
    if acceptance_head_sha != candidate["head_sha"]:
        raise ContractError(
            "Abnahme-Workflow und Kandidaten-Build muessen auf exakt demselben Commit laufen"
        )
    if (
        acceptance_summary.get("schema") != 1
        or acceptance_summary.get("kind") != "release-acceptance-summary"
    ):
        raise ContractError("Unbekanntes oder fehlendes Abschlussmatrix-Schema")
    if acceptance_summary.get("commit_sha") != candidate["head_sha"]:
        raise ContractError("Abschlussmatrix gehoert zu einem anderen Commit")
    _timestamp(acceptance_summary.get("generated_at"), "acceptance_summary.generated_at")
    if acceptance_summary.get("blocking") is not False:
        raise ContractError("Abschlussmatrix enthaelt blockierende Luecken")
    statuses = _validate_platform_statuses(acceptance_summary.get("platforms"))

    expected_by_platform: dict[str, dict[str, dict[str, Any]]] = {}
    for record in records:
        expected_by_platform.setdefault(str(record["platform"]), {})[str(record["name"])] = record
    evidences = _load_platform_evidence(evidence_dir)
    expected_evidence_platforms = {
        platform for platform, status in statuses.items() if status != PAUSED
    }
    if set(evidences) != expected_evidence_platforms:
        raise ContractError(
            "Hardware-Evidenzmenge ist nicht exakt: "
            f"erwartet={sorted(expected_evidence_platforms)}, vorhanden={sorted(evidences)}"
        )
    for platform, status in statuses.items():
        if status == PAUSED:
            if platform in evidences:
                raise ContractError(f"Pausierte Plattform {platform} darf keine Freigabe-Evidenz tragen")
            continue
        evidence = evidences.get(platform)
        if evidence is None:
            raise ContractError(f"Abnahme-Evidenz fuer {platform} fehlt")
        if evidence.get("status") != "bestanden":
            raise ContractError(f"Abnahme fuer {platform} ist nicht bestanden")
        if evidence.get("commit_sha") != candidate["head_sha"]:
            raise ContractError(f"Abnahme fuer {platform} gehoert zu einem anderen Commit")
        source = evidence.get("quelle")
        if not isinstance(source, dict) or source != {
            "art": "run-id", "wert": str(candidate["run_id"]),
        }:
            raise ContractError(f"Abnahme fuer {platform} stammt aus dem falschen Build-Run")
        raw_artifacts = evidence.get("artefakte")
        if not isinstance(raw_artifacts, list):
            raise ContractError(f"Ungueltige Artefaktevidenz fuer {platform}")
        actual: dict[str, tuple[str, int]] = {}
        for item in raw_artifacts:
            if not isinstance(item, dict):
                raise ContractError(f"Ungueltige Artefaktevidenz fuer {platform}")
            item_name = str(item.get("name") or "")
            if item_name in actual:
                raise ContractError(f"Doppelte Artefaktevidenz fuer {item_name}")
            actual[item_name] = (
                str(item.get("sha256") or ""),
                _integer(item.get("bytes"), f"evidence.bytes[{platform}]"),
            )
        expected = {
            name: (str(item["sha256"]), int(item["bytes"]))
            for name, item in expected_by_platform[platform].items()
        }
        if actual != expected:
            raise ContractError(f"Abnahme-Hashes fuer {platform} weichen vom Kandidaten ab")

    manifest_records = [
        {**record, "acceptance_status": statuses[str(record["platform"])]}
        for record in records
    ]
    return {
        "schema": MANIFEST_SCHEMA,
        "kind": MANIFEST_KIND,
        "policy_version": POLICY_VERSION,
        "candidate": candidate,
        "acceptance": {
            "run_id": acceptance_run_id,
            "run_attempt": acceptance_run_attempt,
            "workflow": ACCEPTANCE_WORKFLOW,
            "head_sha": acceptance_head_sha,
            "approval_artifact_name": approval_artifact_name,
            "platforms": statuses,
        },
        "artifacts": manifest_records,
        "generated_at": _utc_now(),
        # Keep the manifest-level reference structurally independent from the
        # embedded candidate contract.  They must compare equal during
        # validation, but changing either copy must be detected as tampering.
        "provenance_reference": dict(
            cast(dict[str, Any], candidate["freeze_provenance"]),
        ),
    }


def validate_approval_manifest(
    manifest: dict[str, Any],
    *,
    expected_tag: str,
    expected_candidate_run_id: int,
    expected_acceptance_run_id: int,
    expected_approval_artifact_name: str,
    candidate_run: dict[str, Any] | None = None,
    acceptance_run: dict[str, Any] | None = None,
    tag_sha: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if (
        manifest.get("schema") != MANIFEST_SCHEMA
        or manifest.get("kind") != MANIFEST_KIND
        or manifest.get("policy_version") != POLICY_VERSION
    ):
        raise ContractError("Unbekanntes oder fehlendes Freigabemanifest-Schema")
    _timestamp(manifest.get("generated_at"), "manifest.generated_at")
    candidate = manifest.get("candidate")
    acceptance = manifest.get("acceptance")
    records = manifest.get("artifacts")
    if not isinstance(candidate, dict) or not isinstance(acceptance, dict):
        raise ContractError("Freigabemanifest ohne Kandidat oder Abnahme")
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise ContractError("Freigabemanifest ohne Artefaktliste")
    candidate = cast(dict[str, Any], candidate)
    acceptance = cast(dict[str, Any], acceptance)
    records = cast(list[dict[str, Any]], records)

    run_id = _integer(candidate.get("run_id"), "candidate.run_id")
    if run_id != expected_candidate_run_id:
        raise ContractError("Manifest ist an einen anderen Kandidaten-Run gebunden")
    if candidate.get("workflow") != BUILD_WORKFLOW:
        raise ContractError("Manifest nennt den falschen Build-Workflow")
    _integer(candidate.get("run_attempt"), "candidate.run_attempt")
    head_sha = _full_sha(candidate.get("head_sha"), "candidate.head_sha")
    version = str(candidate.get("version") or "")
    tag_match = _TAG_RE.fullmatch(expected_tag)
    if not tag_match or tag_match.group(1) != version or candidate.get("expected_tag") != expected_tag:
        raise ContractError("Tag und Manifest-Version stimmen nicht ueberein")

    acceptance_id = _integer(acceptance.get("run_id"), "acceptance.run_id")
    if acceptance_id != expected_acceptance_run_id:
        raise ContractError("Manifest ist an einen anderen Abnahme-Run gebunden")
    if acceptance.get("workflow") != ACCEPTANCE_WORKFLOW:
        raise ContractError("Manifest nennt den falschen Abnahme-Workflow")
    acceptance_attempt = _integer(acceptance.get("run_attempt"), "acceptance.run_attempt")
    if acceptance.get("head_sha") != head_sha:
        raise ContractError("Abnahme und Kandidat haben unterschiedliche Commit-SHAs")
    if acceptance.get("approval_artifact_name") != expected_approval_artifact_name:
        raise ContractError("Falsche Referenz auf das Freigabemanifest-Artefakt")
    artifact_match = _APPROVAL_ARTIFACT_RE.fullmatch(expected_approval_artifact_name)
    if not artifact_match or int(artifact_match.group(1)) != acceptance_attempt:
        raise ContractError("Freigabemanifest-Name und Abnahme-Attempt stimmen nicht ueberein")
    statuses = _validate_platform_statuses(acceptance.get("platforms"))
    containers = candidate.get("artifact_containers")
    if not isinstance(containers, list) or len(containers) != len(ARTIFACT_CONTAINERS):
        raise ContractError("Manifest ohne exakte Artefaktcontainer-Referenzen")
    container_refs = [_validate_stored_reference(item) for item in containers]
    if {item["name"] for item in container_refs} != set(ARTIFACT_CONTAINERS):
        raise ContractError("Manifest hat unvollstaendige Artefaktcontainer")
    _validate_stored_reference(candidate.get("freeze_provenance"), freeze=True)
    if manifest.get("provenance_reference") != candidate.get("freeze_provenance"):
        raise ContractError("Freeze-Provenienzreferenz ist inkonsistent")

    names = tuple(sorted(str(item.get("name") or "") for item in records))
    if names not in (
        expected_artifact_names(version, with_ai=True),
        expected_artifact_names(version, with_ai=False),
    ):
        raise ContractError("Manifest nennt nicht exakt die fuenf Release-Dateien")
    for item in records:
        name = str(item.get("name") or "")
        platform = platform_for_artifact(name)
        if item.get("platform") != platform:
            raise ContractError(f"Falsche Plattform fuer {name}")
        if item.get("acceptance_status") != statuses[platform]:
            raise ContractError(f"Falscher Abnahmestatus fuer {name}")
        if not _DIGEST_RE.fullmatch(str(item.get("sha256") or "")):
            raise ContractError(f"Ungueltiger SHA-256 fuer {name}")
        _integer(item.get("bytes"), f"bytes[{name}]")

    if candidate_run is not None:
        normalized_candidate_run = validate_workflow_run(
            candidate_run,
            expected_run_id=expected_candidate_run_id,
            expected_workflow=BUILD_WORKFLOW,
            expected_head_sha=head_sha,
        )
        if normalized_candidate_run["run_attempt"] != _integer(
            candidate.get("run_attempt"), "candidate.run_attempt"
        ):
            raise ContractError("Kandidaten-Run-Attempt weicht vom Manifest ab")
    if acceptance_run is not None:
        normalized_acceptance_run = validate_workflow_run(
            acceptance_run,
            expected_run_id=expected_acceptance_run_id,
            expected_workflow=ACCEPTANCE_WORKFLOW,
            expected_head_sha=head_sha,
        )
        if normalized_acceptance_run["run_attempt"] != _integer(
            acceptance.get("run_attempt"), "acceptance.run_attempt"
        ):
            raise ContractError("Abnahme-Run-Attempt weicht vom Manifest ab")
    if tag_sha is not None and _full_sha(tag_sha, "tag_sha") != head_sha:
        raise ContractError("Tag zeigt nicht auf den abgenommenen Kandidaten-Commit")
    return candidate, records


def verify_artifact_directory(manifest: dict[str, Any], directory: Path) -> None:
    """Require exact filename, size, and SHA-256 equality with the manifest."""
    records_raw = manifest.get("artifacts")
    if not isinstance(records_raw, list) or not all(isinstance(item, dict) for item in records_raw):
        raise ContractError("Manifest ohne gueltige Artefaktliste")
    records = cast(list[dict[str, Any]], records_raw)
    expected = {str(item["name"]): item for item in records}
    actual = _release_files(directory)
    if set(actual) != set(expected):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise ContractError(f"Artefaktmenge weicht ab: fehlend={missing}, zusaetzlich={extra}")
    for name, path in actual.items():
        record = expected[name]
        if path.stat().st_size != int(record["bytes"]):
            raise ContractError(f"Dateigroesse weicht ab: {name}")
        digest = _sha256_file(path)
        if digest != record["sha256"]:
            raise ContractError(f"SHA-256 weicht ab: {name}")


def plan_publish(
    manifest: dict[str, Any], *, exists: bool, is_draft: bool, existing_dir: Path
) -> str:
    """Return a safe idempotent action; partial/divergent states always block."""
    if not exists:
        return "create-draft-upload"
    files = _release_files(existing_dir)
    if not files:
        if not is_draft:
            raise ContractError("Veroeffentlichtes Release ohne Assets: Owner-Entscheidung noetig")
        return "upload-to-draft"
    try:
        verify_artifact_directory(manifest, existing_dir)
    except ContractError as exc:
        state = "teilweise" if len(files) < 5 else "abweichend"
        raise ContractError(
            f"Bestehendes Release ist {state}; keine automatische Aenderung. "
            "Owner muss den Draft/die Assets bewusst bereinigen oder einen neuen Tag waehlen. "
            f"Details: {exc}"
        ) from exc
    return "publish-existing-draft" if is_draft else "already-complete"


def _write_github_outputs(values: dict[str, object]) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    with Path(output).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare-candidate")
    prepare.add_argument("--run-json", type=Path, required=True)
    prepare.add_argument("--artifacts-json", type=Path, required=True)
    prepare.add_argument("--candidate-dir", type=Path, required=True)
    prepare.add_argument("--provenance-dir", type=Path, required=True)
    prepare.add_argument("--run-id", type=int, required=True)
    prepare.add_argument("--output-dir", type=Path, required=True)

    create = commands.add_parser("create-approval")
    create.add_argument("--candidate-contract", type=Path, required=True)
    create.add_argument("--evidence-dir", type=Path, required=True)
    create.add_argument("--acceptance-summary", type=Path, required=True)
    create.add_argument("--acceptance-run-id", type=int, required=True)
    create.add_argument("--acceptance-run-attempt", type=int, required=True)
    create.add_argument("--acceptance-head-sha", required=True)
    create.add_argument("--approval-artifact-name", required=True)
    create.add_argument("--output", type=Path, required=True)

    verify = commands.add_parser("verify-approval")
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--candidate-run-json", type=Path, required=True)
    verify.add_argument("--acceptance-run-json", type=Path, required=True)
    verify.add_argument("--candidate-run-id", type=int, required=True)
    verify.add_argument("--acceptance-run-id", type=int, required=True)
    verify.add_argument("--approval-artifact-name", required=True)
    verify.add_argument("--tag", required=True)
    verify.add_argument("--tag-sha")

    artifacts = commands.add_parser("verify-artifacts")
    artifacts.add_argument("--manifest", type=Path, required=True)
    artifacts.add_argument("--directory", type=Path, required=True)

    plan = commands.add_parser("plan-publish")
    plan.add_argument("--manifest", type=Path, required=True)
    plan.add_argument("--state", type=Path, required=True)
    plan.add_argument("--existing-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "prepare-candidate":
            contract = prepare_candidate_contract(
                run=_load_json(args.run_json),
                listing=_load_json(args.artifacts_json),
                candidate_dir=args.candidate_dir,
                provenance_dir=args.provenance_dir,
                expected_run_id=args.run_id,
                output_dir=args.output_dir,
            )
            candidate = cast(dict[str, Any], contract["candidate"])
            _write_github_outputs({
                "head_sha": candidate["head_sha"],
                "version": candidate["version"],
                "expected_tag": candidate["expected_tag"],
            })
        elif args.command == "create-approval":
            manifest = create_approval_manifest(
                candidate_contract=_load_json(args.candidate_contract),
                evidence_dir=args.evidence_dir,
                acceptance_summary=_load_json(args.acceptance_summary),
                acceptance_run_id=args.acceptance_run_id,
                acceptance_run_attempt=args.acceptance_run_attempt,
                acceptance_head_sha=args.acceptance_head_sha,
                approval_artifact_name=args.approval_artifact_name,
            )
            _write_json(args.output, manifest)
        elif args.command == "verify-approval":
            candidate, _ = validate_approval_manifest(
                _load_json(args.manifest),
                expected_tag=args.tag,
                expected_candidate_run_id=args.candidate_run_id,
                expected_acceptance_run_id=args.acceptance_run_id,
                expected_approval_artifact_name=args.approval_artifact_name,
                candidate_run=_load_json(args.candidate_run_json),
                acceptance_run=_load_json(args.acceptance_run_json),
                tag_sha=args.tag_sha,
            )
            _write_github_outputs({
                "candidate_sha": candidate["head_sha"],
                "version": candidate["version"],
            })
        elif args.command == "verify-artifacts":
            verify_artifact_directory(_load_json(args.manifest), args.directory)
        else:
            state = _load_json(args.state)
            action = plan_publish(
                _load_json(args.manifest),
                exists=state.get("exists") is True,
                is_draft=state.get("is_draft") is True,
                existing_dir=args.existing_dir,
            )
            print(action)
            _write_github_outputs({"action": action})
    except ContractError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
