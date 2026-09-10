"""Owner-Skript für die Release-Dispatches (#1039).

``gh``, ``git``/``python`` und ``gh run watch`` sind injiziert, damit
Korrelation, Wiederanlauf, Zustandsbindung und Abbruchbedingungen ohne Netz
und ohne GitHub prüfbar sind – dasselbe Muster wie in
``tests/test_release_update_dispatch.py``.

Geprüft wird die Regel, nicht die Ausgabe: Jeder Test bildet genau eine
Zusicherung aus dem Issue ab (race-sichere Korrelation samt Timeout und
Mehrdeutigkeit, Wiederaufnahme nach Abbruch zwischen Dispatch und Korrelation,
atomare und schema-validierte Zustandsdatei, Weitergabe von ``target_issue``,
Abbruch bei falschem Kandidaten-SHA oder fehlendem Ref-Schutz, Manifestname bei
``run_attempt`` 1 und 2, Ablehnung eines ``schedule``-Laufs als Kandidat,
Ablehnung vermischter Release-Zustände, ``finalize`` bis ``post-release``).
"""
from __future__ import annotations

import importlib.util
import json
import stat
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
# ``release_dispatch`` importiert ``release_contract``/``release_update_dispatch``
# über den Dateipfad-Zweig; dafür muss ``scripts/`` auf dem Suchpfad stehen.
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "release_dispatch", ROOT / "scripts" / "release_dispatch.py"
)
assert SPEC is not None and SPEC.loader is not None
rd = importlib.util.module_from_spec(SPEC)
sys.modules["release_dispatch"] = rd
SPEC.loader.exec_module(rd)

REPO = "NikolayDA/picture_helper"
VERSION = "2.9.1"
TAG = f"v{VERSION}"
REF = f"release/{TAG}"
SHA = "a" * 40
OTHER_SHA = "b" * 40
ISSUE = "595"
CANDIDATE_RUN = 4242
ACCEPTANCE_RUN = 5353
PUBLISH_RUN = 6464
UPDATE_RUN = 7575

#: Alles nach dieser Zeit gilt als „neu"; die Fixtures liegen weit dahinter.
LATER = "2099-01-01T00:00:00Z"
EARLIER = "2000-01-01T00:00:00Z"


def run_entry(
    run_id: int,
    *,
    event: str = "workflow_dispatch",
    head_sha: str = SHA,
    branch: str = REF,
    created_at: str = LATER,
    title: str = "",
) -> dict[str, Any]:
    return {
        "databaseId": run_id,
        "displayTitle": title,
        "status": "completed",
        "conclusion": "success",
        "url": f"https://github.com/{REPO}/actions/runs/{run_id}",
        "createdAt": created_at,
        "headSha": head_sha,
        "headBranch": branch,
        "event": event,
    }


def api_run(run_id: int, *, workflow: str, attempt: int = 1, event: str = "workflow_dispatch",
            head_sha: str = SHA) -> dict[str, Any]:
    """Antwort von ``gh api repos/…/actions/runs/<id>`` – die Form, die
    ``release_contract.validate_workflow_run`` liest."""
    return {
        "id": run_id,
        "path": workflow,
        "event": event,
        "status": "completed",
        "conclusion": "success",
        "head_sha": head_sha,
        "run_attempt": attempt,
    }


class FakeGh:
    """Beantwortet ``gh``-Aufrufe aus vorbereiteten Nutzlasten.

    Die Laufliste bildet die Wirklichkeit nach, statt eine Warteschlange
    abzuspulen: ``pre_runs`` existiert von Anfang an, ``post_runs`` erst,
    nachdem ein ``gh workflow run`` gelaufen ist. Genau diese Unterscheidung
    trägt die Korrelations- und Wiederanlauftests – ein Lauf, den es vor dem
    Dispatch schon gab, darf nie als "der eben ausgelöste" gelten.
    """

    def __init__(
        self,
        *,
        pre_runs: list[dict[str, Any]] | None = None,
        post_runs: list[dict[str, Any]] | None = None,
        ref_sha: str | None = SHA,
        rules: list[dict[str, str]] | str | None = None,
        api_runs: dict[int, dict[str, Any]] | None = None,
        artifacts: dict[int, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.pre_runs = pre_runs or []
        self.post_runs = post_runs or []
        self.ref_sha = ref_sha
        self.rules = (
            rules
            if rules is not None
            else [{"type": t} for t in ("deletion", "non_fast_forward", "update")]
        )
        self.api_runs = api_runs or {}
        self.artifacts = artifacts or {}
        self.calls: list[list[str]] = []

    def __call__(self, args: Sequence[str]) -> str:
        self.calls.append(list(args))
        if args[:2] == ["run", "list"]:
            visible = list(self.pre_runs)
            if self.dispatches:
                visible += self.post_runs
            return json.dumps(visible)
        if args[:1] == ["api"]:
            return self._api(args[1])
        if args[:2] in (["workflow", "run"], ["run", "download"]):
            return ""
        raise AssertionError(f"unerwarteter gh-Aufruf: {list(args)}")

    def _api(self, path: str) -> str:
        if path.startswith(f"repos/{REPO}/rules/branches/"):
            return json.dumps(self.rules)
        if path.startswith(f"repos/{REPO}/git/ref/heads/"):
            if self.ref_sha is None:
                raise rd.DispatchError("gh api scheiterte (Exit 1): Not Found")
            ref = path.split("/heads/", 1)[1]
            return json.dumps(
                {"ref": f"refs/heads/{ref}", "object": {"type": "commit", "sha": self.ref_sha}}
            )
        if path.endswith("/artifacts?per_page=100"):
            run_id = int(path.rsplit("/runs/", 1)[1].split("/", 1)[0])
            return json.dumps({"artifacts": self.artifacts.get(run_id, [])})
        if "/actions/runs/" in path:
            run_id = int(path.rsplit("/runs/", 1)[1])
            payload = self.api_runs.get(run_id)
            assert payload is not None, f"kein Fixture für Lauf {run_id}"
            return json.dumps(payload)
        raise AssertionError(f"unerwarteter gh-api-Pfad: {path}")

    @property
    def dispatches(self) -> list[list[str]]:
        return [c for c in self.calls if c[:2] == ["workflow", "run"]]

    def dispatch_input(self, index: int, key: str) -> str:
        args = self.dispatches[index]
        for flag, value in zip(args, args[1:], strict=False):
            if flag == "-f" and value.startswith(f"{key}="):
                return value.split("=", 1)[1]
        raise AssertionError(f"Eingabe {key!r} fehlt im Dispatch {index}: {args}")


def make_context(
    tmp_path: Path,
    gh: FakeGh,
    *,
    watch_code: int = 0,
    commands: list[list[str]] | None = None,
    confirm: str = TAG,
) -> rd.Context:
    sink = commands if commands is not None else []

    def command(argv: Sequence[str]) -> bytes:
        sink.append(list(argv))
        return b""

    return rd.Context(
        runner=gh,
        command=command,
        watcher=lambda _run_id: watch_code,
        state_path=tmp_path / "state.json",
        repo_dir=ROOT,
        echo=lambda _message: None,
        sleep=lambda _seconds: None,
        confirm=lambda _prompt: confirm,
    )


def seeded_state(tmp_path: Path, **overrides: Any) -> rd.ReleaseState:
    fields: dict[str, Any] = {
        "repo": REPO, "version": VERSION, "candidate_sha": SHA, "release_issue": ISSUE
    }
    fields.update(overrides)
    state = rd.ReleaseState(**fields)
    rd.save_state(tmp_path / "state.json", state)
    return state


# ── Zustandsdatei ──────────────────────────────────────────────────────


def test_state_roundtrip_is_atomic_restrictive_and_schema_checked(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    rd.save_state(path, rd.ReleaseState(REPO, VERSION, SHA, ISSUE, candidate_run_id=CANDIDATE_RUN))
    assert stat.S_IMODE(path.stat().st_mode) == rd.STATE_MODE
    loaded = rd.load_state(path)
    assert loaded is not None
    assert (loaded.repo, loaded.tag, loaded.ref) == (REPO, TAG, REF)
    assert loaded.candidate_run_id == CANDIDATE_RUN
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"] == rd.STATE_SCHEMA and payload["kind"] == rd.STATE_KIND


@pytest.mark.parametrize(
    "mutation",
    [
        {"schema": 99},
        {"kind": "etwas-anderes"},
        {"candidate_sha": "kurz"},
        {"version": "2.9"},
        {"release_ref": "release/v9.9.9"},
        {"candidate_run_id": 0},
    ],
    ids=["schema", "kind", "sha", "version", "ref-drift", "run-id"],
)
def test_corrupt_or_foreign_state_is_fail_closed(tmp_path: Path, mutation: dict) -> None:
    path = tmp_path / "state.json"
    rd.save_state(path, rd.ReleaseState(REPO, VERSION, SHA, ISSUE))
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(mutation)
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(rd.DispatchError):
        rd.load_state(path)


def test_missing_state_is_not_an_error_but_absence(tmp_path: Path) -> None:
    assert rd.load_state(tmp_path / "fehlt.json") is None


def test_default_state_path_is_outside_the_worktree(monkeypatch: pytest.MonkeyPatch) -> None:
    """Im Repository wäre die Datei ein unbekannter Pfad für das Freeze-Gate."""
    monkeypatch.setenv("XDG_STATE_HOME", "/tmp/zustand")
    path = rd.default_state_path()
    assert path == Path("/tmp/zustand/bgremover/release-dispatch.json")
    assert ROOT not in path.parents


# ── Korrelation ────────────────────────────────────────────────────────


def test_correlation_accepts_only_a_new_matching_dispatch_run() -> None:
    runs = [
        run_entry(1),                                    # vor dem Dispatch bekannt
        run_entry(2, event="schedule"),                  # Dry-Run (#922)
        run_entry(3, head_sha=OTHER_SHA),                # anderer Commit
        run_entry(4, branch="main"),                     # anderer Ref
        run_entry(5, created_at=EARLIER),                # zu alt
        run_entry(6),                                    # der gesuchte
    ]
    matches = rd.select_new_runs(
        runs,
        known=[1],
        ref=REF,
        expected_head_sha=SHA,
        not_before=rd.parse_github_timestamp("2098-01-01T00:00:00Z", field="t"),
    )
    assert [m.run_id for m in matches] == [6]


def test_scheduled_dry_run_is_never_a_candidate() -> None:
    """AK: Der monatliche Dry-Run wird per Korrelation nicht gefunden (#922)."""
    matches = rd.select_new_runs(
        [run_entry(9, event="schedule")],
        known=[],
        ref=REF,
        expected_head_sha=SHA,
        not_before=rd.parse_github_timestamp(EARLIER, field="t"),
    )
    assert matches == []


def test_marker_bound_correlation_uses_the_shared_boundary_rule() -> None:
    marker = rd.acceptance_marker(tag=TAG, candidate_run_id=CANDIDATE_RUN)
    longer = f"{marker}0"
    matches = rd.select_new_runs(
        [run_entry(11, title=f"Release-Abnahme alle [{longer}]"), run_entry(12, title=f"[{marker}]")],
        known=[],
        ref=REF,
        expected_head_sha=SHA,
        not_before=rd.parse_github_timestamp(EARLIER, field="t"),
        marker=marker,
    )
    assert [m.run_id for m in matches] == [12]


def test_ambiguous_correlation_aborts_instead_of_guessing(tmp_path: Path) -> None:
    gh = FakeGh(pre_runs=[run_entry(20), run_entry(21)])
    pending = rd.PendingDispatch(
        operation=rd.OP_CANDIDATE,
        workflow=rd.BUILD_WORKFLOW,
        ref=REF,
        expected_head_sha=SHA,
        marker="",
        not_before=EARLIER,
        known_run_ids=(),
        recorded_at=EARLIER,
    )
    with pytest.raises(rd.DispatchError, match="Mehrdeutig"):
        rd.await_new_run(gh, repo=REPO, pending=pending, attempts=1, sleep=lambda _s: None)


def test_correlation_timeout_returns_none_instead_of_raising(tmp_path: Path) -> None:
    """Der Aufrufer entscheidet: erneut dispatchen (Versöhnung) oder abbrechen."""
    gh = FakeGh()
    pending = rd.PendingDispatch(
        operation=rd.OP_CANDIDATE,
        workflow=rd.BUILD_WORKFLOW,
        ref=REF,
        expected_head_sha=SHA,
        marker="",
        not_before=EARLIER,
        known_run_ids=(),
        recorded_at=EARLIER,
    )
    assert rd.await_new_run(gh, repo=REPO, pending=pending, attempts=3, sleep=lambda _s: None) is None
    assert len([c for c in gh.calls if c[:2] == ["run", "list"]]) == 3


# ── candidate ──────────────────────────────────────────────────────────


def _candidate_gh(**overrides: Any) -> FakeGh:
    defaults: dict[str, Any] = {
        "post_runs": [run_entry(CANDIDATE_RUN)],
        "api_runs": {CANDIDATE_RUN: api_run(CANDIDATE_RUN, workflow=".github/workflows/release-linux.yml")},
    }
    defaults.update(overrides)
    return FakeGh(**defaults)


def test_candidate_checks_protection_and_ref_before_dispatching(tmp_path: Path) -> None:
    gh = _candidate_gh()
    state = rd.cmd_candidate(
        make_context(tmp_path, gh),
        repo=REPO, version=VERSION, candidate_sha=SHA, target_issue=ISSUE,
    )
    api_paths = [c[1] for c in gh.calls if c[:1] == ["api"]]
    dispatch_index = next(i for i, c in enumerate(gh.calls) if c[:2] == ["workflow", "run"])
    checks = [i for i, c in enumerate(gh.calls) if c[:1] == ["api"] and i < dispatch_index]
    assert len(checks) == 2, "Ruleset- und Ref-Prüfung müssen vor dem Dispatch liegen"
    assert any("rules/branches" in p for p in api_paths)
    assert any("git/ref/heads" in p for p in api_paths)
    assert gh.dispatch_input(0, "with_ai") == "true"
    assert state.candidate_run_id == CANDIDATE_RUN
    assert rd.load_state(tmp_path / "state.json").pending is None


def test_candidate_aborts_on_a_ref_pointing_elsewhere(tmp_path: Path) -> None:
    gh = _candidate_gh(ref_sha=OTHER_SHA)
    with pytest.raises(rd.DispatchError, match="Release-Ref"):
        rd.cmd_candidate(
            make_context(tmp_path, gh),
            repo=REPO, version=VERSION, candidate_sha=SHA, target_issue=ISSUE,
        )
    assert gh.dispatches == []


def test_candidate_aborts_without_ref_protection(tmp_path: Path) -> None:
    gh = _candidate_gh(rules=[])
    with pytest.raises(rd.DispatchError, match="Ref-Schutz"):
        rd.cmd_candidate(
            make_context(tmp_path, gh),
            repo=REPO, version=VERSION, candidate_sha=SHA, target_issue=ISSUE,
        )
    assert gh.dispatches == []


def test_candidate_rejects_a_state_from_another_release(tmp_path: Path) -> None:
    seeded_state(tmp_path)
    gh = _candidate_gh()
    with pytest.raises(rd.DispatchError, match="nicht gemischt"):
        rd.cmd_candidate(
            make_context(tmp_path, gh),
            repo=REPO, version="2.9.2", candidate_sha=OTHER_SHA, target_issue=ISSUE,
        )
    assert gh.dispatches == []


def test_candidate_rejects_a_run_that_is_not_a_workflow_dispatch(tmp_path: Path) -> None:
    """Zweite, unabhängige Schranke: der Freigabevertrag selbst (#922)."""
    gh = _candidate_gh(
        api_runs={
            CANDIDATE_RUN: api_run(
                CANDIDATE_RUN, workflow=".github/workflows/release-linux.yml", event="schedule"
            )
        }
    )
    with pytest.raises(rd.DispatchError, match="workflow_dispatch"):
        rd.cmd_candidate(
            make_context(tmp_path, gh),
            repo=REPO, version=VERSION, candidate_sha=SHA, target_issue=ISSUE,
        )


def test_candidate_reports_a_red_run_instead_of_continuing(tmp_path: Path) -> None:
    gh = _candidate_gh()
    with pytest.raises(rd.DispatchError, match="nicht erfolgreich beendet"):
        rd.cmd_candidate(
            make_context(tmp_path, gh, watch_code=1),
            repo=REPO, version=VERSION, candidate_sha=SHA, target_issue=ISSUE,
        )


@pytest.mark.parametrize(
    ("version", "sha", "issue"),
    [("2.9", SHA, ISSUE), (VERSION, "kurz", ISSUE), (VERSION, SHA, "keine")],
    ids=["version", "sha", "issue"],
)
def test_candidate_validates_its_inputs(tmp_path: Path, version: str, sha: str, issue: str) -> None:
    gh = _candidate_gh()
    with pytest.raises(rd.DispatchError):
        rd.cmd_candidate(
            make_context(tmp_path, gh), repo=REPO, version=version,
            candidate_sha=sha, target_issue=issue,
        )
    assert gh.dispatches == []


# ── Wiederanlauf zwischen Dispatch und Korrelation ─────────────────────


def test_resume_after_crash_between_dispatch_and_correlation_adopts_the_run(
    tmp_path: Path,
) -> None:
    """AK: Ein Abbruch nach dem Dispatch führt beim Wiederanlauf zu **keinem** zweiten Lauf."""
    seeded_state(
        tmp_path,
        pending=rd.PendingDispatch(
            operation=rd.OP_CANDIDATE,
            workflow=rd.BUILD_WORKFLOW,
            ref=REF,
            expected_head_sha=SHA,
            marker="",
            not_before=EARLIER,
            known_run_ids=(1,),
            recorded_at=EARLIER,
        ),
    )
    gh = _candidate_gh(pre_runs=[run_entry(1, created_at=EARLIER), run_entry(CANDIDATE_RUN)],
                       post_runs=[])
    state = rd.cmd_candidate(
        make_context(tmp_path, gh),
        repo=REPO, version=VERSION, candidate_sha=SHA, target_issue=ISSUE,
    )
    assert gh.dispatches == [], "der Wiederanlauf darf nicht erneut dispatchen"
    assert state.candidate_run_id == CANDIDATE_RUN
    assert rd.load_state(tmp_path / "state.json").pending is None


def test_resume_redispatches_only_when_no_run_exists(tmp_path: Path) -> None:
    seeded_state(
        tmp_path,
        pending=rd.PendingDispatch(
            operation=rd.OP_CANDIDATE,
            workflow=rd.BUILD_WORKFLOW,
            ref=REF,
            expected_head_sha=SHA,
            marker="",
            not_before=EARLIER,
            known_run_ids=(),
            recorded_at=EARLIER,
        ),
    )
    gh = _candidate_gh()
    state = rd.cmd_candidate(
        make_context(tmp_path, gh),
        repo=REPO, version=VERSION, candidate_sha=SHA, target_issue=ISSUE,
    )
    assert len(gh.dispatches) == 1
    assert state.candidate_run_id == CANDIDATE_RUN


def test_a_pending_dispatch_of_another_operation_blocks(tmp_path: Path) -> None:
    seeded_state(
        tmp_path,
        candidate_run_id=CANDIDATE_RUN,
        pending=rd.PendingDispatch(
            operation=rd.OP_PUBLISH,
            workflow=rd.PUBLISH_WORKFLOW,
            ref=REF,
            expected_head_sha=SHA,
            marker="",
            not_before=EARLIER,
            known_run_ids=(),
            recorded_at=EARLIER,
        ),
    )
    gh = FakeGh(api_runs={
        CANDIDATE_RUN: api_run(CANDIDATE_RUN, workflow=".github/workflows/release-linux.yml")
    })
    with pytest.raises(rd.DispatchError, match="Offener Dispatch der Operation"):
        rd.cmd_acceptance(make_context(tmp_path, gh), repo=REPO)
    assert gh.dispatches == []


def test_the_pending_entry_is_written_before_the_dispatch(tmp_path: Path) -> None:
    """Ohne diese Reihenfolge erzeugt ein Absturz im Fenster einen zweiten Lauf."""
    order: list[str] = []
    gh = _candidate_gh()
    inner = gh.__call__

    def watching(args: Sequence[str]) -> str:
        if args[:2] == ["workflow", "run"]:
            order.append("dispatch")
            payload = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
            assert payload["pending"] is not None, "pending fehlt zum Dispatch-Zeitpunkt"
            order.append("pending-vorhanden")
        return inner(args)

    ctx = make_context(tmp_path, gh)
    rd.cmd_candidate(
        rd.Context(
            runner=watching, command=ctx.command, watcher=ctx.watcher,
            state_path=ctx.state_path, repo_dir=ctx.repo_dir, echo=ctx.echo,
            sleep=ctx.sleep, confirm=ctx.confirm,
        ),
        repo=REPO, version=VERSION, candidate_sha=SHA, target_issue=ISSUE,
    )
    assert order == ["dispatch", "pending-vorhanden"]


# ── acceptance ─────────────────────────────────────────────────────────


def _acceptance_gh(*, attempt: int = 1, artifacts: list[dict[str, Any]] | None = None) -> FakeGh:
    marker = rd.acceptance_marker(tag=TAG, candidate_run_id=CANDIDATE_RUN)
    return FakeGh(
        post_runs=[run_entry(ACCEPTANCE_RUN, title=f"Release-Abnahme alle [{marker}]")],
        api_runs={
            CANDIDATE_RUN: api_run(
                CANDIDATE_RUN, workflow=".github/workflows/release-linux.yml"
            ),
            ACCEPTANCE_RUN: api_run(
                ACCEPTANCE_RUN, workflow=".github/workflows/release-abnahme.yml", attempt=attempt
            ),
        },
        artifacts={
            ACCEPTANCE_RUN: artifacts
            if artifacts is not None
            else [{"name": f"release-approval-manifest-{attempt}", "expired": False}]
        },
    )


def test_acceptance_binds_issue_marker_and_manifest_name(tmp_path: Path) -> None:
    seeded_state(tmp_path, candidate_run_id=CANDIDATE_RUN)
    gh = _acceptance_gh()
    state = rd.cmd_acceptance(make_context(tmp_path, gh), repo=REPO)
    assert gh.dispatch_input(0, "run_id") == str(CANDIDATE_RUN)
    assert gh.dispatch_input(0, "platforms") == "alle"
    assert gh.dispatch_input(0, "dry_run") == "false"
    assert gh.dispatch_input(0, "target_issue") == ISSUE
    assert gh.dispatch_input(0, "dispatch_marker") == rd.acceptance_marker(
        tag=TAG, candidate_run_id=CANDIDATE_RUN
    )
    assert state.acceptance_run_id == ACCEPTANCE_RUN
    assert state.approval_artifact_name == "release-approval-manifest-1"


@pytest.mark.parametrize("attempt", [1, 2], ids=["attempt-1", "attempt-2"])
def test_manifest_name_follows_the_current_run_attempt(tmp_path: Path, attempt: int) -> None:
    """Ein Wiederanlauf desselben Laufs legt ein zweites Manifest ab (#1039)."""
    seeded_state(tmp_path, candidate_run_id=CANDIDATE_RUN)
    gh = _acceptance_gh(
        attempt=attempt,
        artifacts=[
            {"name": "release-approval-manifest-1", "expired": False},
            {"name": "release-approval-manifest-2", "expired": False},
        ],
    )
    state = rd.cmd_acceptance(make_context(tmp_path, gh), repo=REPO)
    assert state.approval_artifact_name == f"release-approval-manifest-{attempt}"


def test_an_expired_manifest_is_not_accepted(tmp_path: Path) -> None:
    seeded_state(tmp_path, candidate_run_id=CANDIDATE_RUN)
    gh = _acceptance_gh(artifacts=[{"name": "release-approval-manifest-1", "expired": True}])
    with pytest.raises(rd.DispatchError, match="genau ein nicht abgelaufenes Artefakt"):
        rd.cmd_acceptance(make_context(tmp_path, gh), repo=REPO)


def test_acceptance_needs_a_candidate_run_and_an_issue(tmp_path: Path) -> None:
    seeded_state(tmp_path)
    with pytest.raises(rd.DispatchError, match="Kandidaten-Run-ID"):
        rd.cmd_acceptance(make_context(tmp_path, FakeGh()), repo=REPO)
    seeded_state(tmp_path, candidate_run_id=CANDIDATE_RUN, release_issue="")
    with pytest.raises(rd.DispatchError, match="release_issue"):
        rd.cmd_acceptance(make_context(tmp_path, FakeGh()), repo=REPO)


def test_a_state_of_another_repository_is_refused(tmp_path: Path) -> None:
    seeded_state(tmp_path, candidate_run_id=CANDIDATE_RUN)
    with pytest.raises(rd.DispatchError, match="gehoert zu"):
        rd.cmd_acceptance(make_context(tmp_path, FakeGh()), repo="fremd/repo")


# ── approve ────────────────────────────────────────────────────────────


def test_approve_uses_contract_and_checklist_of_the_candidate_revision(tmp_path: Path) -> None:
    seeded_state(
        tmp_path,
        candidate_run_id=CANDIDATE_RUN,
        acceptance_run_id=ACCEPTANCE_RUN,
        approval_artifact_name="release-approval-manifest-1",
    )
    commands: list[list[str]] = []
    work = tmp_path / "work"
    download = work / "approval"
    download.mkdir(parents=True)
    (download / "release-approval-manifest.json").write_text("{}", encoding="utf-8")

    def command(argv: Sequence[str]) -> bytes:
        commands.append(list(argv))
        if argv[:2] == ["git", "-C"]:
            return b"# Kandidatenrevision\n"
        if "extract-instance" in argv:
            Path(argv[argv.index("--output") + 1]).write_text(
                json.dumps({"criteria": [{"id": "BUILD-01", "phase": "pre-release",
                                          "requirement": "MUST", "status": "PASS"}]}),
                encoding="utf-8",
            )
        return b""

    gh = FakeGh()
    ctx = rd.Context(
        runner=gh, command=command, watcher=lambda _r: 0,
        state_path=tmp_path / "state.json", repo_dir=ROOT,
        echo=lambda _m: None, sleep=lambda _s: None, confirm=lambda _p: "",
    )
    rd.cmd_approve(ctx, repo=REPO, work_dir=work)

    shows = [c for c in commands if c[:2] == ["git", "-C"]]
    assert [c[-1] for c in shows] == [
        f"{SHA}:scripts/release_contract.py",
        f"{SHA}:docs/RELEASE_ACCEPTANCE_CHECKLIST.md",
    ]
    contract_calls = [c for c in commands if "release_contract.py" in " ".join(c)]
    assert any("extract-instance" in c for c in contract_calls)
    validate = next(c for c in contract_calls if "validate-instance" in c)
    assert validate[validate.index("--through-phase") + 1] == "pre-release"
    assert str(work / "candidate" / "RELEASE_ACCEPTANCE_CHECKLIST.md") in validate
    assert gh.dispatches == [], "approve löst nichts aus"


def test_approve_needs_an_acceptance_run_with_a_manifest_name(tmp_path: Path) -> None:
    seeded_state(tmp_path, candidate_run_id=CANDIDATE_RUN)
    with pytest.raises(rd.DispatchError, match="Manifestnamen"):
        rd.cmd_approve(make_context(tmp_path, FakeGh()), repo=REPO)


def test_find_payload_handles_both_download_layouts(tmp_path: Path) -> None:
    flat = tmp_path / "flat"
    (flat).mkdir()
    (flat / "release-approval-manifest.json").write_text("{}", encoding="utf-8")
    assert rd.find_payload(flat, "release-approval-manifest.json").parent == flat

    nested = tmp_path / "nested" / "release-approval-manifest-1"
    nested.mkdir(parents=True)
    (nested / "release-approval-manifest.json").write_text("{}", encoding="utf-8")
    assert rd.find_payload(tmp_path / "nested", "release-approval-manifest.json").parent == nested

    (flat / "zweit").mkdir()
    (flat / "zweit" / "release-approval-manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(rd.DispatchError, match="genau eine"):
        rd.find_payload(flat, "release-approval-manifest.json")


# ── publish ────────────────────────────────────────────────────────────


def _publish_state(tmp_path: Path) -> rd.ReleaseState:
    return seeded_state(
        tmp_path,
        candidate_run_id=CANDIDATE_RUN,
        acceptance_run_id=ACCEPTANCE_RUN,
        approval_artifact_name="release-approval-manifest-1",
    )


def _publish_gh() -> FakeGh:
    return FakeGh(post_runs=[run_entry(PUBLISH_RUN)])


def test_publish_passes_every_binding_value_and_the_issue(tmp_path: Path) -> None:
    _publish_state(tmp_path)
    gh = _publish_gh()
    state = rd.cmd_publish(
        make_context(tmp_path, gh), repo=REPO, predecessor_tag="v2.9.0", assume_yes=True
    )
    expected = {
        "tag": TAG,
        "candidate_run_id": str(CANDIDATE_RUN),
        "acceptance_run_id": str(ACCEPTANCE_RUN),
        "approval_artifact_name": "release-approval-manifest-1",
        "create_tag": "true",
        "predecessor_tag": "v2.9.0",
        "target_issue": ISSUE,
    }
    for key, value in expected.items():
        assert gh.dispatch_input(0, key) == value
    assert state.publish_run_id == PUBLISH_RUN
    assert state.predecessor_tag == "v2.9.0"


def test_publish_requires_the_typed_confirmation(tmp_path: Path) -> None:
    _publish_state(tmp_path)
    gh = _publish_gh()
    with pytest.raises(rd.DispatchError, match="Abgebrochen"):
        rd.cmd_publish(
            make_context(tmp_path, gh, confirm="ja"), repo=REPO, predecessor_tag="v2.9.0"
        )
    assert gh.dispatches == []


def test_publish_accepts_the_typed_tag_as_confirmation(tmp_path: Path) -> None:
    _publish_state(tmp_path)
    gh = _publish_gh()
    rd.cmd_publish(make_context(tmp_path, gh, confirm=TAG), repo=REPO, predecessor_tag="v2.9.0")
    assert len(gh.dispatches) == 1


@pytest.mark.parametrize("predecessor", ["2.9.0", "v2.9", TAG], ids=["kein-v", "unvollständig", "selbst"])
def test_publish_never_guesses_the_predecessor(tmp_path: Path, predecessor: str) -> None:
    _publish_state(tmp_path)
    gh = _publish_gh()
    with pytest.raises(rd.DispatchError):
        rd.cmd_publish(
            make_context(tmp_path, gh), repo=REPO, predecessor_tag=predecessor, assume_yes=True
        )
    assert gh.dispatches == []


def test_publish_refuses_an_incomplete_state(tmp_path: Path) -> None:
    seeded_state(tmp_path, candidate_run_id=CANDIDATE_RUN)
    gh = _publish_gh()
    with pytest.raises(rd.DispatchError, match="Unvollstaendiger Zustand"):
        rd.cmd_publish(
            make_context(tmp_path, gh), repo=REPO, predecessor_tag="v2.9.0", assume_yes=True
        )
    assert gh.dispatches == []


def test_publish_aborts_when_the_ref_moved(tmp_path: Path) -> None:
    _publish_state(tmp_path)
    gh = FakeGh(post_runs=[run_entry(PUBLISH_RUN)], ref_sha=OTHER_SHA)
    with pytest.raises(rd.DispatchError, match="Release-Ref"):
        rd.cmd_publish(
            make_context(tmp_path, gh), repo=REPO, predecessor_tag="v2.9.0", assume_yes=True
        )
    assert gh.dispatches == []


# ── finalize ───────────────────────────────────────────────────────────


def test_finalize_finds_the_update_run_by_marker_and_validates_post_release(
    tmp_path: Path,
) -> None:
    seeded_state(
        tmp_path,
        candidate_run_id=CANDIDATE_RUN,
        acceptance_run_id=ACCEPTANCE_RUN,
        approval_artifact_name="release-approval-manifest-1",
        publish_run_id=PUBLISH_RUN,
        predecessor_tag="v2.9.0",
    )
    marker = f"update-check:{TAG}:{CANDIDATE_RUN}"
    gh = FakeGh(pre_runs=[run_entry(UPDATE_RUN, title=f"Release-Abnahme alle [{marker}]")])
    work = tmp_path / "work"
    instance_dir = work / "instance" / "release-acceptance-instance-final-1"
    instance_dir.mkdir(parents=True)
    (instance_dir / "release-acceptance-instance.json").write_text(
        json.dumps({"criteria": [{"id": "UPDATE-LINUX-ARM-01", "phase": "post-release",
                                  "requirement": "POST_RELEASE", "status": "PASS"}]}),
        encoding="utf-8",
    )
    commands: list[list[str]] = []
    ctx = make_context(tmp_path, gh, commands=commands)
    state = rd.cmd_finalize(ctx, repo=REPO, work_dir=work)

    assert state.update_acceptance_run_id == UPDATE_RUN
    validate = next(c for c in commands if "validate-instance" in c)
    assert validate[validate.index("--through-phase") + 1] == "post-release"
    assert any(c[:2] == ["run", "download"] for c in gh.calls)
    assert gh.dispatches == [], "finalize löst nichts aus"


def test_finalize_reports_the_skipped_proof_instead_of_fabricating_it(tmp_path: Path) -> None:
    """Ohne `predecessor_tag` bleiben beide Update-Kriterien PENDING."""
    seeded_state(tmp_path, candidate_run_id=CANDIDATE_RUN, publish_run_id=PUBLISH_RUN)
    messages: list[str] = []
    gh = FakeGh()
    ctx = rd.Context(
        runner=gh, command=lambda _a: b"", watcher=lambda _r: 0,
        state_path=tmp_path / "state.json", repo_dir=ROOT,
        echo=messages.append, sleep=lambda _s: None, confirm=lambda _p: "",
    )
    state = rd.cmd_finalize(ctx, repo=REPO)
    assert state.update_acceptance_run_id is None
    assert gh.calls == [], "ohne Vorgänger wird nichts abgefragt"
    joined = " ".join(messages)
    assert "PENDING" in joined and "nicht auf PASS" in joined


def test_finalize_aborts_when_no_marked_run_exists(tmp_path: Path) -> None:
    seeded_state(
        tmp_path,
        candidate_run_id=CANDIDATE_RUN,
        publish_run_id=PUBLISH_RUN,
        predecessor_tag="v2.9.0",
    )
    gh = FakeGh()
    with pytest.raises(rd.DispatchError, match="Rueckfallweg"):
        rd.cmd_finalize(make_context(tmp_path, gh), repo=REPO)


def test_finalize_needs_a_publish_run(tmp_path: Path) -> None:
    seeded_state(tmp_path, candidate_run_id=CANDIDATE_RUN, predecessor_tag="v2.9.0")
    with pytest.raises(rd.DispatchError, match="Publish-Lauf"):
        rd.cmd_finalize(make_context(tmp_path, FakeGh()), repo=REPO)


# ── Sichtbarkeit und Wiederverwendung ──────────────────────────────────


def test_every_gh_call_is_printed_before_it_runs() -> None:
    """Der Owner muss jederzeit von Hand weitermachen können (#1039)."""
    printed: list[str] = []
    calls: list[list[str]] = []

    def runner(args: Sequence[str]) -> str:
        # Der Aufruf darf erst nach der Ausgabe passieren.
        assert printed and printed[-1].startswith("$ gh ")
        calls.append(list(args))
        return "[]"

    rd.traced(runner, echo=printed.append)(["run", "list", "--repo", REPO])
    assert printed == [f"$ gh run list --repo {REPO}"]
    assert calls == [["run", "list", "--repo", REPO]]


def test_marker_boundary_rule_comes_from_release_update_dispatch() -> None:
    """Keine zweite Kopie der Abgrenzung – sonst driftet genau der #943-Befund.

    Geprüft wird die Quelle, nicht die Objektidentität: Beide Skripte werden in
    dieser Suite über den Dateipfad geladen, und wer zuerst lädt, entscheidet
    über das Modulobjekt. Aussagekräftig ist, dass ``release_dispatch`` die
    Randregeln nicht selbst führt.
    """
    source = (ROOT / "scripts" / "release_dispatch.py").read_text(encoding="utf-8")
    assert "rud.marker_pattern(" in source, "die geteilte Abgrenzung wird nicht benutzt"
    for copied in ("(?<![0-9A-Za-z])", "(?![0-9])", "_MARKER_START", "_MARKER_END"):
        assert copied not in source, f"zweite Quelle der Markerabgrenzung: {copied!r}"

    marker = rd.acceptance_marker(tag=TAG, candidate_run_id=CANDIDATE_RUN)
    pattern = rd.rud.marker_pattern(marker)
    assert pattern.search(f"[{marker}]")
    assert not pattern.search(f"[{marker}0]")


def test_workflow_paths_match_the_release_contract_constants() -> None:
    """Handgepflegte Kopie gegen ihre Quelle: die Workflow-Pfade des Vertrags."""
    import release_contract as rc

    assert rd._WORKFLOW_PATHS[rd.BUILD_WORKFLOW] == rc.BUILD_WORKFLOW
    assert rd._WORKFLOW_PATHS[rd.ACCEPTANCE_WORKFLOW] == rc.ACCEPTANCE_WORKFLOW
    for name, path in rd._WORKFLOW_PATHS.items():
        assert (ROOT / path).is_file(), f"{name}: {path} existiert nicht"
        assert path.endswith(f"/{name}")


def test_candidate_sources_exist_and_are_the_pinned_pair() -> None:
    assert [source for source, _ in rd.CANDIDATE_SOURCES] == [
        "scripts/release_contract.py",
        "docs/RELEASE_ACCEPTANCE_CHECKLIST.md",
    ]
    for source, _ in rd.CANDIDATE_SOURCES:
        assert (ROOT / source).is_file(), source


# ── Wiederholungsaufruf nach abgebrochenem Beobachten ──────────────────


def test_a_correlated_candidate_run_is_reattached_not_dispatched_twice(tmp_path: Path) -> None:
    """Zweites Fenster: ``gh run watch`` bricht ab, die Run-ID steht schon.

    Ohne diese Sperre löste derselbe Befehl einen zweiten Kandidatenbau aus –
    genau das „alte und neue Run-ID mischen" der Wiederanlaufmatrix.
    """
    seeded_state(tmp_path, candidate_run_id=CANDIDATE_RUN)
    gh = _candidate_gh(pre_runs=[], post_runs=[run_entry(9999)])
    watched: list[int] = []
    ctx = make_context(tmp_path, gh)
    state = rd.cmd_candidate(
        rd.Context(
            runner=gh, command=ctx.command,
            watcher=lambda run_id: (watched.append(run_id), 0)[1],
            state_path=ctx.state_path, repo_dir=ctx.repo_dir, echo=ctx.echo,
            sleep=ctx.sleep, confirm=ctx.confirm,
        ),
        repo=REPO, version=VERSION, candidate_sha=SHA, target_issue=ISSUE,
    )
    assert gh.dispatches == []
    assert watched == [CANDIDATE_RUN]
    assert state.candidate_run_id == CANDIDATE_RUN


def test_a_correlated_acceptance_run_is_reattached_and_the_manifest_re_resolved(
    tmp_path: Path,
) -> None:
    seeded_state(tmp_path, candidate_run_id=CANDIDATE_RUN, acceptance_run_id=ACCEPTANCE_RUN)
    gh = _acceptance_gh(attempt=2, artifacts=[
        {"name": "release-approval-manifest-1", "expired": True},
        {"name": "release-approval-manifest-2", "expired": False},
    ])
    state = rd.cmd_acceptance(make_context(tmp_path, gh), repo=REPO)
    assert gh.dispatches == []
    assert state.approval_artifact_name == "release-approval-manifest-2"


def test_a_correlated_publish_run_is_reattached(tmp_path: Path) -> None:
    seeded_state(
        tmp_path,
        candidate_run_id=CANDIDATE_RUN,
        acceptance_run_id=ACCEPTANCE_RUN,
        approval_artifact_name="release-approval-manifest-1",
        publish_run_id=PUBLISH_RUN,
    )
    gh = _publish_gh()
    state = rd.cmd_publish(
        make_context(tmp_path, gh), repo=REPO, predecessor_tag="v2.9.0", assume_yes=True
    )
    assert gh.dispatches == []
    assert state.publish_run_id == PUBLISH_RUN


# ── Review #1067: die vier Bot-Befunde ─────────────────────────────────


def test_the_candidate_revision_lands_byte_identical(tmp_path: Path) -> None:
    """Befund 1: Die Instanz pinnt den SHA-256 der Checkliste – über **Bytes**.

    Ein Text-Kanal dekodierte den `git show`-Blob mit
    ``locale.getpreferredencoding`` und übersetzte Zeilenenden; unter
    ``LC_ALL=C`` wäre das entweder ein `UnicodeDecodeError` oder eine Datei,
    deren Hash nicht mehr zur Kandidatenrevision passt. Der Fehler fiele erst
    in Runbook-Schritt 6 auf und sähe wie ein inhaltlicher Drift aus.
    """
    #: Umlaute (Mehrbyte-UTF-8) und ein CRLF – beides überlebt einen
    #: Text-Kanal nicht unverändert.
    blob = "## Abnahme – Prüfung\r\nZeile\n".encode()
    delivered: dict[str, bytes] = {}

    def command(argv: Sequence[str]) -> bytes:
        return blob

    contract, checklist = rd.materialize_candidate_sources(
        command, repo_dir=ROOT, candidate_sha=SHA, target=tmp_path / "c"
    )
    for path in (contract, checklist):
        delivered[path.name] = path.read_bytes()
    assert delivered == {"release_contract.py": blob, "RELEASE_ACCEPTANCE_CHECKLIST.md": blob}
    import hashlib
    assert hashlib.sha256(checklist.read_bytes()).hexdigest() == hashlib.sha256(blob).hexdigest()


def test_the_real_command_channel_returns_raw_bytes(tmp_path: Path) -> None:
    """Der produktive Kanal selbst – sonst prüfte der Test oben nur sein Mock."""
    raw = rd._command([sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'\\xc3\\xa4\\r\\n')"])
    assert raw == b"\xc3\xa4\r\n"


def test_a_deliberately_empty_predecessor_is_a_reachable_state(tmp_path: Path) -> None:
    """Befund 2: ``release-publish.yml`` führt ``predecessor_tag`` als optional.

    Ohne diesen Weg wäre der Überspringen-Zweig in ``finalize`` über die eigenen
    Kommandos unerreichbar – er stünde nur in der Doku.
    """
    _publish_state(tmp_path)
    gh = _publish_gh()
    messages: list[str] = []
    ctx = make_context(tmp_path, gh)
    state = rd.cmd_publish(
        rd.Context(
            runner=gh, command=ctx.command, watcher=ctx.watcher, state_path=ctx.state_path,
            repo_dir=ctx.repo_dir, echo=messages.append, sleep=ctx.sleep, confirm=ctx.confirm,
        ),
        repo=REPO, predecessor_tag="", assume_yes=True,
    )
    assert gh.dispatch_input(0, "predecessor_tag") == ""
    assert state.predecessor_tag == ""
    # Die Bestätigungsanzeige sagt ausdrücklich, was das bedeutet.
    joined = " ".join(messages)
    assert "keiner" in joined and "PENDING" in joined

    # ... und der finalize-Zweig ist damit über die eigenen Kommandos erreichbar.
    quiet: list[str] = []
    rd.cmd_finalize(
        rd.Context(
            runner=FakeGh(), command=ctx.command, watcher=ctx.watcher,
            state_path=ctx.state_path, repo_dir=ctx.repo_dir, echo=quiet.append,
            sleep=ctx.sleep, confirm=ctx.confirm,
        ),
        repo=REPO,
    )
    assert "nicht auf PASS" in " ".join(quiet)


def test_omitting_the_predecessor_is_not_the_same_as_skipping_it() -> None:
    """Vergessen und Verzichten dürfen nicht dasselbe Kommando sein."""
    with pytest.raises(SystemExit):
        rd._parser().parse_args(["publish"])
    assert rd._parser().parse_args(["publish", "--predecessor", ""]).predecessor == ""


def test_a_foreign_dispatch_error_becomes_a_named_abort(tmp_path: Path) -> None:
    """Befund 3: ``release_update_dispatch`` wirft seine **eigene** Fehlerklasse.

    Sie entkäme dem ``except DispatchError`` in ``main`` und endete als
    Traceback mit Exit 1 – ausgerechnet in Schritt 9.
    """
    seeded_state(
        tmp_path,
        candidate_run_id=CANDIDATE_RUN,
        publish_run_id=PUBLISH_RUN,
        predecessor_tag="v2.9.0",
    )

    class BrokenListing(FakeGh):
        def __call__(self, args: Sequence[str]) -> str:
            if args[:2] == ["run", "list"]:
                return '{"kein": "array"}'  # rud.DispatchError: "Laufliste ist keine Liste"
            return super().__call__(args)

    with pytest.raises(rd.DispatchError, match="Suche nach dem Update-Abnahmelauf"):
        rd.cmd_finalize(make_context(tmp_path, BrokenListing()), repo=REPO)

    class BrokenJson(FakeGh):
        def __call__(self, args: Sequence[str]) -> str:
            if args[:2] == ["run", "list"]:
                return "{kaputt"
            return super().__call__(args)

    with pytest.raises(rd.DispatchError, match="Suche nach dem Update-Abnahmelauf"):
        rd.cmd_finalize(make_context(tmp_path, BrokenJson()), repo=REPO)


def test_main_turns_every_named_abort_into_exit_2(tmp_path: Path, capsys) -> None:
    """Der Vertrag des Moduls: benannter Abbruch, nie ein Traceback."""
    code = rd.main(["--state-file", str(tmp_path / "fehlt.json"), "acceptance"])
    assert code == 2
    assert "FEHLER:" in capsys.readouterr().err


def test_acceptance_refuses_a_failed_candidate_run_before_the_hardware(tmp_path: Path) -> None:
    """Befund 4: Ein roter Kandidatenbau lässt seine Run-ID im Zustand zurück.

    Dispatcht der Owner danach von Hand neu, kennt der Zustand die neue ID
    nicht. Ohne diese Vorprüfung ginge die alte, gescheiterte in die Abnahme –
    fail-closed erst nach einem vollständigen Anlauf auf echter Hardware.
    """
    seeded_state(tmp_path, candidate_run_id=CANDIDATE_RUN)
    failed = api_run(CANDIDATE_RUN, workflow=".github/workflows/release-linux.yml")
    failed["conclusion"] = "failure"
    gh = FakeGh(api_runs={CANDIDATE_RUN: failed})
    with pytest.raises(rd.DispatchError, match="kein gueltiger release-linux.yml-Lauf"):
        rd.cmd_acceptance(make_context(tmp_path, gh), repo=REPO)
    assert gh.dispatches == []


def test_a_red_candidate_run_names_the_state_file_in_its_error(tmp_path: Path) -> None:
    """Der Fehlertext muss sagen, dass ein neuer Bau die Zustandsdatei betrifft."""
    gh = _candidate_gh()
    with pytest.raises(rd.DispatchError, match="--state-file"):
        rd.cmd_candidate(
            make_context(tmp_path, gh, watch_code=1),
            repo=REPO, version=VERSION, candidate_sha=SHA, target_issue=ISSUE,
        )


def test_pending_run_ids_reject_booleans_like_the_state_fields(tmp_path: Path) -> None:
    with pytest.raises(rd.DispatchError, match="positiver Ganzzahlen"):
        rd.PendingDispatch.from_json({
            "operation": "candidate", "workflow": "w", "ref": REF,
            "expected_head_sha": SHA, "marker": "", "not_before": EARLIER,
            "known_run_ids": [True], "recorded_at": EARLIER,
        })
