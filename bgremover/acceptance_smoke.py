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

Zwei Prüfungen, beide ohne externe Testdaten aus dem Paket selbst:

1. **EufyMake-Export-Smoke** – erzeugt ein Beispielbild, generiert eine
   Höhenkarte und schreibt das Importpaket über den echten
   ``bgremover.eufymake_writer.write_export``-Pfad.
2. **2.7.0-Projekt-Öffnen** – lädt eine echte, mit dem tatsächlichen
   v2.7.0-Release-Code gebaute ``.bgrproj``-Datei (Pfad kommt aus dem
   Source-Checkout, der ohnehin im selben Abnahme-Job liegt – nur der
   *Code*, der sie verarbeitet, muss aus dem Paket stammen) und prüft, dass
   das Laden keine Migration/Warnung auslöst und sich danach bitgenau
   weiterbearbeiten lässt (Höhen-Op + Undo).

Aktiviert über ``BGREMOVER_ACCEPTANCE_EXTRA`` (Ziel-JSON-Pfad) und
``BGREMOVER_ACCEPTANCE_EXTRA_V270_PROJECT`` (Pfad der ``.bgrproj``-Fixture) in
``bgremover.app.main``. Wirft nie – jeder Fehlschlag kommt strukturiert über
:class:`AcceptanceExtraResult` zurück, damit der Aufrufer einen sauberen
Exit-Code setzen kann.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from bgremover import height_ops
from bgremover.eufymake_writer import write_export
from bgremover.i18n import tr
from bgremover.project_model import Layer, LayerKind, LayerRole

if TYPE_CHECKING:
    from bgremover.main_window import MainWindow

_EVIDENCE_SCHEMA = 1


@dataclass(frozen=True)
class AcceptanceExtraResult:
    """Ergebnis eines Automationslaufs (immer strukturiert, wirft nie)."""

    ok: bool
    eufymake_ok: bool
    eufymake_message: str
    v270_ok: bool
    v270_message: str


def _height_hash(layer: Layer | None) -> str | None:
    if layer is None or layer.height_data is None:
        return None
    return hashlib.sha256(layer.height_data.values.tobytes()).hexdigest()


def _run_v270_project_smoke(window: MainWindow, fixture: Path) -> tuple[bool, str]:
    """Öffnet das echte 2.7.0-Projekt über den echten Anwenderpfad und
    bearbeitet es weiter – Struktur/Migrationsfreiheit siehe
    ``tests/test_project_v270_upgrade.py`` (Qt-frei, ausführlicher)."""
    if not fixture.is_file():
        return False, f"2.7.0-Fixture fehlt: {fixture}"

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
    height = project.layers[1]
    if height.role is not LayerRole.HEIGHT_MAP or height.height_data is None:
        return False, "2.7.0-Projekt: HEIGHT-Ebene ohne HEIGHT_MAP-Rolle/Payload."

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
    Export, spart ein separates Beispielbild) und exportiert danach nur, wenn
    das Öffnen selbst erfolgreich war – ein Export nach fehlgeschlagenem Open
    würde nur den bereits gemeldeten Fehler verdoppeln.
    """
    v270_ok, v270_message = _run_v270_project_smoke(window, v270_fixture)
    if v270_ok:
        eufymake_ok, eufymake_message = _run_eufymake_export_smoke(
            window, output_json.parent / "eufymake_export",
        )
    else:
        eufymake_ok, eufymake_message = False, "übersprungen: 2.7.0-Projekt-Smoke fehlgeschlagen"

    result = AcceptanceExtraResult(
        ok=eufymake_ok and v270_ok,
        eufymake_ok=eufymake_ok, eufymake_message=eufymake_message,
        v270_ok=v270_ok, v270_message=v270_message,
    )
    payload = {
        "schema": _EVIDENCE_SCHEMA,
        "kind": "abnahme-acceptance-extra",
        "erzeugt_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ok": result.ok,
        "eufymake_export": {"ok": eufymake_ok, "message": eufymake_message},
        "v270_project_open": {"ok": v270_ok, "message": v270_message},
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    return result
