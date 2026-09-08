"""Renderbeweis-Sonde ``scripts/render_proof_probe.py`` (#1010).

Die Sonde läuft selten und auf fremder Hardware (Abnahme-Runner, Dispatch des
Heartbeats). Was sich netzfrei und GL-frei prüfen lässt, steht hier: das
dokumentierte Zeilenformat, Tabelle und JSON, die urteilsfreie Lage
``verborgen`` (Qt malt einen nie gezeigten Viewer nicht – alle Zähler 0,
kein Fehlerzustand) und die CLI-Ränder. Die Bindung an die Viewer-API und an
die echten Signaturen von ``HeightField``/``build_relief_mesh`` hält
``tests/test_viewer_3d.py`` (Drift-Schutz #1010).
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_proof_probe.py"


@pytest.fixture(scope="module")
def probe(qapp):
    """Das Skript als Modul – über den Dateipfad, wie die übrigen Skript-Tests."""
    spec = importlib.util.spec_from_file_location("render_proof_probe", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["render_proof_probe"] = module
    spec.loader.exec_module(module)
    return module


def _messung(probe, **overrides):
    werte = {
        "lage": "sichtbar",
        "paint_events": 2,
        "fbos": [1, 1],
        "paint_gl": 2,
        "frame_swapped": 2,
        "erster_swap": (2, 109),
        "has_rendered": True,
        "refused_paints": 0,
        "has_failed": False,
        "grund": "",
    }
    werte.update(overrides)
    return probe.Messung(**werte)


def test_a_hidden_viewer_is_never_judged(probe, qapp) -> None:
    """Die Lage ``verborgen`` ist plattformunabhängig: kein Paint, kein Urteil.

    Das ist die Asymmetrie des Beweises (#1004) – ein Viewer ohne Paint wird
    nie abgestuft. Unter ``offscreen`` wie auf echter Hardware müssen hier
    alle Zähler 0 sein; die sichtbare Lage ist dagegen genau die Messung,
    die nur das Gerät beantwortet, und gehört nicht in einen Unit-Test.
    """
    messung, renderer = probe.messe(qapp, "verborgen", ms=100)
    assert messung.lage == "verborgen"
    assert (messung.paint_events, messung.fbos, messung.paint_gl) == (0, [], 0)
    assert (messung.frame_swapped, messung.erster_swap) == (0, None)
    assert (messung.has_rendered, messung.refused_paints) == (False, 0)
    assert (messung.has_failed, messung.grund) == (False, "")
    assert renderer == ""  # ohne Paint gibt es keinen Kontext, den man befragen könnte


def test_an_unknown_position_is_rejected(probe, qapp) -> None:
    with pytest.raises(ValueError, match="Unbekannte Lage"):
        probe.messe(qapp, "schwebend", ms=10)


def test_the_documented_line_format_is_stable(probe) -> None:
    """Die Zeile geht wörtlich als Kommentar ins Issue und als Zeile in den
    ADR-Nachtrag – ihr Format ist damit Teil der Prozedur in TESTING.md."""
    zeile = _messung(probe).zeile()
    assert zeile == (
        "sichtbar   paintEvents=2 fbo=[1, 1] paintGL=2 frameSwapped=2 "
        "erster_swap=(2, 109) _has_rendered=True _refused_paints=0 "
        "has_failed=False grund=''"
    )
    kaputt = _messung(
        probe, fbos=[0, 0, 0], paint_gl=0, frame_swapped=0, erster_swap=None,
        has_rendered=False, refused_paints=3, has_failed=True,
        grund="paintEvent: Qt hält keinen Widget-Framebuffer (3 Anforderungen abgewiesen, kein Frame)",
        paint_events=3,
    ).zeile()
    assert "fbo=[0, 0, 0]" in kaputt and "erster_swap=None" in kaputt
    assert kaputt.endswith("grund='paintEvent: Qt hält keinen Widget-Framebuffer (3 Anforderungen abgewiesen, kein Frame)'")


def test_the_header_line_carries_the_provenance(probe) -> None:
    env = {
        "geraet": "Apple M3", "os": "macOS 15.6", "arch": "arm64",
        "qt": "6.11.0", "pyqt": "6.11.0", "python": "3.12.6", "plattform": "cocoa",
    }
    kopf = probe.kopfzeile(env, "Apple M3")
    assert kopf.startswith("Gerät · OS · Qt : Apple M3 · macOS 15.6 (arm64) · Qt 6.11.0 / PyQt 6.11.0")
    assert "Plattform cocoa" in kopf and kopf.endswith("Renderer Apple M3")
    # Ohne Gerät und ohne Renderer bleibt die Zeile lesbar statt leer.
    ohne = probe.kopfzeile({**env, "geraet": ""})
    assert ohne.startswith("Gerät · OS · Qt : unbekanntes Gerät ·") and "Renderer" not in ohne


def test_table_and_report_carry_every_column(probe) -> None:
    env = {"qt": "6.7.1", "pyqt": "6.7.1", "plattform": "xcb", "os": "Ubuntu", "arch": "x86_64",
           "geraet": "", "python": "3.11"}
    messungen = [
        _messung(probe),
        _messung(probe, lage="verborgen", paint_events=0, fbos=[], paint_gl=0,
                 frame_swapped=0, erster_swap=None, has_rendered=False),
    ]
    tabelle = probe.markdown_tabelle(env, messungen, "llvmpipe")
    assert "### Renderbeweis-Sonde (#1010)" in tabelle
    for spalte in ("paintEvents", "`defaultFramebufferObject()` je Paint", "`paintGL`",
                   "`frameSwapped`", "`erster_swap` (Paint, ms)", "`_has_rendered`",
                   "`_refused_paints`", "`has_failed`", "`grund`"):
        assert spalte in tabelle, spalte
    assert "| sichtbar | `xcb` | 2 | 1, 1 | 2 | 2 | 2, 109 | `True` | 0 | `False` | – |" in tabelle
    assert "| verborgen | `xcb` | 0 | – | 0 | 0 | – | `False` | 0 | `False` | – |" in tabelle
    assert "die Sonde bewertet nicht" in tabelle

    report = probe.bericht(env, messungen, 2000, "llvmpipe")
    assert (report["schema"], report["kind"]) == (probe.SCHEMA, probe.KIND)
    assert report["umgebung"]["renderer"] == "llvmpipe" and report["fenster_ms"] == 2000
    assert [m["lage"] for m in report["messungen"]] == ["sichtbar", "verborgen"]
    assert report["messungen"][0]["erster_swap"] == (2, 109)
    json.dumps(report)  # serialisierbar, wie --json-out es braucht


def test_the_positions_are_documented_in_order(probe) -> None:
    """Reihenfolge und Namen sind Teil der Prozedur (TESTING.md, ADR-Tabelle)."""
    assert probe.LAGEN == ("sichtbar", "verborgen", "verdeckt")


def _run(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    umgebung = {**os.environ, "QT_QPA_PLATFORM": "offscreen", **(env or {})}
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, timeout=120, env=umgebung, cwd=ROOT, check=False,
    )


def test_cli_help_and_a_non_positive_window_are_handled() -> None:
    assert _run("--help").returncode == 0
    fehler = _run("--ms", "0")
    assert fehler.returncode == 2 and "--ms muss positiv sein" in fehler.stderr


def test_cli_measures_the_hidden_position_end_to_end(tmp_path: Path) -> None:
    """Der Weg des Dispatch-Schritts: Zeilen auf stdout, Tabelle per --summary,
    JSON per --json-out – hier nur mit der plattformunabhängigen Lage."""
    summary = tmp_path / "summary.md"
    report = tmp_path / "sonde.json"
    lauf = _run("--lage", "verborgen", "--ms", "100",
                "--json-out", str(report), "--summary", str(summary))
    assert lauf.returncode == 0, lauf.stderr
    zeilen = lauf.stdout.splitlines()
    assert zeilen[0].startswith("Gerät · OS · Qt : ") and "Plattform offscreen" in zeilen[0]
    assert zeilen[1].startswith("verborgen  paintEvents=0 fbo=[] paintGL=0 frameSwapped=0 ")
    assert len(zeilen) == 2

    daten = json.loads(report.read_text(encoding="utf-8"))
    assert daten["kind"] == "render-proof-probe" and daten["umgebung"]["plattform"] == "offscreen"
    (messung,) = daten["messungen"]
    assert messung["lage"] == "verborgen" and messung["has_failed"] is False
    assert "| verborgen | `offscreen` | 0 | – | 0 | 0 | – | `False` | 0 | `False` | – |" in (
        summary.read_text(encoding="utf-8")
    )
