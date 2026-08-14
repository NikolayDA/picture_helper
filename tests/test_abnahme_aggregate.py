"""Tests der Evidenz-Aggregation und Abschlussmatrix (#646)."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "abnahme_aggregate", ROOT / "scripts" / "abnahme_aggregate.py"
)
assert _SPEC is not None and _SPEC.loader is not None
agg = importlib.util.module_from_spec(_SPEC)
sys.modules["abnahme_aggregate"] = agg
_SPEC.loader.exec_module(agg)


def _evidence(platform: str, status: str = "bestanden", **extra: object) -> dict:
    base = {
        "schema": 1, "kind": "abnahme-evidenz", "platform": platform, "status": status,
        "commit_sha": "abc", "quelle": {"art": "release-tag", "wert": "v2.7.0"},
        "artefakte": [], "umgebung": {}, "erzeugt_am": "2026-07-21T00:00:00+00:00",
        "gl_provenance": "Broadcom / V3D 7.1 / 3.1",
        "waechter_ergebnisse": [
            {
                "phase": "start", "artefaktklasse": "appimage", "exit_code": 0,
                "peak_instanzen": 1, "status": "ok", "log": "smoke_launch OK",
            },
        ],
        "hinweise": [],
    }
    base.update(extra)
    return base


def _write(root: Path, platform: str, data: dict) -> None:
    d = root / f"abnahme-{platform}"
    d.mkdir(parents=True)
    (d / "evidenz.json").write_text(json.dumps(data), encoding="utf-8")


def _e2e(platform: str, **extra: object) -> dict:
    base = {
        "schema": 1, "kind": "abnahme-e2e", "platform": platform,
        "status": "bestanden", "scenario": "open->height->3d->op->undo/redo->save/open",
        "commit_sha": "abc", "native_3d_required": True, "native_3d_state": "ready",
        "erzeugt_am": "2026-07-21T00:00:00+00:00", "hinweise": [],
    }
    base.update(extra)
    return base


def _live_gl(platform: str, **extra: object) -> dict:
    metrics = {name: 1.0 for name in agg.LIVE_GL_METRICS}
    base = {
        "schema": 3, "suite": "preview3d-live", "platform": platform,
        "git_commit": "abc",
        "environment": {"gl_provenance": "Broadcom / V3D 7.1 / 3.1"},
        "formats": {scenario: dict(metrics) for scenario in agg.LIVE_GL_SCENARIOS},
    }
    base.update(extra)
    return base


def _complete_aux(*platforms: str) -> tuple[dict[str, dict], dict[str, dict]]:
    return (
        {platform: _e2e(platform) for platform in platforms},
        {platform: _live_gl(platform) for platform in platforms},
    )


def test_validate_evidence_reports_missing_fields() -> None:
    assert agg.validate_evidence(_evidence("linux-arm64")) == []
    broken = _evidence("linux-arm64")
    del broken["commit_sha"]
    del broken["umgebung"]
    assert set(agg.validate_evidence(broken)) == {"commit_sha", "umgebung"}


def test_validate_evidence_requires_nonempty_gl_provenance() -> None:
    broken = _evidence("linux-arm64", gl_provenance=None)
    assert "gl_provenance leer" in agg.validate_evidence(broken)


def test_validate_evidence_requires_nonempty_waechter_ergebnisse() -> None:
    # #642-Nachtrag: eine "bestandene" Evidenz ohne strukturierte
    # Wächter-Ergebnisse ist kein vollständiger Nachweis mehr.
    broken = _evidence("linux-arm64", waechter_ergebnisse=[])
    assert "waechter_ergebnisse leer" in agg.validate_evidence(broken)
    # Der Platzhalter-Status ist von der Pflicht ausgenommen (noch kein Smoke gelaufen).
    placeholder = _evidence("linux-arm64", status="platzhalter", waechter_ergebnisse=[])
    assert "waechter_ergebnisse leer" not in agg.validate_evidence(placeholder)


def test_matrix_all_passed(tmp_path: Path) -> None:
    _write(tmp_path, "macos-arm64", _evidence("macos-arm64"))
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    e2e, live_gl = _complete_aux("macos-arm64", "linux-arm64")
    rows = agg.build_matrix(
        agg.load_evidence(tmp_path), e2e=e2e, live_gl=live_gl,
    )
    by = {r.kriterium: r.status for r in rows}
    assert by[agg.EXPECTED_PLATFORMS["macos-arm64"]] == "erfuellt"
    assert by[agg.EXPECTED_PLATFORMS["linux-arm64"]] == "erfuellt"
    assert by["macos-arm64: Live-GL-Performance"] == "erfuellt"
    assert by["linux-arm64: Live-GL-Performance"] == "erfuellt"
    assert by["macos-arm64: Native 3D-E2E (Projekt→HEIGHT→Undo/Save)"] == "erfuellt"
    # x86_64 immer sichtbar als pausiert (kein GPU-Zugang).
    assert any(r.status == "pausiert" and r.kriterium == agg.PAUSED_LABEL for r in rows)
    assert not agg.has_blocking_gaps(rows)

    summary = agg.build_acceptance_summary(rows, commit_sha="abc")
    assert summary["blocking"] is False
    assert summary["platforms"] == {
        "macos-arm64": "approved",
        "linux-arm64": "approved",
        "linux-x86_64": "paused",
    }


def test_acceptance_summary_blocks_incomplete_active_platform() -> None:
    rows = agg.build_matrix({})
    summary = agg.build_acceptance_summary(rows, commit_sha="abc")
    assert summary["blocking"] is True
    assert summary["platforms"]["macos-arm64"] == "blocked"
    assert summary["platforms"]["linux-arm64"] == "blocked"
    assert summary["platforms"]["linux-x86_64"] == "paused"


def test_missing_platform_is_gap(tmp_path: Path) -> None:
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    rows = agg.build_matrix(agg.load_evidence(tmp_path))
    by = {r.kriterium: r.status for r in rows}
    assert by[agg.EXPECTED_PLATFORMS["macos-arm64"]] == "fehlt"
    assert agg.has_blocking_gaps(rows)


def test_loaders_choose_latest_attempt_per_platform(tmp_path: Path) -> None:
    old = tmp_path / "abnahme-linux-arm64-1"
    new = tmp_path / "abnahme-linux-arm64-2"
    old.mkdir()
    new.mkdir()
    (old / "evidenz.json").write_text(
        json.dumps(_evidence("linux-arm64", status="fehlgeschlagen")), encoding="utf-8",
    )
    (new / "evidenz.json").write_text(
        json.dumps(_evidence("linux-arm64", status="bestanden")), encoding="utf-8",
    )
    assert agg.load_evidence(tmp_path)["linux-arm64"]["status"] == "bestanden"


def test_failed_status_maps_and_blocks(tmp_path: Path) -> None:
    _write(tmp_path, "macos-arm64", _evidence("macos-arm64", status="fehlgeschlagen"))
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    e2e, live_gl = _complete_aux("macos-arm64", "linux-arm64")
    rows = agg.build_matrix(agg.load_evidence(tmp_path), e2e=e2e, live_gl=live_gl)
    by = {r.kriterium: r.status for r in rows}
    assert by[agg.EXPECTED_PLATFORMS["macos-arm64"]] == "fehlgeschlagen"
    assert agg.has_blocking_gaps(rows)


def test_contract_violation_flags_unbewertet(tmp_path: Path) -> None:
    broken = _evidence("linux-arm64")
    del broken["commit_sha"]
    _write(tmp_path, "macos-arm64", _evidence("macos-arm64"))
    _write(tmp_path, "linux-arm64", broken)
    rows = agg.build_matrix(agg.load_evidence(tmp_path))
    row = next(r for r in rows if r.kriterium == agg.EXPECTED_PLATFORMS["linux-arm64"])
    assert row.status == "unbewertet"
    assert "commit_sha" in row.hinweis


def test_x86_64_enabled_uses_evidence(tmp_path: Path) -> None:
    _write(tmp_path, "macos-arm64", _evidence("macos-arm64"))
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    _write(tmp_path, "linux-x86_64", _evidence("linux-x86_64"))
    e2e, live_gl = _complete_aux("macos-arm64", "linux-arm64", "linux-x86_64")
    rows = agg.build_matrix(
        agg.load_evidence(tmp_path), x86_64_enabled=True, e2e=e2e, live_gl=live_gl,
    )
    row = next(r for r in rows if r.kriterium == agg.PAUSED_LABEL)
    assert row.status == "erfuellt"


def test_x86_64_enabled_without_evidence_is_gap(tmp_path: Path) -> None:
    rows = agg.build_matrix({}, x86_64_enabled=True)
    row = next(r for r in rows if r.kriterium == agg.PAUSED_LABEL)
    assert row.status == "fehlt"


def test_native_e2e_must_be_ready(tmp_path: Path) -> None:
    _write(tmp_path, "macos-arm64", _evidence("macos-arm64"))
    result = _e2e("macos-arm64", native_3d_state="unavailable")
    rows = agg.build_matrix(
        agg.load_evidence(tmp_path), e2e={"macos-arm64": result},
    )
    row = next(r for r in rows if r.kriterium.startswith("macos-arm64: Native 3D-E2E"))
    assert row.status == "fehlgeschlagen"
    assert "Ready" in row.hinweis


def test_live_gl_requires_all_metrics_and_provenance() -> None:
    result = _live_gl("linux-arm64")
    del result["formats"]["HEIGHT16-40MP"]["gl_frame_ms_p95"]
    result["environment"]["gl_provenance"] = ""
    issues = agg.validate_live_gl(result, platform="linux-arm64", commit_sha="abc")
    assert "gl_provenance leer" in issues
    assert "HEIGHT16-40MP.gl_frame_ms_p95 ungültig" in issues


def test_commit_validation_accepts_git_short_hash() -> None:
    full = "0123456789abcdef0123456789abcdef01234567"
    result = _live_gl("linux-arm64", git_commit=full[:7])
    assert agg.validate_live_gl(
        result, platform="linux-arm64", commit_sha=full,
    ) == []
    result["git_commit"] = "deadbee"
    assert "git_commit abweichend" in agg.validate_live_gl(
        result, platform="linux-arm64", commit_sha=full,
    )


def test_malformed_live_gl_environment_remains_renderable(tmp_path: Path) -> None:
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    result = _live_gl("linux-arm64", environment=["corrupt"])
    rows = agg.build_matrix(
        agg.load_evidence(tmp_path), live_gl={"linux-arm64": result},
    )
    row = next(r for r in rows if r.kriterium == "linux-arm64: Live-GL-Performance")
    assert row.status == "unbewertet"
    assert row.provenance == "—"
    assert "gl_provenance leer" in row.hinweis


def test_live_gl_load_from_disk(tmp_path: Path) -> None:
    target = tmp_path / "abnahme-linux-arm64" / "preview3d-live"
    target.mkdir(parents=True)
    (target / "result.json").write_text(
        json.dumps(_live_gl("linux-arm64")), encoding="utf-8",
    )
    loaded = agg.load_live_gl(tmp_path)
    assert loaded["linux-arm64"]["suite"] == "preview3d-live"


def test_render_markdown_contains_all_states(tmp_path: Path) -> None:
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    rows = agg.build_matrix(agg.load_evidence(tmp_path))
    md = agg.render_markdown(rows, commit_sha="deadbeef")
    assert "Abschlussmatrix" in md
    assert "deadbeef" in md
    assert "pausiert" in md
    assert "Go/No-Go entscheidet ein Mensch" in md


def test_matrix_rows_carry_geraet_os_datum_testperson_and_link(tmp_path: Path) -> None:
    """#685-Review: Testperson/Datum/Gerät-OS/Link fehlten bisher in der Matrix."""
    _write(tmp_path, "linux-arm64", _evidence(
        "linux-arm64", umgebung={"os": "Linux-6.1-aarch64", "runner": "raspberrypi"},
        erzeugt_am="2026-07-29T23:05:31+00:00",
    ))
    e2e, live_gl = _complete_aux("linux-arm64")
    rows = agg.build_matrix(
        agg.load_evidence(tmp_path), e2e=e2e, live_gl=live_gl,
        run_url="https://github.com/example/repo/actions/runs/123",
    )
    smoke_row = next(r for r in rows if r.kriterium == agg.EXPECTED_PLATFORMS["linux-arm64"])
    assert smoke_row.geraet_os == "raspberrypi (Linux-6.1-aarch64)"
    assert smoke_row.datum == "2026-07-29"
    assert smoke_row.testperson == agg.AUTOMATED_TESTPERSON
    assert smoke_row.nachweis_link == "https://github.com/example/repo/actions/runs/123"

    # E2E-Zeilen tragen kein eigenes umgebung, übernehmen aber Gerät/OS von der
    # Plattform-Evidenz desselben Jobs. Das Datum kommt dagegen aus dem eigenen
    # erzeugt_am des E2E-Ergebnisses (hier "2026-07-21" laut _e2e()-Fixture),
    # nicht von der Plattform-Evidenz (siehe eigener Test für den
    # Datumsgrenzen-Fall).
    e2e_row = next(r for r in rows if r.kriterium.startswith("linux-arm64: Native 3D-E2E"))
    assert e2e_row.geraet_os == "raspberrypi (Linux-6.1-aarch64)"
    assert e2e_row.datum == "2026-07-21"

    vision_row = next(r for r in rows if "Vision" in r.kriterium)
    assert vision_row.nachweis_link == "https://github.com/example/repo/actions/runs/123"


def test_matrix_rows_without_evidence_show_placeholder_geraet_os_and_datum() -> None:
    rows = agg.build_matrix({})
    row = next(r for r in rows if r.kriterium == agg.EXPECTED_PLATFORMS["macos-arm64"])
    assert row.geraet_os == "—"
    assert row.datum == "—"
    assert row.nachweis_link == "—"


def test_e2e_and_live_gl_rows_use_their_own_timestamp_across_date_boundary(
    tmp_path: Path,
) -> None:
    """Codex-Fund (#725-Review): überquert der Job die UTC-Datumsgrenze,
    muss die E2E-/Live-GL-Zeile ihr eigenes ``erzeugt_am``/``timestamp``
    zeigen, nicht das der (früher erzeugten) Plattform-Evidenz."""
    _write(tmp_path, "linux-arm64", _evidence(
        "linux-arm64", erzeugt_am="2026-07-29T23:55:00+00:00",
    ))
    e2e_result = _e2e("linux-arm64", erzeugt_am="2026-07-30T00:05:00+00:00")
    live_result = _live_gl("linux-arm64", timestamp="2026-07-30T00:10:00+00:00")
    rows = agg.build_matrix(
        agg.load_evidence(tmp_path),
        e2e={"linux-arm64": e2e_result}, live_gl={"linux-arm64": live_result},
    )
    e2e_row = next(r for r in rows if r.kriterium.startswith("linux-arm64: Native 3D-E2E"))
    live_row = next(r for r in rows if r.kriterium == "linux-arm64: Live-GL-Performance")
    assert e2e_row.datum == "2026-07-30"
    assert live_row.datum == "2026-07-30"


def test_render_markdown_contains_new_columns(tmp_path: Path) -> None:
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    rows = agg.build_matrix(
        agg.load_evidence(tmp_path), run_url="https://example.invalid/runs/1",
    )
    md = agg.render_markdown(rows, commit_sha="deadbeef")
    assert "Gerät/OS" in md
    assert "Testperson" in md
    assert agg.AUTOMATED_TESTPERSON in md
    assert "[Lauf](https://example.invalid/runs/1)" in md


def test_vision_verdicts_embedded_and_block(tmp_path: Path) -> None:
    _write(tmp_path, "macos-arm64", _evidence("macos-arm64"))
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    # nicht_erfuellt → Screenshots-Zeile fehlgeschlagen.
    vision = [
        {"screenshot": "a.png", "criterion": "fenster_sichtbar", "verdict": "erfuellt"},
        {"screenshot": "b.png", "criterion": "relief_sichtbar", "verdict": "nicht_erfuellt"},
    ]
    e2e, live_gl = _complete_aux("macos-arm64", "linux-arm64")
    rows = agg.build_matrix(
        agg.load_evidence(tmp_path), e2e=e2e, live_gl=live_gl, vision=vision,
    )
    row = next(r for r in rows if "Vision" in r.kriterium)
    assert row.status == "fehlgeschlagen"
    assert agg.has_blocking_gaps(rows)


def test_vision_row_surfaces_failed_criterion_reasoning() -> None:
    """#781: Begründung fehlgeschlagener/unsicherer Kriterien landet im Hinweis."""
    verdicts = [
        {"screenshot": "a.png", "criterion": "fenster_sichtbar", "verdict": "erfuellt"},
        {
            "screenshot": "b.png", "criterion": "relief_sichtbar",
            "verdict": "nicht_erfuellt", "begruendung": "Kein Relief im Screenshot erkennbar.",
        },
        {"screenshot": "c.png", "criterion": "3d_aktiv", "verdict": "unsicher"},
    ]
    row = agg._vision_row(verdicts)
    assert row.status == "fehlgeschlagen"
    assert "relief_sichtbar" in row.hinweis
    assert "b.png" in row.hinweis
    assert "Kein Relief im Screenshot erkennbar." in row.hinweis
    assert "3d_aktiv" in row.hinweis
    assert "c.png" in row.hinweis
    # erfuellt-Kriterien bleiben nur in der Zählung, nicht als Detail.
    assert "fenster_sichtbar" not in row.hinweis


def test_vision_row_sanitizes_begruendung_for_markdown_table() -> None:
    """#781: Pipes/Zeilenumbrüche in der Begründung dürfen die Tabelle nicht brechen."""
    verdicts = [
        {
            "screenshot": "a.png", "criterion": "x", "verdict": "nicht_erfuellt",
            "begruendung": "Zeile1\nZeile2 | mit Pipe " + "x" * 200,
        },
    ]
    row = agg._vision_row(verdicts)
    assert "\n" not in row.hinweis
    assert "\\|" in row.hinweis
    md = agg.render_markdown([row], commit_sha="abc")
    # Genau eine Tabellenzeile für diese Zeile: kein eingebetteter Zeilenumbruch.
    assert sum(1 for line in md.splitlines() if "Screenshots (Vision" in line) == 1


def test_sanitize_cell_escapes_preexisting_backslash_before_pipe() -> None:
    """Codex-Review PR #787: Ein bereits vorhandenes ``\\|`` darf durch die
    Pipe-Maskierung keinen wieder freien, trennenden Pipe erzeugen – jedes
    ``|`` im Ergebnis muss eine ungerade Anzahl vorangehender Backslashes
    tragen (sonst hebt ``\\\\`` die Maskierung des folgenden Pipes auf)."""
    sanitized = agg._sanitize_cell("A \\| B")
    for match in re.finditer(r"\\*\|", sanitized):
        backslashes = len(match.group()) - 1
        assert backslashes % 2 == 1, sanitized


def test_vision_load_from_disk(tmp_path: Path) -> None:
    (tmp_path / "vision-verdikte.json").write_text(
        json.dumps({"verdikte": [{"screenshot": "a.png", "criterion": "x", "verdict": "erfuellt"}]}),
        encoding="utf-8",
    )
    loaded = agg.load_vision(tmp_path)
    assert loaded and loaded[0]["verdict"] == "erfuellt"


def test_main_writes_matrix(tmp_path: Path) -> None:
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    out = tmp_path / "matrix.md"
    rc = agg.main(["--artifacts-dir", str(tmp_path), "--output", str(out),
                   "--commit-sha", "abc123"])
    assert rc == 0
    assert "Abschlussmatrix" in out.read_text(encoding="utf-8")
