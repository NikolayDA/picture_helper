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

Fünf Prüfungen, alle ohne externe Testdaten aus dem Paket selbst:

0. **Sichtbare Produktversion** – vergleicht die im Fenstertitel angezeigte
   Version mit dem Sollwert aus dem Artefaktdateinamen (#686). Läuft zuerst
   und unabhängig vom Projektzustand.
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
2b. **Kontrollierte Projekt-Kopie** – speichert das geöffnete Projekt über den
   echten ``_write_project``-Pfad (``save_project``) unter einem eigenen Namen,
   lädt es neu und vergleicht Ebenen, Rollen, Pixel und 16-Bit-Höhenpayload
   wertgleich (#686 – der Schreibpfad, den ``write_export`` nicht abdeckt).
3. **Fehlendes optionales KI-Backend** – erzwingt ``REMBG_AVAILABLE = False``
   im laufenden, gepackten Prozess (unabhängig davon, ob dieses konkrete
   Build tatsächlich mit oder ohne ``--ai`` gepackt wurde) und prüft, dass
   die KI-Aktion die etablierte, übersetzte Meldung zeigt statt eines
   stillen Funktionsausfalls oder Absturzes – dieselbe Prüfung wie
   ``tests/test_main_window.py``, hier zusätzlich aus dem gepackten Artefakt
   heraus (#685-Review).

Aktiviert über ``BGREMOVER_ACCEPTANCE_EXTRA`` (Ziel-JSON-Pfad),
``BGREMOVER_ACCEPTANCE_EXTRA_V270_PROJECT`` (Pfad der ``.bgrproj``-Fixture) und
``BGREMOVER_ACCEPTANCE_EXTRA_VERSION`` (Soll-Version aus dem Artefaktnamen) in
``bgremover.app.main``. Die Evidenz führt zusätzlich ``laufzeit_herkunft`` –
den Pfad, aus dem der geprüfte Code tatsächlich geladen wurde (siehe
:func:`_runtime_provenance`); bewertet wird er nicht, er macht die Frage nur
beantwortbar. Wirft nie – jeder Fehlschlag kommt strukturiert über
:class:`AcceptanceExtraResult` zurück, damit der Aufrufer einen sauberen
Exit-Code setzen kann.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
from PIL import Image

from bgremover import height_ops
from bgremover.eufymake_writer import write_export
from bgremover.height_map import HEIGHT_MAX_16BIT, generate_from_image
from bgremover.i18n import tr
from bgremover.project_model import Layer, LayerKind, LayerRole, Project
from bgremover.project_schema import PROJECT_FORMAT_VERSION

if TYPE_CHECKING:
    from bgremover.main_window import MainWindow

# Schema 3 (#686-Nachtrag): zusätzlich ``laufzeit_herkunft`` – der Nachweis,
# aus welchem Pfad der geprüfte Code tatsächlich stammt.
# Schema 2 (#686): zusätzlich ``visible_version`` und ``project_copy``. Die
# Version ist der Vertrag, an dem ``scripts/abnahme_smoke.py`` erkennt, dass
# ein gepacktes Artefakt die neuen Prüfungen überhaupt kennt – bei jeder
# weiteren Teilprüfung mit hochzählen (dort ACCEPTANCE_EXTRA_SCHEMA).
_EVIDENCE_SCHEMA = 3

# Der Herkunfts-Kindprozess ist reine Diagnose – lieber ohne Ergebnis
# weiterlaufen als das 60s-Budget des Hooks aufbrauchen.
_CHILD_PROVENANCE_TIMEOUT_S = 20

# Vom Fixture-Bau (tests/build_v270_fixture.py, echter v2.7.0-Code)
# protokollierte Werte – identisch zu den Konstanten in
# tests/test_project_v270_upgrade.py, hier dupliziert, weil dieser Hook aus
# dem gepackten Artefakt läuft und nicht auf das tests/-Paket zugreifen kann.
# Versions-Token im Fenstertitel („BgRemover Pro 2.7.1"). Bewusst als
# vollständiger Token verankert – ein Substring-Test hielte "2.7.1" auch in
# "2.7.10" für einen Treffer.
_VERSION_TOKEN_RE = re.compile(r"\b\d+\.\d+\.\d+(?:[.\-+][0-9A-Za-z.\-+]+)?\b")

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
    visible_version_ok: bool
    visible_version_message: str
    project_copy_ok: bool
    project_copy_message: str


def _height_hash(layer: Layer | None) -> str | None:
    if layer is None or layer.height_data is None:
        return None
    return hashlib.sha256(layer.height_data.values.tobytes()).hexdigest()


def _image_hash(layer: Layer) -> str | None:
    """Pixel-Hash der Ebenenansicht (RGBA), für den Round-Trip-Vergleich."""
    if layer.image is None:
        return None
    return hashlib.sha256(np.asarray(layer.image.convert("RGBA")).tobytes()).hexdigest()


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


def _runtime_provenance() -> dict[str, object]:
    """Aus welchem Pfad stammt der Code, der hier gerade läuft?

    Der ganze Zweck dieses Hooks ist der Nachweis am **gepackten Artefakt**
    (#685-Review): ``tests/test_e2e_release_regression.py`` deckt den
    Source-Checkout bereits ab. Läuft hier versehentlich trotzdem der
    Checkout-Code – etwa weil das Arbeitsverzeichnis des Smoke-Aufrufs auf
    ``sys.path`` landet –, prüft der Nachweis genau das, was er ausschließen
    soll, ohne dass es irgendwo auffiele.

    Beobachtet wurde das im Abnahmelauf 30581788054 (Raspberry Pi): Der
    Interpreter kam aus dem entpackten AppImage, ein Kindprozess lud
    ``bgremover/ai_process.py`` aber aus dem Checkout. Diese Funktion bewertet
    **nicht** – sie protokolliert nur, damit die Frage künftig aus der Evidenz
    beantwortbar ist statt aus Vermutungen.
    """
    import bgremover
    from bgremover import ai_process

    return {
        "bgremover_datei": str(getattr(bgremover, "__file__", "unbekannt")),
        # Genau das Modul aus der beobachteten Traceback-Zeile.
        "ai_process_datei": str(getattr(ai_process, "__file__", "unbekannt")),
        "interpreter": sys.executable,
        "eingefroren": bool(getattr(sys, "frozen", False)),
        "arbeitsverzeichnis": os.getcwd(),
        "sys_path_0": sys.path[0] if sys.path else "",
        # Der Kindprozess ist der eigentliche Fundort (siehe unten) – ohne ihn
        # beantwortet dieser Nachweis die Frage nicht, wegen der es ihn gibt.
        "kindprozess": _spawned_provenance(),
    }


def _child_provenance_probe(conn: Any) -> None:
    """Läuft im ``spawn``-Kindprozess und meldet **seine eigene** Herkunft.

    Muss auf Modulebene liegen: ``spawn`` picklet die Zielfunktion über ihren
    qualifizierten Namen und importiert dieses Modul im Kind neu.
    """
    try:
        import sys as child_sys

        import bgremover
        from bgremover import ai_process

        conn.send({
            "bgremover_datei": str(getattr(bgremover, "__file__", "unbekannt")),
            "ai_process_datei": str(getattr(ai_process, "__file__", "unbekannt")),
            "interpreter": child_sys.executable,
            "eingefroren": bool(getattr(child_sys, "frozen", False)),
            "sys_path_0": child_sys.path[0] if child_sys.path else "",
        })
    except BaseException as exc:  # noqa: BLE001 - darf den Hook nie zum Absturz bringen
        conn.send({"fehler": f"{type(exc).__name__}: {exc}"})
    finally:
        conn.close()


def _spawned_provenance() -> dict[str, object]:
    """Herkunft aus einem ``spawn``-Kindprozess – dem eigentlichen Fundort.

    Der Elternprozess allein beantwortet die Frage **nicht**: Beobachtet wurde
    (Lauf 30581788054, Raspberry Pi), dass der Interpreter aus dem entpackten
    AppImage kam, ein `spawn`-Kind aber ``bgremover/ai_process.py`` aus dem
    Source-Checkout lud. ``InferenceProcess`` startet genau so ein Kind; dessen
    Import-Auflösung kann von der des Elternprozesses abweichen, während die
    Evidenz einen gebündelten Pfad zeigt (Codex-Fund auf PR #738).

    Wirft nie und blockiert nicht unbegrenzt: Ein hängendes oder scheiterndes
    Kind wird als ``fehler`` protokolliert, statt den Hook mitzureißen – der
    Nachweis darf die Abnahme nicht zum Absturz bringen.
    """
    import multiprocessing

    try:
        ctx = multiprocessing.get_context("spawn")
        parent_conn, child_conn = ctx.Pipe(duplex=False)
        process = ctx.Process(target=_child_provenance_probe, args=(child_conn,), daemon=True)
        process.start()
        child_conn.close()  # sonst meldet poll() nie EOF, wenn das Kind stirbt
        try:
            if not parent_conn.poll(_CHILD_PROVENANCE_TIMEOUT_S):
                return {"fehler": f"Zeitüberschreitung nach {_CHILD_PROVENANCE_TIMEOUT_S}s"}
            payload = parent_conn.recv()
        finally:
            parent_conn.close()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
        return dict(payload)
    except BaseException as exc:  # noqa: BLE001 - Protokolldaten, nie ein Abbruchgrund
        return {"fehler": f"{type(exc).__name__}: {exc}"}


def _project_state(project: Project) -> dict[str, object]:
    """Vollständiger, **geordneter** Vergleichszustand eines Projekts.

    Die Ebenen liegen bewusst als Liste vor: Ein Dict nach Ebenen-ID hätte eine
    vertauschte Ebenenreihenfolge – also ein sichtbar anderes Komposit – als
    gleich durchgehen lassen. Ebenso vollständig aufgeführt sind alle
    persistierten Felder (Name, Sichtbarkeit, Deckkraft, Sperre) und der
    Projektzustand (Canvasgröße, Schemaversion, Metadaten, aktive Ebene), damit
    der Round-Trip nicht nur Pixel, sondern den ganzen gespeicherten Zustand
    belegt (#686-Review).
    """
    return {
        "canvas": (project.width, project.height),
        "version": project.version,
        "metadata": project.metadata,
        "active_layer_id": project.active_layer_id,
        "layers": [
            {
                "id": layer.id,
                "name": layer.name,
                "kind": layer.kind,
                "role": layer.role,
                "visible": layer.visible,
                "opacity": layer.opacity,
                "locked": layer.locked,
                "height": _height_hash(layer),
                "image": _image_hash(layer),
            }
            for layer in project.layers
        ],
    }


def _first_state_difference(before: dict[str, object], after: dict[str, object]) -> str:
    """Erste abweichende Stelle benennen – eine Meldung ohne Fundort wäre auf
    der Abnahme-Hardware nicht nachverfolgbar."""
    for key in ("canvas", "version", "metadata", "active_layer_id"):
        if before[key] != after[key]:
            return f"{key}: {before[key]!r} → {after[key]!r}"
    old_layers = before["layers"]
    new_layers = after["layers"]
    assert isinstance(old_layers, list) and isinstance(new_layers, list)
    if len(old_layers) != len(new_layers):
        return f"Ebenenanzahl: {len(old_layers)} → {len(new_layers)}"
    for index, (old, new) in enumerate(zip(old_layers, new_layers, strict=True)):
        for field, value in old.items():
            if new[field] != value:
                return f"Ebene {index} ({field}): {value!r} → {new[field]!r}"
    return "unbekannte Abweichung"


def _run_visible_version_smoke(window: MainWindow, expected: str | None) -> tuple[bool, str]:
    """Prüft die im Fenstertitel **sichtbare** Produktversion (#686).

    ``expected`` kommt aus dem Dateinamen des gerade geprüften Artefakts
    (``BgRemover-2.7.1-…`` → ``"2.7.1"``, siehe
    ``scripts/release_abnahme.version_from_artifact_name``) und ist damit ein
    *externer* Sollwert: Ohne ihn verglichen die Prüfung nur das Paket mit sich
    selbst und würde eine falsch paketierte Version nie bemerken. Fehlt der
    Sollwert, bleibt die schwächere Aussage „Titel nennt die Version des
    laufenden Pakets" – das wird in der Meldung ausdrücklich gesagt, statt
    stillschweigend mehr zu behaupten.
    """
    from bgremover import __version__

    title = window.windowTitle()
    # Vollständiger Token, kein Substring: ``"2.7.1" in "BgRemover Pro 2.7.10"``
    # wäre wahr, obwohl der Titel eine *andere* Version zeigt. Genau dieser Fall
    # – Titel aus einer anderen Quelle als ``__version__`` – ist der, den die
    # Prüfung fangen soll.
    shown = _VERSION_TOKEN_RE.search(title)
    if shown is None:
        return False, f"Fenstertitel enthält keine Versionsangabe: {title!r}"
    if shown.group(0) != __version__:
        return False, (
            f"Fenstertitel zeigt Version {shown.group(0)!r}, das Paket meldet "
            f"{__version__!r}: {title!r}"
        )
    if expected is None:
        return True, (
            f"Sichtbare Version {__version__!r} im Fenstertitel (kein externer "
            "Sollwert übergeben – nur Selbstauskunft des Pakets geprüft)."
        )
    if __version__ != expected:
        return False, (
            f"Sichtbare Version {__version__!r} weicht vom Artefaktnamen "
            f"{expected!r} ab – falsch paketierte Version."
        )
    return True, f"Sichtbare Version {__version__!r} stimmt mit dem Artefaktnamen überein."


def _run_project_copy_smoke(window: MainWindow, target: Path) -> tuple[bool, str]:
    """Speichert eine kontrollierte Kopie des offenen Projekts und lädt sie neu.

    Deckt den ``.bgrproj``-**Schreibpfad** des gepackten Artefakts ab (#686):
    ``_run_eufymake_export_smoke`` schreibt über ``write_export`` und sagt
    nichts über ``save_project``. Geprüft wird über den echten UI-Pfad
    ``_write_project`` (ohne Dialog) und anschließendes Neuladen, dass die
    Kopie wertgleich zurückkommt – inklusive der 16-Bit-Höhenpayload, dem
    Teil, den ein 8-Bit-Rückfall still beschädigen würde.

    Die geöffnete v1-Fixture wird beim Speichern kontrolliert auf die aktuelle
    Formatversion gehoben; das ist der dokumentierte Vertrag aus #588 und wird
    hier ausdrücklich mitgeprüft.
    """
    project = window._canvas.project
    if project is None:
        return False, "Kein Projekt für die Speicher-Kopie vorhanden."
    before = _project_state(project)

    target.parent.mkdir(parents=True, exist_ok=True)
    if not window._write_project(str(target)):
        return False, f"Speichern der Kopie fehlgeschlagen: {window._sb.currentMessage()}"
    expected_message = tr("project.saved", name=target.name)
    if window._sb.currentMessage() != expected_message:
        return False, (
            f"Speichern meldete unerwarteten Hinweis: {window._sb.currentMessage()!r}"
        )
    if not target.is_file():
        return False, f"Kopie wurde nicht geschrieben: {target}"

    with zipfile.ZipFile(target) as zf:
        written_version = json.loads(zf.read("manifest.json")).get("version")
    if written_version != PROJECT_FORMAT_VERSION:
        return False, (
            f"Kopie trägt Formatversion {written_version!r}, erwartet "
            f"{PROJECT_FORMAT_VERSION!r}."
        )

    window._load_project_into_canvas(str(target))
    reloaded = window._canvas.project
    if reloaded is None:
        return False, "Kopie ließ sich nicht wieder laden."
    after = _project_state(reloaded)
    if after != before:
        return False, (
            "Kopie weicht nach dem Neuladen vom gespeicherten Projekt ab: "
            f"{_first_state_difference(before, after)}"
        )
    return True, f"Projekt-Kopie bitgenau gespeichert und neu geladen: {target.name}"


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
    expected_version: str | None = None,
) -> AcceptanceExtraResult:
    """Führt die Zusatz-Smokes aus dem laufenden, gepackten Prozess aus.

    Die Versionsprüfung läuft **zuerst und unabhängig**: Sie hängt an keinem
    Projektzustand, und bei einem fehlgeschlagenen Projekt-Öffnen bleibt die
    Aussage über die paketierte Version trotzdem erhalten.

    Danach wird das 2.7.0-Projekt geöffnet (liefert das Motiv für Export und
    Kopie und das Bild für die Fehlende-Komponente-Prüfung, spart ein
    separates Beispielbild); die folgenden Prüfungen laufen nur bei
    erfolgreichem Öffnen – sie würden sonst nur den bereits gemeldeten Fehler
    verdoppeln.
    """
    visible_version_ok, visible_version_message = _run_visible_version_smoke(
        window, expected_version,
    )
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
        # Eigener Dateiname je Aufrufer – wie beim Exportordner teilen sich
        # mehrere Artefaktklassen denselben Evidenz-Ordner (#723).
        project_copy_ok, project_copy_message = _run_project_copy_smoke(
            window, output_json.parent / f"{output_json.stem}_kopie.bgrproj",
        )
        missing_component_ok, missing_component_message = _run_missing_component_smoke(window)
    else:
        skipped = "übersprungen: 2.7.0-Projekt-Smoke fehlgeschlagen"
        eufymake_ok, eufymake_message = False, skipped
        project_copy_ok, project_copy_message = False, skipped
        missing_component_ok, missing_component_message = False, skipped

    result = AcceptanceExtraResult(
        ok=(
            eufymake_ok and v270_ok and missing_component_ok
            and visible_version_ok and project_copy_ok
        ),
        eufymake_ok=eufymake_ok, eufymake_message=eufymake_message,
        v270_ok=v270_ok, v270_message=v270_message,
        missing_component_ok=missing_component_ok,
        missing_component_message=missing_component_message,
        visible_version_ok=visible_version_ok,
        visible_version_message=visible_version_message,
        project_copy_ok=project_copy_ok, project_copy_message=project_copy_message,
    )
    payload = {
        "schema": _EVIDENCE_SCHEMA,
        "kind": "abnahme-acceptance-extra",
        "erzeugt_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ok": result.ok,
        "eufymake_export": {"ok": eufymake_ok, "message": eufymake_message},
        "v270_project_open": {"ok": v270_ok, "message": v270_message},
        "missing_component": {"ok": missing_component_ok, "message": missing_component_message},
        # Reine Protokolldaten, kein Pass/Fail-Kriterium (#686-Nachtrag).
        "laufzeit_herkunft": _runtime_provenance(),
        "visible_version": {"ok": visible_version_ok, "message": visible_version_message},
        "project_copy": {"ok": project_copy_ok, "message": project_copy_message},
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    return result
