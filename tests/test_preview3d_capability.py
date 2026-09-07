"""Tests der 3D-Capability-Probe (#593, Epic #582).

Die Gating-Logik ist über ``probe_fn`` Qt-frei mit Mocks testbar; ein Test
prüft zusätzlich den Vertrag der echten Probe (sie wirft nie und ist in sich
konsistent). Der Fallback-Zweig selbst haengt an der GL-Weiche: „offscreen"
heisst nicht „kein GL-Kontext" (Raspberry Pi mit Broadcom V3D).
"""
from __future__ import annotations

import builtins

import pytest

from bgremover import preview3d_capability as capability
from bgremover.preview3d_capability import (
    NON_RENDERABLE_PLATFORMS,
    UNAVAILABLE_KEY,
    RendererCapability,
    _default_probe,
    _gl_string,
    _platform_render_support,
    _render_probe,
    probe_3d_capability,
    reset_capability_cache,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_capability_cache()
    yield
    reset_capability_cache()


def test_ok_probe_returns_capable() -> None:
    cap = probe_3d_capability(
        probe_fn=lambda: RendererCapability(ok=True, diagnostic="Mesa / llvmpipe"),
        use_cache=False,
    )
    assert cap.ok and cap.diagnostic == "Mesa / llvmpipe"


def test_failing_probe_returns_unavailable_key() -> None:
    cap = probe_3d_capability(
        probe_fn=lambda: RendererCapability(
            ok=False, error_key=UNAVAILABLE_KEY, detail="kein Kontext"),
        use_cache=False,
    )
    assert not cap.ok and cap.error_key == UNAVAILABLE_KEY


def test_raising_probe_never_propagates() -> None:
    def boom() -> RendererCapability:
        raise RuntimeError("Treiber explodiert")

    cap = probe_3d_capability(probe_fn=boom, use_cache=False)
    assert not cap.ok and cap.error_key == UNAVAILABLE_KEY


def test_result_is_cached_until_reset() -> None:
    calls = {"n": 0}

    def counting() -> RendererCapability:
        calls["n"] += 1
        return RendererCapability(ok=True)

    probe_3d_capability(probe_fn=counting)
    probe_3d_capability(probe_fn=counting)
    assert calls["n"] == 1  # zweiter Aufruf trifft den Cache
    reset_capability_cache()
    probe_3d_capability(probe_fn=counting)
    assert calls["n"] == 2


def test_default_probe_keeps_its_contract(qapp) -> None:
    """Die echte Qt-Probe (kein Mock) haelt in beiden Umgebungen ihren Vertrag.

    Frueher stand hier ``assert not cap.ok`` mit der Begruendung „offscreen
    ohne X". Das ist keine Eigenschaft der Probe, sondern eine Annahme ueber
    den Rechner: auf einem Raspberry Pi (Broadcom V3D + Mesa) liefert auch die
    Offscreen-Plattform einen Kontext, und der Test scheiterte. Geprueft wird
    jetzt der Vertrag – die Probe wirft nie und ist in sich konsistent.
    """
    cap = probe_3d_capability(use_cache=False)
    if cap.ok:
        assert cap.error_key is None
        assert cap.diagnostic, "Erfolg ohne Renderer-Provenienz waere nicht nachvollziehbar"
    else:
        assert cap.error_key == UNAVAILABLE_KEY


def test_offscreen_default_probe_reports_unavailable(qapp) -> None:
    """Der echte Fallback-Zweig – seit #1002 ohne Umgebungs-Vorbehalt.

    Bis #1001 stand hier ein hartes ``assert not cap.ok`` mit der Begründung
    „offscreen ohne X"; auf einem Raspberry Pi mit GL-Kontext scheiterte das,
    weshalb #1001 einen Skip einbaute. Beides ist erledigt: Unter einer
    Plattform ohne OpenGL-Widget-Fläche ist das Ergebnis jetzt **deterministisch**
    „nicht verfügbar" – genau der Zustand, den #1002 gemeldet hat. Der Test
    misst damit wieder etwas.
    """
    from PyQt6.QtGui import QGuiApplication

    if QGuiApplication.platformName() not in NON_RENDERABLE_PLATFORMS:
        pytest.skip("Testlauf auf einer renderfähigen Plattform")
    cap = probe_3d_capability(use_cache=False)
    assert not cap.ok
    assert cap.error_key == UNAVAILABLE_KEY
    assert "trägt keine OpenGL-Widget-Fläche" in cap.detail


# ── Spätere Fehlerzweige von ``_default_probe`` (#659, O8) ────────────────
#
# Der reale Offscreen-Testpfad oben trifft nur ``ctx.create() == False`` (den
# frühesten Fehlerzweig). Die tieferen Zweige (Surface/Make-current, GLES,
# fehlende Versionsfunktionen, äußere Exception) werden hier über gefakte
# PyQt6-Klassen erreicht – ``_default_probe`` importiert seine Qt-Klassen
# lokal je Aufruf, ein Patch auf dem Modulattribut wirkt daher sofort
# (Konvention aus ``test_app.py``, ``monkeypatch.setattr("PyQt6....", ...)``).

def _force_platform(monkeypatch, name: str) -> None:
    """Setzt den gemeldeten Qt-Plattformnamen für die Plattformregel (#1002).

    Die Testumgebung läuft unter ``offscreen``; ohne diese Weiche griffe die
    Plattformregel zuerst, und die tieferen Zweige von ``_default_probe``
    wären gar nicht mehr erreichbar.
    """

    class _App:
        @staticmethod
        def instance() -> object:
            return object()  # eine laufende Anwendung vortäuschen

        @staticmethod
        def platformName() -> str:  # noqa: N802
            return name

    monkeypatch.setattr("PyQt6.QtGui.QGuiApplication", _App)


@pytest.fixture
def session_platform(monkeypatch):
    """Stellt eine renderfähige Sitzungs-Plattform für die GL-Mock-Tests."""
    _force_platform(monkeypatch, "xcb")


class _FakeContext:
    """Minimaler ``QOpenGLContext``-Stand-in: Kontext erzeugbar, aber tot."""

    def setFormat(self, fmt: object) -> None:  # noqa: N802
        pass

    def create(self) -> bool:
        return True

    def format(self) -> object:
        return None

    def makeCurrent(self, surface: object) -> bool:  # noqa: N802
        return False

    def isOpenGLES(self) -> bool:  # noqa: N802
        return False

    def doneCurrent(self) -> None:  # noqa: N802
        pass


class _FakeSurface:
    def setFormat(self, fmt: object) -> None:  # noqa: N802
        pass

    def create(self) -> None:
        pass

    def isValid(self) -> bool:
        return True


def test_default_probe_reports_unavailable_when_makecurrent_fails(monkeypatch, session_platform) -> None:
    monkeypatch.setattr("PyQt6.QtGui.QOpenGLContext", _FakeContext)
    monkeypatch.setattr("PyQt6.QtGui.QOffscreenSurface", _FakeSurface)

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert cap.detail == "Kein aktueller Offscreen-Kontext"


def test_default_probe_reports_unavailable_for_opengl_es_context(monkeypatch, session_platform) -> None:
    class _ESContext(_FakeContext):
        def makeCurrent(self, surface: object) -> bool:  # noqa: N802
            return True

        def isOpenGLES(self) -> bool:  # noqa: N802
            return True

    monkeypatch.setattr("PyQt6.QtGui.QOpenGLContext", _ESContext)
    monkeypatch.setattr("PyQt6.QtGui.QOffscreenSurface", _FakeSurface)

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert cap.detail == "Nur OpenGL-ES-Kontext verfügbar"


def test_default_probe_reports_unavailable_without_version_functions(monkeypatch, session_platform) -> None:
    class _ReadyContext(_FakeContext):
        def makeCurrent(self, surface: object) -> bool:  # noqa: N802
            return True

    class _NoFunctionsFactory:
        @staticmethod
        def get(profile: object, ctx: object) -> None:
            return None

    monkeypatch.setattr("PyQt6.QtGui.QOpenGLContext", _ReadyContext)
    monkeypatch.setattr("PyQt6.QtGui.QOffscreenSurface", _FakeSurface)
    monkeypatch.setattr(
        "PyQt6.QtOpenGL.QOpenGLVersionFunctionsFactory", _NoFunctionsFactory
    )

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert cap.detail == "Keine GL-2.1-Versionsfunktionen verfügbar"


def test_default_probe_never_propagates_outer_exception(monkeypatch, session_platform) -> None:
    class _RaisingContext:
        def __init__(self) -> None:
            raise RuntimeError("Treiber explodiert")

    monkeypatch.setattr("PyQt6.QtGui.QOpenGLContext", _RaisingContext)

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert "RuntimeError" in cap.detail
    assert "Treiber explodiert" in cap.detail


def test_gl_string_returns_empty_on_exception() -> None:
    class _Boom:
        def glGetString(self, name: int) -> str:  # noqa: N802
            raise RuntimeError("boom")

    assert _gl_string(_Boom(), 0x1F00) == ""


def test_gl_string_returns_empty_when_none() -> None:
    class _NoneReturning:
        def glGetString(self, name: int) -> None:  # noqa: N802
            return None

    assert _gl_string(_NoneReturning(), 0x1F00) == ""


def test_gl_string_decodes_bytes() -> None:
    class _BytesReturning:
        def glGetString(self, name: int) -> bytes:  # noqa: N802
            return b"Mesa"

    assert _gl_string(_BytesReturning(), 0x1F00) == "Mesa"


# ── Render-Nachweis: „Kontext ja, aber kein Framebuffer" (#1002) ──────────
#
# Der reale Zustand („QOpenGLWidget: No fbo, cannot render" bei gelungener
# Kontexterzeugung) tritt nur auf bestimmter Hardware auf (beobachtet: Raspberry
# Pi 5, Broadcom V3D + Mesa, `QT_QPA_PLATFORM=offscreen`). Hier wird er über
# dieselben lokalen Qt-Importe gestellt wie die Fehlerzweige oben.

class _ReadyContext(_FakeContext):
    """Kontext, der bis zum Render-Nachweis alles besteht.

    ``currentContext`` gehört dazu: ``_render_probe`` fragt es ab, bevor es ein
    Framebuffer-Objekt baut – Qt dereferenziert den aktuellen Kontext dort
    ungeprüft (ohne ihn SIGSEGV statt Ausnahme).
    """

    def makeCurrent(self, surface: object) -> bool:  # noqa: N802
        return True

    @staticmethod
    def currentContext() -> object:  # noqa: N802
        return object()


class _FakeFunctions:
    """GL-2.1-Funktionssatz-Stand-in: liefert Provenienz und zählt ``glClear``."""

    def __init__(
        self,
        clear_error: Exception | None = None,
        *,
        gl_errors: list[int] | None = None,
    ) -> None:
        self.clear_masks: list[int] = []
        self._clear_error = clear_error
        # Warteschlange wie bei echtem GL: ``glGetError`` liefert je Aufruf
        # einen Fehler und löscht ihn; danach 0.
        self._gl_errors = list(gl_errors or [])
        self.get_error_calls = 0

    def glGetString(self, name: int) -> bytes:  # noqa: N802
        return {0x1F00: b"Broadcom", 0x1F01: b"V3D 7.1", 0x1F02: b"2.1 Mesa"}[name]

    def glClear(self, mask: int) -> None:  # noqa: N802
        if self._clear_error is not None:
            raise self._clear_error
        self.clear_masks.append(mask)

    def glGetError(self) -> int:  # noqa: N802
        self.get_error_calls += 1
        return self._gl_errors.pop(0) if self._gl_errors else 0


def _install_ready_context(monkeypatch, fns: _FakeFunctions) -> None:
    """Patcht Kontext, Oberfläche und Funktions-Factory auf den Erfolgspfad."""

    class _Factory:
        @staticmethod
        def get(profile: object, ctx: object) -> _FakeFunctions:
            return fns

    monkeypatch.setattr("PyQt6.QtGui.QOpenGLContext", _ReadyContext)
    monkeypatch.setattr("PyQt6.QtGui.QOffscreenSurface", _FakeSurface)
    monkeypatch.setattr("PyQt6.QtOpenGL.QOpenGLVersionFunctionsFactory", _Factory)


class _FakeFbo:
    """``QOpenGLFramebufferObject``-Stand-in mit steuerbarem Ausgang."""

    valid = True
    bindable = True
    construct_error: Exception | None = None
    last: _FakeFbo | None = None

    class Attachment:
        CombinedDepthStencil = "combined-depth-stencil"

    def __init__(self, width: int, height: int, attachment: object) -> None:
        if type(self).construct_error is not None:
            raise type(self).construct_error
        self.size = (width, height)
        self.attachment = attachment
        self.released = 0
        type(self).last = self

    def isValid(self) -> bool:  # noqa: N802
        return type(self).valid

    def bind(self) -> bool:
        return type(self).bindable

    def release(self) -> None:
        self.released += 1


@pytest.fixture
def fake_fbo(monkeypatch):
    """Frische ``_FakeFbo``-Klasse je Test (die Schalter sind Klassenattribute)."""
    cls = type("_Fbo", (_FakeFbo,), {"valid": True, "bindable": True,
                                     "construct_error": None, "last": None})
    monkeypatch.setattr("PyQt6.QtOpenGL.QOpenGLFramebufferObject", cls)
    return cls


def test_render_proof_mirrors_the_widget_framebuffer(monkeypatch, fake_fbo, session_platform) -> None:
    """Der Nachweis stellt genau nach, was ``QOpenGLWidget`` selbst anlegt.

    ``QOpenGLWidgetPrivate::recreateFbos`` erzeugt ein
    ``QOpenGLFramebufferObject`` mit ``CombinedDepthStencil``, bindet es und
    leert es per ``glClear`` – in der Mindestgröße des Viewers. Weil die Probe
    dieselbe Folge fährt, kann sie
    **nie strenger** sein als der Viewer – ein Falsch-Negativ (3D grundlos
    abgeschaltet) ist damit ausgeschlossen. Genau diese Bindung hält der Test.
    """
    fns = _FakeFunctions()
    _install_ready_context(monkeypatch, fns)

    cap = _default_probe()

    assert cap.ok is True
    assert cap.diagnostic == "Broadcom / V3D 7.1 / 2.1 Mesa"
    assert fake_fbo.last is not None
    assert fake_fbo.last.size == capability.MIN_VIEWER_SIZE_PX
    assert fake_fbo.last.attachment == fake_fbo.Attachment.CombinedDepthStencil
    assert fake_fbo.last.released == 1  # Bindung wieder gelöst
    # Farbe + Tiefe + Stencil, wie recreateFbos() leert.
    assert fns.clear_masks == [0x00004000 | 0x00000100 | 0x00000400]


def test_default_probe_reports_unavailable_without_a_usable_framebuffer(
    monkeypatch, fake_fbo, session_platform
) -> None:
    """Der eigentliche #1002-Fall: Kontext vorhanden, Render-Ziel unvollständig."""
    fake_fbo.valid = False
    _install_ready_context(monkeypatch, _FakeFunctions())

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert cap.detail == "Kontext ohne vollständiges Framebuffer-Objekt"
    # Die Provenienz überlebt den Fehlerfall – sonst wäre das Gerät, das genau
    # hier scheitert, aus dem Log nicht einzuordnen.
    assert cap.diagnostic == "Broadcom / V3D 7.1 / 2.1 Mesa"


def test_default_probe_reports_unavailable_when_the_framebuffer_cannot_bind(
    monkeypatch, fake_fbo, session_platform
) -> None:
    fake_fbo.bindable = False
    _install_ready_context(monkeypatch, _FakeFunctions())

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert cap.detail == "Framebuffer-Objekt nicht bindbar"


def test_default_probe_reports_unavailable_when_the_render_proof_raises(
    monkeypatch, fake_fbo, session_platform
) -> None:
    """Ein Treiber, der beim Leeren abstürzt, ist ein Befund – kein App-Absturz."""
    _install_ready_context(monkeypatch, _FakeFunctions(clear_error=RuntimeError("GPU weg")))

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert cap.detail.startswith("Render-Nachweis fehlgeschlagen: RuntimeError")
    assert "GPU weg" in cap.detail


def test_default_probe_reports_unavailable_when_the_framebuffer_is_not_constructible(
    monkeypatch, fake_fbo, session_platform
) -> None:
    fake_fbo.construct_error = RuntimeError("kein FBO-Support")
    _install_ready_context(monkeypatch, _FakeFunctions())

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert "kein FBO-Support" in cap.detail


def test_render_proof_refuses_without_a_current_context(monkeypatch, fake_fbo) -> None:
    """Fail-closed statt SIGSEGV.

    ``QOpenGLFramebufferObjectPrivate::init`` dereferenziert
    ``QOpenGLContext::currentContext()`` ungeprüft; ohne aktuellen Kontext
    stirbt der Prozess mit SIGSEGV – kein ``except`` fängt das. ``_default_probe``
    hat den Kontext immer (``makeCurrent()`` ist geprüft), die Schranke sichert
    einen künftigen zweiten Aufrufer ab.
    """

    class _NoCurrent:
        @staticmethod
        def currentContext() -> None:  # noqa: N802
            return None

    monkeypatch.setattr("PyQt6.QtGui.QOpenGLContext", _NoCurrent)

    assert _render_probe(object()) == "Render-Nachweis ohne aktuellen Kontext angefordert"
    assert fake_fbo.last is None  # kein Konstruktoraufruf ohne Kontext


# ── Plattformregel: der eigentliche #1002-Fall ───────────────────────────
#
# Reproduziert mit ``xvfb-run -a`` + ``QT_QPA_PLATFORM=offscreen``: Kontext,
# GL-2.1-Funktionssatz **und** der Render-Nachweis gelingen dort alle, Qt meldet
# aber „QOpenGLWidget is not supported on this platform." / „No fbo, cannot
# render" und ``defaultFramebufferObject()`` bleibt 0. Der FBO-Nachweis kann
# diesen Ausfall prinzipiell nicht sehen – die Plattformregel schon.

@pytest.mark.parametrize("name", sorted(NON_RENDERABLE_PLATFORMS))
def test_platform_without_widget_surface_blocks_before_any_gl_call(
    monkeypatch, name: str
) -> None:
    """Die Regel greift **vor** dem GL-Aufbau – und ohne ihn."""
    _force_platform(monkeypatch, name)

    def _explode() -> object:
        raise AssertionError("Die Plattformregel muss vor jedem GL-Aufruf greifen")

    monkeypatch.setattr("PyQt6.QtGui.QOpenGLContext", _explode)

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert name in cap.detail


def test_platform_rule_lets_a_session_platform_through(monkeypatch) -> None:
    """Kein Falsch-Negativ: Sitzungs-Plattformen passieren die Regel.

    Gemessen gegengeprüft (``xvfb-run`` + ``QT_QPA_PLATFORM=xcb``, llvmpipe):
    Dort meldet die Probe ``ok=True`` und ``QOpenGLWidget`` hält einen
    Framebuffer. Die Regel darf 3D auf tauglicher Hardware nie abschalten.
    """
    for name in ("xcb", "wayland", "wayland-egl", "cocoa", "windows"):
        _force_platform(monkeypatch, name)
        assert _platform_render_support() is None, name


def test_platform_rule_is_fail_open_for_unknown_names(monkeypatch) -> None:
    """Blockliste statt Whitelist.

    Ein künftiges oder unbekanntes Plugin darf nicht blockieren – im Zweifel
    landet der Viewer im Fehlerzustand [F], statt dass 3D grundlos verschwindet.
    ``eglfs``/``minimalegl`` sind hier ausdrücklich erwünscht: Sie belegen keine
    Sitzung (deshalb weist die Preflight-Whitelist sie ab), sind aber
    hardwarebeschleunigt.
    """
    for name in ("", "eglfs", "minimalegl", "irgendwas-neues"):
        _force_platform(monkeypatch, name)
        assert _platform_render_support() is None, name


def test_platform_rule_refuses_without_a_running_application(monkeypatch) -> None:
    """Ohne Anwendung gibt es keine Aussage – und keinen Absturz.

    Gemessen: ``QGuiApplication.platformName()`` liefert ohne laufende Instanz
    einen Vorgabewert (``'xcb'``) und ignoriert ``QT_QPA_PLATFORM`` – die Regel
    prüfte also eine Plattform, die gar nicht läuft. Der Probelauf endete in
    diesem Zustand zuvor mit SIGSEGV in ``ctx.create()`` (Exit 139, ohne jede
    Ausgabe); jetzt ist es ein benannter Befund.
    """

    class _NoApp:
        @staticmethod
        def instance() -> None:
            return None

        @staticmethod
        def platformName() -> str:  # noqa: N802
            return "xcb"  # die gemessene Falschauskunft

    monkeypatch.setattr("PyQt6.QtGui.QGuiApplication", _NoApp)

    assert _platform_render_support() == (
        "Keine laufende QGuiApplication – Plattform nicht bestimmbar"
    )


def test_platform_set_is_the_shared_source() -> None:
    """Eine Quelle statt vier Kopien (#1002).

    ``scripts/gl_stress_probe.py`` sowie die Skip-Weichen von
    ``tests/test_viewer_3d_gl.py`` und ``tests/test_screenshot3d.py`` führten
    dieselbe Menge je einzeln. Driftete eine, hielten Sonde und Anwendung
    verschiedene Plattformen für renderfähig.
    """
    import importlib.util
    import sys
    from pathlib import Path

    import tests.test_screenshot3d as shot
    import tests.test_viewer_3d_gl as gl

    root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location(
        "gl_stress_probe", root / "scripts" / "gl_stress_probe.py"
    )
    assert spec is not None and spec.loader is not None
    stress = importlib.util.module_from_spec(spec)
    # Vor ``exec_module`` registrieren: ``dataclasses`` löst Annotationen über
    # ``sys.modules[cls.__module__]`` auf und stürbe sonst mit AttributeError.
    sys.modules["gl_stress_probe"] = stress
    spec.loader.exec_module(stress)

    assert stress.NON_RENDERABLE_PLATFORMS is NON_RENDERABLE_PLATFORMS
    assert gl._NON_RENDERABLE is NON_RENDERABLE_PLATFORMS
    assert shot._NON_RENDERABLE is NON_RENDERABLE_PLATFORMS


def test_no_second_source_declares_the_non_renderable_platforms() -> None:
    """Drift-Wächter: die Menge wird genau **einmal** literal deklariert (#1002).

    Vor #1002 stand die Menge offscreen/minimal/vnc viermal im Repo (neben dem
    Produktivpfad: ``scripts/gl_stress_probe.py`` und die Skip-Weichen von
    ``test_viewer_3d_gl``, ``test_screenshot3d`` und
    ``test_benchmark_preview3d_live``). Driftete eine Kopie, hielten Sonde und
    Anwendung verschiedene Plattformen für renderfähig – und das wäre still
    geblieben. Der Wächter fängt auch eine künftige fünfte Kopie, nicht nur die
    vier bekannten; gesucht wird die Mengenliteral-Schreibweise, nicht der
    Plattformname allein.
    """
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    source = root / "bgremover" / "preview3d_capability.py"
    # Bewusst zusammengesetzt: Stünde das Muster hier ausgeschrieben, meldete
    # der Wächter diese Datei als eigene zweite Quelle.
    literal = re.compile(r"\{\s*[\"']" + "offscreen" + r"[\"']")

    offenders = []
    for folder in ("bgremover", "scripts", "tests"):
        for path in sorted((root / folder).rglob("*.py")):
            if path == source:
                continue
            if literal.search(path.read_text(encoding="utf-8")):
                offenders.append(str(path.relative_to(root)))
    assert not offenders, (
        "Zweite Quelle der Plattformmenge – aus "
        f"preview3d_capability.NON_RENDERABLE_PLATFORMS beziehen: {offenders}"
    )


# ── Nachträge aus dem Bot-Review zu PR #1003 ─────────────────────────────

def test_render_proof_probes_the_size_the_viewer_actually_needs(qapp) -> None:
    """Ein winziges Ziel belegt die echte Widget-Fläche nicht (Codex-Review).

    Auf einer speicherarmen GPU kann ein 4 × 4-FBO gelingen, während
    ``QOpenGLWidget`` sein deutlich größeres Backing-FBO nicht mehr bekommt –
    genau das ready-but-blank, das die Probe verhindern soll. Geprüft wird
    deshalb in der **Mindestgröße des Viewers**; Qt multipliziert die echte
    Fläche zusätzlich mit dem Device-Pixel-Ratio, die Probe bleibt also
    schwächer als der Viewer (kein Falsch-Negativ).
    """
    from bgremover.viewer_3d import GLReliefViewer

    viewer = GLReliefViewer()
    assert (viewer.minimumWidth(), viewer.minimumHeight()) == capability.MIN_VIEWER_SIZE_PX


def test_render_proof_reports_a_gl_error_raised_by_the_clear(
    monkeypatch, fake_fbo, session_platform
) -> None:
    """``glClear`` wirft nicht – es legt einen Fehlercode ab (Codex-Review).

    Ohne die ``glGetError``-Abfrage meldete der Nachweis genau dort Erfolg, wo
    kein Frame entsteht (z. B. ``GL_INVALID_FRAMEBUFFER_OPERATION`` = 0x0506
    nach einem Kontextverlust).
    """
    fns = _FakeFunctions(gl_errors=[0, 0x0506])  # Warteschlange leer, dann Fehler
    _install_ready_context(monkeypatch, fns)

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert cap.detail == "glClear meldete GL-Fehler 0x0506"


def test_render_proof_drains_stale_errors_before_judging(
    monkeypatch, fake_fbo, session_platform
) -> None:
    """Ein Altfehler aus fremdem Code darf nicht dem eigenen Aufruf angelastet
    werden – die Warteschlange wird vorher geleert."""
    fns = _FakeFunctions(gl_errors=[0x0502, 0x0501, 0, 0])  # zwei Altfehler, dann sauber
    _install_ready_context(monkeypatch, fns)

    cap = _default_probe()

    assert cap.ok is True, cap.detail
    assert fns.get_error_calls >= 3  # geleert und danach bewertet


def test_render_proof_survives_a_failing_qt_import(monkeypatch, session_platform) -> None:
    """„Wirft nie" gilt für die **ganze** Funktion, Importe eingeschlossen.

    Lagen die lokalen Importe außerhalb des ``try``, landete ein ``ImportError``
    im äußeren Handler von ``_default_probe`` – und nahm die dort bereits
    gemessene Renderer-Provenienz mit, die Docstring und CHANGELOG „auch im
    Fehlerfall" zusichern (Review PR #1003).
    """
    real_import = builtins.__import__

    def _boom(name, *args, **kwargs):
        if name == "PyQt6.QtOpenGL" and "QOpenGLFramebufferObject" in (args[2] or ()):
            raise ImportError("QtOpenGL fehlt")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _boom)

    assert "QtOpenGL fehlt" in (_render_probe(_FakeFunctions()) or "")


def test_failure_log_carries_the_renderer_provenance(monkeypatch, caplog) -> None:
    """Die Provenienz muss im **Log** stehen, nicht nur im Rückgabeobjekt.

    ``probe_3d_capability`` loggte im Fehlerzweig nur ``detail`` – für ein
    Gerät, das erst am Render-Nachweis scheitert, stünde dort nie, welche GPU
    das war (Codex-Review PR #1003).
    """
    import logging

    cap = RendererCapability(
        ok=False, error_key=UNAVAILABLE_KEY,
        diagnostic="Broadcom / V3D 7.1 / 2.1 Mesa",
        detail="Kontext ohne vollständiges Framebuffer-Objekt",
    )
    with caplog.at_level(logging.INFO):
        probe_3d_capability(probe_fn=lambda: cap, use_cache=False)

    logged = " ".join(record.getMessage() for record in caplog.records)
    assert "Kontext ohne vollständiges Framebuffer-Objekt" in logged
    assert "Broadcom / V3D 7.1 / 2.1 Mesa" in logged
