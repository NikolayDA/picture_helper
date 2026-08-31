"""Minimale Qt-/GL-Sonde des Runner-Preflights (#934, Epic #914).

Zwei Eigenschaften tragen diese Sonde, und beide sind hier festgehalten:

1. **Kein Headless-Ausweichweg.** Der Releasepfad braucht das native
   Sitzungs-Plugin; ein ``offscreen``-Fallback würde genau den Ausfall
   verstecken, den die Sonde finden soll. Dieser Fall läuft hier **echt** —
   die Testumgebung ist offscreen.
2. **Keine zweite Fassung geteilter Regeln.** Die Software-Renderer-Erkennung
   kommt aus ``renderer_provenance``, die GL-Konstanten stimmen mit dem
   Produktivpfad überein.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

from bgremover import preview3d_capability, renderer_provenance

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "qt_gl_probe", ROOT / "scripts" / "qt_gl_probe.py"
)
assert _SPEC is not None and _SPEC.loader is not None
probe_module = importlib.util.module_from_spec(_SPEC)
sys.modules["qt_gl_probe"] = probe_module
_SPEC.loader.exec_module(probe_module)


def test_a_forced_headless_platform_is_a_finding_not_a_fallback() -> None:
    """Echt, nicht gemockt: Die Testumgebung ist ``offscreen``.

    Genau dieser Zustand — Qt läuft, aber nicht in einer echten Sitzung — ist
    der Ausfall, den der reine GL-Ladetest nicht sah.
    """
    result = probe_module.probe({"QT_QPA_PLATFORM": "offscreen"})
    assert result["ok"] is False
    assert result["stage"] == "plugin"
    assert "offscreen" in str(result["detail"])


def test_every_headless_plugin_is_rejected() -> None:
    for name in probe_module.HEADLESS_PLATFORMS:
        result = probe_module.probe({"QT_QPA_PLATFORM": name})
        assert result["stage"] == "plugin", name


def test_the_probe_prints_exactly_one_json_line_and_fails_loudly(capsys) -> None:
    """Der Preflight liest genau diese Zeile; ein stiller Skip existiert nicht."""
    code = probe_module.main([])
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1, out
    payload = json.loads(out[0])
    assert set(payload) >= {"ok", "stage", "detail"}
    # Offscreen-Umgebung: Die Sonde meldet einen Befund und Exit != 0.
    assert payload["ok"] is False and code == 1


def test_the_software_renderer_rule_is_loaded_not_copied() -> None:
    """Geteilte Quelle der Wahrheit (#642) statt einer zweiten Markerliste."""
    rule = probe_module.load_software_renderer_rule()
    for diagnostic in ("Mesa / llvmpipe (LLVM 15) / 4.5", "Apple / Apple M2 / 2.1"):
        assert rule(diagnostic) is renderer_provenance.is_software_renderer(diagnostic)
    source = (ROOT / "scripts" / "qt_gl_probe.py").read_text(encoding="utf-8")
    for marker in renderer_provenance.SOFTWARE_RENDERER_MARKERS:
        assert marker not in source, f"Marker {marker!r} kopiert statt importiert"


def test_gl_constants_match_the_production_probe() -> None:
    """Handgepflegte Kopie gegen ihre Quelle.

    Die Qt-Aufrufsequenz muss die Sonde eigenständig führen (die schlanke
    Runtime hat ``bgremover.constants``/Pillow nicht). Die *Werte*, die sie
    ausliest, dürfen deshalb nicht auseinanderlaufen — sonst berichtete der
    Preflight etwas anderes als der Plattform-Job.
    """
    assert probe_module.GL_VENDOR == preview3d_capability._GL_VENDOR
    assert probe_module.GL_RENDERER == preview3d_capability._GL_RENDERER
    assert probe_module.GL_VERSION == preview3d_capability._GL_VERSION


def test_the_probe_uses_the_same_qt_sequence_as_production() -> None:
    """Kontext, Oberfläche und Versionsfunktionen wie im Produktivpfad."""
    source = (ROOT / "scripts" / "qt_gl_probe.py").read_text(encoding="utf-8")
    for symbol in (
        "QGuiApplication", "QOffscreenSurface", "QOpenGLContext",
        "QSurfaceFormat", "QOpenGLVersionFunctionsFactory",
    ):
        assert symbol in source, symbol
    # QApplication zöge QtWidgets nach – die Sonde bleibt bei QtGui.
    assert "QApplication" not in source.replace("QGuiApplication", "")


def test_the_probe_runs_standalone_without_the_release_venv() -> None:
    """Nur PyQt6 + Checkout: kein Import aus dem installierten ``bgremover``.

    Sonst bräuchte die schlanke Runtime Pillow und alles, was daran hängt —
    und ein Import in ``bgremover.constants`` legte still den Preflight lahm.
    """
    source = (ROOT / "scripts" / "qt_gl_probe.py").read_text(encoding="utf-8")
    # Nur echte Importanweisungen, nicht die Prosa im Docstring, die genau
    # diesen Verzicht begründet.
    assert not re.search(r"(?m)^\s*(?:import|from)\s+bgremover", source)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "qt_gl_probe.py")],
        capture_output=True, text=True, check=False, env={"QT_QPA_PLATFORM": "offscreen"},
    )
    assert json.loads(result.stdout.strip())["stage"] == "plugin"
