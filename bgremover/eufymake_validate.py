"""Qt-freie Konsistenzprüfung für EufyMake-Studio-Import-Assets (#354).

Prüft **vor** dem Rendern/Schreiben (#353), ob BgRemover aus einem ``Project``
ein technisch konsistentes Set importierbarer Studio-Assets erzeugen kann. Das
Modul liefert eine deterministisch sortierte, strukturierte Befundliste
(:class:`ExportFinding`) mit stabilem Code, Schweregrad (``error``/``warning``),
betroffener Assetrolle, i18n-Key und Platzhaltern – **ohne** Dialoge, ohne
Dateisystem und ohne Rendering. Damit bleibt die Prüflogik für eine spätere
allgemeine Pre-Export-Prüfung wiederverwendbar (UI-Texte/Dialoge gehören nicht
hierher).

Vertrag (deckungsgleich mit der ADR ``docs/history/ADR-2026-eufymake-exportpaket.md``
und #352): Es wird **keine** offizielle EufyMake-Triplet-/Container-/Gloss-
Konvention behauptet. Harte Fehler blockieren den Export; Warnungen erlauben ihn
erst nach bewusster Bestätigung durch den aufrufenden Workflow. Gesichert ist nur
die Height-Semantik **hell = hoch**; offene Bittiefen-, Gloss- und Größenannahmen
erscheinen ausschließlich als nicht blockierende Warnungen.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from PIL import Image

from bgremover.eufymake_export import (
    InvalidBitDepthError,
    InvalidPhysicalSizeError,
    _derive_physical_size,
    can_render_color_motif,
    coerce_bit_depth,
)
from bgremover.height_map import layer_to_height
from bgremover.i18n import tr
from bgremover.project_model import LayerRole, Project

# Optionale Rollen, die der Aufrufer für den Export auswählen kann. Das Farbmotiv
# (``COLOR_MOTIF``) ist immer erforderlich und daher hier nicht enthalten.
_OPTIONAL_ROLES: tuple[LayerRole, ...] = (LayerRole.HEIGHT_MAP, LayerRole.GLOSS_MASK)

# Namensraum aller i18n-Keys dieses Moduls. Der konkrete Key eines Befunds ist
# ``f"{_I18N_PREFIX}{code.value}"`` (siehe ``ExportFinding.i18n_key``); die
# de/en-Übersetzungen liegen zentral in :mod:`bgremover.i18n`.
_I18N_PREFIX = "eufymake.export."


class Severity(Enum):
    """Schweregrad eines Befunds."""

    ERROR = "error"  # blockiert den Export
    WARNING = "warning"  # erlaubt den Export erst nach bewusster Bestätigung


class ExportCheckCode(Enum):
    """Stabile Befund-Codes der Konsistenzprüfung (Reihenfolge = Sortierrang).

    Die Reihenfolge ist Teil des Vertrags: sie bestimmt die deterministische
    Sortierung der Befundliste (zuerst nach Schweregrad, dann nach dieser
    Deklarationsreihenfolge, dann nach Rolle).
    """

    # ── Harte Fehler (blockieren) ───────────────────────────────────────
    COLOR_MOTIF_MISSING = "color_motif_missing"
    OPTIONAL_ROLE_MISSING = "optional_role_missing"
    ASSET_SIZE_MISMATCH = "asset_size_mismatch"
    INVALID_TARGET_PARAMS = "invalid_target_params"
    # ── Warnungen (Export nach Bestätigung möglich) ─────────────────────
    HEIGHT_MAP_EMPTY = "height_map_empty"
    GLOSS_MASK_EMPTY = "gloss_mask_empty"
    BIT_DEPTH_UNCONFIRMED = "bit_depth_unconfirmed"
    GLOSS_INK_MODE = "gloss_ink_mode"
    PHYSICAL_SIZE_UNVERIFIED = "physical_size_unverified"


# Schweregrad je Code – die einzige Quelle der Wahrheit für „blockiert ja/nein".
_SEVERITY: dict[ExportCheckCode, Severity] = {
    ExportCheckCode.COLOR_MOTIF_MISSING: Severity.ERROR,
    ExportCheckCode.OPTIONAL_ROLE_MISSING: Severity.ERROR,
    ExportCheckCode.ASSET_SIZE_MISMATCH: Severity.ERROR,
    ExportCheckCode.INVALID_TARGET_PARAMS: Severity.ERROR,
    ExportCheckCode.HEIGHT_MAP_EMPTY: Severity.WARNING,
    ExportCheckCode.GLOSS_MASK_EMPTY: Severity.WARNING,
    ExportCheckCode.BIT_DEPTH_UNCONFIRMED: Severity.WARNING,
    ExportCheckCode.GLOSS_INK_MODE: Severity.WARNING,
    ExportCheckCode.PHYSICAL_SIZE_UNVERIFIED: Severity.WARNING,
}

# Deklarationsrang je Code für die stabile Sortierung.
_CODE_ORDER: dict[ExportCheckCode, int] = {
    code: index for index, code in enumerate(ExportCheckCode)
}


@dataclass(frozen=True)
class ExportFinding:
    """Ein strukturierter Prüfbefund (rein deklarativ, Qt-frei).

    ``code`` ist stabil, ``severity`` ergibt sich daraus, ``role`` benennt die
    betroffene Assetrolle (oder ``None`` für globale Befunde). ``params`` hält die
    Platzhalterwerte der i18n-Meldung. Die Rendern-zu-Klartext-Verantwortung liegt
    bei :func:`format_finding` bzw. der UI (#355) – nicht im Befund selbst.
    """

    code: ExportCheckCode
    severity: Severity
    role: LayerRole | None = None
    params: Mapping[str, object] = field(default_factory=dict)

    @property
    def i18n_key(self) -> str:
        """Zentraler i18n-Key dieses Befunds (Namensraum ``eufymake.export.``)."""
        return f"{_I18N_PREFIX}{self.code.value}"

    @property
    def is_error(self) -> bool:
        return self.severity is Severity.ERROR


def _finding(code: ExportCheckCode, role: LayerRole | None = None, **params: object) -> ExportFinding:
    """Baut einen Befund mit dem für ``code`` registrierten Schweregrad."""
    return ExportFinding(code=code, severity=_SEVERITY[code], role=role, params=params)


def _sort_key(finding: ExportFinding) -> tuple[int, int, str]:
    """Deterministische Sortierung: Fehler vor Warnungen, dann Code, dann Rolle."""
    severity_rank = 0 if finding.severity is Severity.ERROR else 1
    role_rank = finding.role.value if finding.role is not None else ""
    return (severity_rank, _CODE_ORDER[finding.code], role_rank)


def _gray_array(image: Image.Image) -> np.ndarray:
    """Einkanaliges Graustufen-Array (``uint8``) eines Ebenenbildes."""
    return np.asarray(image.convert("L"))


def _is_constant(values: np.ndarray) -> bool:
    """True, wenn alle Werte gleich sind (konstantes – oft nutzloses – Asset)."""
    return values.size == 0 or bool(values.min() == values.max())


def validate_export(
    project: Project,
    *,
    requested_optional_roles: Iterable[LayerRole] | None = None,
    target_size: tuple[int, int] | None = None,
    bit_depth: int | None = None,
) -> tuple[ExportFinding, ...]:
    """Prüft ``project`` auf konsistente, exportierbare Import-Assets.

    ``requested_optional_roles`` benennt die optionalen Rollen, die der Aufrufer
    exportieren möchte; ``None`` bedeutet „alle aktuell im Projekt vergebenen
    optionalen Rollen". ``target_size`` ist die gemeinsame Zielgröße ``(w, h)``;
    ``None`` nutzt die Canvas-Größe. ``bit_depth`` überschreibt die aus den
    Metadaten abgeleitete Tiefe (UI-Wahl 8/16). Es werden **alle** zutreffenden
    Befunde gesammelt (nicht nur der erste) und deterministisch sortiert
    zurückgegeben – Fehler vor Warnungen.
    """
    target = target_size if target_size is not None else project.size
    if requested_optional_roles is None:
        requested = tuple(r for r in _OPTIONAL_ROLES if project.layer_by_role(r) is not None)
    else:
        wanted = set(requested_optional_roles)
        requested = tuple(r for r in _OPTIONAL_ROLES if r in wanted)

    findings: list[ExportFinding] = []

    # ── Zielparameter (Bittiefe / physische Größe) ──────────────────────
    effective_bit_depth: int | None = None
    try:
        effective_bit_depth = coerce_bit_depth(project.metadata, bit_depth)
    except InvalidBitDepthError as exc:
        findings.append(_finding(ExportCheckCode.INVALID_TARGET_PARAMS, detail=str(exc)))
    physical_size: tuple[float, float] | None = None
    try:
        physical_size = _derive_physical_size(project.metadata)
    except InvalidPhysicalSizeError as exc:
        findings.append(_finding(ExportCheckCode.INVALID_TARGET_PARAMS, detail=str(exc)))
    if target[0] <= 0 or target[1] <= 0:
        findings.append(
            _finding(
                ExportCheckCode.INVALID_TARGET_PARAMS,
                detail=f"Zielgröße muss positiv sein, war {target[0]}x{target[1]}",
            )
        )

    # ── Farbmotiv (erforderlich) ────────────────────────────────────────
    if not can_render_color_motif(project):
        findings.append(_finding(ExportCheckCode.COLOR_MOTIF_MISSING, role=LayerRole.COLOR_MOTIF))
    else:
        motif_layer = project.layer_by_role(LayerRole.COLOR_MOTIF)
        motif_size = motif_layer.size if motif_layer is not None else project.size
        if motif_size != target:
            findings.append(
                _finding(
                    ExportCheckCode.ASSET_SIZE_MISMATCH,
                    role=LayerRole.COLOR_MOTIF,
                    actual=_fmt_size(motif_size),
                    expected=_fmt_size(target),
                )
            )

    # ── Optionale Rollen (Height / Gloss) ───────────────────────────────
    for role in requested:
        layer = project.layer_by_role(role)
        if layer is None:
            findings.append(
                _finding(ExportCheckCode.OPTIONAL_ROLE_MISSING, role=role, role_name=role.value)
            )
            continue
        if layer.size != target:
            findings.append(
                _finding(
                    ExportCheckCode.ASSET_SIZE_MISMATCH,
                    role=role,
                    actual=_fmt_size(layer.size),
                    expected=_fmt_size(target),
                )
            )
        if role is LayerRole.HEIGHT_MAP:
            field_ = layer_to_height(layer.image)
            if int(field_.coverage.max(initial=0)) == 0 or _is_constant(field_.values):
                findings.append(_finding(ExportCheckCode.HEIGHT_MAP_EMPTY, role=role))
            if effective_bit_depth == 16:
                findings.append(
                    _finding(
                        ExportCheckCode.BIT_DEPTH_UNCONFIRMED, role=role, bits=effective_bit_depth
                    )
                )
        elif role is LayerRole.GLOSS_MASK:
            if _is_constant(_gray_array(layer.image)):
                findings.append(_finding(ExportCheckCode.GLOSS_MASK_EMPTY, role=role))
            # Gloss bleibt ein Import-/Hilfsasset – Ink-Mode/Layerzuweisung in Studio.
            findings.append(_finding(ExportCheckCode.GLOSS_INK_MODE, role=role))

    # ── Physische Größe / DPI: plausibel, aber kein Herstellervertrag ───
    if physical_size is not None:
        findings.append(_finding(ExportCheckCode.PHYSICAL_SIZE_UNVERIFIED))

    return tuple(sorted(findings, key=_sort_key))


def _fmt_size(size: tuple[int, int]) -> str:
    """Formatiert eine Größe ``(w, h)`` als ``"w×h"`` für Meldungen."""
    return f"{size[0]}×{size[1]}"


def has_blocking_errors(findings: Iterable[ExportFinding]) -> bool:
    """True, wenn mindestens ein blockierender Fehler vorliegt."""
    return any(finding.is_error for finding in findings)


def split_findings(
    findings: Iterable[ExportFinding],
) -> tuple[tuple[ExportFinding, ...], tuple[ExportFinding, ...]]:
    """Teilt Befunde in ``(errors, warnings)`` – stabile Reihenfolge bleibt erhalten."""
    items = tuple(findings)
    errors = tuple(f for f in items if f.is_error)
    warnings = tuple(f for f in items if not f.is_error)
    return errors, warnings


def format_finding(finding: ExportFinding) -> str:
    """Qt-freie, lokalisierte Klartextmeldung eines Befunds (de/en über ``tr``).

    Nutzt je Code einen **literalen** i18n-Key, damit die zentrale Coverage-Prüfung
    (``test_no_unused_keys_in_table``) jede Meldung als referenziert erkennt. Die
    eigentliche Dialog-/UI-Anbindung folgt in #355; hier entsteht nur der
    übersetzte String (z. B. für Logs, Tests und später die UI).
    """
    p = dict(finding.params)
    code = finding.code
    if code is ExportCheckCode.COLOR_MOTIF_MISSING:
        return tr("eufymake.export.color_motif_missing")
    if code is ExportCheckCode.OPTIONAL_ROLE_MISSING:
        return tr("eufymake.export.optional_role_missing", **p)
    if code is ExportCheckCode.ASSET_SIZE_MISMATCH:
        return tr("eufymake.export.asset_size_mismatch", **p)
    if code is ExportCheckCode.INVALID_TARGET_PARAMS:
        return tr("eufymake.export.invalid_target_params", **p)
    if code is ExportCheckCode.HEIGHT_MAP_EMPTY:
        return tr("eufymake.export.height_map_empty")
    if code is ExportCheckCode.GLOSS_MASK_EMPTY:
        return tr("eufymake.export.gloss_mask_empty")
    if code is ExportCheckCode.BIT_DEPTH_UNCONFIRMED:
        return tr("eufymake.export.bit_depth_unconfirmed", **p)
    if code is ExportCheckCode.GLOSS_INK_MODE:
        return tr("eufymake.export.gloss_ink_mode")
    if code is ExportCheckCode.PHYSICAL_SIZE_UNVERIFIED:
        return tr("eufymake.export.physical_size_unverified")
    raise AssertionError(f"Unbehandelter Befund-Code: {code}")  # pragma: no cover
