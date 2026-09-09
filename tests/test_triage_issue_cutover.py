"""Netzfreie Tests des einmaligen Triage-Cutovers (#1033).

``scripts/triage_issue_cutover.py`` wird über den Dateipfad geladen (kein
``scripts/__init__.py``). Der GitHub-Client bekommt einen Attrappen-Opener;
kein Test liest den Live-Bestand – der Vollständigkeitsabgleich bleibt laut
#1033 eine einmalige Cutover-Abnahme und wird hier nicht zum Wächter.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "triage_issue_cutover.py"

_SPEC = importlib.util.spec_from_file_location("triage_issue_cutover", SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
tic = importlib.util.module_from_spec(_SPEC)
sys.modules["triage_issue_cutover"] = tic
_SPEC.loader.exec_module(tic)

_URL = "https://github.com/NikolayDA/picture_helper/issues"
TABLE = f"""# Empfehlungen

## Aktueller Stand

Text.

## Offene GitHub-Issues – Triage-Stand

| # | Titel | Relevanz | Komplexität | Empfohlenes Modell (Aufwand) | Nächster Schritt |
|---|-------|----------|--------------|-------------------------------|-------------------|
| [#10]({_URL}/10) | Zehn | 🟠 Hoch (a) | 🟢 Niedrig (b) | Sonnet, mittel | Startbereit – los |
| [#11]({_URL}/11) | Elf `x` | 🟡 Mittel | 🔴 Hoch | – (kein Agent) | Blocked (extern) – Hardware |

### Als Nächstes empfohlen

1. **#10** – zuerst; danach
   #11.
2. Dann **#11** messen.

## Vorige Runden
"""


def test_parse_triage_table_drops_model_column_and_keeps_text() -> None:
    rows = tic.parse_triage_table(TABLE)
    assert sorted(rows) == [10, 11]
    assert rows[10].title == "Zehn"
    assert rows[10].relevance == "🟠 Hoch (a)"
    assert rows[10].complexity == "🟢 Niedrig (b)"
    assert rows[10].next_step == "Startbereit – los"
    assert rows[11].title == "Elf `x`"
    assert not hasattr(rows[11], "model")


def test_parse_next_steps_joins_continuation_lines() -> None:
    assert tic.parse_next_steps(TABLE) == [
        "**#10** – zuerst; danach #11.",
        "Dann **#11** messen.",
    ]


@pytest.mark.parametrize(
    "broken",
    [
        TABLE.replace("| Sonnet, mittel |", "|"),  # fünf statt sechs Zellen
        TABLE.replace(f"[#11]({_URL}/11)", f"[#11]({_URL}/12)"),  # Link ≠ Nummer
        TABLE.replace("\n### Als", f"| [#10]({_URL}/10) | Doppelt | a | b | c | d |\n\n### Als"),
    ],
)
def test_parse_triage_table_fails_closed(broken: str) -> None:
    with pytest.raises(tic.CutoverError):
        tic.parse_triage_table(broken)


def test_decision_record_is_internally_consistent() -> None:
    """Die Akte gegen die echte Tabelle im Checkout – so lange es sie gibt (#1040)."""
    text = (ROOT / "RECOMMENDATIONS.md").read_text(encoding="utf-8")
    rows = tic.parse_triage_table(text)
    tic.validate_decisions(tic.DECISIONS, rows)
    assert len(tic.LEGACY_ROWS) == 41
    assert set(tic.DECISIONS) >= tic.LEGACY_ROWS
    for number, decision in tic.DECISIONS.items():
        assert decision.prio in tic.PRIO_LABELS, number


def test_validate_decisions_rejects_unknown_blocker_and_self_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tic, "LEGACY_ROWS", frozenset({10, 11}))
    rows = tic.parse_triage_table(TABLE)
    decisions = {
        10: tic.Decision(tic.PRIO_NOW, "r", blocked_by=(99,)),
        11: tic.Decision(tic.PRIO_NEXT, "r"),
    }
    with pytest.raises(tic.CutoverError, match="geschlossen"):
        tic.validate_decisions(decisions, rows)
    decisions[10] = tic.Decision(tic.PRIO_NOW, "r", blocked_by=(10,))
    with pytest.raises(tic.CutoverError, match="selbst"):
        tic.validate_decisions(decisions, rows)
    decisions[10] = tic.Decision("prio:never", "r")
    with pytest.raises(tic.CutoverError, match="unbekanntes Prio-Label"):
        tic.validate_decisions(decisions, rows)


def test_validate_live_coverage_requires_exact_match() -> None:
    decisions = {10: tic.Decision(tic.PRIO_NOW, "r")}
    live = {10: tic.LiveIssue(10, 1, frozenset()), 12: tic.LiveIssue(12, 2, frozenset())}
    with pytest.raises(tic.CutoverError, match=r"ohne Entscheidung \[12\]"):
        tic.validate_live_coverage(decisions, live)
    with pytest.raises(tic.CutoverError, match=r"nicht mehr offen \[10\]"):
        tic.validate_live_coverage(decisions, {12: live[12]})


def test_render_comment_matches_issue_pattern() -> None:
    rows = tic.parse_triage_table(TABLE)
    plain = tic.render_comment(rows[10], tic.Decision(tic.PRIO_NOW, "Regel A", blocked_by=(11,)))
    assert plain.startswith(
        "**Triage-Übernahme aus RECOMMENDATIONS.md (Stand 2026-09-07, Commit dd6c572):** "
        "Relevanz 🟠 Hoch (a); Komplexität 🟢 Niedrig (b); nächster Schritt: Startbereit – los"
    )
    assert "Owner-Regel aus #1033): Regel A." in plain
    assert "„blocked by“: #11." in plain
    assert "Sonnet" not in plain  # Modellspalte wird nicht übernommen
    assert plain.endswith(tic.FOOTER)

    extern = tic.render_comment(
        rows[11], tic.Decision(tic.PRIO_LATER, "Regel B", extern="Hardware X", note="Abw."),
    )
    assert extern.splitlines()[0] == "Blockiert extern durch: Hardware X"
    assert "Bewusste Abweichung vom Tabellentext: Abw." in extern


def test_render_epic_comment_keeps_points_verbatim() -> None:
    body = tic.render_epic_comment(tic.parse_next_steps(TABLE), "abc1234")
    assert body.startswith(f"{tic.EPIC_MARKER} (Cutover-Stand abc1234):**")
    assert "\n1. **#10** – zuerst; danach #11.\n2. Dann **#11** messen." in body


class _FakeResponse(io.BytesIO):
    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class _FakeGitHub:
    """Minimaler In-Memory-GitHub für Plan/Apply/Verify."""

    def __init__(self, issues: dict[int, dict[str, Any]], labels: set[str]) -> None:
        self.issues = issues
        self.labels = labels
        self.calls: list[tuple[str, str, Any]] = []

    def __call__(self, request: Any, timeout: float) -> _FakeResponse:
        method, path = request.get_method(), request.full_url.split("api.github.com", 1)[1]
        body = json.loads(request.data) if request.data else None
        self.calls.append((method, path, body))
        query = path.split("?", 1)[0]
        parts = query.strip("/").split("/")
        if method == "GET" and query.endswith("/issues"):
            page = int(path.rsplit("page=", 1)[1])
            items = [
                {"number": n, "id": i["id"], "labels": [{"name": x} for x in i["labels"]]}
                for n, i in sorted(self.issues.items())
            ]
            return _FakeResponse(json.dumps(items if page == 1 else []).encode())
        if method == "GET" and query.endswith("/labels") and len(parts) == 4:
            return _FakeResponse(json.dumps([{"name": x} for x in self.labels]).encode())
        number = int(parts[4]) if len(parts) > 4 else 0
        if method == "GET" and query.endswith("/comments"):
            bodies = self.issues[number]["comments"]
            page = int(path.rsplit("page=", 1)[1])
            data = [{"body": b} for b in bodies] if page == 1 else []
            return _FakeResponse(json.dumps(data).encode())
        if method == "GET" and query.endswith("/blocked_by"):
            deps = [{"number": n} for n in self.issues[number]["blocked_by"]]
            return _FakeResponse(json.dumps(deps).encode())
        if method == "POST" and query.endswith("/labels") and len(parts) == 4:
            self.labels.add(body["name"])
        elif method == "POST" and query.endswith("/labels"):
            self.issues[number]["labels"].update(body["labels"])
        elif method == "DELETE" and "/labels/" in query:
            self.issues[number]["labels"].discard(parts[-1].replace("%3A", ":"))
        elif method == "POST" and query.endswith("/blocked_by"):
            blocker = next(n for n, i in self.issues.items() if i["id"] == body["issue_id"])
            self.issues[number]["blocked_by"].add(blocker)
        elif method == "POST" and query.endswith("/comments"):
            self.issues[number]["comments"].append(body["body"])
        else:
            raise AssertionError(f"unerwartet: {method} {path}")
        return _FakeResponse(b"{}")


def _issue(issue_id: int, *labels: str) -> dict[str, Any]:
    return {"id": issue_id, "labels": set(labels), "blocked_by": set(), "comments": []}


def _fixture_world() -> tuple[_FakeGitHub, dict[int, Any], dict[int, Any], list[str]]:
    rows = tic.parse_triage_table(TABLE)
    next_steps = tic.parse_next_steps(TABLE)
    decisions = {
        10: tic.Decision(tic.PRIO_NOW, "Regel A"),
        11: tic.Decision(tic.PRIO_NEXT, "Regel B", blocked_by=(10,), extern="Hardware"),
        tic.EPIC_ISSUE: tic.Decision(tic.PRIO_NOW, "Regel C"),
    }
    fake = _FakeGitHub(
        {10: _issue(100, "bug", "prio:later"), 11: _issue(110), tic.EPIC_ISSUE: _issue(120)},
        {"bug", "prio:now"},
    )
    return fake, rows, decisions, next_steps


def test_plan_apply_verify_roundtrip_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tic, "LEGACY_ROWS", frozenset({10, 11}))
    fake, rows, decisions, next_steps = _fixture_world()
    client = tic.GitHubClient("o/r", token="t", opener=fake)

    actions = tic.build_plan(client, rows, decisions, next_steps, "abc1234")
    kinds = sorted((a.kind, a.issue, a.payload[:12]) for a in actions)
    assert ("create_label", 0, '["prio:next"') in kinds
    assert ("create_label", 0, '["blocked:ex') in kinds
    assert ("add_label", 10, "prio:now") in kinds
    assert ("remove_label", 10, "prio:later") in kinds
    assert ("add_label", 11, "blocked:exte") in kinds
    assert ("add_blocked_by", 11, "10") in kinds
    assert sum(1 for a in actions if a.kind == "comment") == 3  # #10, #11, Epic

    report_before = tic.verify(client, rows, decisions, now=datetime(2026, 9, 9, tzinfo=timezone.utc))
    assert not report_before.ok
    assert any("(a)" in p for p in report_before.problems)
    assert any("(b)" in p for p in report_before.problems)

    tic.apply_plan(client, actions, client.list_open_issues())
    assert fake.issues[10]["labels"] == {"bug", "prio:now"}
    assert fake.issues[11]["labels"] == {"prio:next", "blocked:extern"}
    assert fake.issues[11]["blocked_by"] == {10}
    assert fake.issues[11]["comments"][0].startswith("Blockiert extern durch: Hardware")
    assert fake.issues[tic.EPIC_ISSUE]["comments"][0].startswith(tic.EPIC_MARKER)

    assert tic.build_plan(client, rows, decisions, next_steps, "abc1234") == []
    report = tic.verify(client, rows, decisions, now=datetime(2026, 9, 9, tzinfo=timezone.utc))
    assert report.ok, report.problems
    assert report.open_count == 3
    rendered = tic.render_report(report, "abc1234")
    assert rendered.startswith("**Cutover-Abgleich grün** – 2026-09-09T00:00:00Z")
    assert "2/2 offene Legacy-Zeilen" in rendered
    assert "3/3 Issues" in rendered
    assert "1 × `blocked:extern`, 1/1 native Abhängigkeiten" in rendered


def test_build_plan_refuses_duplicate_transfer_comment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tic, "LEGACY_ROWS", frozenset({10, 11}))
    fake, rows, decisions, next_steps = _fixture_world()
    fake.issues[10]["comments"] = [f"{tic.COMMENT_MARKER} x", f"{tic.COMMENT_MARKER} y"]
    client = tic.GitHubClient("o/r", token=None, opener=fake)
    with pytest.raises(tic.CutoverError, match="bereits 2 Übernahmekommentare"):
        tic.build_plan(client, rows, decisions, next_steps, "abc1234")


def test_build_plan_stops_on_live_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tic, "LEGACY_ROWS", frozenset({10, 11}))
    fake, rows, decisions, next_steps = _fixture_world()
    fake.issues[13] = _issue(130)
    client = tic.GitHubClient("o/r", token=None, opener=fake)
    with pytest.raises(tic.CutoverError, match=r"ohne Entscheidung \[13\]"):
        tic.build_plan(client, rows, decisions, next_steps, "abc1234")
    assert not any(c[0] != "GET" for c in fake.calls)


def test_http_errors_become_cutover_errors() -> None:
    import urllib.error

    def opener(request: Any, timeout: float) -> _FakeResponse:
        raise urllib.error.HTTPError(request.full_url, 403, "nope", None, io.BytesIO(b"denied"))

    client = tic.GitHubClient("o/r", token=None, opener=opener)
    with pytest.raises(tic.CutoverError, match="HTTP 403: denied"):
        client.list_labels()


def test_cli_plan_is_offline_and_reports_counts(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    exit_code = tic.main(["plan"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "41 Legacy-Zeilen" in out
    assert f"{len(tic.DECISIONS)} Entscheidungen" in out
    broken = tmp_path / "RECOMMENDATIONS.md"
    broken.write_text("# nichts\n", encoding="utf-8")
    assert tic.main(["--recommendations", str(broken), "plan"]) == 2
