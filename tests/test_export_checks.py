"""Qt-freie Tests der allgemeinen Pre-Export-Prüfung (#379).

Deckt jede Prüfkategorie mit Positiv- und Negativfall ab (Fehler vs. Warnung
korrekt klassifiziert), die deterministische Sortierung, die geteilten
Blockier-/Aufteilungs-Helfer sowie die de/en-i18n-Parität und -Coverage der
``export.checks.*``-Meldungen.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

import bgremover.i18n as i18n
from bgremover.constants import _MAX_MEGAPIXELS
from bgremover.export_checks import (
    CheckCode,
    Finding,
    Severity,
    check_color_space,
    check_dimensions,
    check_export,
    check_print_area,
    check_resolution,
    check_transparency,
    format_finding,
    has_blocking_errors,
    sort_findings,
    split_findings,
)
from bgremover.project_model import Project


def _solid(size: tuple[int, int], color: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", size, color)


def _codes(findings: tuple[Finding, ...] | list[Finding]) -> list[CheckCode]:
    return [f.code for f in findings]


def _color_project(size: tuple[int, int] = (8, 4)) -> Project:
    project = Project(*size)
    project.create_layer(_solid(size, (10, 20, 30, 255)), name="Farbe")
    return project


# ── Abmessungen ────────────────────────────────────────────────────────────

def test_dimensions_valid_has_no_finding() -> None:
    assert check_dimensions((8, 4)) == []


def test_dimensions_nonpositive_is_error() -> None:
    findings = check_dimensions((0, 4))
    assert _codes(findings) == [CheckCode.DIMENSIONS_INVALID]
    assert findings[0].severity is Severity.ERROR


def test_dimensions_too_large_is_error() -> None:
    edge = int((_MAX_MEGAPIXELS * 1_000_000) ** 0.5) + 1000
    findings = check_dimensions((edge, edge))
    assert _codes(findings) == [CheckCode.DIMENSIONS_TOO_LARGE]
    assert findings[0].severity is Severity.ERROR


# ── Auflösung / DPI ──────────────────────────────────────────────────────────

def test_resolution_plausible_has_no_finding() -> None:
    assert check_resolution((300.0, 300.0)) == []


def test_resolution_none_has_no_finding() -> None:
    assert check_resolution(None) == []


def test_resolution_too_low_is_warning() -> None:
    findings = check_resolution((5.0, 5.0))
    assert _codes(findings) == [CheckCode.RESOLUTION_TOO_LOW]
    assert findings[0].severity is Severity.WARNING


def test_resolution_too_high_is_warning() -> None:
    findings = check_resolution((9000.0, 9000.0))
    assert _codes(findings) == [CheckCode.RESOLUTION_TOO_HIGH]
    assert findings[0].severity is Severity.WARNING


# ── Farbraum ─────────────────────────────────────────────────────────────────

def test_color_space_rgba_has_no_finding() -> None:
    assert check_color_space(Image.new("RGBA", (4, 4))) == []


def test_color_space_non_rgba_is_error() -> None:
    findings = check_color_space(Image.new("RGB", (4, 4)))
    assert _codes(findings) == [CheckCode.COLOR_SPACE_UNEXPECTED]
    assert findings[0].severity is Severity.ERROR
    assert findings[0].params["actual"] == "RGB"


# ── Transparenz ──────────────────────────────────────────────────────────────

def test_transparency_opaque_has_no_finding() -> None:
    assert check_transparency(_solid((4, 4), (10, 20, 30, 255))) == []


def test_transparency_hard_edges_have_no_finding() -> None:
    # Nur 0/255-Alpha (harte Freistellungskante) ist erwartbar, keine Warnung.
    arr = np.zeros((4, 4, 4), dtype=np.uint8)
    arr[:, :2, 3] = 255
    findings = check_transparency(Image.fromarray(arr, "RGBA"))
    assert findings == []


def test_transparency_fully_transparent_is_warning() -> None:
    findings = check_transparency(_solid((4, 4), (10, 20, 30, 0)))
    assert _codes(findings) == [CheckCode.FULLY_TRANSPARENT]
    assert findings[0].severity is Severity.WARNING


def test_transparency_partial_alpha_is_warning() -> None:
    findings = check_transparency(_solid((4, 4), (10, 20, 30, 128)))
    assert _codes(findings) == [CheckCode.UNEXPECTED_ALPHA]
    assert findings[0].severity is Severity.WARNING


# ── Druckfläche ──────────────────────────────────────────────────────────────

def test_print_area_within_medium_has_no_finding() -> None:
    assert check_print_area((50.0, 25.0), (100.0, 100.0)) == []


def test_print_area_missing_medium_has_no_finding() -> None:
    assert check_print_area((50.0, 25.0), None) == []


def test_print_area_exceeded_is_warning() -> None:
    findings = check_print_area((200.0, 50.0), (100.0, 100.0))
    assert _codes(findings) == [CheckCode.PRINT_AREA_EXCEEDED]
    assert findings[0].severity is Severity.WARNING


# ── Orchestrator check_export ────────────────────────────────────────────────

def test_check_export_clean_project_has_no_findings() -> None:
    assert check_export(_color_project()) == ()


def test_check_export_empty_project_is_output_empty() -> None:
    findings = check_export(Project(8, 4))
    assert CheckCode.OUTPUT_EMPTY in _codes(findings)
    assert next(f for f in findings if f.code is CheckCode.OUTPUT_EMPTY).severity is Severity.ERROR


def test_check_export_transparent_project_warns() -> None:
    project = Project(8, 4)
    project.create_layer(_solid((8, 4), (0, 0, 0, 0)), name="leer")
    assert CheckCode.FULLY_TRANSPARENT in _codes(check_export(project))


def test_check_export_uses_physical_size_for_print_area() -> None:
    project = _color_project((8, 4))
    project.set_physical_size_mm(200.0, 50.0)
    findings = check_export(project, medium_size_mm=(100.0, 100.0))
    assert CheckCode.PRINT_AREA_EXCEEDED in _codes(findings)


def test_check_export_flags_low_resolution_from_model_dpi() -> None:
    project = _color_project((10, 10))
    project.set_physical_size_mm(500.0, 500.0)  # 10 px / ~19.7 in → ~0.5 dpi
    assert CheckCode.RESOLUTION_TOO_LOW in _codes(check_export(project))


# ── Sortierung & geteilte Helfer ─────────────────────────────────────────────

def test_findings_sorted_errors_before_warnings() -> None:
    findings = sort_findings(
        [
            Finding(CheckCode.RESOLUTION_TOO_LOW, Severity.WARNING),
            Finding(CheckCode.DIMENSIONS_INVALID, Severity.ERROR),
        ]
    )
    assert _codes(findings) == [CheckCode.DIMENSIONS_INVALID, CheckCode.RESOLUTION_TOO_LOW]


def test_sort_is_deterministic_by_code_order_within_severity() -> None:
    findings = sort_findings(
        [
            Finding(CheckCode.OUTPUT_EMPTY, Severity.ERROR),
            Finding(CheckCode.DIMENSIONS_INVALID, Severity.ERROR),
        ]
    )
    assert _codes(findings) == [CheckCode.DIMENSIONS_INVALID, CheckCode.OUTPUT_EMPTY]


def test_has_blocking_errors_and_split() -> None:
    findings = (
        Finding(CheckCode.DIMENSIONS_INVALID, Severity.ERROR),
        Finding(CheckCode.RESOLUTION_TOO_LOW, Severity.WARNING),
    )
    assert has_blocking_errors(findings) is True
    errors, warnings = split_findings(findings)
    assert _codes(errors) == [CheckCode.DIMENSIONS_INVALID]
    assert _codes(warnings) == [CheckCode.RESOLUTION_TOO_LOW]


def test_no_blocking_errors_for_warnings_only() -> None:
    assert has_blocking_errors([Finding(CheckCode.FULLY_TRANSPARENT, Severity.WARNING)]) is False


# ── i18n: Parität, Coverage, Rendern ─────────────────────────────────────────

def _derived_keys() -> set[str]:
    return {f"export.checks.{code.value}" for code in CheckCode}


def test_every_check_code_has_de_and_en_translation() -> None:
    de = i18n._TRANSLATIONS["de"]
    en = i18n._TRANSLATIONS["en"]
    for key in _derived_keys():
        assert key in de, f"DE fehlt: {key}"
        assert key in en, f"EN fehlt: {key}"


def test_finding_i18n_key_matches_namespace() -> None:
    finding = Finding(CheckCode.OUTPUT_EMPTY, Severity.ERROR)
    assert finding.i18n_key == "export.checks.output_empty"


def test_format_finding_renders_every_code_in_de_and_en() -> None:
    samples: dict[CheckCode, Finding] = {
        CheckCode.DIMENSIONS_INVALID: Finding(
            CheckCode.DIMENSIONS_INVALID, Severity.ERROR, {"width": 0, "height": 4}
        ),
        CheckCode.DIMENSIONS_TOO_LARGE: Finding(
            CheckCode.DIMENSIONS_TOO_LARGE, Severity.ERROR, {"mp": 99.9, "limit": 40.0}
        ),
        CheckCode.COLOR_SPACE_UNEXPECTED: Finding(
            CheckCode.COLOR_SPACE_UNEXPECTED, Severity.ERROR,
            {"actual": "RGB", "expected": "RGBA"},
        ),
        CheckCode.OUTPUT_EMPTY: Finding(CheckCode.OUTPUT_EMPTY, Severity.ERROR),
        CheckCode.RESOLUTION_TOO_LOW: Finding(
            CheckCode.RESOLUTION_TOO_LOW, Severity.WARNING, {"dpi": 5.0, "minimum": 30.0}
        ),
        CheckCode.RESOLUTION_TOO_HIGH: Finding(
            CheckCode.RESOLUTION_TOO_HIGH, Severity.WARNING, {"dpi": 9000.0, "maximum": 5000.0}
        ),
        CheckCode.FULLY_TRANSPARENT: Finding(CheckCode.FULLY_TRANSPARENT, Severity.WARNING),
        CheckCode.UNEXPECTED_ALPHA: Finding(
            CheckCode.UNEXPECTED_ALPHA, Severity.WARNING, {"percent": 12.5}
        ),
        CheckCode.PRINT_AREA_EXCEEDED: Finding(
            CheckCode.PRINT_AREA_EXCEEDED, Severity.WARNING,
            {"width": 200.0, "height": 50.0, "medium_w": 100.0, "medium_h": 100.0},
        ),
    }
    assert set(samples) == set(CheckCode)
    for locale in ("de", "en"):
        i18n.configure_locale(locale)
        try:
            for finding in samples.values():
                text = format_finding(finding)
                assert text and "{" not in text
        finally:
            i18n.configure_locale(i18n.DEFAULT_LOCALE)
