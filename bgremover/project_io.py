"""Speichern/Laden von ``.bgrproj``-Projektdateien (versioniert, atomar, validiert).

Qt-freier Round-Trip eines kompletten Mehr-Ebenen-Projekts auf die Platte. Das
Format ist ein **ZIP-Container** (ADR in #329):

- ``manifest.json`` – Formatversion, Canvas-Größe, geordnete Ebenenliste
  (id, name, kind, visible, opacity, locked, Rolle, Dateiname, Bittiefe),
  ``active_layer_id`` und projektweite Metadaten (siehe :mod:`project_schema`).
- **Eine PNG-Datei je Ebene** (RGBA, verlustfrei).

Schreiben ist **atomar** (Muster aus ``image_ops.save_image_file``: ``mkstemp``
im Zielverzeichnis + ``os.replace``), sodass ein Abbruch keine bestehende Datei
zerstört. Lesen ist **defensiv** (Philosophie aus
``image_loading.open_validated_image``): Dateigrößen-Limit, Zip-Bomb-Schutz je
Eintrag, Megapixel-Limit je Ebene, Abwehr von Zip-Slip-/unerwarteten Einträgen
und klare, übersetzte Fehlermeldungen statt Crashes. Die Versionsmigration liegt
in :mod:`project_schema` (Zukunfts-Version wird nicht überschrieben).
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import zipfile
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from bgremover.constants import (
    _MAX_MEGAPIXELS,
    _MAX_PROJECT_FILE_BYTES,
    logger,
)
from bgremover.i18n import tr
from bgremover.project_model import Project
from bgremover.project_schema import (
    MANIFEST_NAME,
    ProjectFileError,
    build_manifest,
    layer_files,
    migrate_manifest,
    project_from_manifest,
)

# Standard-Dateiendung.
PROJECT_SUFFIX = ".bgrproj"

# Obergrenze der **entpackten** Größe eines einzelnen ZIP-Eintrags (Zip-Bomb-
# Schutz). Eine RGBA-Ebene am Megapixel-Limit belegt ``_MAX_MEGAPIXELS`` · 4 MB;
# etwas Reserve für PNG-Metadaten/Manifest obendrauf.
_MAX_ENTRY_UNCOMPRESSED_BYTES = _MAX_MEGAPIXELS * 1_000_000 * 4 + (8 * 1024 * 1024)


def _is_safe_member_name(name: str) -> bool:
    """True, wenn ``name`` ein harmloser Basisname ohne Pfadanteile ist.

    Wehrt Zip-Slip ab: keine Verzeichnistrenner, kein ``..``/``.``, nicht
    absolut, keine Laufwerks-/UNC-Pfade. Erlaubt sind genau die von uns selbst
    geschriebenen flachen Namen (``manifest.json``, ``layer_NNNN.png``).
    """
    if not name or name in (".", ".."):
        return False
    if "/" in name or "\\" in name:
        return False
    if os.path.isabs(name) or os.path.splitdrive(name)[0]:
        return False
    return name == os.path.basename(name)


# ── Speichern ────────────────────────────────────────────────────────────
def save_project(project: Project, path: str | Path) -> None:
    """Speichert ``project`` *atomar* als ``.bgrproj``-Container unter ``path``.

    Schreibt zunächst in eine temporäre Datei im Zielverzeichnis und hebt sie per
    ``os.replace`` an die Zielstelle – ein abgebrochener Schreibvorgang (Platte
    voll, Encoder-Fehler) lässt eine bereits vorhandene Datei unangetastet. Die
    Ebenen werden in Modellreihenfolge (unten→oben) als RGBA-PNG abgelegt.
    """
    out = Path(path)
    manifest = build_manifest(project)
    files = layer_files(manifest)

    # ``mkstemp`` + manuelles Aufräumen: wir brauchen den Pfad für ``os.replace``;
    # bei Fehler wird die Temp-Datei entfernt.
    fd, tmp_name = tempfile.mkstemp(dir=str(out.parent), suffix=".bgrproj.tmp")
    try:
        with (
            os.fdopen(fd, "wb") as raw,
            zipfile.ZipFile(raw, "w", zipfile.ZIP_DEFLATED) as zf,
        ):
            for layer, file_name in zip(project.layers, files, strict=True):
                buffer = io.BytesIO()
                layer.image.save(buffer, format="PNG")
                zf.writestr(file_name, buffer.getvalue())
            zf.writestr(
                MANIFEST_NAME,
                json.dumps(manifest, ensure_ascii=False, indent=2),
            )
        os.replace(tmp_name, out)
    except BaseException:
        # Temp-Datei bei jedem Abbruch (auch KeyboardInterrupt) entfernen.
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise


# ── Laden ────────────────────────────────────────────────────────────────
def _read_manifest(zf: zipfile.ZipFile) -> dict:
    try:
        raw = zf.read(MANIFEST_NAME)
    except KeyError as exc:
        raise ProjectFileError(tr("project.error.manifest_missing")) from exc
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProjectFileError(tr("project.error.manifest_invalid")) from exc
    if not isinstance(manifest, dict):
        raise ProjectFileError(tr("project.error.manifest_invalid"))
    return manifest


def _validate_members(zf: zipfile.ZipFile, expected_files: list[str]) -> None:
    """Stellt sicher, dass der Container nur erwartete, sichere Einträge enthält.

    Wehrt Zip-Slip (Pfadanteile/``..``) und unerwartete Einträge ab und begrenzt
    die entpackte Größe je Eintrag (Zip-Bomb). ``expected_files`` sind die im
    Manifest deklarierten Ebenen-Dateinamen; erlaubt ist genau diese Menge plus
    das Manifest selbst.
    """
    allowed = {MANIFEST_NAME, *expected_files}
    for info in zf.infolist():
        name = info.filename
        if not _is_safe_member_name(name):
            raise ProjectFileError(tr("project.error.unexpected_entry", name=name))
        if name not in allowed:
            raise ProjectFileError(tr("project.error.unexpected_entry", name=name))
        if info.file_size > _MAX_ENTRY_UNCOMPRESSED_BYTES:
            raise ProjectFileError(tr("project.error.entry_too_large", name=name))


def _load_layer_image(zf: zipfile.ZipFile, file_name: str) -> Image.Image:
    """Dekodiert eine Ebenen-PNG aus dem Container nach RGBA – größengeprüft."""
    try:
        data = zf.read(file_name)
    except KeyError as exc:
        raise ProjectFileError(
            tr("project.error.layer_file_missing", file=file_name)
        ) from exc
    try:
        with Image.open(io.BytesIO(data)) as probe:
            mp = probe.width * probe.height / 1_000_000
            if mp > _MAX_MEGAPIXELS:
                raise ProjectFileError(
                    tr("project.error.layer_too_large", mp=mp, limit=_MAX_MEGAPIXELS)
                )
            return probe.convert("RGBA")
    except Image.DecompressionBombError as exc:
        raise ProjectFileError(
            tr("project.error.layer_too_large", mp=0, limit=_MAX_MEGAPIXELS)
        ) from exc
    except (UnidentifiedImageError, OSError) as exc:
        raise ProjectFileError(tr("project.error.manifest_invalid")) from exc


def load_project(path: str | Path, *, warnings: list[str] | None = None) -> Project:
    """Lädt und validiert eine ``.bgrproj``-Datei und gibt das Projekt zurück.

    Wirft :class:`ProjectFileError` mit klarer, übersetzter Meldung bei
    beschädigten/zu großen Dateien, fehlenden Manifest-Einträgen, zu großen oder
    abweichend dimensionierten Ebenen und Zip-Slip-/unerwarteten Einträgen –
    ohne Crash. Eine **neuere** Formatversion wird best-effort geladen (Warnung,
    Datei bleibt unangetastet; siehe :func:`project_schema.migrate_manifest`).

    Wird ``warnings`` übergeben, sammelt der Loader dort nutzerverständliche,
    bereits übersetzte Hinweise zu verlustfrei geheilten Altzuständen (etwa eine
    entfernte inkompatible ``HEIGHT_MAP``-Rolle, #364), die die UI anzeigen kann.
    """
    p = Path(path)
    try:
        size = os.path.getsize(p)
    except OSError as exc:
        raise ProjectFileError(tr("project.error.corrupt")) from exc
    if size > _MAX_PROJECT_FILE_BYTES:
        raise ProjectFileError(
            tr(
                "project.error.too_large",
                size=size // (1024 * 1024),
                limit=_MAX_PROJECT_FILE_BYTES // (1024 * 1024),
            )
        )

    try:
        with zipfile.ZipFile(p) as zf:
            manifest = _read_manifest(zf)
            manifest = migrate_manifest(manifest)
            expected = layer_files(manifest)
            _validate_members(zf, expected)
            images = {name: _load_layer_image(zf, name) for name in expected}
            return project_from_manifest(manifest, images, warnings=warnings)
    except zipfile.BadZipFile as exc:
        raise ProjectFileError(tr("project.error.corrupt")) from exc
    except OSError as exc:
        logger.exception("Projektdatei konnte nicht gelesen werden: %s", p)
        raise ProjectFileError(tr("project.error.corrupt")) from exc
