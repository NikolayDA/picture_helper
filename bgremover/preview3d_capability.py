"""Laufzeit-Capability-Probe für die 3D-Reliefvorschau (#593, ADR #591).

Ermittelt, ob die Umgebung einen nutzbaren Desktop-OpenGL-Kontext (≥ 2.1)
bietet. Die eigentliche Qt-Probe (``QOpenGLContext`` + ``QOffscreenSurface``)
ist über ``probe_fn`` **injizierbar**, damit die Gating-Logik Qt-frei mit einem
Mock getestet werden kann; die Standard-Probe kapselt den Qt-Zugriff und wirft
**nie** – jeder Fehler wird als strukturierte :class:`RendererCapability`
(``ok=False`` + i18n-Key) zurückgegeben.

Der Repo-Standard-Testpfad (``offscreen`` ohne X) liefert real
``QOpenGLContext.create() == False`` – dort testet die Probe den Fallback-Zweig
unverfälscht echt (ADR-Evidenz Nr. 1). Das Ergebnis wird je Sitzung gecacht;
:func:`reset_capability_cache` verwirft den Cache für die „Erneut versuchen"-
Aktion des UX-Vertrags.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from bgremover.constants import logger

# i18n-Key für den „nicht verfügbar"-Zustand (UX §5, Zustand [U]).
UNAVAILABLE_KEY = "preview3d.unavailable"


@dataclass(frozen=True)
class RendererCapability:
    """Ergebnis der Capability-Probe.

    ``ok`` = nutzbarer Desktop-GL-Kontext vorhanden. ``diagnostic`` trägt
    Vendor/Renderer/Version als Klartext für Logs (nie Bild-/Nutzerdaten);
    ``error_key`` ist der i18n-Key des Fehlerzustands (nur bei ``ok=False``),
    ``detail`` ein technischer Kurzgrund fürs Log.
    """

    ok: bool
    diagnostic: str = ""
    error_key: str | None = None
    detail: str = ""


ProbeFn = Callable[[], RendererCapability]

_cached: RendererCapability | None = None


def _default_probe() -> RendererCapability:
    """Standard-Qt-Probe: erzeugt lazy einen Offscreen-GL-2.1-Kontext.

    Kapselt jeden Qt-/Treiberfehler in eine ``ok=False``-Capability. Ein reiner
    OpenGL-ES-Kontext gilt als „nicht 3D-fähig" (PyQt6 bindet keine ES-
    Funktionssätze, ADR) → Fallback.
    """
    try:
        from PyQt6.QtGui import QOffscreenSurface, QOpenGLContext, QSurfaceFormat
        from PyQt6.QtOpenGL import (
            QOpenGLVersionFunctionsFactory,
            QOpenGLVersionProfile,
        )

        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)
        fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
        ctx = QOpenGLContext()
        ctx.setFormat(fmt)
        if not ctx.create():
            return RendererCapability(
                ok=False, error_key=UNAVAILABLE_KEY,
                detail="QOpenGLContext.create() fehlgeschlagen",
            )
        surface = QOffscreenSurface()
        surface.setFormat(ctx.format())
        surface.create()
        if not surface.isValid() or not ctx.makeCurrent(surface):
            return RendererCapability(
                ok=False, error_key=UNAVAILABLE_KEY,
                detail="Kein aktueller Offscreen-Kontext",
            )
        try:
            if ctx.isOpenGLES():
                return RendererCapability(
                    ok=False, error_key=UNAVAILABLE_KEY,
                    detail="Nur OpenGL-ES-Kontext verfügbar",
                )
            profile = QOpenGLVersionProfile()
            profile.setVersion(2, 1)
            fns = QOpenGLVersionFunctionsFactory.get(profile, ctx)
            if fns is None:
                return RendererCapability(
                    ok=False, error_key=UNAVAILABLE_KEY,
                    detail="Keine GL-2.1-Versionsfunktionen verfügbar",
                )
            vendor = _gl_string(fns, _GL_VENDOR)
            renderer = _gl_string(fns, _GL_RENDERER)
            version = _gl_string(fns, _GL_VERSION)
            diagnostic = f"{vendor} / {renderer} / {version}".strip(" /")
            return RendererCapability(ok=True, diagnostic=diagnostic)
        finally:
            ctx.doneCurrent()
    except Exception as exc:  # noqa: BLE001 – Probe darf nie propagieren
        return RendererCapability(
            ok=False, error_key=UNAVAILABLE_KEY, detail=f"{type(exc).__name__}: {exc}"
        )


# Rohe glGetString-Namen (Teil des OpenGL-Vertrags, nicht der PyQt6-Bindings).
_GL_VENDOR = 0x1F00
_GL_RENDERER = 0x1F01
_GL_VERSION = 0x1F02


def _gl_string(fns: object, name: int) -> str:
    """Liest einen ``glGetString``-Wert defensiv als Text (leer bei Fehler)."""
    try:
        value = fns.glGetString(name)  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        return ""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("ascii", "replace")
    return str(value)


def probe_3d_capability(
    *, probe_fn: ProbeFn | None = None, use_cache: bool = True
) -> RendererCapability:
    """Prüft (gecacht) die 3D-Fähigkeit der Umgebung.

    Das Ergebnis wird je Sitzung gecacht (``use_cache``); ``probe_fn`` ersetzt
    die Qt-Probe für Tests. Erfolge/Fehler werden einmal geloggt (Backend,
    Capability, Fehlerklasse – ohne Bild-/Nutzerdaten).
    """
    global _cached
    if use_cache and _cached is not None:
        return _cached
    probe = probe_fn or _default_probe
    try:
        result = probe()
    except Exception as exc:  # noqa: BLE001 – auch ein defekter Mock darf nicht durchschlagen
        result = RendererCapability(
            ok=False, error_key=UNAVAILABLE_KEY,
            detail=f"{type(exc).__name__}: {exc}",
        )
    if result.ok:
        logger.info("3D-Capability: verfügbar (%s)", result.diagnostic or "unbekannt")
    else:
        logger.info("3D-Capability: nicht verfügbar (%s)", result.detail or "unbekannt")
    if use_cache:
        _cached = result
    return result


def cached_3d_capability() -> RendererCapability | None:
    """Liefert das Sitzungs-Ergebnis, ohne eine GL-Probe auszulösen.

    Der Hauptfenster-Aufbau nutzt ausschließlich diesen read-only Zugriff, damit
    der verbindliche ADR-Vertrag „erst beim ersten 3D-Wunsch" gewahrt bleibt.
    """
    return _cached


def reset_capability_cache() -> None:
    """Verwirft den Sitzungs-Cache – für die „Erneut versuchen"-Aktion (UX §5)."""
    global _cached
    _cached = None
