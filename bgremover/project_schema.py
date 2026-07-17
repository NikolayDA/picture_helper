"""Versioniertes Manifest-Schema für das ``.bgrproj``-Projektformat.

Qt-freie Brücke zwischen dem Domänenmodell (:mod:`bgremover.project_model`) und
der serialisierten Manifest-Form (ein JSON-taugliches ``dict``), die
:mod:`bgremover.project_io` in den ZIP-Container schreibt bzw. daraus liest.

Versionierung analog ``settings_schema``: das Manifest trägt einen eigenen
``version``-Schlüssel mit Migrationshaken. Ältere Versionen durchlaufen die
registrierten ``_MIGRATIONS``-Schritte; die **gleiche** Version ist ein No-op;
eine **neuere** (Zukunfts-)Version wird **nicht** umgeschrieben – es wird nur
gewarnt und das Manifest best-effort weiterverarbeitet (Vorwärtskompatibilität:
unbekannte Felder werden ignoriert).

**Formatversion 2 (#588, ADR #586):** Je HEIGHT-Ebene referenziert das
Manifest zusätzlich eine 16-Bit-Graustufen-PNG (``layer_NNNN_height16.png``)
mit den kanonischen Höhenwerten (``height16_file``), deren Integrität über
``height16_sha256`` (Hexdigest der PNG-Bytes) abgesichert ist;
``height16_max_value`` fixiert den Wertebereich (immer ``65535``). Das
bestehende 8-Bit-RGBA-PNG bleibt je Ebene erhalten – für HEIGHT enthält es die
abgeleitete Ansicht, deren Alphakanal weiterhin die Deckung trägt (bewusste
Redundanz: Deckungs-Transport, einheitliche RGBA-Pipeline, 8-Bit-Sicht für
externe Werkzeuge). Ältere Anwendungsstände (bis 2.6.0) können v2-Dateien
**nicht** öffnen – ihr Container-Validator weist die ``height16``-Zusatzdatei
als unerwarteten Eintrag ab (klarer Fehler, keine stille Beschädigung).
v1-Projekte laden unverändert: HEIGHT-Ebenen **ohne** ``height16_file``
migrieren deterministisch über den ×257-Adapter des Modells; in einer echten
v2-Datei ist eine fehlende Payload-Deklaration dagegen ein Integritätsverstoß.

Fehler werden als :class:`ProjectFileError` mit bereits übersetzter,
nutzerverständlicher Meldung geworfen (deutsche/englische Laufzeit-Keys), damit
die UI-Anbindung (#334) sie unverändert anzeigen kann.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import numpy as np
from PIL import Image

from bgremover.constants import logger
from bgremover.height_map import HEIGHT_MAX_16BIT, HeightField, HeightMapError
from bgremover.i18n import tr
from bgremover.project_model import (
    PROJECT_VERSION,
    Layer,
    LayerKind,
    LayerRole,
    Project,
    ProjectModelError,
    role_allowed_for_kind,
)

# Formatversion des ``.bgrproj``-Manifests (unabhängig von ``Project.version``,
# der Modell-Schemaversion). Eigener Schlüssel mit Migrationshaken.
# Version 2 (#588): 16-Bit-HEIGHT-Payload je Höhenebene (siehe Modul-Doku).
PROJECT_FORMAT_VERSION = 2

# Manifest-Dateiname im ZIP-Container und Namensschema der Ebenen-Bilddateien.
MANIFEST_NAME = "manifest.json"


class ProjectFileError(Exception):
    """Projektdatei ist beschädigt, unvollständig oder nicht interpretierbar.

    Die ``args[0]``-Meldung ist bereits via :func:`tr` übersetzt und für die
    direkte Anzeige in der UI gedacht.
    """


def _layer_filename(index: int) -> str:
    """Stabiler, sicherer Basisname der Bilddatei einer Ebene (von unten gezählt)."""
    return f"layer_{index:04d}.png"


def _layer_height16_filename(index: int) -> str:
    """Basisname der 16-Bit-Höhen-Payload einer HEIGHT-Ebene (v2, #588)."""
    return f"layer_{index:04d}_height16.png"


# ── Project -> Manifest ──────────────────────────────────────────────────
def build_manifest(project: Project) -> dict[str, Any]:
    """Baut das JSON-taugliche Manifest-``dict`` eines Projekts (Format v2).

    Die Ebenen werden in Modellreihenfolge (Index 0 = unten) abgelegt; jede
    erhält den Dateinamen ihres RGBA-PNG im Container. Eine HEIGHT-Ebene
    referenziert zusätzlich ihre kanonische 16-Bit-Payload (``height16_file``,
    ``height16_max_value``; ``bit_depth`` wird dort informativ 16). Den
    Integritäts-Hexdigest ``height16_sha256`` ergänzt ``project_io.save_project``
    beim Kodieren der PNG-Bytes. ``metadata`` muss JSON-serialisierbar sein.
    """
    layers: list[dict[str, Any]] = []
    for index, layer in enumerate(project.layers):
        entry: dict[str, Any] = {
            "id": layer.id,
            "name": layer.name,
            "kind": layer.kind.value,
            "visible": layer.visible,
            "opacity": layer.opacity,
            "locked": layer.locked,
            "role": layer.role.value if layer.role is not None else None,
            "bit_depth": 8,
            "file": _layer_filename(index),
        }
        if layer.height_data is not None:
            entry["bit_depth"] = 16
            entry["height16_file"] = _layer_height16_filename(index)
            entry["height16_max_value"] = HEIGHT_MAX_16BIT
        layers.append(entry)
    return {
        "version": PROJECT_FORMAT_VERSION,
        "project_version": project.version,
        "width": project.width,
        "height": project.height,
        "active_layer_id": project.active_layer_id,
        "metadata": dict(project.metadata),
        "layers": layers,
    }


def layer_files(manifest: Mapping[str, Any]) -> list[str]:
    """Liste der im Manifest referenzierten Ebenen-Dateinamen (Reihenfolge: unten→oben)."""
    raw_layers = manifest.get("layers")
    if not isinstance(raw_layers, list):
        raise ProjectFileError(tr("project.error.manifest_invalid"))
    files: list[str] = []
    for entry in raw_layers:
        if not isinstance(entry, Mapping):
            raise ProjectFileError(tr("project.error.manifest_invalid"))
        name = entry.get("file")
        if not isinstance(name, str):
            raise ProjectFileError(tr("project.error.manifest_invalid"))
        files.append(name)
    return files


def height16_files(manifest: Mapping[str, Any]) -> dict[str, str]:
    """Mapping ``height16``-Dateiname → erwarteter sha256-Hexdigest (v2, #588).

    Liefert alle im Manifest deklarierten 16-Bit-Höhen-Payloads. Ein Eintrag,
    der ``height16_file`` deklariert, **muss** einen ``height16_sha256``-String
    tragen (Integritätsvertrag des Containers); fehlende/falsch typisierte
    Digests, Nicht-String-Dateinamen, Duplikate und Kollisionen mit den
    RGBA-Dateinamen werden als :class:`ProjectFileError` abgewiesen –
    vertauschte oder abgeschnittene Payloads fallen so vor jedem Dekodieren auf.
    """
    raw_layers = manifest.get("layers")
    if not isinstance(raw_layers, list):
        raise ProjectFileError(tr("project.error.manifest_invalid"))
    rgba_names = set(layer_files(manifest))
    result: dict[str, str] = {}
    for entry in raw_layers:
        if not isinstance(entry, Mapping):
            raise ProjectFileError(tr("project.error.manifest_invalid"))
        name = entry.get("height16_file")
        if name is None:
            continue
        if not isinstance(name, str):
            raise ProjectFileError(tr("project.error.manifest_invalid"))
        digest = entry.get("height16_sha256")
        if not isinstance(digest, str) or not digest:
            raise ProjectFileError(tr("project.error.manifest_invalid"))
        if name in result or name in rgba_names or name == MANIFEST_NAME:
            raise ProjectFileError(tr("project.error.manifest_invalid"))
        result[name] = digest
    return result


# ── Versionierung / Migration ────────────────────────────────────────────
def _migrate_0_to_1(manifest: dict[str, Any]) -> dict[str, Any]:
    """No-op-Migration für die erste explizit versionierte Manifest-Generation."""
    return manifest


def _migrate_1_to_2(manifest: dict[str, Any]) -> dict[str, Any]:
    """v1 → v2 (#588): strukturell ein No-op – die 8→16-Abbildung liegt im Modell.

    Ein v1-Manifest kennt keine ``height16_file``-Einträge; solche HEIGHT-Ebenen
    rekonstruiert :func:`project_from_manifest` über den befristeten
    ×257-Adapter des Modells (#587) deterministisch und verlustfrei im Sinne
    der ursprünglichen 256 Stufen (ADR #586). Beim nächsten Speichern entsteht
    kontrolliert eine vollwertige v2-Datei mit 16-Bit-Payload.
    """
    return manifest


# Migrationen von Manifest-Version N nach N+1 (auch No-op-Schritte explizit
# registriert, damit jede unterstützte Vorversion einen Weg zur aktuellen hat).
_MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {
    0: _migrate_0_to_1,
    1: _migrate_1_to_2,
}


def migrate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Bringt ``manifest`` auf ``PROJECT_FORMAT_VERSION``.

    - Gleiche Version: unverändert zurück.
    - Ältere Version: registrierte ``_MIGRATIONS`` anwenden, ``version`` heben.
    - **Neuere** Version: unangetastet zurück, nur warnen (kein Downgrade) –
      das Laden bleibt best-effort vorwärtskompatibel.
    """
    version = manifest.get("version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise ProjectFileError(tr("project.error.manifest_invalid"))

    if version == PROJECT_FORMAT_VERSION:
        return manifest
    if version > PROJECT_FORMAT_VERSION:
        logger.warning(
            "Projektdatei-Formatversion %d ist neuer als die unterstützte "
            "Version %d – lade best-effort, die Datei bleibt unverändert.",
            version, PROJECT_FORMAT_VERSION,
        )
        return manifest

    migrated = manifest
    for step_version in range(version, PROJECT_FORMAT_VERSION):
        step = _MIGRATIONS.get(step_version)
        if step is None:
            raise ProjectFileError(
                tr("project.error.unsupported_version", version=version)
            )
        migrated = step(migrated)
    migrated = {**migrated, "version": PROJECT_FORMAT_VERSION}
    return migrated


# ── Manifest -> Project ──────────────────────────────────────────────────
def _require(manifest: Mapping[str, Any], key: str, types: type | tuple[type, ...]) -> Any:
    value = manifest.get(key)
    # ``bool`` ist Subtyp von ``int`` – wo ``int`` erwartet wird, echte Booleans
    # nicht durchrutschen lassen.
    if isinstance(value, bool) and types is int:
        raise ProjectFileError(tr("project.error.manifest_invalid"))
    if not isinstance(value, types):
        raise ProjectFileError(tr("project.error.manifest_invalid"))
    return value


def _enum_from_value(enum_cls: type, value: Any) -> Any:
    try:
        return enum_cls(value)
    except ValueError as exc:
        raise ProjectFileError(tr("project.error.manifest_invalid")) from exc


def _height_field_from_entry(
    entry: Mapping[str, Any],
    *,
    kind: LayerKind,
    image: Image.Image,
    height_values: Mapping[str, np.ndarray] | None,
    canvas_size: tuple[int, int],
    require_height16: bool = False,
) -> HeightField | None:
    """Baut die kanonische 16-Bit-Payload eines v2-``height16``-Eintrags (#588).

    ``None``, wenn der Eintrag keine Payload deklariert (COLOR/GLOSS/GENERIC
    sowie v1-/Legacy-HEIGHT – Letztere migriert der Modell-Adapter). Stammt das
    Manifest nachweislich aus einer v2-Datei (``require_height16``), ist eine
    HEIGHT-Ebene **ohne** Payload-Deklaration dagegen ein Integritätsverstoß
    (abgeschnittenes/manipuliertes Archiv) und wird abgewiesen – der stille
    Rückfall auf die requantisierte 8-Bit-Ansicht bleibt echten v1-Dateien
    vorbehalten. Deklariert ein Nicht-HEIGHT-Eintrag eine Payload, ist
    ``height16_max_value`` nicht der Vertragswert ``65535``, fehlt das
    dekodierte Array, passt Shape/dtype/Wertebereich nicht oder verletzt die
    Kombination die Modell-Invarianten, wird ebenfalls mit
    :class:`ProjectFileError` abgewiesen – keine stillen Reparaturen an
    Pixeldaten. Die Deckung stammt aus dem Alphakanal des (bereits
    canvas-größengeprüften) RGBA-PNGs der Ebene.
    """
    file_name = entry.get("height16_file")
    if file_name is None:
        if require_height16 and kind is LayerKind.HEIGHT:
            raise ProjectFileError(tr("project.error.manifest_invalid"))
        return None
    if not isinstance(file_name, str) or kind is not LayerKind.HEIGHT:
        raise ProjectFileError(tr("project.error.manifest_invalid"))
    max_value = entry.get("height16_max_value")
    if max_value != HEIGHT_MAX_16BIT:
        raise ProjectFileError(
            tr("project.error.height16_invalid", file=file_name)
        )
    values = None if height_values is None else height_values.get(file_name)
    if values is None:
        raise ProjectFileError(
            tr("project.error.layer_file_missing", file=file_name)
        )
    width, height = canvas_size
    if values.ndim != 2:
        raise ProjectFileError(
            tr("project.error.height16_invalid", file=file_name)
        )
    if values.shape != (height, width):
        raise ProjectFileError(
            tr(
                "project.error.layer_size_mismatch",
                expected=f"{width}x{height}",
                actual=f"{values.shape[1]}x{values.shape[0]}",
            )
        )
    coverage = np.array(image, dtype=np.uint8)[:, :, 3].copy()
    try:
        return HeightField(values, coverage, HEIGHT_MAX_16BIT)
    except HeightMapError as exc:
        raise ProjectFileError(
            tr("project.error.height16_invalid", file=file_name)
        ) from exc


def project_from_manifest(
    manifest: Mapping[str, Any],
    images: Mapping[str, Image.Image],
    *,
    height_values: Mapping[str, np.ndarray] | None = None,
    warnings: list[str] | None = None,
    require_height16: bool = False,
) -> Project:
    """Rekonstruiert ein :class:`Project` aus Manifest + dekodierten Ebenendaten.

    ``images`` bildet den Manifest-Dateinamen je Ebene auf das **bereits**
    dekodierte, größengeprüfte RGBA-Bild ab (Dekodierung/Megapixel-Schutz liegen
    in :mod:`project_io`); ``height_values`` analog den ``height16_file``-Namen
    auf das dekodierte, integritätsgeprüfte ``uint16``-Array (v2, #588).
    Strukturelle Verstöße (fehlende Felder, unbekannte Kind/Rolle, doppelte
    Rollen/IDs, Größenabweichung, unbekannte aktive ID, ``height16``-Payloads
    mit falschem Typ/Shape/Wertebereich oder auf Nicht-HEIGHT-Ebenen) werden
    als :class:`ProjectFileError` mit klarer Meldung abgewiesen – **bevor**
    etwas in ein aktives Projekt eingebaut wird.

    **v1-/Legacy-HEIGHT (#587/#588):** Eine HEIGHT-Ebene ohne
    ``height16_file`` wird über den befristeten Modell-Adapter deterministisch
    (``×257``) aus dem R-Kanal ihres RGBA-PNGs rekonstruiert. Da die Migration
    v1-Manifeste bereits vor diesem Aufruf auf Version 2 hebt, sagt der
    Aufrufer über ``require_height16`` an, ob die Datei **ursprünglich** eine
    v2-Datei war – dort ist eine HEIGHT-Ebene ohne Payload-Deklaration ein
    Verstoß gegen den Integritätsvertrag und wird abgewiesen.

    **Legacy-Normalisierung (#364):** Ein von älteren Versionen geschriebener,
    inkompatibler Zustand – etwa ``HEIGHT_MAP`` auf einer Nicht-HEIGHT-Ebene –
    wird deterministisch geheilt: nur die unzulässige Rolle wird entfernt; Kind,
    Name, Pixel, Reihenfolge und übrige Metadaten bleiben wertgleich. Jede
    Korrektur wird protokolliert und – falls ``warnings`` übergeben ist – als
    bereits übersetzte, nutzerverständliche Warnung dort angehängt.
    """
    width = _require(manifest, "width", int)
    height = _require(manifest, "height", int)
    if width <= 0 or height <= 0:
        raise ProjectFileError(tr("project.error.manifest_invalid"))

    metadata = manifest.get("metadata", {})
    if not isinstance(metadata, Mapping):
        raise ProjectFileError(tr("project.error.manifest_invalid"))
    project_version = manifest.get("project_version", PROJECT_VERSION)
    if not isinstance(project_version, int) or isinstance(project_version, bool):
        raise ProjectFileError(tr("project.error.manifest_invalid"))

    project = Project(
        width, height, version=project_version, metadata=dict(metadata)
    )

    raw_layers = _require(manifest, "layers", list)
    for entry in raw_layers:
        if not isinstance(entry, Mapping):
            raise ProjectFileError(tr("project.error.manifest_invalid"))
        layer_id = _require(entry, "id", str)
        name = _require(entry, "name", str)
        kind = _enum_from_value(LayerKind, entry.get("kind"))
        visible = _require(entry, "visible", bool)
        opacity = entry.get("opacity")
        if not isinstance(opacity, (int, float)) or isinstance(opacity, bool):
            raise ProjectFileError(tr("project.error.manifest_invalid"))
        locked = _require(entry, "locked", bool)
        raw_role = entry.get("role")
        role = None if raw_role is None else _enum_from_value(LayerRole, raw_role)
        if role is not None and not role_allowed_for_kind(role, kind):
            # Historisch inkompatibler Zustand (z. B. HEIGHT_MAP auf COLOR vor
            # #364): nur die unzulässige Rolle entfernen – alles andere bleibt
            # wertgleich. So lädt das Projekt verlustfrei statt hart zu scheitern.
            logger.warning(
                "Inkompatible Rolle %s auf Ebene %r (Typ %s) beim Laden entfernt.",
                role, name, kind,
            )
            if warnings is not None:
                warnings.append(tr("project.warning.role_normalized", name=name))
            role = None
        file_name = _require(entry, "file", str)

        image = images.get(file_name)
        if image is None:
            raise ProjectFileError(
                tr("project.error.layer_file_missing", file=file_name)
            )
        if image.size != (width, height):
            raise ProjectFileError(
                tr(
                    "project.error.layer_size_mismatch",
                    expected=f"{width}x{height}",
                    actual=f"{image.width}x{image.height}",
                )
            )
        field = _height_field_from_entry(
            entry, kind=kind, image=image, height_values=height_values,
            canvas_size=(width, height), require_height16=require_height16,
        )
        try:
            project.add_layer(
                Layer(
                    name=name,
                    kind=kind,
                    image=None if field is not None else image,
                    id=layer_id,
                    visible=visible,
                    opacity=float(opacity),
                    locked=locked,
                    role=role,
                    height_data=field,
                ),
                make_active=False,
            )
        except (ProjectModelError, ValueError) as exc:
            raise ProjectFileError(tr("project.error.manifest_invalid")) from exc

    active_id = manifest.get("active_layer_id")
    if active_id is not None:
        if not isinstance(active_id, str) or not project.has_layer(active_id):
            raise ProjectFileError(tr("project.error.manifest_invalid"))
        project.set_active(active_id)
    return project
