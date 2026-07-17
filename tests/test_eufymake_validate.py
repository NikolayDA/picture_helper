"""Qt-freie Tests der EufyMake-Konsistenzprüfung (#354).

Deckt einen positiven Plan, jeden Fehlercode, jeden Warnungstyp, mehrere
gleichzeitige Befunde mit stabiler Sortierung, die Blockier-/Bestätigungs-Logik
sowie die de/en-i18n-Parität (Keys + Platzhalter, Coverage) ab.
"""
from __future__ import annotations

import re

import numpy as np
import pytest
from PIL import Image

import bgremover.i18n as i18n
from bgremover.eufymake_validate import (
    ExportCheckCode,
    ExportFinding,
    Severity,
    format_finding,
    has_blocking_errors,
    split_findings,
    validate_export,
)
from bgremover.project_model import (
    META_BIT_DEPTH,
    META_PHYSICAL_SIZE_MM,
    LayerKind,
    LayerRole,
    Project,
)

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def _solid(size: tuple[int, int], color: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", size, color)


def _gradient_gray(size: tuple[int, int]) -> Image.Image:
    """Nicht-konstante Graustufen-RGBA-Ebene (für „nicht leere" Height/Gloss)."""
    w, h = size
    row = np.linspace(0, 255, num=w, dtype=np.uint8)
    grid = np.tile(row, (h, 1))
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :, 0] = arr[:, :, 1] = arr[:, :, 2] = grid
    arr[:, :, 3] = 255
    return Image.fromarray(arr, "RGBA")


def _color_project(size: tuple[int, int] = (4, 2)) -> Project:
    project = Project(*size)
    project.create_layer(_solid(size, (10, 20, 30, 255)), name="Farbe")
    return project


def _with_height(project: Project, *, image: Image.Image | None = None) -> Project:
    size = project.size
    img = image if image is not None else _gradient_gray(size)
    layer = project.create_layer(img, name="Höhe", kind=LayerKind.HEIGHT)
    project.assign_role(layer.id, LayerRole.HEIGHT_MAP)
    return project


def _with_gloss(project: Project, *, image: Image.Image | None = None) -> Project:
    size = project.size
    img = image if image is not None else _gradient_gray(size)
    layer = project.create_layer(img, name="Gloss", kind=LayerKind.GLOSS)
    project.assign_role(layer.id, LayerRole.GLOSS_MASK)
    return project


def _codes(findings: tuple[ExportFinding, ...]) -> list[ExportCheckCode]:
    return [f.code for f in findings]


# ── Positiver Plan ───────────────────────────────────────────────────────

def test_clean_project_has_no_findings() -> None:
    assert validate_export(_color_project()) == ()


def test_color_plus_nonconstant_height_is_clean() -> None:
    project = _with_height(_color_project())
    assert validate_export(project) == ()


def test_validation_is_deterministic() -> None:
    project = _with_gloss(_with_height(_color_project()))
    assert validate_export(project) == validate_export(project)


# ── Harte Fehler ─────────────────────────────────────────────────────────

def test_color_motif_missing_is_error() -> None:
    project = Project(4, 2)
    project.create_layer(_gradient_gray((4, 2)), name="Höhe", kind=LayerKind.HEIGHT)
    findings = validate_export(project)
    assert ExportCheckCode.COLOR_MOTIF_MISSING in _codes(findings)
    motif = next(f for f in findings if f.code is ExportCheckCode.COLOR_MOTIF_MISSING)
    assert motif.severity is Severity.ERROR
    assert motif.role is LayerRole.COLOR_MOTIF


def test_color_motif_missing_for_hidden_only_color() -> None:
    project = Project(4, 2)
    hidden = project.create_layer(_solid((4, 2), (1, 2, 3, 255)), name="h")
    project.set_visible(hidden.id, False)
    assert ExportCheckCode.COLOR_MOTIF_MISSING in _codes(validate_export(project))


def test_requested_optional_role_missing_is_error() -> None:
    project = _color_project()
    findings = validate_export(project, requested_optional_roles=[LayerRole.HEIGHT_MAP])
    missing = next(f for f in findings if f.code is ExportCheckCode.OPTIONAL_ROLE_MISSING)
    assert missing.severity is Severity.ERROR
    assert missing.role is LayerRole.HEIGHT_MAP
    assert missing.params["role_name"] == LayerRole.HEIGHT_MAP.value


def test_size_mismatch_is_error() -> None:
    project = _color_project((4, 2))
    findings = validate_export(project, target_size=(8, 8))
    mismatch = next(f for f in findings if f.code is ExportCheckCode.ASSET_SIZE_MISMATCH)
    assert mismatch.severity is Severity.ERROR
    assert mismatch.role is LayerRole.COLOR_MOTIF
    assert mismatch.params["actual"] == "4×2"
    assert mismatch.params["expected"] == "8×8"


def test_size_mismatch_flags_optional_role() -> None:
    project = _with_height(_color_project((4, 2)))
    findings = validate_export(project, target_size=(8, 8))
    mismatched_roles = {
        f.role for f in findings if f.code is ExportCheckCode.ASSET_SIZE_MISMATCH
    }
    assert LayerRole.COLOR_MOTIF in mismatched_roles
    assert LayerRole.HEIGHT_MAP in mismatched_roles


@pytest.mark.parametrize("bad_meta", [{META_BIT_DEPTH: 7}, {META_PHYSICAL_SIZE_MM: (0.0, 5.0)}])
def test_invalid_target_params_is_error(bad_meta: dict[str, object]) -> None:
    project = _color_project()
    project.metadata.update(bad_meta)
    findings = validate_export(project)
    invalid = [f for f in findings if f.code is ExportCheckCode.INVALID_TARGET_PARAMS]
    assert invalid and invalid[0].severity is Severity.ERROR


def test_nonpositive_target_size_is_error() -> None:
    findings = validate_export(_color_project(), target_size=(0, 5))
    assert ExportCheckCode.INVALID_TARGET_PARAMS in _codes(findings)


def test_present_null_physical_size_is_invalid_target_param() -> None:
    # Ein vorhandener, ungültiger Wert (``physical_size_mm: null``) muss als
    # blockierender Befund auftauchen – deckungsgleich mit dem Render-/Schreibpfad,
    # sonst schlüge der Writer mit einer nicht abgefangenen Ausnahme auf.
    project = _color_project()
    project.metadata[META_PHYSICAL_SIZE_MM] = None
    findings = validate_export(project)
    assert ExportCheckCode.INVALID_TARGET_PARAMS in _codes(findings)


# ── Warnungen ────────────────────────────────────────────────────────────

def test_constant_height_is_warning() -> None:
    project = _with_height(_color_project(), image=_solid((4, 2), (128, 128, 128, 255)))
    findings = validate_export(project)
    empty = next(f for f in findings if f.code is ExportCheckCode.HEIGHT_MAP_EMPTY)
    assert empty.severity is Severity.WARNING
    assert empty.role is LayerRole.HEIGHT_MAP


def test_transparent_height_is_warning() -> None:
    project = _with_height(_color_project(), image=_solid((4, 2), (0, 0, 0, 0)))
    assert ExportCheckCode.HEIGHT_MAP_EMPTY in _codes(validate_export(project))


def test_constant_gloss_is_warning() -> None:
    project = _with_gloss(_color_project(), image=_solid((4, 2), (255, 255, 255, 255)))
    assert ExportCheckCode.GLOSS_MASK_EMPTY in _codes(validate_export(project))


def test_gloss_always_warns_ink_mode() -> None:
    project = _with_gloss(_color_project())
    findings = validate_export(project)
    ink = next(f for f in findings if f.code is ExportCheckCode.GLOSS_INK_MODE)
    assert ink.severity is Severity.WARNING
    # Nicht-konstanter Gloss → keine "leer"-Warnung, aber Ink-Mode bleibt.
    assert ExportCheckCode.GLOSS_MASK_EMPTY not in _codes(findings)


def test_16bit_height_is_unconfirmed_warning() -> None:
    project = _with_height(_color_project())
    project.metadata[META_BIT_DEPTH] = 16
    findings = validate_export(project)
    warn = next(f for f in findings if f.code is ExportCheckCode.BIT_DEPTH_UNCONFIRMED)
    assert warn.severity is Severity.WARNING
    assert warn.params["bits"] == 16


def test_8bit_height_has_no_bitdepth_warning() -> None:
    project = _with_height(_color_project())
    assert ExportCheckCode.BIT_DEPTH_UNCONFIRMED not in _codes(validate_export(project))


def test_bit_depth_override_triggers_warning() -> None:
    # Override 16 ohne Metadaten → Bittiefen-Warnung (UI-Wahl, #355).
    project = _with_height(_color_project())
    findings = validate_export(project, bit_depth=16)
    assert ExportCheckCode.BIT_DEPTH_UNCONFIRMED in _codes(findings)


def test_invalid_bit_depth_override_is_error() -> None:
    findings = validate_export(_color_project(), bit_depth=7)
    assert ExportCheckCode.INVALID_TARGET_PARAMS in _codes(findings)


def test_physical_size_is_warning() -> None:
    project = _color_project()
    project.metadata[META_PHYSICAL_SIZE_MM] = (50.0, 25.0)
    findings = validate_export(project)
    warn = next(f for f in findings if f.code is ExportCheckCode.PHYSICAL_SIZE_UNVERIFIED)
    assert warn.severity is Severity.WARNING
    assert warn.role is None


# ── Mehrere Befunde + stabile Sortierung ─────────────────────────────────

def test_multiple_findings_are_sorted_errors_first() -> None:
    project = _color_project((4, 2))
    project.metadata[META_PHYSICAL_SIZE_MM] = (50.0, 25.0)  # → Warnung
    findings = validate_export(
        project, requested_optional_roles=[LayerRole.HEIGHT_MAP], target_size=(8, 8)
    )
    codes = _codes(findings)
    # Fehler (size_mismatch, optional_role_missing) vor der Warnung.
    assert codes.index(ExportCheckCode.ASSET_SIZE_MISMATCH) < codes.index(
        ExportCheckCode.PHYSICAL_SIZE_UNVERIFIED
    )
    assert codes.index(ExportCheckCode.OPTIONAL_ROLE_MISSING) < codes.index(
        ExportCheckCode.PHYSICAL_SIZE_UNVERIFIED
    )
    severities = [f.severity for f in findings]
    assert severities == sorted(
        severities, key=lambda s: 0 if s is Severity.ERROR else 1
    )


def test_findings_sorted_by_code_order_within_severity() -> None:
    project = _color_project((4, 2))
    project.metadata[META_BIT_DEPTH] = 99  # invalid → INVALID_TARGET_PARAMS (idx 3)
    findings = validate_export(project, target_size=(8, 8))  # ASSET_SIZE_MISMATCH (idx 2)
    codes = _codes(findings)
    assert codes.index(ExportCheckCode.ASSET_SIZE_MISMATCH) < codes.index(
        ExportCheckCode.INVALID_TARGET_PARAMS
    )


# ── Blockier-/Bestätigungs-Logik ─────────────────────────────────────────

def test_has_blocking_errors_and_split() -> None:
    project = _color_project()
    project.metadata[META_PHYSICAL_SIZE_MM] = (50.0, 25.0)
    findings = validate_export(project, requested_optional_roles=[LayerRole.GLOSS_MASK])
    assert has_blocking_errors(findings) is True  # optional_role_missing
    errors, warnings = split_findings(findings)
    assert all(f.is_error for f in errors)
    assert all(not f.is_error for f in warnings)
    assert len(errors) + len(warnings) == len(findings)


def test_clean_project_has_no_blocking_errors() -> None:
    assert has_blocking_errors(validate_export(_color_project())) is False


# ── i18n-Parität & Coverage ──────────────────────────────────────────────

def _derived_keys() -> set[str]:
    return {f"eufymake.export.{code.value}" for code in ExportCheckCode}


def _placeholders(template: str) -> set[str]:
    return set(_PLACEHOLDER_RE.findall(template))


def test_every_code_has_de_and_en_translation() -> None:
    de = i18n._TRANSLATIONS["de"]
    en = i18n._TRANSLATIONS["en"]
    for key in _derived_keys():
        assert key in de, f"DE fehlt: {key}"
        assert key in en, f"EN fehlt: {key}"


def test_table_eufymake_keys_match_codes_exactly() -> None:
    # Keine verwaisten oder fehlenden eufymake.export.*-Keys in der Tabelle.
    for locale in ("de", "en"):
        table_keys = {k for k in i18n._TRANSLATIONS[locale] if k.startswith("eufymake.export.")}
        assert table_keys == _derived_keys(), locale


def test_de_en_placeholder_parity() -> None:
    de = i18n._TRANSLATIONS["de"]
    en = i18n._TRANSLATIONS["en"]
    for key in _derived_keys():
        assert _placeholders(de[key]) == _placeholders(en[key]), key


def test_format_finding_renders_every_code() -> None:
    samples: dict[ExportCheckCode, ExportFinding] = {
        ExportCheckCode.COLOR_MOTIF_MISSING: ExportFinding(
            ExportCheckCode.COLOR_MOTIF_MISSING, Severity.ERROR, LayerRole.COLOR_MOTIF
        ),
        ExportCheckCode.OPTIONAL_ROLE_MISSING: ExportFinding(
            ExportCheckCode.OPTIONAL_ROLE_MISSING, Severity.ERROR, LayerRole.HEIGHT_MAP,
            {"role_name": "height_map"},
        ),
        ExportCheckCode.ASSET_SIZE_MISMATCH: ExportFinding(
            ExportCheckCode.ASSET_SIZE_MISMATCH, Severity.ERROR, LayerRole.COLOR_MOTIF,
            {"actual": "4×2", "expected": "8×8"},
        ),
        ExportCheckCode.INVALID_TARGET_PARAMS: ExportFinding(
            ExportCheckCode.INVALID_TARGET_PARAMS, Severity.ERROR, None, {"detail": "x"},
        ),
        ExportCheckCode.HEIGHT_MAP_EMPTY: ExportFinding(
            ExportCheckCode.HEIGHT_MAP_EMPTY, Severity.WARNING, LayerRole.HEIGHT_MAP
        ),
        ExportCheckCode.GLOSS_MASK_EMPTY: ExportFinding(
            ExportCheckCode.GLOSS_MASK_EMPTY, Severity.WARNING, LayerRole.GLOSS_MASK
        ),
        ExportCheckCode.BIT_DEPTH_UNCONFIRMED: ExportFinding(
            ExportCheckCode.BIT_DEPTH_UNCONFIRMED, Severity.WARNING, LayerRole.HEIGHT_MAP,
            {"bits": 16},
        ),
        ExportCheckCode.HEIGHT_PRECISION_LOSS: ExportFinding(
            ExportCheckCode.HEIGHT_PRECISION_LOSS, Severity.WARNING, LayerRole.HEIGHT_MAP
        ),
        ExportCheckCode.GLOSS_INK_MODE: ExportFinding(
            ExportCheckCode.GLOSS_INK_MODE, Severity.WARNING, LayerRole.GLOSS_MASK
        ),
        ExportCheckCode.PHYSICAL_SIZE_UNVERIFIED: ExportFinding(
            ExportCheckCode.PHYSICAL_SIZE_UNVERIFIED, Severity.WARNING, None
        ),
    }
    # Jeder Code hat ein Beispiel und rendert in de/en ohne KeyError.
    assert set(samples) == set(ExportCheckCode)
    for locale in ("de", "en"):
        i18n.configure_locale(locale)
        try:
            for finding in samples.values():
                text = format_finding(finding)
                assert text and "{" not in text
        finally:
            i18n.configure_locale(i18n.DEFAULT_LOCALE)


def test_finding_i18n_key_matches_namespace() -> None:
    finding = ExportFinding(ExportCheckCode.COLOR_MOTIF_MISSING, Severity.ERROR)
    assert finding.i18n_key == "eufymake.export.color_motif_missing"


# ── Präzisionsverlust-Warnung beim 8-Bit-Ziel (#590) ─────────────────────


def _with_height_payload(project: Project, values: np.ndarray) -> Project:
    """HEIGHT-Ebene direkt aus einer kanonischen 16-Bit-Payload."""
    from bgremover.height_map import HeightField

    layer = project.create_layer(
        name="Höhe", kind=LayerKind.HEIGHT,
        height_data=HeightField(
            values, np.full(values.shape, 255, dtype=np.uint8), max_value=65535))
    project.assign_role(layer.id, LayerRole.HEIGHT_MAP)
    return project


def test_8bit_target_with_true_16bit_heights_warns_precision_loss() -> None:
    """Echte Niederbits + 8-Bit-Ziel → bestätigungspflichtige Warnung (#590)."""
    values = np.array([[0x1234, 0x0000], [0x8000, 0xFFFF]], dtype=np.uint16)
    project = _with_height_payload(_color_project((2, 2)), values)
    findings = validate_export(
        project, requested_optional_roles=(LayerRole.HEIGHT_MAP,), bit_depth=8)
    codes = [f.code for f in findings]
    assert ExportCheckCode.HEIGHT_PRECISION_LOSS in codes
    finding = next(
        f for f in findings if f.code is ExportCheckCode.HEIGHT_PRECISION_LOSS)
    assert finding.severity is Severity.WARNING
    assert format_finding(finding)                       # rendert ohne KeyError


def test_16bit_target_does_not_warn_precision_loss() -> None:
    values = np.array([[0x1234, 0x0000], [0x8000, 0xFFFF]], dtype=np.uint16)
    project = _with_height_payload(_color_project((2, 2)), values)
    findings = validate_export(
        project, requested_optional_roles=(LayerRole.HEIGHT_MAP,), bit_depth=16)
    codes = [f.code for f in findings]
    assert ExportCheckCode.HEIGHT_PRECISION_LOSS not in codes
    assert ExportCheckCode.BIT_DEPTH_UNCONFIRMED in codes


def test_8bit_target_without_low_bits_does_not_warn() -> None:
    """Reine ×257-Stufen (8-Bit-äquivalent) verlieren nichts – keine Warnung."""
    values = (np.array([[0, 1], [128, 255]], dtype=np.uint32) * 257).astype(np.uint16)
    project = _with_height_payload(_color_project((2, 2)), values)
    findings = validate_export(
        project, requested_optional_roles=(LayerRole.HEIGHT_MAP,), bit_depth=8)
    assert ExportCheckCode.HEIGHT_PRECISION_LOSS not in [f.code for f in findings]


def test_low_bit_only_variation_counts_as_non_empty() -> None:
    """Konstante 8-Bit-Ansicht, aber variierende Niederbits: nicht „leer" (#590)."""
    values = np.array([[0x0100, 0x0101], [0x0102, 0x0103]], dtype=np.uint16)
    project = _with_height_payload(_color_project((2, 2)), values)
    findings = validate_export(
        project, requested_optional_roles=(LayerRole.HEIGHT_MAP,), bit_depth=16)
    assert ExportCheckCode.HEIGHT_MAP_EMPTY not in [f.code for f in findings]
