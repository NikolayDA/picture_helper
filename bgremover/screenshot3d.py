"""Nativer 3D-Screenshot-Automationshook des gepackten Artefakts (#648).

Erzeugt ohne manuelle Interaktion einen Screenshot der 3D-Reliefvorschau aus
dem **laufenden Prozess** heraus: synthetisches Beispielbild laden →
Höhenkarte erzeugen → 3D-Ansicht aktivieren → auf den ``ready``-Zustand warten
→ Fenster-Grab (GL-Viewer **und** 3D-Inspector-Bedienelemente, für die
Vision-Kriterien aus #646) → PNG + Provenance-JSON schreiben.

Der Hook wird über die Umgebungsvariable ``BGREMOVER_SCREENSHOT_3D`` (Pfad der
Ziel-PNG) in ``bgremover.app.main`` aktiviert – analog zu den bestehenden
Automationshooks ``BGREMOVER_SMOKE_TEST``/``BGREMOVER_AI_SELFCHECK``. Bewusst
**kein** CLI-Flag: das gepackte Artefakt startet plattformabhängig über einen
python-appimage-Entrypoint bzw. ein ``.app``-Bundle, deren Argument-Handling
schon für Bilddateien reserviert ist (``_startup_image_paths``); ein
Umgebungshook bleibt unabhängig davon eindeutig.

Läuft bewusst **nicht** offscreen: die GL-Provenance des Nachweises muss aus
diesem laufenden, gepackten Prozess stammen (Abgrenzung zu #642/#643, deren
Start-Wächter ``QT_QPA_PLATFORM=offscreen`` erzwingt, und zu #644, dessen
nativer E2E-Nachweis aus dem Source-Checkout stammt statt aus dem Paket).
Ein Software-Renderer (llvmpipe & Co., geteilte Regel aus
``renderer_provenance``) lässt den Nachweis fehlschlagen statt ihn stillschweigend
als Hardware-Nachweis zu akzeptieren.
"""
from __future__ import annotations

import json
import platform
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, cast

from PyQt6.QtCore import QDeadlineTimer, QEventLoop, QTimer
from PyQt6.QtGui import QGuiApplication

from bgremover.renderer_provenance import is_software_renderer

if TYPE_CHECKING:
    from bgremover.main_window import MainWindow

# Synthetisches Beispielbild: kein externes Asset nötig (portabel über alle
# Paketformate hinweg), reicht als HEIGHT-Quelle mit sichtbarem Relief.
_SAMPLE_SIZE = 512
_PROVENANCE_SCHEMA = 1


@dataclass(frozen=True)
class Screenshot3DResult:
    """Ergebnis eines Automationslaufs (immer strukturiert, wirft nie)."""

    ok: bool
    state: str
    diagnostic: str
    message: str


def _pump_until(predicate, timeout_ms: int) -> bool:  # type: ignore[no-untyped-def]
    """Pumpt die Qt-Event-Loop, bis *predicate* wahr wird oder das Timeout greift."""
    if predicate():
        return True
    loop = QEventLoop()
    deadline = QDeadlineTimer(timeout_ms)
    timer = QTimer()
    timer.setInterval(50)

    def _check() -> None:
        if predicate() or deadline.hasExpired():
            loop.quit()

    timer.timeout.connect(_check)
    timer.start()
    loop.exec()
    timer.stop()
    return predicate()


def _sample_image():  # type: ignore[no-untyped-def]
    """Deterministisches radiales Verlaufsbild – keine externen Assets."""
    import numpy as np
    from PIL import Image

    size = _SAMPLE_SIZE
    yy, xx = np.mgrid[0:size, 0:size]
    dist = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2)
    ramp = np.clip(255 - dist * (255.0 / (size / 2)), 0, 255).astype(np.uint8)
    alpha = np.full((size, size), 255, dtype=np.uint8)
    rgba = np.dstack([ramp, ramp, ramp, alpha])
    return Image.fromarray(rgba, mode="RGBA")


def run_native_3d_screenshot(
    window: MainWindow, output_path: Path, *, timeout_ms: int = 25_000,
) -> Screenshot3DResult:
    """Führt den Automationsablauf aus; schreibt PNG + Provenance-JSON bei Erfolg.

    Wirft nie – jeder Fehlschlag (nicht bereiter 3D-Zweig, Viewer-Fehler,
    Software-Renderer) kommt strukturiert über :class:`Screenshot3DResult`
    zurück, damit der Aufrufer (``bgremover.app.main``) einen sauberen
    Exit-Code setzen kann.
    """
    window._canvas.apply_loaded_image(_sample_image(), "screenshot3d://sample")
    window._canvas.fit_to_view()
    window._canvas.generate_height_map()

    window._set_preview3d_mode(True)
    reached = _pump_until(
        lambda: window._relief3d_view.state in {"ready", "unavailable", "error"},
        timeout_ms,
    )
    state = window._relief3d_view.state
    if not reached or state != "ready":
        return Screenshot3DResult(False, state, "", f"3D-Vorschau nicht bereit: {state}")

    viewer = window._relief3d_view.viewer()
    if viewer is None:
        return Screenshot3DResult(False, state, "", "Ready-Zustand ohne GL-Viewer.")

    frame_ready = _pump_until(
        lambda: viewer.has_failed or (
            viewer.isValid()
            and viewer._gl_ready
            and viewer._mesh is not None
            and viewer._pending_mesh is None
        ),
        timeout_ms,
    )
    state = window._relief3d_view.state
    if not frame_ready or viewer.has_failed or state != "ready":
        return Screenshot3DResult(False, state, "", "Nativer GL-Frame fehlgeschlagen.")
    if viewer._index_count <= 0:
        return Screenshot3DResult(False, state, "", "GL-Viewer hat keine Geometrie hochgeladen.")

    diagnostic = window._preview3d._capability_probe().diagnostic
    if not diagnostic.strip():
        return Screenshot3DResult(False, state, "", "Keine GL-Provenance verfügbar.")
    if is_software_renderer(diagnostic):
        return Screenshot3DResult(
            False, state, diagnostic, f"Software-Renderer abgewiesen: {diagnostic}",
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Ganzes Fenster grabben, nicht nur den GL-Viewer: die Vision-Vorbewertung
    # (#646, ``criteria_for``) bewertet ``*preview3d*ready*`` u. a. gegen
    # ``controls_sichtbar`` (3D-Inspector-Bedienelemente) – ein reiner
    # Viewport-Screenshot könnte dieses Kriterium nie erfüllen (Codex-Fund,
    # PR #652).
    if not window.grab().save(str(output_path)):
        return Screenshot3DResult(False, state, diagnostic, f"Screenshot nicht speicherbar: {output_path}")

    _write_provenance(output_path, diagnostic)
    return Screenshot3DResult(True, state, diagnostic, f"Nativer 3D-Screenshot erzeugt: {output_path}")


def _write_provenance(output_path: Path, diagnostic: str) -> None:
    """Provenance-Sidecar-JSON neben dem Screenshot ablegen (Abnahme-Auswertung)."""
    instance = QGuiApplication.instance()
    app = cast(QGuiApplication, instance) if instance is not None else None
    payload = {
        "schema": _PROVENANCE_SCHEMA,
        "kind": "abnahme-native-3d-screenshot",
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "qt_platform": app.platformName() if app is not None else "unbekannt",
        "host": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "gl_provenance": diagnostic,
    }
    sidecar = output_path.with_name(output_path.name + ".json")
    sidecar.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
