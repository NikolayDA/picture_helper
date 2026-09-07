"""Laufzeit-Capability-Probe für die 3D-Reliefvorschau (#593, ADR #591).

Ermittelt, ob die Umgebung Desktop-OpenGL (≥ 2.1) nicht nur bereitstellt,
sondern damit auch **rendern** kann. Die eigentliche Qt-Probe (``QOpenGLContext`` + ``QOffscreenSurface``)
ist über ``probe_fn`` **injizierbar**, damit die Gating-Logik Qt-frei mit einem
Mock getestet werden kann; die Standard-Probe kapselt den Qt-Zugriff und wirft
**nie** – jeder Fehler wird als strukturierte :class:`RendererCapability`
(``ok=False`` + i18n-Key) zurückgegeben.

Gemessen wird **Renderfähigkeit**, nicht bloß Kontextexistenz (#1002) – in
zwei Regeln, die verschiedene Ausfälle fangen:

1. **Plattformregel** (:data:`NON_RENDERABLE_PLATFORMS`, zuerst geprüft, ohne
   jeden GL-Aufruf). ``QOpenGLWidget`` braucht eine Plattformintegration mit
   ``RhiBasedRendering``; fehlt sie, warnt Qt im Widget-Konstruktor
   („QOpenGLWidget is not supported on this platform."), ``initialize()``
   gelingt trotzdem, und erst ``render()`` meldet
   ``QOpenGLWidget: No fbo, cannot render``. **Das ist der Ausfall aus #1002**
   – reproduziert mit ``xvfb-run`` + ``QT_QPA_PLATFORM=offscreen``: Kontext,
   Funktionssatz und Framebuffer-Objekt gelingen alle, der Viewer rendert
   trotzdem nie (``defaultFramebufferObject() == 0``).
2. **Render-Nachweis** (:func:`_render_probe`, nach dem GL-2.1-Funktionssatz):
   ein kleines ``QOpenGLFramebufferObject`` derselben Bauart, die
   ``QOpenGLWidget`` für seinen Widget-Framebuffer anlegt. Er fängt eine
   **andere** Klasse – Treiber, die auf einer Sitzungsplattform kein
   vollständiges Render-Ziel liefern – und ausdrücklich **nicht** den Fall
   oben.

Beide Regeln sind fail-open gebaut: Sie können 3D auf tauglicher Hardware
nicht abschalten. Zusammen bleiben sie **notwendig, nicht hinreichend** –
bleibt der Widget-Framebuffer aus Gründen des Widget-Lebenszyklus aus, sieht
ihn keine Probe.

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

#: Qt-Platform-Plugins, unter denen ``QOpenGLWidget`` grundsätzlich keinen
#: Frame erzeugt – **die** geteilte Quelle dieser Regel (#1002). Die
#: Plattformintegration dieser Plugins meldet kein ``RhiBasedRendering``; Qt
#: warnt im Widget-Konstruktor („QOpenGLWidget is not supported on this
#: platform.") und ``render()`` bricht später mit „No fbo, cannot render" ab.
#: Die zugrunde liegende Fähigkeit ist in PyQt6 nicht abfragbar, der
#: Plugin-Name ist der verfügbare, deterministische Stellvertreter.
#:
#: Bewusst eine **Blockliste**, keine Whitelist: Ein unbekanntes oder neues
#: Plugin bleibt erlaubt. Die Fehlerrichtung ist damit dieselbe wie beim
#: Render-Nachweis – 3D auf tauglicher Hardware wird nie abgeschaltet; im
#: Zweifel landet der Viewer im dokumentierten Fehlerzustand [F] statt
#: grundlos im Zustand [U]. Ergänzt wird nur mit beobachteter Qt-Meldung.
#:
#: ``scripts/gl_stress_probe.py`` und ``tests/test_viewer_3d_gl.py`` führten
#: dieselbe Menge je als eigene Kopie; beide beziehen sie jetzt von hier.
NON_RENDERABLE_PLATFORMS: frozenset[str] = frozenset({"offscreen", "minimal", "vnc"})


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

    Prüfreihenfolge: Plattformregel (ohne GL-Aufruf), Kontext, Oberfläche +
    ``makeCurrent()``, ES-Abweisung, GL-2.1-Funktionssatz, Provenienz,
    Render-Nachweis. Kapselt jeden Qt-/Treiberfehler in eine
    ``ok=False``-Capability. Ein reiner OpenGL-ES-Kontext gilt als „nicht
    3D-fähig" (PyQt6 bindet keine ES-Funktionssätze, ADR) → Fallback.
    """
    try:
        from PyQt6.QtGui import QOffscreenSurface, QOpenGLContext, QSurfaceFormat
        from PyQt6.QtOpenGL import (
            QOpenGLVersionFunctionsFactory,
            QOpenGLVersionProfile,
        )

        platform_error = _platform_render_support()
        if platform_error is not None:
            return RendererCapability(
                ok=False, error_key=UNAVAILABLE_KEY, detail=platform_error,
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

# Rohe glClear-Masken und -Fehlercodes (ebenfalls OpenGL-Vertrag). ``viewer_3d``
# teilt davon Farbe und Tiefe; das Stencil-Bit kommt aus
# ``QOpenGLWidgetPrivate::recreateFbos``, das der Nachweis unten nachstellt –
# ``paintGL`` leert selbst nur mit ``COLOR | DEPTH``.
_GL_NO_ERROR = 0x0000
_GL_DEPTH_BUFFER_BIT = 0x00000100
_GL_STENCIL_BUFFER_BIT = 0x00000400
_GL_COLOR_BUFFER_BIT = 0x00004000

#: Obergrenze für das Leeren der GL-Fehlerwarteschlange vor dem Nachweis.
#: ``glGetError`` liefert je Aufruf **einen** Fehler und löscht ihn; ein Treiber,
#: der endlos Fehler meldet, darf die Probe nicht aufhängen.
_GL_ERROR_DRAIN_LIMIT = 32

#: Maße des Nachweis-Framebuffers – **die** Mindestgröße des Viewers
#: (``GLReliefViewer.setMinimumSize``), damit die Probe nicht kleiner misst als
#: das, was ``QOpenGLWidget`` später wirklich anfordert. Ein 4 × 4-Ziel gelang
#: auf einer speicherarmen GPU auch dann noch, wenn die echte Widget-Fläche
#: schon an einer Treibergrenze scheiterte (Codex-Review PR #1003). Qt
#: multipliziert zusätzlich mit dem Device-Pixel-Ratio – die Probe bleibt
#: dadurch **schwächer** als der Viewer, also weiterhin ohne Falsch-Negativ.
MIN_VIEWER_SIZE_PX: tuple[int, int] = (240, 200)


def _platform_render_support() -> str | None:
    """Trägt das aktive Qt-Platform-Plugin überhaupt eine GL-Widget-Fläche?

    Die eigentliche Bedingung ist ``QPlatformIntegration::RhiBasedRendering``;
    PyQt6 bindet sie nicht, der Plugin-Name ist der Stellvertreter (siehe
    :data:`NON_RENDERABLE_PLATFORMS`). Liefert ``None``, wenn nichts dagegen
    spricht.

    **Ohne laufende ``QGuiApplication`` gibt es keine Aussage.** Gemessen:
    ``QGuiApplication.platformName()`` liefert dann einen Vorgabewert (hier
    ``'xcb'``) und ignoriert ``QT_QPA_PLATFORM`` – die Regel prüfte also eine
    Plattform, die gar nicht läuft. Der ganze Probelauf setzt die Anwendung
    ohnehin voraus (``ctx.create()`` endet sonst mit SIGSEGV, reproduziert);
    statt in diesen Absturz zu laufen, ist das hier ein benannter Befund. Im
    Anwendungsprozess existiert die Instanz immer, die Skripte in ``scripts/``
    legen sie vorher an.
    """
    from PyQt6.QtGui import QGuiApplication

    if QGuiApplication.instance() is None:
        return "Keine laufende QGuiApplication – Plattform nicht bestimmbar"
    name = str(QGuiApplication.platformName() or "")
    if name in NON_RENDERABLE_PLATFORMS:
        return f"Qt-Plattform {name!r} trägt keine OpenGL-Widget-Fläche"
    return None


def _drain_gl_errors(fns: object) -> None:
    """Leert die GL-Fehlerwarteschlange (hart begrenzt, wirft nie)."""
    for _ in range(_GL_ERROR_DRAIN_LIMIT):
        if int(fns.glGetError()) == _GL_NO_ERROR:  # type: ignore[attr-defined]
            return


def _render_probe(fns: object) -> str | None:
    """Minimaler Render-Nachweis im aktuellen Kontext (#1002).

    ``QOpenGLWidgetPrivate::recreateFbos`` legt den Widget-Framebuffer als
    ``QOpenGLFramebufferObject`` mit ``CombinedDepthStencil`` an, bindet ihn und
    leert ihn per ``glClear`` – genau diese Folge wird hier in der
    Viewer-Mindestgröße (:data:`MIN_VIEWER_SIZE_PX`) nachgestellt. Die Prüfung
    bleibt damit **nie strenger** als der Viewer: Ein Kontext, der sie besteht,
    hätte auch dessen Framebuffer bekommen (Qt skaliert die echte Fläche
    zusätzlich mit dem Device-Pixel-Ratio); ein Falsch-Negativ (3D grundlos
    abgeschaltet) ist ausgeschlossen.

    ``glClear`` **wirft nicht**, sondern legt einen Fehlercode in die
    GL-Warteschlange (etwa ``GL_INVALID_FRAMEBUFFER_OPERATION`` nach einem
    Kontextverlust). Ohne die ``glGetError``-Abfrage hätte der Nachweis genau
    dort Erfolg gemeldet, wo kein Frame entsteht – der Zustand, den er
    verhindern soll (Codex-Review PR #1003). Vorher wird die Warteschlange
    geleert, damit ein fremder Altfehler nicht dem eigenen Aufruf angelastet
    wird.

    Liefert ``None`` bei Erfolg, sonst den technischen Kurzgrund. Wirft nie –
    ein Treiber, der hier abstürzt, ist ein Befund, kein Absturz der App.
    Das gilt für die **ganze** Funktion: Auch die lokalen Qt-Importe und die
    Kontextabfrage liegen im ``try``. Sonst landete ein ``ImportError`` im
    äußeren Handler von :func:`_default_probe` und nähme die dort bereits
    gemessene Provenienz mit (Review PR #1003).

    **Setzt einen aktuellen Kontext voraus.** Qt dereferenziert in
    ``QOpenGLFramebufferObjectPrivate::init`` den ``currentContext()``
    ungeprüft: Ohne Kontext endet der Prozess mit SIGSEGV, und das fängt kein
    ``except``. Der Aufrufer hat ihn hier immer (``makeCurrent()`` ist geprüft);
    die Schranke unten ist die fail-closed Absicherung gegen einen künftigen
    zweiten Aufrufer.
    """
    fbo = None
    try:
        from PyQt6.QtGui import QOpenGLContext
        from PyQt6.QtOpenGL import QOpenGLFramebufferObject

        if QOpenGLContext.currentContext() is None:
            return "Render-Nachweis ohne aktuellen Kontext angefordert"

        width, height = MIN_VIEWER_SIZE_PX
        fbo = QOpenGLFramebufferObject(
            width, height,
            QOpenGLFramebufferObject.Attachment.CombinedDepthStencil,
        )
        if not fbo.isValid():
            return "Kontext ohne vollständiges Framebuffer-Objekt"
        if not fbo.bind():
            return "Framebuffer-Objekt nicht bindbar"
        try:
            _drain_gl_errors(fns)
            fns.glClear(  # type: ignore[attr-defined]
                _GL_COLOR_BUFFER_BIT | _GL_DEPTH_BUFFER_BIT | _GL_STENCIL_BUFFER_BIT
            )
            error = int(fns.glGetError())  # type: ignore[attr-defined]
        finally:
            fbo.release()
        if error != _GL_NO_ERROR:
            return f"glClear meldete GL-Fehler 0x{error:04X}"
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
        # Die Provenienz mitloggen, sonst stünde für ein Gerät, das erst am
        # Render-Nachweis scheitert, nur „Kontext ohne vollständiges
        # Framebuffer-Objekt" im Log – ohne die Angabe, welche GPU das war
        # (Codex-Review PR #1003).
        logger.info(
            "3D-Capability: nicht verfügbar (%s%s)",
            result.detail or "unbekannt",
            f"; {result.diagnostic}" if result.diagnostic else "",
        )
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
