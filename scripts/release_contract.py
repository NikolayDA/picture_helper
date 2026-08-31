#!/usr/bin/env python3
"""Fail-closed contract for release candidates, approval, and publishing.

The contract introduced for #744 binds one successful candidate-build run to
one successful hardware-acceptance run and to exactly five files.  Publishing
may only download those files from the recorded build run and must reproduce
their SHA-256 values byte for byte.  No build is performed in this module.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, cast

MANIFEST_SCHEMA: Final = 2
MANIFEST_KIND: Final = "release-approval-manifest"
POLICY_VERSION: Final = 2
CANDIDATE_SCHEMA: Final = 1
CANDIDATE_KIND: Final = "release-candidate-contract"
CHECKLIST_SCHEMA: Final = 1
CHECKLIST_KIND: Final = "release-acceptance-checklist"
CHECKLIST_INSTANCE_SCHEMA: Final = 1
CHECKLIST_INSTANCE_KIND: Final = "release-acceptance-instance"
CHECKLIST_PATH: Final = "docs/RELEASE_ACCEPTANCE_CHECKLIST.md"
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
_CHECKLIST_ID_RE = re.compile(r"^[A-Z][A-Z0-9-]+-[0-9]{2}$")
_CHECKLIST_TABLE_ROW_RE = re.compile(
    r"(?m)^\|\s*`(?P<id>[A-Z][A-Z0-9-]+-[0-9]{2})`\s*"
    r"\|\s*(?P<phase>[^|]+?)\s*"
    r"\|\s*(?P<requirement>[^|]+?)\s*"
    r"\|\s*(?P<owner>[^|]+?)\s*\|"
)
_SEMVER_RE = re.compile(r"^[1-9][0-9]*\.[0-9]+\.[0-9]+$")
#: Namensschema des unveraenderlichen Release-Refs (#918). Ein Branch, damit
#: Ruleset/Branch-Protection ihn gegen Force-Push und Nachschub schuetzen
#: koennen - Tags tragen diesen Schutz nicht in gleicher Form.
RELEASE_REF_PREFIX: Final = "release/"
#: Bewusst dieselbe Versionsregel wie ueberall sonst im Vertrag: Der Ref wird
#: aus RELEASE_TAG = "v${RELEASE_VERSION}" gebildet, zwei Versionsschemata in
#: einer Datei waeren der Anfang genau der Drift, die dieses Repo festnagelt.
_RELEASE_REF_RE = re.compile(
    rf"^{RELEASE_REF_PREFIX}v(?:{_SEMVER_RE.pattern.strip('^$')})$"
)
#: Schutzoperationen, die der Release-Ref tragen muss (#918). ``update``
#: verhindert **jede** Bewegung des Refs und damit auch nachgeschobene Commits,
#: ``non_fast_forward`` den Force-Push, ``deletion`` das Loeschen. Zusammen
#: ergeben sie die Unveraenderlichkeit, auf der die ganze Entscheidung ruht -
#: ohne sie waere der Ref nur eine Verabredung.
REQUIRED_REF_RULES: Final = ("deletion", "non_fast_forward", "update")

CHECKLIST_STATES: Final = ("PASS", "FAIL", "WAIVED", "NOT_APPLICABLE", "PENDING")
CHECKLIST_PHASES: Final = ("pre-release", "publish", "post-release")
CHECKLIST_REQUIREMENTS: Final = ("MUST", "SHOULD", "POST_RELEASE")
CHECKLIST_ARTIFACTS: Final = (
    "linux-x86_64-appimage",
    "linux-x86_64-deb",
    "linux-arm64-appimage",
    "linux-arm64-deb",
    "macos-arm64-dmg",
)

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


def _load_json_array(path: Path) -> list[Any]:
    """Wie :func:`_load_json`, aber fuer Endpunkte mit Listen-Wurzel.

    ``rules/branches/<ref>`` antwortet mit einem Array; eine eigene Funktion
    ist ehrlicher als ein aufgeweichtes ``_load_json``, das dann ueberall
    ``dict | list`` zurueckgaebe.
    """
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"JSON kann nicht gelesen werden: {path}: {exc}") from exc
    if not isinstance(value, list):
        raise ContractError(f"JSON-Wurzel muss eine Liste sein: {path}")
    return cast(list[Any], value)


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


def load_release_checklist(path: Path) -> dict[str, Any]:
    """Load and validate the single machine-readable block in the checklist."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractError(f"Release-Checkliste kann nicht gelesen werden: {path}: {exc}") from exc
    marker = "<!-- release-checklist-json:start -->"
    end_marker = "<!-- release-checklist-json:end -->"
    if text.count(marker) != 1 or text.count(end_marker) != 1:
        raise ContractError("Release-Checkliste braucht genau einen JSON-Vertragsblock")
    marker_index = text.find(marker)
    end_marker_index = text.find(end_marker, marker_index + len(marker))
    if marker_index < 0 or end_marker_index < 0:
        raise ContractError("Release-Checkliste ohne eindeutigen JSON-Vertragsblock")
    fence_index = text.find("```json", marker_index, end_marker_index)
    if fence_index < 0:
        raise ContractError("Release-Checkliste ohne json-Codeblock")
    json_start = text.find("\n", fence_index) + 1
    json_end = text.find("\n```", json_start, end_marker_index)
    if json_start < 1 or json_end < 0:
        raise ContractError("Release-Checklisten-JSON ist nicht korrekt eingefasst")
    try:
        raw = json.loads(text[json_start:json_end])
    except json.JSONDecodeError as exc:
        raise ContractError(f"Release-Checklisten-JSON ist ungueltig: {exc}") from exc
    if not isinstance(raw, dict):
        raise ContractError("Release-Checklisten-JSON muss ein Objekt sein")
    checklist = cast(dict[str, Any], raw)
    validate_release_checklist(checklist)

    table_rows = [
        match.groupdict() for match in _CHECKLIST_TABLE_ROW_RE.finditer(text[:marker_index])
    ]
    table_ids = [row["id"] for row in table_rows]
    if len(table_ids) != len(set(table_ids)):
        raise ContractError("Kriteriums-IDs in der Tabelle sind nicht eindeutig")
    table_by_id = {row["id"]: row for row in table_rows}
    criteria = cast(list[dict[str, Any]], checklist["criteria"])
    contract_ids = {str(item["id"]) for item in criteria}
    if set(table_ids) != contract_ids:
        raise ContractError(
            "Kriteriums-IDs in Tabelle und JSON driften: "
            f"nur_tabelle={sorted(set(table_ids) - contract_ids)}, "
            f"nur_json={sorted(contract_ids - set(table_ids))}"
        )
    owner_aliases = {"hardware-abnahme": "hardware-acceptance"}
    for item in criteria:
        criterion_id = str(item["id"])
        row = table_by_id[criterion_id]
        table_values = {
            "phase": row["phase"].strip().casefold(),
            "requirement": row["requirement"].strip().upper(),
            "owner": owner_aliases.get(
                row["owner"].strip().casefold(), row["owner"].strip().casefold()
            ),
        }
        for field, table_value in table_values.items():
            contract_value = str(item[field]).strip()
            if field != "requirement":
                contract_value = contract_value.casefold()
            if table_value != contract_value:
                raise ContractError(
                    f"Kriterium {criterion_id}: Tabellenfeld {field} driftet vom JSON "
                    f"({table_value!r} != {contract_value!r})"
                )
    return checklist


def validate_release_checklist(checklist: dict[str, Any]) -> None:
    """Validate checklist schema, stable IDs, artifact scope, and gate mapping."""
    if checklist.get("schema") != CHECKLIST_SCHEMA or checklist.get("kind") != CHECKLIST_KIND:
        raise ContractError("Unbekanntes Release-Checklisten-Schema")
    if not _SEMVER_RE.fullmatch(str(checklist.get("checklist_version") or "")):
        raise ContractError("Release-Checkliste ohne gueltige semantische Version")
    if tuple(checklist.get("allowed_states") or ()) != CHECKLIST_STATES:
        raise ContractError("Release-Checkliste hat unerwartete Zustaende")
    if tuple(checklist.get("phases") or ()) != CHECKLIST_PHASES:
        raise ContractError("Release-Checkliste hat unerwartete Phasen")
    if tuple(checklist.get("requirements") or ()) != CHECKLIST_REQUIREMENTS:
        raise ContractError("Release-Checkliste hat unerwartete Pflichtgrade")

    artifacts_raw = checklist.get("artifacts")
    if not isinstance(artifacts_raw, list) or not all(
        isinstance(item, dict) for item in artifacts_raw
    ):
        raise ContractError("Release-Checkliste ohne Artefaktdefinitionen")
    artifacts = cast(list[dict[str, Any]], artifacts_raw)
    artifact_ids = tuple(str(item.get("id") or "") for item in artifacts)
    if artifact_ids != CHECKLIST_ARTIFACTS or len(set(artifact_ids)) != len(artifact_ids):
        raise ContractError("Release-Checkliste muss exakt die fuenf Produktartefakte definieren")
    if any("windows" in str(item.get("platform") or "").lower() for item in artifacts):
        raise ContractError("Windows ist nicht Teil des Releasevertrags")

    criteria_raw = checklist.get("criteria")
    if not isinstance(criteria_raw, list) or not all(
        isinstance(item, dict) for item in criteria_raw
    ):
        raise ContractError("Release-Checkliste ohne Kriterien")
    criteria = cast(list[dict[str, Any]], criteria_raw)
    ids = [str(item.get("id") or "") for item in criteria]
    if len(ids) != len(set(ids)) or not ids or not all(_CHECKLIST_ID_RE.fullmatch(i) for i in ids):
        raise ContractError("Release-Checkliste hat fehlende, doppelte oder ungueltige stabile IDs")

    artifact_set = set(CHECKLIST_ARTIFACTS)
    verification_values = {
        "candidate-contract",
        "active-platforms",
        "manual",
        "publish",
        "post-release",
        "platform:linux-x86_64",
        "platform:linux-arm64",
        "platform:macos-arm64",
    }
    for item in criteria:
        criterion_id = str(item["id"])
        if item.get("phase") not in CHECKLIST_PHASES:
            raise ContractError(f"Ungueltige Phase fuer {criterion_id}")
        if item.get("requirement") not in CHECKLIST_REQUIREMENTS:
            raise ContractError(f"Ungueltiger Pflichtgrad fuer {criterion_id}")
        for field in ("owner", "evidence_source", "description"):
            if not str(item.get(field) or "").strip():
                raise ContractError(f"Pflichtfeld {field} fehlt fuer {criterion_id}")
        criterion_artifacts = item.get("artifacts")
        if not isinstance(criterion_artifacts, list) or len(criterion_artifacts) != len(
            set(str(value) for value in criterion_artifacts)
        ):
            raise ContractError(f"Ungueltige Artefaktliste fuer {criterion_id}")
        unknown = set(str(value) for value in criterion_artifacts) - artifact_set
        if unknown:
            raise ContractError(f"Unbekannte Artefakte fuer {criterion_id}: {sorted(unknown)}")
        verification = str(item.get("verification") or "")
        if verification not in verification_values:
            raise ContractError(f"Unbekannte Evidenzabbildung fuer {criterion_id}")
        if (
            item.get("phase") == "pre-release"
            and item.get("requirement") == "MUST"
            and verification == "manual"
        ):
            raise ContractError(f"Pre-Release-MUST {criterion_id} darf nicht nur manuell bleiben")
        if item.get("requirement") == "POST_RELEASE" and item.get("phase") != "post-release":
            raise ContractError(f"POST_RELEASE-Kriterium {criterion_id} hat die falsche Phase")
        if not isinstance(item.get("waiver_allowed"), bool) or not isinstance(
            item.get("not_applicable_allowed"), bool
        ):
            raise ContractError(f"Waiver-/N/A-Regel fehlt fuer {criterion_id}")

    directly_covered = {
        str(item["artifacts"][0])
        for item in criteria
        if isinstance(item.get("artifacts"), list) and len(item["artifacts"]) == 1
    }
    if directly_covered != artifact_set:
        raise ContractError("Nicht alle fuenf Artefakte besitzen ein getrenntes Kriterium")


def _checklist_reference(
    path: Path,
    checklist: dict[str, Any],
    *,
    commit_sha: str,
) -> dict[str, Any]:
    if not path.as_posix().endswith(CHECKLIST_PATH):
        raise ContractError(f"Release-Checkliste muss unter {CHECKLIST_PATH} liegen")
    return {
        "schema": CHECKLIST_SCHEMA,
        "checklist_version": checklist["checklist_version"],
        "path": CHECKLIST_PATH,
        "commit_sha": _full_sha(commit_sha, "checklist.commit_sha"),
        "sha256": _sha256_file(path),
    }


def _automatic_criterion_record(
    definition: dict[str, Any],
    *,
    candidate: dict[str, Any],
    statuses: dict[str, str],
    acceptance_run_id: int,
) -> dict[str, Any]:
    verification = str(definition["verification"])
    evidence: list[str] = []
    if verification == "candidate-contract":
        status = "PASS"
        evidence = [
            f"github-actions-run:{candidate['run_id']}",
            "release-candidate-contract.json",
        ]
    elif verification.startswith("platform:"):
        platform = verification.partition(":")[2]
        platform_status = statuses[platform]
        status = (
            "PASS"
            if platform_status == APPROVED
            else ("FAIL" if platform_status == "blocked" else "PENDING")
        )
        if status != "PENDING":
            evidence = [f"github-actions-run:{acceptance_run_id}", f"platform:{platform}"]
    elif verification == "active-platforms":
        active = (statuses["linux-arm64"], statuses["macos-arm64"])
        status = "PASS" if all(value == APPROVED for value in active) else "FAIL"
        evidence = [f"github-actions-run:{acceptance_run_id}", "active-platforms"]
    else:
        status = "PENDING"
    return {
        "id": definition["id"],
        "phase": definition["phase"],
        "requirement": definition["requirement"],
        "status": status,
        "evidence": evidence,
        "waiver": None,
    }


def build_release_instance(
    *,
    checklist: dict[str, Any],
    checklist_path: Path,
    candidate: dict[str, Any],
    statuses: dict[str, str],
    acceptance_run_id: int,
) -> dict[str, Any]:
    """Create the pinned per-release criterion ledger stored in the manifest."""
    criteria = cast(list[dict[str, Any]], checklist["criteria"])
    instance = {
        "schema": CHECKLIST_INSTANCE_SCHEMA,
        "kind": CHECKLIST_INSTANCE_KIND,
        "release_version": candidate["version"],
        "candidate_sha": candidate["head_sha"],
        "checklist": _checklist_reference(
            checklist_path,
            checklist,
            commit_sha=str(candidate["head_sha"]),
        ),
        "criteria": [
            _automatic_criterion_record(
                item,
                candidate=candidate,
                statuses=statuses,
                acceptance_run_id=acceptance_run_id,
            )
            for item in criteria
        ],
        "generated_at": _utc_now(),
    }
    validate_release_instance(instance, checklist=checklist, checklist_path=checklist_path)
    validate_release_instance_completion(
        instance,
        checklist=checklist,
        checklist_path=checklist_path,
        through_phase="pre-release",
    )
    return instance


def validate_release_instance(
    instance: dict[str, Any],
    *,
    checklist: dict[str, Any] | None = None,
    checklist_path: Path | None = None,
) -> None:
    if (
        instance.get("schema") != CHECKLIST_INSTANCE_SCHEMA
        or instance.get("kind") != CHECKLIST_INSTANCE_KIND
    ):
        raise ContractError("Unbekanntes Release-Instanz-Schema")
    _full_sha(instance.get("candidate_sha"), "release_instance.candidate_sha")
    if not re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+(?:[.-][0-9A-Za-z.]+)?",
        str(instance.get("release_version") or ""),
    ):
        raise ContractError("Release-Instanz ohne gueltige Version")
    _timestamp(instance.get("generated_at"), "release_instance.generated_at")
    reference = instance.get("checklist")
    if not isinstance(reference, dict):
        raise ContractError("Release-Instanz ohne Checklisten-Pin")
    reference = cast(dict[str, Any], reference)
    if reference.get("schema") != CHECKLIST_SCHEMA or reference.get("path") != CHECKLIST_PATH:
        raise ContractError("Release-Instanz hat einen ungueltigen Checklisten-Pfad")
    if reference.get("commit_sha") != instance.get("candidate_sha"):
        raise ContractError("Checklisten-Pin und Release-Instanz haben verschiedene Commits")
    if not _SEMVER_RE.fullmatch(str(reference.get("checklist_version") or "")):
        raise ContractError("Release-Instanz ohne Checklisten-Version")
    if not _DIGEST_RE.fullmatch(str(reference.get("sha256") or "")):
        raise ContractError("Release-Instanz ohne Checklisten-SHA-256")

    criteria_raw = instance.get("criteria")
    if not isinstance(criteria_raw, list) or not all(
        isinstance(item, dict) for item in criteria_raw
    ):
        raise ContractError("Release-Instanz ohne Kriteriumsstaende")
    records = cast(list[dict[str, Any]], criteria_raw)
    record_ids = [str(item.get("id") or "") for item in records]
    if len(record_ids) != len(set(record_ids)) or not all(
        _CHECKLIST_ID_RE.fullmatch(item) for item in record_ids
    ):
        raise ContractError("Release-Instanz hat doppelte oder ungueltige Kriteriums-IDs")

    definitions: dict[str, dict[str, Any]] = {}
    if checklist is not None:
        validate_release_checklist(checklist)
        definitions = {
            str(item["id"]): item for item in cast(list[dict[str, Any]], checklist["criteria"])
        }
        if set(record_ids) != set(definitions):
            raise ContractError("Release-Instanz bildet nicht exakt alle Checklisten-IDs ab")
        if reference.get("checklist_version") != checklist.get("checklist_version"):
            raise ContractError("Release-Instanz pinnt eine andere Checklisten-Version")
    if checklist_path is not None and _sha256_file(checklist_path) != reference.get("sha256"):
        raise ContractError("Release-Instanz pinnt einen anderen Checklisten-Dateihash")

    for record in records:
        criterion_id = str(record["id"])
        status = str(record.get("status") or "")
        if record.get("phase") not in CHECKLIST_PHASES:
            raise ContractError(f"Ungueltige Phase in Release-Instanz: {criterion_id}")
        if record.get("requirement") not in CHECKLIST_REQUIREMENTS:
            raise ContractError(f"Ungueltiger Pflichtgrad in Release-Instanz: {criterion_id}")
        if status not in CHECKLIST_STATES:
            raise ContractError(f"Ungueltiger Status in Release-Instanz: {criterion_id}")
        evidence = record.get("evidence")
        if not isinstance(evidence, list) or not all(
            isinstance(item, str) and item.strip() for item in evidence
        ):
            raise ContractError(f"Ungueltige Evidenzliste fuer {criterion_id}")
        if status in ("PASS", "FAIL", "WAIVED", "NOT_APPLICABLE") and not evidence:
            raise ContractError(f"{status} ohne Evidenz fuer {criterion_id}")
        waiver = record.get("waiver")
        definition = definitions.get(criterion_id)
        if definition is not None:
            if record.get("phase") != definition.get("phase") or record.get(
                "requirement"
            ) != definition.get("requirement"):
                raise ContractError(f"Release-Instanz veraendert die Semantik von {criterion_id}")
            if status == "NOT_APPLICABLE" and definition.get("not_applicable_allowed") is not True:
                raise ContractError(f"NOT_APPLICABLE ist fuer {criterion_id} nicht erlaubt")
            if status == "WAIVED" and definition.get("waiver_allowed") is not True:
                raise ContractError(f"Waiver ist fuer {criterion_id} nicht erlaubt")
        if status == "WAIVED":
            if not isinstance(waiver, dict):
                raise ContractError(f"Waiver-Daten fehlen fuer {criterion_id}")
            waiver_data = cast(dict[str, Any], waiver)
            waiver_evidence = waiver_data.get("evidence")
            if (
                not str(waiver_data.get("owner") or "").strip()
                or not str(waiver_data.get("reason") or "").strip()
                or not isinstance(waiver_evidence, list)
                or not waiver_evidence
                or not all(isinstance(item, str) and item.strip() for item in waiver_evidence)
            ):
                raise ContractError(f"Waiver fuer {criterion_id} ist unvollstaendig")
        elif waiver is not None:
            raise ContractError(f"Waiver-Daten ohne WAIVED-Status fuer {criterion_id}")


def validate_release_instance_completion(
    instance: dict[str, Any],
    *,
    checklist: dict[str, Any],
    checklist_path: Path,
    through_phase: str,
) -> None:
    validate_release_instance(instance, checklist=checklist, checklist_path=checklist_path)
    if through_phase not in CHECKLIST_PHASES:
        raise ContractError(f"Unbekannte Abschlussphase: {through_phase}")
    last_phase = CHECKLIST_PHASES.index(through_phase)
    for record in cast(list[dict[str, Any]], instance["criteria"]):
        if CHECKLIST_PHASES.index(str(record["phase"])) > last_phase:
            continue
        requirement = str(record["requirement"])
        status = str(record["status"])
        if status == "FAIL":
            raise ContractError(f"Kriterium {record['id']} ist fehlgeschlagen")
        if requirement == "MUST" and status not in ("PASS", "WAIVED"):
            raise ContractError(
                f"Pflichtkriterium {record['id']} ist nicht abgeschlossen: {status}"
            )
        if requirement == "POST_RELEASE" and status != "PASS":
            raise ContractError(f"Post-Release-Kriterium {record['id']} ist nicht abgeschlossen")


def set_release_instance_criterion(
    instance: dict[str, Any],
    *,
    checklist: dict[str, Any],
    checklist_path: Path,
    criterion_id: str,
    status: str,
    evidence: list[str],
    waiver_owner: str = "",
    waiver_reason: str = "",
) -> dict[str, Any]:
    updated = copy.deepcopy(instance)
    records = cast(list[dict[str, Any]], updated.get("criteria") or [])
    matches = [item for item in records if item.get("id") == criterion_id]
    if len(matches) != 1:
        raise ContractError(f"Kriterium {criterion_id} fehlt oder ist doppelt")
    record = matches[0]
    record["status"] = status
    record["evidence"] = evidence
    record["waiver"] = (
        {"owner": waiver_owner, "reason": waiver_reason, "evidence": evidence}
        if status == "WAIVED"
        else None
    )
    updated["generated_at"] = _utc_now()
    validate_release_instance(updated, checklist=checklist, checklist_path=checklist_path)
    return updated


def expected_artifact_names(version: str, *, with_ai: bool) -> tuple[str, ...]:
    suffix = "-ai" if with_ai else ""
    stem = f"BgRemover-{version}"
    return tuple(
        sorted(
            (
                f"{stem}-linux-x86_64{suffix}.AppImage",
                f"{stem}-linux-x86_64{suffix}.deb",
                f"{stem}-linux-raspberrypi-arm64{suffix}.AppImage",
                f"{stem}-linux-raspberrypi-arm64{suffix}.deb",
                f"{stem}-macos-arm64{suffix}.dmg",
            )
        )
    )


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
        raise ContractError(f"Run {run_id} gehoert zu {head_sha}, erwartet ist {expected_head_sha}")
    return {
        "run_id": run_id,
        "run_attempt": _integer(run.get("run_attempt"), "run.run_attempt"),
        "workflow": workflow,
        "head_sha": head_sha,
    }


def validate_release_ref(
    payload: dict[str, Any], *, expected_ref: str, expected_sha: str
) -> str:
    """Prueft eine ``git/ref``-Antwort gegen Ref-Namen und Kandidaten-SHA (#918).

    Der Release laeuft seit #918 auf einem unveraenderlichen
    ``release/vX.Y.Z``-Branch statt auf ``main``; ``main`` bleibt waehrenddessen
    mergebar. Die Beweiskette traegt weiterhin der SHA, nicht der Ref-Name -
    diese Pruefung ist die *vorgelagerte* Kontrolle, damit ein verwechselter
    oder nachtraeglich bewegter Ref auffaellt, **bevor** ein Dispatch laeuft,
    statt erst im ``candidate-source``-Gate der Abnahme.

    Bewusst netzfrei: Der Aufrufer reicht die Antwort von
    ``gh api repos/OWNER/REPO/git/ref/heads/release/vX.Y.Z`` als JSON herein -
    dasselbe Muster wie bei den Run-Metadaten in ``verify-approval``. Damit ist
    die Regel testbar, ohne GitHub zu befragen.

    Liefert den bestaetigten SHA; jede Abweichung wirft.
    """
    if not _RELEASE_REF_RE.fullmatch(expected_ref):
        raise ContractError(
            f"Release-Ref muss dem Schema {RELEASE_REF_PREFIX}vX.Y.Z entsprechen: {expected_ref!r}"
        )
    expected_sha = _full_sha(expected_sha, "release_ref.expected_sha")
    actual_ref = str(payload.get("ref") or "")
    if actual_ref != f"refs/heads/{expected_ref}":
        raise ContractError(
            f"Ref-Antwort gehoert zu {actual_ref!r}, erwartet refs/heads/{expected_ref}"
        )
    obj = payload.get("object")
    if not isinstance(obj, dict):
        raise ContractError(f"Ref {expected_ref} ohne Objektangabe")
    target = cast(dict[str, Any], obj)
    # Ein annotiertes Tag-Objekt zeigt nur mittelbar auf den Commit; die
    # Gleichheitspruefung waere dann gegen den Tag-SHA statt gegen den Commit.
    if target.get("type") != "commit":
        raise ContractError(
            f"Ref {expected_ref} zeigt auf {target.get('type')!r} statt auf einen Commit"
        )
    actual_sha = _full_sha(target.get("sha"), "release_ref.object.sha")
    if actual_sha != expected_sha:
        raise ContractError(
            f"Ref {expected_ref} zeigt auf {actual_sha}, erwartet ist {expected_sha} - "
            "Kandidat verwerfen oder Ref korrigieren, nicht dispatchen."
        )
    return actual_sha


def validate_ref_protection(
    payload: Any, *, expected_ref: str, required: tuple[str, ...] = REQUIRED_REF_RULES
) -> tuple[str, ...]:
    """Prueft die **aktiven** Schutzregeln eines Release-Refs (#918).

    Der Ref traegt die Unveraenderlichkeit dieser Entscheidung; ohne Ruleset
    ist er nur eine Verabredung. Bis #933 gab das Runbook die Regeltypen
    lediglich aus und ueberliess die Bewertung dem Augenschein - eine leere
    Liste sah damit aus wie eine bestandene Pruefung. Diese Funktion ist die
    fail-closed Fassung derselben Kontrolle: Sie laeuft vor dem ersten
    Dispatch und wirft, statt zu berichten.

    Der Aufrufer reicht die Antwort von
    ``gh api repos/OWNER/REPO/rules/branches/release/vX.Y.Z`` als JSON herein -
    netzfrei wie der Rest des Vertrags. Der Endpunkt liefert laut
    GitHub-Referenz ausschliesslich die *aktiven* Regeln des konkreten Refs;
    ein Ruleset in ``evaluate`` oder ``disabled`` erscheint dort nicht.
    Vorhandensein bedeutet hier also tatsaechlich "greift".

    Liefert die gefundenen Regeltypen sortiert; jede Luecke wirft.
    """
    if not _RELEASE_REF_RE.fullmatch(expected_ref):
        raise ContractError(
            f"Release-Ref muss dem Schema {RELEASE_REF_PREFIX}vX.Y.Z entsprechen: {expected_ref!r}"
        )
    if not isinstance(payload, list):
        raise ContractError(
            f"Regelantwort fuer {expected_ref} ist keine Liste, sondern {type(payload).__name__}"
        )
    found: set[str] = set()
    for index, entry in enumerate(cast(list[Any], payload)):
        if not isinstance(entry, dict):
            raise ContractError(f"Regeleintrag {index} von {expected_ref} ist kein Objekt")
        rule_type = cast(dict[str, Any], entry).get("type")
        if not isinstance(rule_type, str) or not rule_type:
            raise ContractError(f"Regeleintrag {index} von {expected_ref} ohne 'type'")
        found.add(rule_type)
    missing = tuple(sorted(set(required) - found))
    if missing:
        # Die leere Liste ist der haeufigste und gefaehrlichste Fall: Das
        # Ruleset wurde nie angelegt, der Ref ist voellig ungeschuetzt.
        state = "keine aktive Regel" if not found else f"aktiv: {', '.join(sorted(found))}"
        raise ContractError(
            f"Release-Ref {expected_ref} ist nicht ausreichend geschuetzt ({state}); "
            f"es fehlen: {', '.join(missing)}. Ruleset fuer {RELEASE_REF_PREFIX}* in Ordnung "
            "bringen, nicht dispatchen."
        )
    return tuple(sorted(found))


#: Ergebnisse von :func:`plan_release_tag`. Ein dritter Zustand ist bewusst
#: nicht vorgesehen: Ein abweichender Tag wirft, statt einen "fix"-Plan zu
#: liefern - ein Tag wird nie verschoben (Runbook, Rollback-Abschnitt).
TAG_PLAN_CREATE: Final = "create"
TAG_PLAN_ALREADY_CORRECT: Final = "already-correct"


def resolve_tag_commit(
    ref_payload: dict[str, Any], *, tag: str, tag_object_payload: dict[str, Any] | None = None
) -> str:
    """Loest eine ``git/ref/tags``-Antwort auf den Commit auf, auf den sie zeigt.

    Ein **annotiertes** Tag zeigt im Ref auf ein Tag-*Objekt*, nicht auf den
    Commit; erst dessen ``object.sha`` ist der Commit. Genau diese Verwechslung
    wuerde eine SHA-Gleichheitspruefung still gegen den falschen Wert fuehren -
    dieselbe Falle, die :func:`validate_release_ref` fuer Branch-Refs abfaengt.
    Der Aufrufer reicht deshalb bei ``type == "tag"`` zusaetzlich die Antwort von
    ``gh api repos/OWNER/REPO/git/tags/<sha>`` herein; netzfrei wie ueberall in
    diesem Vertrag.
    """
    actual_ref = str(ref_payload.get("ref") or "")
    if actual_ref != f"refs/tags/{tag}":
        raise ContractError(
            f"Tag-Antwort gehoert zu {actual_ref!r}, erwartet refs/tags/{tag}"
        )
    obj = ref_payload.get("object")
    if not isinstance(obj, dict):
        raise ContractError(f"Tag {tag} ohne Objektangabe")
    target = cast(dict[str, Any], obj)
    kind = target.get("type")
    if kind == "commit":
        return _full_sha(target.get("sha"), "tag.object.sha")
    if kind != "tag":
        raise ContractError(f"Tag {tag} zeigt auf {kind!r} statt auf Commit oder Tag-Objekt")
    if tag_object_payload is None:
        raise ContractError(
            f"Tag {tag} ist annotiert; zur Aufloesung fehlt die git/tags-Antwort"
        )
    tag_object_sha = _full_sha(target.get("sha"), "tag.object.sha")
    if _full_sha(tag_object_payload.get("sha"), "tag_object.sha") != tag_object_sha:
        raise ContractError(f"Tag-Objekt-Antwort gehoert nicht zu {tag}")
    inner = tag_object_payload.get("object")
    if not isinstance(inner, dict):
        raise ContractError(f"Tag-Objekt {tag} ohne Zielangabe")
    pointed = cast(dict[str, Any], inner)
    if pointed.get("type") != "commit":
        raise ContractError(
            f"Tag-Objekt {tag} zeigt auf {pointed.get('type')!r} statt auf einen Commit"
        )
    return _full_sha(pointed.get("sha"), "tag_object.object.sha")


def select_tag_ref(matching_refs: object, *, tag: str) -> dict[str, Any] | None:
    """Waehlt aus einer ``git/matching-refs``-Antwort genau ``refs/tags/<tag>``.

    Der Endpunkt sucht per **Praefix**: laut GitHub-Referenz werden zu
    ``tags/v2.9.0`` auch ``v2.9.0-rc1`` und ``v2.9.0.1`` geliefert ("If the
    ``:ref`` doesn't exist in the repository, but existing refs start with
    ``:ref``, they will be returned as an array"). Ohne exakte Auswahl haette
    ein Vorabtag den Anschein erweckt, der Release-Tag existiere bereits.

    Genau deshalb wird die Liste hier gefiltert statt im Shell: ``[]`` heisst
    "Tag fehlt" und ist damit vom Fehlerfall unterscheidbar, ohne 404 aus
    stderr zu lesen.
    """
    if not isinstance(matching_refs, list):
        raise ContractError("matching-refs-Antwort ist keine Liste")
    wanted = f"refs/tags/{tag}"
    hits = [
        cast(dict[str, Any], item)
        for item in cast(list[Any], matching_refs)
        if isinstance(item, dict) and item.get("ref") == wanted
    ]
    if len(hits) > 1:
        raise ContractError(f"matching-refs liefert {wanted} mehrfach")
    return hits[0] if hits else None


def plan_release_tag(
    manifest: dict[str, Any],
    *,
    tag: str,
    ref_payload: dict[str, Any] | None,
    tag_object_payload: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Entscheidet netzfrei, ob der Release-Tag angelegt werden darf (#919).

    ``ref_payload is None`` heisst "Tag existiert nicht" - beim Aufrufer die
    leere Auswahl aus :func:`select_tag_ref`. Bewusst **kein** 404-Pfad: Der
    Endpunkt ``git/matching-refs`` antwortet immer mit HTTP 200 und einer
    (ggf. leeren) Liste. Sollwert ist ausschliesslich ``candidate.head_sha``
    aus dem Freigabemanifest - nie der aktuelle Checkout, nie ein
    Eingabewert.

    Drei Ausgaenge, davon einer fail-closed:

    * Tag fehlt        -> ``create``
    * Tag zeigt richtig -> ``already-correct`` (Wiederanlauf ist idempotent)
    * Tag zeigt anders  -> ``ContractError``

    Ein abweichender Tag wird bewusst **nicht** repariert: Sobald ein Release
    oder ein externer Download existiert, waere jedes Verschieben ein Bruch der
    bereits veroeffentlichten Zuordnung. Der Runbook-Weg ist dann eine neue
    Patch-Version, keine Tag-Korrektur.
    """
    candidate = manifest.get("candidate")
    if not isinstance(candidate, dict):
        raise ContractError("Manifest ohne Kandidatenblock")
    expected_sha = _full_sha(
        cast(dict[str, Any], candidate).get("head_sha"), "candidate.head_sha"
    )
    expected_tag = str(cast(dict[str, Any], candidate).get("expected_tag") or "")
    if tag != expected_tag:
        raise ContractError(
            f"Tag {tag!r} weicht vom Manifest-Tag {expected_tag!r} ab"
        )
    if ref_payload is None:
        return TAG_PLAN_CREATE, expected_sha
    actual_sha = resolve_tag_commit(
        ref_payload, tag=tag, tag_object_payload=tag_object_payload
    )
    if actual_sha != expected_sha:
        raise ContractError(
            f"Tag {tag} zeigt auf {actual_sha}, das Manifest bindet {expected_sha}. "
            "Tag wird nicht verschoben - Ursache klaeren oder neue Patch-Version."
        )
    return TAG_PLAN_ALREADY_CORRECT, expected_sha


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


def _validate_freeze(provenance: dict[str, Any], *, source: dict[str, Any], version: str) -> None:
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


def _freeze_payload_path(
    provenance_dir: Path,
    artifact_name: str,
    downloaded_artifact_names: set[str],
) -> Path:
    """Resolve the two layouts emitted by ``download-artifact`` fail-closed.

    A pattern matching one artifact is extracted directly into ``path`` by
    actions/download-artifact@v8. Multiple matches retain one directory per
    artifact. The candidate contract accepts both deterministic layouts,
    validates every downloaded attempt, and returns only the selected attempt.
    """

    if artifact_name not in downloaded_artifact_names:
        raise ContractError("Ausgewaehlte Freeze-Provenienz fehlt in der Artefaktliste")
    if not provenance_dir.is_dir():
        raise ContractError("Freeze-Provenienzdownload fehlt")

    entries = sorted(provenance_dir.iterdir())
    if any(entry.is_symlink() for entry in entries):
        raise ContractError("Freeze-Provenienzdownload enthaelt einen symbolischen Link")

    expected_name = "release-freeze-provenance.json"
    flat_payload = provenance_dir / expected_name
    if flat_payload in entries:
        if (
            len(downloaded_artifact_names) != 1
            or entries != [flat_payload]
            or not flat_payload.is_file()
        ):
            raise ContractError(
                "Flacher Freeze-Provenienzdownload muss genau eine regulaere Datei "
                "fuer genau einen Versuch enthalten"
            )
        return flat_payload

    expected_directories = {
        provenance_dir / name for name in downloaded_artifact_names
    }
    if set(entries) != expected_directories or any(
        not directory.is_dir() for directory in expected_directories
    ):
        raise ContractError(
            "Benannter Freeze-Provenienzdownload stimmt nicht mit der "
            "Artefaktliste ueberein"
        )

    for directory in expected_directories:
        payload = directory / expected_name
        attempt_entries = sorted(directory.iterdir())
        if (
            any(entry.is_symlink() for entry in attempt_entries)
            or attempt_entries != [payload]
            or not payload.is_file()
        ):
            raise ContractError(
                f"Freeze-Provenienzartefakt {directory.name!r} muss genau "
                "eine regulaere Payload enthalten"
            )
    return provenance_dir / artifact_name / expected_name


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
        run,
        expected_run_id=expected_run_id,
        expected_workflow=BUILD_WORKFLOW,
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
        name
        for name in by_name
        if name.startswith("bgremover-") and name not in ARTIFACT_CONTAINERS
    )
    if unexpected:
        raise ContractError(f"Unerwartete Release-Artefaktcontainer: {unexpected}")

    freeze_candidates: list[tuple[int, dict[str, Any]]] = []
    for name, matches in by_name.items():
        match = _FREEZE_ARTIFACT_RE.fullmatch(name)
        if match:
            freeze_candidates.extend(
                (int(match.group(1)), item) for item in matches if item.get("expired") is not True
            )
    if not freeze_candidates:
        raise ContractError("Build-Run enthaelt keine Freeze-Provenienz")
    freeze_attempts = [attempt for attempt, _ in freeze_candidates]
    if len(freeze_attempts) != len(set(freeze_attempts)):
        raise ContractError("Build-Run enthaelt mehrdeutige Freeze-Provenienzversuche")
    _, freeze_artifact = max(freeze_candidates, key=lambda item: item[0])
    freeze_reference = _artifact_reference(freeze_artifact)
    freeze_path = _freeze_payload_path(
        provenance_dir,
        freeze_reference["name"],
        {str(item.get("name") or "") for _, item in freeze_candidates},
    )
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


def _validate_candidate_contract(
    contract: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
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


#: Post-Release-Kriterium je Plattform (#917). Die Zuordnung ist die einzige
#: Quelle: Ein Lauf ohne macOS-Evidenz laesst UPDATE-MACOS-ARM-01 PENDING,
#: statt es aus dem Linux-Ergebnis mitzuziehen.
UPDATE_CHECK_CRITERIA: Final = {
    "linux-arm64": "UPDATE-LINUX-ARM-01",
    "macos-arm64": "UPDATE-MACOS-ARM-01",
}
#: Nutzlast, die ``abnahme_smoke`` je Plattform schreibt. Bewusst hier
#: gespiegelt statt importiert: Dieser Vertrag bleibt von der Smoke-Maschinerie
#: unabhaengig. ``tests/test_release_contract.py`` haelt beide Seiten synchron
#: (Drift-Disziplin wie bei der Qt-apt-Paketliste).
UPDATE_CHECK_SCHEMA: Final = 1
UPDATE_CHECK_KIND: Final = "abnahme-update-check"
UPDATE_CHECK_SUMMARY_NAME: Final = "update_check.json"
#: Beide Rollen muessen in der Nutzlast stehen; eine leere oder halbe
#: Pruefungsliste ist kein bestandener Nachweis.
UPDATE_CHECK_ROLES: Final = ("kandidat", "vorgaenger")
UPDATE_CHECK_VERDICT_OK: Final = "ok"


def load_update_check_payloads(root: Path) -> dict[str, tuple[int, dict[str, Any]]]:
    """Sammelt ``update_check/update_check.json`` je Plattform aus der Evidenz.

    Attempt-Auswahl wie in :func:`_load_platform_evidence`: Bei einem
    Wiederanlauf liegt dieselbe Plattform mehrfach im Artefaktbaum, und nur der
    juengste Versuch beschreibt den geltenden Stand.

    Der Versuch wird **mitgeliefert**, nicht verworfen: Hochgeladen wird
    ``abnahme-<plattform>-<versuch>``, ein Evidenzverweis ohne Versuchsnummer
    zeigte also auf ein Artefakt, das es so nie gibt.
    """
    selected: dict[str, tuple[int, dict[str, Any]]] = {}
    if not root.is_dir():
        return {}
    for path in root.rglob(f"update_check/{UPDATE_CHECK_SUMMARY_NAME}"):
        for platform in UPDATE_CHECK_CRITERIA:
            pattern = re.compile(rf"^abnahme-{re.escape(platform)}-(\d+)$")
            attempts = [
                int(match.group(1))
                for part in path.parts
                if (match := pattern.fullmatch(part)) is not None
            ]
            if not attempts:
                continue
            attempt = max(attempts)
            if platform not in selected or attempt >= selected[platform][0]:
                selected[platform] = (attempt, _load_json(path))
            break
    return selected


#: Name des Instanz-Artefakts, das der Publish-Lauf je Versuch hochlaedt.
_INSTANCE_ARTIFACT_RE: Final = re.compile(r"^release-acceptance-instance-([1-9][0-9]*)$")
INSTANCE_PAYLOAD_NAME: Final = "release-acceptance-instance.json"


def select_instance_payload(root: Path) -> Path:
    """Waehlt aus dem Instanz-Download deterministisch den juengsten Versuch.

    Ein wiederholter Publish-Lauf legt in **einem** Lauf mehrere Artefakte ab
    (``…-instance-1``, ``…-instance-2``), jedes mit derselben Datei an seiner
    Wurzel. Ohne Auswahl gaebe es zwei Wege in den Fehler: ``merge-multiple``
    entpackt beide in dasselbe Verzeichnis, wobei die zuletzt entpackte Datei
    gewinnt (Reihenfolge nicht zugesichert), oder das Verzeichnis enthaelt
    mehrere Kandidaten und irgendeiner wird genommen. Der Abnahme-Lauf traege
    dann die Instanz eines ueberholten Versuchs nach - still, im genau dem
    Artefakt, das anschliessend die Post-Release-Kriterien traegt.

    Dieselbe Regel wie fuer die Freeze-Provenienz (#760/#761): der juengste
    Versuch gewinnt, alles Mehrdeutige bricht ab.
    """
    if not root.is_dir():
        raise ContractError(f"Instanz-Download fehlt: {root}")
    entries = sorted(root.iterdir())
    if any(entry.is_symlink() for entry in entries):
        raise ContractError("Instanz-Download enthaelt einen symbolischen Link")

    # Flaches Layout: genau ein Artefakt, Datei direkt in der Wurzel.
    flat = root / INSTANCE_PAYLOAD_NAME
    if flat in entries:
        if entries != [flat] or not flat.is_file():
            raise ContractError(
                "Flacher Instanz-Download muss genau eine regulaere Datei enthalten"
            )
        return flat

    # Benanntes Layout: je Artefakt ein Verzeichnis mit der Versuchsnummer.
    attempts: list[tuple[int, Path]] = []
    for entry in entries:
        match = _INSTANCE_ARTIFACT_RE.fullmatch(entry.name)
        if match is None or not entry.is_dir():
            raise ContractError(f"Unerwarteter Eintrag im Instanz-Download: {entry.name!r}")
        payload = entry / INSTANCE_PAYLOAD_NAME
        if not payload.is_file():
            raise ContractError(f"Instanz-Artefakt {entry.name!r} ohne Nutzlast")
        attempts.append((int(match.group(1)), payload))
    if not attempts:
        raise ContractError("Instanz-Download enthaelt keine Release-Instanz")
    numbers = [attempt for attempt, _ in attempts]
    if len(numbers) != len(set(numbers)):
        raise ContractError("Instanz-Download enthaelt mehrdeutige Versuchsnummern")
    return max(attempts, key=lambda item: item[0])[1]


def update_check_status(
    payload: dict[str, Any] | None, *, expected_version: str
) -> tuple[str, str]:
    """Bildet eine Update-Check-Nutzlast auf Kriteriumsstatus und Begruendung ab.

    Drei Ausgaenge, keiner davon geschoent:

    * keine Evidenz -> ``PENDING`` (der Lauf hat den Nachweis nicht erbracht)
    * ``ok: true`` **und** vollstaendige, passende Nutzlast -> ``PASS``
    * ``ok: false`` -> ``FAIL``

    ``FAIL`` ist Absicht: Ein fehlgeschlagener Update-Check betrifft alle
    bereits ausgelieferten Installationen und wird laut Runbook nie auf
    ``WAIVED`` gesetzt.

    Der Wahrheitswert allein traegt das ``PASS`` bewusst **nicht**. Er
    schliesst ein nicht waiverfaehiges Post-Release-Kriterium ab, also wird
    die Nutzlast gegen die Bindung geprueft, die sie belegt haben soll:
    Schema und Art, die Kandidatenversion gegen die Release-Instanz und die
    Anwesenheit **beider** Rollen mit eigenem ``ok``-Befund. Sonst schloesse
    eine veraltete oder leere Nutzlast (fremde Version, ``pruefungen: []``)
    den Release ab, ohne je etwas geprueft zu haben. Jede Abweichung wirft,
    statt als ``PENDING`` durchzugehen - ein Schemabruch darf nicht wie ein
    nicht gelaufener Nachweis aussehen.
    """
    if payload is None:
        return "PENDING", "keine Update-Check-Evidenz in diesem Lauf"
    if payload.get("schema") != UPDATE_CHECK_SCHEMA or payload.get("kind") != UPDATE_CHECK_KIND:
        raise ContractError(
            "Unbekannte Update-Check-Nutzlast: "
            f"schema={payload.get('schema')!r} kind={payload.get('kind')!r}"
        )
    ok = payload.get("ok")
    if not isinstance(ok, bool):
        raise ContractError("Update-Check-Nutzlast ohne belastbares ok-Feld")
    reported_version = str(payload.get("kandidaten_version") or "")
    if reported_version != expected_version:
        raise ContractError(
            f"Update-Check-Evidenz gehoert zu Version {reported_version!r}, "
            f"die Release-Instanz zu {expected_version!r}"
        )
    checks = payload.get("pruefungen")
    if not isinstance(checks, list):
        raise ContractError("Update-Check-Nutzlast ohne Pruefungsliste")
    by_role = {
        str(item.get("rolle") or ""): item
        for item in cast(list[Any], checks)
        if isinstance(item, dict)
    }
    missing = sorted(set(UPDATE_CHECK_ROLES) - set(by_role))
    if missing:
        raise ContractError(f"Update-Check-Evidenz ohne Rollen {missing}")
    findings = ", ".join(
        f"{role}={by_role[role].get('befund')}" for role in sorted(by_role)
    )
    if not ok:
        return "FAIL", findings
    unclear = sorted(
        role for role in UPDATE_CHECK_ROLES
        if by_role[role].get("befund") != UPDATE_CHECK_VERDICT_OK
    )
    if unclear:
        # ok:true bei nicht-ok Rollen ist ein Widerspruch in der Evidenz
        # selbst - er darf nie zum PASS werden.
        raise ContractError(
            f"Update-Check meldet ok, aber die Rollen {unclear} sind nicht ok: {findings}"
        )
    return "PASS", findings


def apply_update_criteria(
    instance: dict[str, Any],
    *,
    checklist: dict[str, Any],
    checklist_path: Path,
    payloads: dict[str, tuple[int, dict[str, Any]]],
    run_url: str,
) -> tuple[dict[str, Any], list[str]]:
    """Traegt beide Post-Release-Kriterien in die Instanz ein (#919, Stufe 3).

    Liefert die aktualisierte Instanz und je Kriterium eine Protokollzeile.
    Die Validierung bleibt bewusst beim Aufrufer: Erst wird die Instanz
    geschrieben, dann geprueft - sonst verloere ein ``FAIL`` genau die Evidenz,
    die ihn belegt.
    """
    updated = instance
    log: list[str] = []
    expected_version = str(instance.get("release_version") or "")
    for platform, criterion in sorted(UPDATE_CHECK_CRITERIA.items()):
        found = payloads.get(platform)
        attempt, payload = found if found is not None else (0, None)
        status, detail = update_check_status(payload, expected_version=expected_version)
        log.append(f"{criterion}: {status} ({platform}) - {detail}")
        if status == "PENDING":
            # PENDING braucht (und duldet) keine Evidenz; ein Eintrag hier
            # wuerde einen nicht erbrachten Nachweis belegt aussehen lassen.
            continue
        updated = set_release_instance_criterion(
            updated,
            checklist=checklist,
            checklist_path=checklist_path,
            criterion_id=criterion,
            status=status,
            # Mit Versuchsnummer: Genau so heisst das hochgeladene Artefakt.
            evidence=[run_url, f"Artefakt abnahme-{platform}-{attempt}"],
        )
    return updated, log


def create_approval_manifest(
    *,
    candidate_contract: dict[str, Any],
    checklist_path: Path,
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
        acceptance_run_attempt,
        "acceptance.run_attempt",
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
                raise ContractError(
                    f"Pausierte Plattform {platform} darf keine Freigabe-Evidenz tragen"
                )
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
            "art": "run-id",
            "wert": str(candidate["run_id"]),
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

    checklist = load_release_checklist(checklist_path)
    release_instance = build_release_instance(
        checklist=checklist,
        checklist_path=checklist_path,
        candidate=candidate,
        statuses=statuses,
        acceptance_run_id=acceptance_run_id,
    )
    manifest_records = [
        {**record, "acceptance_status": statuses[str(record["platform"])]} for record in records
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
        "release_instance": release_instance,
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
    checklist_path: Path | None = None,
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
    if (
        not tag_match
        or tag_match.group(1) != version
        or candidate.get("expected_tag") != expected_tag
    ):
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
    release_instance = manifest.get("release_instance")
    if not isinstance(release_instance, dict):
        raise ContractError("Freigabemanifest ohne gepinnte Release-Instanz")
    release_instance = cast(dict[str, Any], release_instance)
    checklist = load_release_checklist(checklist_path) if checklist_path is not None else None
    validate_release_instance(
        release_instance,
        checklist=checklist,
        checklist_path=checklist_path,
    )
    if release_instance.get("candidate_sha") != head_sha:
        raise ContractError("Release-Instanz gehoert zu einem anderen Kandidaten-Commit")
    if release_instance.get("release_version") != version:
        raise ContractError("Release-Instanz gehoert zu einer anderen Version")
    if checklist is not None:
        assert checklist_path is not None
        validate_release_instance_completion(
            release_instance,
            checklist=checklist,
            checklist_path=checklist_path,
            through_phase="pre-release",
        )
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


def manifest_artifacts(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the validated artifact list of an approval manifest."""
    records_raw = manifest.get("artifacts")
    if not isinstance(records_raw, list) or not all(isinstance(item, dict) for item in records_raw):
        raise ContractError("Manifest ohne gueltige Artefaktliste")
    return cast(list[dict[str, Any]], records_raw)


def compare_artifact_directory(
    manifest: dict[str, Any], directory: Path
) -> list[dict[str, Any]]:
    """Compare every manifest entry against the directory, file by file.

    Einzige Vergleichsregel des Vertrags: ``verify_artifact_directory`` (das
    Publish-Gate) und der oeffentliche Download-Nachweis (#916) werten
    dasselbe Ergebnis aus. Ein Bericht kann so nie etwas anderes behaupten
    als das Verdikt, das den Lauf scheitern laesst.  Anders als das Gate
    bricht diese Funktion nicht beim ersten Fund ab, sondern beschreibt jede
    Datei: ``PASS``, ``FAIL`` (Groesse oder SHA-256 weichen ab), ``MISSING``
    (im Manifest, nicht im Verzeichnis) oder ``UNEXPECTED`` (umgekehrt).

    Eine ``UNEXPECTED``-Datei wird bewusst **nicht** gehasht (Review-Befund
    PR #925): Der Hash einer Fremddatei ist keine Evidenz ueber den Release,
    und ein Lesefehler darauf wuerde den sauberen ``ContractError`` des
    Publish-Gates durch einen rohen ``OSError`` ersetzen. Name und Groesse
    benennen den Fund vollstaendig.  Die im Manifest *erwarteten* Dateien
    hasht das Gate dagegen auch dann, wenn die Menge ohnehin schon abweicht -
    der Preis dafuer, dass Bericht und Verdikt aus demselben Aufruf stammen.
    Reihenfolge und Wortlaut der Gate-Meldungen bleiben unveraendert.
    """
    expected = {str(item["name"]): item for item in manifest_artifacts(manifest)}
    actual = _release_files(directory)
    results: list[dict[str, Any]] = []
    for name in sorted(set(expected) | set(actual)):
        record = expected.get(name)
        path = actual.get(name)
        if record is None:
            results.append(
                {
                    "name": name,
                    "status": "UNEXPECTED",
                    "detail": "Datei ist nicht Teil des Freigabemanifests",
                    "expected_bytes": None,
                    "expected_sha256": None,
                    "bytes": path.stat().st_size if path is not None else None,
                    "sha256": None,
                }
            )
            continue
        entry: dict[str, Any] = {
            "name": name,
            "status": "PASS",
            "detail": "",
            "expected_bytes": int(record["bytes"]),
            "expected_sha256": str(record["sha256"]),
            "bytes": None,
            "sha256": None,
        }
        if path is None:
            entry["status"] = "MISSING"
            entry["detail"] = "Datei fehlt"
        else:
            entry["bytes"] = path.stat().st_size
            entry["sha256"] = _sha256_file(path)
            if entry["bytes"] != entry["expected_bytes"]:
                entry["status"] = "FAIL"
                entry["detail"] = "Dateigroesse weicht ab"
            elif entry["sha256"] != entry["expected_sha256"]:
                entry["status"] = "FAIL"
                entry["detail"] = "SHA-256 weicht ab"
        results.append(entry)
    return results


def verify_artifact_directory(manifest: dict[str, Any], directory: Path) -> None:
    """Require exact filename, size, and SHA-256 equality with the manifest."""
    results = compare_artifact_directory(manifest, directory)
    missing = sorted(item["name"] for item in results if item["status"] == "MISSING")
    extra = sorted(item["name"] for item in results if item["status"] == "UNEXPECTED")
    if missing or extra:
        raise ContractError(f"Artefaktmenge weicht ab: fehlend={missing}, zusaetzlich={extra}")
    for item in results:
        if item["status"] == "FAIL":
            raise ContractError(f"{item['detail']}: {item['name']}")


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
    create.add_argument("--checklist", type=Path, required=True)
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
    verify.add_argument("--checklist", type=Path)

    release_ref = commands.add_parser("verify-release-ref")
    release_ref.add_argument("--ref-json", type=Path, required=True)
    release_ref.add_argument("--ref", required=True)
    release_ref.add_argument("--expected-sha", required=True)

    ref_protection = commands.add_parser("verify-ref-protection")
    ref_protection.add_argument("--rules-json", type=Path, required=True)
    ref_protection.add_argument("--ref", required=True)

    artifacts = commands.add_parser("verify-artifacts")
    artifacts.add_argument("--manifest", type=Path, required=True)
    artifacts.add_argument("--directory", type=Path, required=True)

    plan_tag = commands.add_parser("plan-tag")
    plan_tag.add_argument("--manifest", type=Path, required=True)
    plan_tag.add_argument("--tag", required=True)
    # Antwort von git/matching-refs/tags/<tag>: immer HTTP 200, leere Liste =
    # Tag fehlt. Kein 404-Sonderfall im Shell.
    plan_tag.add_argument("--matching-refs-json", type=Path, required=True)
    plan_tag.add_argument("--tag-object-json", type=Path)

    plan = commands.add_parser("plan-publish")
    plan.add_argument("--manifest", type=Path, required=True)
    plan.add_argument("--state", type=Path, required=True)
    plan.add_argument("--existing-dir", type=Path, required=True)

    validate_checklist = commands.add_parser("validate-checklist")
    validate_checklist.add_argument("--checklist", type=Path, required=True)

    extract_instance = commands.add_parser("extract-instance")
    extract_instance.add_argument("--manifest", type=Path, required=True)
    extract_instance.add_argument("--output", type=Path, required=True)

    set_criterion = commands.add_parser("set-criterion")
    set_criterion.add_argument("--checklist", type=Path, required=True)
    set_criterion.add_argument("--instance", type=Path, required=True)
    set_criterion.add_argument("--criterion", required=True)
    set_criterion.add_argument("--status", choices=CHECKLIST_STATES, required=True)
    set_criterion.add_argument("--evidence", action="append", default=[])
    set_criterion.add_argument("--waiver-owner", default="")
    set_criterion.add_argument("--waiver-reason", default="")
    set_criterion.add_argument("--output", type=Path, required=True)

    finalize = commands.add_parser("finalize-instance")
    finalize.add_argument("--checklist", type=Path, required=True)
    finalize.add_argument("--instance", type=Path, required=True)
    finalize.add_argument("--evidence-dir", type=Path, required=True)
    finalize.add_argument("--run-url", required=True)
    finalize.add_argument("--output", type=Path, required=True)

    validate_instance = commands.add_parser("validate-instance")
    validate_instance.add_argument("--checklist", type=Path, required=True)
    validate_instance.add_argument("--instance", type=Path, required=True)
    validate_instance.add_argument("--through-phase", choices=CHECKLIST_PHASES)
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
            _write_github_outputs(
                {
                    "head_sha": candidate["head_sha"],
                    "version": candidate["version"],
                    "expected_tag": candidate["expected_tag"],
                }
            )
        elif args.command == "create-approval":
            manifest = create_approval_manifest(
                candidate_contract=_load_json(args.candidate_contract),
                checklist_path=args.checklist,
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
                checklist_path=args.checklist,
            )
            _write_github_outputs(
                {
                    "candidate_sha": candidate["head_sha"],
                    "version": candidate["version"],
                }
            )
        elif args.command == "verify-release-ref":
            sha = validate_release_ref(
                _load_json(args.ref_json),
                expected_ref=args.ref,
                expected_sha=args.expected_sha,
            )
            print(f"Release-Ref {args.ref} zeigt auf {sha}.")
        elif args.command == "verify-ref-protection":
            rules = validate_ref_protection(
                _load_json_array(args.rules_json), expected_ref=args.ref
            )
            print(f"Release-Ref {args.ref} geschuetzt durch: {', '.join(rules)}.")
        elif args.command == "verify-artifacts":
            verify_artifact_directory(_load_json(args.manifest), args.directory)
        elif args.command == "plan-tag":
            ref_payload = select_tag_ref(
                json.loads(args.matching_refs_json.read_text(encoding="utf-8")),
                tag=args.tag,
            )
            tag_object_payload = (
                _load_json(args.tag_object_json)
                if args.tag_object_json is not None and args.tag_object_json.is_file()
                else None
            )
            action, candidate_sha = plan_release_tag(
                _load_json(args.manifest),
                tag=args.tag,
                ref_payload=ref_payload,
                tag_object_payload=tag_object_payload,
            )
            _write_github_outputs({"action": action, "candidate_sha": candidate_sha})
            print(f"Tag-Plan fuer {args.tag}: {action} (Kandidat {candidate_sha}).")
        elif args.command == "plan-publish":
            state = _load_json(args.state)
            action = plan_publish(
                _load_json(args.manifest),
                exists=state.get("exists") is True,
                is_draft=state.get("is_draft") is True,
                existing_dir=args.existing_dir,
            )
            print(action)
            _write_github_outputs({"action": action})
        elif args.command == "validate-checklist":
            checklist = load_release_checklist(args.checklist)
            print(f"Checkliste {checklist['checklist_version']} ist gueltig.")
        elif args.command == "extract-instance":
            manifest = _load_json(args.manifest)
            instance = manifest.get("release_instance")
            if not isinstance(instance, dict):
                raise ContractError("Freigabemanifest ohne Release-Instanz")
            validate_release_instance(cast(dict[str, Any], instance))
            _write_json(args.output, cast(dict[str, Any], instance))
        elif args.command == "set-criterion":
            checklist = load_release_checklist(args.checklist)
            instance = set_release_instance_criterion(
                _load_json(args.instance),
                checklist=checklist,
                checklist_path=args.checklist,
                criterion_id=args.criterion,
                status=args.status,
                evidence=list(args.evidence),
                waiver_owner=args.waiver_owner,
                waiver_reason=args.waiver_reason,
            )
            _write_json(args.output, instance)
        elif args.command == "finalize-instance":
            checklist = load_release_checklist(args.checklist)
            instance_path = (
                select_instance_payload(args.instance)
                if args.instance.is_dir()
                else args.instance
            )
            updated, log = apply_update_criteria(
                _load_json(instance_path),
                checklist=checklist,
                checklist_path=args.checklist,
                payloads=load_update_check_payloads(args.evidence_dir),
                run_url=args.run_url,
            )
            # Erst schreiben, dann pruefen: Ein FAIL darf die Instanz, die ihn
            # belegt, nicht mitreissen.
            _write_json(args.output, updated)
            for line in log:
                print(line)
            validate_release_instance_completion(
                updated,
                checklist=checklist,
                checklist_path=args.checklist,
                through_phase="post-release",
            )
            print("Release-Instanz ist bis post-release abgeschlossen.")
        else:
            checklist = load_release_checklist(args.checklist)
            instance = _load_json(args.instance)
            if args.through_phase:
                validate_release_instance_completion(
                    instance,
                    checklist=checklist,
                    checklist_path=args.checklist,
                    through_phase=args.through_phase,
                )
            else:
                validate_release_instance(
                    instance,
                    checklist=checklist,
                    checklist_path=args.checklist,
                )
            print("Release-Instanz ist gueltig.")
    except ContractError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
