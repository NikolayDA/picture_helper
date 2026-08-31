"""Post-Release-Update-Dispatch aus dem Publish-Lauf (#919, Stufe 2).

Der Netzweg (``gh``) ist injiziert, damit Korrelation, Idempotenz und die
Abbruchbedingungen ohne GitHub prüfbar sind – dasselbe Muster wie beim Fetcher
in ``tests/test_public_download_check.py``.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "release_update_dispatch", ROOT / "scripts" / "release_update_dispatch.py"
)
assert SPEC is not None and SPEC.loader is not None
rud = importlib.util.module_from_spec(SPEC)
sys.modules["release_update_dispatch"] = rud
SPEC.loader.exec_module(rud)

REPO = "NikolayDA/picture_helper"
TAG = "v2.9.1"
PREDECESSOR = "v2.9.0"
CANDIDATE_RUN = "4242"
PUBLISH_RUN = "8888"
#: Seit #918 ist der Dispatch-Ref der Release-Ref, nicht der Tag.
REF = f"release/{TAG}"
CANDIDATE_SHA = "c" * 40
MARKER = f"update-check:{TAG}:{CANDIDATE_RUN}"


class FakeGh:
    """Protokolliert Aufrufe und liefert je Abfrage die nächste Laufliste.

    ``ref_payload`` beantwortet die Ref-Abfrage vor einem Dispatch;
    ``None`` lässt sie wie einen ``gh``-Fehler scheitern (gelöschter Ref).
    """

    def __init__(self, listings: list[list[dict]], *, ref_payload: dict | None = "default") -> None:
        self.listings = listings
        self.calls: list[list[str]] = []
        self.ref_payload = (
            {"ref": f"refs/heads/{REF}", "object": {"type": "commit", "sha": CANDIDATE_SHA}}
            if ref_payload == "default"
            else ref_payload
        )

    def __call__(self, args: Sequence[str]) -> str:
        self.calls.append(list(args))
        if args[:2] == ["run", "list"]:
            payload = self.listings.pop(0) if self.listings else []
            return json.dumps(payload)
        if args[:1] == ["api"]:
            if self.ref_payload is None:
                raise rud.DispatchError("gh api scheiterte (Exit 1): Not Found")
            return json.dumps(self.ref_payload)
        return ""

    @property
    def dispatches(self) -> list[list[str]]:
        return [call for call in self.calls if call[:2] == ["workflow", "run"]]

    @property
    def ref_lookups(self) -> list[list[str]]:
        return [call for call in self.calls if call[:1] == ["api"]]


def _run_entry(run_id: int = 777, *, marker: str = MARKER, status: str = "queued",
               conclusion: str = "") -> dict:
    return {
        "databaseId": run_id,
        "displayTitle": f"Release-Abnahme [{marker}]",
        "status": status,
        "conclusion": conclusion,
        "url": f"https://github.com/{REPO}/actions/runs/{run_id}",
        "createdAt": "2026-08-30T22:00:00Z",
    }


def _invoke(gh: FakeGh, tmp_path: Path, *, predecessor: str = PREDECESSOR) -> str:
    return rud.run(
        repo=REPO,
        ref=REF,
        expected_sha=CANDIDATE_SHA,
        tag=TAG,
        candidate_run_id=CANDIDATE_RUN,
        predecessor_tag=predecessor,
        target_issue="595",
        publish_run_id=PUBLISH_RUN,
        markdown=tmp_path / "report.md",
        runner=gh,
        sleep=lambda _s: None,
    )


# ── Marker ─────────────────────────────────────────────────────────────

def test_marker_is_deterministic_and_independent_of_the_publish_run() -> None:
    """Die Idempotenz haengt daran: gleiche Bindung, gleicher Marker.

    Ginge der Publish-Lauf ein, waere jeder Wiederanlauf ein neuer Marker und
    damit ein zweiter Nachweislauf – genau das, was Stufe 2 ausschliesst.
    """
    first = rud.dispatch_marker(tag=TAG, candidate_run_id=CANDIDATE_RUN)
    assert first == rud.dispatch_marker(tag=TAG, candidate_run_id=CANDIDATE_RUN) == MARKER
    assert rud.dispatch_marker(tag="v3.0.0", candidate_run_id=CANDIDATE_RUN) != first
    assert rud.dispatch_marker(tag=TAG, candidate_run_id="99") != first


@pytest.mark.parametrize("tag", ["2.9.1", "v2.9", "v2.9.1 ", "", "v2.9.1;rm -rf /"])
def test_marker_rejects_malformed_tags(tag: str) -> None:
    with pytest.raises(rud.DispatchError, match="Schema"):
        rud.dispatch_marker(tag=tag, candidate_run_id=CANDIDATE_RUN)


def test_marker_rejects_a_non_numeric_run_id() -> None:
    with pytest.raises(rud.DispatchError, match="positive Ganzzahl"):
        rud.dispatch_marker(tag=TAG, candidate_run_id="0")


# ── Korrelation ────────────────────────────────────────────────────────

def test_only_the_matching_marker_is_selected() -> None:
    runs = [
        _run_entry(1, marker="update-check:v2.9.0:1111"),
        {"databaseId": 2, "displayTitle": "Release-Abnahme", "status": "completed"},
        _run_entry(3),
    ]
    found = rud.select_marked_run(runs, marker=MARKER)
    assert found is not None and found.run_id == 3


def test_newest_matching_run_wins_and_missing_ids_fail_closed() -> None:
    # Liste kommt absteigend nach Startzeit: der erste Treffer ist der juengste.
    runs = [_run_entry(9), _run_entry(3)]
    found = rud.select_marked_run(runs, marker=MARKER)
    assert found is not None and found.run_id == 9

    with pytest.raises(rud.DispatchError, match="databaseId"):
        rud.select_marked_run([{"displayTitle": f"x {MARKER}"}], marker=MARKER)
    with pytest.raises(rud.DispatchError, match="keine Liste"):
        rud.select_marked_run({"databaseId": 1}, marker=MARKER)


def test_no_match_returns_none() -> None:
    assert rud.select_marked_run([], marker=MARKER) is None
    assert rud.select_marked_run([_run_entry(marker="update-check:v1.0.0:5")], marker=MARKER) is None


# ── Dispatch, Idempotenz, Abbruch ──────────────────────────────────────

def test_dispatch_binds_every_input_and_forces_all_platforms(tmp_path: Path) -> None:
    """Ein Einzelplattform-Lauf liesse eines der beiden Kriterien PENDING."""
    gh = FakeGh([[], [_run_entry()]])
    assert _invoke(gh, tmp_path) == rud.ACTION_DISPATCHED

    (dispatch,) = gh.dispatches
    assert dispatch[:3] == ["workflow", "run", "release-abnahme.yml"]
    assert "--ref" in dispatch and dispatch[dispatch.index("--ref") + 1] == REF
    bound = dict(part.split("=", 1) for part in dispatch if "=" in part)
    assert bound == {
        "run_id": CANDIDATE_RUN,
        "platforms": "alle",
        "dry_run": "false",
        "predecessor_tag": PREDECESSOR,
        "dispatch_marker": MARKER,
        "publish_run_id": PUBLISH_RUN,
        "target_issue": "595",
    }


def test_an_existing_run_with_the_same_marker_is_never_dispatched_twice(
    tmp_path: Path,
) -> None:
    gh = FakeGh([[_run_entry(555, status="completed", conclusion="success")]])
    assert _invoke(gh, tmp_path) == rud.ACTION_ALREADY_PRESENT
    assert gh.dispatches == []
    assert "555" in (tmp_path / "report.md").read_text(encoding="utf-8")


def test_a_failed_previous_run_is_reported_but_not_repeated(tmp_path: Path) -> None:
    """Ein fehlgeschlagener Update-Nachweis ist laut Runbook ein Incident.

    Ein automatischer zweiter Versuch wuerde den Befund verdecken und im
    schlechtesten Fall in einer Schleife enden.
    """
    gh = FakeGh([[_run_entry(556, status="completed", conclusion="failure")]])
    assert _invoke(gh, tmp_path) == rud.ACTION_ALREADY_PRESENT
    assert gh.dispatches == []
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "Incident" in report and "failure" in report


def test_missing_predecessor_skips_visibly_without_touching_github(tmp_path: Path) -> None:
    """Der Vorgaenger wird nie geraten – lieber PENDING als fabriziert PASS."""
    gh = FakeGh([])
    assert _invoke(gh, tmp_path, predecessor="") == rud.ACTION_SKIPPED_NO_PREDECESSOR
    assert gh.calls == []
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "PENDING" in report and "nicht geraten" in report


def test_malformed_predecessor_tag_aborts(tmp_path: Path) -> None:
    gh = FakeGh([])
    with pytest.raises(rud.DispatchError, match="predecessor_tag"):
        _invoke(gh, tmp_path, predecessor="latest")
    assert gh.calls == []


def test_polling_waits_for_the_run_to_appear(tmp_path: Path) -> None:
    """workflow_dispatch antwortet ohne Body; die Run-ID entsteht serverseitig."""
    gh = FakeGh([[], [], [], [_run_entry(4711)]])
    assert _invoke(gh, tmp_path) == rud.ACTION_DISPATCHED
    assert len(gh.dispatches) == 1
    assert "4711" in (tmp_path / "report.md").read_text(encoding="utf-8")


def test_an_undetectable_run_fails_loudly_instead_of_reporting_success() -> None:
    """Ein stiller Erfolg waere die schlimmste Variante: Der Dispatch kann
    gelaufen sein, ohne dass jemand den Lauf verlinkt bekommt."""
    gh = FakeGh([])
    with pytest.raises(rud.DispatchError, match="nicht auffindbar"):
        rud.await_dispatched_run(
            gh, repo=REPO, marker=MARKER, attempts=3, sleep=lambda _s: None,
        )
    assert len(gh.calls) == 3


def test_empty_target_issue_is_passed_through_instead_of_omitted(tmp_path: Path) -> None:
    """Weglassen liesse den Default 595 des Abnahme-Laufs greifen.

    Der Publish-Lauf sagt fuer den leeren Wert ausdruecklich "nur Artefakt und
    Job-Summary" zu. Wuerde das Feld weggelassen, kommentierte der ausgeloeste
    Lauf Abschlussmatrix und finale Instanz in Issue 595 - ein Schreibvorgang
    nach aussen, der aus einer Nicht-Angabe entsteht.
    """
    gh = FakeGh([[], [_run_entry()]])
    rud.run(
        repo=REPO, ref=REF, expected_sha=CANDIDATE_SHA, tag=TAG, candidate_run_id=CANDIDATE_RUN,
        predecessor_tag=PREDECESSOR, target_issue="", publish_run_id=PUBLISH_RUN,
        markdown=tmp_path / "report.md", runner=gh, sleep=lambda _s: None,
    )
    (dispatch,) = gh.dispatches
    assert "target_issue=" in dispatch, dispatch


# ── Ref-Prüfung nur vor einem echten Dispatch (#936-Review) ─────────────────


def test_the_ref_is_verified_before_dispatching(tmp_path: Path) -> None:
    """Der Ref wird gegen den Kandidaten-SHA geprüft, bevor der Lauf startet."""
    gh = FakeGh([[], [_run_entry()]])
    _invoke(gh, tmp_path)
    lookup, = gh.ref_lookups
    assert lookup == ["api", f"repos/{REPO}/git/ref/heads/{REF}"]
    assert gh.calls.index(lookup) < gh.calls.index(gh.dispatches[0])


def test_a_rerun_after_the_ref_was_deleted_stays_green(tmp_path: Path) -> None:
    """Nach Schritt 9 darf der Release-Ref gelöscht sein (ADR, Lebenszyklus).

    Ein Wiederanlauf des Publish-Laufs findet dann den vorhandenen
    Nachweislauf und dispatcht gar nicht — die Ref-Abfrage darf ihn nicht
    rot machen, nur weil eine Quelle fehlt, die niemand mehr braucht.
    """
    gh = FakeGh([[_run_entry(status="completed", conclusion="success")]], ref_payload=None)
    assert _invoke(gh, tmp_path) == rud.ACTION_ALREADY_PRESENT
    assert gh.ref_lookups == [], "Ref abgefragt, obwohl nicht dispatcht wurde"
    assert gh.dispatches == []


def test_a_missing_ref_blocks_a_real_dispatch_with_a_named_cause(tmp_path: Path) -> None:
    """Muss dispatcht werden, ist der fehlende Ref ein Abbruch – mit Weg heraus."""
    gh = FakeGh([[]], ref_payload=None)
    with pytest.raises(rud.DispatchError, match="nicht abrufbar"):
        _invoke(gh, tmp_path)
    assert gh.dispatches == []


def test_a_ref_that_moved_off_the_candidate_blocks_the_dispatch(tmp_path: Path) -> None:
    """Dieselbe Regel wie vor jedem manuellen Dispatch – aus dem Vertrag, nicht kopiert."""
    moved = {"ref": f"refs/heads/{REF}", "object": {"type": "commit", "sha": "d" * 40}}
    gh = FakeGh([[]], ref_payload=moved)
    with pytest.raises(rud.DispatchError, match="nicht verwendbar"):
        _invoke(gh, tmp_path)
    assert gh.dispatches == []


def test_cli_reports_failures_as_exit_two(tmp_path: Path, capsys) -> None:
    code = rud.main([
        "--repo", REPO, "--ref", REF, "--expected-sha", CANDIDATE_SHA, "--tag", "kaputt",
        "--candidate-run-id", CANDIDATE_RUN, "--publish-run-id", PUBLISH_RUN,
        "--markdown", str(tmp_path / "report.md"),
    ])
    assert code == 2
    assert "FEHLER" in capsys.readouterr().err
