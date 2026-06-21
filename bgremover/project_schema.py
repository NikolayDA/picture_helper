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

Fehler werden als :class:`ProjectFileError` mit bereits übersetzter,
nutzerverständlicher Meldung geworfen (deutsche/englische Laufzeit-Keys), damit
die UI-Anbindung (#334) sie unverändert anzeigen kann.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from PIL import Image

from bgremover.constants import logger
from bgremover.i18n import tr
from bgremover.project_model import (
    PROJECT_VERSION,
    Layer,
    LayerKind,
    LayerRole,
    Project,
    ProjectModelError,
)

# Formatversion des ``.bgrproj``-Manifests (unabhängig von ``Project.version``,
# der Modell-Schemaversion). Eigener Schlüssel mit Migrationshaken.
PROJECT_FORMAT_VERSION = 1

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


# ── Project -> Manifest ──────────────────────────────────────────────────
def build_manifest(project: Project) -> dict[str, Any]:
    """Baut das JSON-taugliche Manifest-``dict`` eines Projekts.

    Die Ebenen werden in Modellreihenfolge (Index 0 = unten) abgelegt; jede
    erhält den Dateinamen ihres PNG im Container. ``bit_depth`` ist je Ebene
    reserviert (heute 8), damit spätere 16-Bit-Height-Maps ohne Formatbruch
    ergänzt werden können. ``metadata`` muss JSON-serialisierbar sein.
    """
    layers: list[dict[str, Any]] = []
    for index, layer in enumerate(project.layers):
        layers.append(
            {
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
        )
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


# ── Versionierung / Migration ────────────────────────────────────────────
def _migrate_0_to_1(manifest: dict[str, Any]) -> dict[str, Any]:
    """No-op-Migration für die erste explizit versionierte Manifest-Generation."""
    return manifest


# Migrationen von Manifest-Version N nach N+1 (auch No-op-Schritte explizit
# registriert, damit jede unterstützte Vorversion einen Weg zur aktuellen hat).
_MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {
    0: _migrate_0_to_1,
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


def project_from_manifest(
    manifest: Mapping[str, Any],
    images: Mapping[str, Image.Image],
) -> Project:
    """Rekonstruiert ein :class:`Project` aus Manifest + dekodierten Ebenenbildern.

    ``images`` bildet den Manifest-Dateinamen je Ebene auf das **bereits**
    dekodierte, größengeprüfte RGBA-Bild ab (Dekodierung/Megapixel-Schutz liegen
    in :mod:`project_io`). Strukturelle Verstöße (fehlende Felder, unbekannte
    Kind/Rolle, doppelte Rollen/IDs, Größenabweichung, unbekannte aktive ID)
    werden als :class:`ProjectFileError` mit klarer Meldung abgewiesen.
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
        try:
            project.add_layer(
                Layer(
                    name=name,
                    kind=kind,
                    image=image,
                    id=layer_id,
                    visible=visible,
                    opacity=float(opacity),
                    locked=locked,
                    role=role,
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
