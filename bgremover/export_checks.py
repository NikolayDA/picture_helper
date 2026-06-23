"""Allgemeine, Qt-freie Pre-Export-Prüfung (#379).

Verallgemeinert das in :mod:`bgremover.eufymake_validate` (#354) bewusst
wiederverwendbar geschnittene Befund-Framework zu einer **geteilten Basis**, die
vor *jedem* Export/Speichern laufen kann – nicht nur für EufyMake. Geliefert wird
eine deterministisch sortierte, strukturierte Befundliste (:class:`Finding`) mit
stabilem Code, Schweregrad (``error``/``warning``), i18n-Key und Platzhaltern –
**ohne** Dialoge, Dateisystem oder Rendering von Drittsystemen.

Konventionen analog ``project_model``/``units``: reine Logik ohne Datei-/Netz-/
Qt-Zugriffe, deutsche Docstrings, englische Identifier, strikte mypy-Typisierung.
Allgemeine, formatunabhängige Prüfungen (Abmessungen, DPI-Plausibilität, Farbraum,
Transparenz, leere Ausgabe, Druckfläche) leben hier; produktspezifische
Konventionsprüfungen (z. B. EufyMake-Rollen) bleiben in ihren Fachmodulen und
bauen lediglich auf den hier definierten Primitiven (:class:`Severity`,
:func:`has_blocking_errors`, :func:`split_findings`) auf.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, TypeVar

import numpy as np
from PIL import Image

from bgremover.constants import _MAX_MEGAPIXELS
from bgremover.i18n import tr
from bgremover.project_model import Project
from bgremover.units import UnitsError

# Namensraum aller i18n-Keys dieses Moduls. Der konkrete Key eines Befunds ist
# ``f"{_I18N_PREFIX}{code.value}"`` (siehe :attr:`Finding.i18n_key`).
_I18N_PREFIX = "export.checks."

# Plausibilitätsgrenzen der Auflösung (DPI). Bewusst weit gefasst, damit echte
# Druckaufträge (Foto ~150–300, UV/Gravur bis einige Tausend) nicht fälschlich
# beanstandet werden; nur grob unplausible Werte lösen eine **Warnung** aus.
MIN_PLAUSIBLE_DPI = 30.0
MAX_PLAUSIBLE_DPI = 5000.0


class Severity(Enum):
    """Schweregrad eines Befunds (geteilt über alle Prüfmodule)."""

    ERROR = "error"  # blockiert den Export
    WARNING = "warning"  # erlaubt den Export erst nach bewusster Bestätigung


def severity_rank(severity: Severity) -> int:
    """Sortierrang eines Schweregrads: Fehler (0) vor Warnungen (1)."""
    return 0 if severity is Severity.ERROR else 1


class _Severable(Protocol):
    """Strukturelle Mindestschnittstelle für die geteilten Befund-Helfer.

    Als **lesbares** Property deklariert, damit auch eingefrorene Befund-
    Dataclasses (``frozen=True``, deren Felder mypy als nur-lesbar führt) wie
    :class:`Finding` und ``eufymake_validate.ExportFinding`` strukturell passen.
    """

    @property
    def severity(self) -> Severity: ...


_FindingT = TypeVar("_FindingT", bound=_Severable)


def has_blocking_errors(findings: Iterable[_Severable]) -> bool:
    """True, wenn mindestens ein blockierender Fehler vorliegt.

    Geteilt für alle Befundtypen (eigene wie EufyMake-spezifische), solange sie
    einen ``severity`` tragen.
    """
    return any(finding.severity is Severity.ERROR for finding in findings)


def split_findings(
    findings: Iterable[_FindingT],
) -> tuple[tuple[_FindingT, ...], tuple[_FindingT, ...]]:
    """Teilt Befunde in ``(errors, warnings)`` – stabile Reihenfolge bleibt erhalten."""
    items = tuple(findings)
    errors = tuple(f for f in items if f.severity is Severity.ERROR)
    warnings = tuple(f for f in items if f.severity is not Severity.ERROR)
    return errors, warnings


class CheckCode(Enum):
    """Stabile Befund-Codes der allgemeinen Prüfung (Reihenfolge = Sortierrang).

    Die Deklarationsreihenfolge ist Teil des Vertrags: sie bestimmt – nach dem
    Schweregrad – die deterministische Sortierung der Befundliste.
    """

    # ── Harte Fehler (blockieren) ───────────────────────────────────────
    DIMENSIONS_INVALID = "dimensions_invalid"
    DIMENSIONS_TOO_LARGE = "dimensions_too_large"
    COLOR_SPACE_UNEXPECTED = "color_space_unexpected"
    OUTPUT_EMPTY = "output_empty"
    # ── Warnungen (Export nach Bestätigung möglich) ─────────────────────
    RESOLUTION_TOO_LOW = "resolution_too_low"
    RESOLUTION_TOO_HIGH = "resolution_too_high"
    FULLY_TRANSPARENT = "fully_transparent"
    UNEXPECTED_ALPHA = "unexpected_alpha"
    PRINT_AREA_EXCEEDED = "print_area_exceeded"


# Schweregrad je Code – die einzige Quelle der Wahrheit für „blockiert ja/nein".
_SEVERITY: dict[CheckCode, Severity] = {
    CheckCode.DIMENSIONS_INVALID: Severity.ERROR,
    CheckCode.DIMENSIONS_TOO_LARGE: Severity.ERROR,
    CheckCode.COLOR_SPACE_UNEXPECTED: Severity.ERROR,
    CheckCode.OUTPUT_EMPTY: Severity.ERROR,
    CheckCode.RESOLUTION_TOO_LOW: Severity.WARNING,
    CheckCode.RESOLUTION_TOO_HIGH: Severity.WARNING,
    CheckCode.FULLY_TRANSPARENT: Severity.WARNING,
    CheckCode.UNEXPECTED_ALPHA: Severity.WARNING,
    CheckCode.PRINT_AREA_EXCEEDED: Severity.WARNING,
}

# Deklarationsrang je Code für die stabile Sortierung.
_CODE_ORDER: dict[CheckCode, int] = {code: index for index, code in enumerate(CheckCode)}


@dataclass(frozen=True)
class Finding:
    """Ein strukturierter Prüfbefund der allgemeinen Prüfung (rein deklarativ).

    ``code`` ist stabil, ``severity`` ergibt sich daraus, ``params`` hält die
    Platzhalterwerte der i18n-Meldung. Die Übersetzung übernimmt
    :func:`format_finding`.
    """

    code: CheckCode
    severity: Severity
    params: Mapping[str, object] = field(default_factory=dict)

    @property
    def i18n_key(self) -> str:
        """Zentraler i18n-Key dieses Befunds (Namensraum ``export.checks.``)."""
        return f"{_I18N_PREFIX}{self.code.value}"

    @property
    def is_error(self) -> bool:
        return self.severity is Severity.ERROR


def _finding(code: CheckCode, **params: object) -> Finding:
    """Baut einen Befund mit dem für ``code`` registrierten Schweregrad."""
    return Finding(code=code, severity=_SEVERITY[code], params=params)


def _sort_key(finding: Finding) -> tuple[int, int]:
    """Deterministische Sortierung: Fehler vor Warnungen, dann Code-Reihenfolge."""
    return (severity_rank(finding.severity), _CODE_ORDER[finding.code])


def sort_findings(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    """Sortiert Befunde deterministisch (Fehler vor Warnungen, dann Code-Rang)."""
    return tuple(sorted(findings, key=_sort_key))


# ── Einzelprüfungen (rein, je Kategorie separat testbar) ───────────────────
def check_dimensions(
    size: tuple[int, int], *, max_megapixels: float = _MAX_MEGAPIXELS
) -> list[Finding]:
    """Prüft die Pixelabmessungen: positiv und innerhalb des Megapixel-Limits."""
    width, height = size
    findings: list[Finding] = []
    if width <= 0 or height <= 0:
        findings.append(
            _finding(CheckCode.DIMENSIONS_INVALID, width=width, height=height)
        )
        return findings
    megapixels = width * height / 1_000_000
    if megapixels > max_megapixels:
        findings.append(
            _finding(
                CheckCode.DIMENSIONS_TOO_LARGE,
                mp=round(megapixels, 1),
                limit=round(max_megapixels, 1),
            )
        )
    return findings


def check_resolution(
    dpi: tuple[float, float] | None,
    *,
    min_dpi: float = MIN_PLAUSIBLE_DPI,
    max_dpi: float = MAX_PLAUSIBLE_DPI,
) -> list[Finding]:
    """Prüft die Auflösung (DPI) auf Plausibilität – nur wenn ``dpi`` vorliegt.

    Konsumiert die aus physischer Größe + Pixelgröße abgeleitete DPI (#376). Eine
    fehlende DPI (``None``) liefert keinen Befund (keine erfundene Auflösung).
    """
    if dpi is None:
        return []
    findings: list[Finding] = []
    low = min(dpi)
    high = max(dpi)
    if low < min_dpi:
        findings.append(
            _finding(CheckCode.RESOLUTION_TOO_LOW, dpi=round(low, 1), minimum=round(min_dpi, 1))
        )
    if high > max_dpi:
        findings.append(
            _finding(CheckCode.RESOLUTION_TOO_HIGH, dpi=round(high, 1), maximum=round(max_dpi, 1))
        )
    return findings


def check_color_space(image: Image.Image, *, expected: str = "RGBA") -> list[Finding]:
    """Prüft den Farbraum eines Bildes gegen den erwarteten Modus (Standard RGBA)."""
    if image.mode != expected:
        return [
            _finding(
                CheckCode.COLOR_SPACE_UNEXPECTED, actual=image.mode, expected=expected
            )
        ]
    return []


def check_transparency(image: Image.Image) -> list[Finding]:
    """Prüft die Transparenz: vollständig transparent bzw. unerwartete Teiltransparenz.

    Ohne Alphakanal (kein ``A`` im Modus) gibt es nichts zu prüfen. Sonst:
    ``FULLY_TRANSPARENT`` wenn das Alpha überall 0 ist (keine sichtbaren Pixel),
    ``UNEXPECTED_ALPHA`` wenn es teiltransparente Pixel (``0 < a < 255``) gibt –
    harte Freistellungskanten (nur 0/255) bleiben unbeanstandet.
    """
    if "A" not in image.getbands():
        return []
    alpha = np.asarray(image.convert("RGBA"))[:, :, 3]
    if alpha.size == 0:
        return []
    if int(alpha.max()) == 0:
        return [_finding(CheckCode.FULLY_TRANSPARENT)]
    partial = int(np.count_nonzero((alpha > 0) & (alpha < 255)))
    if partial > 0:
        percent = round(100.0 * partial / alpha.size, 1)
        return [_finding(CheckCode.UNEXPECTED_ALPHA, percent=percent)]
    return []


def check_print_area(
    physical_size_mm: tuple[float, float] | None,
    medium_size_mm: tuple[float, float] | None,
) -> list[Finding]:
    """Prüft, ob die physische Motivgröße die Zielmedium-/Druckfläche überschreitet.

    Nutzt die physische Größe (mm) aus #376. Nur wenn **beide** Größen vorliegen;
    sonst kein Befund. Überschreitet das Motiv eine der beiden Kanten, entsteht
    eine Warnung mit den konkreten Maßen.
    """
    if physical_size_mm is None or medium_size_mm is None:
        return []
    motif_w, motif_h = physical_size_mm
    medium_w, medium_h = medium_size_mm
    if motif_w > medium_w or motif_h > medium_h:
        return [
            _finding(
                CheckCode.PRINT_AREA_EXCEEDED,
                width=round(motif_w, 1),
                height=round(motif_h, 1),
                medium_w=round(medium_w, 1),
                medium_h=round(medium_h, 1),
            )
        ]
    return []


def check_export(
    project: Project,
    *,
    target_size: tuple[int, int] | None = None,
    medium_size_mm: tuple[float, float] | None = None,
    min_dpi: float = MIN_PLAUSIBLE_DPI,
    max_dpi: float = MAX_PLAUSIBLE_DPI,
) -> tuple[Finding, ...]:
    """Allgemeine Pre-Export-Prüfung eines Projekts – deterministisch sortiert.

    Führt alle allgemeinen Prüfungen zusammen: Abmessungen (``target_size`` oder
    Canvas-Größe), Farbraum/Transparenz des Farb-Komposits, Auflösungs-Plausibilität
    (aus der Projekt-DPI, #376) und – sofern ``medium_size_mm`` gesetzt ist – die
    Druckflächenprüfung. Ein Projekt **ohne Ebenen** ergibt eine leere Ausgabe
    (``OUTPUT_EMPTY``); andernfalls werden die Komposit-basierten Prüfungen
    durchlaufen. Ein (defensiv) korrupter Metadatenwert für die physische Größe
    unterdrückt nur die davon abhängigen Prüfungen, statt hart zu scheitern.
    """
    size = target_size if target_size is not None else project.size
    findings: list[Finding] = []
    findings += check_dimensions(size)

    if len(project) == 0:
        findings.append(_finding(CheckCode.OUTPUT_EMPTY))
    else:
        composite = project.composite_color()
        findings += check_color_space(composite)
        findings += check_transparency(composite)

    try:
        dpi = project.dpi
        physical = project.physical_size_mm
    except UnitsError:
        dpi, physical = None, None
    findings += check_resolution(dpi, min_dpi=min_dpi, max_dpi=max_dpi)
    findings += check_print_area(physical, medium_size_mm)

    return sort_findings(findings)


def format_finding(finding: Finding) -> str:
    """Qt-freie, lokalisierte Klartextmeldung eines Befunds (de/en über ``tr``).

    Nutzt je Code einen **literalen** i18n-Key, damit die zentrale Coverage-Prüfung
    jede Meldung als referenziert erkennt.
    """
    p = dict(finding.params)
    code = finding.code
    if code is CheckCode.DIMENSIONS_INVALID:
        return tr("export.checks.dimensions_invalid", **p)
    if code is CheckCode.DIMENSIONS_TOO_LARGE:
        return tr("export.checks.dimensions_too_large", **p)
    if code is CheckCode.COLOR_SPACE_UNEXPECTED:
        return tr("export.checks.color_space_unexpected", **p)
    if code is CheckCode.OUTPUT_EMPTY:
        return tr("export.checks.output_empty")
    if code is CheckCode.RESOLUTION_TOO_LOW:
        return tr("export.checks.resolution_too_low", **p)
    if code is CheckCode.RESOLUTION_TOO_HIGH:
        return tr("export.checks.resolution_too_high", **p)
    if code is CheckCode.FULLY_TRANSPARENT:
        return tr("export.checks.fully_transparent")
    if code is CheckCode.UNEXPECTED_ALPHA:
        return tr("export.checks.unexpected_alpha", **p)
    if code is CheckCode.PRINT_AREA_EXCEEDED:
        return tr("export.checks.print_area_exceeded", **p)
    raise AssertionError(f"Unbehandelter Befund-Code: {code}")  # pragma: no cover
