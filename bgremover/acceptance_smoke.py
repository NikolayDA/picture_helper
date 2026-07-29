"""Nativer EufyMake-Export-/2.7.0-Projekt-Automationshook des gepackten
Artefakts (#685-Review, Codex-Fund auf PR #720).

``tests/test_e2e_release_regression.py`` bindet seinen EufyMake-Export- und
2.7.0-Projekt-Nachweis an den **Source-Checkout** (``pip install -e ".[test]"``
in ``release-abnahme.yml``), nicht an das über ``run_id``/``release_tag``
bezogene, tatsächlich gepackte Kandidatenartefakt – bei abweichendem Build-SHA
oder einer Paketierungslücke bliebe die Abnahme trotzdem grün. Dieser Hook
schließt genau diese Lücke, analog zu ``screenshot3d.py``/
``BGREMOVER_SCREENSHOT_3D`` für den 3D-Nachweis: läuft aus dem **laufenden,
gepackten Prozess** heraus (AppImage/.deb/.app), nicht aus dem Checkout.

Drei Prüfungen, alle ohne externe Testdaten aus dem Paket selbst:

1. **EufyMake-Export-Smoke** – erzeugt ein Beispielbild, generiert eine
   Höhenkarte und schreibt das Importpaket über den echten
   ``bgremover.eufymake_writer.write_export``-Pfad.
2. **2.7.0-Projekt-Öffnen** – lädt eine echte, mit dem tatsächlichen
   v2.7.0-Release-Code gebaute ``.bgrproj``-Datei (Pfad kommt aus dem
   Source-Checkout, der ohnehin im selben Abnahme-Job liegt – nur der
   *Code*, der sie verarbeitet, muss aus dem Paket stammen) und prüft, dass
   das Laden keine Migration/Warnung auslöst, **alle** persistierten Felder
   (IDs, Namen, Metadaten, Schemaversion) sowie Farbmotiv-/Höhenkarten-Pixel
   gegen die beim Fixture-Bau protokollierten Referenzwerte wertgleich sind
   (dieselbe Prüftiefe wie ``tests/test_project_v270_upgrade.py``, #685-
   Review nach PR #721) und sich das Projekt danach bitgenau weiterbearbeiten
   lässt (Höhen-Op + Undo).
3. **Fehlendes optionales KI-Backend** – erzwingt ``REMBG_AVAILABLE = False``
   im laufenden, gepackten Prozess (unabhängig davon, ob dieses konkrete
   Build tatsächlich mit oder ohne ``--ai`` gepackt wurde) und prüft, dass
   die KI-Aktion die etablierte, übersetzte Meldung zeigt statt eines
   stillen Funktionsausfalls oder Absturzes – dieselbe Prüfung wie
   ``tests/test_main_window.py``, hier zusätzlich aus dem gepackten Artefakt
   heraus (#685-Review).

Aktiviert über ``BGREMOVER_ACCEPTANCE_EXTRA`` (Ziel-JSON-Pfad) und
``BGREMOVER_ACCEPTANCE_EXTRA_V270_PROJECT`` (Pfad der ``.bgrproj``-Fixture) in
``bgremover.app.main``. Wirft nie – jeder Fehlschlag kommt strukturiert über
:class:`AcceptanceExtraResult` zurück, damit der Aufrufer einen sauberen
Exit-Code setzen kann.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

from bgremover import height_ops
from bgremover.eufymake_writer import write_export
from bgremover.height_map import HEIGHT_MAX_16BIT, generate_from_image
from bgremover.i18n import tr
from bgremover.project_model import Layer, LayerKind, LayerRole
from bgremover.project_schema import PROJECT_FORMAT_VERSION

if TYPE_CHECKING:
    from bgremover.main_window import MainWindow

_EVIDENCE_SCHEMA = 1

# Vom Fixture-Bau (tests/build_v270_fixture.py, echter v2.7.0-Code)
# protokollierte Werte – identisch zu den Konstanten in
# tests/test_project_v270_upgrade.py, hier dupliziert, weil dieser Hook aus
# dem gepackten Artefakt läuft und nicht auf das tests/-Paket zugreifen kann.
_V270_COLOR_ID = "50530890db2d4515baec0862fb89cc49"
_V270_HEIGHT_ID = "eed93ecfb5264b278ee2e5e0782ca86a"
_V270_EXPECTED_METADATA = {
    "physical_size_mm": [50.0, 30.0],
    "fixture_source": "v2.7.0 (echter Release-Code, #685-Nachweis)",
}


def _v270_gradient(size: int = 16) -> Image.Image:
    """Dieselbe Quelle wie beim Bau des Fixtures (identisch zu
    tests/test_project_v270_upgrade.py)."""
    img = Image.new("RGBA", (size, size))
    for x in range(size):
        for y in range(size):
            img.putpixel((x, y), (x * 16 % 256, y * 16 % 256, (x + y) * 8 % 256, 255))
    return img


@dataclass(frozen=True)
class AcceptanceExtraResult:
    """Ergebnis eines Automationslaufs (immer strukturiert, wirft nie)."""

    ok: bool
    eufymake_ok: bool
    eufymake_message: str
    v270_ok: bool
    v270_message: str
    missing_component_ok: bool
    missing_component_message: str


def _height_hash(layer: Layer | None) -> str | None:
    if layer is None or layer.height_data is None:
        return None
    return hashlib.sha256(layer.height_data.values.tobytes()).hexdigest()


def _run_v270_project_smoke(window: MainWindow, fixture: Path) -> tuple[bool, str]:
    """Öffnet das echte 2.7.0-Projekt über den echten Anwenderpfad, vergleicht
    **alle** persistierten Felder plus Farbmotiv-/Höhenkarten-Payload gegen
    die beim Fixture-Bau protokollierten Referenzwerte (dieselbe Prüftiefe wie
    ``tests/test_project_v270_upgrade.py``, hier zusätzlich aus dem
    gepackten Artefakt heraus) und bearbeitet es danach bitgenau weiter."""
    if not fixture.is_file():
        return False, f"2.7.0-Fixture fehlt: {fixture}"

    # Formatversion direkt aus der rohen Manifest-Datei lesen und gegen das im
    # gepackten Prozess geltende PROJECT_FORMAT_VERSION prüfen – project.version
    # ist das separate, semantische "project_version"-Feld (immer 1) und sagt
    # nichts über die .bgrproj-Schemaversion aus. Weicht die Manifest-Version
    # vom Paket-Konstante ab, ist der No-Migration-Pfad nicht mehr garantiert,
    # und `load_project` würde (still, ohne UI-Warnung) migrieren.
    with zipfile.ZipFile(fixture) as zf:
        manifest = json.loads(zf.read("manifest.json"))
    manifest_version = manifest.get("version")
    if manifest_version != PROJECT_FORMAT_VERSION:
        return False, (
            f"2.7.0-Fixture-Manifest meldet Formatversion {manifest_version!r}, "
            f"gepacktes PROJECT_FORMAT_VERSION ist {PROJECT_FORMAT_VERSION!r} – "
            "Migrationspfad wäre nicht mehr ausgeschlossen."
        )

    window._load_project_into_canvas(str(fixture))
    expected_message = tr("project.opened", name=fixture.name)
    actual_message = window._sb.currentMessage()
    if actual_message != expected_message:
        return False, (
            f"2.7.0-Projekt löste einen unerwarteten Hinweis aus: {actual_message!r}"
        )

    project = window._canvas.project
    kinds: list[LayerKind] = [] if project is None else [layer.kind for layer in project.layers]
    if kinds != [LayerKind.COLOR, LayerKind.HEIGHT]:
        return False, f"2.7.0-Projekt hat unerwartete Ebenenstruktur: {kinds}"
    assert project is not None

    if project.version != 1:
        return False, f"2.7.0-Projekt: unerwartete Schemaversion {project.version}"
    if project.metadata != _V270_EXPECTED_METADATA:
        return False, f"2.7.0-Projekt: Metadaten weichen ab: {project.metadata}"

    if project.active_layer_id != _V270_COLOR_ID:
        return False, f"2.7.0-Projekt: aktive Ebene verändert ({project.active_layer_id!r})"

    color, height = project.layers
    if color.id != _V270_COLOR_ID or color.name != "Farbmotiv":
        return False, (
            f"2.7.0-Projekt: Farb-Ebene verändert (id={color.id!r}, name={color.name!r})"
        )
    if color.role is not None or not color.visible or color.opacity != 1.0 or color.locked:
        return False, (
            f"2.7.0-Projekt: Farb-Ebenen-Zustand verändert (role={color.role!r}, "
            f"visible={color.visible!r}, opacity={color.opacity!r}, locked={color.locked!r})"
        )
    if height.id != _V270_HEIGHT_ID or height.name != "Höhenkarte":
        return False, (
            f"2.7.0-Projekt: Höhen-Ebene verändert (id={height.id!r}, name={height.name!r})"
        )
    if height.role is not LayerRole.HEIGHT_MAP or height.height_data is None:
        return False, "2.7.0-Projekt: HEIGHT-Ebene ohne HEIGHT_MAP-Rolle/Payload."
    if not height.visible or height.opacity != 1.0 or height.locked:
        return False, (
            f"2.7.0-Projekt: Höhen-Ebenen-Zustand verändert (visible={height.visible!r}, "
            f"opacity={height.opacity!r}, locked={height.locked!r})"
        )

    expected_color = _v270_gradient()
    if not np.array_equal(np.asarray(color.image), np.asarray(expected_color)):
        return False, "2.7.0-Projekt: Farbmotiv weicht vom erwarteten Fixture-Inhalt ab."
    expected_field = generate_from_image(expected_color, max_value=HEIGHT_MAX_16BIT)
    if height.height_data.max_value != HEIGHT_MAX_16BIT or not (
        np.array_equal(height.height_data.values, expected_field.values)
        and np.array_equal(height.height_data.coverage, expected_field.coverage)
    ):
        return False, "2.7.0-Projekt: Höhenkarten-Payload weicht von der erwarteten Referenz ab."

    window._canvas.set_active_layer(height.id)
    hash_before = _height_hash(height)
    window._canvas.apply_height_op(lambda f: height_ops.quantize(f, 4))
    after_op = window._canvas.project.active_layer() if window._canvas.project else None
    hash_after_op = _height_hash(after_op)
    if hash_after_op is None or hash_after_op == hash_before:
        return False, "2.7.0-Projekt: Höhen-Op auf der aktivierten HEIGHT-Ebene war ein No-op."

    window._canvas.undo()
    after_undo = window._canvas.project.active_layer() if window._canvas.project else None
    hash_after_undo = _height_hash(after_undo)
    if hash_after_undo != hash_before:
        return False, "2.7.0-Projekt: Undo stellte die Payload nicht bitgenau wieder her."

    return True, "2.7.0-Projekt öffnet ohne Migration und lässt sich bitgenau weiterbearbeiten."


def _run_missing_component_smoke(window: MainWindow) -> tuple[bool, str]:
    """Simuliert ein fehlendes optionales KI-Backend und prüft die Meldung.

    Erzwingt ``REMBG_AVAILABLE = False`` nur für die Dauer dieser Prüfung
    (unabhängig vom tatsächlichen ``--ai``-Build dieses Artefakts) und setzt
    den Originalwert danach zuverlässig zurück, damit nachfolgende Prüfungen
    im selben Prozess unbeeinflusst bleiben. Ein zuvor geladenes Projekt
    (das 2.7.0-Fixture) liefert das Bild, ohne das die KI-Aktion vorher schon
    mit dem "kein Bild geladen"-Hinweis abbrechen würde.
    """
    import bgremover.main_window as main_window_module

    original = main_window_module.REMBG_AVAILABLE
    main_window_module.REMBG_AVAILABLE = False
    try:
        window._sync_ai_controls()
        expected = tr("toolbar.ai.missing.tooltip")
        tooltip = window._right_panel.ai_button.toolTip()
        if tooltip != expected:
            return False, f"Tooltip bei fehlendem KI-Backend weicht ab: {tooltip!r}"

        window._run_ai()
        actual_message = window._sb.currentMessage()
        if actual_message != expected:
            return False, (
                f"KI-Aktion bei fehlendem Backend zeigte unerwarteten Hinweis: "
                f"{actual_message!r}"
            )
    finally:
        main_window_module.REMBG_AVAILABLE = original

    return True, "Fehlendes KI-Backend erzeugt die erwartete Meldung, kein stiller Ausfall."


def _run_eufymake_export_smoke(window: MainWindow, export_dir: Path) -> tuple[bool, str]:
    """Schreibt das Importpaket aus dem aktuell geladenen Projekt (i. d. R. das
    zuvor geöffnete 2.7.0-Projekt) über den echten ``write_export``-Pfad."""
    project = window._canvas.project
    if project is None:
        return False, "Kein Projekt für den EufyMake-Export vorhanden."
    try:
        written = write_export(
            project, str(export_dir),
            optional_roles=[LayerRole.HEIGHT_MAP], bit_depth=16, confirm_warnings=True,
        )
    except Exception as exc:  # noqa: BLE001 - jeder Fehlschlag muss strukturiert zurückkommen
        return False, f"write_export fehlgeschlagen: {exc}"

    missing = [
        name for name in ("color_motif.png", "manifest.json")
        if not (written / name).is_file()
    ]
    if missing:
        return False, f"EufyMake-Export unvollständig ({missing}): {written}"
    return True, f"EufyMake-Export ok: {written}"


def run_acceptance_extra(
    window: MainWindow, output_json: Path, v270_fixture: Path,
) -> AcceptanceExtraResult:
    """Führt beide Zusatz-Smokes aus dem laufenden, gepackten Prozess aus.

    Öffnet zuerst das 2.7.0-Projekt (liefert das Motiv für den nachfolgenden
    Export und das Bild für die Fehlende-Komponente-Prüfung, spart ein
    separates Beispielbild) und führt die beiden folgenden Prüfungen danach
    nur aus, wenn das Öffnen selbst erfolgreich war – sie würden sonst nur
    den bereits gemeldeten Fehler verdoppeln.
    """
    v270_ok, v270_message = _run_v270_project_smoke(window, v270_fixture)
    if v270_ok:
        # Eigener Exportordner je Aufrufer (Dateiname von ``output_json``, z. B.
        # "acceptance_extra_deb"): mehrere Artefaktklassen teilen sich denselben
        # Evidenz-Ordner (scripts/abnahme_smoke.py ruft je Klasse mit demselben
        # ``evidence_dir`` auf) – ein fester Name "eufymake_export" kollidierte
        # sonst mit dem der zuerst gelaufenen Klasse und ließ ``write_export``
        # ohne ``overwrite`` mit ``ExportTargetExistsError`` fehlschlagen (#685-
        # Hardware-Abnahme auf dem finalen Kandidaten, Pi 5: AppImage lief zuerst
        # erfolgreich, .deb schlug danach genau daran fehl).
        eufymake_ok, eufymake_message = _run_eufymake_export_smoke(
            window, output_json.parent / f"{output_json.stem}_eufymake_export",
        )
        missing_component_ok, missing_component_message = _run_missing_component_smoke(window)
    else:
        eufymake_ok, eufymake_message = False, "übersprungen: 2.7.0-Projekt-Smoke fehlgeschlagen"
        missing_component_ok = False
        missing_component_message = "übersprungen: 2.7.0-Projekt-Smoke fehlgeschlagen"

    result = AcceptanceExtraResult(
        ok=eufymake_ok and v270_ok and missing_component_ok,
        eufymake_ok=eufymake_ok, eufymake_message=eufymake_message,
        v270_ok=v270_ok, v270_message=v270_message,
        missing_component_ok=missing_component_ok,
        missing_component_message=missing_component_message,
    )
    payload = {
        "schema": _EVIDENCE_SCHEMA,
        "kind": "abnahme-acceptance-extra",
        "erzeugt_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ok": result.ok,
        "eufymake_export": {"ok": eufymake_ok, "message": eufymake_message},
        "v270_project_open": {"ok": v270_ok, "message": v270_message},
        "missing_component": {"ok": missing_component_ok, "message": missing_component_message},
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    return result
