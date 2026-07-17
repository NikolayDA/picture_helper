"""Speichern/Laden von ``.bgrproj``-Projektdateien (versioniert, atomar, validiert).

Qt-freier Round-Trip eines kompletten Mehr-Ebenen-Projekts auf die Platte. Das
Format ist ein **ZIP-Container** (ADR in #329; Formatversion 2 seit #588,
Datenvertrag in ADR #586):

- ``manifest.json`` – Formatversion, Canvas-Größe, geordnete Ebenenliste
  (id, name, kind, visible, opacity, locked, Rolle, Dateiname, Bittiefe),
  ``active_layer_id`` und projektweite Metadaten (siehe :mod:`project_schema`).
- **Eine RGBA-PNG-Datei je Ebene** (verlustfrei; für HEIGHT die abgeleitete
  8-Bit-Ansicht, deren Alphakanal die Deckung trägt).
- **Je HEIGHT-Ebene zusätzlich eine 16-Bit-Graustufen-PNG**
  (``layer_NNNN_height16.png``) mit den kanonischen ``uint16``-Höhenwerten –
  geschrieben und gelesen mit expliziter Little-Endian-Kontrolle über numpy
  (kein Verlass auf PIL-Modusdetails) und über ``height16_sha256`` im Manifest
  gegen abgeschnittene/vertauschte Payloads abgesichert.

Schreiben ist **atomar** (Muster aus ``image_ops.save_image_file``: ``mkstemp``
im Zielverzeichnis + ``os.replace``), sodass ein Abbruch keine bestehende Datei
zerstört. Lesen ist **defensiv** (Philosophie aus
``image_loading.open_validated_image``): Dateigrößen-Limit, Zip-Bomb-Schutz je
Eintrag (getrennte Limits für RGBA- und 16-Bit-Grau-Einträge), Megapixel-Limit
je Ebene, Abwehr von Zip-Slip-/unerwarteten Einträgen und klare, übersetzte
Fehlermeldungen statt Crashes. Die Versionsmigration liegt in
:mod:`project_schema` (Zukunfts-Version wird nicht überschrieben; v1-Projekte
laden über den ×257-Adapter des Modells, #587).
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import tempfile
import zipfile
from pathlib import Path

import numpy as np
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
    height16_files,
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

# Eigenes Limit für 16-Bit-Grau-Einträge (2 B/px statt 4 B/px, ADR #586):
# ``40 MP × 2 B`` plus Puffer für PNG-Metadaten.
_MAX_HEIGHT16_ENTRY_BYTES = _MAX_MEGAPIXELS * 1_000_000 * 2 + (8 * 1024 * 1024)


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


# ── 16-Bit-Höhen-Payload: Kodierung/Dekodierung (v2, #588) ───────────────
def _encode_height16_png(values: np.ndarray) -> bytes:
    """Kodiert kanonische ``uint16``-Höhenwerte als 16-Bit-Graustufen-PNG.

    Endianness-kontrolliert über numpy (ADR-#586-Risikohinweis): die Rohbytes
    werden explizit als Little-Endian (``<u2``) an PILs ``I;16``-Modus
    übergeben, statt sich auf plattformabhängige Modus-Konvertierungen zu
    verlassen. PNG speichert 16-Bit-Grau verlustfrei – der Roundtrip ist
    bitgenau (inklusive Niederbits).
    """
    h, w = values.shape
    raw = np.ascontiguousarray(values, dtype="<u2").tobytes()
    image = Image.frombytes("I;16", (w, h), raw)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _decode_height16_values(data: bytes, file_name: str) -> np.ndarray:
    """Dekodiert eine ``height16``-PNG strikt zu einem ``uint16``-Array.

    Megapixel-geprüft wie die RGBA-Ebenen; akzeptiert die 16-Bit-Grau-Modi
    (``I;16``/``I;16B`` – Rohbytes explizit über numpy gedeutet) sowie PILs
    ``I``-Fallback (32-Bit, wertebereichsgeprüft). Alles andere – 8-Bit-Grau,
    Farbbilder, undekodierbare Daten, Werte außerhalb ``0..65535`` – wird als
    :class:`ProjectFileError` abgewiesen, bevor etwas ins Projekt gelangt.
    """
    try:
        with Image.open(io.BytesIO(data)) as probe:
            mp = probe.width * probe.height / 1_000_000
            if mp > _MAX_MEGAPIXELS:
                raise ProjectFileError(
                    tr("project.error.layer_too_large", mp=mp, limit=_MAX_MEGAPIXELS)
                )
            probe.load()
            mode = probe.mode
            w, h = probe.size
            if mode in ("I;16", "I;16L", "I;16B"):
                byte_order = ">u2" if mode == "I;16B" else "<u2"
                values = np.frombuffer(
                    probe.tobytes(), dtype=byte_order
                ).reshape(h, w).astype(np.uint16)
                return values
            if mode == "I":
                arr = np.asarray(probe, dtype=np.int64)
                if arr.size and (int(arr.min()) < 0 or int(arr.max()) > 65535):
                    raise ProjectFileError(
                        tr("project.error.height16_invalid", file=file_name)
                    )
                return arr.astype(np.uint16)
    except Image.DecompressionBombError as exc:
        raise ProjectFileError(
            tr("project.error.layer_too_large", mp=0, limit=_MAX_MEGAPIXELS)
        ) from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ProjectFileError(
            tr("project.error.height16_invalid", file=file_name)
        ) from exc
    # 8-Bit-Grau/Farbmodi sind keine gültige 16-Bit-Payload (kein stilles
    # Hochrechnen an dieser Grenze – die ×257-Abbildung gehört zum v1-Pfad).
    raise ProjectFileError(tr("project.error.height16_invalid", file=file_name))


def _load_height16_values(
    zf: zipfile.ZipFile, file_name: str, expected_sha256: str
) -> np.ndarray:
    """Liest eine ``height16``-Payload integritätsgeprüft aus dem Container.

    Der sha256-Hexdigest der PNG-Bytes muss dem Manifest-Eintrag entsprechen –
    abgeschnittene oder untereinander vertauschte Payload-Dateien fallen so
    **vor** dem Dekodieren auf (#588-Integritätsvertrag).
    """
    try:
        data = zf.read(file_name)
    except KeyError as exc:
        raise ProjectFileError(
            tr("project.error.layer_file_missing", file=file_name)
        ) from exc
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ProjectFileError(
            tr("project.error.height16_integrity", file=file_name)
        )
    return _decode_height16_values(data, file_name)


# ── Speichern ────────────────────────────────────────────────────────────
def save_project(project: Project, path: str | Path) -> None:
    """Speichert ``project`` *atomar* als ``.bgrproj``-Container unter ``path``.

    Schreibt zunächst in eine temporäre Datei im Zielverzeichnis und hebt sie per
    ``os.replace`` an die Zielstelle – ein abgebrochener Schreibvorgang (Platte
    voll, Encoder-Fehler) lässt eine bereits vorhandene Datei unangetastet und
    hinterlässt keine gültig wirkende Teil-Datei. Die Ebenen werden in
    Modellreihenfolge (unten→oben) als RGBA-PNG abgelegt; HEIGHT-Ebenen
    schreiben zusätzlich ihre kanonische 16-Bit-Payload (Formatversion 2, #588)
    **direkt aus dem Modell** – ohne Rückweg über 8-Bit-RGBA – samt
    sha256-Integritätsdigest im Manifest. Ein einmal geöffnetes v1-Projekt wird
    beim Speichern dadurch kontrolliert als v2 geschrieben.
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
            for index, (layer, file_name) in enumerate(
                zip(project.layers, files, strict=True)
            ):
                buffer = io.BytesIO()
                layer.image.save(buffer, format="PNG")
                zf.writestr(file_name, buffer.getvalue())
                field = layer.height_data
                if field is not None:
                    entry = manifest["layers"][index]
                    payload = _encode_height16_png(field.values)
                    entry["height16_sha256"] = hashlib.sha256(payload).hexdigest()
                    zf.writestr(entry["height16_file"], payload)
            # Manifest zuletzt: es trägt die beim Kodieren berechneten Digests.
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


def _validate_members(
    zf: zipfile.ZipFile,
    expected_files: list[str],
    height16_names: set[str] | None = None,
) -> None:
    """Stellt sicher, dass der Container nur erwartete, sichere Einträge enthält.

    Wehrt Zip-Slip (Pfadanteile/``..``) und unerwartete Einträge ab und begrenzt
    die entpackte Größe je Eintrag (Zip-Bomb). ``expected_files`` sind die im
    Manifest deklarierten Ebenen-Dateinamen, ``height16_names`` die deklarierten
    16-Bit-Höhen-Payloads (eigenes, kleineres Limit: 2 B/px, ADR #586); erlaubt
    ist genau diese Menge plus das Manifest selbst.
    """
    height16 = height16_names or set()
    allowed = {MANIFEST_NAME, *expected_files, *height16}
    for info in zf.infolist():
        name = info.filename
        if not _is_safe_member_name(name):
            raise ProjectFileError(tr("project.error.unexpected_entry", name=name))
        if name not in allowed:
            raise ProjectFileError(tr("project.error.unexpected_entry", name=name))
        limit = (
            _MAX_HEIGHT16_ENTRY_BYTES
            if name in height16
            else _MAX_ENTRY_UNCOMPRESSED_BYTES
        )
        if info.file_size > limit:
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

    **Formatversion 2 (#588):** 16-Bit-Höhen-Payloads werden vor dem Einbau
    integritätsgeprüft (sha256 aus dem Manifest), größen-/typvalidiert und
    bitgenau wiederhergestellt; v1-Dateien laden unverändert über die
    deterministische ×257-Migration des Modells. Ein Fehlschlag lässt das
    aktuell geöffnete Projekt des Aufrufers unangetastet – erst ein
    vollständig validiertes Projekt wird zurückgegeben.
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
            height16 = height16_files(manifest)
            _validate_members(zf, expected, set(height16))
            images = {name: _load_layer_image(zf, name) for name in expected}
            height_values = {
                name: _load_height16_values(zf, name, digest)
                for name, digest in height16.items()
            }
            return project_from_manifest(
                manifest, images, height_values=height_values, warnings=warnings
            )
    except zipfile.BadZipFile as exc:
        raise ProjectFileError(tr("project.error.corrupt")) from exc
    except OSError as exc:
        logger.exception("Projektdatei konnte nicht gelesen werden: %s", p)
        raise ProjectFileError(tr("project.error.corrupt")) from exc
