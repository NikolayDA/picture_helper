#!/usr/bin/env python3
"""Create GitHub issues from scheduled Codex security-scan JSON output."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}
DEFAULT_API_URL = "https://api.github.com"


@dataclass(frozen=True)
class Finding:
    title: str
    severity: str
    confidence: str
    category: str
    cwe: list[str]
    dedupe_key: str
    summary: str
    impact: str
    evidence: list[str]
    affected_locations: list[dict[str, Any]]
    remediation: list[str]
    notes: str

    @property
    def marker_id(self) -> str:
        digest = hashlib.sha256(self.dedupe_key.encode("utf-8")).hexdigest()
        return digest[:24]

    @property
    def marker(self) -> str:
        return f"codex-security-scan:{self.marker_id}"


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _location_key(location: dict[str, Any]) -> str:
    path = str(location.get("path", "")).strip()
    start = location.get("start_line")
    end = location.get("end_line")
    if start and end and start != end:
        return f"{path}:{start}-{end}"
    if start:
        return f"{path}:{start}"
    return path


def _fallback_dedupe_key(raw: dict[str, Any]) -> str:
    locations = raw.get("affected_locations")
    first_location = ""
    if isinstance(locations, list) and locations:
        first = locations[0]
        if isinstance(first, dict):
            first_location = _location_key(first)
    parts = [
        str(raw.get("category", "")).strip(),
        str(raw.get("title", "")).strip(),
        first_location,
    ]
    return "|".join(part for part in parts if part) or "unknown-finding"


def load_findings(path: Path, min_severity: str) -> list[Finding]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_findings = data.get("findings", data if isinstance(data, list) else [])
    if not isinstance(raw_findings, list):
        raise ValueError("security scan output must contain a findings array")

    threshold = SEVERITY_ORDER[min_severity]
    findings: list[Finding] = []
    for raw in raw_findings:
        if not isinstance(raw, dict):
            continue
        if raw.get("reportable") is False:
            continue
        severity = str(raw.get("severity", "")).lower()
        if severity not in SEVERITY_ORDER or SEVERITY_ORDER[severity] < threshold:
            continue
        title = str(raw.get("title", "")).strip()
        if not title:
            continue
        locations = raw.get("affected_locations")
        if not isinstance(locations, list) or not locations:
            locations = [{"path": "unknown"}]
        findings.append(
            Finding(
                title=title,
                severity=severity,
                confidence=str(raw.get("confidence", "medium")).lower(),
                category=str(raw.get("category", "Security finding")).strip(),
                cwe=_as_list(raw.get("cwe")),
                dedupe_key=str(raw.get("dedupe_key") or _fallback_dedupe_key(raw)).strip(),
                summary=str(raw.get("summary", "")).strip(),
                impact=str(raw.get("impact", "")).strip(),
                evidence=_as_list(raw.get("evidence")),
                affected_locations=[loc for loc in locations if isinstance(loc, dict)],
                remediation=_as_list(raw.get("remediation")),
                notes=str(raw.get("notes", "")).strip(),
            )
        )
    return findings


def github_request(
    method: str,
    path: str,
    token: str,
    *,
    api_url: str = DEFAULT_API_URL,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = api_url.rstrip("/") + path
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if body is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {path} failed: {exc.code} {detail}") from exc
    return json.loads(content) if content else {}


def issue_exists(repo: str, finding: Finding, token: str, api_url: str) -> str | None:
    query = f'repo:{repo} is:issue is:open in:body "{finding.marker}"'
    encoded = urllib.parse.urlencode({"q": query, "per_page": "1"})
    result = github_request("GET", f"/search/issues?{encoded}", token, api_url=api_url)
    items = result.get("items") or []
    if items:
        return str(items[0].get("html_url") or items[0].get("url") or "")
    return None


def format_locations(locations: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for location in locations:
        label = str(location.get("label") or "").strip()
        suffix = f" ({label})" if label else ""
        lines.append(f"- `{_location_key(location)}`{suffix}")
    return "\n".join(lines) if lines else "- `unknown`"


def format_issue_body(
    finding: Finding,
    *,
    repo: str,
    server_url: str,
    run_id: str,
    sha: str,
) -> str:
    run_url = f"{server_url.rstrip('/')}/{repo}/actions/runs/{run_id}" if run_id else ""
    cwe = ", ".join(finding.cwe) if finding.cwe else "not specified"
    evidence = "\n".join(f"- {item}" for item in finding.evidence) or "- Not specified"
    remediation = "\n".join(f"- {item}" for item in finding.remediation) or "- Not specified"
    notes = finding.notes or "None"
    run_line = f"\n- Run: {run_url}" if run_url else ""
    sha_line = f"\n- Commit: `{sha}`" if sha else ""

    return f"""<!-- {finding.marker} -->
## Summary

{finding.summary or finding.title}

## Severity

- Severity: `{finding.severity}`
- Confidence: `{finding.confidence}`
- Category: {finding.category}
- CWE: {cwe}

## Affected locations

{format_locations(finding.affected_locations)}

## Impact

{finding.impact or "Not specified"}

## Evidence

{evidence}

## Recommended fix

{remediation}

## Notes

{notes}

---

Found by automated Codex security scan.{sha_line}{run_line}
"""


def create_issue(
    repo: str,
    finding: Finding,
    token: str,
    api_url: str,
    server_url: str,
    run_id: str,
    sha: str,
    labels: list[str],
) -> str:
    title = finding.title
    if not title.lower().startswith("security"):
        title = f"Security: {title}"
    body = format_issue_body(
        finding,
        repo=repo,
        server_url=server_url,
        run_id=run_id,
        sha=sha,
    )
    payload: dict[str, Any] = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    result = github_request("POST", f"/repos/{repo}/issues", token, api_url=api_url, payload=payload)
    return str(result.get("html_url") or result.get("url") or "")


def write_summary(results: list[dict[str, str]]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    lines = ["## Codex security issue sync", "", "| Finding | Status | URL |", "|---|---|---|"]
    for result in results:
        lines.append(f"| {result['title']} | {result['status']} | {result.get('url', '')} |")
    Path(summary_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("findings_json", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--results", type=Path, default=Path("security-issue-results.json"))
    args = parser.parse_args()

    min_severity = os.environ.get("SECURITY_SCAN_MIN_SEVERITY", "low").lower()
    if min_severity not in SEVERITY_ORDER:
        raise SystemExit(f"invalid SECURITY_SCAN_MIN_SEVERITY: {min_severity}")

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    api_url = os.environ.get("GITHUB_API_URL", DEFAULT_API_URL)
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    sha = os.environ.get("GITHUB_SHA", "")
    labels = [
        label.strip()
        for label in os.environ.get("SECURITY_SCAN_LABELS", "").split(",")
        if label.strip()
    ]

    findings = load_findings(args.findings_json, min_severity)
    results: list[dict[str, str]] = []
    if not findings:
        results.append({"title": "No reportable findings", "status": "skipped", "url": ""})
    for finding in findings:
        if args.dry_run:
            body = format_issue_body(
                finding,
                repo=repo or "owner/repo",
                server_url=server_url,
                run_id=run_id,
                sha=sha,
            )
            print(f"Would create or reuse issue for: {finding.title}")
            print(body)
            results.append({"title": finding.title, "status": "dry-run", "url": ""})
            continue
        if not repo or not token:
            raise SystemExit("GITHUB_REPOSITORY and GITHUB_TOKEN are required unless --dry-run is used")
        existing_url = issue_exists(repo, finding, token, api_url)
        if existing_url:
            print(f"Existing issue found for {finding.title}: {existing_url}")
            results.append({"title": finding.title, "status": "existing", "url": existing_url})
            continue
        issue_url = create_issue(repo, finding, token, api_url, server_url, run_id, sha, labels)
        print(f"Created issue for {finding.title}: {issue_url}")
        results.append({"title": finding.title, "status": "created", "url": issue_url})

    args.results.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    write_summary(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
