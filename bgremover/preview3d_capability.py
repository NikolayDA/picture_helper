"""Laufzeit-Capability-Probe für die 3D-Reliefvorschau (#593, ADR #591).

Ermittelt, ob die Umgebung Desktop-OpenGL (≥ 2.1) nicht nur bereitstellt,
sondern damit auch **rendern** kann. Die eigentliche Qt-Probe (``QOpenGLContext`` + ``QOffscreenSurface``)
ist über ``probe_fn`` **injizierbar**, damit die Gating-Logik Qt-frei mit einem
Mock getestet werden kann; die Standard-Probe kapselt den Qt-Zugriff und wirft
**nie** – jeder Fehler wird als strukturierte :class:`RendererCapability`
(``ok=False`` + i18n-Key) zurückgegeben.

Gemessen wird **Renderfähigkeit**, nicht bloß Kontextexistenz (#1002): Nach
Kontext, Oberfläche und GL-2.1-Funktionssatz folgt ein minimaler Render-Nachweis
in ein ``QOpenGLFramebufferObject``. ``QOpenGLWidget`` legt seinen
Widget-Framebuffer genau so an (``CombinedDepthStencil``, anschließend
``glClear``); ein Kontext ohne nutzbares Framebuffer-Objekt meldete sonst
„verfügbar", während der Viewer keinen Frame erzeugt und Qt nur
``QOpenGLWidget: No fbo, cannot render`` protokolliert. Der Nachweis ist eine
**notwendige**, keine hinreichende Bedingung: Bleibt der Widget-Framebuffer aus
Gründen des Widget-Lebenszyklus aus, sieht ihn keine Probe.

Ob ``offscreen`` einen GL-Kontext liefert, ist eine Eigenschaft des Rechners,
keine der Plattform: Die GitHub-Runner liefern real
``QOpenGLContext.create() == False`` (ADR-Evidenz Nr. 1), ein Raspberry Pi mit
Broadcom V3D + Mesa dagegen einen Kontext. Das Ergebnis wird je Sitzung gecacht;
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

    ``ok`` = renderfähiger Desktop-GL-Kontext vorhanden. ``diagnostic`` trägt
    Vendor/Renderer/Version als Klartext für Logs (nie Bild-/Nutzerdaten) und
    steht seit #1002 auch bei ``ok=False``, sobald die Probe so weit kam – ein
    Gerät, das erst am Render-Nachweis scheitert, ist ohne diese Angabe nicht
    einzuordnen. ``error_key`` ist der i18n-Key des Fehlerzustands (nur bei
    ``ok=False``), ``detail`` ein technischer Kurzgrund fürs Log.
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
    Funktionssätze, ADR) → Fallback. Zuletzt läuft der Render-Nachweis
    (:func:`_render_probe`) – ohne ihn meldete die Probe „verfügbar" für einen
    Kontext, in den der Viewer nicht zeichnen kann (#1002).
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
            render_error = _render_probe(fns)
            if render_error is not None:
                return RendererCapability(
                    ok=False, error_key=UNAVAILABLE_KEY, diagnostic=diagnostic,
                    detail=render_error,
                )
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

# Rohe glClear-Masken (ebenfalls OpenGL-Vertrag; identisch zu ``viewer_3d``).
_GL_DEPTH_BUFFER_BIT = 0x00000100
_GL_STENCIL_BUFFER_BIT = 0x00000400
_GL_COLOR_BUFFER_BIT = 0x00004000

#: Kantenlänge des Nachweis-Framebuffers. Vier Pixel genügen: geprüft wird, ob
#: der Kontext ein vollständiges Render-Ziel liefert, nicht dessen Inhalt.
_RENDER_PROBE_PX = 4


def _render_probe(fns: object) -> str | None:
    """Minimaler Render-Nachweis im aktuellen Kontext (#1002).

    ``QOpenGLWidgetPrivate::recreateFbos`` legt den Widget-Framebuffer als
    ``QOpenGLFramebufferObject`` mit ``CombinedDepthStencil`` an, bindet ihn und
    leert ihn per ``glClear`` – genau diese Folge wird hier in 4 × 4 Pixeln
    nachgestellt. Die Prüfung kann damit **nie strenger** sein als der Viewer:
    Ein Kontext, der sie besteht, hätte auch dessen Framebuffer bekommen; ein
    Falsch-Negativ (3D grundlos abgeschaltet) ist ausgeschlossen.

    Liefert ``None`` bei Erfolg, sonst den technischen Kurzgrund. Wirft nie –
    ein Treiber, der hier abstürzt, ist ein Befund, kein Absturz der App.

    **Setzt einen aktuellen Kontext voraus.** Qt dereferenziert in
    ``QOpenGLFramebufferObjectPrivate::init`` den ``currentContext()``
    ungeprüft: Ohne Kontext endet der Prozess mit SIGSEGV, und das fängt kein
    ``except``. Der Aufrufer hat ihn hier immer (``makeCurrent()`` ist geprüft);
    die Schranke unten ist die fail-closed Absicherung gegen einen künftigen
    zweiten Aufrufer.
    """
    from PyQt6.QtGui import QOpenGLContext
    from PyQt6.QtOpenGL import QOpenGLFramebufferObject

    if QOpenGLContext.currentContext() is None:
        return "Render-Nachweis ohne aktuellen Kontext angefordert"

    fbo = None
    try:
        fbo = QOpenGLFramebufferObject(
            _RENDER_PROBE_PX, _RENDER_PROBE_PX,
            QOpenGLFramebufferObject.Attachment.CombinedDepthStencil,
        )
        if not fbo.isValid():
            return "Kontext ohne vollständiges Framebuffer-Objekt"
        if not fbo.bind():
            return "Framebuffer-Objekt nicht bindbar"
        try:
            fns.glClear(  # type: ignore[attr-defined]
                _GL_COLOR_BUFFER_BIT | _GL_DEPTH_BUFFER_BIT | _GL_STENCIL_BUFFER_BIT
            )
        finally:
            fbo.release()
    except Exception as exc:  # noqa: BLE001 – Treiberfehler ist ein Befund
        return f"Render-Nachweis fehlgeschlagen: {type(exc).__name__}: {exc}"
    finally:
        # Freigabe noch im aktuellen Kontext: Der Aufrufer ruft gleich
        # ``doneCurrent()``; ein danach eingesammeltes FBO verlöre seine
        # GL-Objekte nicht sauber.
        del fbo
    return None


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
