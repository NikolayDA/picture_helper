#!/usr/bin/env python3
"""Versionierte, fail-closed Pfadklassifikation fuer Release-Gates (#743).

Die positive Neutral-Allowlist lebt in ``release/path-policy.json``. Ein Pfad,
der dort weder als release-neutral noch als bekannte relevante Klasse erfasst
ist, bleibt kandidatenrelevant und wird als unklassifiziert markiert. Das
Freeze-Gate kann dadurch unbekannte Build-Eingaenge blockieren, statt sie still
an der Kandidatenbewegung vorbeizuschleusen.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Final, cast

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
POLICY_PATH: Final = "release/path-policy.json"

RELEASE_NEUTRAL: Final = "release-neutral"
CANDIDATE_RELEVANT: Final = "candidate-relevant"
UNKNOWN_RULE_ID: Final = "unknown-default"


class PolicyFormatError(RuntimeError):
    """Die Policy ist unlesbar, mehrdeutig oder nicht fail-closed."""


@dataclass(frozen=True)
class PolicyRule:
    """Eine begruendete exakte oder praefixbasierte Pfadregel."""

    rule_id: str
    kind: str
    path: str
    sample_path: str
    reason: str
    evidence: tuple[str, ...]

    def matches(self, path: str) -> bool:
        if self.kind == "exact":
            return path == self.path
        return path.startswith(self.path)


@dataclass(frozen=True)
class PathClassification:
    """Ergebnis der Policy fuer genau einen Git-Pfad."""

    path: str
    classification: str
    rule_id: str
    reason: str
    explicit: bool


@dataclass(frozen=True)
class PathPolicy:
    """Validierte Policy samt Digest der versionierten Quelldatei."""

    schema: int
    version: int
    digest: str
    neutral_rules: tuple[PolicyRule, ...]
    relevant_rules: tuple[PolicyRule, ...]
    drift_guards: dict[str, tuple[str, ...]]


def _normalise_path(path: str, *, prefix: bool) -> str:
    if not path or "\\" in path or path.startswith("/"):
        raise PolicyFormatError(f"ungueltiger relativer POSIX-Pfad: {path!r}")
    pure = PurePosixPath(path)
    if any(part in ("", ".", "..") for part in pure.parts):
        raise PolicyFormatError(f"nicht normalisierter Policy-Pfad: {path!r}")
    canonical = pure.as_posix() + ("/" if prefix else "")
    if path != canonical:
        raise PolicyFormatError(f"nicht normalisierter Policy-Pfad: {path!r}")
    if prefix != path.endswith("/"):
        expected = "mit" if prefix else "ohne"
        raise PolicyFormatError(f"Policy-Pfad {path!r} muss {expected} abschliessendem '/' stehen")
    return path


def _parse_rule(raw: object, classification: str) -> PolicyRule:
    if not isinstance(raw, dict):
        raise PolicyFormatError(f"{classification}-Regel ist kein Objekt")
    data = cast(dict[str, Any], raw)
    required = {"id", "kind", "path", "sample_path", "reason"}
    missing = sorted(required - data.keys())
    if missing:
        raise PolicyFormatError(f"{classification}-Regel ohne {', '.join(missing)}")
    kind = data["kind"]
    if kind not in ("exact", "prefix"):
        raise PolicyFormatError(f"Regel {data['id']!r} hat unbekannte Art {kind!r}")
    rule_id = data["id"]
    path = data["path"]
    sample = data["sample_path"]
    reason = data["reason"]
    if not all(isinstance(value, str) and value.strip() for value in (rule_id, path, sample, reason)):
        raise PolicyFormatError("Regel-ID, Pfad, Beispiel und Begruendung muessen Text enthalten")
    path = _normalise_path(path, prefix=kind == "prefix")
    _normalise_path(sample, prefix=False)
    evidence_raw = data.get("evidence", [])
    if classification == RELEASE_NEUTRAL:
        if not isinstance(evidence_raw, list) or not evidence_raw:
            raise PolicyFormatError(f"neutrale Regel {rule_id!r} ohne Build-Input-Nachweis")
        if not all(isinstance(item, str) and item.strip() for item in evidence_raw):
            raise PolicyFormatError(f"neutrale Regel {rule_id!r} mit leerem Nachweis")
    elif not isinstance(evidence_raw, list):
        raise PolicyFormatError(f"Regel {rule_id!r}: evidence muss eine Liste sein")
    rule = PolicyRule(
        rule_id=rule_id,
        kind=kind,
        path=path,
        sample_path=sample,
        reason=reason,
        evidence=tuple(cast(list[str], evidence_raw)),
    )
    if not rule.matches(sample):
        raise PolicyFormatError(
            f"Beispiel {sample!r} wird von Regel {rule_id!r} ({path!r}) nicht erfasst"
        )
    return rule


def _rules_overlap(left: PolicyRule, right: PolicyRule) -> bool:
    if left.kind == right.kind == "exact":
        return left.path == right.path
    if left.kind == "prefix" and right.kind == "prefix":
        return left.path.startswith(right.path) or right.path.startswith(left.path)
    prefix, exact = (left, right) if left.kind == "prefix" else (right, left)
    return exact.path.startswith(prefix.path)


def parse_policy(text: str) -> PathPolicy:
    """Liest und validiert eine Policy aus ihrem versionierten JSON-Text."""
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PolicyFormatError(f"ungueltiges Policy-JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise PolicyFormatError("Policy-Wurzel ist kein Objekt")
    data = cast(dict[str, Any], raw)
    if data.get("schema") != 1:
        raise PolicyFormatError(f"unbekanntes Policy-Schema {data.get('schema')!r}")
    version = data.get("policy_version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise PolicyFormatError("policy_version muss eine positive Ganzzahl sein")
    if data.get("unknown_path_behavior") != "candidate-relevant-blocking":
        raise PolicyFormatError("unbekannte Pfade muessen candidate-relevant-blocking sein")
    neutral_raw = data.get("release_neutral")
    relevant_raw = data.get("candidate_relevant")
    if not isinstance(neutral_raw, list) or not isinstance(relevant_raw, list):
        raise PolicyFormatError("release_neutral und candidate_relevant muessen Listen sein")
    neutral = tuple(_parse_rule(item, RELEASE_NEUTRAL) for item in neutral_raw)
    relevant = tuple(_parse_rule(item, CANDIDATE_RELEVANT) for item in relevant_raw)
    all_rules = (*neutral, *relevant)
    ids = [rule.rule_id for rule in all_rules]
    if len(ids) != len(set(ids)):
        raise PolicyFormatError("Policy-Regel-IDs muessen eindeutig sein")
    for index, left in enumerate(all_rules):
        for right in all_rules[index + 1 :]:
            if _rules_overlap(left, right):
                raise PolicyFormatError(
                    f"mehrdeutige Policy-Regeln {left.rule_id!r} und {right.rule_id!r}"
                )
    guards_raw = data.get("drift_guards")
    if not isinstance(guards_raw, dict):
        raise PolicyFormatError("drift_guards fehlt oder ist kein Objekt")
    guards: dict[str, tuple[str, ...]] = {}
    for name, values in cast(dict[str, Any], guards_raw).items():
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value for value in values
        ):
            raise PolicyFormatError(f"Drift-Guard {name!r} muss eine Textliste sein")
        guards[name] = tuple(cast(list[str], values))
    digest = "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
    return PathPolicy(
        schema=1,
        version=version,
        digest=digest,
        neutral_rules=neutral,
        relevant_rules=relevant,
        drift_guards=guards,
    )


def load_policy(path: Path = REPO_ROOT / POLICY_PATH) -> PathPolicy:
    """Liest die Policy aus dem Arbeitsbaum."""
    return parse_policy(path.read_text(encoding="utf-8"))


def classify_path(path: str, policy: PathPolicy) -> PathClassification:
    """Klassifiziert *path*; unbekannt bleibt relevant und unklassifiziert."""
    _normalise_path(path, prefix=False)
    for rule in policy.neutral_rules:
        if rule.matches(path):
            return PathClassification(path, RELEASE_NEUTRAL, rule.rule_id, rule.reason, True)
    for rule in policy.relevant_rules:
        if rule.matches(path):
            return PathClassification(path, CANDIDATE_RELEVANT, rule.rule_id, rule.reason, True)
    return PathClassification(
        path,
        CANDIDATE_RELEVANT,
        UNKNOWN_RULE_ID,
        "Unbekannter Pfad: fail-closed kandidatenrelevant; Policy-Ergaenzung erforderlich.",
        False,
    )


def is_candidate_relevant(path: str, policy: PathPolicy) -> bool:
    return classify_path(path, policy).classification == CANDIDATE_RELEVANT


def candidate_relevant_paths(paths: list[str] | tuple[str, ...], policy: PathPolicy) -> tuple[str, ...]:
    """Kandidatenrelevante Teilmenge, Reihenfolge erhalten."""
    return tuple(path for path in paths if is_candidate_relevant(path, policy))


if __name__ == "__main__":
    loaded = load_policy()
    print(f"Policy {loaded.version}: {loaded.digest}")
