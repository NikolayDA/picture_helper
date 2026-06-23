"""Qt-freies Rendern und atomares Schreiben der EufyMake-Import-Assets (#353).

Rendert die in #352 (:mod:`bgremover.eufymake_export`) geplanten Assets aus einem
``Project`` und schreibt sie als klar benannten **Exportordner** – ein
BgRemover-Importpaket für EufyMake Studio, **keine** native ``.empf``-Datei und
keine behauptete offizielle EufyMake-Containerkonvention. Reine Logik (Pillow +
Dateisystem), Qt-frei, strikt getypt.

Rendern (rein, ohne Dateisystem): :func:`render_export` erzeugt die Pixel:

- **Farbmotiv** aus :meth:`Project.composite_color` (bzw. der explizit als
  ``COLOR_MOTIF`` markierten Ebene), verlustfrei als RGBA – der Alphakanal bleibt
  erhalten.
- **Höhenkarte** aus der ``HEIGHT_MAP``-Ebene als Graustufe mit **hell = hoch,
  dunkel = niedrig** (8-Bit-``L`` bzw., wenn das Profil 16 Bit plant, ``I;16``).
- **Gloss-Maske** aus der ``GLOSS_MASK``-Ebene als Graustufe; im Manifest als
  optional/experimentell markiert (offene Semantik, siehe ADR/#352).

Schreiben (atomar): :func:`write_export` validiert zuerst (#354) – Fehler
blockieren, Warnungen erfordern ``confirm_warnings=True`` –, rendert dann
vollständig in ein temporäres Verzeichnis **im selben Verzeichnis** wie das Ziel
und veröffentlicht es in **einem** ``os.replace``-Schritt. Schlägt etwas vor der
Veröffentlichung fehl, bleibt kein halbfertiges Ziel zurück; schlägt das Ersetzen
fehl, bleibt ein vorhandenes gültiges Ziel unversehrt. Temporärdaten werden in
jedem Fehlerfall aufgeräumt.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from bgremover.eufymake_export import (
    AssetPixelFormat,
    ExportAsset,
    ExportPlan,
    build_export_plan,
)
from bgremover.eufymake_validate import (
    ExportFinding,
    split_findings,
    validate_export,
)
from bgremover.height_map import HEIGHT_MAX_8BIT, layer_to_height
from bgremover.project_model import LayerRole, Project

# Manifest-Dateiname im Exportordner (BgRemover-Konvention).
MANIFEST_FILENAME = "manifest.json"

# Resampling je Asset-Typ: glatt fürs Farbmotiv, kantenerhaltend (Nearest) für
# Graustufen-Daten, damit beim Skalieren keine Zwischen-Höhen/Graustufen erfunden
# werden. Beides ist deterministisch.
_COLOR_RESAMPLE = Image.Resampling.LANCZOS
_DATA_RESAMPLE = Image.Resampling.NEAREST


class EufyMakeWriteError(Exception):
    """Basis aller Schreib-/Render-Fehler des EufyMake-Exports."""


class ExportTargetExistsError(EufyMakeWriteError):
    """Das Ziel existiert bereits und ``overwrite`` ist nicht gesetzt."""


class ExportValidationError(EufyMakeWriteError):
    """Die Konsistenzprüfung (#354) meldete blockierende Fehler.

    ``findings`` hält die blockierenden Fehlerbefunde; der Export wurde **nicht**
    geschrieben.
    """

    def __init__(self, findings: Sequence[ExportFinding]) -> None:
        self.findings: tuple[ExportFinding, ...] = tuple(findings)
        super().__init__(f"Export blockiert: {len(self.findings)} Fehler")


class ExportConfirmationRequired(EufyMakeWriteError):
    """Es liegen nur Warnungen vor; der Aufrufer muss bewusst bestätigen.

    ``findings`` hält die Warnungen; mit ``confirm_warnings=True`` wird trotzdem
    geschrieben.
    """

    def __init__(self, findings: Sequence[ExportFinding]) -> None:
        self.findings: tuple[ExportFinding, ...] = tuple(findings)
        super().__init__(f"Bestätigung nötig: {len(self.findings)} Warnung(en)")


@dataclass(frozen=True)
class RenderedAsset:
    """Ein gerendertes Asset: der Plan-Eintrag plus das fertige Pillow-Bild."""

    asset: ExportAsset
    image: Image.Image


@dataclass(frozen=True)
class RenderedExport:
    """Das vollständige, noch nicht geschriebene Renderergebnis."""

    plan: ExportPlan
    assets: tuple[RenderedAsset, ...]
    manifest: dict[str, Any]


def _ensure_size(
    image: Image.Image, target: tuple[int, int], resample: Image.Resampling
) -> Image.Image:
    """Gibt ``image`` in Zielgröße zurück – als **eigene** Kopie (nie Eingaberef.)."""
    if image.size == target:
        return image.copy()
    return image.resize(target, resample)


def _render_color_motif(
    project: Project, asset: ExportAsset, target: tuple[int, int]
) -> Image.Image:
    """Rendert das Farbmotiv aus dem COLOR-Komposit bzw. der Rollen-Ebene (RGBA)."""
    if asset.source_layer_id is None:
        image = project.composite_color()
    else:
        image = project.layer_by_id(asset.source_layer_id).image
    rgba = image if image.mode == "RGBA" else image.convert("RGBA")
    return _ensure_size(rgba, target, _COLOR_RESAMPLE)


def _render_height(
    layer_image: Image.Image, bit_depth: int, target: tuple[int, int]
) -> Image.Image:
    """Rendert die Höhenkarte als Graustufe (hell = hoch); 8-Bit ``L`` oder 16-Bit.

    Die HEIGHT-Ebene führt ihre Höhe als ``R==G==B==Höhe`` (0..255). Der Grauwert
    *ist* die Höhe, sodass **Weiß = höchste, Schwarz = niedrigste** Stufe gilt. Für
    16 Bit wird verlustfrei auf ``0..65535`` gespreizt (``×257``); das ist der im
    Plan vorgesehene Hook, keine bestätigte EufyMake-Anforderung (#354 warnt).
    """
    values = layer_to_height(layer_image).values  # uint16, 0..HEIGHT_MAX_8BIT
    if bit_depth == 16:
        spread = values.astype(np.uint32) * (65535 // HEIGHT_MAX_8BIT)
        image = Image.fromarray(spread.astype(np.uint16))  # Modus I;16
    else:
        image = Image.fromarray(values.astype(np.uint8))  # Modus L
    return _ensure_size(image, target, _DATA_RESAMPLE)


def _render_gloss(layer_image: Image.Image, target: tuple[int, int]) -> Image.Image:
    """Rendert die Gloss-Maske als 8-Bit-Graustufe (Semantik bewusst offen)."""
    gray = layer_image.convert("L")
    return _ensure_size(gray, target, _DATA_RESAMPLE)


def _asset_manifest(asset: ExportAsset) -> dict[str, Any]:
    """Maschinenlesbare Beschreibung eines Assets fürs Manifest."""
    return {
        "filename": asset.filename,
        "role": asset.role.value,
        "pixel_format": asset.pixel_format.value,
        "bit_depth": asset.bit_depth,
        "required": asset.required,
        "experimental": asset.experimental,
    }


def _build_manifest(plan: ExportPlan) -> dict[str, Any]:
    """Baut das ``manifest.json``-Objekt aus dem Plan (reine Daten, kein UI-Text)."""
    target = plan.target
    return {
        "profile": plan.profile,
        "profile_version": plan.profile_version,
        "kind": "eufymake_import_assets",
        "note": (
            "BgRemover-Importpaket für EufyMake Studio – keine offizielle "
            "EufyMake-Spezifikation, kein natives .empf."
        ),
        "height_semantics": plan.height_semantics.value,
        "open_questions": [question.value for question in plan.open_questions],
        "target": {
            "pixel_size": list(target.pixel_size),
            "bit_depth": target.bit_depth,
            "physical_size_mm": (
                list(target.physical_size_mm) if target.physical_size_mm is not None else None
            ),
            "dpi": list(target.dpi) if target.dpi is not None else None,
        },
        "assets": [_asset_manifest(asset) for asset in plan.assets],
    }


def render_export(project: Project, plan: ExportPlan) -> RenderedExport:
    """Rendert **alle** Assets des Plans in Zielgröße (rein, ohne Dateisystem).

    Jedes Asset erhält exakt die im Plan geforderte Zielgröße
    (``plan.target.pixel_size``); abweichende Quellgrößen werden deterministisch
    resampelt (Farbmotiv glatt, Graustufen kantenerhaltend). Das Ergebnis enthält
    zusätzlich das fertige Manifest-Objekt.
    """
    target = plan.target.pixel_size
    rendered: list[RenderedAsset] = []
    for asset in plan.assets:
        if asset.role is LayerRole.COLOR_MOTIF:
            image = _render_color_motif(project, asset, target)
        elif asset.role is LayerRole.HEIGHT_MAP:
            layer = project.layer_by_id(_require_source(asset))
            image = _render_height(layer.image, asset.bit_depth, target)
        elif asset.role is LayerRole.GLOSS_MASK:
            layer = project.layer_by_id(_require_source(asset))
            image = _render_gloss(layer.image, target)
        else:  # pragma: no cover - Plan kennt nur die drei Rollen
            raise EufyMakeWriteError(f"Unbekannte Asset-Rolle: {asset.role}")
        assert image.size == target  # Zielgrößen-Invariante
        if asset.pixel_format is AssetPixelFormat.RGBA and image.mode != "RGBA":
            raise EufyMakeWriteError(f"Farb-Asset {asset.filename} ist nicht RGBA")
        rendered.append(RenderedAsset(asset=asset, image=image))
    return RenderedExport(plan=plan, assets=tuple(rendered), manifest=_build_manifest(plan))


def _require_source(asset: ExportAsset) -> str:
    """Quell-Ebenen-ID eines optionalen Assets; fehlt sie, ist der Plan inkonsistent."""
    if asset.source_layer_id is None:  # pragma: no cover - Plan setzt sie immer
        raise EufyMakeWriteError(f"Asset {asset.filename} ohne Quell-Ebene")
    return asset.source_layer_id


def _write_png(image: Image.Image, path: Path) -> None:
    """Schreibt ein Bild verlustfrei als PNG (eigene Funktion = Test-Injektionspunkt)."""
    image.save(path, "PNG")


def _write_rendered(rendered: RenderedExport, out_dir: Path) -> None:
    """Schreibt alle Assets + Manifest in ein (bereits existierendes) Verzeichnis."""
    for item in rendered.assets:
        _write_png(item.image, out_dir / item.asset.filename)
    manifest_text = json.dumps(rendered.manifest, indent=2, ensure_ascii=False)
    (out_dir / MANIFEST_FILENAME).write_text(manifest_text, encoding="utf-8")


def _publish_dir(tmp: Path, dest: Path, *, overwrite: bool) -> None:
    """Veröffentlicht ``tmp`` als ``dest`` in einem atomaren ``os.replace``-Schritt.

    Existiert ``dest`` (nur mit ``overwrite``), wird es zuerst beiseitegeschoben
    und bei einem Fehler beim Einspielen des neuen Inhalts wiederhergestellt –
    ein vorhandenes gültiges Ziel bleibt so unversehrt.
    """
    if not dest.exists():
        os.replace(tmp, dest)
        return
    backup = dest.parent / f".{dest.name}.bak-{uuid.uuid4().hex}"
    os.replace(dest, backup)
    try:
        os.replace(tmp, dest)
    except BaseException:
        os.replace(backup, dest)  # vorhandenes Ziel wiederherstellen
        raise
    shutil.rmtree(backup, ignore_errors=True)


def _atomic_publish(rendered: RenderedExport, dest: Path, *, overwrite: bool) -> Path:
    """Rendert in ein Temp-Verzeichnis im Zielordner und veröffentlicht es atomar."""
    parent = dest.parent
    if not parent.is_dir():
        raise EufyMakeWriteError(f"Zielverzeichnis existiert nicht: {parent}")
    if dest.exists() and not overwrite:
        raise ExportTargetExistsError(str(dest))
    tmp = Path(tempfile.mkdtemp(prefix=f".{dest.name}.tmp-", dir=parent))
    try:
        _write_rendered(rendered, tmp)
        _publish_dir(tmp, dest, overwrite=overwrite)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return dest


def write_export(
    project: Project,
    dest: str | os.PathLike[str],
    *,
    optional_roles: Iterable[LayerRole] | None = None,
    bit_depth: int | None = None,
    overwrite: bool = False,
    confirm_warnings: bool = False,
    validate: bool = True,
) -> Path:
    """Validiert, rendert und schreibt das EufyMake-Importpaket atomar nach ``dest``.

    ``dest`` ist der Zielordner. ``optional_roles`` wählt die einzubeziehenden
    optionalen Assets (``None`` = alle vorhandenen) und wird konsistent an Prüfung
    und Plan durchgereicht. Mit ``validate=True`` (Standard) läuft zuerst die
    Konsistenzprüfung (#354): **Fehler** lösen :class:`ExportValidationError` aus
    und verhindern jeden Schreibzugriff; liegen nur **Warnungen** vor, ist
    ``confirm_warnings=True`` nötig, sonst :class:`ExportConfirmationRequired`.
    ``overwrite`` steuert das Kollisionsverhalten: ohne es löst ein vorhandenes
    Ziel :class:`ExportTargetExistsError` aus, mit ihm wird es atomar und
    verlustsicher ersetzt. Gibt den geschriebenen Zielpfad zurück.
    """
    target_dir = Path(dest)
    if validate:
        errors, warnings = split_findings(
            validate_export(
                project, requested_optional_roles=optional_roles, bit_depth=bit_depth
            )
        )
        if errors:
            raise ExportValidationError(errors)
        if warnings and not confirm_warnings:
            raise ExportConfirmationRequired(warnings)
    plan = build_export_plan(project, optional_roles=optional_roles, bit_depth=bit_depth)
    rendered = render_export(project, plan)
    return _atomic_publish(rendered, target_dir, overwrite=overwrite)
